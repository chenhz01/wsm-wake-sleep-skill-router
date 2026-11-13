# LIMITATIONS.md — WSM · Wake-Sleep Skill Router · 诚实边界

> 本文件列出**已知局限与口径边界**。凡对外引用本项目数字，都应先读这里。
> 项目对外发表名（用户原话确认）：**WSM · Wake-Sleep Skill Router**；品类定位 `wake-sleep skill router`（双相上下文路由）。

## 1. 合成基准与历史实跑是两套数字，不可混用

- 历史台账（如 `WSSR-代理基线实跑台账.md` 及 `wsm_bench_proxy_v1.json` 早期快照）里的数字，来自**作者本机 180 个私有技能语料**的一次实跑。
- 本仓库 A 路径自包含化之后，评测跑在**合成 / 脱敏语料**上，是**另一套基准**。换语料后 hit@3、自信错率、Wilson 区间、token 三口径**全部会变**，需整套重跑并回灌。
- 两套数字的分母、语料分布、技能全文长度都不同，**不得相加、相减、并列比较，也不得用旧数字冒充新结果**。引用时务必写明「基于哪套语料、哪次实跑」。

## 2. BLIND-100 不是真第三方盲测

- BLIND-100 是**同一作者撰写题面、标注金标、同一引擎评分**的扩大版内部盲测（6:2:2 分层：A 清晰 60 / B 近邻 20 / C 应弃权 20，n=100）。
- 它的统计价值是**把 Wilson 区间收窄**（相对小样本），**不能**消除同作者闭环带来的系统性偏差。
- 它**不是**「第三方盲测」「独立评测」。
- 真第三方盲测至少需同时满足：**不同厂商家族出题 + 禁止访问技能库文本 + ≥ 1/3 人类真题**。当前这三项尚未齐备（≥1/3 人类工单这一项已满足，另两项仍缺），列为后续 P0 行动。
- C 层「应弃权」题上，词法代理基线 / 全量常驻控制组**没有弃权机制**，其 0 命中是**结构缺失**，不是同口径精度对撞，不得包装成「精度失败」。

## 3. 外部三项目只做代理对照，不是 1:1 复现或头对头实测

- `context-mode` / `context-router` / `skill-weave` 的源码**本地不存在**，本项目**没有**对它们做 1:1 复现，更没有跑过它们的二进制做头对头实测。
- 本地对照实验里的 `strict_baseline` 定义为 **`skiplib.rank@3`**（纯词法 / BM25+FTS5 路由），它只是三者**公共核心机制的代理基线**，不代表那三个项目本身。
- 三方对照表整体须标注「同口径代理对照实验」，**禁止**写成「WSM vs 三大竞品头对头」「WSM 击败 context-mode」。
- 外部项目的 `99%` / `96%` / `69.6%` 等数字只是其 README / description 的**公开宣称引用值**，不是本项目实测数字，不得与本项目数字并列相减。

## 4. 三个口径不可混用：64.7% / 96% / 91%

这三者都是**竞品 `mohankrishnaalavala/context-router`** 在不同版本 / 不同字段上的数字，**不是 WSM 的实测数字**，且彼此**不可混用**：

| 数字 | 口径 | 载体 / 证据 |
|---|---|---|
| **64.7%** | **历史 codebase 实测** | 最早引入 commit `5a65920`（`2026-04-12`，`feat: Phase 7 + 8 — multi-repo workspace and benchmark harness`）；patch 原文：`+See [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) for real measured numbers on` / `+the context-router codebase (64.7% average token reduction, 131 ms avg latency).`；当前 HEAD 的 `apps/cli/README.md:11`（`(64.7% average reduction)`）与 `apps/cli/README.md:587`（`\| **overall** \| **1 475** \| **−64.7%** \| **131 ms** \|`）仍在使用。`BENCHMARKS.md` **从未**写过该数字（`git log --all -S64.7 -- BENCHMARKS.md` → 0 命中）。 |
| **96%** | 当前根 README 正文宣称 | `96% fewer end-to-end tokens`（21 tasks / 7 OSS / 21-of-21 rank-1）；当前根 README 里 `64.7` 命中 0 次。 |
| **91%** | repo description 宣称 | `up to 91% fewer tokens, 17/18 rank-1 across 6 OSS projects`。 |

- 引用 `64.7%` 必须**同时**带上：commit `5a65920`、日期 `2026-04-12`、patch 原文、以及「**历史 codebase 实测**」限定；并把早期草稿「旧版 BENCHMARKS 曾写 64.7%」的**错误文件归属**纠正为「根 README 历史版本 / `apps/cli/README.md` / `BENCHMARK_RESULTS.md` 历史文件」。
- `64.7%` / `96%` / `91%` 是三个版本 / 口径，**任何场合都不许混用或拼成一句结论**，引用必带版本与字段限定。

## 5. 命名权边界

- 可对外主张的只有一句：**精确品类串 `wake-sleep skill router` 在 GitHub 检索中无人占位**（`total_count = 0`；交叉 query `dual phase context activation` / `selective skill wake` / `sleep-wake context routing` 亦为 0）。
- **禁止**说「wake/sleep 概念无人做」「无人做过双相记忆」——邻近概念是活跃领域（`wake sleep memory agent` 15 / `skill activation gating` 17，且头部多为搜索噪声，不可读作「竞品数」）。
- `wake-sleep **memory**` 字面已被 `JayYun98/jev-lucid-memory`（★2，`Wake–sleep memory for AI agents`）使用；另有 `huanghuangdaquan-beep/dream-rsi-skill` 的 `wake-phase / sleep-phase` 双相变体。二者**均不做上下文 / 技能选择性路由**，不算直接竞品，但坐实「`wake-sleep memory` 词组已被占用」，故该词只作内部代号，**绝不可对外说「wake-sleep memory 无人做」**。

## 6. token 节省不是 WSM 相对词法基线的差异化

- token 节省来自「**检索式路由 vs 全量常驻**」：WSM 与纯词法 `strict_baseline` **都只加载 top3**，因此连词法基线也省下差不多的比例。
- 这是**共同优势**，不是 WSM 相对词法基线的差异化。
- 本项目真正该主打的是**同口径路由质量**（命中率、自信错率、Wilson 区间、弃权纪律），而非压缩百分比。
- token 三口径（全量目录 → top3 候选 → 端到端）必须并列披露，**任何地方不许只报候选清单口径的单一百分比**；且 token 为保守估算，非真实 tokenizer 计数，端到端含「1 篇技能全文」假设。

## 7. 其他已披露的局限

- 提升是**整系统**结果（BM25 + doc2query 语义编译 + SHY 降权 + replay 共现 + 低置信弃权共同贡献），**不全归因于 wake-sleep 单机制**。
- 仅在**单一技能库规模（180）**、单一作者语域上验证；语义编译依赖 doc2query 语料质量。
- C 层弃权纪律是真实短板（历史实跑中该弃权却自信误路由的题必须一并披露，不得只报 A+B 层光鲜数字）；旧版小样本门禁也有 FAIL 记录，不得隐藏。
- 全量常驻控制组的「命中率」本地**不可实跑**（纯检索器，无 LLM 端到端选择环节），标 `N/A`，仅作 token 成本上界，**禁止编造**。
- 竞品 stars / 检索命中数会随时间变化；`docs/competitor-analysis.md` 里的数字带取证时间戳，引用时请注明「某时点实测」。
