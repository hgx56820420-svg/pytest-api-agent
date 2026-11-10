"""接口执行率：契约里的接口有多少被测试真正请求过、多少有通过的测试。

用法：
    python scripts/operation_coverage.py contracts/portal.openapi.json contracts/admin.openapi.json \
        --operations artifacts/evidence/operations.json [--operations other/operations.json] [--list-missing]

operations.json 由插件在配置了 --api-contract 时，每次运行结束写出。
定义：
    执行  = 至少发出过 1 个请求
    通过  = 至少有 1 条通过的测试请求过它
    仅失败 = 请求过，但请求过它的测试全部失败
"""

import argparse
import json
import sys
from pathlib import Path

METHODS = {"get", "post", "put", "delete", "patch"}


def operations_of(contract: Path) -> list[str]:
    spec = json.loads(contract.read_text(encoding="utf-8"))
    return [f"{contract.stem}:{m.upper()} {p}" for p, item in spec.get("paths", {}).items() for m in item if m in METHODS]


def merge(files: list[Path]) -> dict[str, dict[str, int]]:
    merged: dict[str, dict[str, int]] = {}
    for path in files:
        for key, stats in json.loads(path.read_text(encoding="utf-8")).items():
            into = merged.setdefault(key, {"requests": 0, "tests_passed": 0, "tests_failed": 0})
            for field in into:
                into[field] += stats.get(field, 0)
    return merged


def summarize(contracts: list[Path], stats: dict[str, dict[str, int]]) -> dict:
    result = {}
    for contract in contracts:
        ops = operations_of(contract)
        executed = [o for o in ops if stats.get(o, {}).get("requests", 0) > 0]
        passed = [o for o in ops if stats.get(o, {}).get("tests_passed", 0) > 0]
        failed_only = [o for o in executed if o not in passed]
        result[contract.stem] = {
            "total": len(ops),
            "executed": len(executed),
            "passed": len(passed),
            "failed_only": failed_only,
            "missing": [o for o in ops if o not in executed],
        }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contracts", nargs="+", type=Path)
    parser.add_argument("--operations", action="append", type=Path, required=True)
    parser.add_argument("--list-missing", action="store_true")
    args = parser.parse_args(argv)
    summary = summarize(args.contracts, merge(args.operations))
    total = sum(s["total"] for s in summary.values())
    executed = sum(s["executed"] for s in summary.values())
    passed = sum(s["passed"] for s in summary.values())
    for name, s in summary.items():
        print(f"{name}: 共 {s['total']} 个接口，执行 {s['executed']}（{s['executed'] * 100 // max(s['total'], 1)}%），有通过的测试 {s['passed']}（{s['passed'] * 100 // max(s['total'], 1)}%）")
    print(f"合计: 共 {total} 个接口，执行 {executed}（{executed * 100 // max(total, 1)}%），有通过的测试 {passed}（{passed * 100 // max(total, 1)}%）")
    failed_only = [o for s in summary.values() for o in s["failed_only"]]
    if failed_only:
        print(f"仅失败（请求过但没有通过的测试）{len(failed_only)} 个：")
        for op in failed_only:
            print(f"  {op}")
    if args.list_missing:
        print("未执行：")
        for s in summary.values():
            for op in s["missing"]:
                print(f"  {op}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
