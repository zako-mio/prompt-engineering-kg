#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-nodes.py —— 节点页生成器（只落 `content_status = complete` 的节点）

输出：`11-node-pages/<小写 id>.html`，全部经 gen-common.page_shell 产出。

★ 形态 v2（2026-10-15 用户走查第 2 轮反馈后重做；契约见 `16-checkpoint/CONTENT-V2.md`）：
  ① 标题区：`h1` = **纯中文名**（一行）＋ 英文名**独立成行、去括号**（反馈 #4）；
  ② 一行一件事：身份行 / 标签行 分离（反馈 #6）；
  ③ 页首导读：**先给一句话结论**，再给可跳转的结构地图（反馈 #2）；
  ④ 散文 → 主张句 + 展开点（每句一行）+ 独立「适用边界」块（反馈 #2）；
  ⑤ 该用 / 不该用 → **对照表**（类别 ｜ 场景 ｜ 做法），每条按全角冒号切「总结 / 细节」（反馈 #7）；
  ⑥ 证据 / 术语 → 表；原文与代码 → `<details>` 渐进披露（反馈 #3）；
  ⑦ 每页一张**内联 SVG 自制图**（反馈 #3）。
  ⛔ 不改 `dag.json` 任何字段值；⛔ 不新增内联脚本（P09 断言每页内联脚本恰 1 条）。
"""

import importlib.util
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _imp(os.path.join(HERE, "gen-common.py"), "pekg_common")

BASE = "../"

WHEN_AVOID_PREFIX = "不适用于"

# 页首结构地图与区块序号：**站点级约定**（⛔ 不是逐节点内容），顺序即阅读顺序。
SECTIONS = (
    ("sec-why", "为什么需要它", 1),
    ("sec-intro", "机制说明", 2),
    ("sec-when", "何时该用 / 何时不该用", 3),
    ("sec-lab", "实验台", 4),
    ("sec-evidence", "证据", 5),
    ("sec-terms", "术语", 6),
    ("sec-pitfalls", "失效模式", 7),
    ("sec-rel", "在本站知识结构中的位置", 8),
)

# 每页一张自制图（键 = 节点 id；图件由 `gen-figs.py` 预渲染入库）
# ★ P35 ⑧ 要求**每个节点页 ≥1 图**，且 `figure_html` 对缺失图 id **静默返回空串**（不会报错）
#   ⇒ 新增节点页时必须**成对**新增：`gen-figs.FIGS` 一条 + 本表一条，并跑 `gen-figs.py --write`。
NODE_FIG = {
    "PE-F-01": ("pe-f-01", "机制图：从概率分布到确定性边界——三类工程手段各自作用在哪一步。"),
    "PE-F-02": ("pe-f-02", "分层图：三层的稳定性与特权递减，以及「缓存命中面」恰好切在稳定前缀与易变后缀之间。"),
    "PE-F-03": ("pe-f-03", "结构图：四类内容各自被固定标签划出边界后交给模型解析，与「连成一段的裸文本」对照。"),
    "PE-F-04": ("pe-f-04", "收益曲线图：示例从 0 到 3 到 10 的边际收益，以及它在推理模型上发生的符号反转。"),
    "PE-F-05": ("pe-f-05", "双维图：具体性（说多少细节）与可验证性（能否判定）方向相反却不矛盾，因为对象不同。"),
    "PE-F-06": ("pe-f-06", "位置图：同一关键信息在首/中/尾三处的可用性差异，以及由此推出的三个工程动作。"),
    "PE-R-02": ("pe-r-02", "对照图：同一技巧在两类条件下符号相反，以及判定纪律。"),
    "PE-P-02": ("pe-p-02", "结构图：技能文件的「主文件 + 按需展开」与旧写法的对照。"),
    # ★ 2026-10-16 内容波次 2：G01「确定性输出」的 5 条（★ 与 `gen-figs.FIGS` 成对，
    #   caption 两处**逐字同文**：一条只加在一侧 ⇒ 节点页 P35 ⑧ 缺图 FAIL）。
    "PE-S-01": ("pe-s-01", "机制图：约束解码在生成期屏蔽非法路径——从概率分布到「过滤后再取样」，与「生成后校验」的位置对照。"),
    "PE-S-02": ("pe-s-02", "分档图：自然语言要求 / 结构契约 / 约束解码三档的强度递增，与成本、可移植性的同向递减。"),
    "PE-S-03": ("pe-s-03", "对照图：同一任务在「先自由推理后格式化」与「边推理边守 schema」两种形态下的推理预算与质量差异。"),
    "PE-S-04": ("pe-s-04", "选型图：同一份信息在四种格式下的相对体积（条宽即相对 token 量），与三个选型判据。"),
    "PE-S-05": ("pe-s-05", "回路图：生成 → 校验 → 把具体错误回喂 → 重生成的限次闭环，以及超限样本的处置。"),
    # ★ 2026-10-16 内容波次 3：22 条（G02 7 + G05 9 + G06 6）。与 `gen-figs.FIGS` 成对，
    #   caption 两处**逐字同文**：一条只加在一侧 ⇒ 节点页 P35 ⑧ 缺图 FAIL。
    "PE-A-01": ("pe-a-01", "层级图：系统 > 开发者 > 用户 > 外部内容的特权递减，三层实现路径（提示 / 训练 / 架构），以及「降低而非消除、必须配合权限收窄」。"),
    "PE-A-02": ("pe-a-02", "攻击面图：直接注入与间接注入两类路径，三条放大危害的属性，以及「模型架构上不区分指令与数据 ⇒ 无可靠拦截式预防」这一反直觉结论。"),
    "PE-A-03": ("pe-a-03", "阶段映射图：十大风险按工程阶段分派为四组检查项（设计 / 接入 / 上线 / 运行），以及「覆盖检查表而非合规认证、引用必须标版本」。"),
    "PE-A-04": ("pe-a-04", "权衡图：过拒的三类成因、三条改进方向，以及「拦截率与过拒率必须双向度量」的度量纪律与业务侧落点。"),
    "PE-A-05": ("pe-a-05", "改写对照图：负向提示「不要做 X」反而激活 X 的机制、改写成期望行为的前后对照，以及无法正向化时的可判定处置规则。"),
    "PE-A-06": ("pe-a-06", "四步隔离图：标注 / 声明 / 收窄 / 校验四个动作，以及「提示层的标注不构成安全边界、权限收窄才是关键」的分界。"),
    "PE-E-01": ("pe-e-01", "三件套结构图：评测集的输入 / 期望输出 / 判据，两类判据的先后关系，以及按失败模式分层与版本化的两条组织要求。"),
    "PE-E-02": ("pe-e-02", "构造动作图：测试集的四个构造动作（真实采样 / 失败模式分层 / 负例与边界例 / 判据与容差）、留出集，及「只收典型样本」的对照。"),
    "PE-E-03": ("pe-e-03", "偏差对照图：模型即裁判的四类系统性偏差与各自的缓解手段，以及「确定性断言优先、模型裁判只做相对比较」的并用纪律。"),
    "PE-E-04": ("pe-e-04", "三层落地图：本地批量 / 持续集成回归 / 对抗评测三层工具链，断言类型的二分，以及红蓝对抗必须同时报告「攻击成功率」与「正常请求拒绝率」。"),
    "PE-E-05": ("pe-e-05", "自动优化回路图：生成候选 → 评测集评估 → 选择或组合 → 必要时迭代的闭环，与三条工程要点（留出集、可自动计算的判据、搜索预算）。"),
    "PE-E-06": ("pe-e-06", "编译流水线图：签名 / 模块 / 优化器三个构件与「按指标搜索产出指令与示例」的编译过程，以及选型两轴与「无单一最优」的官方边界。"),
    "PE-E-07": ("pe-e-07", "两条优化路线对照图：文本梯度把自然语言评价当梯度回传到各组件，反思式进化由执行轨迹生成改进规则；共同前提是轨迹与评分函数。"),
    "PE-E-08": ("pe-e-08", "层次图：元提示处在被优化对象的上一层、三种典型用法，以及「提高候选生成速度、判定权仍在评测集」的对照纪律。"),
    "PE-E-09": ("pe-e-09", "版本—回归图：提示词版本与评测基线必须成对留档、换模型必须重建基线，以及「跑全量」「同时跟踪成本与延迟」两条回归纪律。"),
    "PE-R-01": ("pe-r-01", "判据分流图：按「模型类别 × 任务串行深度」决定写不写显式推理指令，并把思考内容的回传约束单列。"),
    "PE-R-03": ("pe-r-03", "曲线对照图：自一致性的两个前提与样本数收益的早期饱和，以及系统偏见下「路径同错、投票放大置信度」。"),
    "PE-R-04": ("pe-r-04", "搜索结构图：从候选思维到评估、展开与剪枝的树状搜索拓扑（含被丢弃的分支），以及思维图允许的中间结果合并。"),
    "PE-R-05": ("pe-r-05", "轻量替代图：完整树搜索之下，步骤回溯与改写择优两类做法的共同前提（判据）与共同闸门（次数上限）。"),
    "PE-R-06": ("pe-r-06", "压缩比对照图：原报告的最优极简程度与代码任务上的实测节省幅度差距悬殊，以及质量损失与「预算也是待调参量」。"),
    "PE-R-07": ("pe-r-07", "循环图：ReAct 的「思考—行动—观察」三步回路，三条现行实现路径，以及四类失效计数与轮数上限。"),
    "PE-R-08": ("pe-r-08", "强度阶梯图：自评 / 独立评估 / 外部信号驱动三种反思来源的可靠性递增，与纯自评对事实性错误的失灵机制。"),
    # ★ 2026-10-16 内容波次 4：G07 4 条（PE-M-01…04）+ G08 3 条（PE-V-01…03）+ G09 6 条
    #   （PE-P-01 / PE-P-03…07）。与 `gen-figs.FIGS` 成对，caption 两处**逐字同文**：
    #   一条只加在一侧 ⇒ 节点页 P35 ⑧ 缺图 FAIL（`figure_html` 对缺失图 id 静默返回空串）。
    "PE-M-01": ("pe-m-01", "机制图：请求按难度分派到不同档位、弱档失败再升档，以及「各档各自建基线 + 档位写成配置」两个前提。"),
    "PE-M-02": ("pe-m-02", "对照图：同一套标记写法在两个模型上收益相反、标记泄漏这一判据，以及按模型维护标记配置的应对。"),
    "PE-M-03": ("pe-m-03", "流程图：换模型后的四步固定动作（建新基线 → 分离差异 → 针对性调整 → 跑全量回归），以及「哪些必须重建、哪些可以复用」。"),
    "PE-M-04": ("pe-m-04", "权衡图：三项指标互相牵制、三组典型取舍，以及「先定质量下限与延迟上限，再在约束内压成本」的工程做法。"),
    "PE-V-01": ("pe-v-01", "结构图：文本与图像交错成序列的三种排布写法与其指代构造要点（可靠性须按目标模型实测），以及三条设计要点与一条边界。"),
    "PE-V-02": ("pe-v-02", "两段图：把「先定位再推断」拆成可复核的中间读数，以及不可信图像与不可信文本同等设防。"),
    "PE-V-03": ("pe-v-03", "位置图：文本长上下文实测的首尾优先与中段退化、四条由该实测外推的应对手段，以及「多模态侧须在真实序列长度上重测」的纪律。"),
    "PE-P-01": ("pe-p-01", "结构图：提示词面的四层构成（常驻 / 按需 / 传递 / 判据）、各自的验证方式，以及盘点产出的清单形态。"),
    "PE-P-03": ("pe-p-03", "契约图：任务描述的五项自包含字段与返回结果的四项固定字段，以及模板化、可解析、可追溯三条工程要点。"),
    "PE-P-04": ("pe-p-04", "对照图：判据的四要素与三种失败形态（恒真 / 假绿 / 代理判据），以及失败输出三元组、不设豁免的纪律。"),
    "PE-P-05": ("pe-p-05", "生命周期图：记忆的四个动作（写入 / 检索 / 复核 / 退役）与零和预算，以及「未复核的反思结论不得入库」。"),
    "PE-P-06": ("pe-p-06", "结构图：接入实况的四个方面（来源与签名 / 传输与权限 / 能力面 / 可观测性），以及传输不是沙箱、规范转无状态两条硬事实。"),
    "PE-P-07": ("pe-p-07", "对照图：跨运行时差异的五处来源、最小复现三步流程，以及「搬得走结构、搬不走效力」的迁移边界。"),
}


def _when_rows(node):
    """该用 / 不该用 → 对照表行：[(类别, 句子)]。

    ★ 类别已由第一列承载 ⇒ 第二列**去掉「不适用于」前缀**（否则「场景」列读起来是
      「不适用于把确定性当作唯一目标」，与「不该用」这一列语义重复）。
    """
    rows = []
    for e in node.get("when") or []:
        s = str(e).strip()
        if s.startswith(WHEN_AVOID_PREFIX):
            rows.append(("不该用", s[len(WHEN_AVOID_PREFIX):].lstrip("：: ")))
        else:
            rows.append(("该用", s))
    return rows


def _missing(what="本轮未写。"):
    return '<p class="lede">%s</p>' % C.esc(what)


def node_page(node, groups_by_id, page_exists, glossary, page_rel=None):
    gid = node["group"]
    g = groups_by_id[gid]
    nid = node["id"]
    status = node["content_status"]
    cn_name, en_name = C.split_name(node["name"], node.get("en", ""))
    body = []
    body.append(C.crumbs(BASE, [("首页", "index.html"), ("知识分组", C.DIR_GROUPS + "/index.html"),
                                (C.group_label(gid, g["name"]), C.group_page_rel(gid)), (nid, None)]))
    # ---- 标题区：中文名一行 / 英文名独立一行 / 身份行 / 标签行（各自独占一行）
    body.append('<h1>%s</h1>' % C.esc(cn_name))
    if en_name:
        body.append('<p class="page-en">%s</p>' % C.esc(en_name))
    body.append('<p class="meta-line"><span class="nid">%s</span>%s%s<span>第 %d 层</span></p>'
                % (C.esc(nid), C.status_badge(status),
                   C.group_chip(gid, g["name"], BASE + C.group_page_rel(gid)), node["layer"]))
    tags = node.get("tags") or []
    if tags:
        body.append('<div class="tag-row" aria-label="标签">%s</div>'
                    % "".join('<span class="tier">%s</span>' % C.esc(t) for t in tags))
    # ---- 页首导读：一句话结论 + 结构地图（先给结论，再给地图）
    body.append(C.read_map_html(node.get("summary", ""), SECTIONS, reveal=0))
    # ---- 机制图（页面级总览图；随主题）
    fig = NODE_FIG.get(nid)
    if fig:
        body.append(C.figure_html(fig[0], fig[1], reveal=1))

    # 01 为什么需要它（主张 + 展开点 + 适用边界）
    # ★ 2026-10-16（B-1）：适用边界改为**读字段**（`node.boundary`），不再从 `why` 里按标记切；
    #   判据 P05 同批断言「`boundary` 非空」且「`why`/`intro` 中不得残留引导串」（否则会出现第二个边界块）。
    body.append(C.section("为什么需要它", 1, "sec-why"))
    body.append(C.prose_html(node.get("why", ""), node.get("boundary")))
    # 02 机制说明（⛔ 不传 boundary：边界块只在 sec-why 出现一次）
    body.append(C.section("机制说明", 2, "sec-intro"))
    body.append(C.prose_html(node.get("intro", "")))
    # 03 何时该用 / 何时不该用 → 对照表
    body.append(C.section("何时该用 / 何时不该用", 3, "sec-when"))
    rows = _when_rows(node)
    body.append(C.pair_table(rows, "按场景对照：先看条件，再看该怎么做。")
                if rows else _missing())
    # 04 实验台
    body.append(C.section("实验台", 4, "sec-lab"))
    body.append(C.steps_html(node.get("lab")) if node.get("lab") else _missing())
    # 05 证据
    body.append(C.section("证据", 5, "sec-evidence"))
    body.append(C.ev_table_html(node.get("evidence")) if node.get("evidence") else _missing())
    # 06 术语
    body.append(C.section("术语", 6, "sec-terms"))
    body.append(C.terms_table_html(node.get("terms"), glossary, BASE, page_exists)
                if node.get("terms") else _missing())
    # 07 失效模式
    body.append(C.section("失效模式", 7, "sec-pitfalls"))
    body.append(C.pair_list(node.get("pitfalls")) if node.get("pitfalls") else _missing())
    # 08 在本站知识结构中的位置
    body.append(C.section("在本站知识结构中的位置", 8, "sec-rel"))
    body.append('<dl class="kv"><dt>所属分组</dt><dd><a href="%s">%s</a></dd>'
                '<dt>依赖深度</dt><dd>第 %d 层（同层节点彼此无先后约束）</dd></dl>'
                % (C.esc(BASE + C.group_page_rel(gid)), C.group_chip(gid, g["name"]), node["layer"]))
    body.append(C.relchain_html(nid, node.get("prereq"), node.get("successors"), page_exists, BASE))
    body.append('<p class="lede">在 <a href="%s">交互全景图</a> 中定位本节点。</p>'
                % C.esc(BASE + C.DIR_INTERACTIVE + "/index.html#node-" + nid))

    return C.page_shell(BASE, "node", nid, cn_name, "\n".join(body),
                        nav_extra=[(BASE + C.group_page_rel(gid), g["name"])],
                        # ★ 2026-10-16 第 8 轮（SH4）：description 取**本页**页首导读的结论句
                        #   （＝已有结论，⛔ 不新写一句给搜索引擎看的话，避免同一页两种口径）
                        meta_desc=node.get("summary", ""),
                        page_rel=page_rel or C._derive_page_rel("node", nid))


def generate(root=None):
    """返回 {相对路径: 内容}。"""
    data = C.load_sources()
    dag = data["dag"]
    nodes = dag["nodes"]
    groups_by_id = {g["id"]: g for g in dag["groups"]}
    published = [n for n in nodes if n["content_status"] == "complete"]
    page_exists = {n["id"] for n in published}
    out = {}
    for n in sorted(published, key=lambda x: x["id"]):
        rel = "%s/%s.html" % (C.DIR_NODES, C.id_slug(n["id"]))
        # ★ 2026-10-16 第 8 轮（SH4）：把**产物路径本身**传给页面构建器 ⇒ canonical 与产物同源，
        #   ⛔ 不在 page_shell 里另推一份（同一条信息两处各存一份是本站的老毛病）。
        out[rel] = node_page(n, groups_by_id, page_exists, data["glossary"], page_rel=rel)
    return out


if __name__ == "__main__":
    for k, v in sorted(generate().items()):
        print(k, len(v))
