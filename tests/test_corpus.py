"""契约用例 (a)：语料可扫描且恰好 180 个技能。

180 是「语料规模」结构常量（任务约定），不是实验数字，本文件不硬编码
任何命中率 / token / 区间等实验数值。

语料由代码工程师构建，布局可能是：corpus/skills/ 一技能一文件、
单个 JSON 数组、或 skillgraph.db 里的技能表。这里做自适应只读探测；
依赖尚未就绪（目录不存在 / 尚未填充）时按约定 skipTest，不假装通过。
"""

import json
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SKILLS = 180  # 语料规模结构常量，非实验数字

SKILL_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
SHADOW_MARKERS = (
    "_data", "_idx", "_content", "_docsize", "_config", "_segdir", "_segments",
)


def _count_skill_files(base: Path) -> int:
    if not base.is_dir():
        return 0
    return sum(
        1
        for p in base.rglob("*")
        if p.is_file()
        and not p.name.startswith(".")
        and p.suffix.lower() in SKILL_SUFFIXES
    )


def _count_from_single_json(corpus: Path) -> int:
    for p in sorted(corpus.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict) and isinstance(data.get("skills"), list):
            return len(data["skills"])
    return 0


def _count_from_db(db_path: Path) -> int:
    if not db_path.is_file():
        return 0
    try:
        conn = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    except (sqlite3.Error, ValueError):
        return 0
    try:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        best = 0
        for name in names:
            if any(m in name for m in SHADOW_MARKERS):
                continue
            try:
                n = conn.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
            except sqlite3.Error:
                continue
            best = max(best, n)
        return best
    finally:
        conn.close()


class TestCorpus(unittest.TestCase):
    def test_corpus_scannable_and_exactly_180_skills(self):
        corpus = ROOT / "corpus"
        if not corpus.is_dir():
            self.skipTest("corpus/ 尚未就绪（自包含语料由代码工程师构建中）")

        skills_dir = corpus / "skills"
        count = (
            _count_skill_files(skills_dir)
            if skills_dir.is_dir()
            else _count_skill_files(corpus)
        )
        source = "corpus 技能文件数"
        if count == 0:
            count = _count_from_single_json(corpus)
            source = "单 JSON 技能数组"
        if count == 0:
            count = _count_from_db(ROOT / "skillgraph.db")
            source = "skillgraph.db 表行数"
        if count == 0:
            self.skipTest("语料/db 已存在但尚无法数出技能数（仍在填充或结构待对齐）")

        self.assertEqual(
            count,
            EXPECTED_SKILLS,
            f"按 {source} 得到 {count} 个技能，契约要求恰好 {EXPECTED_SKILLS} 个。"
            "若语料规模变更，须按 AGENTS.md 一致性清单同更语料/db/评测集/文档并重跑整套实验。",
        )


if __name__ == "__main__":
    unittest.main()
