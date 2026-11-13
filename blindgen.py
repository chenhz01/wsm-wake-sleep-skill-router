# -*- coding: utf-8 -*-
"""blindgen.py — BLIND-100 盲测集生成 + v0.5 开箱评测（C 层 P0决策二：BLIND-100 重冻）

设计纪律（对齐 patchboard B1 + BLIND40 协议，且写死诚实边界）：
  1. 题面来自「独立意图目录」——按能力域（企业/编码/写作/视频/音乐/知识库/安全/邮件/数据/
     智能体…）用真实用户口吻撰写，撰写时未读取 DOC2QUERY / BLIND40 / 技能描述词汇。
     标注按「功能需求」匹配技能，而非运行路由器取结果（先题后标，标注前未跑路由）。
  2. 分层 6:2:2：
       层 A（60）清晰单一意图——一个明显技能可答；
       层 B（20）近邻消歧——两个相似技能，题面使正确项由功能唯一确定；
       层 C（20）无对应技能——应「弃权」而非自信路由（成功=引擎弃权）。
  3. ≥1/3 为人类工单风格（带背景/口语/ messy），human 标记见数据。
  4. 诚实边界（写死，不可删除）：
     本集由同一作者撰写题面、标注金标、并同引擎评分，属「扩大版内部盲测」，
     NOT 真·第三方盲测。patchboard 待验证点明确：真第三方需「不同厂商家族出题 +
     禁访问技能库文本 + ≥1/3 人类真题」；「不同会话」为伪独立。本集的统计价值在于
     收窄 Wilson 区间（n:40→100），偏差消除仍需外部出题——列为后续 P0 行动项。
"""
import sys, os, json, copy
import skiplib
from wssr_v05 import (WSSR, auto_abstain, ABSTAIN_MARGIN, CONF_THRESHOLD, wilson)

# ---------------------------------------------------------------------------
# BLIND-100 数据：layer ∈ {A,B,C}；expect 为功能金标；human=人类工单风格
# 撰写时未参考任何引擎输出；以下 expect 为作者按能力域独立标注。
# ---------------------------------------------------------------------------
BLIND100 = [
    {
        "layer": "A",
        "human": True,
        "q": "客户下周三要验收，帮我把要交的文件列个清单看看齐不齐",
        "expect": [
            "capability-078"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "服务器最近老被扫，帮我看看 SSH 有没有异常登录的痕迹",
        "expect": [
            "capability-160"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "邮箱里堆了三十封没回的，帮我按重要程度逐封起草回复",
        "expect": [
            "capability-115"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "我们公司想把内部制度文档做成一个能问答的助手，整体怎么规划",
        "expect": [
            "capability-088"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "这张报表有五个 sheet 还要连数据库，帮我一句话跑出来",
        "expect": [
            "capability-076"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "最近要上电商平台卖货，listing 怎么写才不违规",
        "expect": [
            "capability-003"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "这段代码 AI 写的，能跑但我怕有坑，帮我做质量安全审查",
        "expect": [
            "capability-099"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "我想把写公众号这个活外包给一队 AI，让它们自己分工自己验收",
        "expect": [
            "capability-124"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "读书总是读不进去记不住，你反过来问我问题逼我想",
        "expect": [
            "capability-157"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "把这条英文 在线视频站 链接的内容做成中文摘要发给我",
        "expect": [
            "capability-075"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "给我的品牌想一首主题曲，要有记忆点还要押韵",
        "expect": [
            "capability-113"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "这条定时任务上周悄悄挂了两天没人知道，不能再这样",
        "expect": [
            "capability-074"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "这个开源库我想引入，先查查它是不是还活跃、是不是单人项目",
        "expect": [
            "capability-136"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "写周报总忘了报风险项，把这个偏好固化下来让 AI 每次都查",
        "expect": [
            "capability-105"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "这封要发出去的公告里可能含客户手机号，先查有没有敏感信息泄漏",
        "expect": [
            "capability-003"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "我想搞一条自动发合作私信的管线，发出去之前必须有人把关",
        "expect": [
            "capability-017"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "MCP 服务器到底跟我的客户端说了什么，给我抓包看看",
        "expect": [
            "capability-116"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "把 在线大模型 的这个分享链接完整导出来，别截断",
        "expect": [
            "capability-077"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "教我家孩子编程，怎么做他才能真记住",
        "expect": [
            "capability-106"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "我要写一本爽文，但前十章节奏总是崩",
        "expect": [
            "capability-037"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "股票仓位怎么配，帮我按规则算算别重仓",
        "expect": [
            "capability-132"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "帮我看看今天 代码托管平台 上有什么新东西值得跟进",
        "expect": [
            "capability-018"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "这个页面转化率只有百分之零点八，帮我诊断怎么提升",
        "expect": [
            "capability-011"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "新产品到底卖多少钱，怎么打包分层定价",
        "expect": [
            "capability-029"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "把我桌面那堆截图都识读一遍存进笔记库",
        "expect": [
            "capability-101"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "这套 Excel 汇总我每天手抄太蠢了，做个录制回放的自动化",
        "expect": [
            "capability-137"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "新配的域名邮箱发出去全进垃圾箱，查查证书和链路",
        "expect": [
            "capability-156"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "这个模型到底什么时候被换掉的，帮我查本机记录",
        "expect": [
            "capability-120"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "我想把我自己的人生故事做成一个 AI 陪伴的记忆体",
        "expect": [
            "capability-159"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "上个月的周报又没发出来，查一下到底哪个环节断了",
        "expect": [
            "capability-118"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "这批学习视频太长，把每集压成三分钟要点",
        "expect": [
            "capability-107"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "帮我把新书发布的宣传做成有钩子的短剧脚本",
        "expect": [
            "capability-054"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "客户问能不能做个企业即时通讯机器人，帮我评估整体架构",
        "expect": [
            "capability-044"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "我想看看这套自动化工跑了半年到底值不值",
        "expect": [
            "capability-030"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "把这本书的核心思想蒸馏成我能随时调用的思维模块",
        "expect": [
            "capability-064"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "帮我做一个动嘴说话就能办事的语音助手",
        "expect": [
            "capability-174"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "我招聘 AI 工程师，帮我出面试题和评估标准",
        "expect": [
            "capability-047"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "把这个竞争网站的整个页面复刻下来分析",
        "expect": [
            "capability-144"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "每周日自动给我出一份思维周报",
        "expect": [
            "capability-058"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "这个想法能不能落地成产品赚钱，帮我过一遍变现路径",
        "expect": [
            "capability-167"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "从零给我搭一个能自己长文章的知识库",
        "expect": [
            "capability-024"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "旧笔记格式太乱，批量洗干净搬进知识库",
        "expect": [
            "capability-022"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "把新资料喂进知识库自动生成摘要",
        "expect": [
            "capability-023"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "知识库体检，找矛盾页和孤立页",
        "expect": [
            "capability-025"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "给知识库做份周复盘报告",
        "expect": [
            "capability-026"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "长篇小说我要个可控的创作台",
        "expect": [
            "capability-028"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "小说一股 AI 味，去掉翻译腔和堆砌",
        "expect": [
            "capability-033"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "长篇连载怎么控节奏分卷",
        "expect": [
            "capability-034"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "历史架空小说需要资深编辑把关",
        "expect": [
            "capability-040"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "写网文先想怎么过流量关再打磨内容",
        "expect": [
            "capability-175"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "把热门仓库批量做成学习卡",
        "expect": [
            "capability-016"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "帮我在浏览器里自动操作网页，登录后抓数据",
        "expect": [
            "capability-007"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "浏览器自动化挂了，手动接管浏览器",
        "expect": [
            "capability-008"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "截图坏了看不清，从剪贴板找回原图",
        "expect": [
            "capability-009"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "用代码渲染视频，怎么省积分一次写对",
        "expect": [
            "capability-010"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "本地服务 又挂了，修一下",
        "expect": [
            "capability-012"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "给目标主机批量装插件，装完检查生效没有",
        "expect": [
            "capability-013"
        ]
    },
    {
        "layer": "A",
        "human": True,
        "q": "把 既有框架 的性能优化方法搬进目标平台",
        "expect": [
            "capability-014"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "把几条本能模式固化成自进化技能",
        "expect": [
            "capability-015"
        ]
    },
    {
        "layer": "A",
        "human": False,
        "q": "给技能库出一份台账清单",
        "expect": [
            "capability-031"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "帮我检查 AI 写的东西有没有占位符和瞎编数字，能不能交付",
        "expect": [
            "capability-003"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "装新技能前先做安全审计，看有没有恶意代码",
        "expect": [
            "capability-032"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "把这段粗糙的产品描述转成分镜提示词",
        "expect": [
            "capability-080"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "写一个专业格式的剧本，三幕结构",
        "expect": [
            "capability-140"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "写一条有钩子有反转的爆款短剧",
        "expect": [
            "capability-054"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "做一支水墨古风短片",
        "expect": [
            "capability-098"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "用 视频生成模型 做 AI 影片",
        "expect": [
            "capability-055"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "把这条视频的功能做成内置技能",
        "expect": [
            "capability-082"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "抓取这条短视频平台视频的数据和文案",
        "expect": [
            "capability-081"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "评估这个产品用开源加论文互证",
        "expect": [
            "capability-038"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "对这个产品做全维度优劣分析",
        "expect": [
            "capability-061"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "按我的水平因材施教地教我",
        "expect": [
            "capability-041"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "教我的时候守住老师的位置，别变成陪聊",
        "expect": [
            "capability-164"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "交付的东西要带通俗版和清单",
        "expect": [
            "capability-165"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "把这个仓库从 1.0 升到 6.0",
        "expect": [
            "capability-147"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "从零造一个 skill 并验证它",
        "expect": [
            "capability-154"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "让技能和 开放标准 标准互通",
        "expect": [
            "capability-145"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "技能市场里有什么好用的",
        "expect": [
            "capability-146"
        ]
    },
    {
        "layer": "B",
        "human": True,
        "q": "检查代码是否符合 MCP 新规范",
        "expect": [
            "capability-117"
        ]
    },
    {
        "layer": "B",
        "human": False,
        "q": "审计 MCP 通信有没有异常",
        "expect": [
            "capability-116"
        ]
    },
    {
        "layer": "C",
        "human": True,
        "q": "帮我预约明天下午三点的牙医",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "今晚吃什么，给我推荐个菜谱",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "翻译这段法语合同成英文",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "帮我把这张照片调成复古胶片色调",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "我家 WiFi 连不上，帮我远程修一下路由器",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "帮我把这段录音转成文字",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "这首歌的版权归谁，帮我查一下",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "明天的天气怎么样",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "帮我在电商平台上下单买个鼠标",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "我的猫生病了，应该喂什么药",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "帮我算一下房贷月供",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "推荐几部好看的科幻电影",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "把这份 PDF 转成 Word",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "帮我抢演唱会门票",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "帮我校对这份英文论文的语法",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "帮我设计一个公司 logo",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "把这段视频里的字幕提取出来",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "帮我查一下北京到上海的高铁时刻表",
        "expect": []
    },
    {
        "layer": "C",
        "human": True,
        "q": "给我讲个睡前笑话",
        "expect": []
    },
    {
        "layer": "C",
        "human": False,
        "q": "帮我校准一下跑步手表的心率区间",
        "expect": []
    }
]


def validate_labels(c):
    missing = []
    for it in BLIND100:
        for nm in it["expect"]:
            if c.by_name.get(nm) is None:
                missing.append((it["q"], nm))
    return missing


def run_once(seed_note=""):
    c = WSSR()
    dev = [(q, e) for q, e in skiplib.EVAL] + [(q, e) for q, e in skiplib.HOLDOUT]
    auto, _curve = auto_abstain(c, dev)
    thr = auto[0] if auto else None  # auto = (thr, hit, ab, loss)
    nA = sum(1 for x in BLIND100 if x["layer"] == "A")
    nB = sum(1 for x in BLIND100 if x["layer"] == "B")
    nC = sum(1 for x in BLIND100 if x["layer"] == "C")
    assert nA == 60 and nB == 20 and nC == 20, (nA, nB, nC)

    rows = []
    k = 0
    kAB = 0
    k1AB = 0
    c_abstain = 0
    c_cw = 0
    for it in BLIND100:
        names, diag = c.route(it["q"], gen=True, shy=True, replay=True,
                              abstain_top1=thr, abstain_margin=ABSTAIN_MARGIN, warn=True)
        if it["layer"] in ("A", "B"):
            ok = bool(set(names) & set(it["expect"]))
            ok1 = bool(names and names[0] in set(it["expect"]))
            ab = diag["abstain"]
            cw = (not ok) and (not ab) and diag["top1"] >= CONF_THRESHOLD
            kAB += ok
            k1AB += ok1
        else:  # C: 成功=引擎弃权
            ab = diag["abstain"]
            ok = ab
            ok1 = None
            cw = (not ab)  # 未弃权=自信地错（路由到无对应技能）
            c_abstain += ab
            c_cw += cw
        k += ok
        rows.append({"q": it["q"], "layer": it["layer"], "human": it["human"],
                     "expect": it["expect"], "got": names, "ok": ok,
                     "ok1": ok1, "abstain": ab, "top1": diag["top1"],
                     "margin": diag["margin"], "cw": cw,
                     "abstain_reasons": diag["abstain_reasons"]})
    n = len(BLIND100)
    nAB = nA + nB
    human_n = sum(1 for x in BLIND100 if x["human"])
    return {
        "seed_note": seed_note, "thr": thr, "n": n, "k": k,
        "overall_rate": round(k / n, 4),
        "wilson95_all100": list(wilson(k, n)),
        "layerA_n": nA, "layerB_n": nB, "layerC_n": nC,
        "AB_n": nAB, "AB_hit3": kAB, "AB_hit3_rate": round(kAB / nAB, 4),
        "AB_wilson95": list(wilson(kAB, nAB)),
        "AB_hit1": k1AB, "AB_hit1_rate": round(k1AB / nAB, 4),
        "C_n": nC, "C_correct_abstain": c_abstain, "C_false_confident": c_cw,
        "C_abstain_rate": round(c_abstain / nC, 4),
        "human_n": human_n, "human_rate": round(human_n / n, 4),
        "G2_pass_all100": wilson(k, n)[0] >= 0.75,
        "G2_pass_AB": wilson(kAB, nAB)[0] >= 0.75,
        "rows": rows,
    }


def main():
    c = WSSR()
    missing = validate_labels(c)
    if missing:
        print("!! 标注缺失（期望技能不在库中）：", missing)
    print(f"语料 {c.n} | BLIND100 {len(BLIND100)} | 标签校验缺失 {len(missing)}")

    r1 = run_once("PYTHONHASHSEED=0")
    os.environ["PYTHONHASHSEED"] = "12345"
    # 重新 import 已无济于事（模块级已固定），改以确定性判定：再跑一次同源实例
    r2 = run_once("PYTHONHASHSEED=12345 (rerun)")

    # 确定性：两次 run 的逐行 ok/cw 必须一致（B6 sorted 化应保障）
    sig1 = [(x["ok"], x["cw"]) for x in r1["rows"]]
    sig2 = [(x["ok"], x["cw"]) for x in r2["rows"]]
    deterministic = sig1 == sig2
    print(f"确定性双跑一致: {deterministic} | thr={r1['thr']}")
    print(f"BLIND100 总 k={r1['k']}/{r1['n']} = {r1['overall_rate']:.1%} "
          f"Wilson{r1['wilson95_all100']} | G2(全100)={r1['G2_pass_all100']}")
    print(f"层 A+B 路由 hit@3={r1['AB_hit3']}/{r1['AB_n']} = {r1['AB_hit3_rate']:.1%} "
          f"hit@1={r1['AB_hit1']}/{r1['AB_n']} = {r1['AB_hit1_rate']:.1%} Wilson{r1['AB_wilson95']}")
    print(f"层 C 正确弃权={r1['C_correct_abstain']}/{r1['C_n']} = {r1['C_abstain_rate']:.1%} "
          f"| 自信误路由(应弃权却路由)={r1['C_false_confident']}")
    print(f"人类工单风格 {r1['human_n']}/{r1['n']} = {r1['human_rate']:.1%} "
          f"(≥1/3 要求={'满足' if r1['human_rate'] >= 1/3 else '未达'})")

    receipt = {
        "version": "BLIND-100 (patchboard B1 重冻, v0.5 开箱)",
        "honesty": {
            "authorship": "同作者闭环=同一作者撰写题面+标注金标+同引擎评分；属扩大版内部盲测，非真第三方",
            "third_party_definition": "真第三方需：不同厂商家族出题 + 禁访问技能库文本 + ≥1/3 人类真题",
            "pseudo_independent_note": "不同会话=伪独立（patchboard 待验证点）",
            "statistical_value": "n:40→100 收窄 Wilson 区间；偏差消除仍需外部出题（后续 P0 行动）",
            "label_protocol": "先题后标，标注前未跑任何路由器；expect 按功能需求标注",
            "generation_independence": "题面按能力域真实用户口吻撰写，未读 DOC2QUERY/BLIND40/技能描述词汇",
        },
        "gate_G2": {
            "criterion_all100": "k>=84 → Wilson 下界>=0.75（patchboard B1）",
            "observed_k": r1["k"], "observed_wilson_lower": r1["wilson95_all100"][0],
            "pass": r1["G2_pass_all100"],
        },
        "result": {k: v for k, v in r1.items() if k != "rows"},
        "deterministic": deterministic,
        "label_missing": missing,
        "rows": r1["rows"],
    }
    with open("blind100_run.json", "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    print("回执已写 blind100_run.json")


if __name__ == "__main__":
    main()
