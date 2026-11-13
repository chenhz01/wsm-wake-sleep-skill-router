# 竞品对标 · 五路实测真实 API 数据

> 本文件是 **WSM · Wake-Sleep Skill Router** 的**发布态竞品数字真相源**，由 `WSM-五路实测竞品数据.md`（§7 为终审版）+ `raw_competitor_5tracks.json` + `raw_followup.json` 提炼。
> 取证数据落盘件，**只记录查证到的值与原文，区分「实拉 / 引用 / 查不到」，不编造任何 stars 或数字**。
> 项目对外发表名（用户原话确认）：**WSM · Wake-Sleep Skill Router**；品类定位 `wake-sleep skill router`（双相上下文路由）。

## 0. 取证元信息与「来源标注」体系

| 项 | 值 |
|---|---|
| 取证时间 | 2026-11-12 12:55–12:58 (UTC+8)，见 `raw_competitor_5tracks.json._meta.generated_at` |
| 工具 | `gh api`（GitHub CLI 2.97.0），`gh auth status` 已鉴权账号 `chenhz01` |
| 数据源 | GitHub REST API `https://api.github.com`（实时、非缓存） |
| 请求量 | 14 个 search + 4 个 repos + 4 个 readme + 4 个 cross_check 共 26 次，**全部成功、0 失败、0 限流** |
| 端点 | 搜索 `GET /search/repositories?q={urlencoded}&sort=stars&per_page=10`；仓库 `GET /repos/{owner}/{repo}`；README `GET /repos/{owner}/{repo}/readme`（raw） |
| 补查轮 | `fetch_followup2.py` 增量落盘 `raw_followup.json`；`context-router` 历史数字（全套引用口径见 §4）溯源改用本地 `gh repo clone mohankrishnaalavala/context-router cr_hist` + `git log -S64.7` 逐 commit |
| 原始响应 | `raw_competitor_5tracks.json`、`raw_followup.json`；git 取证原文 `p1_git_forensics.txt` / `p1_git_detail.txt` / `p1_git_detail2.txt` / `p1_clone.txt` |
| 网页核实 | WebSearch / WebFetch（一手页面） |

**来源标注（本文每个数字都带其一）**：

| 标记 | 含义 | 可信度 |
|---|---|---|
| **【A】gh api 实拉** | `GET /repos/...`、`/search/...` 返回的 `stargazers_count` / `total_count` / `description` / `license` / `pushed_at` 等**字段实时值** | 实时一手字段 |
| **【B】README 引用值** | 对方 README 正文 / repo description 里的**公开宣称数字**（命中统计来自 `readmes[*].keyword_hits` 与 `readme_text` 原文），**非本项目实测** | 对方自述，须注明字段 |
| **【C】本地 git history 取证** | clone 对方仓库后 `git log -S64.7` / `git show 5a65920` 得到的 patch 原文 | 历史 commit 一手证据 |
| **【D】补查轮交叉 query** | `raw_followup.json` 里补跑的 T5 交叉 query 与 `total_count` | 实时一手字段 |

> 背景：GitHub 搜索 `q=` 默认匹配 name / description / topics，**不搜 README 正文**，故结果会混入字面命中的无关仓库；这是 T5 判定的重要背景，不能把 `total_count` 直接读作「竞品数」。

---

## 1. 「哪些是 gh api 实拉、哪些是 README 引用值」速查

| 数字 / 说法 | 来源 | 说明 |
|---|---|---|
| `context-mode` 33,909★ | **【A】** | `GET /repos/mksglu/context-mode` 返回；搜索端点返回 33,908（抓取瞬间 +1 星），以 repo 端点为准 |
| `context-router` 11★ / `skill-weave` 1★ / `skill-memory` 21★ | **【A】** | 三个微型仓，`GET /repos/...` 实时值 |
| `mem0` 68,839★ / `Acontext` 3,696★ | **【A】** | T4 搜索 top1 / 精确 query top1 的 `stargazers_count` |
| T1–T5 各 query 的 `total_count` | **【A】** | `/search/repositories` 实时返回 |
| T5 交叉 query `0 / 15 / 17` | **【D】** | 补查轮 `raw_followup.json` |
| `context-mode` 官方主标语「**99% fewer bytes in context**」 | **【A】** | repo `description` 字段原文（非 README 正文）；精确字面 `"99%"` 在 README 正文命中 0 次 |
| `context-mode` 的「**98%**」 | **【B】** | README 引用的 **Hacker News 帖标题**「MCP server that reduces Claude Code context consumption by 98%」（2026-02-28，570+ points / 107 comments），**第三方报道，非官方主标语** |
| `context-router` README 正文「**96% fewer end-to-end tokens**」 | **【B】** | README 正文出现 2 次（21 tasks / 7 OSS / 21-of-21 rank-1；v4.5） |
| `context-router` description「**91% fewer tokens, 17/18 rank-1 across 6 OSS projects**」 | **【A】** | repo `description` 字段原文，与 README 96% 口径打架 |
| `context-router`「**64.7%**」 | **【C】** | 本地 git history + 当前 `apps/cli/README.md`（见 §4，**须带全套限定**） |
| `skill-weave`「**69.6%（16/23）**」 | **【B】** | README 原文，口径是 **BM25 单独阶段**，非整体路由 top-1 |
| `skill-weave`「3 段级联 / UCB / Tree Filter 141→15」 | **【B】** | README 命中统计（BM25 10 次 / UCB 3 次 / Tree Filter 4 次） |
| `skill-memory`「**agent skill as memory layer**」 | **【A】** | repo `description`；README 正文 `memory layer` 命中 **0** 次（叙事在 description 不在正文） |
| `context-mode` 机制 BM25 / FTS5 / PreToolUse / Thinking in Code | **【B】** | README 命中统计（BM25 2 / FTS5 2 / PreToolUse 4 / Thinking in Code 15） |
| `context-router` 机制 FTS5 / feedback / observation / BM25 | **【B】** | README 命中统计（5 / 6 / 1 次等） |

---

## 2. 五路赛道 T1–T5 实测（全部【A】）

字段：`query → total_count`；top1 只列全名与 stars。

| 赛道 | query | total_count | top1（★） |
|---|---|---|---|
| T1 压缩 / 重定向 | `context window compression agent` | 31 | `Paritok-official/paritok-4b-v1` 1,446 |
| | `context-mode` | 3,429 | `mksglu/context-mode` 33,908*→33,909 |
| | `tool output context reduction` | 10 | `speedydiv/TokenForge` 18 |
| T2 路由 / 打包 | `context router llm` | 701 | `deepset-ai/haystack` 26,993 |
| | `context packing agent` | 31 | `codefromkarl/ContextAtlas` 30 |
| T3 技能路由 | `skill router agent` | 2,059 | `gamedev-skills/awesome-gamedev-agent-skills` 8,408 |
| | `agent skill selection` | 251 | `sickn33/agentic-awesome-skills` 49,567 |
| T4 技能即记忆 | `agent memory layer` | 2,859 | `mem0ai/mem0` **68,839** |
| | `skill as memory` | 711 | `memodb-io/Acontext` **3,696**（「Agent Skills as a Memory Layer」） |
| T5 双相 / 休眠 | `wake sleep agent` | 104 | `zszszszsz/.config` 369（OpenWrt 配置，噪声） |
| | `sleep wake llm` | 25 | `leomariga/ProactiveAgent` 53 |
| | `activation gating llm` | 15 | `anthony-maio/mnemos` 28 |
| | **`wake-sleep skill router`** | **0** | **无返回项目** |
| | `context suspension` | 6 | `hayabusa-cloud/cove` 2 |

> \* 搜索端点 33,908，`repos` 端点 **33,909**（抓取瞬间 +1 星），以 repo 端点为准。
> T5 的高计数（104 / 25 / 15 / 6）来自 description 字面含 sleep/wake/suspension 的无关仓库（OpenWrt、Termux、模型级 vLLM sleep/wake 等）。**越接近精确品类词，命中越少直至归零**。

---

## 3. 四个对标项目逐仓核实

### 3.1 `mksglu/context-mode` — 唯一真热门

| 字段 | 值 | 来源 |
|---|---|---|
| stars | **33,909** | 【A】 |
| language / license | JavaScript / NOASSERTION | 【A】 |
| pushed_at / created_at | 2026-11-12 / 2026-02-23 | 【A】 |
| description 原文 | 「…Sandbox and SQLite FTS5 search, **99% fewer bytes in context**. Works with Claude Code, Codex, Pi, OpenCode, Gemini CLI, Copilot CLI… Zero telemetry.」 | 【A】 |

- **官方主标语是 `99% fewer bytes`（repo description）**。草稿曾写「98–99%」，需精确到 99%。【A】
- `98%` 在 README 出现 1 次，位于引用的 **Hacker News 帖标题**（第三方报道），**不是官方主标语**。【B】
- 机制：BM25 + Reciprocal Rank Fusion（`ctx_search`）、FTS5（Porter-stemmed + trigram）、`PreToolUse` 钩子把大输出重定向到 `ctx_*`、「Thinking in Code」。【B】

### 3.2 `mohankrishnaalavala/context-router` — 一仓三口径

| 字段 | 值 | 来源 |
|---|---|---|
| stars | **11**（微型仓） | 【A】 |
| language / license | Python / NOASSERTION | 【A】 |
| pushed_at / created_at | 2026-06-12 / 2026-04-12 | 【A】 |
| description 原文 | 「…**up to 91% fewer tokens, 17/18 rank-1 across 6 OSS projects**. MCP-native, multi-repo…」 | 【A】 |
| README 正文 | 「**96% fewer end-to-end tokens** than comparable tooling (21 tasks, 7 OSS projects, 21/21 rank-1)」×2 | 【B】 |

- 同一仓库 **description 91%（17/18）** 与 **README 96%（21/21）** 两处口径打架，引用须注明字段。【A+B 对照】
- 机制：FTS5、feedback（`record_feedback` 按 useful/missing/noisy 调 per-file 置信，≥3 reports）、observation、BM25。【B】
- 历史数字 `64.7%` 见 §4。

### 3.3 `Hxh-yaoxing/skill-weave` — 微型仓，数字口径须精确

| 字段 | 值 | 来源 |
|---|---|---|
| stars | **1**（微型仓） | 【A】 |
| language / license | Python / MIT | 【A】 |
| pushed_at / created_at | 2026-07-03 / 2026-06-05 | 【A】 |
| description 原文 | 「Adaptive skill routing for multi-agent systems — 4-dimension scoring engine」 | 【A】 |

- `69.6%` 在 README 出现 3 次，原文：「**BM25 alone pushes accuracy to 69.6% (16/23), and LLM re-rank further improves it**」、流程图 `R2[BM25: 69.6% → +LLM re-rank]`。【B】
- **精确口径是「BM25 单独阶段准确率 69.6%（16/23）」，不是整体路由 top-1**；草稿写「路由 top-1 69.6%」是概述，引用须用原文口径。
- 机制：**3 段级联**（Tree Filter 141→15 → BM25 → LLM Re-rank）、UCB 在线学习、DAG 编织。【B】

### 3.4 `memodb-io/skill-memory` — 微型仓，叙事在 description

| 字段 | 值 | 来源 |
|---|---|---|
| stars | **21**（微型仓） | 【A】 |
| language / license | TypeScript / 无 license 字段 | 【A】 |
| pushed_at / created_at | 2026-01-30 / 2026-01-27 | 【A】 |
| description 原文 | 「**agent skill as memory layer**」 | 【A】 |

- README 正文中字面 `memory layer` 命中 **0** 次（`skill` 28 / `memory` 19），该叙事**只在 description**。【B】
- 同组织 `memodb-io/Acontext`（3,696★，「Agent Skills as a Memory Layer」）才是 T4「技能即记忆」赛道真头部。【A】

### 3.5 体量修正

早期草稿把 4 个项目统称「头部竞品」是错的。实测 stars：**33,909 / 11 / 1 / 21**【A】——只有 `context-mode` 是真热门，其余三个是 1–21★ 的零星小仓；T4 真头部是 `mem0`(68,839★) 与 `Acontext`(3,696★)，T3/T2 头部另有 haystack 等。【A】

---

## 4. `context-router` 64.7% · 终审引用口径（**必须整套引用**）

> 这**不是**本项目的实测数字，而是竞品 `context-router` 的公开历史数字。
> 引用 `64.7%` 时，**必须同时带**：commit `5a65920`、日期 `2026-04-12`、patch 原文、以及「**历史 codebase 实测**」限定，且**不与 96% / 91% 混用**。

| 项 | 值 | 来源 |
|---|---|---|
| 判定 | ✅ **确实存在、可对外引用**（终审改判） | 【C】 |
| 最早引入 commit | `5a65920` · `2026-04-12` · `feat: Phase 7 + 8 — multi-repo workspace and benchmark harness` | 【C】 |
| patch 原文 | `+See [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) for real measured numbers on` / `+the context-router codebase (64.7% average token reduction, 131 ms avg latency).` | 【C】 |
| 当前 HEAD 仍在用 | `apps/cli/README.md:11`（`(64.7% average reduction)`）；`apps/cli/README.md:587`（`\| **overall** \| **1 475** \| **−64.7%** \| **131 ms** \|`） | 【C】 |
| `git log --all -S64.7` | 9 个 commit，日期 `2026-04-12` ~ `2026-04-28` | 【C】 |
| `BENCHMARKS.md` | `git log --all -S64.7 -- BENCHMARKS.md` → **0 命中**，该文件从未写过 64.7 | 【C】 |
| 数字实际载体 | 根 README 历史版本 + `apps/cli/README.md`（含当前 HEAD）+ `BENCHMARK_RESULTS.md` 历史文件；另散见 `benchmarks/results/2026-06-10-v4.5-e2e/holdout/*.json` | 【C】 |
| 当前根 README | `3.12%` / `96%` / `96.0%`，`64.7` 命中 0 次（这正是 v1 误判「查无实据」的原因：只查了根 README 当前版本） | 【C】 |
| repo description | 「up to **91%** fewer tokens, 17/18 rank-1…」 | 【A】 |

**三口径不可混用（终审裁决）**：

| 数字 | 口径 | 载体 |
|---|---|---|
| **64.7%** | **历史 codebase 实测**（commit `5a65920` / `2026-04-12` / patch 原文见上） | 根 README 历史版本 / `apps/cli/README.md` / `BENCHMARK_RESULTS.md` 历史文件 |
| **96%** | 当前根 README 正文宣称（`96% fewer end-to-end tokens`） | README 正文【B】 |
| **91%** | repo description 宣称（`up to 91% fewer tokens, 17/18 rank-1`） | description【A】 |

- **禁止**「旧版 **BENCHMARKS** 曾写 64.7%」这一错误归属（`BENCHMARKS.md` 从无 64.7）；正确归属是「根 README 历史版本 / `apps/cli/README.md` / `BENCHMARK_RESULTS.md` 历史文件」。
- **禁止**把 64.7% / 96% / 91% 拼成一句结论或互相替代；引用必带版本与字段限定。
- 改判留痕：补查轮 v1 曾误判「查无实据」（被 SIGTERM 脚本的草稿 verdict + 只查根 README 当前版本），终审用本地 git history 逐 commit 溯源改判「确实存在」，处置由「删数字」改为「修正文件归属 + 补版本限定」。

---

## 5. T5 命名权交叉 query 与边界（【A】/【D】）

| 交叉 query | total_count | 来源 | 判定 |
|---|---|---|---|
| `wake-sleep skill router` | **0** | 【A】 | 精确品类串零结果 |
| `dual phase context activation` | **0** | 【D】 | |
| `selective skill wake` | **0** | 【D】 | |
| `sleep-wake context routing` | **0** | 【D】 | |
| `wake sleep memory agent` | 15 | 【D】 | 头部几乎全是搜索噪声（`zszszszsz/.config` OpenWrt 配置 ★369、语音助手 `wake word` 等） |
| `skill activation gating` | 17 | 【D】 | 头部为领域工程 skill / quality gates，非双相路由 |

**结论**：无「技能 / 上下文双相选择性路由」占位竞品；三条精确串均 0 命中，与 `wake-sleep skill router`（0）一致。15 / 17 两个非零计数**不能读作「竞品数」**，更不可用于说「无人做」。

**两个最需点名的邻接项，明确「算不算竞品」**：

| 项目 | 撞名 / 相似 | 机制差异 | 判定 |
|---|---|---|---|
| `JayYun98/jev-lucid-memory` ★2（2026-10-09）【A】 | 字面「**Wake–sleep memory for AI agents**」 | README 命中 wake 9 / sleep 13 / memory 36 / lesson 25，而 context 0 / token 0 / dual-phase 0 / activation 0 / selective 0；是「经验→lesson 的记忆层」，默认 shadow mode 不激活 | ❌ 不算直接竞品；✅ **坐实 `wake-sleep memory` 词组已被占用** |
| `huanghuangdaquan-beep/dream-rsi-skill` ★5【D】 | `wake-phase / sleep-phase` 双相 + agent skill（改编自 DeepMind Dream-RSI） | 自我改进 meta-skill / 梦境重放改策略层记忆，无「选择性上下文压缩 / 按任务激活技能」 | ❌ 不算直接竞品；比 jev 更贴近「双相」字面，须诚实披露 |

**命名权边界（对外引用裁决）**：
- ✅ `wake-sleep skill router`：**0 结果**，可作为主推品类词主张「**精确品类串无人占位**」。
- ❌ `wake-sleep memory`：已被 `JayYun98/jev-lucid-memory` 字面使用（且有 `dream-rsi-skill` 双相变体），**只能留作内部代号，绝不可对外说「wake-sleep memory 无人做」**。
- 对外安全表述：「在『wake-sleep 双相的技能 / 上下文选择性路由』这一精确品类上，GitHub 检索无占位项目」。
- 禁止表述：「wake/sleep 概念无人做」「无人做过双相记忆」；禁止把 `jev-lucid-memory` / `dream-rsi-skill` 写成 WSM 竞品（可作「概念邻接 / 命名权已占用」的诚实披露）。

---

## 6. 与早期草稿种子数据的偏差汇总（供引用时核对）

| 项目 | 早期草稿 | 实测 / 终审 | 性质 |
|---|---|---|---|
| `context-mode` | 「98–99% fewer bytes」 | 官方 description = **99% fewer bytes**【A】；98% 出自 HN 帖标题【B】 | 精确到 99% |
| `context-router` | 「96% fewer tokens；旧版 64.7%（BENCHMARKS）」 | README 96% ✅【B】、description 91%【A】、**历史 codebase 实测 64.7% 经终审确实存在**（commit `5a65920` / `2026-04-12` / patch 原文 /「历史 codebase 实测」全套口径见 §4）【C】但 `BENCHMARKS.md` 归属错误 | 一处口径漂移 + 一处文件归属修正 |
| `skill-weave` | 「路由 top-1 69.6%；头部竞品」 | 69.6% = **BM25 单独阶段 16/23**【B】；**★1**【A】 | 口径精确 + 体量错配 |
| `skill-memory` | 「约 21★」 | **21★** ✅【A】 | 一致 |
| 4 项目整体 | 与 mem0 / context-mode 并列「头部竞品」 | 实测 ★ 33,909 / **11** / **1** / **21**【A】 | 后三个是微型仓 |
| T4 代表 | mem0 / skill-memory | 实测 T4 头部 = mem0(68,839) / **Acontext(3,696)**【A】 | 草稿漏列 Acontext |

---

## 7. 对外引用裁决（速查）

| 数字 / 说法 | 能否对外 |
|---|---|
| 四项目 stars `33,909 / 11 / 1 / 21`（注明 gh api 2026-11-12 实拉） | ✅ |
| `mem0` 68,839★ / `Acontext` 3,696★ | ✅ |
| `context-mode` 官方主标语 `99% fewer bytes` | ✅（附「repo description」字段；98% 仅作 HN 帖标题引用） |
| `context-router` README 96% / description 91% | ✅（须注明字段，且两处口径打架须一并说明） |
| `context-router` 64.7% | ✅（**必须**带 commit `5a65920` / `2026-04-12` / patch 原文 /「历史 codebase 实测」/ 当前 `apps/cli/README.md` 仍在用；**不与 96% / 91% 混用**） |
| 「旧版 **BENCHMARKS** 曾写 64.7%」 | ❌ 禁止（`BENCHMARKS.md` 从无 64.7） |
| `skill-weave` 69.6% | ✅（须注明「BM25 单独阶段 16/23，非整体 top-1」） |
| `wake-sleep skill router` 精确串 0 命中 | ✅（须附「精确品类串」限定） |
| 交叉 query `0 / 15 / 17` | ✅（15 / 17 头部多为噪声，不可读作「竞品数」，不可用于说「无人做」） |
| `wake-sleep memory` 无人做 | ❌ 禁止（已被 `JayYun98/jev-lucid-memory` 字面用过） |
| 把 `jev-lucid-memory` / `dream-rsi-skill` 写成竞品 | ❌ 禁止（可作「概念邻接 / 命名权已占用」诚实披露） |
| 把上述任何外部宣称数字当成本项目头对头实测 | ❌ 禁止（本项目只做 `strict_baseline = skiplib.rank@3` 代理对照，见 `LIMITATIONS.md`） |

---

## 8. 复现

```bash
python fetch_competitors.py        # 重跑 14 search + 4 repos + 4 readme（需 gh 鉴权）
# 64.7% 溯源：
gh repo clone mohankrishnaalavala/context-router cr_hist
cd cr_hist && git log --all --oneline -S64.7 && git show 5a65920
```

> 全部数字来自上述实时 API / 公开网页 / 本地 git history 原文；未命中或无法核实处已显式标注「查不到 / 0 命中」，**无编造**。
> 竞品 stars 与检索命中数会随时间变化，引用时请注明「2026-11-12 某时点实测」。
