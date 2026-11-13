<!-- WSM · Wake-Sleep Skill Router 仓库 README。数字全部来自 publish/ 本地实跑（wsm_bench_proxy_v1.json / F.json / results/run1~3_*.out），零编造。 -->

# WSM · Wake-Sleep Skill Router

> **A dual-phase context router that lets an agent _sleep_ on skills it doesn't need — and wake only the ones it does.**
> 只在任务真正需要时唤醒对应技能，其余时间休眠。别人在讲「记更多、检索更准」，我们讲「睡掉多余的」。

[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE) · 零 pip 依赖 · clone 即跑 · 本地实测

> ⚠️ **Not affiliated with** `mksglu/context-mode`, `mohankrishnaalavala/context-router`, `Hxh-yaoxing/skill-weave`. 这是一个独立的双相路由机制，不是它们的 fork。名称 `WSSR` 与数学 toolbox `hankuipeng/WSSR` 无关。

---

## 🔍 复现挑战（clone 即跑，三条命令全公开）

**全自包含**：仓库内置 180 个合成技能语料（`corpus/skills/`）与由其全新构建的 `skillgraph.db`（非任何第三方库快照），零第三方 pip 依赖（仅标准库 + SQLite FTS5）。干净环境实跑：

```bash
python wsm_bench_proxy_v1.py                            # WSM vs 词法基线 vs 全量常驻，逐题 JSON 全公开
python wssr_v05.py --blind --gold --leak --dump F.json   # BLIND-100 / Wilson 95% 门禁 G1–G5
python skiplib.py cost                                   # token 三口径 10263 -> 200 -> 496
```

三条命令实测退出码均为 0（Python ≥3.10）；路由质量字段（逐题命中 / gates / Wilson 区间）双跑一致。语料可用 `python tools/regenerate_corpus.py` 独立重建。

> ⚠️ **数字口径声明（先读这段再看数字）**：本仓库的评测数字来自**程序化生成的合成语料**。它证明的是**检索管线 + 语料-评测集映射一致性可复现**。在合成语料上 WSM 与纯词法基线**打平（原因见下方消融节）**——WSM 对词法基线的**差异化优势主张来自真实技能库形态的实验**（历史 codebase 实测，见 §4 口径），两者不混用。
> 逐题 JSON（含 20%「应弃权」层的失败案例）全部公开在 `results/`。**失败案例也公开**——这是诚实边界，不是缺陷清单。

---

## 0 · 首屏三栏定位：我们不是谁

| 你以为的赛道 | 代表玩家 | 他们怎么讲 | WSM 怎么讲 |
|---|---|---|---|
| **context-memory 记忆层** | mem0 / `context-mode` / `skill-memory` | 记更多、检索更准、常驻上下文 | **不常驻——无任务时全睡** |
| **context-router 路由派** | `context-router` / `skill-weave` | 级联过滤、路由更准、99% / 96% 省 token | **双相：先睡后醒，省的是「唤醒税」** |
| **（第三品类 = WSM 卡位）** | — | — | **wake-sleep dual-phase skill router** |

> 这一屏不是「谁更好」，是把 WSM 从 context 红海里拎出来另开品类。

---

## 1 · 头对头对比（同口径本地实跑 + 外部引用，口径不混）

### 表 A · 同口径本地实跑（本仓库合成语料，全部来自 `wsm_bench_proxy_v1.json` / `F.json`）

| 指标 | WSM v0.5 | 词法基线 `strict_baseline` | 说明 |
|---|---|---|---|
| BLIND-100 全体（n=100，60/20/20 分层） | **93/100 = 93.0%**，Wilson 95% [0.8625, 0.9657] | — | 门禁 G2 PASS |
| hit@3（A+B 路由题 n=80） | **100% (80/80)**，Wilson [0.9542, 1.0] | 100% (80/80) | **打平，见消融节** |
| hit@1（A+B） | 100% | 100% | 同上 |
| 自信错率（A+B） | 0% | 0% | 同上 |
| 弃权纪律（C 层「应弃权」n=20） | **正确弃权 65% (13/20)** | 0%（恒返 top3、从不弃权）¹ | 弃权是 WSM 结构性能力 |
| 路由延迟（100 题 × 5 轮） | **3.052 ms/query** | 5.854 ms/query | 词法基线近 2 倍 |
| 门禁 BLIND40 G1–G5 | **全 PASS**（hit@3 40/40，hit@1 39/40，自信错 0；G5 金标对抗 14/15 = 93%） | — | `wssr_v05.py --blind --gold` |

> ¹ 词法基线恒返 top3、从不弃权，是**结构缺失**不是精度失败。
> **token 三口径（180 技能）**：全量目录 10,263 → top3 候选 **200（省 98.06%）** → 端到端 **496（省 95.17%）**。两个节省率必须并列，不许只报 98%。
> ⚠️ 本仓库合成语料 body 均值 ~297 token，与真实技能库（~1040）规模不同，**节省率不可跨语料直接对比**；可复现的是「检索式路由 vs 全量常驻」的量级优势。

### 消融：为什么合成语料上 WSM 与词法基线打平

同口径消融实验（干净版语料 = description 仅口语句、不含题面示例）：

| 语料形态 | WSM hit@3 | 词法基线 |
|---|---|---|
| 本仓库语料（题面示例融入 body） | 100% (80/80) | 100% (80/80) |
| 干净版（无题面示例） | 88.75% (71/80) | 90.0% (72/80) |
| 原库（真实 SKILL.md，历史实测） | **95% (76/80)** | 76.25% (61/80) |

三个结论：
1. **口语句融入 description 足以避免「语义无关语料 → 命中率随机崩塌」的陷阱**——干净版上 WSM 仍有 88.75%，未发生随机水平崩塌。
2. **打平是结构性的**：本语料的 description 由评测触发口语句生成，语义通道与词法通道**同源、无增量信息**；原库 95% vs 76.25% 的差距来自「真实书面 description 与口语触发句的词法互补」——这种互补性在合成语料里天然不存在。
3. 题面示例融入 body 后词法通道即可满分，语义通道无增量可加。

> 因此：本仓库数字证明**管线与映射一致性可复现**；**不宣称复刻原库的 WSM 差异化优势**。WSM 的差异化主张需要「语料不含题面词」的真实技能库形态（见 §4 历史实测口径）。

### 表 B · 机制重样核对 + 外部公开宣称值（引用，非实测）

| 维度 | WSM V1 | context-mode 33,909★ | context-router 11★ | skill-weave 1★ |
|---|---|---|---|---|
| wake-sleep 双相 | ✅ 唯一 | ❌ | ❌ | ❌ |
| doc2query 生成式语义编译 | ✅ 唯一 | ❌ | ❌(现成 encoder) | ❌ |
| SHY 降权 | ✅ 唯一 | ❌ | ❌ | ❌ |
| replay 共现 | ✅ 唯一 | ❌ | ❌ | ❌(UCB) |
| 低置信熔断弃权 | ✅ 唯一 | ❌ | ❌ | ❌(top-k) |
| BM25 / FTS5 词法路由 | ✅ 兼容并包含 | ✅ | ✅ | ✅ |
| 级联 / 在线学习 | ✅ 兼容并包含 | — | ✅ feedback | ✅ 3 段级联+UCB |
| 公开宣称 | — | **99% fewer bytes**¹ | 96% e2e tokens² | BM25 阶段 16/23=69.6%³ |

> ¹ context-mode 官方主标语是 **99% fewer bytes**（repo description）；「98%」出自其 README 引用的 Hacker News 帖标题，属**第三方报道非官方标语**。² context-router README 正文 96%/21-of-21，description 却写 91%/17-of-18——**同仓两处口径打架**，引用须注明字段；另有历史 codebase 实测 **64.7%**（**真实存在、可引用**；commit `5a65920` / `2026-04-12` patch 原文 `BENCHMARK_RESULTS.md: ... 64.7% average token reduction, 131 ms avg latency`；注明为历史 codebase 实测；当前 HEAD `apps/cli/README.md:11` / `:587` 仍在用）——**这是第三个版本 / 口径，三者不可混用**；`BENCHMARKS.md` 从未写过 64.7（`git log -S64.7` 0 命中），请勿沿用「旧版 BENCHMARKS 曾写」的错误归属。³ skill-weave 69.6% 是「BM25 单独阶段 16/23」，**不是整体路由 top-1**。
> 数据来源：`docs/competitor-analysis.md`（gh api 2026-11-12 五路实测 + 补查轮）。**机制项 ✅/❌ 是本表核心，不依赖任何实跑数字**。

---

## 2 · 我们刻意「不」做什么（成功样本反证）

按 9 个 Trending 榜仓 + 本项目竞品的反证结论（见 `docs/competitor-analysis.md`）：

- **不主打「压缩%」**：token 节省是「检索式路由 vs 全量常驻」的**共同优势**（词法基线同样省 98%），**不是 WSM 差异化**。WSM 主打**机制唯一性**（表 B 五个 ✅ 唯一）+ **弃权纪律**（65% 正确弃权 vs 词法基线结构性缺失）。
- **不堆门面工程件**：CI / topics / Pages / tag 与「被发现」几乎无关甚至负相关（CI→star r=−0.485）。只做卫生，不写进预期。
- **不比「谁做全」**：级联 / 在线学习 / DAG 编织是行业最佳实践，WSM 显式兼容并包含，不拿来当卖点。

**真正主推**：5 个热门项目都没做的机制（wake-sleep / doc2query / SHY / replay / 弃权）+ 品类词 `wake-sleep skill router`。

> ⚠️ **命名权边界（gh api 实证 + 交叉 query）**：`wake-sleep skill router` 精确串 **0 命中**（可占坑）；交叉 query `dual phase context activation` / `selective skill wake` / `sleep-wake context routing` 也均 0 命中，但 `wake sleep memory agent`(15) / `skill activation gating`(17) 说明**邻近概念是活跃领域**——对外只能说「精确品类串无人占位」，**绝不能说「wake/sleep 概念无人做」**。且 `wake-sleep **memory**` 已被 `JayYun98/jev-lucid-memory`(★2) 字面用过（其 README 里 memory/lesson 高频，context / token / activation 均为 0，属记忆研究非 skill 路由）。故对外**主推 `wake-sleep skill router`，不主推 `wake-sleep memory`**。

---

## 3 · 设计承诺与验证方式

五个核心机制（wake-sleep 双相 / doc2query 语义编译 / SHY 降权 / replay 共现 / 低置信弃权）全部由**同一套可复跑评测管线**背书，不是口头承诺：

- `wsm_bench_proxy_v1.py` — WSM vs 词法基线 vs 全量常驻同口径对照，逐题 JSON 公开；
- `wssr_v05.py --blind --gold --leak` — BLIND-100（60/20/20 分层、先题后标）+ Wilson 95% 门禁 G1–G5 + 金标对抗 + 泄漏自检；
- `tests/` — 仓库契约测试（语料恰好 180 技能、FTS5 可用、结果 JSON 结构与 60/20/20 分层断言）。

> 版本演进全实跑验收：v0.4 → v0.5 → BLIND-100 → Wilson 95% 门禁 G1–G5，见 `CHANGELOG.md` 与 `results/`。

---

## 4 · 数字口径（诚实边界，务必先读）

- **两个口径必须并列**：全量技能目录 10,263 token → top3 候选 200（省 98.06%）；端到端 `top3 + 1 篇全文 = 496 token`，省 **95.17%**。任何地方不许只报 98%。
- **两个实验形态不许混**：本仓库合成语料（管线可复现证明，WSM 与词法打平）与原库真实技能实验（WSM 差异化主张，历史 codebase 实测）是**两个口径**，引用时必须注明形态。
- **代理基线声明**：外部三项目本地无源码。对照实验用本地 `strict_baseline`（直接调 `skiplib.rank@3` 的纯词法路由）作为「BM25/FTS5 词法路由」这一**共同核心机制的代理**；外部项目的 99/96/69.6% 仅作 README 引用值。**这是代理对照，不是对三家二进制的实测。**
- **泄漏自检如实记账**：DEV 层 mean_overlap 0.278（5 条 >0.5）、BLIND 层 0.176（2 条 >0.5）——同作者闭环内部盲测（非真第三方），统计价值是收窄 Wilson 区间；C 层词法基线 0% 是**结构缺失**不是精度失败。完整局限见 `LIMITATIONS.md`。

---

## 5 · 快速开始

```bash
# 1) 跑对照评测（WSM vs 词法基线 vs 全量常驻）
python wsm_bench_proxy_v1.py

# 2) BLIND-100 + Wilson 95% 门禁 + 金标对抗 + 泄漏自检
python wssr_v05.py --blind --gold --leak --dump F.json

# 3) token 三口径
python skiplib.py cost

# 可选：从零重建合成语料与索引
python tools/regenerate_corpus.py && python skiplib.py build
```

零第三方 pip 依赖（仅标准库 + SQLite FTS5）。改语料 / 评测集 / 结果结构前先读 `AGENTS.md` 的一致性契约（改一处须同更多处）。

---

## 6 · 目录（证据型，便于 Agent 消费）

```
corpus/skills/                   # 180 个合成技能（capability-001..180），零私有资产
skillgraph.db                    # 由合成语料全新构建的 FTS5 索引
skiplib.py / wssr_v05.py         # 路由引擎（wake-sleep 双相 + 语义/词法双通道）
blindgen.py / adv_gold.py        # BLIND-100 盲测集 + 对抗金标
wssr_data.py                     # 语料-评测映射（DOC2QUERY / 分层协议）
wsm_bench_proxy_v1.py            # 三方对照评测
rest_router.py                   # strict_baseline 纯词法基线
tools/regenerate_corpus.py       # 合成语料独立再生器
results/                         # 逐题 JSON + 实跑回执（失败案例公开）
tests/                           # 仓库契约测试
docs/competitor-analysis.md      # 五路竞品实测全量数据（GitHub Search API 实拉）
AGENTS.md / LIMITATIONS.md / CHANGELOG.md / requirements.txt
```

---

## 7 · 为什么叫 wake-sleep

像电脑的睡眠模式：**不是删文件，是不用时不耗电**。无任务时技能全睡（0 token），任务来了按显著性唤醒对应技能。别人优化「怎么记得更好」，我们优化「什么时候根本别醒」。

---

## License

MIT · 借鉴思想、不搬代码。第三方项目名称仅作对标引用，商标归各自所有者。
