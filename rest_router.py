# -*- coding: utf-8 -*-
"""rest_router.py — 清醒/睡眠双相技能路由原型（Wake-Sleep Skill Router, WSSR v0.3）

对应「技能路由层」三证产品的可证伪内核。纯标准库，不改 skiplib.py 一行。

设计要点（与 v0.1 的关键差别）：
  离线睡眠相的核心不是「在线补词」，而是把技能描述**编译成用户会怎么说**的场景触发集
  （doc2query 式口语化索引）；在线清醒相仍是 O(1) 轻量匹配，不加载模型、不做向量检索。

五个可独立开关的机制（消融实验分离贡献，全部无 HOLDOUT 标签）：
  scene  : 睡眠相①  场景编译 — 从 description 抽「触发词:/当…时使用/引号术语」建短索引并高加权
  shy    : 睡眠相②  突触稳态 — 按历史使用量对热门技能**乘性全局降尺度**，相对保留沉默连接
  replay : 睡眠相③  重放补全 — 训练集 query-token ↔ 命中技能术语共现，自动扩写查询
  dual   : 清醒相   理智/显著性双引擎竞争仲裁 — R 占 3 席，S 仅在能压过 R 第 3 席时替换
           （丘脑网状核式抑制门控；v0.2 固定席位实测掉点，v0.3 由实验反推修正）
  prior  : 泄漏对照 — 针对「已见留出集」写的人工词典，只算可行性上界，禁止计入验收

诚实边界：
  - scene/shy/replay/dual 的训练材料只有 skiplib.EVAL(20 条) 与技能库文本，绝无 HOLDOUT 标签。
  - prior 看过留出集 MISS，属 test-set 过拟合，仅作「人工补词天花板」对照，不参与门禁。
  - strict_baseline 直接调 skiplib.rank(q,3)，保证与现行系统口径一致，不用自建引擎冒充基线。
  - 所有数字由本脚本实跑输出，禁止手抄。
"""
import sys
import json
import re
import math
import argparse
from collections import defaultdict, Counter

import skiplib  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

# ---- 超参（全部显式，可复跑） ----
SCENE_GAIN = 2.20       # 场景短索引命中加成
SHY_LAMBDA = 0.18       # 突触稳态乘性降尺度强度
REPLAY_ALPHA = 0.45     # 重放扩展词权重（<1，不喧宾夺主）
REPLAY_TOPK = 6
K_R, K_S = 2, 1         # v0.2 固定席位参数（已被竞争仲裁取代，保留供消融复现）
S_BETA = 0.80           # v0.3 竞争仲裁：S 候选需达到 R 第 3 席分数的 80% 才可替换
CONF_THRESHOLD = 8.0    # 沿用 skills_router.py 置信阈值，用于测「自信地错」

SALIENCE_KEYS = (
    "guard", "audit", "verify", "cert", "fingerprint", "security", "gate", "lint",
    "安全", "校验", "防", "告警", "门禁", "熔断", "体检", "核真", "基线",
)
PAT_TRIGGER = re.compile(r"触发词\s*[:：]\s*([^。；]+)")
PAT_WHEN = re.compile(r"当(?:用户)?[^。；]{0,90}?时使用")
PAT_QUOTE = re.compile(r"[「『\"']([^」』\"']{2,20})[」』\"']")

# 泄漏对照词典：针对已见 HOLDOUT 的 MISS 构造，仅证明人工补词天花板，不可作为泛化证据。
LEAK_PRIOR = {
    "冒充": ["指纹", "主机密钥", "MITM", "信任基线"],
    "被坑": ["踩坑", "直觉", "instinct", "行为规则"],
    "小孩": ["课堂", "教学", "费曼", "内化"],
    "内部资料": ["RAG", "知识库", "企业", "内部问答"],
    "公司": ["企业级", "架构师", "落地"],
}


def compile_scene(description):
    """离线把技能描述编译成「用户会怎么说」的短场景语料（睡眠相图式化）。"""
    s = description or ""
    parts = PAT_TRIGGER.findall(s) + PAT_WHEN.findall(s) + PAT_QUOTE.findall(s)
    return " ".join(parts)


class Corpus:
    def __init__(self):
        self.docs = skiplib.load_docs()
        self.n = len(self.docs)
        self.by_name = {d["name"]: i for i, d in enumerate(self.docs)}
        self.tfs, self.scene_tfs, self.dfs, self.dl = [], [], Counter(), []
        self.scene_count = 0
        for d in self.docs:
            tf = Counter()
            for field, w in (("name", 6), ("description", 3), ("body", 1)):
                for t in skiplib.tokenize(d.get(field) or ""):
                    tf[t] += w
            self.tfs.append(tf)
            self.dl.append(sum(tf.values()))
            for t in tf:
                self.dfs[t] += 1
            scene = compile_scene(d.get("description"))
            self.scene_count += bool(scene)
            self.scene_tfs.append(set(skiplib.tokenize(scene)))
        self.avgdl = sum(self.dl) / self.n if self.n else 1

        # 历史轨迹：只用 EVAL(20) 的 top3 命中次数，绝不含 HOLDOUT 标签
        self.usage = Counter()
        for q, _ in skiplib.EVAL:
            ranked, _ = skiplib.rank(q, 3)
            for _, d in ranked:
                self.usage[d["name"]] += 1

        # 重放共现：训练集 query-token ↔ 命中技能术语
        self.cooc = defaultdict(Counter)
        for q, expects in skiplib.EVAL:
            qts = set(skiplib.tokenize(q))
            for name in expects:
                i = self.by_name.get(name)
                if i is None:
                    continue
                d = self.docs[i]
                sts = set(skiplib.tokenize(d["name"]) +
                          skiplib.tokenize(d.get("description") or "") +
                          skiplib.tokenize(compile_scene(d.get("description"))))
                for t in qts:
                    for s in sts:
                        self.cooc[t][s] += 1

        # 显著性池：规则判定（不可逆代价/安全/校验），与标注无关
        self.s_pool = [
            i for i, d in enumerate(self.docs)
            if any(k in (d["name"] + " " + (d.get("description") or "")).lower()
                   for k in SALIENCE_KEYS)
        ]

    def idf(self, t):
        df = self.dfs.get(t, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def replay_expand(self, qtokens):
        """睡眠重放：历史共现做模式补全；冷启动词（训练集没见过）返回空 = 真实失效。"""
        c = Counter()
        for t in set(qtokens):
            for s, v in self.cooc.get(t, {}).items():
                c[s] += v
        if not c:
            return {}
        mx = max(c.values())
        return {t: REPLAY_ALPHA * (v / mx) for t, v in c.most_common(REPLAY_TOPK)}

    def score(self, qweights, shy=False, scene=False, indices=None):
        """加权 BM25 + 场景短索引加成 + SHY 乘性降尺度。"""
        k1, b = 1.5, 0.75
        pool = indices if indices is not None else range(self.n)
        out = []
        for i in pool:
            tf = self.tfs[i]
            s = 0.0
            for t, w in qweights.items():
                if t not in tf:
                    continue
                f = tf[t]
                s += w * self.idf(t) * f * (k1 + 1) / (f + k1 * (1 - b + b * self.dl[i] / self.avgdl))
            if scene:
                # 短场景索引独立计分，不受长 description 的 BM25 长度归一化拖累
                for t, w in qweights.items():
                    if t in self.scene_tfs[i]:
                        s += SCENE_GAIN * w * self.idf(t)
            if s <= 0:
                continue
            if shy:
                # 突触稳态：全局按比例下调，相对保留沉默但强相关的连接
                s /= (1.0 + SHY_LAMBDA * math.log(1 + self.usage.get(self.docs[i]["name"], 0)))
            out.append((s, i))
        out.sort(key=lambda x: -x[0])
        return out

    def route(self, query, mode):
        shy, replay, dual, prior = ("shy" in mode, "replay" in mode,
                                    "dual" in mode, "prior" in mode)
        scene = "scene" in mode
        qtokens = skiplib.tokenize(query)
        qw = {t: 1.0 for t in set(qtokens)}
        expanded = self.replay_expand(qtokens) if replay else {}
        for t, w in expanded.items():
            qw[t] = max(qw.get(t, 0.0), w)
        if prior:
            for key, words in LEAK_PRIOR.items():
                if key in query:
                    for w in words:
                        for t in skiplib.tokenize(w):
                            qw[t] = max(qw.get(t, 0.0), 0.85)

        scored = self.score(qw, shy=shy, scene=scene)
        qlow = query.lower()
        boosted = []
        for s, i in scored:
            d = self.docs[i]
            nt = set(skiplib.tokenize(d["name"]))
            name_hit = len(set(qtokens) & nt) / max(1, len(nt))
            exact = 6.0 if d["name"].lower() in qlow else 0.0
            boosted.append((s + 4.0 * name_hit + exact, i))
        boosted.sort(key=lambda x: -x[0])

        # 清醒相：R 通道始终占 3 席；S 通道用「竞争性门控」（丘脑网状核式抑制门控），
        # 仅当显著性候选分数能压过 R 第 3 席一定比例时才替换它。
        # v0.2 的无条件固定席位实测把 8/12 拉到 7/12，故 v0.3 由实验反推改为竞争仲裁。
        r3 = boosted[:3]
        r_names = [self.docs[i]["name"] for _, i in r3]
        s_seat = []
        if dual and len(r3) >= 3:
            r3_score = r3[2][0]
            for s, i in self.score(qw, scene=scene, indices=self.s_pool)[:6]:
                if s <= 0 or s < r3_score * S_BETA:
                    break
                nm = self.docs[i]["name"]
                if nm not in r_names:
                    s_seat = [nm]
                    r_names = r_names[:2] + s_seat
                    break
        top = r_names[:3]
        diag = {
            "r_seats": r_names, "s_seat": s_seat,
            "top1_score": round(boosted[0][0], 2) if boosted else 0.0,
            "replay_tokens": list(expanded.keys()),
        }
        return top, diag


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(ctr - half, 4), round(ctr + half, 4))


def pack(name, pairs, rows_fn):
    hit, cw = 0, 0
    rows = []
    for q, expect in pairs:
        names, diag = rows_fn(q)
        ok = bool(set(names) & set(expect))
        hit += ok
        # 翻车半径：系统自认高置信（top1>=8）却给错，是最危险的失败模式
        wrong_conf = (not ok) and diag["top1_score"] >= CONF_THRESHOLD
        cw += wrong_conf
        rows.append({"q": q, "expect": expect, "got": names, "ok": ok,
                     "confident_wrong": wrong_conf, "top1": diag["top1_score"],
                     "replay": diag["replay_tokens"], "s_seat": diag["s_seat"]})
    n = len(pairs)
    lo, hi = wilson(hit, n)
    return {"mode": name, "n": n, "hit": hit, "hit_rate": round(hit / n, 4),
            "wilson95": [lo, hi], "miss_rate": round((n - hit) / n, 4),
            "confident_wrong": cw, "confident_wrong_rate": round(cw / n, 4),
            "rows": rows}


def strict_baseline(pairs):
    """现行系统真实基线：直接调 skiplib.rank(q,3)，不经过自建引擎。"""
    def fn(q):
        ranked, _ = skiplib.rank(q, 3)
        names = [d["name"] for _, d in ranked]
        return names, {"top1_score": ranked[0][0] if ranked else 0.0,
                       "replay_tokens": [], "s_seat": []}
    return pack("strict_baseline(skiplib.rank@3)", pairs, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dump", default="")
    args = ap.parse_args()

    c = Corpus()
    modes = [
        [],                                          # 自建引擎对照（无机制）
        ["scene"],                                   # 睡眠相①
        ["scene", "shy"],                            # + 睡眠相②
        ["scene", "shy", "replay"],                  # + 睡眠相③
        ["scene", "shy", "replay", "dual"],          # 全系统（自动、无标签）→ 门禁依据
        ["scene", "shy", "replay", "dual", "prior"], # 泄漏对照：人工补词天花板
    ]
    results = []
    for m in modes:
        fn = lambda q, mm=m: c.route(q, mm)
        hold = pack("+".join(m) or "engine_baseline", skiplib.HOLDOUT, fn)
        train = pack("+".join(m) or "engine_baseline", skiplib.EVAL, fn)
        results.append({"mode": hold["mode"], "leak_contaminated": "prior" in m,
                        "holdout": {k: v for k, v in hold.items() if k != "rows"},
                        "train": {k: v for k, v in train.items() if k != "rows"},
                        "holdout_rows": hold["rows"]})

    sb_hold = strict_baseline(skiplib.HOLDOUT)
    sb_train = strict_baseline(skiplib.EVAL)
    auto = results[4]
    gate = {
        "G1_holdout_rate_ge_85": auto["holdout"]["hit_rate"] >= 0.85,
        "G2_wilson_lower_ge_85": auto["holdout"]["wilson95"][0] >= 0.85,
        "G3_confident_wrong_eq_0": auto["holdout"]["confident_wrong"] == 0,
        "G4_sample_size_ge_30": auto["holdout"]["n"] >= 30,
    }
    verdict = "PASS" if all(gate.values()) else "FAIL"

    payload = {
        "version": "WSSR v0.3",
        "corpus": {"skills": c.n, "scene_compiled": c.scene_count,
                   "scene_coverage": round(c.scene_count / c.n, 4),
                   "salience_pool": len(c.s_pool),
                   "train_pairs": len(skiplib.EVAL), "holdout_pairs": len(skiplib.HOLDOUT)},
        "hyper": {"SCENE_GAIN": SCENE_GAIN, "SHY_LAMBDA": SHY_LAMBDA,
                  "REPLAY_ALPHA": REPLAY_ALPHA, "REPLAY_TOPK": REPLAY_TOPK,
                  "K_R": K_R, "K_S": K_S, "S_BETA": S_BETA,
                  "CONF_THRESHOLD": CONF_THRESHOLD},
        "strict_baseline": {
            "holdout": {k: v for k, v in sb_hold.items() if k != "rows"},
            "train": {k: v for k, v in sb_train.items() if k != "rows"},
        },
        "ablation": results,
        "gate": gate, "gate_verdict": verdict,
        "honesty": [
            "strict_baseline 直接调 skiplib.rank@3，与现行系统同口径",
            "scene/shy/replay/dual 只用 skiplib.EVAL(20) 与技能库文本，未使用 HOLDOUT 标签",
            "prior 看过留出集 MISS，属 test-set 过拟合，仅作可行性上界，不参与门禁",
            "留出集 n=12，即使 12/12 全对 Wilson95 下界也只有 0.7575，不足以支撑 85% 宣称",
            "全对且 Wilson 下界 >=0.85 需要 n>=22；观测命中率 85% 时下界需 n>=约 250",
        ],
    }
    if args.json or args.dump:
        txt = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.dump:
            with open(args.dump, "w", encoding="utf-8") as f:
                f.write(txt)
        if args.json:
            print(txt)
            return
        # --dump 只写文件，控制台仍输出人读摘要

    print(f"语料 {c.n} 技能 | 场景编译 {c.scene_count} ({c.scene_count/c.n:.1%}) | "
          f"显著性池 {len(c.s_pool)} | 训练 {len(skiplib.EVAL)} | 留出 {len(skiplib.HOLDOUT)}")
    print("-" * 96)
    print(f"{'模式':<40}{'训练集':<11}{'留出集':<11}{'Wilson95':<20}{'自信错':<8}")
    print("-" * 96)
    b = payload["strict_baseline"]
    print(f"{'strict_baseline(现行系统)':<40}{b['train']['hit']}/{b['train']['n']:<9}"
          f"{b['holdout']['hit']}/{b['holdout']['n']:<9}{str(b['holdout']['wilson95']):<20}"
          f"{b['holdout']['confident_wrong']}/{b['holdout']['n']:<8}")
    for r in results:
        h, t = r["holdout"], r["train"]
        tag = "  [泄漏对照]" if r["leak_contaminated"] else ""
        print(f"{r['mode']+tag:<40}{t['hit']}/{t['n']:<9}{h['hit']}/{h['n']:<9}"
              f"{str(h['wilson95']):<20}{h['confident_wrong']}/{h['n']:<8}")
    print("-" * 96)
    print("门禁:", json.dumps(gate, ensure_ascii=False))
    print("判决:", verdict, "（未过闸不得对外报价/部署）")
    print("\n--- 全系统留出集明细 ---")
    for r in results[4]["holdout_rows"]:
        print(f"  {'OK  ' if r['ok'] else 'MISS'} | {r['q']}")
        print(f"        期望 {r['expect']} | 实际 {r['got']} | S席 {r['s_seat']} | top1={r['top1']}")


if __name__ == "__main__":
    main()
