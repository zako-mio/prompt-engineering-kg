#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-state.py —— 发布状态出口生成器

输出：`04-prototype/PUBLISH-STATE.json`（经 gen-common.page_shell 之外的纯数据出口；
它不是页面，故不经外壳函数，但由同一生成链路产出并纳入幂等与孤儿管理）。

内容：as_of / edition / round / published / counts / content_status / pending_nodes / gates / repo。
`pending_nodes` 显式登记本轮"架构在册、内容待填充"的节点，⛔ 不让它们静默缺席。
"""

import importlib.util
import json
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

GATE_DECL = ("python3 16-checkpoint/gate_prototype.py（判据 P01–P41；退出码 0 = 全部 PASS；"
             "本文件不缓存裁决，避免出现陈旧 PASS）")
CHANGE_DECL = ("16-checkpoint/CRITERIA-CHANGE-P05.md（2026-10-15 判据变更：`why` 上限与 `summary` 下限"
               "两次同型缺陷，处置均为「换判据」而非「改数字」；口径写死为 caliber = 汉字数 + 拉丁词数）")
CHANGE_DECL_2 = ("16-checkpoint/CRITERIA-CHANGE-P23.md（2026-10-15 判据变更：设计系统换底座与交互重做"
                 "同批新增 P23–P32 共 10 条判据；含 P20 作用域由「消费 7/11」改为「消费 11/11」、"
                 "P09 白名单由一类拆为两类（脚本 / 图片）、P11 由契约快照口径改为站点调色板口径）")
CHANGE_DECL_3 = ("16-checkpoint/CRITERIA-CHANGE-P34.md（2026-10-15 判据变更：用户走查反馈轮新增 P34"
                 "「宽屏左栏完整性 + 根入口标题宽度预算」；同时改写令牌 `--fs-hero` 取值"
                 "（hub 的 4rem → 本站按内容列宽预算推导的 3rem）、左栏形态"
                 "（rail 撑满整页竖向、跨到页脚行、显示开关由顶部导航搬入侧栏底端）、"
                 "显示开关由 2 枚扩为 4 枚（主题 / 动效 / 背景素材 / 正文字号，后者走新增令牌"
                 " `--fs-body-lg`）、窄屏档开关收进 `<details>` 折叠件）")
CHANGE_DECL_4 = ("16-checkpoint/CRITERIA-CHANGE-P22.md（2026-10-16 判据变更：P22 由「content_status"
                 " 数量配额（complete ≥3 / registered ≥60 + 固定名单）」改为「**状态↔内容一致性**」"
                 "（complete ⟺ 8 区块全非空；registered ⟹ lab/evidence/pitfalls 必须为空，禁半填）；"
                 "撤销无因果依据的 `registered ≥60` 与数据侧 C24/C25/C27 旧形，"
                 "并与 `10-dag-data/_selfcheck.py` 同源同值）")
CHANGE_DECL_5 = ("16-checkpoint/CRITERIA-CHANGE-P05-R5.md（2026-10-16 判据变更执行：`boundary` 由"
                 "「渲染期从句切出」升为**节点级必填字段**（执行 CRITERIA-CHANGE-P05.md 的 C3 裁决）；"
                 "同批新增 P05 的三条硬断言（非空 / 不与 why·intro 整句重复 / 正文不残留引导串）、"
                 "P01 的 `need_node` 加 `boundary`、数据侧 C32 由子串探测改为字段断言，"
                 "并修 `gen-md` 的 MD 镜像（原只印 `why` ⇒ 字段化后会静默丢失边界））"
                 "★ 本行原文曾把「第 3 节」写成内部编号记号，被 P12 当场判 FAIL（公开产物禁内部编号）"
                 "⇒ 已改写为「的 C3 裁决」；该命中是判据起作用的正例，非回归。")
CHANGE_DECL_6 = ("16-checkpoint/CRITERIA-CHANGE-R07.md（2026-10-16 判据变更：R-07 的作用域由「每页」"
                 "收敛为**知识承载页（节点页 / 组页；不含分组索引）**——同批**补产物**（11 个组页各一张"
                 "由 dag.json 数据派生的本组 mini-DAG）与**改契约**（两半同批），其余 5 页写成显式排除清单 + "
                 "全集闭合断言；R-03 的作用域同批对齐为**正文承载页**；并给 R-08 的图件规格补**缩放比下界**"
                 "（原规格只卡高度上界，会放过「机检全绿、人看不见」的宽图，当场抓到存量图 pe-f-06 缩放 0.79 倍））")
CHANGE_DECL_7 = ("16-checkpoint/CRITERIA-CHANGE-P13-C58-P41.md（2026-10-16 判据变更：四条「已实现但无判据」"
                 "的面全部升级为判据——P13 扩出 counts 逐项比对（G12）与 MD 镜像内容比对（G13）；"
                 "数据侧新增 C58 引文回源（G14）；门控新增 P41「已登记的历史句不得复活」（G20，窄版，"
                 "含显式豁免清单与「提及/断言」引号判定）；判据数 40 → 41）")
CHANGE_DECL_8 = ("16-checkpoint/CRITERIA-CHANGE-R01.md（2026-10-16 第 7 轮判据变更：**R-01 口径由"
                 "「h1 纯中文」改为「h1 的拉丁缩写须在术语台账登记」**（大小写敏感子串命中 "
                 "`glossary.json` 的某个 `term`）——触发事实 = 数据侧 5 个节点名含拉丁词"
                 "（ReAct / RAG / Agent），旧口径下一发布即 FAIL 并**阻塞 28 个待写节点**；"
                 "用户裁决走 **N1**（改判据、⛔ 不改名）。同批删除 P35 ② 的 `kind != \"interactive\"`"
                 "**控制流豁免**，改走「显式对象集 + 排除清单 + 全集闭合断言」（本仓通用作用域机制）；"
                 "夹具 32 → 34，并新增②的阈值两侧探针（已登记 ⇒ PASS / 未登记 ⇒ FAIL / 低于 3 字母 ⇒ 不触发））")
CHANGE_DECL_9 = ("16-checkpoint/CRITERIA-CHANGE-P35-G4.md（2026-10-15 判据变更：P35 ⑪–⑭ 四条新断言"
                 "（组页节点与前后继区竖表 / 组页横表列数 ≤3（代理）/ 组页依赖一行结构 / 导读结论句 = "
                 "结论来源），并把 ④⑤⑦⑨ 的作用域扩到组页与视图页；见 `CRITERIA-CHANGE-P35-G4.md`）")
CHANGE_DECL_10 = ("16-checkpoint/CRITERIA-CHANGE-P38-P40.md（2026-10-15 判据变更：新增 P38「验证通道："
                  "能力声明与事实一致 ＋ 渲染产物非退化」、P39「判据变更登记件引用解析」、P40「轮次台账"
                  "结构合规」；判据数 37 → 40；见 `CRITERIA-CHANGE-P38-P40.md`）")
CHANGE_DECL_11 = ("16-checkpoint/CRITERIA-CHANGE-P39.md（2026-10-16 第 7 轮判据变更：**P39 补第 ④ 条断言**"
                  "「结构化出口闭合」——`PUBLISH-STATE.json` 的 `gates` 里 `criteria_change_*` 的**键集合 "
                  "⟺ 磁盘 `CRITERIA-CHANGE-*.md` 文件集合**（双向）；缺键 / 孤儿键 / gates 不可读或键集为空 ⇒ FAIL。"
                  "触发事实：第 6 轮末态**磁盘 9 件而 gates 只载荷 7 件**（缺 P35-G4 / P38-P40），"
                  "而 P39 当时报「9 个 / 9 个、违例 0 处」**全绿** —— 因为它的 ①②③ 只判「文件名字符串"
                  "有没有在文本里出现过」，⛔ 不判「有没有被**结构化字段承载**」；同批补全 `gates` 7 → 10 键，"
                  "P39 夹具 3 → 6）")
CHANGE_DECL_12 = ("16-checkpoint/CRITERIA-CHANGE-R08.md（2026-10-16 第 8 轮判据变更：**三条判据的对象收窄**"
                  "＋**新增发布级元数据判据族**。① P09（R-18）：`<link>` 按 **rel 闭集**分流，"
                  "元数据类 rel（canonical / icon / alternate…）不当加载类资源，⛔ 不再「一切 link 皆资源」；"
                  "同批加 rel 闭集与「canonical/alternate 必须本站自指」两条防退化断言。"
                  "② P12（R-19）：「主机名」一项只在**正文**上判（摘掉 href 与带主机的 content；"
                  "sitemap/robots 再摘掉 URL 词），属性的取值归 P09/P30。"
                  "③ R-08：内容列口径落实为「`.layout > main` 的 border-box 内宽 ＝ 868 − 2×32 ＝ 804px」。"
                  "④ 新增 **A1–A7**（`gate_a11y.py`）与 **S1–S11**（`gate_seo_meta.py`）两个独立门控；"
                  "⑤ 图件补 `aria-label`（由 `gen-figs` 从图注首句派生）并去掉 Graphviz 的无信息 `<title>fig</title>`。"
                  "★ 触发事实：SH4 落地时 P09/P12 **整站 FAIL** 51 页（判假探针 `_probe/r8_t1_p09_probe.py` 实测），"
                  "根因是「判据对象 > 断言对象」（R-23 同型第 3 次复发）；P01–P41 编号未动）")
ASSET_DECL = ("16-checkpoint/CRITERIA-CHANGE-P23.md 与 gen-common.BACKDROP_CREDITS："
              "`assets/backdrop/` 为站点级只读图片资产（真实摄影素材），"
              "与 `13-interactive/vendor/` 的脚本白名单**分开声明、互不包含**；"
              "夜间帧 CC BY 4.0（须署名）、日间帧 CC0 1.0；页脚逐素材登记署名与出处")

ROUND = 8      # ★ 2026-10-16 第 8 轮：产出本快照的轮次


MD_EXTS = (".md",)
# ★ 镜像族里**不随节点/分组翻转**的固定件 —— 逐条对应 `gen-md.generate()` 里真看得到的行：
#   `index.md`（根索引）＋ `groups/index.md`（分组索引）＋ `learning-path.md` ＋ `frontier.md` = **4**
MD_FIXED = 4
MD_DIR_REL = "15-md/"      # ★ `counts.md` 是**镜像数**，⛔ 不含发布根上的手写 `README.md`


def _md_expected(groups, complete):
    """镜像数的**真相源侧**派生：固定件 ＋ 每组 1 ＋ 每已发布节点 1。

    ★ 为什么不数磁盘（2026-10-16 第 8 轮）：本条是给 `P13` 的 G12（`counts` ⟺ 产物实数）用的
      **期望值**。若期望值取自磁盘，它就和 G12 的实测值同源 ⇒ **判据变成恒真**
      （少一个镜像文件时期望值跟着少，永远相等）。⇒ 必须从**真相源对象**推。
    ★ 实测校验（⛔ 不靠推）：`gen-md.generate()` 的产出集合大小 = `MD_FIXED + len(groups) + len(complete)`
      —— 本轮把 `MD_FIXED` 由误写的 **4** 修正为与其一致之前，G12 当场 FAIL（判据干了它该干的事）；
      ★ 复算命令：`python3 -c "import importlib.util as u; s=u.spec_from_file_location('m','gen-md.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print(len(m.generate()))"`
      ⇒ 期望与实测必须**逐数**相等，任一侧变动都判 FAIL（这才是双向）。
    """
    return MD_FIXED + len(groups) + len(complete)


def state_doc():
    data = C.load_sources()
    dag = data["dag"]
    nodes = dag["nodes"]
    groups = dag["groups"]
    complete = sorted(n["id"] for n in nodes if n["content_status"] == "complete")
    registered = sorted(n["id"] for n in nodes if n["content_status"] == "registered")
    # ★ 2026-10-16 修 bug：原写 `3 + (len(groups)+1) + 2 + 1 + 1` —— 那个字面量 3 是**节点页数**，
    #   被写死后第 1 波一翻态就与真实产物数不符（属「有保质期的读数」被固化进生成器）。
    #   改为由 `complete` 派生。★ 无判据覆盖此面 ⇒ 已登记为未落实（见 ROUND-LEDGER 第 5 轮的 G12）。
    html_count = len(complete) + (len(groups) + 1) + 2 + 1 + 1
    # ★ 2026-10-16 第 8 轮：镜像数改由**磁盘实数**派生（见 `_md_on_disk` 的 docstring）
    md_count = _md_expected(groups, complete)
    return {
        "as_of": dag["meta"]["as_of"],
        "edition": dag["meta"]["edition"],
        "round": ROUND,
        # ★ 2026-10-16 第 8 轮：站点**已真实发布**（仓 `zako-mio/prompt-engineering-kg`、Pages `build_type=workflow`、hub 自动收录 `has_pages=true`）
        "published": True,
        # ★ `publish` 段是**发布事实**（⛔ 不是声明）：与 `published` 的**内部一致性**由 P13 判
        #   （`published=true` 却缺字段、或 `published=false` 却残留本段，均 FAIL）。
        "publish": {
            # ★ `repo` 写成**完整 URL**：① 它是可点的（比裸 slug 更有用）；
            #   ② 让 P12 的「元数据面」摘除逻辑能覆盖它（裸 slug 不含 scheme，摘不掉）。
            #   ★ 同一处置口径的另一次实测：sitemap/robots 的 URL 载荷也是靠这一条摘掉的。
            "repo": "https://github.com/zako-mio/prompt-engineering-kg",
            "entry_url": C.SITE_BASE_URL,
            "pages_build_type": "workflow",
            "hub_listed": True,
            "note": "★ 本仓与同类卫星站的**有意偏离**：同类站走 legacy 分支发布（`main /` 为发布根），"
                    "而 legacy **不支持子目录** ⇒ 本仓发布根在 `04-prototype/`，必须走 Actions 的 "
                    "artifact 通道。理由与代价见 `04-prototype/README.md` §六。",
        },
        "counts": {
            "nodes": len(nodes), "groups": len(groups), "edges": len(dag["edges"]),
            "layers": dag["meta"]["layer_count"], "html": html_count, "md": md_count,
            # ★ `md_total` = 发布面**全部** `*.md`（＝ 镜像 ＋ 手写 `README.md`）；
            #   与 `md`（镜像数）分开，两个口径各自可被独立判（见 P13 的 G12）。
            "md_total": md_count + 1,
            "node_pages": len(complete), "group_pages": len(groups) + 1,
            "view_pages": 2, "interactive": 1, "root": 1,
            "assets": len(C.BACKDROP_CREDITS) + 1,
        },
        "assets": {
            "images": sorted(C.BACKDROP_CREDITS.keys()),
            "favicon": "assets/favicon.svg",
            "whitelist": {
                "kind": "image",
                "prefix": C.ASSET_PREFIX,
                "exts": list(C.ASSET_EXTS),
                "note": "★ 第二类白名单，与 13-interactive/vendor/ 的脚本白名单分开声明、互不包含。"
                        "受检集合中命中该前缀的引用必须全部为图片扩展名，"
                        "⛔ 不得混入 script / stylesheet / @import。",
            },
            "credits": {fn: {"name": c["name"], "author": c["author"], "license": c["license"],
                             "url": c["url"], "frame": c["frame"]}
                        for fn, c in sorted(C.BACKDROP_CREDITS.items())},
        },
        "content_status": {
            "complete": len(complete), "registered": len(registered),
            "complete_nodes": complete,
        },
        "pending_nodes": registered,
        "pending_note": ("节点页按内容波次逐步落盘（只落 `complete` 节点）；`registered` 节点的知识"
                         "架构位置已确定、导读已写，其「架构在册」状态在组页、学习路径与交互图上"
                         "以徽标显式标注，并在此逐条登记，⛔ 不静默留白。"
                         "★ 措辞于 2026-10-16 改为与轮次无关（原文写死「待第 2 轮波次填充」，"
                         "属会被后续轮次读旧的表述）。"),
        "gates": {"prototype": GATE_DECL, "criteria_change_P05": CHANGE_DECL,
                  "criteria_change_P22": CHANGE_DECL_4,
                  "criteria_change_P05_R5": CHANGE_DECL_5,
                  "criteria_change_R07": CHANGE_DECL_6,
                  "criteria_change_P13_C58_P41": CHANGE_DECL_7,
                  "criteria_change_P23": CHANGE_DECL_2, "criteria_change_P34": CHANGE_DECL_3,
                  "criteria_change_R01": CHANGE_DECL_8,
                  "criteria_change_P35_G4": CHANGE_DECL_9,
                  "criteria_change_P38_P40": CHANGE_DECL_10,
                  "criteria_change_P39": CHANGE_DECL_11,
                  "criteria_change_R08": CHANGE_DECL_12,
                  "assets": ASSET_DECL},
        "repo": None,
    }


def generate(root=None):
    return {"PUBLISH-STATE.json": json.dumps(state_doc(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"}


if __name__ == "__main__":
    for k, v in sorted(generate().items()):
        print(k, len(v))
