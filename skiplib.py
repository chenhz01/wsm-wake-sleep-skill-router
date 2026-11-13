# -*- coding: utf-8 -*-
"""skiplib.py — 技能目录按需检索（SkillGraph / BM25 检索层）

纯标准库。索引存 sqlite3：
  - 优先 FTS5（unicode61 + 预切分的中文二元 token）
  - FTS5 不可用 / 设置 SKIPLIB_FORCE_FALLBACK=1 时，自写 BM25（内存倒排）

命令：
  python skiplib.py build            建/重建索引
  python skiplib.py top "任务描述" -k 3
  python skiplib.py cost             全量目录 vs top3 的 token 对比
  python skiplib.py eval             跑内置 20 条评测，输出 hit@3
  python skiplib.py list [--full]    列出已索引技能（调试用）
"""
import argparse
import json
import math
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
SKILLS_DIR = BASE / "corpus" / "skills"
DB_PATH = BASE / "skillgraph.db"
BODY_SNIPPET = 300  # 正文只取前 300 字

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_\-\.\+#]*|[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")

# 中文单字/高频二元停用词；英文停用词
ZH_STOP = {
    "的", "了", "是", "在", "和", "与", "或", "把", "被", "为", "我", "你", "他", "她", "它",
    "这", "那", "个", "们", "吗", "呢", "吧", "啊", "有", "不", "就", "都", "要", "会",
    "一个", "以及", "如何", "怎么", "什么", "可以", "进行", "使用", "需要", "帮我", "我们",
    "并且", "然后", "如果", "因为", "所以", "还是", "已经", "通过", "对于", "关于", "以及",
}
EN_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "be",
    "it", "this", "that", "you", "your", "my", "i", "me", "we", "how", "what", "when", "use",
    "using", "used", "can", "do", "does", "from", "by", "as", "at", "into", "not",
}


def tokenize(text):
    """CJK 二元切分 + 拉丁词；返回 token 列表（保留重复，供 BM25 统计 tf）。"""
    if not text:
        return []
    out = []
    # 先把标点/连字符/点号统一成空格，避免 "ssh-keyscan"、"SKILL.md" 变成脏 token
    text = re.sub(r"[^0-9a-z\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+", " ", text.lower())
    for m in TOKEN_RE.finditer(text):
        s = m.group(0)
        if CJK_RE.match(s):
            if len(s) == 1:
                if s not in ZH_STOP:
                    out.append(s)
            else:
                for i in range(len(s) - 1):
                    bg = s[i:i + 2]
                    if bg not in ZH_STOP:
                        out.append(bg)
        else:
            if len(s) >= 2 and s not in EN_STOP:
                out.append(s)
    return out


def est_tokens(text):
    """token 估算（保守）：CJK 1 token/字，拉丁词 1.3 token/词，空白与标点忽略。"""
    if not text:
        return 0
    cjk = sum(1 for ch in text if CJK_RE.match(ch))
    latin = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-\.\+#]*", text))
    return int(round(cjk + latin * 1.3))


def est_tokens_bpe(text):
    """token 估算（cl100k 经验值）：CJK 1.5 token/字，拉丁词 1.3 token/词。"""
    if not text:
        return 0
    cjk = sum(1 for ch in text if CJK_RE.match(ch))
    latin = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-\.\+#]*", text))
    return int(round(cjk * 1.5 + latin * 1.3))


def _clean_yaml_value(v):
    v = v.strip()
    if v[:1] in ("'", '"'):
        q = v[0]
        if v.endswith(q) and len(v) > 1:
            v = v[1:-1]
    if v[:1] in (">", "|"):
        v = v[1:].strip()
    return re.sub(r"\s+", " ", v).strip()


def parse_skill(path):
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    fm, body = {}, raw
    if raw.lstrip().startswith("---"):
        lines = raw.splitlines()
        start = next(i for i, ln in enumerate(lines) if ln.strip() == "---")
        end = None
        for i in range(start + 1, len(lines)):
            if lines[i].strip() in ("---", "..."):
                end = i
                break
        if end:
            key = None
            for ln in lines[start + 1:end]:
                m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", ln)
                if m and not ln.startswith((" ", "\t")):
                    key = m.group(1).strip().lower()
                    fm[key] = m.group(2)
                elif key and ln.startswith((" ", "\t")):
                    fm[key] = fm.get(key, "") + " " + ln.strip()
            body = "\n".join(lines[end + 1:])
    name = _clean_yaml_value(fm.get("name", "")) or path.parent.name
    desc = _clean_yaml_value(fm.get("description", ""))
    if not desc:
        # 少数 SKILL.md 不用 YAML，而是 "# name: ... # description: ..." 注释式头
        m = re.search(r"^#\s*description\s*:\s*(.+)$", raw, re.M)
        if m:
            desc = _clean_yaml_value(m.group(1))
        m2 = re.search(r"^#\s*name\s*:\s*(.+)$", raw, re.M)
        if m2:
            name = _clean_yaml_value(m2.group(1)) or name
    snippet = re.sub(r"\s+", " ", body).strip()[:BODY_SNIPPET]
    return {
        "name": name,
        "dir": path.parent.name,
        "description": desc,
        "body": snippet,
        "path": str(path),
    }


def scan_skills():
    docs = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        # 跳过 _archive 等隐藏/归档目录
        if skill_md.parent.name.startswith((".", "_")):
            continue
        docs.append(parse_skill(skill_md))
    return docs


# ---------------------------------------------------------------- index

def fts5_ok(conn):
    try:
        conn.execute("CREATE VIRTUAL TABLE temp.__fts_probe USING fts5(x)")
        conn.execute("DROP TABLE temp.__fts_probe")
        return True
    except sqlite3.OperationalError:
        return False


def connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def build(verbose=True):
    t0 = time.time()
    docs = scan_skills()
    if not docs:
        raise SystemExit("没有扫描到任何 SKILL.md，请检查 SKILLS_DIR")
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = connect()
    conn.execute(
        "CREATE TABLE skills(id INTEGER PRIMARY KEY, name TEXT, dir TEXT, description TEXT,"
        " body TEXT, path TEXT)"
    )
    conn.executemany(
        "INSERT INTO skills(name, dir, description, body, path) VALUES (?,?,?,?,?)",
        [(d["name"], d["dir"], d["description"], d["body"], d["path"]) for d in docs],
    )
    use_fts = fts5_ok(conn) and os.environ.get("SKIPLIB_FORCE_FALLBACK") != "1"
    meta = {"fts5": int(use_fts), "built_at": int(time.time()), "n": len(docs),
            "skills_dir": "corpus/skills"}
    conn.execute("CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT)")
    conn.executemany("INSERT INTO meta(k, v) VALUES (?,?)", [(k, str(v)) for k, v in meta.items()])
    if use_fts:
        conn.execute(
            "CREATE VIRTUAL TABLE skills_fts USING fts5(name, description, body,"
            " tokenize='unicode61')"
        )
        rows = []
        for d in docs:
            rid = conn.execute("SELECT id FROM skills WHERE path=?", (d["path"],)).fetchone()[0]
            rows.append((rid, " ".join(tokenize(d["name"])),
                         " ".join(tokenize(d["description"])),
                         " ".join(tokenize(d["body"]))))
        conn.executemany("INSERT INTO skills_fts(rowid, name, description, body) VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()
    if verbose:
        mode = "FTS5" if use_fts else "内置 BM25 回退"
        print(f"[build] {len(docs)} 个技能，索引模式：{mode}，耗时 {time.time()-t0:.2f}s -> {DB_PATH}")


def load_docs():
    conn = connect()
    docs = [dict(r) for r in conn.execute("SELECT * FROM skills ORDER BY id")]
    conn.close()
    return docs


# ---------------------------------------------------------------- ranking

def _fts_scores(query, k):
    conn = connect()
    toks = tokenize(query)
    if not toks:
        conn.close()
        return []
    expr = " OR ".join('"%s"' % t for t in toks)
    sql = (
        "SELECT rowid, -bm25(skills_fts, 8.0, 4.0, 1.0) AS s FROM skills_fts"
        " WHERE skills_fts MATCH ? ORDER BY s DESC LIMIT ?"
    )
    try:
        rows = conn.execute(sql, (expr, max(k * 5, 20))).fetchall()
    except sqlite3.OperationalError as e:
        # MATCH 语法异常时退回自写 BM25，绝不静默返回空
        print(f"[warn] FTS5 MATCH 失败（{e}），本次退回内置 BM25", file=sys.stderr)
        conn.close()
        return _fallback_scores(query, k)
    conn.close()
    return [(r["rowid"], float(r["s"])) for r in rows]


def _fallback_scores(query, k):
    docs = load_docs()
    qt = tokenize(query)
    if not qt:
        return []
    # 字段加权：name x6, description x3, body x1
    item_tfs, dfs, dl = [], {}, []
    for d in docs:
        tf = {}
        for field, w in (("name", 6), ("description", 3), ("body", 1)):
            for t in tokenize(d[field]) * w:
                tf[t] = tf.get(t, 0) + 1
        item_tfs.append(tf)
        dl.append(sum(tf.values()))
        for t in set(tf):
            dfs[t] = dfs.get(t, 0) + 1
    n = len(docs)
    avgdl = sum(dl) / n if n else 1
    k1, b = 1.5, 0.75
    scored = []
    for i, tf in enumerate(item_tfs):
        s = 0.0
        for t in set(qt):
            if t not in tf:
                continue
            df = dfs.get(t, 0)
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            f = tf[t]
            s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * dl[i] / avgdl))
        if s > 0:
            scored.append((docs[i]["id"], s))
    scored.sort(key=lambda x: -x[1])
    return scored[:max(k * 5, 20)]


def rank(query, k=3):
    docs = {d["id"]: d for d in load_docs()}
    conn = connect()
    meta = {r["k"]: r["v"] for r in conn.execute("SELECT * FROM meta")}
    conn.close()
    use_fts = meta.get("fts5") == "1" and os.environ.get("SKIPLIB_FORCE_FALLBACK") != "1"
    pairs = _fts_scores(query, k) if use_fts else _fallback_scores(query, k)
    qt = set(tokenize(query))
    qlow = query.lower()
    out = []
    for rid, score in pairs:
        d = docs.get(rid)
        if not d:
            continue
        nt = set(tokenize(d["name"]))
        name_hit = len(qt & nt) / max(1, len(nt))
        exact = 6.0 if d["name"].lower() in qlow else 0.0
        out.append((score + 4.0 * name_hit + exact, d))
    out.sort(key=lambda x: -x[0])
    return out[:k], use_fts


def why(query, doc):
    qt = set(tokenize(query))
    hits = sorted(qt & (set(tokenize(doc["description"])) | set(tokenize(doc["body"]))))
    n = len(hits)
    desc = doc["description"] or doc["body"]
    if len(desc) > 78:
        desc = desc[:78].rstrip() + "…"
    lead = f"命中 {n} 个关键词" if n else "弱匹配"
    return f"{lead}；{desc}"


# ---------------------------------------------------------------- cost

def cost():
    docs = load_docs()
    n = len(docs)
    cat_tok = sum(est_tokens(d["name"] + " " + d["description"]) for d in docs)
    full_tok = sum(est_tokens(d["name"] + " " + d["description"] + " " + d["body"]) for d in docs)
    cat_bpe = sum(est_tokens_bpe(d["name"] + " " + d["description"]) for d in docs)
    full_bpe = sum(est_tokens_bpe(d["name"] + " " + d["description"] + " " + d["body"]) for d in docs)

    top3_sizes = []
    for q, _ in EVAL:
        ranked, _ = rank(q, 3)
        top3_sizes.append(sum(est_tokens(d["name"] + " " + d["description"]) + 8 for _, d in ranked))
    top3_avg = sum(top3_sizes) / len(top3_sizes) if top3_sizes else 0

    full_body = []
    for d in docs:
        txt = Path(d["path"]).read_text(encoding="utf-8-sig", errors="replace")
        full_body.append(est_tokens(txt))
    body_avg = sum(full_body) / len(full_body)

    print(f"技能数                    : {n}")
    print(f"全量目录 token(保守估)     : {cat_tok:,}   （name+description，每 skill 均值 {cat_tok/n:.0f}）")
    print(f"全量目录 token(cl100k 估)  : {cat_bpe:,}   （CJK=1.5 token/字）")
    print(f"全量语料 token(含正文300)  : {full_tok:,} / cl100k {full_bpe:,}")
    print(f"top3 候选清单 token        : {top3_avg:.0f}   （20 条评测查询平均，含每条 8 token 格式开销）")
    print(f"选中 1 个技能全文 token    : {body_avg:.0f}   （按需加载完整 SKILL.md 的均值）")
    print(f"生产单任务 ≈ top3 + 1 篇   : {top3_avg + body_avg:.0f}")
    print(f"节省（对全量目录）         : {1 - (top3_avg + body_avg) / cat_tok:.2%}")
    print(f"节省（只算 top3 vs 目录）  : {1 - top3_avg / cat_tok:.2%}")
    return {"n": n, "cat_tokens": cat_tok, "cat_tokens_bpe": cat_bpe,
            "full_tokens": full_tok, "top3_tokens": int(top3_avg),
            "skill_body_tokens": int(body_avg)}


# ---------------------------------------------------------------- eval

EVAL = [
    [
        "短视频平台视频链接里的方法，帮我走十流程提炼成系统能力",
        [
            "capability-180"
        ]
    ],
    [
        "给 代码托管平台 上的项目发合作 Issue，先写草稿再过验证再发送",
        [
            "capability-017",
            "capability-127"
        ]
    ],
    [
        "知识库 wiki 体检，找矛盾页面、孤立页面和缺失引用",
        [
            "capability-025"
        ]
    ],
    [
        "把 raw 目录的新资料摄入知识库，生成来源摘要并更新索引",
        [
            "capability-023"
        ]
    ],
    [
        "把一篇长文蒸馏成可复用的认知胶囊和决策要点",
        [
            "capability-107"
        ]
    ],
    [
        "给面条品牌写一首歌，还要交互式 MV 和多平台分发清单",
        [
            "capability-019"
        ]
    ],
    [
        "用 视频生成模型 做古风短片，水墨留白、中式美学和运镜",
        [
            "capability-098"
        ]
    ],
    [
        "小说翻译腔太重，帮我治理堆砌形容词和万能句式",
        [
            "capability-033",
            "capability-059"
        ]
    ],
    [
        "用 代码托管平台 API 评估仓库近四周提交、贡献者数和发版心跳",
        [
            "capability-136"
        ]
    ],
    [
        "检查 SMTP 服务器的 加密传输 支持和证书有效期",
        [
            "capability-156"
        ]
    ],
    [
        "ssh-keyscan 拿到的指纹和信任基线对不上，要告警",
        [
            "capability-160"
        ]
    ],
    [
        "一句话让 AI 处理 Excel，做多源结构化数据操作",
        [
            "capability-076"
        ]
    ],
    [
        "把一张截图识读成结构化内容并沉淀到 本地笔记库",
        [
            "capability-101"
        ]
    ],
    [
        "换了模型，做换前换后的四轴量化对比",
        [
            "capability-121"
        ]
    ],
    [
        "搭 AI 量化交易，策略回测和选股，用 量化回测框架 或 量化回测框架",
        [
            "capability-132"
        ]
    ],
    [
        "给 插件平台 批量装插件，装完核验有没有生效",
        [
            "capability-013"
        ]
    ],
    [
        "从零写一个 skill，要 SKILL.md 模板和评测验证",
        [
            "capability-154"
        ]
    ],
    [
        "技能库膨胀了，找孤立和近重复的 skill，出剪枝清单",
        [
            "capability-151"
        ]
    ],
    [
        "把长视频内容做成知识视频脚本，科普讲解那种讲法",
        [
            "capability-108"
        ]
    ],
    [
        "企业 AI 落地，RAG 部署、成熟度评估和组织设计",
        [
            "capability-088"
        ]
    ]
]

# 留出集：故意不抄 description 关键词，只用同义/口语转述，检验泛化而非词面命中
HOLDOUT = [
    [
        "网上那个视频讲的东西，我想变成自己电脑上能用的工具",
        [
            "capability-094"
        ]
    ],
    [
        "帮我把一堆散落的旧笔记整理进我的资料库",
        [
            "capability-022"
        ]
    ],
    [
        "每次都被同一个问题坑，想让 AI 记住别再犯",
        [
            "capability-105"
        ]
    ],
    [
        "写文章一眼就被看出是机器写的，怎么改",
        [
            "capability-033",
            "capability-059"
        ]
    ],
    [
        "看看某个开源项目是不是只靠一个人撑着",
        [
            "capability-136"
        ]
    ],
    [
        "把英文长文缩成中文要点",
        [
            "capability-075"
        ]
    ],
    [
        "给公司搭一套能问答内部资料的系统",
        [
            "capability-088"
        ]
    ],
    [
        "帮我盯着定时任务，挂了要第一时间知道",
        [
            "capability-074"
        ]
    ],
    [
        "检查一下这台机器的 SSH 有没有被人冒充",
        [
            "capability-160"
        ]
    ],
    [
        "客户要的文件我到底交付到哪一步了",
        [
            "capability-078"
        ]
    ],
    [
        "帮我想想这个技术怎么变成收入",
        [
            "capability-167"
        ]
    ],
    [
        "给小孩讲一个知识点，怎么讲才能记住",
        [
            "capability-106"
        ]
    ]
]


HARD_EVAL = [
    [
        "帮我把这个链接里的东西变成我自己的能力",
        []
    ],
    [
        "最近有什么值得看的新东西吗",
        []
    ],
    [
        "这段代码跑不通，帮我看看",
        [
            "capability-012"
        ]
    ],
    [
        "帮我写一份周报",
        []
    ],
    [
        "这个方案到底能不能赚钱",
        [
            "capability-167"
        ]
    ]
]


def run_eval(verbose=True):
    rows, hit = [], 0
    ks = 3
    for q, expect in EVAL:
        ranked, use_fts = rank(q, ks)
        names = [d["name"] for _, d in ranked]
        ok = bool(set(names) & set(expect))
        hit += ok
        rows.append((q, expect, names, ok))
    rate = hit / len(EVAL) if EVAL else 0.0
    if verbose:
        for i, (q, expect, names, ok) in enumerate(rows, 1):
            mark = "OK  " if ok else "MISS"
            print(f"{i:02d} {mark} | {q}")
            print(f"        期望 {expect} | 实际 {names}")
        print(f"\nhit@{ks} = {hit}/{len(EVAL)} = {rate:.1%}")
        h2 = 0
        hrows = []
        for q, expect in HOLDOUT:
            ranked, _ = rank(q, 3)
            names = [d["name"] for _, d in ranked]
            ok = bool(set(names) & set(expect))
            h2 += ok
            hrows.append((q, expect, names, ok))
        print("\n--- 留出集（同义转述，检验泛化）---")
        for i, (q, expect, names, ok) in enumerate(hrows, 1):
            print(f"H{i:02d} {'OK  ' if ok else 'MISS'} | {q}")
            print(f"        期望 {expect} | 实际 {names}")
        print(f"holdout hit@{ks} = {h2}/{len(HOLDOUT)} = {h2/len(HOLDOUT):.1%}")
        print("\n--- 压力探针（不计入 hit@3）---")
        for q, expect in HARD_EVAL:
            ranked, _ = rank(q, 3)
            names = [d["name"] for _, d in ranked]
            print(f"* {q}")
            print(f"        实际 {names}   （期望 {'无明确对应' if not expect else expect}）")
        return {"hit": hit, "n": len(EVAL), "hit3": rate,
                "holdout_hit": h2, "holdout_n": len(HOLDOUT), "rows": rows}
    return {"hit": hit, "n": len(EVAL), "hit3": rate, "rows": rows}


def main():
    ap = argparse.ArgumentParser(prog="skiplib")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    p_top = sub.add_parser("top")
    p_top.add_argument("query")
    p_top.add_argument("-k", type=int, default=3)
    p_top.add_argument("--json", action="store_true")
    sub.add_parser("cost")
    p_eval = sub.add_parser("eval")
    p_eval.add_argument("--json", action="store_true")
    p_list = sub.add_parser("list")
    p_list.add_argument("--full", action="store_true")
    args = ap.parse_args()

    if args.cmd == "build":
        build()
    elif args.cmd == "top":
        ranked, use_fts = rank(args.query, args.k)
        if args.json:
            print(json.dumps([{**{k: d[k] for k in ("name", "description")},
                               "score": round(s, 3), "why": why(args.query, d)}
                              for s, d in ranked], ensure_ascii=False, indent=2))
        else:
            print(f"查询：{args.query}   (k={args.k}, {'FTS5' if use_fts else 'BM25'})")
            for i, (s, d) in enumerate(ranked, 1):
                print(f"{i}. {d['name']}  [{s:.2f}]")
                print(f"   {why(args.query, d)}")
    elif args.cmd == "cost":
        cost()
    elif args.cmd == "eval":
        res = run_eval()
        if args.json:
            print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False))
    elif args.cmd == "list":
        for d in load_docs():
            print(f"{d['name']}\t{d['description'][:120]}")
            if args.full:
                print(f"    body: {d['body'][:120]}")


if __name__ == "__main__":
    main()
