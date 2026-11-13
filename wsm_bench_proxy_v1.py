# -*- coding: utf-8 -*-
"""wsm_bench_proxy_v1.py — WSM V1「同口径代理对照实验」本地实跑 harness

背景（诚实口径，务必读懂）：
  外部三基线 context-mode / context-router / skill-weave 本地【无源码】，严禁 1:1 复现或编造头对头。
  三者共同核心 = BM25/FTS5 词法路由 + 级联；本地 skiplib.rank@3 正是该公共机制的【代理基线】。
  故本 harness 在【同一冻结盲测集 BLIND-100】上跑三方：
    (1) WSM   = wssr_v05.WSSR 全系统（gen+shy+replay+弃权+警示）
    (2) strict_baseline = skiplib.rank@3 纯词法/BM25 代理（复刻三外部项目公共机制）
    (3) full_resident    = 全量技能描述常驻控制组（token 成本上界；准确率本地不可实跑，标 N/A）

分层口径（防口径混淆）：
  A+B 层(n=80) 路由命中题：三方 hit@3 / hit@1 公平对比（主对照）。
  C   层(n=20) 应弃权题  ：仅 WSM 有弃权机制；strict_baseline/full_resident 无弃权动作，
                            标「结构缺失/不适用」，绝不把它们恒不弃权包装成"精度失败"去对比。
  自主率两口径：含兜底(=hit@3，弃权后人工兜底仍算命中) vs 自主(=命中且未弃权)。
  token 三口径：全量目录 / top3 候选 / 端到端(top3+1篇)。注意 token 节省是「检索式路由 vs 全量常驻」
                的共同优势，非 WSM 相对词法基线的优势（两者都只加载 top3）——不夸大。

所有数字实跑产出，禁止手抄。复现命令：
  python wsm_bench_proxy_v1.py
输出：wsm_bench_proxy_v1.json（本任务唯一原始结果文件，不覆盖任何历史回执）。
"""
import sys
import os
import json
import time
import statistics
from pathlib import Path
from datetime import datetime

import skiplib
from wssr_v05 import (WSSR, evaluate, auto_abstain, gold_adversarial,
                      ABSTAIN_MARGIN, CONF_THRESHOLD, wilson)
from wssr_data import BLIND40
import blindgen  # 冻结 BLIND100；绝不调用其 main（会覆盖历史 blind100_run.json）

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
PY = "python"


# ---------------------------------------------------------------- token 三口径
def token_cost():
    """复刻 skiplib.py cost() 口径（est_tokens 保守估），返回精确浮点，便于审计。"""
    docs = skiplib.load_docs()
    cat = sum(skiplib.est_tokens(d["name"] + " " + d["description"]) for d in docs)
    cat_bpe = sum(skiplib.est_tokens_bpe(d["name"] + " " + d["description"]) for d in docs)
    full = sum(skiplib.est_tokens(d["name"] + " " + d["description"] + " " + d["body"]) for d in docs)
    top3_sizes = []
    for q, _ in skiplib.EVAL:
        ranked, _ = skiplib.rank(q, 3)
        top3_sizes.append(sum(skiplib.est_tokens(d["name"] + " " + d["description"]) + 8
                              for _, d in ranked))
    top3_avg = sum(top3_sizes) / len(top3_sizes)
    body_sizes = []
    for d in docs:
        txt = open(d["path"], encoding="utf-8-sig", errors="replace").read()
        body_sizes.append(skiplib.est_tokens(txt))
    body_avg = sum(body_sizes) / len(body_sizes)
    e2e = top3_avg + body_avg
    return {
        "source": "skiplib.py cost() / est_tokens()（保守估：CJK 1 token/字，拉丁 1.3/词）",
        "reproduce": "python skiplib.py cost",
        "skills_n": len(docs),
        "full_resident_catalog_tokens": cat,          # 口径①：全量 name+description 常驻
        "full_resident_catalog_tokens_bpe": cat_bpe,   # cl100k 估，仅参考
        "full_corpus_with_body300_tokens": full,
        "top3_candidate_tokens": round(top3_avg),      # 口径②：top3 候选（20 条 EVAL 查询均值，含每条 8 token 格式开销）
        "skill_body_avg_tokens": round(body_avg),      # 加载 1 篇完整 SKILL.md 均值
        "end_to_end_tokens": round(e2e),               # 口径③：端到端 = top3 + 1 篇
        "saving_top3_vs_catalog": round(1 - top3_avg / cat, 4),
        "saving_e2e_vs_catalog": round(1 - e2e / cat, 4),
        "note": ("token 节省是『检索式路由 vs 全量常驻』的共同优势，WSM 与 strict_baseline 都只加载 top3，"
                 "此口径非 WSM 相对词法基线的差异化优势。全部数字由本次对自包含合成语料实跑产出。"),
    }


# ---------------------------------------------------------------- 三方逐题评估
def route_wsm(c, q, thr):
    names, diag = c.route(q, gen=True, shy=True, replay=True,
                          abstain_top1=thr, abstain_margin=ABSTAIN_MARGIN, warn=True)
    return names, diag


def route_strict(q):
    """词法代理基线：直接调 skiplib.rank@3（与 wssr_v05.strict_baseline 同口径）。"""
    ranked, use_fts = skiplib.rank(q, 3)
    names = [d["name"] for _, d in ranked]
    t1 = ranked[0][0] if ranked else 0.0
    return names, t1, use_fts


def eval_blind100(c, thr):
    """同一冻结集 BLIND-100 上，WSM 与 strict_baseline 逐题同口径对照。"""
    items = blindgen.BLIND100
    nA = sum(1 for x in items if x["layer"] == "A")
    nB = sum(1 for x in items if x["layer"] == "B")
    nC = sum(1 for x in items if x["layer"] == "C")
    assert (nA, nB, nC) == (60, 20, 20), (nA, nB, nC)

    # 标注校验：期望技能是否仍在当前 180 库（技能库变动会污染数字，须如实记录）
    missing = []
    for it in items:
        for nm in it["expect"]:
            if c.by_name.get(nm) is None:
                missing.append((it["q"][:20], nm))

    wsm_ab = {"hit3": 0, "hit1": 0, "cw": 0, "abstain": 0, "autonomous": 0, "n": 0}
    sb_ab = {"hit3": 0, "hit1": 0, "cw": 0, "abstain": 0, "autonomous": 0, "n": 0}
    wsm_c = {"correct_abstain": 0, "false_confident": 0, "n": 0}
    sb_c = {"correct_abstain": 0, "false_confident": 0, "n": 0}
    wsm_pseudo = 0  # 伪弃权：弃权但 top3 已含期望技能
    rows = []
    use_fts_flag = None

    for it in items:
        q, expect, layer = it["q"], set(it["expect"]), it["layer"]
        # --- WSM ---
        wn, wd = route_wsm(c, q, thr)
        w_ok3 = bool(set(wn) & expect)
        w_ok1 = bool(wn and wn[0] in expect)
        w_ab = wd["abstain"]
        w_top1 = wd["top1"]
        # --- strict_baseline ---
        sn, s_t1, ufts = route_strict(q)
        use_fts_flag = ufts
        s_ok3 = bool(set(sn) & expect)
        s_ok1 = bool(sn and sn[0] in expect)

        if layer in ("A", "B"):
            wsm_ab["n"] += 1
            sb_ab["n"] += 1
            wsm_ab["hit3"] += w_ok3
            wsm_ab["hit1"] += w_ok1
            wsm_ab["abstain"] += w_ab
            wsm_ab["autonomous"] += (w_ok3 and not w_ab)
            wsm_ab["cw"] += (not w_ok3) and (not w_ab) and w_top1 >= CONF_THRESHOLD
            if w_ab and w_ok3:
                wsm_pseudo += 1
            sb_ab["hit3"] += s_ok3
            sb_ab["hit1"] += s_ok1
            sb_ab["autonomous"] += s_ok3          # 无弃权，自主==含兜底
            sb_ab["cw"] += (not s_ok3) and s_t1 >= CONF_THRESHOLD
        else:  # C：成功=弃权
            wsm_c["n"] += 1
            sb_c["n"] += 1
            wsm_c["correct_abstain"] += w_ab
            wsm_c["false_confident"] += (not w_ab)
            # strict_baseline 无弃权机制：结构上恒不弃权
            sb_c["correct_abstain"] += 0
            sb_c["false_confident"] += 1
        rows.append({
            "q": q, "layer": layer, "expect": it["expect"], "human": it["human"],
            "wsm": {"got": wn, "ok3": w_ok3, "ok1": w_ok1, "abstain": w_ab, "top1": w_top1},
            "strict": {"got": sn, "ok3": s_ok3, "ok1": s_ok1, "top1": round(s_t1, 2)},
        })

    def finish(d, nkey="n"):
        n = d[nkey]
        d["hit3_rate"] = round(d["hit3"] / n, 4) if n else 0
        d["hit1_rate"] = round(d["hit1"] / n, 4) if n else 0
        if "hit3" in d:
            d["wilson95_hit3"] = list(wilson(d["hit3"], n))
            d["autonomous_rate"] = round(d.get("autonomous", 0) / n, 4)
            d["with_fallback_rate"] = d["hit3_rate"]   # 含兜底 == hit@3
            d["abstain_rate"] = round(d.get("abstain", 0) / n, 4)
            d["confident_wrong_rate"] = round(d.get("cw", 0) / n, 4)
        return d
    finish(wsm_ab); finish(sb_ab)
    wsm_c["abstain_rate"] = round(wsm_c["correct_abstain"] / wsm_c["n"], 4)
    sb_c["abstain_rate"] = round(sb_c["correct_abstain"] / sb_c["n"], 4)
    wsm_ab["pseudo_abstain"] = wsm_pseudo

    # 全体 100（与 blindgen.run_once 口径一致：k = AB hit3 + C 正确弃权）
    k_all = wsm_ab["hit3"] + wsm_c["correct_abstain"]
    overall = {
        "n": 100, "k": k_all,
        "overall_rate": round(k_all / 100, 4),
        "wilson95_all100": list(wilson(k_all, 100)),
        "G2_pass_all100": wilson(k_all, 100)[0] >= 0.75,
        "AB_wilson95": list(wilson(wsm_ab["hit3"], 80)),
        "G2_pass_AB": wilson(wsm_ab["hit3"], 80)[0] >= 0.75,
        "note": "k = A+B 层 hit@3 + C 层正确弃权；与 blind100_run.json 历史 k=89 交叉验证口径一致",
    }
    return {
        "blind_set": "blindgen.BLIND100（冻结 6:2:2，同作者闭环内部盲测，非真第三方）",
        "label_protocol": "先题后标，expect 按功能需求；C 层 expect=[] 应弃权",
        "layer_counts": {"A": nA, "B": nB, "C": nC},
        "missing_labels": missing,
        "fts5_enabled": use_fts_flag,
        "AB_router_n80": {
            "note": "A+B 路由命中题，三方公平对比主口径；分母 n=80",
            "WSM_v05": wsm_ab,
            "strict_baseline_lexical_proxy": sb_ab,
            "full_resident_control": {
                "accuracy": "N/A",
                "reason": "全量常驻无检索/无 LLM 选择动作；本地为纯检索器，无 LLM 端到端评测能力，命中率不可实跑，禁止编造。仅作 token 成本上界对照。",
            },
        },
        "C_abstain_discipline_n20": {
            "note": "C 层成功=引擎弃权；strict_baseline/full_resident 无弃权机制（结构缺失，非精度失败）",
            "WSM_v05": wsm_c,
            "strict_baseline_lexical_proxy": {
                **sb_c,
                "has_abstain_mechanism": False,
                "reason": "纯词法 rank 恒返回 top3，从不弃权；C 层 20/20 必然自信路由。此为机制差异，非同口径精度对撞。",
            },
            "full_resident_control": {"has_abstain_mechanism": False, "accuracy": "N/A"},
        },
        "overall_100_WSM": overall,
        "rows": rows,
    }


# ---------------------------------------------------------------- 门禁 G1–G5
def gates(c, thr, bl100):
    """两套门禁并列，绝不混淆：BLIND40(v0.5 定义 G1–G5) 与 BLIND100(发表级 G2)。"""
    bl40 = evaluate(c, [(b["q"], b["expect"]) for b in BLIND40],
                    gen=True, shy=True, replay=True, abstain_top1=thr,
                    abstain_margin=ABSTAIN_MARGIN, warn=True, mode="BLIND40")
    g5 = gold_adversarial()["robust_rate"]
    g40 = {
        "G1_blind_hit3_ge_85": bl40["hit_rate"] >= 0.85,
        "G2_wilson_lower_ge_75": bl40["wilson95"][0] >= 0.75,
        "G3_confident_wrong_eq_0": bl40["confident_wrong"] == 0,
        "G3b_confident_wrong_rate_le_5pct": bl40["confident_wrong"] / bl40["n"] <= 0.05,
        "G4_sample_size_ge_30": bl40["n"] >= 30,
        "G5_gold_robust_ge_85": g5 >= 0.85,
    }
    return {
        "definitions_source": {
            "BLIND40_G1_G5": "wssr_v05.py --blind --gold（gate_inputs）",
            "BLIND100_G2": "blindgen.py / blind_kit/score_blind.py（全100 Wilson 下界 ≥0.75）",
        },
        "BLIND40_v05_gate": {
            "n": bl40["n"], "hit3": bl40["hit"], "hit3_rate": bl40["hit_rate"],
            "wilson95": bl40["wilson95"], "hit1_rate": bl40["hit1_rate"],
            "confident_wrong": bl40["confident_wrong"],
            "abstain": bl40["abstain"], "autonomous": bl40["autonomous"],
            "gold_robust_rate": g5,
            "gates": g40, "verdict": "PASS" if all(g40.values()) else "FAIL",
        },
        "BLIND100_publish_gate": {
            "G2_wilson_all100_ge_75": bl100["overall_100_WSM"]["G2_pass_all100"],
            "observed_wilson_lower_all100": bl100["overall_100_WSM"]["wilson95_all100"][0],
            "G2_wilson_AB_ge_75": bl100["overall_100_WSM"]["G2_pass_AB"],
            "observed_wilson_lower_AB": bl100["overall_100_WSM"]["AB_wilson95"][0],
        },
    }


# ---------------------------------------------------------------- 延迟实跑
def latency(c, items, thr):
    queries = [it["q"] for it in items]
    rounds = 5

    def measure(fn):
        per_round = []
        for _ in range(rounds):
            t0 = time.perf_counter()
            for q in queries:
                fn(q)
            per_round.append((time.perf_counter() - t0) / len(queries) * 1000)  # ms/query
        return round(statistics.mean(per_round), 3), round(max(per_round), 3)

    wsm_mean, wsm_p95 = measure(lambda q: route_wsm(c, q, thr))
    sb_mean, sb_p95 = measure(lambda q: route_strict(q))
    return {
        "source": "本 harness 实跑（time.perf_counter，BLIND100 全部 100 题 ×5 轮均值）",
        "queries": len(queries), "rounds": rounds,
        "WSM_route_ms_per_query_mean": wsm_mean, "WSM_route_ms_per_query_max_round": wsm_p95,
        "strict_baseline_rank_ms_per_query_mean": sb_mean,
        "strict_baseline_rank_ms_per_query_max_round": sb_p95,
        "historical_scale_ref": {
            "source": "scale_report.json（N=200→500 合成噪声技能压测，历史回执，非本次实跑）",
            "latency_ms_avg_N200": 4.11, "latency_ms_avg_N500": 7.11,
            "catalog_tokens_N200": 24057, "catalog_tokens_N500": 48527,
            "top3_tokens_avg_stable": "398–401（不随 N 增长，在线 O(1) 实证）",
        },
    }


def main():
    c = WSSR()
    dev = [(q, e) for q, e in skiplib.EVAL] + [(q, e) for q, e in skiplib.HOLDOUT]
    auto, _ = auto_abstain(c, dev)
    thr = auto[0] if auto else None

    tc = token_cost()
    bl100 = eval_blind100(c, thr)
    gt = gates(c, thr, bl100)
    lat = latency(c, blindgen.BLIND100, thr)

    # 确定性双跑（B6 sorted 化保障）：WSM 逐行 ok/abstain 签名一致
    sig1 = [(r["wsm"]["ok3"], r["wsm"]["abstain"]) for r in bl100["rows"]]
    c2 = WSSR()
    bl100_b = eval_blind100(c2, thr)
    sig2 = [(r["wsm"]["ok3"], r["wsm"]["abstain"]) for r in bl100_b["rows"]]
    deterministic = sig1 == sig2 and bl100["overall_100_WSM"]["k"] == bl100_b["overall_100_WSM"]["k"]

    payload = {
        "meta": {
            "title": "WSM V1 同口径代理对照实验（本地实跑原始结果）",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "python": sys.version.split()[0],
            "python_path": "python (managed)",
            "package_dir": HERE.name,
            "cwd": ".",
            "abstain_threshold_thr": thr,
            "conf_threshold": CONF_THRESHOLD,
            "deterministic_double_run": deterministic,
        },
        "honesty": [
            "外部三基线 context-mode/context-router/skill-weave 本地无源码，未做 1:1 复现；strict_baseline=skiplib.rank@3 仅为三者公共机制(BM25/FTS5 词法路由)的代理基线。",
            "外部 README 宣称数字(98–99% fewer bytes / 96% fewer tokens / top-1 69.6%)只可作公开宣称引用值，绝非本实验头对头实测。",
            "BLIND-100 为同作者闭环内部盲测（同作者出题+标注+同引擎评分），非真第三方；统计价值是收窄 Wilson 区间，偏差消除需外部出题。",
            "C 层应弃权题：strict_baseline/full_resident 无弃权机制，标结构缺失，不当作同口径精度对撞。",
            "token 节省为『检索式路由 vs 全量常驻』共同优势，非 WSM 相对词法基线的差异化优势。",
            "本次实验全部基于自包含合成语料，数字由实跑产出，不引用任何历史值；语料与题面经一致性映射与脱敏，不含私有资产。",
        ],
        "token_cost_three_metrics": tc,
        "three_way_blind100": {k: v for k, v in bl100.items() if k != "rows"},
        "gates": gt,
        "latency": lat,
        "blind100_rows": bl100["rows"],
    }
    out = "wsm_bench_proxy_v1.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # ---- 控制台摘要 ----
    ab = bl100["AB_router_n80"]
    w, s = ab["WSM_v05"], ab["strict_baseline_lexical_proxy"]
    print(f"语料 {tc['skills_n']} | thr={thr} | FTS5={bl100['fts5_enabled']} | 确定性双跑一致={deterministic}")
    print("=" * 92)
    print("【token 三口径 · skiplib.cost 实跑】")
    print(f"  全量目录 {tc['full_resident_catalog_tokens']:,} → top3 候选 {tc['top3_candidate_tokens']} "
          f"→ 端到端 {tc['end_to_end_tokens']} | 省(top3) {tc['saving_top3_vs_catalog']:.2%} "
          f"省(端到端) {tc['saving_e2e_vs_catalog']:.2%}")
    print("=" * 92)
    print("【BLIND-100 · A+B 路由题 n=80 · 三方对照主口径】")
    print(f"  {'指标':<20}{'WSM v0.5':<20}{'strict_baseline(词法代理)':<28}{'全量常驻':<12}")
    print(f"  {'hit@3':<20}{f'{w['hit3']}/80 = {w['hit3_rate']:.1%}':<20}{f'{s['hit3']}/80 = {s['hit3_rate']:.1%}':<28}{'N/A':<12}")
    print(f"  {'hit@1':<20}{f'{w['hit1']}/80 = {w['hit1_rate']:.1%}':<20}{f'{s['hit1']}/80 = {s['hit1_rate']:.1%}':<28}{'N/A':<12}")
    print(f"  {'Wilson95(hit@3)':<20}{str(w['wilson95_hit3']):<20}{str(s['wilson95_hit3']):<28}{'—':<12}")
    print(f"  {'含兜底率(=hit@3)':<20}{f'{w['with_fallback_rate']:.1%}':<20}{f'{s['with_fallback_rate']:.1%}':<28}{'—':<12}")
    print(f"  {'自主率':<20}{f'{w['autonomous_rate']:.1%}':<20}{f'{s['autonomous_rate']:.1%}':<28}{'—':<12}")
    print(f"  {'弃权率/伪弃权':<20}{f'{w['abstain_rate']:.1%} / {w['pseudo_abstain']}':<20}{'0(无弃权机制)':<28}{'—':<12}")
    print(f"  {'自信错率':<20}{f'{w['confident_wrong_rate']:.1%}':<20}{f'{s['confident_wrong_rate']:.1%}':<28}{'—':<12}")
    print("=" * 92)
    print("【BLIND-100 · C 应弃权题 n=20 · 弃权纪律】")
    wc = bl100["C_abstain_discipline_n20"]["WSM_v05"]
    sc = bl100["C_abstain_discipline_n20"]["strict_baseline_lexical_proxy"]
    print(f"  WSM 正确弃权 {wc['correct_abstain']}/20 = {wc['abstain_rate']:.1%} | 自信误路由 {wc['false_confident']}")
    print(f"  strict_baseline 正确弃权 {sc['correct_abstain']}/20（无弃权机制，结构缺失，非精度对撞）")
    print("=" * 92)
    ov = bl100["overall_100_WSM"]
    print(f"【BLIND-100 全体 n=100】WSM k={ov['k']}/100 = {ov['overall_rate']:.1%} "
          f"Wilson{ov['wilson95_all100']} | G2(全100下界≥0.75)={ov['G2_pass_all100']}")
    g = gt["BLIND40_v05_gate"]
    print(f"【门禁 BLIND40 v0.5】{g['verdict']} | G1..G5={list(g['gates'].values())}")
    print(f"  明细 hit@3={g['hit3']}/40 Wilson{g['wilson95']} 自信错={g['confident_wrong']} G5金标={g['gold_robust_rate']:.0%}")
    print(f"【门禁 BLIND100】G2(全100)={gt['BLIND100_publish_gate']['G2_wilson_all100_ge_75']} "
          f"下界={gt['BLIND100_publish_gate']['observed_wilson_lower_all100']}")
    print(f"【延迟实跑】WSM {lat['WSM_route_ms_per_query_mean']} ms/题 | "
          f"strict {lat['strict_baseline_rank_ms_per_query_mean']} ms/题（100题×5轮）")
    print(f"【标注校验】缺失标签 {len(bl100['missing_labels'])} 条")
    print("=" * 92)
    print("已写:", out)


if __name__ == "__main__":
    main()
