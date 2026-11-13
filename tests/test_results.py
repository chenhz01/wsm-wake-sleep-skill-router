"""契约用例 (c)：结果 JSON 顶层键齐全 + BLIND-100 分层 60/20/20 断言。

只校验「结构」，不硬编码任何实验数字（命中率 / token / Wilson 区间等）。
分层 60/20/20 与 100 题是冻结的结构常量（见 AGENTS.md / results/README.md），
不是实验数值。结果文件由复现命令产出，尚未产出时按约定 skipTest。
"""

import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 与 AGENTS.md / results/README.md 声明的结构契约一致
REQUIRED_TOP_KEYS = {
    "meta",
    "honesty",
    "token_cost_three_metrics",
    "three_way_blind100",
    "gates",
    "latency",
    "blind100_rows",
}
EXPECTED_LAYERS = {"A": 60, "B": 20, "C": 20}  # 结构常量，非实验数字


def _find_result():
    candidates = [
        ROOT / "results" / "wsm_bench_proxy_v1.json",
        ROOT / "wsm_bench_proxy_v1.json",
    ]
    results_dir = ROOT / "results"
    if results_dir.is_dir():
        candidates += sorted(p for p in results_dir.glob("*.json") if p.is_file())
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and data:
            return path, data
    return None, None


class TestResultsContract(unittest.TestCase):
    def test_result_json_top_level_keys_complete(self):
        path, data = _find_result()
        if data is None:
            self.skipTest("结果 JSON 尚未产出（A 路径重跑结果未回填 results/）")
        missing = REQUIRED_TOP_KEYS - set(data.keys())
        self.assertFalse(
            missing,
            f"{path.name} 缺少契约顶层键 {sorted(missing)}；实际键={sorted(data.keys())}",
        )

    def test_blind100_layer_split_60_20_20(self):
        path, data = _find_result()
        if data is None:
            self.skipTest("结果 JSON 尚未产出（A 路径重跑结果未回填 results/）")

        counts = None
        three_way = data.get("three_way_blind100")
        if isinstance(three_way, dict) and isinstance(three_way.get("layer_counts"), dict):
            try:
                counts = {k: int(v) for k, v in three_way["layer_counts"].items()}
            except (TypeError, ValueError):
                counts = None
        rows = data.get("blind100_rows")
        if counts is None and isinstance(rows, list) and rows and isinstance(rows[0], dict):
            counts = dict(Counter(str(r.get("layer")) for r in rows))
        if counts is None:
            self.skipTest("结果 JSON 未携带分层字段（layer_counts / 逐题 layer），待对齐契约")

        observed = {k: counts.get(k) for k in EXPECTED_LAYERS}
        self.assertEqual(
            observed,
            EXPECTED_LAYERS,
            f"{path.name} BLIND-100 分层应为 A60/B20/C20，实际 {observed}；"
            "分层是冻结结构常量，改动须按 AGENTS.md 一致性清单联动重做。",
        )
        if isinstance(rows, list):
            self.assertEqual(len(rows), 100, "BLIND-100 逐题记录应恰好 100 条")


if __name__ == "__main__":
    unittest.main()
