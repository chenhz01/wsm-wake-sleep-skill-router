# CHANGELOG — WSM · Wake-Sleep Skill Router

按时间线记录 **WSSR v0.5 → WSM V1（Wake-Sleep Skill Router）** 的演进。
项目对外发表名（用户原话确认）：**WSM · Wake-Sleep Skill Router**；品类定位 `wake-sleep skill router`（双相上下文路由）。`wake-sleep memory` 字面已被第三方占用，只作内部代号，不对外主张。

> **日期约定**：只使用取证材料里已出现过的日历日；无法确定具体日期的写「本轮」，**不编造日期**。
> 本文件只记事件、判定变更与口径修正，**不重复引用实验数字**；实验数字的真相源是 `results/` 与 `wsm_bench_proxy_v1.json`。

---

## [v0.5] — 2026-11-10（WSSR 引擎基线）

- 在 v0.4 基础上落地 5 个机制：**wake-sleep 双相 / doc2query 生成式语义编译 / SHY 降权 / replay 共现 / 低置信熔断弃权**。
- BLIND-100 重冻为 **6:2:2 分层**（A 清晰 60 / B 近邻 20 / C 应弃权 20，n=100），配 Wilson 95% 门禁 G1–G5。
- 经历多身份对攻、交叉验证抓伪补丁、三迭代实测；诚实边界写死：**同作者闭环内部盲测，非真第三方**。
- 已知短板如实保留：C 层弃权纪律、小样本旧门禁的 FAIL 判定，均不得隐藏。

---

## [V1] — 2026-11-12（发表策略轮，按发生顺序）

### 1. GitHub 五路竞品实测 + 4 项目核实

- 用 `gh api`（鉴权账号）实时实拉 T1–T5 五路赛道、`GET /repos/{owner}/{repo}` 的 stars、以及 4 个项目 README 原文；原始响应落盘 `raw_competitor_5tracks.json`，复现脚本可重跑。
- 结论要点：`context-mode` 33,909★ 是唯一真热门；`context-router` 11★ / `skill-weave` 1★ / `skill-memory` 21★ 是微型仓；T4 真头部是 `mem0`(68,839★) 与 `Acontext`(3,696★)。
- T5 精确品类串 `wake-sleep skill router` `total_count = 0`；补查轮交叉 query 加固「精确品类串无人占位」边界，并坐实 `wake-sleep memory` 已被 `JayYun98/jev-lucid-memory` 字面占用。
- 逐条区分「gh api 实拉值」与「README 引用值」，见 `docs/competitor-analysis.md`。

### 2. 本地代理基线实跑

- 新建同口径三方对照 harness，产出 `wsm_bench_proxy_v1.json` 与逐题 JSON（`results/`），并配机器实跑台账。
- 明确口径：外部三项目本地无源码，对照用 `strict_baseline = skiplib.rank@3` 纯词法 **代理基线**，是「同口径代理对照实验」，**不是 1:1 复现或头对头实测**。
- 换锚结论：token 节省是「检索式路由 vs 全量常驻」共同优势，对外主打同口径路由质量，不主打压缩百分比。

### 3. 补查轮 · 64.7% 终审改判（v1 误判 → 终审「确实存在、可引用」）

- **v1 误判**：补查轮 v1 曾把 `context-router` 的 `64.7%`（历史 codebase 实测数字，全套引用口径见本节末）判为「查无实据 / 历史 commit 未逐版取证」，并据此在若干稿件里删除或改写该数字。根因是 `fetch_followup.py` 被 SIGTERM 前写下的草稿 verdict（`all_hits` 为空即判「查无实据」），且只查了根 README 当前版本（0 命中），未查 git history 与子目录 README。
- **终审改判**：改用本地 `gh repo clone mohankrishnaalavala/context-router` + `git log -S64.7` 逐 commit 溯源，确证数字**真实存在、可对外引用**：
  - 最早引入 commit **`5a65920`**（**`2026-04-12`**，`feat: Phase 7 + 8 — multi-repo workspace and benchmark harness`）；
  - patch 原文：`+See [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) for real measured numbers on` / `+the context-router codebase (64.7% average token reduction, 131 ms avg latency).`；
  - 当前 HEAD 的 `apps/cli/README.md:11` / `:587` 仍在用；
  - `BENCHMARKS.md` **从未**写过该数字（`git log --all -S64.7 -- BENCHMARKS.md` → 0 命中）。
  - 口径限定：**这是「历史 codebase 实测」**，`64.7%`（历史 codebase 实测）/ `96%`（当前根 README）/ `91%`（repo description）是三个版本 / 口径，**不可混用，引用必带版本限定**。
- **处置由「删数字」改为「修正文件归属 + 补版本限定」**：删的是「旧版 BENCHMARKS 曾写」这个错误归属，不是删数字本身。v1 的下游删除动作基于错误前提，已按终审版重新裁决回灌。
- 教训留痕：git history / 子目录 README 未穷尽前不得下「查无实据」结论；被中断脚本的草稿 verdict 必须作废重跑。

### 4. v3 clean-env 可复现性阻断（F5 **PASS → BLOCKED**）

- 干净目录独立复核（只放工作区 `.py`、清空 `PYTHONPATH`、拦截脚本自插的仓库外绝对路径）证伪了 README 第一屏「clone 即跑 / 一键复现」：3 条复现命令中 2 条在 `import skiplib` 阶段 `ModuleNotFoundError`、1 条 `skiplib.py` 不存在。作者本机跑得通只是私有目录真实存在的**本机特例**。
- 依赖闭包越界：仓库外 `skiplib.py` / `skillgraph.db` / 私有 `skills/`（记忆资产，未经单独授权不得外发）；三处 `sys.path.insert` 硬编码 + `SKILLS_DIR` / `DB_PATH` / `HERE` 三处绝对路径硬编码。
- 两个副作用：结果写回硬编码 `HERE`（复核时跨域覆盖工作区结果文件）；读语料失败有 `except OSError → txt = d["body"]` **静默兜底**，命令可退出 0 但 token 数字悄悄漂移。
- 数字漂移留痕：两次实跑的端到端 token / 节省率 / 技能全文均值出现 1-token 级差异，逐题 JSON、门禁、Wilson、命中与错率字段保持一致；结果文件已还原至原始快照并留痕。
- **门禁改判**：F5 `PASS` → **BLOCKED**；技术证据层 `v2 复核通过` → **NOT READY**（F2 / F4 维持 PASS）。README 撤下「一键复现」，改为写明前置条件与确定性边界。
- 由此暴露「零第三方 pip 依赖 ≠ 零外部数据依赖」，直接催生下一步 A 路径自包含化。

---

## [V1] — 本轮（发布准备，进行中）

### 5. A 路径 · 合成语料自包含化

- 选定 **A 路径**：生成一份**合成 / 脱敏**技能语料快照（不公开任何私有技能资产），把 `corpus/` 与 `skillgraph.db` 纳入仓库、所有路径改相对、输出写 cwd、去掉静默兜底，并**重跑整套实验**。
- 诚实前提（已先说明）：现有历史数字建立在 180 个私有技能上，换语料后 hit@3 / 自信错率 / Wilson / token 三口径**全部会变**，等于重做一次实验 + 全部稿件回灌一轮。
- 由此形成两套不可混用的数字：**作者本机 180 私有技能上的历史实跑** vs **合成基准上的本轮结果**（见 `LIMITATIONS.md` §1）。

### 6. 仓库级配套文件落地

- 生成 `LICENSE`（MIT，版权行善伦；须与 README license badge 一致）、`requirements.txt`（Python ≥3.10 / 零第三方 pip 依赖 / 需 FTS5 / 需仓库内 `corpus/` + `skillgraph.db`）、`AGENTS.md`、`LIMITATIONS.md`、`CHANGELOG.md`、`docs/competitor-analysis.md`、`tests/`、`results/README.md`、`.gitignore`。
- `tests/` 用标准库 `unittest` 校验：语料可扫描且恰好 180 个技能、FTS5 可用、结果 JSON 顶层键齐全 + BLIND-100 分层 60/20/20；**不硬编码任何实验数字**，依赖文件未就绪则 skip。
- `.gitignore` 忽略 `F.json` / `_preflight_*` / `__pycache__/` / `*.pyc` / `*.db-wal` 等临时产物，**但明确不忽略 `skillgraph.db`**。

> 本轮止于「把仓库级文件备齐 + 自包含化重跑」。**未执行任何对外动作**（未 git init / commit / push）。
