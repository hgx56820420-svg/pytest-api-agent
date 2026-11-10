"""operation_coverage.py：接口执行率的口径。"""

import json

from scripts.operation_coverage import main, summarize

SPEC = {"paths": {"/a": {"get": {}, "post": {}}, "/b/{id}": {"get": {}}}}


def _files(tmp_path, stats):
    contract = tmp_path / "shop.openapi.json"
    contract.write_text(json.dumps(SPEC), encoding="utf-8")
    ops = tmp_path / "operations.json"
    ops.write_text(json.dumps(stats), encoding="utf-8")
    return contract, ops


def test_executed_passed_and_failed_only_are_counted_separately(tmp_path):
    contract, ops = _files(
        tmp_path,
        {
            "shop.openapi:GET /a": {"requests": 3, "tests_passed": 2, "tests_failed": 0},
            "shop.openapi:POST /a": {"requests": 1, "tests_passed": 0, "tests_failed": 1},
        },
    )

    [(name, s)] = summarize([contract], json.loads(ops.read_text(encoding="utf-8"))).items()

    assert name == "shop.openapi"
    assert (s["total"], s["executed"], s["passed"]) == (3, 2, 1)
    assert s["failed_only"] == ["shop.openapi:POST /a"]
    assert s["missing"] == ["shop.openapi:GET /b/{id}"]


def test_cli_prints_rates(tmp_path, capsys):
    contract, ops = _files(tmp_path, {"shop.openapi:GET /a": {"requests": 1, "tests_passed": 1, "tests_failed": 0}})

    assert main([str(contract), "--operations", str(ops)]) == 0

    assert "共 3 个接口，执行 1（33%），有通过的测试 1（33%）" in capsys.readouterr().out
