# results/ — 逐题结果与失败案例

本目录存放评测的**逐题 JSON 结果**。它是仓库对外「数字单一真相源」的一部分：README / 文档里出现的任何实验数字，都必须能在这里的 JSON 里按字段路径核对到。

> 本目录**不预置任何结果数据**。结果文件由复现命令实跑产出，不由文档手工编写。若目录里暂时只有本 README，说明新一轮结果尚未跑出（或尚未回填），此时不得在别处引用「本轮结果」。

## 存放约定

- 一次实跑一个文件，文件名带运行标识，例如 `wsm_bench_proxy_v1.json`、`wsm_bench_proxy_v1.run2.json`。
- 同一评测里 WSM / 词法代理基线 / 全量常驻控制组用**同一套字段格式**，便于逐题对账。
- 每个结果 JSON 顶层应至少包含这些结构键（详见 `AGENTS.md`）：
  `meta`、`honesty`、`token_cost_three_metrics`、`three_way_blind100`、`gates`、`latency`、`blind100_rows`。
  - `blind100_rows`：逐题记录数组，每题带 `layer`（A / B / C）、`expect`、`wsm`、`strict` 等字段。
  - `three_way_blind100.layer_counts`：分层计数，冻结为 `A=60 / B=20 / C=20`（6:2:2，n=100）。
- `meta` 里记录 `generated_at`、`python`、`deterministic_double_run` 等元信息；**这些元信息不是逐字节确定性承诺**：延迟实测值、时间戳、以及随语料变化的 `skill_body_avg_tokens` 允许在两次实跑间轻微漂移，如实记账即可，不要冒充恒定值。

## 诚实边界：失败案例也公开

这是本目录最重要的约定，不是缺陷清单：

- **20% 的 C 层「应弃权」题必须原样公开**。这批题专门检验引擎「置信不足时宁可不路由也不错路由」——引擎在该弃权时却自信误路由的记录，是真实短板，必须保留、不能删、不能只报 A+B 层的光鲜数字。
- 每一道 MISS / 自信错 / 伪弃权的逐题记录都保留，供任何人开 issue 逐条对账。
- 分层冻结为 `A（清晰）60 / B（近邻）20 / C（应弃权）20`；这个分层是**结构常量**，改动它属于「改一处须同更 N 处」的联动项（见 `AGENTS.md`），不是可以随手调的参数。
- 若某一层、某一基线或控制组的某项指标**本地不可实跑**（例如全量常驻控制组没有 LLM 端到端选择环节），在结果里标 `N/A` 并写明原因，**不要填一个编造的数字**。

## 口径提示

- 外部三项目（`context-mode` / `context-router` / `skill-weave`）本地无源码，结果里的 `strict_baseline` 只是 `skiplib.rank@3` 纯词法 **代理对照**，不是对那三个项目二进制的 1:1 复现或头对头实测。
- BLIND-100 是**同一作者撰写题面、标注金标、同引擎评分**的扩大版内部盲测，**不是真第三方盲测**；详见 `LIMITATIONS.md`。
- token 节省是「检索式路由 vs 全量常驻」的共同优势，不是 WSM 相对词法基线的差异化。

## 复现

```bash
python wsm_bench_proxy_v1.py                          # 产出主结果 JSON
python wssr_v05.py --blind --gold --leak --dump F.json  # 门禁 / 金标独立复现（F.json 为临时产物，已被 .gitignore 忽略）
python -m unittest discover -s tests                 # 校验语料 / FTS5 / 结果结构
```
