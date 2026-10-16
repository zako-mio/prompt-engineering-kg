#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-figs.py —— 图件层（自制数据图解，diagram-lite T2 档：DSL→SVG）

职责：把本文件内的 `.dot` 源**一次性、确定性**地渲染为 `10-dag-data/figures/*.svg`，
并做确定性后处理，使图件可**内联**进页面且**随主题切换**。

★ 为什么预渲染入库、而不是构建期调 graphviz：
  ① 构建链保持纯 Python（`build-all.py` 不引入外部可执行依赖，发布环境不必装 graphviz）；
  ② 图件是**可复现的入库产物**（源 `.dot` 与产物 `.svg` 同目录，重跑即得同一结果）。
  ⇒ 本脚本是**图件的唯一生成入口**，⛔ 页面生成器只读不渲染。

★ 后处理五步（确定性，逐条可复算）：
  ① 剥 XML 声明 / DOCTYPE / graphviz 注释；
  ② 删 graphviz 画的**背景多边形**（否则白底会盖住站点背景与主题切换）；
  ③ 去固定 `width`/`height`，只留 `viewBox`（⇒ 内联后由 CSS 定尺寸，⛔ 不外包固定尺寸容器）；
  ④ **调色板 hex → CSS 变量**（⇒ 深浅主题自动跟随；⛔ 不留裸色值）；
  ⑤ `font-family` 换成站点字体栈（与正文同栈，避免图内字体与页面不一致）。

用法：
  python3 gen-figs.py --write    渲染并落盘（需本机 graphviz `dot`）
  python3 gen-figs.py --check    与磁盘对账（漂移 → 退出码 1）
  python3 gen-figs.py --list     只列出图件 id 与用途
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "10-dag-data"))
OUTDIR = os.path.join(DATA, "figures")

# 调色板 hex → CSS 变量（浅色档字面值；⛔ 变量名须与 site-palette.css_names 一致）
HEX2VAR = {
    "#0e1729": "--text-primary",
    "#46536b": "--text-secondary",
    "#5f6d84": "--text-tertiary",
    "#f4f7fc": "--surface-page",
    "#ffffff": "--surface-raised",
    "#e9eef8": "--surface-subtle",
    "#f0f4fa": "--surface-stripe",
    "#cfd8e8": "--border-card",
    "#7c8aa5": "--border-line",
    "#dde4f0": "--border-subtle",
    "#2f4bd8": "--brand-primary",
    "#1d33a6": "--brand-deep",
    "#dfe6fb": "--brand-soft",
    "#136f3a": "--success",
    "#9a5310": "--warning",
    "#b3181f": "--danger",
}
FONT = "Noto Sans CJK SC"          # 渲染期字体（本机 fontconfig 实测覆盖全部 CJK 字形）
FONT_STACK = ("system-ui, -apple-system, 'Segoe UI', Roboto, 'PingFang SC', "
              "'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans SC', sans-serif")

NODE_ATTR = ('node[shape=box, style="rounded,filled", fillcolor="#ffffff", '
             'color="#7c8aa5", fontcolor="#0e1729", fontname="%s", fontsize=13, '
             'margin="0.20,0.12"];' % FONT)
EDGE_ATTR = ('edge[color="#7c8aa5", fontcolor="#46536b", fontname="%s", fontsize=11, '
             'arrowsize=0.7];' % FONT)
NOTE_ATTR = ('node[shape=note, style="filled", fillcolor="#e9eef8", color="#9a5310", '
             'fontcolor="#0e1729", fontname="%s", fontsize=12];' % FONT)


# ---------------------------------------------------------------- 图件源（每图唯一问题，见 caption）

FIGS = {}

FIGS["pe-f-01"] = dict(
    caption="机制图：从概率分布到确定性边界——三类工程手段各自作用在哪一步。",
    dot="""
digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  m  [label="自回归模型\\n每步输出下一个 token 的概率分布"];
  s  [label="解码策略：贪心 / 温度 / top-p\\n只改取样规则，不改结论"];
  o  [label="一次输出 ＝ 分布的一个样本", fillcolor="#dfe6fb", color="#2f4bd8"];
  d1 [label="① 约束解码\\n按文法或 schema 屏蔽非法路径"];
  d2 [label="② 结构校验与重试\\n把失败当常规分支"];
  d3 [label="③ 固定可固定的一切\\n提示 · 顺序 · 工具 · 参数"];
  m -> s -> o;
  d1 -> o [style=dashed]; d2 -> o [style=dashed]; d3 -> o [style=dashed];
  d1 -> d2 -> d3 [style=invis];
  %(note)s
  b  [label="适用边界\\n把随机性压到零 ≠ 结果稳定"];
  o -> b [style=dotted, arrowhead=none];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR, note=NOTE_ATTR))

FIGS["pe-r-02"] = dict(
    caption="对照图：同一技巧在两类条件下符号相反，以及判定纪律。",
    dot="""
digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  q [label="显式思维链（CoT）与示例堆砌\\n同一技巧，符号随条件反转", fillcolor="#dfe6fb", color="#2f4bd8"];
  a [label="条件 A：非推理模型\\n或 高串行深度任务（GSM8K / MATH）\\n⇒ CoT 仍有大幅增益", color="#136f3a"];
  b [label="条件 B：推理模型 · 且高串行深度已被底座内化\\n⇒ 增益仅 2.9%%–3.1%%，Gemini Flash 2.5 为 −3.3%%\\n耗时 +20%%–80%%，指令遵循下降", color="#b3181f"];
  q -> a [label="成立"];
  q -> b [label="反转"];
  {rank=same; a; b;}
  %(note)s
  n [label="判定纪律\\n缺席证据 ≠ 反证（未被文档收录 ≠ 已被证伪）\\n不得把单一任务域的结论外推为普遍规律"];
  b -> n [style=dotted, arrowhead=none];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR, note=NOTE_ATTR))

FIGS["pe-p-02"] = dict(
    caption="结构图：技能文件的「主文件 + 按需展开」与旧写法的对照。",
    dot="""
digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  subgraph cluster_new {
    label="现行写法：短触发 + 渐进式披露"; fontname="%(font)s"; fontsize=12; color="#7c8aa5";
    style="rounded,dashed"; fontcolor="#46536b";
    main [label="主文件（常驻成本）\\n① 触发描述：尽可能短、可判定\\n② 要点：做什么 / 不做什么 / 判据\\n③ 边界声明：适用范围与不适用场景\\n④ 索引：指向按需加载的引用文件", fillcolor="#dfe6fb", color="#2f4bd8"];
    r1 [label="引用文件 1\\n细节", fillcolor="#ffffff"];
    r2 [label="引用文件 2\\n细节", fillcolor="#ffffff"];
    r3 [label="引用文件 n\\n细节", fillcolor="#ffffff"];
    main -> r1 [style=dashed, label="按需"];
    main -> r2 [style=dashed, label="按需"];
    main -> r3 [style=dashed, label="按需"];
  }
  old [label="旧写法：详尽操作手册式\\n⇒ 在新一代模型上反而降低效果\\n并把常驻 token 推高", color="#b3181f", shape=note, fillcolor="#e9eef8"];
  main -> old [style=dotted, arrowhead=none, label="对照"];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR, font=FONT))

FIGS["pe-n-01"] = dict(
    caption="时间轴：三代范式的重心迁移——三代是叠加而非替代，判断投入方向的依据是当前瓶颈落在哪一代。",
    dot="""
digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  g1 [label="2020–2023\n提示词工程\n单次调用 · 手工技巧", width=2.4];
  g2 [label="2023–2025\n上下文工程\n检索 · 压缩 · 位置", fillcolor="#dfe6fb", color="#2f4bd8", width=2.4];
  g3 [label="2025–2026\n编排与编译\n协议 · 编译", width=2.2];
  g1 -> g2 [label="重心迁移"];
  g2 -> g3 [label="重心迁移"];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

# ★ 2026-10-16 内容波次 1：G00 的 5 个节点页各自一张自制图（P35 ⑧ 要求每个节点页 ≥1 图）。
#   规格纪律（R-08 / gen-figs.check_spec）：内容列 804px 下渲染高度 ≤600px ⇒ viewBox 的高宽比
#   必须 ≤0.746；下面 5 图均按「宽 > 高」排（LR 或并列 rank），⛔ 不做竖长条。
#   色值只用 HEX2VAR 里的 16 个（越界 postprocess 会 SystemExit）。
FIGS["pe-f-02"] = dict(
    caption="分层图：三层的稳定性与特权递减，以及「缓存命中面」恰好切在稳定前缀与易变后缀之间。",
    dot="""
digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  L1 [label="系统层\\n产品身份 · 长期约束 · 安全策略\\n几乎不变 ⇒ 可缓存", fillcolor="#dfe6fb", color="#2f4bd8"];
  L2 [label="开发者层\\n任务级指令 · 输出契约\\n随调用点变化"];
  L3 [label="用户层\\n本次输入\\n完全不可信", color="#b3181f"];
  L1 -> L2 [label="特权递减"];
  L2 -> L3 [label="特权递减"];
  C [label="稳定前缀\\n缓存命中面", color="#136f3a", width=2.2];
  X [label="易变后缀\\n每次重算", color="#b3181f", width=2.2];
  L1 -> C [style=dashed, arrowhead=none];
  L2 -> X [style=dashed, arrowhead=none];
  L3 -> X [style=dashed, arrowhead=none];
  {rank=same; L1; C;}
  {rank=same; L2; X;}
  {rank=same; L3; X;}
  N [label="放错层的代价\\n易变内容进了系统层 ⇒ 前缀失效、缓存归零\\n（还顺手把「谁说了算」也搅乱了）", shape=note, fillcolor="#e9eef8"];
  L3 -> N [style=dotted, arrowhead=none, label="失配"];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-f-03"] = dict(
    caption="结构图：四类内容各自被固定标签划出边界后交给模型解析，与「连成一段的裸文本」对照。",
    dot="""
digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  T [label="<instructions>\\n指令", fillcolor="#dfe6fb", color="#2f4bd8"];
  E [label="<examples>\\n示例", fillcolor="#dfe6fb", color="#2f4bd8"];
  D [label="<documents>\\n资料", fillcolor="#dfe6fb", color="#2f4bd8"];
  U [label="<user_input>\\n用户输入\\n不可信", color="#b3181f"];
  M [label="模型\\n按标签无歧义解析结构", fillcolor="#dfe6fb", color="#2f4bd8", width=2.6];
  T -> M; E -> M; D -> M; U -> M;
  B [label="裸文本连成一段\\n⇒ 指令与数据没有边界\\n标签只消歧 · 不保安全", shape=note, fillcolor="#e9eef8"];
  M -> B [style=dotted, arrowhead=none, label="对照"];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-f-04"] = dict(
    caption="收益曲线图：示例从 0 到 3 到 10 的边际收益，以及它在推理模型上发生的符号反转。",
    dot="""
digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  Z [label="零样本：先量基线", fillcolor="#dfe6fb", color="#2f4bd8", width=2.9];
  F [label="3 个示例：消歧 + 格式对齐", fillcolor="#dfe6fb", color="#2f4bd8", width=2.9];
  T [label="10 个示例：边际收益趋零", width=2.9];
  R [label="推理模型：示例可持续降准", color="#b3181f", width=2.9];
  R2 [label="改写为显式要点：可重新获益", color="#136f3a", width=2.9];
  Z -> F [label="格式违规下降"];
  F -> T [label="收益饱和"];
  F -> R [label="条件反转"];
  R -> R2 [style=dashed, label="形态变了"];
  {rank=same; F; R;}
  {rank=same; T; R2;}
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-f-05"] = dict(
    caption="双维图：具体性（说多少细节）与可验证性（能否判定）方向相反却不矛盾，因为对象不同。",
    dot="""
digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  A [label="具体性：说了多少细节\\n现行口径向「更一般」移动\\n（推理路径不写死）", fillcolor="#dfe6fb", color="#2f4bd8", width=3.0];
  B [label="可验证性：结果能否被判定\\n现行口径向「更严格」移动\\n（交付契约必须可判定）", fillcolor="#dfe6fb", color="#2f4bd8", width=3.0];
  A -> B [dir=both, label="不矛盾：一个管推理路径，一个管交付契约"];
  N [label="混为一谈的两种后果\\n把「具体」当「长」 ⇒ 重复指令只烧 token\\n把「一般」当「模糊」 ⇒ 契约不可判定", shape=note, fillcolor="#e9eef8", width=3.0];
  B -> N [style=dotted, arrowhead=none];
  {rank=same; B; N;}
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-f-06"] = dict(
    caption="位置图：同一段上下文的三个位置（窗口条）可用性差异，以及由此推出的三个工程动作。",
    dot="""
digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  subgraph cluster_win {
    label="同一段上下文的三个位置（窗口条）"; fontname="%(font)s"; fontsize=12;
    color="#7c8aa5"; style="rounded,dashed"; fontcolor="#46536b";
    H [label="首部\\n最易被用到", color="#136f3a", width=1.5];
    M [label="中部\\n显著下降", color="#b3181f", width=1.5];
    T [label="尾部\\n最易被用到", color="#136f3a", width=1.5];
    H -> M [style=solid, arrowhead=none];
    M -> T [style=solid, arrowhead=none];
    {rank=same; H; M; T;}
  }
  W [label="上下文窗口：容量 ≠ 有效注意力\\ntoken 越多，注意力越稀释", fillcolor="#dfe6fb", color="#2f4bd8"];
  A1 [label="动作一 位置安排\\n重要内容置首尾", shape=note, fillcolor="#e9eef8"];
  A2 [label="动作二 压缩与摘要\\n不是省成本的附属品", shape=note, fillcolor="#e9eef8"];
  A3 [label="动作三 检索精度\\n优先于检索数量", shape=note, fillcolor="#e9eef8"];
  W -> H [label="作用于"];
  W -> M [style=dotted, arrowhead=none, constraint=false];
  W -> T [style=dotted, arrowhead=none, constraint=false];
  M -> A1 [style=solid, arrowhead=none, constraint=false];
  M -> A2 [style=solid, arrowhead=none, constraint=false];
  M -> A3 [style=solid, arrowhead=none, constraint=false];
  H -> A1 [style=invis];
  {rank=same; A1; A2; A3;}
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR, font=FONT))

# ★ 2026-10-16 内容波次 2：G01「确定性输出」的 5 个节点页各自一张自制图。
#   ★ 成对纪律：本处每条必须与 `gen-nodes.NODE_FIG` 的那条**同 fid 同 caption** 一起加
#     （`figure_html` 对缺失图 id **静默返回空串** ⇒ 只加一处会让节点页 P35 ⑧ FAIL）。
#   ★ 规格纪律（同波次 1）：宽 ≤ 893（缩放比 ≥ 0.90）且渲染高 ≤ 600px。下面 5 图一律
#     `rankdir=LR` + `{rank=same; …}`：★ 在 LR 下 `rank=same` = **同一列内纵向堆叠**，
#     故「多行内容」只涨高度、不涨宽度 —— 这是本波次控制 viewBox 宽的**唯一**手法。
FIGS["pe-s-01"] = dict(
    caption="机制图：约束解码在生成期屏蔽非法路径——从概率分布到「过滤后再取样」，与「生成后校验」的位置对照。",
    dot="""
digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  A [label="每一步：下一个 token\\n的概率分布", fillcolor="#dfe6fb", color="#2f4bd8"];
  B [label="约束解码\\n按 schema 过滤候选\\n非法路径概率置零", color="#136f3a"];
  C [label="在剩余候选上取样\\n输出结构必然合法", fillcolor="#dfe6fb", color="#2f4bd8"];
  D [label="生成后校验\\n先自由生成，再逐条校验", color="#9a5310"];
  E [label="非法已经发生\\n只能事后发现并重试", color="#b3181f"];
  A -> B [label="生成期"];
  B -> C;
  A -> D [style=dashed, label="生成后"];
  D -> E [style=dashed];
  {rank=same; B; D;}
  {rank=same; C; E; N;}
  N [label="关键差别\\n前者：非法路径根本没被采到\\n后者：非法已发生，只能补救", shape=note, fillcolor="#e9eef8"];
  C -> N [style=dotted, arrowhead=none];
  E -> N [style=dotted, arrowhead=none, constraint=false];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-s-02"] = dict(
    caption="分档图：自然语言要求 / 结构契约 / 约束解码三档的强度递增，与成本、可移植性的同向递减。",
    dot="""
digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  T1 [label="第一档：自然语言要求\\n「只输出 JSON」\\n可靠性最差 · 成本最低", color="#9a5310"];
  T2 [label="第二档：结构契约\\n把 schema 放进提示\\n可靠性中等 · 必须有重试兜底", fillcolor="#dfe6fb", color="#2f4bd8"];
  T3 [label="第三档：约束解码\\n解码期按 schema 屏蔽候选\\n结构必然合法", color="#136f3a"];
  T1 -> T2 [label="强度递增"];
  T2 -> T3 [label="强度递增"];
  {rank=same; T3; X;}
  X [label="同一轴上的另一档位差\\n强度递增 ⇒ 成本与可移植性同向递减\\n（可移植性：换模型换供应商是否还成立）", shape=note, fillcolor="#e9eef8"];
  T3 -> X [style=dotted, arrowhead=none];
  {rank=same; T1; L;}
  L [label="松 ⇒ 必须配人工或后置校验\\n中 ⇒ 必须配重试\\n紧 ⇒ 才可把结构失败视为已消除", shape=note, fillcolor="#e9eef8"];
  T1 -> L [style=dotted, arrowhead=none];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-s-03"] = dict(
    caption="对照图：同一任务在「先自由推理后格式化」与「边推理边守 schema」两种形态下的推理预算与质量差异。",
    dot="""
digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  Q [label="同一个任务\\n要推理 + 要结构化输出", fillcolor="#dfe6fb", color="#2f4bd8"];
  A1 [label="形态 A：先自由推理\\n输出契约不参与解码", color="#136f3a"];
  A2 [label="再一次调用格式化\\n按 schema 整理结论\\n推理质量完整保留", color="#136f3a"];
  B1 [label="形态 B：边推理边守 schema\\n每一步都屏蔽大部分候选", color="#b3181f"];
  B2 [label="中间状态无法自由试探\\n格式约束挤占推理预算\\n⇒ 质量可差一截", color="#b3181f"];
  Q -> A1; A1 -> A2;
  Q -> B1 [style=dashed]; B1 -> B2 [style=dashed];
  {rank=same; A1; B1;}
  {rank=same; A2; B2; N;}
  N [label="代价与收益\\nA：调用次数与延迟上升\\nB：一次调用，但推理表现下降", shape=note, fillcolor="#e9eef8"];
  A2 -> N [style=dotted, arrowhead=none];
  B2 -> N [style=dotted, arrowhead=none, constraint=false];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-s-04"] = dict(
    caption="选型图：同一份信息在四种格式下的相对体积（条宽即相对 token 量），与三个选型判据。",
    dot="""
digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  H [label="同一份信息\\n四种承载形态\\n条宽 ＝ 相对 token 量\\n以缩进 JSON 为基线 1.0", fillcolor="#dfe6fb", color="#2f4bd8"];
  {rank=same; J; Y; M; S;}
  J [label="缩进 JSON 1.0", width=4.40];
  Y [label="YAML 0.70", width=3.08];
  M [label="Markdown 表 0.55", width=2.42];
  S [label="TSV 0.35", width=1.54];
  H -> J [style=invis];
  N [label="三个选型判据\\n① 下游是否要流式解析\\n② 是否含大量重复结构\\n③ 解析失败的代价\\n长列表看 ① · 单对象看 ③", shape=note, fillcolor="#e9eef8"];
  M -> N [style=invis];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-s-05"] = dict(
    caption="回路图：生成 → 校验 → 把具体错误回喂 → 重生成的限次闭环，以及超限样本的处置。",
    dot="""
digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  G [label="生成\\n按提示与结构契约出结果"];
  V [label="校验\\n结构校验 + 业务规则\\n写成与模型无关的纯函数", fillcolor="#dfe6fb", color="#2f4bd8"];
  P [label="通过\\n交付下游", color="#136f3a"];
  R [label="失败：把具体错误回喂\\n给出位置与期望值\\n（不是笼统的「格式错误」）", color="#9a5310"];
  G -> V;
  V -> P [label="通过"];
  V -> R [style=dashed, label="失败"];
  R -> G [style=dashed, label="限次重生成"];
  {rank=same; P; R; N;}
  N [label="限次闭环 ≠ 异常分支\\n重试上限必须显式写死\\n超限样本必须落盘可查\\n并区分首次通过率与最终通过率", shape=note, fillcolor="#e9eef8"];
  V -> N [style=dotted, arrowhead=none, constraint=false];
}
""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

# ★ 2026-10-16 内容波次 3：G02「推理增强」7 条 + G05「评测与自动优化」9 条 +
#   G06「安全与鲁棒性」6 条，共 22 个节点页各自一张自制图。
#   ★ 成对纪律：本处每条必须与 `gen-nodes.NODE_FIG` 的那条**同 fid 同 caption** 一起加
#     （`figure_html` 对缺失图 id **静默返回空串** ⇒ 只加一处会让节点页 P35 ⑧ FAIL）。
#   ★ 规格纪律（同波次 1/2）：`gen-figs.check_spec` 两条界同时生效 ——
#     804px 内容列下渲染高 ≤ 600px、缩放比 `804 / viewBox 宽` ≥ 0.90（⇒ 宽 ≤ 893）。
#     本波 22 图实测宽 507–856、缩放比 0.939–1.584、渲染高 177–479px。
#   ★ 布局手法：`rankdir=LR` 下 `rank=same` = **同一列内纵向堆叠**（只涨高不涨宽）；
#     需要「一行并列」时用 `rankdir=TB` + `{rank=same; …}`（此时才是同行）。
#   ⛔ 色值只用 HEX2VAR 的 16 个；⛔ 无裸 hex / 无固定 width·height / 无外链。
FIGS["pe-a-01"] = dict(
    caption="层级图：系统 > 开发者 > 用户 > 外部内容的特权递减，三层实现路径（提示 / 训练 / 架构），以及「降低而非消除、必须配合权限收窄」。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  L1 [label="最高特权 系统\n产品身份与安全策略", fillcolor="#dfe6fb", color="#2f4bd8"];
  L2 [label="开发者\n任务级指令与输出契约", fillcolor="#dfe6fb", color="#2f4bd8"];
  L3 [label="用户\n本次输入", fillcolor="#dfe6fb", color="#2f4bd8"];
  L4 [label="最低特权 外部内容\n工具返回 / 检索结果 / 网页", color="#b3181f"];
  {rank=same; L1; L2; L3; L4;}
  L1 -> L2 [label="特权递减"];
  L2 -> L3 [label="特权递减"];
  L3 -> L4 [label="特权递减"];
  P [label="三层实现路径\n① 提示层：在系统提示中声明优先级与处理规则\n② 训练层：用偏好优化或强化学习让模型学会拒绝低特权指令\n③ 架构层：在中间表示中注入层级信号", color="#136f3a"];
  L2 -> P [style=dashed, label="实现"];
  {rank=same; P; N;}
  N [label="边界\n降低而非消除注入风险：注入仍列风险清单首位\n模型不能作为唯一安全控制\n复杂 Agent 网络中的多层级动态控制仍属前沿\n⇒ 层级必须配合权限收窄与显式标注", shape=note, fillcolor="#e9eef8"];
  L4 -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-a-02"] = dict(
    caption="攻击面图：直接注入与间接注入两类路径，三条放大危害的属性，以及「模型架构上不区分指令与数据 ⇒ 无可靠拦截式预防」这一反直觉结论。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  D1 [label="直接注入\n恶意指令由用户直接输入\n⇒ 攻击面较窄", color="#9a5310"];
  D2 [label="间接注入\n恶意指令藏在外部内容中\n（网页、邮件、文档、工具返回、记忆）\n⇒ 攻击面很宽", color="#b3181f"];
  {rank=same; D1; D2;}
  H [label="三条放大危害的属性\n① 上下文池化：不同来源混在同一窗口\n② 记忆持久化：注入可跨会话留存\n③ agentic 执行：被劫持指令触发真实副作用", color="#b3181f"];
  D1 -> H [style=invis];
  D2 -> H;
  {rank=same; H; R;}
  R [label="根本原因\n模型在架构上不区分「指令」与「数据」\n⇒ 不存在可靠的拦截式预防\n⇒ 防御落在架构与权限上", color="#2f4bd8", fillcolor="#dfe6fb"];
  H -> R;
  N [label="边界\n注入是当前生成式 AI 的固有属性\n把某条缓解措施说成「已解决注入」\n即为越界表述\n输入过滤可被编码与多模态绕过", shape=note, fillcolor="#e9eef8"];
  {rank=same; N;}
  R -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-a-03"] = dict(
    caption="阶段映射图：十大风险按工程阶段分派为四组检查项（设计 / 接入 / 上线 / 运行），以及「覆盖检查表而非合规认证、引用必须标版本」。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  S1 [label="设计阶段\n检查能力边界与权限\n提示注入 · 过度自主权 · 敏感信息泄露", fillcolor="#dfe6fb", color="#2f4bd8"];
  S2 [label="接入阶段\n检查供应链与数据面\n供应链 · 数据与模型投毒 · 向量与嵌入弱点", fillcolor="#dfe6fb", color="#2f4bd8"];
  S3 [label="上线阶段\n检查消耗与输出\n无界消耗 · 输出处理不当", fillcolor="#dfe6fb", color="#2f4bd8"];
  S4 [label="运行阶段\n检查注入与信息面\n提示注入 · 敏感信息泄露 · 错误信息 · 隐藏上下文暴露", fillcolor="#dfe6fb", color="#2f4bd8"];
  {rank=same; S1; S2; S3; S4;}
  S1 -> S2 [style=invis];
  S2 -> S3 [style=invis];
  S3 -> S4 [style=invis];
  D [label="相对上一版的实质调整\n权限类风险位次前移\n隐藏上下文暴露取代系统提示泄露\n新增与多模态相关的注入形态\n⇒ 条目变动信息部分来自二手来源，须标注", color="#9a5310"];
  S2 -> D [style=dashed, label="版本差"];
  {rank=same; D; N;}
  N [label="边界\n清单是覆盖检查表，不是风险排序或合规认证\n引用必须注明版本；官网索引页与官方仓库正文同步状态存在落差", shape=note, fillcolor="#e9eef8"];
  S4 -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-a-04"] = dict(
    caption="权衡图：过拒的三类成因、三条改进方向，以及「拦截率与过拒率必须双向度量」的度量纪律与业务侧落点。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  C1 [label="成因一 分类器粒度过粗\n把整段内容判为可疑", color="#b3181f"];
  C2 [label="成因二 安全指令过于绝对\n遇任何可疑内容即中止", color="#b3181f"];
  C3 [label="成因三 层级冲突处理过保守\n一律拒绝而非降级", color="#b3181f"];
  {rank=same; C1; C2; C3;}
  F1 [label="改进一 拦截粒度做细\n只剔除可疑片段而非整段失败", color="#136f3a"];
  F2 [label="改进二 处置规则可判定\n区分继续 / 降级 / 中止三种结果", color="#136f3a"];
  F3 [label="改进三 为可降级场景设计降级路径\n读取外部内容时尤其关键", color="#136f3a"];
  C1 -> F1; C2 -> F2; C3 -> F3;
  {rank=same; F1; F2; F3;}
  M [label="度量纪律\n同时记录攻击成功率与正常请求拒绝率\n定期用正常流量样本估算过拒率\n⇒ 只优化一侧会把系统推向极端", color="#2f4bd8", fillcolor="#dfe6fb"];
  F2 -> M;
  {rank=same; M; N;}
  N [label="边界\n权衡落点由业务风险决定，没有普适最优点\n高风险场景可接受更高过拒率\n但必须是有意识的取舍并写进指标", shape=note, fillcolor="#e9eef8"];
  F3 -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-a-05"] = dict(
    caption="改写对照图：负向提示「不要做 X」反而激活 X 的机制、改写成期望行为的前后对照，以及无法正向化时的可判定处置规则。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  A [label="原提示「不要提到 X」", color="#b3181f"];
  B [label="机制：提示中的词本身激活相关表征\n⇒ X 被放进上下文，可及性反而提高\n⇒ 否定词在后续 token 预测中提高而非降低相关内容概率（模型规模越小越明显）", color="#b3181f"];
  A -> B;
  {rank=same; B; C;}
  C [label="改法：描述期望行为而不是禁止行为\n与其说「不要用某类格式」\n不如说「回答应由怎样的结构组成」", color="#136f3a"];
  B -> C [label="改写"];
  {rank=same; C; D;}
  D [label="无法正向化的约束\n（例如必须拒绝某类请求）\n⇒ 改为可判定的处置规则并配合输出校验", color="#9a5310"];
  C -> D [style=dashed];
  {rank=same; D; N;}
  N [label="清查纪律\n把每条「不要」改写为对应的正向描述\n并检查改写后是否仍覆盖原意\n负向清单只作兜底，不承担主要行为控制职责", shape=note, fillcolor="#e9eef8"];
  C -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-a-06"] = dict(
    caption="四步隔离图：标注 / 声明 / 收窄 / 校验四个动作，以及「提示层的标注不构成安全边界、权限收窄才是关键」的分界。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  T [label="标注\n用固定标记包裹外部内容\n并声明来源与不可信属性", fillcolor="#dfe6fb", color="#2f4bd8"];
  D [label="声明\n在系统层说明处理规则\n如仅可引用不可执行", fillcolor="#dfe6fb", color="#2f4bd8"];
  N [label="收窄\n把处理外部内容的步骤\n放在权限受控的子流程中", color="#136f3a"];
  V [label="校验\n对输出做结构或规则校验\n拦截被劫持后的越界行为", fillcolor="#dfe6fb", color="#2f4bd8"];
  T -> D -> N -> V;
  {rank=same; T; D; N; V;}
  L [label="位置对照\n标注与声明在提示层\n⇒ 提示层不构成安全边界\n收窄与校验在架构层，才是防线的落点", color="#9a5310"];
  V -> L [style=dashed, label="分界"];
  {rank=same; L; G;}
  G [label="配套实践\n把标注体系写进提示词模板并版本化，新增外部来源时不漏标\n剥离不可见字符（零宽字符可绕过标注与检测）\n最小权限与标注必须配套，否则模型仍可能造成损害", shape=note, fillcolor="#e9eef8"];
  N -> G [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-01"] = dict(
    caption="三件套结构图：评测集的输入 / 期望输出 / 判据，两类判据的先后关系，以及按失败模式分层与版本化的两条组织要求。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  I [label="输入", fillcolor="#dfe6fb", color="#2f4bd8", width=1.2];
  O [label="期望输出", fillcolor="#dfe6fb", color="#2f4bd8", width=1.2];
  C [label="判据\n决定评测集的\n价值上限", fillcolor="#dfe6fb", color="#2f4bd8"];
  {rank=same; I; O; C;}
  D [label="确定性判据\n字段是否合法 / 是否含指定内容\n是否命中正则\n⇒ 可复现、成本低，应优先", color="#136f3a"];
  M [label="模型辅助判据\n相似度 / 评分准则 / 事实一致性\n⇒ 覆盖无法机械判定的质量标准\n但自身有偏差", color="#9a5310"];
  L [label="两条组织要求\n① 按失败模式分层而非随机抽样\n② 与提示词一起版本化", shape=note, fillcolor="#e9eef8"];
  {rank=same; D; M; L;}
  C -> D [label="优先"];
  D -> M [style=dashed, label="补充"];
  M -> L [style=dotted, arrowhead=none, label="组织"];
  N [label="边界\n只覆盖被采样到的失败模式\n⇒ 须随真实故障持续增补", shape=note, fillcolor="#e9eef8"];
  {rank=same; N;}
  D -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-02"] = dict(
    caption="构造动作图：测试集的四个构造动作（真实采样 / 失败模式分层 / 负例与边界例 / 判据与容差）、留出集，及「只收典型样本」的对照。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  A1 [label="① 采样\n从真实流量与故障记录\n保证分布真实", fillcolor="#dfe6fb", color="#2f4bd8"];
  A2 [label="② 分层\n按失败模式组织\n保证覆盖", fillcolor="#dfe6fb", color="#2f4bd8"];
  A3 [label="③ 负例与边界例\n保证区分度\n能发现误拒与过度保守", fillcolor="#dfe6fb", color="#2f4bd8"];
  A4 [label="④ 判据与容差\n保证可判定", fillcolor="#dfe6fb", color="#2f4bd8"];
  {rank=same; A1; A2; A3; A4;}
  S [label="每层设定负例与边界例；每个样本记录来源\n（真实流量 / 构造 / 对抗生成）与稳定性", color="#136f3a"];
  A1 -> S [style=invis];
  A2 -> S; A3 -> S; A4 -> S;
  H [label="留出集\n一份不参与优化的\n固定留出集\n用于判断是否过拟合", color="#136f3a"];
  {rank=same; S; H;}
  S -> H [style=dashed, label="单列"];
  X [label="对照：只收典型样本\n⇒ 系统性漏掉边界与对抗场景\n而线上故障恰恰集中在这些地方", shape=note, fillcolor="#e9eef8"];
  {rank=same; X;}
  H -> X [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-03"] = dict(
    caption="偏差对照图：模型即裁判的四类系统性偏差与各自的缓解手段，以及「确定性断言优先、模型裁判只做相对比较」的并用纪律。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  B1 [label="位置偏差\n候选顺序影响评分", color="#b3181f"];
  B2 [label="冗长偏好\n更长的回答更易得高分", color="#b3181f"];
  B3 [label="自我偏好\n倾向给同族模型更高分", color="#b3181f"];
  B4 [label="准则漂移\n同一准则跨批次理解不一致", color="#b3181f"];
  {rank=same; B1; B2; B3; B4;}
  M1 [label="随机化顺序", color="#136f3a"];
  M2 [label="长度归一或显式准则", color="#136f3a"];
  M3 [label="多模型交叉评分", color="#136f3a"];
  M4 [label="固定准则文本与示例校准", color="#136f3a"];
  {rank=same; M1; M2; M3; M4;}
  B1 -> M1; B2 -> M2; B3 -> M3; B4 -> M4;
  P [label="并用纪律\n能用确定性断言判定的部分绝不用模型裁判\n必须用时：固定准则文本、随机化顺序\n并在小样本上与人工标注做一致性校准\n裁判结果保留原始评分与理由", color="#2f4bd8", fillcolor="#dfe6fb"];
  M3 -> P;
  {rank=same; P; S;}
  S [label="边界\n适合相对比较与粗筛\n不适合作为唯一判据\n对高风险判定须与确定性断言\n或人工抽检交叉验证", shape=note, fillcolor="#e9eef8"];
  M4 -> S [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-04"] = dict(
    caption="三层落地图：本地批量 / 持续集成回归 / 对抗评测三层工具链，断言类型的二分，以及红蓝对抗必须同时报告「攻击成功率」与「正常请求拒绝率」。",
    dot="""digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  L1 [label="第一层 本地批量评测\n改动时跑\n答「这次改动是否变好」", fillcolor="#dfe6fb", color="#2f4bd8", width=2.9];
  L2 [label="第二层 持续集成回归\n提交时跑固定子集\n答「是否打破既有行为」", fillcolor="#dfe6fb", color="#2f4bd8", width=2.9];
  L3 [label="第三层 对抗评测\n安全改动或定期跑\n答「攻击面是否被扩大」", color="#dfe6fb", color="#2f4bd8", width=2.9];
  {rank=same; L1; L2; L3;}
  D [label="确定性断言\n相等 / 包含 / 正则 / JSON 合法性\n脚本 / 延迟 / 成本 / 工具调用指标", color="#136f3a", width=3.2];
  A [label="模型辅助断言\n相似度 / 分类器 / 评分准则\n答案相关性 / 上下文忠实度 / 事实性", color="#9a5310", width=3.2];
  L1 -> D [label="断言类型"];
  D -> A [style=dashed, label="不足时"];
  {rank=same; D; A;}
  R [label="红蓝对抗的产出应有两列\n拦截率（攻击成功率）\n过拒率（正常请求拒绝率）\n⇒ 两者共同构成防御质量画像", color="#136f3a", width=3.4];
  L3 -> R;
  {rank=same; R; N;}
  N [label="只测拦截率会奖励过度保守的防御\n并伤害可用性", shape=note, fillcolor="#e9eef8", width=3.0];
  A -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-05"] = dict(
    caption="自动优化回路图：生成候选 → 评测集评估 → 选择或组合 → 必要时迭代的闭环，与三条工程要点（留出集、可自动计算的判据、搜索预算）。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  G [label="生成候选指令", fillcolor="#dfe6fb", color="#2f4bd8"];
  V [label="在评测集上评估", fillcolor="#dfe6fb", color="#2f4bd8"];
  S [label="按指标选择\n或组合", fillcolor="#dfe6fb", color="#2f4bd8"];
  G -> V -> S;
  S -> G [style=dashed, label="必要时迭代"];
  N [label="三条工程要点\n① 评测集必须含留出部分，防搜索过拟合\n② 判据必须可自动计算：人工判断先固化为代理指标\n③ 限制搜索预算并记录最优候选", shape=note, fillcolor="#e9eef8"];
  {rank=same; G; N;}
  G -> N [style=dotted, arrowhead=none];
  F [label="前提与边界\n无评测集与判据时，搜索没有目标函数\n推理模型上自动优化的空间与人工优化一样被压缩", shape=note, fillcolor="#e9eef8"];
  {rank=same; S; F;}
  S -> F [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-06"] = dict(
    caption="编译流水线图：签名 / 模块 / 优化器三个构件与「按指标搜索产出指令与示例」的编译过程，以及选型两轴与「无单一最优」的官方边界。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  A [label="构件一 签名\n声明输入与输出字段", fillcolor="#dfe6fb", color="#2f4bd8"];
  B [label="构件二 模块\n把调用组织成流水线", fillcolor="#dfe6fb", color="#2f4bd8"];
  C [label="构件三 优化器\n在指令与示例空间中搜索", fillcolor="#dfe6fb", color="#2f4bd8"];
  {rank=same; A; B; C;}
  D [label="编译器按指标在训练集上搜索\n产出可直接使用的指令与少量示例", color="#136f3a"];
  A -> D [style=invis];
  B -> D; C -> D;
  {rank=same; D; T;}
  T [label="选型两轴（官方口径）\n① 瓶颈在指令、示例还是权重\n② 可用的算力预算\n⇒ 官方明确否认存在单一最优优化器，也不提供自动选择", color="#9a5310"];
  C -> T [style=dotted, arrowhead=none];
  {rank=same; T; O;}
  O [label="两个已具名定位\n入门路径：某个基于反思的优化器（其结构化指令提议器已设为默认）\n另一优化器的定位：指令与示例需要一起调时最先进", shape=note, fillcolor="#e9eef8"];
  D -> O [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-07"] = dict(
    caption="两条优化路线对照图：文本梯度把自然语言评价当梯度回传到各组件，反思式进化由执行轨迹生成改进规则；共同前提是轨迹与评分函数。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  Q [label="共同前提\n① 能拿到完整执行轨迹\n② 有可用的评分函数", fillcolor="#dfe6fb", color="#2f4bd8"];
  A1 [label="路线一 文本梯度\n把每个可变部分（提示、代码片段、输出）\n表示为变量", color="#136f3a"];
  A2 [label="模型给出自然语言评价\n评价作为「梯度」回传到变量\n⇒ 逐组件更新", color="#136f3a"];
  B1 [label="路线二 反思式进化\n让模型看到自己的推理轨迹\n与评分", color="#9a5310"];
  B2 [label="模型生成改进规则并更新提示\n报告称在多任务上优于强化学习基线\n且所需采样次数大幅减少", color="#9a5310"];
  Q -> A1; A1 -> A2;
  Q -> B1 [style=dashed]; B1 -> B2 [style=dashed];
  {rank=same; A1; B1;}
  {rank=same; A2; B2; N;}
  N [label="边界\n无轨迹 ⇒ 反思失去依据\n无评分函数 ⇒ 无法判断改进方向、优化不可收敛\n部分实现的收益还依赖底座模型规模与任务可分解性", shape=note, fillcolor="#e9eef8"];
  A2 -> N [style=dotted, arrowhead=none];
  B2 -> N [style=dotted, arrowhead=none, constraint=false];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-08"] = dict(
    caption="层次图：元提示处在被优化对象的上一层、三种典型用法，以及「提高候选生成速度、判定权仍在评测集」的对照纪律。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  M [label="元提示层\n让模型生成或改进提示词本身", fillcolor="#dfe6fb", color="#2f4bd8"];
  U1 [label="用法一 扩写\n粗糙指令 ⇒ 完整提示", color="#136f3a"];
  U2 [label="用法二 压缩\n长提示 ⇒ 要点", color="#136f3a"];
  U3 [label="用法三 归一\n一组提示统一结构", color="#136f3a"];
  M -> U1; M -> U2; M -> U3;
  {rank=same; U1; U2; U3;}
  N [label="三条工程要点\n① 必须附带明确目标与约束\n（目标模型、输出契约、风格要求）\n② 候选必须经评测集筛选，不能直接采用\n③ 保留改写前后的对照记录", shape=note, fillcolor="#e9eef8"];
  {rank=same; N;}
  M -> N [style=dotted, arrowhead=none];
  C [label="批量产出的候选", fillcolor="#dfe6fb", color="#2f4bd8"];
  U2 -> C;
  {rank=same; C; D;}
  D [label="价值与边界\n价值在规模：大量同类提示逐条人工改写不现实\n边界：提高的是候选生成速度，判定权仍在评测集\n无基线与判据时不能替代人工判断", shape=note, fillcolor="#e9eef8"];
  C -> D [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-e-09"] = dict(
    caption="版本—回归图：提示词版本与评测基线必须成对留档、换模型必须重建基线，以及「跑全量」「同时跟踪成本与延迟」两条回归纪律。",
    dot="""digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  P1 [label="提示词 v1", fillcolor="#dfe6fb", color="#2f4bd8", width=1.7];
  P2 [label="改动后的提示词 v2", fillcolor="#dfe6fb", color="#2f4bd8", width=2.1];
  E [label="评测集\n（自身也要版本化）", color="#136f3a", width=2.5];
  {rank=same; P1; P2; E;}
  B [label="基线：提示词版本 × 评测集版本 之间的对应关系", shape=note, fillcolor="#e9eef8", width=5.2];
  E -> B [style=dashed, label="固定"];
  V [label="回归判定：与基线比较 ⇒ 接受或回退，结论与版本一并留档", color="#136f3a", width=5.2];
  B -> V;
  S [label="另一条边界\n只跑改动点相关的用例会漏掉交叉影响\n⇒ 须定期跑全量", shape=note, fillcolor="#e9eef8", width=2.6];
  V -> S [style=dotted, arrowhead=none];
  N [label="三条纪律\n① 评测集不版本化 ⇒ 基线不可比\n② 除准确率外同时跟踪成本与延迟（改动常以成本换质量）\n③ 换模型必须重建基线，否则把模型差异误判为提示词差异", shape=note, fillcolor="#e9eef8", width=4.0];
  {rank=same; S; N;}
  E -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-r-01"] = dict(
    caption="判据分流图：按「模型类别 × 任务串行深度」决定写不写显式推理指令，并把思考内容的回传约束单列。",
    dot="""digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  Q [label="要不要写显式推理指令\n（CoT / 零样本 CoT）", fillcolor="#dfe6fb", color="#2f4bd8", width=3.2];
  A [label="条件 A：非推理模型\n或任务串行深度高\n⇒ 显式引导推理步骤仍有明确收益", color="#136f3a"];
  B [label="条件 B：推理模型且原生思考已开启\n⇒ 边际收益趋零甚至为负\n（官方口径：偏好一般性指令）", color="#b3181f"];
  C [label="条件 C：推理模型的思考功能被关闭\n⇒ 手写思维链降级为兜底手段", color="#9a5310"];
  Q -> A [label="该写"];
  Q -> B [label="不该写"];
  Q -> C [label="可写"];
  {rank=same; A; B; C;}
  N [label="另有一条与写法无关的硬约束（多轮对话）\n含思考内容的历史必须原样追加回传\n⇒ 改写历史会被报错或丢弃", shape=note, fillcolor="#e9eef8", width=3.2];
  B -> N [style=dotted, arrowhead=none];
  {rank=same; N; D;}
  D [label="零样本形态的差别\n只加一句「一步一步思考」\n⇒ 不需要示例即可诱发推理步骤", shape=note, fillcolor="#e9eef8"];
  A -> D [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-r-03"] = dict(
    caption="曲线对照图：自一致性的两个前提与样本数收益的早期饱和，以及系统偏见下「路径同错、投票放大置信度」。",
    dot="""digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  P [label="自一致性的两个前提\n① 答案唯一 ② 错误路径彼此发散", fillcolor="#dfe6fb", color="#2f4bd8", width=3.2];
  A [label="前提成立\n正确路径收敛、错误路径分散\n⇒ 多数投票有效", color="#136f3a"];
  B [label="前提不成立：模型存在系统性偏见\n所有路径犯同一个错\n⇒ 投票高置信度地输出错答案", color="#b3181f"];
  P -> A [label="成立"];
  P -> B [label="不成立"];
  {rank=same; A; B;}
  S [label="样本数与收益（现行证据）\n20 个样本：HotpotQA +0.4 个百分点\nMATH-500 +1.6 个百分点\ntoken 成本近线性增长 ⇒ 收益早期饱和", color="#9a5310", width=3.2];
  A -> S [label="实测"];
  {rank=same; S; T;}
  T [label="另一种收益口径\n需要推理忠实度而非仅准确率时\n投票可能提高忠实度\n但方向须实测确认", shape=note, fillcolor="#e9eef8", width=3.2];
  B -> T [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-r-04"] = dict(
    caption="搜索结构图：从候选思维到评估、展开与剪枝的树状搜索拓扑（含被丢弃的分支），以及思维图允许的中间结果合并。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  S [label="一步推理\n生成多个候选思维", fillcolor="#dfe6fb", color="#2f4bd8"];
  T1 [label="候选一", color="#136f3a", width=1.2];
  T2 [label="候选二", color="#136f3a", width=1.2];
  T3 [label="候选三", color="#b3181f", width=1.2];
  {rank=same; S; T1; T2; T3;}
  E [label="评估环节\n打分 / 判可行性", fillcolor="#dfe6fb", color="#2f4bd8"];
  S -> E [style=invis];
  T1 -> E; T2 -> E; T3 -> E;
  X [label="展开得分高的候选 ⇒ 可回溯的树状搜索", color="#136f3a"];
  P [label="其余候选被剪枝：按搜索策略放弃，不再展开", color="#b3181f"];
  G [label="思维图：中间结果可合并与复用，树扩展为图", color="#136f3a"];
  N [label="两条冲突结论（现行研究）\n低预算下某方法有冷启动瓶颈\n另一种方法的激进合并\n会永久丢弃未探索路径\n⇒ 不存在跨预算通用的固定策略", shape=note, fillcolor="#e9eef8"];
  {rank=same; X; P; G; N;}
  E -> X [label="保留"];
  E -> P [style=dashed, label="丢弃"];
  G -> N [style=dotted, arrowhead=none, constraint=false];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-r-05"] = dict(
    caption="轻量替代图：完整树搜索之下，步骤回溯与改写择优两类做法的共同前提（判据）与共同闸门（次数上限）。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  W [label="完整树搜索\n回溯点与分支全开\n⇒ 代价高", color="#9a5310"];
  B [label="做法一 步骤回溯\n判定某步失败后回到该步之前\n重新展开，而不是从头重来", fillcolor="#dfe6fb", color="#2f4bd8"];
  R [label="做法二 改写变体\n对同一输入生成多个表述或角度\n再按判据择优或合并", fillcolor="#dfe6fb", color="#2f4bd8"];
  W -> B [style=dashed, label="降级"];
  W -> R [style=dashed, label="降级"];
  {rank=same; B; R;}
  J [label="共同前提：一个可用的判据\n外部信号（测试通过 / 字段合法）可靠\n模型自评可靠性有限\n⇒ 无判据时退化为随机重试", color="#136f3a"];
  B -> J [label="需要"];
  R -> J [label="需要"];
  {rank=same; J; L;}
  L [label="工程闸门\n最大回溯次数与最大候选数写死\n超限即返回当前最优\n并记录未收敛样本", shape=note, fillcolor="#e9eef8"];
  J -> L [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-r-06"] = dict(
    caption="压缩比对照图：原报告的最优极简程度与代码任务上的实测节省幅度差距悬殊，以及质量损失与「预算也是待调参量」。",
    dot="""digraph fig {
  rankdir=TB; bgcolor="transparent";
  %(node)s %(edge)s
  A [label="完整思维链\ntoken 基线 100%%", fillcolor="#dfe6fb", color="#2f4bd8", width=4.0];
  B [label="原报告的最优情形：token 最少降到 7.6%%\n准确率持平或超越完整思维链", color="#136f3a", width=4.0];
  C [label="代码任务全量样本实测：最省时变体仍用 55.4%%\n且仅保持原有代码质量的九成以上（存在质量损失）", color="#b3181f", width=4.0];
  A -> B [label="原报告"];
  A -> C [label="跨域外推"];
  {rank=same; B; C;}
  D [label="另一条路线：在提示中声明 token 预算\n预算取值本身决定压缩成效\n⇒ 预算也是需要调参的对象", shape=note, fillcolor="#e9eef8", width=4.0];
  C -> D [style=dotted, arrowhead=none];
  {rank=same; D; E;}
  E [label="结论口径\n7.6%% 是各任务中的最优情形，不是目标值\n极简草稿应当作待测变体", shape=note, fillcolor="#e9eef8", width=4.0];
  B -> E [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-r-07"] = dict(
    caption="循环图：ReAct 的「思考—行动—观察」三步回路，三条现行实现路径，以及四类失效计数与轮数上限。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  T [label="思考\n分析当前状态\n与所需工具", fillcolor="#dfe6fb", color="#2f4bd8"];
  A [label="行动\n发起工具调用", fillcolor="#dfe6fb", color="#2f4bd8"];
  O [label="观察\n读取工具返回的\n真实反馈", fillcolor="#dfe6fb", color="#2f4bd8"];
  T -> A; A -> O; O -> T [style=dashed, label="未得结论则继续"];
  P [label="三条现行实现路径\n① 模型原生工具调用\n② 框架封装的循环\n③ 手写格式约束（受限环境）", color="#136f3a"];
  O -> P [label="停止条件"];
  {rank=same; P; N;}
  N [label="四类失效模式\n格式塌陷 ⇒ 调用不被解析\n工具滥用 ⇒ 成本失控\n死循环 ⇒ 轮数耗尽\n被观察结果带偏 ⇒ 污染回到上下文", shape=note, fillcolor="#e9eef8"];
  A -> N [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))

FIGS["pe-r-08"] = dict(
    caption="强度阶梯图：自评 / 独立评估 / 外部信号驱动三种反思来源的可靠性递增，与纯自评对事实性错误的失灵机制。",
    dot="""digraph fig {
  rankdir=LR; bgcolor="transparent";
  %(node)s %(edge)s
  S1 [label="强度一 模型自评\n自己检查自己的输出\n可靠性最低 · 成本最低", color="#b3181f"];
  S2 [label="强度二 独立评估\n另一个模型或另一段提示\n按判据评估", color="#9a5310"];
  S3 [label="强度三 外部信号驱动\n测试通过 / 校验器报错\n工具返回预期结果", color="#136f3a"];
  S1 -> S2 [label="可靠性递增"];
  S2 -> S3 [label="可靠性递增"];
  {rank=same; S3; N;}
  N [label="为什么自评会失灵\n它依赖与生成同一套内部表征\n能纠正遗漏与格式问题\n对事实性与逻辑错误几乎无效\n⇒ 无外部信号时反思沿同一个错误走得更远\n并给错误结论更高的置信度", shape=note, fillcolor="#e9eef8"];
  S3 -> N [style=dotted, arrowhead=none];
  {rank=same; S1; L;}
  L [label="无外部信号时的纪律\n限制反思轮数\n或改为引入独立评估者", shape=note, fillcolor="#e9eef8"];
  S1 -> L [style=dotted, arrowhead=none];
}""" % dict(node=NODE_ATTR, edge=EDGE_ATTR))


# ---------------------------------------------------------------- 组页 mini-DAG（★ 2026-10-16 第 6 轮：G19 / B″ 收口）
#
# ★ 为什么是**派生**而不是手绘 11 张：用户裁决 B″ 要求组页图「由 `10-dag-data/dag.json` 数据派生」。
#   手绘 11 张会与 dag.json 各自漂移（本仓最贵的一类教训就是「同一真相两份」）。
#   本函数是**唯一**的组图来源：`gen-figs.py` 用它出图，`gen-groups.py` 用它的 caption 渲染
#   （⇒ caption 不会两处各写一份），门控可同源复算。
#
# ★ 布局决策（含一条**实测逼出的修正**，登记在 CRITERIA-CHANGE-R07.md）：
#   D6 原设计是「`rankdir=LR` + **按层** `{rank=same}`（层变成列）」。实测各组的**不同层数**
#   为 3–8（G00 6 / G01 5 / G02 8 / G03 7 / G04 8 / G05 8 / G06 6 / G07 4 / G08 3 / G09 7 / GD-N 4）
#   ⇒ 每层一列时最宽约 1860–2650 单位，在 **804px** 内容列下要缩到 **0.43×**，13pt 文字只剩 ~5.6px。
#   而当时的 `check_spec` **只卡高度上界、不卡缩放比** ⇒ 这类图会「机检全绿、人看不见」。
#   ⇒ 修正为**层带**：把连续层合成「带」，每带一列（≤ GROUP_COL_MAX 列），带宽 B 由数据求解；
#     并给 `check_spec` 补**缩放比下界**（MIN_SCALE）。列自左向右层号递增，带内节点的层号写在标签里。
GROUP_COL_MAX = 3        # 列数上限（每列 = 一个相邻层带）
GROUP_BAND_MAX = 5       # 带宽上限（层数 15 以内都解得开；越界即 SystemExit，fail-closed）
MIN_SCALE = 0.90         # 缩放比下界 = CONTENT_COL_PX / viewBox.w（⇒ viewBox.w ≤ ~893）
SHORT_NAME_LIMIT = 12    # 节点中文短名截断长度（实测全站最长 18 字，仅 8/67 超过 12）


def _short_name(name, limit=SHORT_NAME_LIMIT):
    """`中文名（English）` → 中文短名（超长截断加 `…`）；⛔ 不改数据，只在图内做标签压缩。"""
    cn = (name or "").split("（")[0].strip()
    return cn if len(cn) <= limit else cn[:limit] + "…"


def _band_size(n_layers, col_max=GROUP_COL_MAX):
    """由层数求解带宽 B（最小 B 使 `ceil(L/B) ≤ col_max`）——确定性、可复现、⛔ 无实验性调参。"""
    b = max(1, -(-n_layers // col_max))
    if b > GROUP_BAND_MAX:
        raise SystemExit("[FAIL] 层带求解失败：层数 %d 需要带宽 %d > 上限 %d（须重新设计图件布局）"
                         % (n_layers, b, GROUP_BAND_MAX))
    return b


def group_figs(nodes, groups, edges):
    """派生 11 张组图：`{fid: {"caption": str, "dot": str}}`，`fid = grp-<gid 小写>`。

    图内包含（⛔ 只读 `nodes/groups/edges`，⛔ 不改数据）：
      · 本组成员（label = 中文短名 + 组号·层号）；
      · **内部边**（两端都在组内）= 实线，⛔ 不逐条标 `rel`（9 条边时标了会糊成一片）；
      · **跨组边** = 汇聚成一个 `组外接口` stub（虚线 + 「出 K 条 / 入 J 条」），逐**端点成员**连一条
        （实测每向端点成员 ≤5 个 ⇒ 11 张图宽度与连线数都可控）。
    """
    out = {}
    for g in sorted(groups, key=lambda x: x["order"]):
        gid = g["id"]
        members = sorted([n for n in nodes if n["group"] == gid], key=lambda x: (x["layer"], x["id"]))
        if not members:
            raise SystemExit("[FAIL] 组 %s 无成员 ⇒ 组图无对象" % gid)
        mids = {m["id"] for m in members}
        inner = [e for e in edges if e["source"] in mids and e["target"] in mids]
        out_edges = [e for e in edges if e["source"] in mids and e["target"] not in mids]
        in_edges = [e for e in edges if e["target"] in mids and e["source"] not in mids]
        layers = sorted({m["layer"] for m in members})
        b = _band_size(len(layers))
        bands = [layers[i:i + b] for i in range(0, len(layers), b)]
        slot = {m["id"]: "n%d" % i for i, m in enumerate(members)}
        # 节点 → 层带序号（★ 键必须是**节点 id**：首版误用 layer 作键 ⇒ 索引时报 KeyError）
        band_of = {m["id"]: bi for bi, bd in enumerate(bands)
                   for m in members if m["layer"] in bd}
        L = []
        A = L.append
        A("digraph grp {")
        A("  rankdir=LR; bgcolor=\"transparent\";")
        A("  %s %s" % (NODE_ATTR, EDGE_ATTR))
        for m in members:
            A('  %s [label="%s\\n(%s · 第 %d 层)", fillcolor="#dfe6fb", color="#2f4bd8"];'
              % (slot[m["id"]], _short_name(m["name"]).replace('"', ""), m["id"], m["layer"]))
        # 层带 = 一列（rankdir=LR 下 `rank=same` 即同列）；带内节点纵向堆叠
        for bi, bd in enumerate(bands):
            ids = [slot[m["id"]] for m in members if m["layer"] in bd]
            A("  {rank=same; %s;}" % "; ".join(ids))
        # 相邻带之间补**不可见**边 ⇒ 强制「带序 = 层序」（⛔ 否则无内部边的两带可能被并成一列）
        for bi in range(len(bands) - 1):
            last = [m for m in members if m["layer"] in bands[bi]][-1]
            nxt = [m for m in members if m["layer"] in bands[bi + 1]][0]
            A("  %s -> %s [style=invis, weight=100];" % (slot[last["id"]], slot[nxt["id"]]))
        # 内部边：实线；同带内的边不参与排序（否则与 rank=same 相抵，dot 会画成 flat edge）
        for e in inner:
            same = band_of[e["source"]] == band_of[e["target"]]
            A("  %s -> %s [%s];" % (slot[e["source"]], slot[e["target"]],
                                    "constraint=false" if same else "color=\"#7c8aa5\""))
        # 对外接口 stub：与首带 / 末带同列，虚线连接**端点成员**（去重，⛔ 不画平行边）
        if in_edges:
            A('  stub_in [label="组外接口\\n入 %d 条", shape=note, style="filled", '
              'fillcolor="#e9eef8", color="#9a5310"];' % len(in_edges))
            first = [slot[m["id"]] for m in members if m["layer"] in bands[0]]
            A("  {rank=same; stub_in; %s;}" % "; ".join(first))
            for tgt in sorted({e["target"] for e in in_edges}):
                A("  stub_in -> %s [style=dashed, constraint=false, arrowhead=none];"
                  % slot[tgt])
        if out_edges:
            A('  stub_out [label="组外接口\\n出 %d 条", shape=note, style="filled", '
              'fillcolor="#e9eef8", color="#9a5310"];' % len(out_edges))
            lastband = [slot[m["id"]] for m in members if m["layer"] in bands[-1]]
            A("  {rank=same; stub_out; %s;}" % "; ".join(lastband))
            for src in sorted({e["source"] for e in out_edges}):
                A("  %s -> stub_out [style=dashed, constraint=false, arrowhead=none];"
                  % slot[src])
        A("}")
        caption = ("本组内部依赖与对外接口：组内 %d 个节点、%d 条内部边、%d 条跨组边（层 %d–%d）；"
                   "列自左向右按依赖深度递增，同一列为相邻层带。"
                   % (len(members), len(inner), len(out_edges) + len(in_edges),
                      min(layers), max(layers)))
        out["grp-" + gid.lower()] = dict(caption=caption, dot="\n".join(L) + "\n")
    return out


def _load_dag():
    with open(os.path.join(DATA, "dag.json"), encoding="utf-8") as f:
        return json.load(f)


def all_figs():
    """全部图件源：手绘图（`FIGS`）+ 数据派生的组图（`group_figs`）。⛔ 这是图件的唯一入口。"""
    dag = _load_dag()
    merged = dict(FIGS)
    derived = group_figs(dag["nodes"], dag["groups"], dag["edges"])
    for fid in derived:
        if fid in merged:
            raise SystemExit("[FAIL] 图件 id 冲突：%s 同时由手绘与派生提供" % fid)
    merged.update(derived)
    return merged


# ---------------------------------------------------------------- 后处理

def postprocess(svg):
    """确定性后处理五步；⛔ 任一步骤不得依赖时钟/环境。"""
    s = svg
    s = re.sub(r"<\?xml[^>]*\?>\s*", "", s)
    s = re.sub(r"<!DOCTYPE[^>]*>\s*", "", s)
    s = re.sub(r"<!--.*?-->\s*", "", s, flags=re.S)
    # ② 删 graphviz 的背景多边形（fill="white"/"transparent" 那一个）
    s = re.sub(r'<polygon fill="white" stroke="transparent"[^/]*/>\s*', "", s)
    # ③ 去固定尺寸，保 viewBox
    s = re.sub(r'<svg width="[^"]*" height="[^"]*"', "<svg", s, count=1)
    # ④ hex → CSS 变量（含 fill/stroke/color 三类；大小写归一）
    def sub_hex(m):
        # ★ 捕获组不含 `#`，故查表时必须补回（本轮实测：漏补 ⇒ 全部 hex 原样留在产物里，
        #   且 `grep -c 'var(--'` 得 0 —— 一个"看起来跑了、其实什么都没做"的静默失败）
        key = "#" + m.group(1).lower()
        var = HEX2VAR.get(key)
        if not var:
            raise SystemExit("[FAIL] 图件出现调色板外的色值 %s：⛔ 不得留裸色值" % key)
        return "var(%s)" % var
    s = re.sub(r'#([0-9a-fA-F]{6})\b', sub_hex, s)
    # ⑤ 字体栈统一
    s = re.sub(r'font-family="[^"]*"', 'font-family="%s"' % FONT_STACK.replace('"', "'"), s)
    # 补 a11y 与响应式钩子（★ 去尺寸后 `<svg` 后面跟的是换行 ⇒ ⛔ 不能按 `<svg ` 匹配）
    s = re.sub(r"<svg\b", '<svg class="fig__svg" role="img"', s, count=1)
    return s.strip() + "\n"


CONTENT_COL_PX = 804      # 宽屏内容列宽（与 P34 的预算同源）
FIG_MAX_H_PX = 600        # 图在内容列宽下的渲染高度上限（约 0.67 屏，保证「图 + 图注」一屏可见）


def _viewbox(svg):
    m = re.search(r'viewBox="([-\d. ]+)"', svg)
    if not m:
        raise SystemExit("[FAIL] 图件缺 viewBox")
    return [float(x) for x in m.group(1).split()]


def check_spec(fid, svg):
    """★ 用户反馈 #2：*「绘图之前就要定好图片规格」* —— 两条**上下界**，缺一不可：

      ① **渲染高度 ≤ FIG_MAX_H_PX**：否则读者要缩放到 67% 才能一屏看完（本轮首次实测的真实缺陷）；
      ② **缩放比 ≥ MIN_SCALE**（★ 2026-10-16 第 6 轮补）：`CONTENT_COL_PX / viewBox 宽`。
         ⛔ 原规格**只卡 ①**：一张 2650px 宽的图渲染高度只有几十 px，① 轻松通过，但它会被缩到
            0.30×、13pt 文字落到 4px —— **机检全绿、人看不见**，与 R-08 自己写的
            「⛔ 不得靠 CSS 缩放掩盖」直接相悖。★ 加上 ② 后**当场抓到存量图 `pe-f-06`（1016px ⇒ 0.79×）**，
            见 `CRITERIA-CHANGE-R07.md` §L·D-1。
    """
    vb = _viewbox(svg)
    w, h = vb[2], vb[3]
    if w <= 0 or h <= 0:
        raise SystemExit("[FAIL] %s 的 viewBox 非法：%s" % (fid, vb))
    rendered_h = h / w * CONTENT_COL_PX
    if rendered_h > FIG_MAX_H_PX:
        raise SystemExit("[FAIL] %s 规格超限：viewBox %gx%g ⇒ 在 %dpx 内容列下高 %.0fpx > 上限 %dpx"
                         "（⛔ 不得靠 CSS 缩放掩盖，须重排图件本身）"
                         % (fid, w, h, CONTENT_COL_PX, rendered_h, FIG_MAX_H_PX))
    scale = CONTENT_COL_PX / w
    if scale < MIN_SCALE:
        raise SystemExit("[FAIL] %s 缩放比过低：viewBox 宽 %g ⇒ 在 %dpx 内容列下缩放 %.2f× < 下界 %.2f×"
                         "（13pt 文字将落到 %.1fpx，读者看不见；⛔ 不得靠 CSS 缩放掩盖，"
                         "须重排图件本身：细分层带 / 缩短标签 / 减少列数）"
                         % (fid, w, CONTENT_COL_PX, scale, MIN_SCALE, 13.0 * scale))
    return rendered_h


def render(dot_src):
    p = subprocess.run(["dot", "-Tsvg"], input=dot_src, capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        raise SystemExit("[FAIL] dot 渲染失败：%s" % p.stderr[:400])
    return postprocess(p.stdout)


def build():
    out = {}
    for fid, spec in sorted(all_figs().items()):
        out[fid + ".dot"] = spec["dot"].strip() + "\n"
        svg = render(spec["dot"])
        check_spec(fid, svg)
        out[fid + ".svg"] = svg
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for fid, spec in sorted(all_figs().items()):
            print("%-10s %s" % (fid, spec["caption"]))
        return 0
    expected = build()
    if a.check:
        bad = []
        for rel, text in sorted(expected.items()):
            p = os.path.join(OUTDIR, rel)
            if not os.path.exists(p):
                bad.append((rel, "缺失"))
            elif open(p, encoding="utf-8").read() != text:
                bad.append((rel, "漂移"))
        for b in bad:
            print("[FAIL] 图件%s：%s" % (b[1], b[0]))
        if bad:
            return 1
        print("[PASS] 图件 %d 件与派生结果一致" % len(expected))
        return 0
    if a.write:
        if not os.path.isdir(OUTDIR):
            os.makedirs(OUTDIR, exist_ok=True)
        for rel, text in sorted(expected.items()):
            with open(os.path.join(OUTDIR, rel), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print("[OK] %s（%d B）" % (rel, len(text.encode())))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
