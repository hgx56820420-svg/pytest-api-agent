# pytest-api-agent

用 pytest 写接口业务测试的插件：不只看状态码，还查数据库里库存、余额、订单状态有没有按需求变化；每个响应按 OpenAPI 契约校验；失败时自动留下请求、响应和库查询证据。另带一套从需求文档设计用例的 Skill 和两个校验脚本，让 AI 起草、脚本校验、人审核。

被测的演示服务（商城、图书借阅、会议室预约）和它们的业务测试、实测记录在 [pytest-api-automation](https://github.com/hgx56820420-svg/pytest-api-automation)。

## 安装

```bash
pip install "pytest-api-agent[contract,tools] @ git+https://github.com/hgx56820420-svg/pytest-api-agent"
```

`contract` 提供响应契约校验（Schemathesis），`tools` 提供校验脚本需要的 PyYAML。

## 写一条测试

```python
import pytest

@pytest.mark.case("TC-ORDER-007")            # 关联测试设计里的用例编号
def test_stock_boundary(api, db):
    ...
    response = api.post("/api/orders", user=buyer, json={"product_id": pid, "quantity": 4})

    assert response.status_code == 400
    assert db.row("products", pid)["stock"] == before    # 失败时库存不能变
```

| fixture | 作用 |
|---|---|
| `api` | HTTP 客户端：`get/post/put/delete`、`register()`、`login()`。路径必须以 `/` 开头，只能发往被测服务；配置契约后每个响应都会校验 |
| `db` | 只读查询：`row(table, id)`、`rows(table, **where)`、`count(table, **where)`；表名和列名做标识符校验，SQLite 以只读模式打开 |
| `admin` | 用配置里的管理员账号登录后的用户 |

## 配置

| 参数 | 环境变量 | 说明 |
|---|---|---|
| `--api-base-url` | `API_BASE_URL` | 被测服务地址 |
| `--api-db-url` | `API_DB_URL` | 测试库连接，请使用只读账号 |
| `--api-admin-user` / `--api-admin-password` | `API_ADMIN_USERNAME` / `API_ADMIN_PASSWORD` | 测试管理员账号 |
| `--api-contract` | `API_CONTRACT` | 接口基线 OpenAPI JSON；配置后每个响应都要：状态码已在契约里声明、响应体符合 schema、没有契约外的字段 |
| `--api-evidence-dir` | | 证据目录，默认 `artifacts/evidence` |

默认认证接口是 `/api/auth/register`、`/api/auth/login`、`/api/auth/me`，令牌字段 `access_token`。项目不同时，在 conftest 里覆盖 `api_target` fixture，改 `ApiTarget` 的 `register_path`、`login_path`、`me_path`、`token_field`。

测试失败时，证据写入 `artifacts/evidence/<测试名>.json`，同时附在 pytest 报告的 `api evidence` 段，密码、token 等字段替换为 `***`。每次运行结束写出 `case-results.json`（用例编号 → passed / failed / skipped）。

## 需求驱动的测试设计

`skill/api-test-design/SKILL.md` 引导 Agent 按四个阶段产出 `cases/<service>.yaml`：

1. 提取需求规则：每条规则必须附需求原文；需求没写清楚的，用必问清单（归属、状态终态、幂等、并发、金额、时间、级联、审计）变成待确认问题，不让 AI 猜。
2. 覆盖矩阵：每条规则过 7 个维度（正常、边界、异常输入、权限、状态、数据副作用、并发），每格要么测，要么写明不测的理由。
3. 测试点：停下来给人审。
4. 用例：标明接口 / UI / 人工可测，后两者要写原因。

两个校验脚本不依赖项目代码，对任意项目可用：

```bash
python scripts/check_cases.py cases/shop.yaml --root /path/to/project    # root 下有 docs/ contracts/ tests/
python scripts/check_tests.py /path/to/project                           # 读 tests/ 和 cases/
```

| 脚本 | 检查 |
|---|---|
| `check_cases.py` | 规则原文能在需求文档里逐字找到、接口在契约里、待确认问题已回答、规则→矩阵→测试点→用例不断链、统计已自动化的接口用例比例 |
| `check_tests.py` | 无断言、常量断言、吞异常、无理由 skip、缺用例编号、属于数据副作用/状态/并发维度的用例没查库、只断言状态码（警告） |

## 已知限制

- 业务失败返回 HTTP 200 加响应体错误码的项目，契约校验只能检查结构，业务结果需要断言响应体。
- 内置的 `register()` / `login()` 假设 JSON 登录；表单登录或响应体多包一层 `code/data` 的项目需要自己写登录 fixture。
- 变异测试（mutmut）需要 Linux / WSL，并要求被测服务和测试在同一进程内运行，做法见演示仓库。

## 开发

```bash
pip install -e ".[dev]"
python -m pytest
```
