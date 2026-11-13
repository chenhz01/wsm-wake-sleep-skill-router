"""契约用例 (b)：SQLite FTS5 扩展可用。

纯标准库、不依赖仓库里任何数据文件，因此本用例始终可运行。
FTS5 是 requirements.txt 声明的硬性前置条件；若当前 Python 的 SQLite
未编译 FTS5，则明确 skip 并说明这是环境能力缺失，不假装通过。
"""

import sqlite3
import unittest


class TestFTS5Available(unittest.TestCase):
    def test_fts5_virtual_table_and_match(self):
        try:
            conn = sqlite3.connect(":memory:")
            conn.execute("CREATE VIRTUAL TABLE t USING fts5(body)")
        except sqlite3.OperationalError as exc:
            self.skipTest(f"当前 SQLite 未编译 FTS5，不满足 requirements.txt：{exc}")

        try:
            conn.executemany(
                "INSERT INTO t(body) VALUES (?)",
                [("wake sleep skill router",), ("context compression baseline",)],
            )
            rows = conn.execute("SELECT body FROM t WHERE t MATCH ?", ("router",)).fetchall()
            self.assertEqual(len(rows), 1, "FTS5 MATCH 应精确命中含 router 的一行")
            self.assertIn("wake sleep", rows[0][0])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
