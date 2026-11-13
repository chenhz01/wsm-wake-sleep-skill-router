# AGENTS.md — WSM · Wake-Sleep Skill Router · AI Agent 消费契约

> 本文件是给 **AI Agent / 自动化工具**看的仓库契约，不是给人看的介绍。改这个仓库前先读完它。
> 项目对外发表名（用户原话确认）：**WSM · Wake-Sleep Skill Router**；品类定位 **`wake-sleep skill router`**（双相上下文路由）。
> 注意：`wake-sleep memory` 字面已被 `JayYun98/jev-lucid-memory` 占用，只作内部代号，不对外主张「无人做」。

## 1. 目录结构

| 路径 | 角色 | 谁维护 | 可否随仓库发布 |
|---|---|---|---|
| `README.md` | 首屏三栏定位 + 表 A（同口径本地实跑）/ 表 B（机制重样 + 引用值） | team-lead | 是 |
| `LICENSE` | MIT 全文（版权行：善伦） | — | 是（**须与 README license badge 一致**；README 归 team-lead 维护，若 badge 仍为 Apache--2.0 需同步改 MIT） |
| `requirements.txt` | 零第三方 pip 依赖声明 + FTS5 / 数据前置条件 | — | 是 |
| `AGENTS.md` | 本文件 | — | 是 |
| `LIMITATIONS.md` | 诚实边界 | — | 是 |
| `CHANGELOG.md` | 版本演进 | — | 是 |
| `docs/competitor-analysis.md` | 五路竞品实测 + 补查终审，发布态竞品数字真相源 | — | 是 |
| `corpus/` | 180 个技能定义（合成 / 脱敏语料） | 代码工程师 | 是（**必须自包含**） |
| `skillgraph.db` | SQLite + FTS5 索引（由 `corpus/` 构建） | 代码工程师 | 是（**不要加进 `.gitignore`**） |
| `skiplib.py` / `wssr_v05.py` / `wsm_bench_proxy_v1.py` / `tools/` | 运行代码、评测 harness、语料构建工具 | 代码工程师 | 是（纯标准库） |
| `results/` | 逐题 JSON（含失败案例，尤其 20% 应弃权层） | 实跑产出 | 是 |
| `tests/` | stdlib `unittest` 契约用例 | — | 是 |
| `.gitignore` | 忽略临时产物，**不**忽略 `skillgraph.db` | — | 是 |

> 若实际运行文件名与上表不同，**以仓库内真实文件为准**，但 `results/` 与 `docs/competitor-analysis.md` 这两个真相源路径不变。

## 2. 三条复现命令

在仓库根目录执行（需要 Python ≥ 3.10 且 SQLite 带 FTS5）：

```bash
python wsm_bench_proxy_v1.py                            # 主评测：WSM vs 词法代理 vs 全量常驻 → wsm_bench_proxy_v1.json
python wssr_v05.py --blind --gold --leak --dump F.json  # BLIND-100 / Wilson 95% 门禁 / 金标独立复现
python skiplib.py cost                                  # token 三口径（全量目录 → top3 候选 → 端到端）
```

外加结构自检：

```bash
python -m unittest discover -s tests
```

> 前置条件：需仓库内 `corpus/` + `skillgraph.db`；**无任何外部数据下载**。
> `--dump F.json` 是临时产物，已被 `.gitignore` 忽略，不要提交。
> 结果写到**当前工作目录 / 相对仓库根**，不写任何硬编码绝对路径。

## 3. 数字单一真相源

- **实验数字**：`wsm_bench_proxy_v1.json` 与 `results/` 下的逐题 JSON 是唯一真相源。README / 文档里出现的每个实验数字，都必须能在这里按字段路径核对到；**不得在文档里手写或推算实验数字**。
- **竞品数字**：`docs/competitor-analysis.md` 是发布态真相源，其中逐条标明「gh api 实拉 / README 引用值 / git history 取证」三种来源。
- 结果 JSON 顶层结构键：`meta`、`honesty`、`token_cost_three_metrics`、`three_way_blind100`、`gates`、`latency`、`blind100_rows`。
- `meta.generated_at` / `latency.*` / `skill_body_avg_tokens` 允许在两次实跑间轻微漂移，如实记账；**逐题 JSON、`gates`、Wilson 区间、命中与错率字段应保持一致**。不要冒充「逐字节确定性」。

## 4. 「改一处须同更 N 处」一致性清单

以下四处是**强联动**，改任何一处都必须重跑整套实验并把全部数字回灌，否则文档与结果会互相矛盾：

| # | 联动项 | 改动会波及 |
|---|---|---|
| 1 | **语料** `corpus/`（180 技能定义） | token 三口径 + 路由质量数字全部会变 |
| 2 | **db** `skillgraph.db`（FTS5 索引） | 必须与 `corpus/` 由同一份语料重建；不得与语料版本错配 |
| 3 | **评测集** BLIND-100（冻结 6:2:2） | 逐题 JSON、门禁 G1–G5、Wilson 区间、分层计数 |
| 4 | **文档** `README.md` / `LIMITATIONS.md` / `CHANGELOG.md` / `docs/competitor-analysis.md` / `results/README.md` / 本文件 | 所有引用数字、口径限定、版本说明 |

标准流程：`改语料 → 重建 db → 重跑三条命令 → 生成新 results/ → 逐处回灌文档 → 跑 tests/ → 复核无残留旧数字`。
**禁止只更新其中一处**（例如只改 README 数字而不重跑，或只换语料不改 db）。

另有两个跨文件口径锁定项：
- **64.7% 引用口径**（commit `5a65920` / `2026-04-12` / patch 原文 / 「历史 codebase 实测」限定）在任何文件里出现时都必须带全套限定，且不与 `96%` / `91%` 混用——见 `LIMITATIONS.md` 与 `docs/competitor-analysis.md`。
- **命名权表述**在任何文件里都只能说「精确品类串 `wake-sleep skill router` 无人占位」。

## 5. 禁止事项（红线）

1. **不要改 BLIND-100 分层 `60/20/20`**（A 清晰 60 / B 近邻 20 / C 应弃权 20）。这是冻结的结构常量，不是可调参数；改它必须连同评测集、门禁、逐题 JSON、文档一起重做，并显式说明理由。
2. **不要引入静默兜底**。读技能语料 / db 失败时必须**显式报错并让命令非零退出**，禁止 `except ... → 退化成片段` 这种「命令退出 0 但 token 数字悄悄变」的写法（历史上真实出现过，见 `CHANGELOG.md` v3 条）。
3. **不要把结果写到硬编码绝对路径**。输出一律用 `cwd` 或相对仓库根的路径；禁止 `sys.path.insert` 到仓库外私有目录、禁止把结果写回某个固定盘符路径。
4. 不要把外部三项目（`context-mode` / `context-router` / `skill-weave`）的公开宣称值写成**头对头实测**；本地 `strict_baseline` 只是 `skiplib.rank@3` 纯词法代理对照。
5. 不要把 BLIND-100 称为「第三方盲测 / 独立评测」；不要把 `64.7%` / `96%` / `91%` 混用；不要写「wake/sleep 概念无人做」或「wake-sleep memory 无人做」。
6. 不要把 token 节省百分比当 WSM 相对词法基线的差异化优势（它是「检索式路由 vs 全量常驻」的共同优势）。
7. 不要提交 `F.json`、`_preflight_*`、`__pycache__/`、`*.pyc`、`*.db-wal` / `*.db-shm` 等临时产物；但 `skillgraph.db` 本身**必须提交**。
