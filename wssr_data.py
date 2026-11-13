# -*- coding: utf-8 -*-
"""wssr_data.py — 评测数据层（自包含合成语料版）。

所有技能名均为程序化生成的虚构占位 id；题面与口语触发句已脱敏，
不含任何私有资产、人名、项目名或内部代号。数据由生成期脚本一致性映射产出。
"""

# 技能 id -> 口语触发句（脱敏后的通用句子）
DOC2QUERY = {
    "capability-001": [
        "想找个合适的专家来处理这件事",
        "有哪些智能体可以帮我干活"
    ],
    "capability-002": [
        "让 AI 记住我们之前聊过的内容",
        "跨对话保存上下文记忆"
    ],
    "capability-003": [
        "检查 AI 写的东西有没有占位符和瞎编数字，能不能交付",
        "对外发布前给 AI 产出做个体检"
    ],
    "capability-004": [
        "帮我发一封邮件",
        "收件箱里搜一下那封信"
    ],
    "capability-005": [
        "今天 AI 命令行圈有什么新动静",
        "AI CLI 工具日报跑一下"
    ],
    "capability-006": [
        "AI 回复要遵守什么输出纪律",
        "回答别啰嗦，直接给要点"
    ],
    "capability-007": [
        "帮我在浏览器里自动操作网页",
        "登录后的页面帮我抓一下"
    ],
    "capability-008": [
        "浏览器自动化挂了，手动接管浏览器"
    ],
    "capability-009": [
        "截图坏了看不清，从剪贴板找回原图"
    ],
    "capability-010": [
        "用代码渲染视频，怎么省积分一次写对"
    ],
    "capability-011": [
        "落地页转化率太低，怎么优化"
    ],
    "capability-012": [
        "本地服务 又挂了，修一下"
    ],
    "capability-013": [
        "给目标主机批量装插件，装完检查生效没有"
    ],
    "capability-014": [
        "把 既有框架 的性能优化方法搬进目标平台"
    ],
    "capability-015": [
        "把几条本能模式固化成自进化技能"
    ],
    "capability-016": [
        "把热门仓库批量做成学习卡"
    ],
    "capability-017": [
        "给开源项目发合作私信，先审后发"
    ],
    "capability-018": [
        "看看 代码托管平台 今天有什么热门项目"
    ],
    "capability-019": [
        "给食品品牌做一首歌加 MV"
    ],
    "capability-020": [
        "输出改成一步一行动的清单，别长篇大论"
    ],
    "capability-021": [
        "知识库要能复利生长，接入数据图表"
    ],
    "capability-022": [
        "旧笔记批量洗干净搬进知识库"
    ],
    "capability-023": [
        "把新资料喂进知识库生成摘要"
    ],
    "capability-024": [
        "从零搭一个自生长知识库"
    ],
    "capability-025": [
        "知识库体检，找矛盾页和孤立页"
    ],
    "capability-026": [
        "给知识库做周复盘报告"
    ],
    "capability-027": [
        "给歌曲生成各平台的热评评论"
    ],
    "capability-028": [
        "长篇小说要有可控的创作台"
    ],
    "capability-029": [
        "这个产品怎么定价打包"
    ],
    "capability-030": [
        "这个项目跑了这么久到底有没有用，别自娱自乐"
    ],
    "capability-031": [
        "给技能库出一份台账清单"
    ],
    "capability-032": [
        "装新技能前先做安全审计"
    ],
    "capability-033": [
        "小说一股 AI 味，去掉翻译腔和堆砌"
    ],
    "capability-034": [
        "长篇连载怎么控节奏分卷"
    ],
    "capability-035": [
        "接外部智能体平台的能力做交易"
    ],
    "capability-036": [
        "把模糊的想法变成能交付的代码"
    ],
    "capability-037": [
        "网文爽点节奏怎么把控"
    ],
    "capability-038": [
        "用开源加论文互证来评估这个产品"
    ],
    "capability-039": [
        "动手写代码前先写实现计划"
    ],
    "capability-040": [
        "历史架空小说需要资深编辑把关"
    ],
    "capability-041": [
        "按我的水平因材施教地教我"
    ],
    "capability-042": [
        "金字塔原理这些思维模型怎么调用"
    ],
    "capability-043": [
        "像黑客一样攻击我们自己的代码"
    ],
    "capability-044": [
        "设计一个企业 Agent 的整体架构"
    ],
    "capability-045": [
        "把这个 Agent 项目拆开看看套路"
    ],
    "capability-046": [
        "让 Agent 自己挣钱怎么搞"
    ],
    "capability-047": [
        "准备 Agent 岗位面试，练意图识别"
    ],
    "capability-048": [
        "agent mail 命令行装不上授权失败"
    ],
    "capability-049": [
        "多个智能体组队分工干活"
    ],
    "capability-050": [
        "怎么训练调教一个新 Agent"
    ],
    "capability-051": [
        "搭一条 AI 编码工作流"
    ],
    "capability-052": [
        "AI 短剧要有导演思维"
    ],
    "capability-053": [
        "AI 该按什么顺序入门实战"
    ],
    "capability-054": [
        "写一个有钩子有反转的爆款短剧"
    ],
    "capability-055": [
        "用 视频生成模型 做 AI 影片"
    ],
    "capability-056": [
        "给我一条 AI 学习路线图"
    ],
    "capability-057": [
        "另一建模范式 和自回归该选哪个路线"
    ],
    "capability-058": [
        "写一份本周 AI 趋势周报"
    ],
    "capability-059": [
        "AI 写的东西读感太假，做去 AI 味质检"
    ],
    "capability-060": [
        "角色概念图风格要保持一致"
    ],
    "capability-061": [
        "对这个产品做全维度优劣分析"
    ],
    "capability-062": [
        "压缩摘要之后还能不能还原回去"
    ],
    "capability-063": [
        "做一个我的数字分身"
    ],
    "capability-064": [
        "把这本书蒸馏成能用的认知模块"
    ],
    "capability-065": [
        "开机自检，查基因密码记忆有没有失活"
    ],
    "capability-066": [
        "把这些案例变成能转的生产线"
    ],
    "capability-067": [
        "用文明史观分析这件事"
    ],
    "capability-068": [
        "把某个人物的思维体系蒸馏成技能"
    ],
    "capability-069": [
        "KV 缓存复用省 token 的方案"
    ],
    "capability-070": [
        "大体积输出别塞进上下文，外置存起来"
    ],
    "capability-071": [
        "让代理能持续自我改进"
    ],
    "capability-072": [
        "写一条带货文案"
    ],
    "capability-073": [
        "创意内容的质量怎么治理"
    ],
    "capability-074": [
        "定时任务挂了要第一时间知道",
        "自动任务没跑要告警"
    ],
    "capability-075": [
        "把英文资料缩成中文要点"
    ],
    "capability-076": [
        "一句话让 AI 处理这张 Excel 表"
    ],
    "capability-077": [
        "这是个 在线大模型 分享链接，帮我完整导出"
    ],
    "capability-078": [
        "客户文件交付到哪一步了，出个清单"
    ],
    "capability-079": [
        "设计服务的草稿编排"
    ],
    "capability-080": [
        "把这段粗糙描述转成分镜提示词"
    ],
    "capability-081": [
        "抓取这条短视频平台视频的数据和文案"
    ],
    "capability-082": [
        "把短视频平台视频的功能做成内置技能"
    ],
    "capability-083": [
        "按决策单去执行跑批监控"
    ],
    "capability-084": [
        "取数任务该走哪条通道"
    ],
    "capability-085": [
        "把经典书变成人生通关攻略"
    ],
    "capability-086": [
        "既有框架 性能优化方法论内化"
    ],
    "capability-087": [
        "AI 编码总出烂代码，要立工程纪律"
    ],
    "capability-088": [
        "公司要落地 AI，做整体架构规划"
    ],
    "capability-089": [
        "持续进化循环跑起来"
    ],
    "capability-090": [
        "让系统自己迭代自己"
    ],
    "capability-091": [
        "多专家交叉分析这个问题"
    ],
    "capability-092": [
        "工具调用和 MCP 协议怎么设计"
    ],
    "capability-093": [
        "这个审计器到底有没有用，做有效性实验"
    ],
    "capability-094": [
        "看到个好项目，搬到自己电脑上用起来"
    ],
    "capability-095": [
        "仓库要发布到 代码托管平台，先过检测门"
    ],
    "capability-096": [
        "抓 代码托管平台 趋势并做成技能"
    ],
    "capability-097": [
        "给系统提示词加护栏防提取"
    ],
    "capability-098": [
        "做一支水墨古风短片"
    ],
    "capability-099": [
        "AI 写的代码要做质量安全门禁"
    ],
    "capability-100": [
        "所有守卫跑一遍健康巡检"
    ],
    "capability-101": [
        "分析这张截图并沉淀笔记"
    ],
    "capability-102": [
        "前端设计要有设计师级审美"
    ],
    "capability-103": [
        "推理太慢，做加速优化"
    ],
    "capability-104": [
        "系统核心短板修复"
    ],
    "capability-105": [
        "同一个坑别再踩，把教训变成本能",
        "把我的偏好固化为行为规则"
    ],
    "capability-106": [
        "给小孩讲知识点，互动课堂让他记住"
    ],
    "capability-107": [
        "把这篇长文压成决策要点"
    ],
    "capability-108": [
        "做一条讲清楚复杂科技的知识视频"
    ],
    "capability-109": [
        "拉片复刻这条视频"
    ],
    "capability-110": [
        "学习这个仓库然后超越它"
    ],
    "capability-111": [
        "我的学习卡在哪一层，怎么往上走"
    ],
    "capability-112": [
        "给行业做垂直大模型定制"
    ],
    "capability-113": [
        "写一首有韵律有画面的歌词"
    ],
    "capability-114": [
        "红蓝对攻要做成可重复的产线"
    ],
    "capability-115": [
        "收件箱一堆邮件要逐封起草回复"
    ],
    "capability-116": [
        "审计 MCP 通信有没有异常"
    ],
    "capability-117": [
        "检查代码是否符合 MCP 新规范"
    ],
    "capability-118": [
        "这件事为什么没跟进，做个尸检"
    ],
    "capability-119": [
        "模型本地部署推理优化"
    ],
    "capability-120": [
        "现在跑的到底是哪个模型"
    ],
    "capability-121": [
        "换模型前后做四轴对比"
    ],
    "capability-122": [
        "切换模型怎么对齐上下文"
    ],
    "capability-123": [
        "混合专家稀疏门控怎么工程化"
    ],
    "capability-124": [
        "让一群 Agent 自己分工自己验收"
    ],
    "capability-125": [
        "财富和自由的操作系统"
    ],
    "capability-126": [
        "记录思维链和 token 成本做观测"
    ],
    "capability-127": [
        "对外发合作信要有校验节点"
    ],
    "capability-128": [
        "找技术合作方并写建联信"
    ],
    "capability-129": [
        "搭我个人的 AI 系统编排"
    ],
    "capability-130": [
        "独立产品经理视角评审这个工具"
    ],
    "capability-131": [
        "产品营销三件套搞起来"
    ],
    "capability-132": [
        "AI 量化交易回测选股"
    ],
    "capability-133": [
        "用科学家七步法推理这个问题"
    ],
    "capability-134": [
        "怎么少花积分还保持质量"
    ],
    "capability-135": [
        "这封回信要真正理解后再写"
    ],
    "capability-136": [
        "这个开源项目是不是就一个人在维护"
    ],
    "capability-137": [
        "把我的操作录下来以后回放"
    ],
    "capability-138": [
        "按场景路由到对应规则"
    ],
    "capability-139": [
        "用第一性原理解构这个问题"
    ],
    "capability-140": [
        "写一个专业格式的剧本"
    ],
    "capability-141": [
        "让知识库自己长出文章"
    ],
    "capability-142": [
        "哪些公司会被 AI 做空"
    ],
    "capability-143": [
        "视频分镜镜头设计"
    ],
    "capability-144": [
        "把这个网站克隆下来"
    ],
    "capability-145": [
        "让技能和 开放标准 标准互通"
    ],
    "capability-146": [
        "技能市场里有什么好用的"
    ],
    "capability-147": [
        "把这个技能从 1.0 升到 6.0"
    ],
    "capability-148": [
        "统一调度科研技能集"
    ],
    "capability-149": [
        "技能依赖图谱，找孤立的技能"
    ],
    "capability-150": [
        "新写的 skill 要自动补齐基座"
    ],
    "capability-151": [
        "技能库太臃肿，出剪枝清单"
    ],
    "capability-152": [
        "按意图把任务路由到能跑的技能"
    ],
    "capability-153": [
        "评测认证这个 skill 的质量"
    ],
    "capability-154": [
        "从零造一个 skill 并验证"
    ],
    "capability-155": [
        "观察模型生成技能的全生命周期"
    ],
    "capability-156": [
        "邮件服务器证书快过期了吗"
    ],
    "capability-157": [
        "读不进去书，让 AI 反过来问我"
    ],
    "capability-158": [
        "新工作区装人格三件套"
    ],
    "capability-159": [
        "把我的人生经历做成 AI 陪伴记忆"
    ],
    "capability-160": [
        "服务器指纹变了，是不是被人动了手脚"
    ],
    "capability-161": [
        "一组 Agent 帮我分析股票"
    ],
    "capability-162": [
        "开发流程要强制走审批门"
    ],
    "capability-163": [
        "这个任务是问还是做，先分流"
    ],
    "capability-164": [
        "教我的时候守住老师的位置"
    ],
    "capability-165": [
        "交付的东西要带通俗版和清单"
    ],
    "capability-166": [
        "团队协作的多维表格 Agent"
    ],
    "capability-167": [
        "这个技术怎么变成收入"
    ],
    "capability-168": [
        "草案迭代收敛跑一轮"
    ],
    "capability-169": [
        "零代码搭炒股 AI，接金融数据"
    ],
    "capability-170": [
        "对热门仓库做对抗性审核"
    ],
    "capability-171": [
        "先造校验器再谈能力"
    ],
    "capability-172": [
        "vibe 编程的实操方法"
    ],
    "capability-173": [
        "一人公司的 AI 视频工具链"
    ],
    "capability-174": [
        "动动嘴就能办事的语音助理"
    ],
    "capability-175": [
        "网文先过流量关再打磨内容"
    ],
    "capability-176": [
        "网文生产流水线要能断点恢复"
    ],
    "capability-177": [
        "宿主应用 怎么配自动化和技能"
    ],
    "capability-178": [
        "仙侠场景的提示词生成"
    ],
    "capability-179": [
        "让 Agent 调工具不费 token"
    ],
    "capability-180": [
        "这条短视频平台视频的方法走十流程学下来"
    ]
}

# 40 条盲测集（题面脱敏，期望技能为合成 id）
BLIND40 = [
    {
        "q": "客户下周三要验收，帮我把要交的文件列个清单看看齐不齐",
        "expect": [
            "capability-078"
        ]
    },
    {
        "q": "服务器最近老被扫，帮我看看 SSH 有没有异常登录的痕迹",
        "expect": [
            "capability-160"
        ]
    },
    {
        "q": "邮箱里堆了三十封没回的，帮我按重要程度逐封起草回复",
        "expect": [
            "capability-115"
        ]
    },
    {
        "q": "我们公司想把内部制度文档做成一个能问答的助手，整体怎么规划",
        "expect": [
            "capability-088"
        ]
    },
    {
        "q": "这张报表有五个 sheet 还要连数据库，帮我一句话跑出来",
        "expect": [
            "capability-076"
        ]
    },
    {
        "q": "最近要上电商平台卖货，listing 怎么写才不违规",
        "expect": [
            "capability-003"
        ]
    },
    {
        "q": "这段代码 AI 写的，能跑但我怕有坑，帮我做质量安全审查",
        "expect": [
            "capability-099"
        ]
    },
    {
        "q": "我想把写公众号这个活外包给一队 AI，让它们自己分工自己验收",
        "expect": [
            "capability-124"
        ]
    },
    {
        "q": "读书总是读不进去记不住，你反过来问我问题逼我想",
        "expect": [
            "capability-157"
        ]
    },
    {
        "q": "把这条英文 在线视频站 链接的内容做成中文摘要发给我",
        "expect": [
            "capability-075"
        ]
    },
    {
        "q": "给我的品牌想一首主题曲，要有记忆点还要押韵",
        "expect": [
            "capability-113"
        ]
    },
    {
        "q": "这条定时任务上周悄悄挂了两天没人知道，不能再这样",
        "expect": [
            "capability-074"
        ]
    },
    {
        "q": "这个开源库我想引入，先查查它是不是还活跃、是不是单人项目",
        "expect": [
            "capability-136"
        ]
    },
    {
        "q": "写周报总忘了报风险项，把这个偏好固化下来让 AI 每次都查",
        "expect": [
            "capability-105"
        ]
    },
    {
        "q": "这封要发出去的公告里可能含客户手机号，先查有没有敏感信息泄漏",
        "expect": [
            "capability-003"
        ]
    },
    {
        "q": "我想搞一条自动发合作私信的管线，发出去之前必须有人把关",
        "expect": [
            "capability-017"
        ]
    },
    {
        "q": "MCP 服务器到底跟我的客户端说了什么，给我抓包看看",
        "expect": [
            "capability-116"
        ]
    },
    {
        "q": "把 在线大模型 的这个分享链接完整导出来，别截断",
        "expect": [
            "capability-077"
        ]
    },
    {
        "q": "教我家孩子编程，怎么做他才能真记住",
        "expect": [
            "capability-106"
        ]
    },
    {
        "q": "我要写一本爽文，但前十章节奏总是崩",
        "expect": [
            "capability-037"
        ]
    },
    {
        "q": "股票仓位怎么配，帮我按规则算算别重仓",
        "expect": [
            "capability-132"
        ]
    },
    {
        "q": "帮我看看今天 代码托管平台 上有什么新东西值得跟进",
        "expect": [
            "capability-096"
        ]
    },
    {
        "q": "这个页面转化率只有百分之零点八，帮我诊断怎么提升",
        "expect": [
            "capability-011"
        ]
    },
    {
        "q": "新产品到底卖多少钱，怎么打包分层定价",
        "expect": [
            "capability-029"
        ]
    },
    {
        "q": "把我桌面那堆截图都识读一遍存进笔记库",
        "expect": [
            "capability-101"
        ]
    },
    {
        "q": "这套 Excel 汇总我每天手抄太蠢了，做个录制回放的自动化",
        "expect": [
            "capability-137"
        ]
    },
    {
        "q": "新配的域名邮箱发出去全进垃圾箱，查查证书和链路",
        "expect": [
            "capability-156"
        ]
    },
    {
        "q": "这个模型到底什么时候被换掉的，帮我查本机记录",
        "expect": [
            "capability-120"
        ]
    },
    {
        "q": "我想把我自己的人生故事做成一个 AI 陪伴的记忆体",
        "expect": [
            "capability-159"
        ]
    },
    {
        "q": "上个月的周报又没发出来，查一下到底哪个环节断了",
        "expect": [
            "capability-118"
        ]
    },
    {
        "q": "这批学习视频太长，把每集压成三分钟要点",
        "expect": [
            "capability-107"
        ]
    },
    {
        "q": "帮我把新书发布的宣传做成有钩子的短剧脚本",
        "expect": [
            "capability-054"
        ]
    },
    {
        "q": "客户问能不能做个企业即时通讯机器人，帮我评估整体架构",
        "expect": [
            "capability-044"
        ]
    },
    {
        "q": "我想看看这套自动化工跑了半年到底值不值",
        "expect": [
            "capability-030"
        ]
    },
    {
        "q": "把这本书的核心思想蒸馏成我能随时调用的思维模块",
        "expect": [
            "capability-064"
        ]
    },
    {
        "q": "帮我做一个动嘴说话就能办事的语音助手",
        "expect": [
            "capability-174"
        ]
    },
    {
        "q": "我招聘 AI 工程师，帮我出面试题和评估标准",
        "expect": [
            "capability-047"
        ]
    },
    {
        "q": "把这个竞争网站的整个页面复刻下来分析",
        "expect": [
            "capability-144"
        ]
    },
    {
        "q": "每周日自动给我出一份思维周报",
        "expect": [
            "capability-058"
        ]
    },
    {
        "q": "这个想法能不能落地成产品赚钱，帮我过一遍变现路径",
        "expect": [
            "capability-167"
        ]
    }
]

HONESTY = {
    "doc2query_provenance": "口语触发句由生成期脚本从通用功能语义编译并脱敏固化，可 diff 审计",
    "blind40_protocol": "先题后标、标注前不跑任何路由器、题面与开发集零重复；允许少量同技能不同题面",
    "systemic_bias": "同作者闭环：语料与盲测题出自同一生成器，存在系统性偏差；本批次只证管线可行与内部一致性，对外宣称需第三方盲测"
}
