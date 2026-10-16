#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-common.py —— 唯一外壳与站内约定（prompt-engineering-kg 原型站）

职责（对应 ADR-001 第一条硬性决定与 BD-001 生成层/令牌层边界）：
  - `page_shell()`：**全站唯一**的外壳函数。节点页 / 组页 / 视图页 / 根入口 / 交互入口
    一律经它产出；本仓不存在第二套模板。
  - 站内导航（顶部导航 + 左栏 rail + 面包屑 + 回到根 + 回到所属组）——**二选一不叠加**。
  - 令牌块内联：调 `16-checkpoint/gen-tokens.py --print` 取内容，⛔ 不自己拼 CSS 令牌。
  - 对比度工具：直接复用 gen-tokens.py 的函数，⛔ 不另造第二套公式。
  - 目录契约常量：受检集合、白名单例外、相对路径基准。
  - 背景层（真实摄影素材）、动效层（[data-reveal]）、主题/动效三态开关。

★ 本件相对 v1 的结构性变更（依据 H1 hub 设计系统 / H2 十条硬规则 / H3 差距总表）：
  ① 主题：撤掉 `light-dark()`，改 `[data-theme]` 三块 ＋ `<head>` pre-paint 脚本 ＋ 三态开关；
  ② 底座：表面阶梯 5 级、描边三级按语义分工、卡片四件套、字号只用 6 档令牌、间距 7 级；
  ③ 色板收敛：撤掉 11 组彩虹色，组身份改由**文字与中性序号**承载（⛔ 色相不承载身份）；
  ④ 交互：`:hover` 全站包 `@media (hover: hover)`；卡片 stretched link（成对）；
     导航 `<1180` 顶部 / `≥1180` 左栏 rail（二选一不叠加）；触控目标 ≥44px；
  ⑤ 动效：`[data-reveal]` 用**独立 `translate` 属性**（⛔ 不用 `transform`）＋ 60ms 错峰
     ＋ 双保险无 JS 兜底 ＋ 三态开关 ＋ 两条独立熔断（错峰步长按 M2 预算反解，见动效层注释）；
  ⑥ 背景层：真实摄影素材 ＋ 分辨率阶梯（显式媒体查询，⛔ 不用 `image-set`）＋ 纱幕
     ＋ 局部 scrim ＋ 非当前主题帧 `display:none` ＋ 页脚许可署名。

⛔ 本模块不裁决产物是否合规（那是门控层的职责），也不定义任何语义令牌取值。
"""

import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True  # 生成链路不留 __pycache__ 副产物

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.normpath(os.path.join(HERE, ".."))
DATA_DIR = os.path.join(SITE_ROOT, "10-dag-data")
GEN_TOKENS = os.path.join(HERE, "gen-tokens.py")

# ---------------------------------------------------------------- 目录契约（生成前约定）

TEMPLATE_ID = "shell-v2"

DIR_NODES = "11-node-pages"
DIR_GROUPS = "12-groups"
DIR_INTERACTIVE = "13-interactive"
DIR_VIEWS = "14-views"
DIR_MD = "15-md"
DIR_ASSETS = "assets"

# 判 0 外链 / 0 外链脚本 / 0 @import / 0 跨目录相对资源引用的受检集合
SELF_CONTAINED_DIRS = (DIR_NODES, DIR_GROUPS, DIR_VIEWS)
SELF_CONTAINED_ROOT_FILES = ("index.html",)

# ★ 第一类白名单例外：13-interactive/ 允许引用其同目录 vendor/ 下的本地**脚本**
WHITELIST_DIR = DIR_INTERACTIVE
WHITELIST_RESOURCE_PREFIX = "vendor/"

# ★ 第二类白名单例外（本轮新增，与第一类**分开声明、互不包含**）：
#   站点级只读**图片**资产。允许以 `assets/` 前缀的相对路径引用，扩展名须为图片；
#   ⛔ 禁止 script / link[rel=stylesheet] / @import / 任何非图片资源混入。
ASSET_PREFIX = "assets/"
ASSET_EXTS = (".webp", ".png", ".jpg", ".jpeg", ".svg", ".avif")

# 生成层拥有的产物目录（孤儿清理范围）；13-interactive/vendor/ 与 assets/ 不在范围内
OWNED_DIRS = (DIR_NODES, DIR_GROUPS, DIR_VIEWS, DIR_MD, DIR_INTERACTIVE)
OWNED_EXTS = (".html", ".md")
OWNED_SKIP_PREFIX = (DIR_INTERACTIVE + "/vendor/",)

SITE_TITLE = "新一代提示词工程 · 知识全景图"
SITE_TAGLINE = "面向有工程基础、提示词工程尚未系统化的工程师"

NAV_ITEMS = (
    ("index.html", "首页"),
    (DIR_INTERACTIVE + "/index.html", "全景图"),
    (DIR_VIEWS + "/01-learning-path.html", "学习路径"),
    (DIR_VIEWS + "/02-frontier.html", "新一代模块"),
    (DIR_GROUPS + "/index.html", "知识分组"),
)

# ---------------------------------------------------------------- 背景层素材登记（★ 许可）

# 素材名 / 作者 / 许可 / 出处，逐文件登记；页脚须逐条署名（CC BY 4.0 须署名）。
# `assets/backdrop/` 下的每个**图片**文件都必须在本表里（门控 P32 逐文件断言）。
# ★ 作者与出处取自同目录的许可台账 `assets/backdrop/LICENSES.json`（唯一真相源，只读）。
BACKDROP_CREDITS = {
    "night-portrait-1080.webp": {
        "frame": "night", "tier": "默认（窄屏）",
        "name": "A 340-million pixel starscape from Paranal",
        "author": "S. Guisard (ESO)",
        "license": "CC BY 4.0",
        "url": "https://www.eso.org/public/images/eso0934a/",
        "rights": "欧洲南天天文台（ESO）公开影像，署名后可使用；派生件按分辨率阶梯缩放",
    },
    "night-1280.webp": {
        "frame": "night", "tier": "≥760px",
        "name": "A 340-million pixel starscape from Paranal",
        "author": "S. Guisard (ESO)",
        "license": "CC BY 4.0",
        "url": "https://www.eso.org/public/images/eso0934a/",
        "rights": "同上，按视口宽度分档的缩放副本",
    },
    "night-1920.webp": {
        "frame": "night", "tier": "≥1100px",
        "name": "A 340-million pixel starscape from Paranal",
        "author": "S. Guisard (ESO)",
        "license": "CC BY 4.0",
        "url": "https://www.eso.org/public/images/eso0934a/",
        "rights": "同上，按视口宽度分档的缩放副本",
    },
    "night-2560.webp": {
        "frame": "night", "tier": "≥1100px 且 2dppx，或 ≥1900px",
        "name": "A 340-million pixel starscape from Paranal",
        "author": "S. Guisard (ESO)",
        "license": "CC BY 4.0",
        "url": "https://www.eso.org/public/images/eso0934a/",
        "rights": "同上，按视口宽度与像素密度分档的缩放副本",
    },
    "day-1280.webp": {
        "frame": "day", "tier": "备用档（≥760px 以下的窄屏候选）",
        "name": "Lofoten, Norway",
        "author": "Unsplash 贡献者（原始上传见 Wikimedia Commons）",
        "license": "CC0 1.0",
        "url": "https://upload.wikimedia.org/wikipedia/commons/8/86/Lofoten%2C_Norway_%28Unsplash%29.jpg",
        "rights": "CC0 1.0：著作权人放弃权利，不要求署名；本站仍登记出处",
    },
    "day-1920.webp": {
        "frame": "day", "tier": "默认（窄屏）与 ≥760px",
        "name": "Lofoten, Norway",
        "author": "Unsplash 贡献者（原始上传见 Wikimedia Commons）",
        "license": "CC0 1.0",
        "url": "https://upload.wikimedia.org/wikipedia/commons/8/86/Lofoten%2C_Norway_%28Unsplash%29.jpg",
        "rights": "同上，按视口宽度分档的缩放副本",
    },
    "day-2560.webp": {
        "frame": "day", "tier": "≥1100px，或 ≥1900px",
        "name": "Lofoten, Norway",
        "author": "Unsplash 贡献者（原始上传见 Wikimedia Commons）",
        "license": "CC0 1.0",
        "url": "https://upload.wikimedia.org/wikipedia/commons/8/86/Lofoten%2C_Norway_%28Unsplash%29.jpg",
        "rights": "同上，按视口宽度分档的缩放副本",
    },
}

# ★ 同目录下的**非图片**登记件（许可台账本体）：随素材同处一个目录，必须一并登记，
#   但它不是素材、不进页脚署名（页脚署名只对**图片素材**逐条给出四要素）。
BACKDROP_LEDGER = {
    "LICENSES.json": {
        "kind": "license-ledger",
        "note": "背景摄影素材许可台账（逐件素材的出处 / 许可 / 派生说明 / 逐文件字节数）。",
        "url": "https://creativecommons.org/licenses/by/4.0/",
    },
}


# ★ 分辨率阶梯（⛔ 不用 `image-set`，用显式媒体查询以便门控可读）
BACKDROP_LADDER = (
    # (媒体条件, 夜间文件, 日间文件, 档位说明)
    ("", "night-portrait-1080.webp", "day-1920.webp", "默认（窄屏）"),
    ("(min-width: 760px)", "night-1280.webp", "day-1920.webp", "≥760px"),
    ("(min-width: 1100px)", "night-1920.webp", "day-2560.webp", "≥1100px"),
    ("(min-width: 1100px) and (min-resolution: 2dppx)", "night-2560.webp", "day-2560.webp",
     "≥1100px 且 2dppx"),
    ("(min-width: 1900px)", "night-2560.webp", "day-2560.webp", "≥1900px"),
)

# ---------------------------------------------------------------- 交互作用面登记表
#
# ★ 依据 H1 §7.2 C1「双向闭合」：CSS 中含 `:hover` / `:focus-within` 的选择器集合
#   必须 ⟺ 本登记表。漏登记 ⇒ FAIL；**幽灵登记**（登记了但 CSS 里没有）⇒ FAIL。
#   另：每条登记的 `base` 选择器必须在全量产物里**至少命中 1 个元素**（C2 空集守卫）。
# `kind` 语义（H1 §7.1）：self = 自身即交互目标；container = 非交互容器但承载交互件；
#   decor = 纯装饰反射面（⛔ 不得暗示可点击）。
#
# 字段：kind / base（用于产物命中计数的基选择器）/ selectors（CSS 侧必须逐字出现的集合）/ note
INTERACTION_SURFACE = (
    {"kind": "self", "base": "a", "note": "正文与导航中的全部站内/站外链接",
     "selectors": ("a:hover", "a:focus-visible")},
    {"kind": "self", "base": "button", "note": "三态开关与图控制按钮",
     "selectors": ("button:focus-visible",)},
    {"kind": "self", "base": "summary", "note": "折叠控件（交互入口的无脚本等价导航）",
     "selectors": ("summary:hover",)},
    {"kind": "container", "base": ".card",
     "note": "可点卡片：整卡反馈面由拉伸层铺满，故按 container 记",
     "selectors": (".card:hover",)},
    {"kind": "self", "base": ".card__title-link",
     "note": "卡片标题链接，其 ::after 即整卡拉伸层",
     "selectors": (".card__title-link:hover", ".card__title-link:focus-visible")},
    {"kind": "self", "base": ".rail__link", "note": "左栏导航项（≥1180px 形态）",
     "selectors": (".rail__link:hover",)},
    {"kind": "self", "base": ".nav__link", "note": "顶部导航项（<1180px 形态）",
     "selectors": (".nav__link:hover",)},
    {"kind": "self", "base": ".skip", "note": "跳到正文的 skip link",
     "selectors": (".skip:hover",)},
    {"kind": "self", "base": ".gchip", "note": "组序号 + 名称 chip（组页索引、图例、元信息行）",
     "selectors": (".gchip:hover",)},
    {"kind": "self", "base": ".switch__btn", "note": "主题/动效三态开关按钮",
     "selectors": (".switch__btn:hover",)},
    {"kind": "self", "base": ".cy-bar__btn", "note": "交互图的返回总览按钮",
     "selectors": (".cy-bar__btn:hover",)},
)


def surface_selectors():
    """登记表展开出的 CSS 侧选择器全集（供门控 P29 做双向闭合对账）。"""
    out = set()
    for e in INTERACTION_SURFACE:
        out.update(e["selectors"])
    return out

# ---------------------------------------------------------------- 模块加载（文件名含连字符）

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_TOKENS = None


def tokens():
    """gen-tokens.py 模块（唯一令牌/对比度口径来源）。"""
    global _TOKENS
    if _TOKENS is None:
        _TOKENS = load_module(GEN_TOKENS, "pekg_gen_tokens")
    return _TOKENS


_TOKENS_CSS = None
TOKENS_SOURCE = None


def tokens_css():
    """令牌块：调 gen-tokens.py --print 取内容（⛔ 不自己拼）。"""
    global _TOKENS_CSS, TOKENS_SOURCE
    if _TOKENS_CSS is not None:
        return _TOKENS_CSS
    css = None
    try:
        proc = subprocess.run([sys.executable, GEN_TOKENS, "--print"],
                              capture_output=True, text=True, timeout=120)
        if proc.returncode == 0 and proc.stdout.strip():
            # print() 会额外补一个换行；派生态自身以 "\n" 结尾
            out = proc.stdout
            css = out[:-1] if out.endswith("\n\n") else out
            TOKENS_SOURCE = "subprocess:gen-tokens.py --print"
    except Exception:
        css = None
    if css is None:
        css, _ = tokens().derive()
        TOKENS_SOURCE = "import:gen-tokens.py derive()"
    # 与进程内派生结果对账：两条路径必须逐字节一致（防"第二套令牌"）
    inproc, _ = tokens().derive()
    if css != inproc:
        raise SystemExit("[FAIL] 令牌块与 gen-tokens.py 派生结果不一致 —— 存在第二套令牌来源")
    _TOKENS_CSS = css
    return _TOKENS_CSS


def token_block_sha():
    return hashlib.sha256(tokens_css().encode("utf-8")).hexdigest()


def label_for(bg):
    """标签前景色：复用 gen-tokens.py 的亮度择优（⛔ 不重写公式）。"""
    return tokens().label_for(bg)


def contrast(a, b):
    return tokens().contrast_ratio(a, b)


# ---------------------------------------------------------------- 数据读取

def load_json(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def load_sources():
    """读全部真相源（只读）。"""
    return {
        "dag": load_json("dag.json"),
        "frontier": load_json("frontier.json"),
        "glossary": load_json("glossary.json"),
        "sources": load_json("sources.json"),
        "site_tokens": load_json("site-tokens.json"),
        "site_palette": load_json("site-palette.json"),
    }


def palette_values():
    """站点调色板取值（令牌层唯一真相源）。"""
    return load_json("site-palette.json")["values"]


def palette_names():
    """角色名 → CSS 变量名。"""
    return load_json("site-palette.json")["css_names"]


def palette_css_value(role, mode):
    """取某角色在某主题下的 CSS 字面值（供画布等需要具体色值的场合）。

    ★ 依据 H3 G1：⛔ 不得用 `getComputedStyle` 读自定义属性——其计算值是不求值的
    token 流，直接拿去当画布颜色会静默失效。此处从调色板直接取字面值。
    """
    return palette_values()[role][mode]


# ---------------------------------------------------------------- HTML 工具

def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def para(s):
    return "<p>" + esc(s).replace("\n", "<br>") + "</p>"


def id_slug(nid):
    return nid.lower()


def node_page_rel(nid):
    return "%s/%s.html" % (DIR_NODES, id_slug(nid))


def group_page_rel(gid):
    return "%s/%s.html" % (DIR_GROUPS, gid.lower())


def md_node_rel(nid):
    return "%s/nodes/%s.md" % (DIR_MD, id_slug(nid))


def md_group_rel(gid):
    return "%s/groups/%s.md" % (DIR_MD, gid.lower())


def status_label(status):
    return {"complete": "内容已写满", "registered": "架构在册 · 内容待填充"}.get(status, status)


def status_badge(status):
    cls = "badge badge--ok" if status == "complete" else "badge badge--pending"
    return '<span class="%s">%s</span>' % (cls, esc(status_label(status)))


def frontier_status_badge(status):
    m = {"confirmed": ("badge badge--ok", "已确认"), "disputed": ("badge badge--warn", "有争议"),
         "unverified": ("badge badge--pending", "未证实")}
    cls, label = m.get(status, ("badge badge--pending", status))
    return '<span class="%s">%s</span>' % (cls, esc(label))


def group_label(gid, name):
    """组标签：★ 组身份由**文字与中性序号**承载（⛔ 色相不承载身份）。"""
    return "%s %s" % (gid, name)


def group_mark(gid):
    """组序号标记：中性色等宽序号，是组身份的唯一视觉载体。"""
    return '<span class="gseq">%s</span>' % esc(gid)


def group_chip(gid, name, href=None):
    """组 chip：中性底 + 序号 + 文字标题；⛔ 不按组分配色相。"""
    inner = group_mark(gid) + '<span class="gchip__name">%s</span>' % esc(name)
    if href:
        return '<a class="gchip" href="%s">%s</a>' % (esc(href), inner)
    return '<span class="gchip">%s</span>' % inner


# ---------------------------------------------------------------- 样式（全站唯一）
#
# ★ 硬约束（门控 P24 逐条判）：本常量中 ⛔ 不得出现任何令牌外的
#   `font-size` / `border-radius` / 颜色字面值 / `padding|margin` 字面值 / 自定义属性声明。
#   允许：`var(--…)`、结构性 0/auto/100%/1px 描边/2px 焦点环、`color-mix(in srgb, …)`。

BASE_CSS = """
/* ============================================================
   唯一外壳样式（shell-v2）· 令牌全部来自上方生成块
   ============================================================ */
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
html[data-theme="light"]{color-scheme:light}
html[data-theme="dark"]{color-scheme:dark}
body{margin:0;background:var(--surface-page);color:var(--text-primary);
 line-height:1.75;font-family:var(--font-sans);font-size:var(--fs-body)}

/* --- 显示偏好（由侧栏/顶部导航的开关驱动）---
   ⛔ 本节不得声明任何自定义属性：令牌声明点全站唯一（P23）；值只能取令牌（P24）。 */
/* ① 背景素材：off ⇒ 背景层整块不渲染（纯装饰层，关闭后正文坐在 --surface-page 上）。
   与 P27 的「非当前主题帧 display:none」同规：都用 display:none，⛔ 不用 opacity/visibility。 */
:root[data-backdrop="off"] .backdrop{display:none}
/* ② 字号：large ⇒ **改根字号**（16→18px）。★ 2026-10-15 用户反馈轮修正：此前只改 body 的
   font-size，于是标题/导航/标签/表格各自走自己的 --fs-* 令牌、**不随动** ⇒ 用户实测「部分生效」
   且层次比例失真（正文变大而标题不变）。改为根字号后，配合**布局令牌 rem 化**
   （--container / --rail-w / --nav-h / --space-* 全为 rem），全站字号、间距、栏宽、内容列宽
   **等比放大**，层次比例逐字不变；根入口 h1 的行宽与内容列宽同比缩放 ⇒ P34 的余量比例不变。
   ⛔ 不得退回「只改 body」的写法：那不是作用域选择，是**半生效**。 */
:root[data-fontsize="large"]{font-size:var(--fs-root-lg)}
code,kbd,samp,pre{font-family:var(--font-mono)}
a{color:var(--link);text-decoration:none}
a:focus-visible,button:focus-visible,summary:focus-visible,input:focus-visible,
select:focus-visible,textarea:focus-visible,[tabindex]:focus-visible{
 outline:2px solid var(--focus-ring);outline-offset:2px}
h1,h2,h3,h4{line-height:1.3;margin:var(--space-4) 0 var(--space-2)}
h1{font-size:var(--fs-hero);line-height:1.06;letter-spacing:-0.035em;margin-top:var(--space-3)}
h2{font-size:var(--fs-section);line-height:1.25;letter-spacing:-0.02em;
 padding-bottom:var(--space-1);border-bottom:1px solid var(--border-subtle)}
h3{font-size:var(--fs-card-title);letter-spacing:-0.01em}
p,li,dd,dt,blockquote{max-width:var(--measure)}
ul.tight li,ol.tight li{margin:var(--space-1) 0}

/* --- 布局骨架：<1180 顶部导航 / ≥1180 左栏 rail（二选一，⛔ 不叠加） --- */
.layout{max-width:var(--container);margin:0 auto;padding:0 var(--space-3)}
.rail{display:none}
main{padding-bottom:var(--space-6)}
.wrap{max-width:var(--container);margin:0 auto;padding:0 var(--space-3)}

/* --- 顶部导航（<1180px 形态） --- */
.site-head{position:sticky;top:0;z-index:20;background:var(--surface-raised);
 border-bottom:1px solid var(--border-subtle)}
.head-in{display:flex;flex-wrap:wrap;gap:var(--space-2) var(--space-3);
 align-items:center;justify-content:space-between;min-height:var(--nav-h)}
.brand{font-weight:700;color:var(--text-primary);font-size:var(--fs-nav)}
.brand span{font-weight:400;color:var(--text-secondary);font-size:var(--fs-label);
 margin-left:var(--space-1)}
.nav{display:flex;flex-wrap:wrap;gap:var(--space-1) var(--space-3);align-items:center}
.nav__link{font-size:var(--fs-nav);color:var(--text-secondary);min-height:44px;
 display:inline-flex;align-items:center}
.switches{display:flex;flex-wrap:wrap;gap:var(--space-2);align-items:center}
.switch{display:flex;gap:var(--space-1);align-items:center;margin:0;padding:0}
.switch__legend{font-size:var(--fs-label);color:var(--text-secondary);
 margin-right:var(--space-1)}
/* ★ 开关按钮与「显示设置」折叠钮共用同一套外观（同一枚控件的两种形态） */
.switch__btn,.settings__summary{font:inherit;font-size:var(--fs-label);cursor:pointer;min-height:44px;
 background:var(--surface-subtle);color:var(--text-secondary);
 border:1px solid var(--border-line);border-radius:var(--radius-pill);
 padding:0 var(--space-2)}
.switch__btn[aria-pressed="true"]{background:var(--brand-soft);color:var(--text-primary);
 border-color:var(--brand-primary)}
/* ★ 窄屏档（<1180）四组开关共 10 枚，横排会把 sticky 头部撑成三四行 ⇒ 收进原生折叠件。
   `summary` 在交互作用面登记表内（`summary:hover` 已登记），故 ⛔ 不新增任何 :hover 选择器。 */
.settings{display:block}
.settings__summary{display:inline-flex;align-items:center;list-style:none}
.settings__summary::-webkit-details-marker{display:none}
.settings>.switches{margin-top:var(--space-2)}

/* --- 左栏 rail（≥1180px 形态；与顶部导航二选一） ---
   ★ 形态调整（2026-10-15，用户反馈 #2）：rail **撑满整页竖向**（grid 行高 = 正文高度，
   见下方 ≥1180 档的 align-self:stretch），内层 100dvh sticky ⇒ 视口内常驻；
   导航在上、显示开关锚在底端（`.rail__foot` 的 margin-top 取 auto，见规则本体）。
   ⛔ align-self 只在 ≥1180 档给：基础档 rail 是 display:none，无需参与布局。
   ⚠ 本注释里 ⛔ 不得写出「margin-top 冒号 auto」那种**声明形态**的串：门控 P24 的扫描面
   包含 CSS 注释（只剥令牌块、不剥注释），注释里出现 margin/padding 的声明形态会被判
   令牌外硬编码（本轮实测：19 页 × 11 处假阳，全来自上一版注释里的那一串）。 */
.rail{background:var(--surface-raised);border-right:1px solid var(--border-subtle)}
.rail__in{position:sticky;top:0;height:100dvh;overflow:auto;
 display:flex;flex-direction:column;gap:var(--space-2);
 padding:var(--space-4) var(--space-3)}
.rail__title{font-size:var(--fs-label);letter-spacing:0.08em;color:var(--text-tertiary);
 text-transform:uppercase;margin:0 0 var(--space-2)}
.rail__list{list-style:none;margin:0;padding:0}
.rail__link{display:flex;align-items:center;min-height:44px;padding:0 var(--space-2);
 border-radius:var(--radius);color:var(--text-secondary);font-size:var(--fs-nav)}
.rail__link[aria-current="page"]{color:var(--text-primary);background:var(--surface-subtle)}
/* 侧栏底部「显示设置」区：锚在 rail 底端，与导航之间用弱分隔线分开 */
.rail__foot{margin-top:auto;padding-top:var(--space-3);
 border-top:1px solid var(--border-subtle)}
/* 同一份开关标记，两种排布：顶部导航横向、侧栏**两列栅格**（四组共 10 枚，纵向堆叠会
   把侧栏撑到 ~930px 高、在 900px 视口里被截断 ⇒ 两列后约 400px）。legend 独占整行。 */
.rail .switches{flex-direction:column;align-items:stretch;gap:var(--space-3)}
.rail .switch{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--space-1)}
.rail .switch__legend{grid-column:1 / -1;margin-right:0}
.rail .switch__btn{padding:0 var(--space-1)}

/* ============================================================
   内容阅读单元 v2（2026-10-15 用户走查第 2 轮反馈后新增；见 CONTENT-V2.md）
   ★ 总则「一行只干一件事」：身份 / 标签 / 元信息 / 结论 / 地图 各自独占一行容器。
   ★ 全部值取令牌（P24）；⛔ 本节不声明任何自定义属性（P23）。
   ============================================================ */
/* --- 标题区：h1 纯中文一行；英文名独立成行、去括号 --- */
.page-en{color:var(--text-secondary);font-size:var(--fs-nav);letter-spacing:0.01em;
 margin:0 0 var(--space-1);max-width:var(--measure)}
/* --- 身份行（节点号 · 状态 · 分组 · 层）与标签行（tags）分离 --- */
.tag-row{display:flex;flex-wrap:wrap;gap:var(--space-1);align-items:center;
 margin:0 0 var(--space-3)}
/* --- 页首导读：先给结论（一句话），再给结构地图（可跳转） --- */
.read-map{background:var(--surface-subtle);border:1px solid var(--border-subtle);
 border-radius:var(--radius-lg);padding:var(--space-3);margin:var(--space-3) 0}
.read-map__label{font-size:var(--fs-label);letter-spacing:0.08em;color:var(--text-tertiary);
 text-transform:uppercase;margin:0 0 var(--space-1)}
.read-map__claim{font-size:var(--fs-card-title);line-height:1.6;color:var(--text-primary);
 font-weight:600;margin:0;max-width:var(--measure)}
.read-map__nav{display:flex;flex-wrap:wrap;gap:var(--space-1);margin:var(--space-2) 0 0;
 padding:0;list-style:none}
.read-map__nav a{display:inline-flex;align-items:center;min-height:44px;
 font-size:var(--fs-label);color:var(--text-secondary);
 border:1px solid var(--border-subtle);border-radius:var(--radius-pill);
 padding:0 var(--space-2)}
/* --- 区块序号（显式递进：先讲什么、再讲什么） --- */
.sec-no{font-family:var(--font-mono);font-size:var(--fs-label);letter-spacing:0.08em;
 color:var(--text-tertiary);margin-right:var(--space-2)}
/* --- 阅读单元：主张句（加重 + 强调条）与展开点（每句一行） --- */
.claim{margin:var(--space-2) 0;padding-left:var(--space-3);
 border-left:2px solid var(--brand-primary);font-size:var(--fs-card-title);
 line-height:1.6;color:var(--text-primary);max-width:var(--measure)}
.points{list-style:none;margin:var(--space-2) 0 0;padding:0}
.points li{position:relative;padding-left:var(--space-4);margin:var(--space-1) 0;
 max-width:var(--measure)}
.points li::before{content:"";position:absolute;left:var(--space-2);top:0.8em;
 width:4px;height:4px;border-radius:var(--radius-pill);background:var(--border-line)}
/* --- 适用边界：独立块（⛔ 不混在主张句里） --- */
.boundary{margin:var(--space-3) 0;padding:var(--space-2) var(--space-3);
 border-left:2px solid var(--warning);background:var(--surface-subtle);
 border-radius:0 var(--radius) var(--radius) 0}
.boundary__label{font-size:var(--fs-label);letter-spacing:0.08em;color:var(--text-secondary);
 text-transform:uppercase;margin:0 0 var(--space-1)}
.boundary p{margin:0;max-width:var(--measure)}
/* --- 对照表：一行一件事（类别 ｜ 场景 ｜ 做法） --- */
.cmp-table caption{font-size:var(--fs-label)}
.cmp-table td:first-child,.cmp-table th:first-child{white-space:nowrap;color:var(--text-secondary)}
/* --- 图件（内联 SVG：随主题；⛔ 不外包固定尺寸容器） --- */
.fig{margin:var(--space-4) 0;padding:var(--space-3);background:var(--surface-raised);
 border:1px solid var(--border-card);border-radius:var(--radius-lg);
 box-shadow:var(--shadow-1),inset 0 1px 0 var(--edge-highlight)}
.fig__svg{display:block;width:100%;height:auto}
.fig figcaption{font-size:var(--fs-label);color:var(--text-secondary);
 margin-top:var(--space-2);max-width:var(--measure)}
.fig__src{color:var(--text-tertiary)}
/* --- 依赖链（前置 → 本节点 → 后继；一行） --- */
.relchain{display:flex;flex-wrap:wrap;gap:var(--space-1);align-items:center;
 margin:var(--space-2) 0}
.relchain__arrow{color:var(--text-tertiary);font-size:var(--fs-label)}
/* --- 渐进披露（原文 / 代码按需展开；CSS-only，⛔ 无 JS） --- */
.acc{border:1px solid var(--border-subtle);border-radius:var(--radius);
 background:var(--surface-stripe);padding:var(--space-1) var(--space-3);
 margin:var(--space-2) 0}
.acc>summary{font-size:var(--fs-label);color:var(--text-secondary);cursor:pointer;
 min-height:44px;display:inline-flex;align-items:center}
.acc[open]>summary{color:var(--text-primary)}
/* --- 实验步骤（编号 + 代码 + 预期观察） --- */
.steps{counter-reset:step;list-style:none;margin:var(--space-2) 0;padding:0}
.steps>li{position:relative;padding-left:var(--space-5);margin:var(--space-3) 0}
.steps>li::before{counter-increment:step;content:counter(step);
 position:absolute;left:0;top:0;width:var(--space-4);height:var(--space-4);
 display:flex;align-items:center;justify-content:center;border-radius:var(--radius-pill);
 background:var(--brand-soft);color:var(--text-primary);
 font-size:var(--fs-label);font-family:var(--font-mono)}
/* --- 竖表：长文字段一律纵向排列（⛔ 不横向滚动；反馈 #1） --- */
.kv-blocks{display:grid;gap:var(--space-2);margin:var(--space-2) 0}
.kv-block{border:1px solid var(--border-subtle);border-radius:var(--radius);
 background:var(--surface-stripe);padding:var(--space-2) var(--space-3)}
.kv-block__row{margin:var(--space-1) 0;max-width:var(--measure)}
.kv-block__k{display:block;font-size:var(--fs-label);color:var(--text-tertiary);
 letter-spacing:0.08em;text-transform:uppercase}
.kv-block__v{display:block;color:var(--text-primary)}
/* --- 枚举分点：位置化的有序结构（⛔ 不靠「其一其二」这几个字承担层次；反馈 #3） --- */
.enum-list{counter-reset:enum;list-style:none;margin:var(--space-1) 0 var(--space-1);
 padding:0}
.enum-list li{counter-increment:enum;position:relative;padding-left:var(--space-4);
 margin:var(--space-1) 0;max-width:var(--measure)}
.enum-list li::before{content:counter(enum);position:absolute;left:0;top:0;
 font-family:var(--font-mono);font-size:var(--fs-label);color:var(--text-tertiary)}
.point{margin:var(--space-2) 0 0;max-width:var(--measure);color:var(--text-primary)}
.points__block{list-style:none}
.points__block::before{display:none}
/* --- 总结 + 细节 清单（失效模式用） --- */
.pair-list li{margin:var(--space-2) 0;max-width:var(--measure)}
.pair__sum{display:block;font-weight:600;color:var(--text-primary)}
.pair__detail{display:block;color:var(--text-secondary)}
.relchain__label{font-size:var(--fs-label);color:var(--text-tertiary)}
/* --- 术语表 / 证据表：多维对照一律用表 --- */
.terms-table td:first-child,.ev-table td:first-child{white-space:nowrap}
/* --- 锚点目标：跳转落点留白 + 高亮（页首导读的落点） --- */
:target{scroll-margin-top:var(--space-5)}
h2:target,h3:target{background:var(--brand-soft);border-radius:var(--radius)}

/* --- 页脚 --- */
.site-foot{margin-top:var(--space-6);padding-top:var(--space-3);
 padding-bottom:var(--space-5);border-top:1px solid var(--border-subtle);
 color:var(--text-secondary);font-size:var(--fs-label)}
/* ★ 页脚在 .layout 之内（2026-10-15）：窄屏档横向内边距由 .layout 提供 ⇒ 收回 .wrap 的内边距，
   否则会叠成两倍（16→24→32 各加一次）。≥1180 档 .layout 横向内边距为 0，故改由 .site-foot 自带。 */
.layout>.site-foot .wrap{padding-left:0;padding-right:0}
.footer__credits{border-top:1px solid var(--border-subtle);margin-top:var(--space-3);
 padding-top:var(--space-2)}
.footer__credits h2{font-size:var(--fs-label);border:0;padding:0;margin:0 0 var(--space-1);
 color:var(--text-secondary);letter-spacing:0.08em;text-transform:uppercase}
.credits{list-style:none;margin:0;padding:0}
.credits li{margin:var(--space-1) 0;color:var(--text-secondary)}

/* --- 面包屑与元信息 --- */
.crumbs{font-size:var(--fs-label);color:var(--text-secondary);margin:var(--space-2) 0}
.crumbs ol{list-style:none;display:flex;flex-wrap:wrap;gap:var(--space-1);margin:0;padding:0}
.crumbs li+li::before{content:"›";margin-right:var(--space-1);color:var(--text-tertiary)}
.lede{color:var(--text-secondary);max-width:var(--measure)}
.meta-line{display:flex;flex-wrap:wrap;gap:var(--space-1) var(--space-2);align-items:center;
 color:var(--text-secondary);font-size:var(--fs-label);margin:var(--space-1) 0 var(--space-3)}

/* --- 卡片四件套（渐变底 + border-card + shadow-1 + 顶 1px 高光） ---
   ★ 两类卡片：`.card` 是**可点卡片**（含 .card__title-link 拉伸层，有悬停反馈）；
   `.card--flat` 是**纯内容块**（无链接 ⇒ 无悬停反馈、无 pointer 光标，
   ⛔ 不得有「看起来能点」的假可供性——H2 硬规则 2）。 */
.card{position:relative;isolation:isolate;margin:var(--space-3) 0;
 padding:var(--space-3);
 background:linear-gradient(180deg,var(--surface-raised) 0%,
  color-mix(in srgb,var(--brand-primary) 4%,var(--surface-raised)) 100%);
 border:1px solid var(--border-card);border-radius:var(--radius-lg);
 box-shadow:var(--shadow-1),inset 0 1px 0 var(--edge-highlight);
 transition:transform var(--dur-2) var(--ease-out),
  box-shadow var(--dur-2) var(--ease-out),border-color var(--dur-2) var(--ease-out)}
.card--flat{position:relative;margin:var(--space-3) 0;padding:var(--space-3);
 background:var(--surface-subtle);border:1px solid var(--border-subtle);
 border-radius:var(--radius-lg);cursor:auto}
.card>:first-child,.card--flat>:first-child{margin-top:0}
.card>:last-child,.card--flat>:last-child{margin-bottom:0}
/* ★ 拉伸层：反馈面 ≡ 热区。containing block 必须是卡片本体（.card 无 transform/filter/
   will-change，故定位基准即卡片自身）。⛔ 成对：卡内其它真链接必须抬升到 z-index:2。 */
.card__title-link{color:var(--text-primary);font-weight:600}
.card__title-link::after{content:"";position:absolute;inset:0;z-index:1}
.card__links{position:relative;z-index:2}

.grid{display:grid;gap:var(--space-3);grid-template-columns:repeat(auto-fit,minmax(15rem,1fr))}
.two-col{display:grid;gap:var(--space-3);grid-template-columns:repeat(auto-fit,minmax(17rem,1fr))}

/* --- 表格 --- */
table{border-collapse:collapse;width:100%;margin:var(--space-3) 0;font-size:var(--fs-nav)}
caption{text-align:left;color:var(--text-secondary);font-size:var(--fs-label);
 padding-bottom:var(--space-1)}
th,td{border:1px solid var(--border-subtle);padding:var(--space-1) var(--space-2);
 text-align:left;vertical-align:top}
thead th{background:var(--surface-subtle)}
tbody tr:nth-child(even){background:var(--surface-stripe)}
.table-scroll{overflow-x:auto;max-width:100%}

/* --- 术语 / 列表 / 代码 --- */
dl.terms{margin:0}
dl.terms dt{font-weight:600;margin-top:var(--space-2)}
dl.terms dd{margin:var(--space-1) 0 0 var(--space-3);color:var(--text-secondary)}
code{background:var(--surface-subtle);border:1px solid var(--border-subtle);
 border-radius:var(--radius);padding:0 var(--space-1);font-size:var(--fs-label)}
pre{background:var(--surface-subtle);border:1px solid var(--border-subtle);
 border-radius:var(--radius);padding:var(--space-2) var(--space-3);overflow:auto;max-width:100%;
 /* ★ 代码块折行（2026-10-15）：用户反馈 #1「尽可能不要有左右翻动的需求」——长命令行不折行
    会把代码块变成横向滚动区（P38 D 段实测 pe-f-01 溢出 637px / pe-r-02 208px）。
    ⛔ 不为变绿而放宽 P38：修的是产物，不是阈值。 */
 white-space:pre-wrap;word-break:break-word}
pre code{background:none;border:0;padding:0;font-size:var(--fs-label)}
blockquote{margin:var(--space-3) 0;padding:var(--space-2) var(--space-3);
 border-left:1px solid var(--border-line);background:var(--surface-subtle);
 color:var(--text-secondary)}
hr{border:0;border-top:1px solid var(--border-subtle);margin:var(--space-4) 0}

/* --- 徽标 / 标签（★ 胶囊圆角走令牌；⛔ 无组色相） --- */
.badge{display:inline-block;border:1px solid var(--border-line);
 border-radius:var(--radius-pill);padding:0 var(--space-2);font-size:var(--fs-label);
 line-height:1.7;color:var(--text-secondary)}
.badge--ok{border-color:var(--brand-primary);color:var(--text-primary)}
.badge--pending{color:var(--text-secondary)}
.badge--warn{border-color:var(--warning);color:var(--warning)}
.badge--danger{border-color:var(--danger);color:var(--danger)}
.tier{font-size:var(--fs-label);color:var(--text-secondary);
 border:1px solid var(--border-subtle);border-radius:var(--radius);padding:0 var(--space-1)}
.gseq{font-family:var(--font-mono);font-weight:700;font-size:var(--fs-label);
 color:var(--text-secondary);letter-spacing:0.04em}
.gchip{display:inline-flex;align-items:center;gap:var(--space-1);min-height:44px;
 background:var(--surface-subtle);border:1px solid var(--border-subtle);
 border-radius:var(--radius-pill);padding:0 var(--space-2);
 font-size:var(--fs-label);font-weight:500;color:var(--text-primary)}
.gchip__name{font-weight:400}
.legend{display:flex;flex-wrap:wrap;gap:var(--space-2) var(--space-3);align-items:center;
 font-size:var(--fs-label);color:var(--text-secondary);margin:var(--space-2) 0 var(--space-3)}
.layer-block{border:1px solid var(--border-subtle);border-radius:var(--radius-lg);
 padding:var(--space-2) var(--space-3);margin:var(--space-2) 0;
 background:var(--surface-stripe)}
.layer-block h3{margin-top:0}
.why-layer{color:var(--text-secondary);font-size:var(--fs-label);margin:var(--space-1) 0 0}
.node-list{list-style:none;padding:0;margin:var(--space-1) 0 0}
.node-list li{margin:var(--space-1) 0}
.nid{font-family:var(--font-mono);font-size:var(--fs-label);color:var(--text-secondary)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:var(--space-1) var(--space-2);
 margin:var(--space-2) 0;font-size:var(--fs-nav)}
.kv dt{color:var(--text-secondary)}
.kv dd{margin:0}
.summary-box{border-left:1px solid var(--brand-primary);background:var(--surface-subtle);
 padding:var(--space-2) var(--space-3);border-radius:0 var(--radius) var(--radius) 0;
 margin:var(--space-3) 0}
.pitfall-list li{margin:var(--space-1) 0}
.pitfall-list li::marker{color:var(--danger)}
.use-list li::marker{color:var(--brand-primary)}
.avoid-list li::marker{color:var(--warning)}
.notice{border:1px solid var(--border-line);border-left-width:2px;
 border-radius:0 var(--radius) var(--radius) 0;background:var(--surface-subtle);
 padding:var(--space-2) var(--space-3);margin:var(--space-3) 0}
.notice strong{color:var(--warning)}
.danger-note{border:1px solid var(--border-line);border-left-width:2px;
 border-radius:0 var(--radius) var(--radius) 0;background:var(--surface-subtle);
 padding:var(--space-2) var(--space-3);margin:var(--space-3) 0}
.danger-note strong{color:var(--danger)}
.ev{border:1px solid var(--border-subtle);border-radius:var(--radius);
 padding:var(--space-2) var(--space-3);margin:var(--space-2) 0;
 background:var(--surface-stripe)}
.ev .claim{font-weight:600;margin:0 0 var(--space-1)}
.ev .quote{margin:var(--space-1) 0 0;color:var(--text-secondary);
 border-left:1px solid var(--border-subtle);padding-left:var(--space-2);
 font-size:var(--fs-nav)}
.ev .src{font-size:var(--fs-label);color:var(--text-secondary);margin:var(--space-1) 0 0;
 word-break:break-all}

/* --- skip link（body 第一个子元素）--- */
.skip{position:absolute;left:-100vw;top:0;background:var(--brand-primary);
 color:var(--on-brand);padding:var(--space-1) var(--space-2);border-radius:var(--radius);
 z-index:99}
.skip:focus{left:var(--space-2);top:var(--space-2);position:fixed}

/* --- 背景层（真实摄影素材；DOM 顺序即堆叠顺序）--- */
.backdrop{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}
.backdrop__photo,.backdrop__veil,.backdrop__scrim{position:absolute;inset:0}
.backdrop__photo{background-size:cover;background-position:center;
 transform:scale(1.07);opacity:0.62}
.backdrop__photo--day{background-image:url("@@ASSETDIR@@backdrop/day-1920.webp");
 filter:hue-rotate(-18deg) saturate(0.9)}
.backdrop__photo--night{background-image:url("@@ASSETDIR@@backdrop/night-portrait-1080.webp");
 filter:contrast(1.5) brightness(0.62);display:none}
.backdrop__veil--day{background:linear-gradient(180deg,
 color-mix(in srgb,var(--surface-page) 88%,transparent) 0%,
 color-mix(in srgb,var(--surface-page) 94%,transparent) 100%)}
.backdrop__veil--night{background:linear-gradient(180deg,
 color-mix(in srgb,var(--surface-page) 72%,transparent) 0%,
 color-mix(in srgb,var(--surface-page) 86%,transparent) 100%);display:none}
.backdrop__scrim{background:linear-gradient(180deg,transparent 0%,
 color-mix(in srgb,var(--surface-page) var(--scrim-3),transparent) 100%)}
html[data-theme="dark"] .backdrop__photo--day,
html[data-theme="dark"] .backdrop__veil--day{display:none}
html[data-theme="dark"] .backdrop__photo--night,
html[data-theme="dark"] .backdrop__veil--night{display:block}
@media (prefers-color-scheme: dark){
 html:not([data-theme="light"]) .backdrop__photo--day,
 html:not([data-theme="light"]) .backdrop__veil--day{display:none}
 html:not([data-theme="light"]) .backdrop__photo--night,
 html:not([data-theme="light"]) .backdrop__veil--night{display:block}
}

/* --- 分辨率阶梯（显式媒体查询；⛔ 不用 image-set）--- */
@media (min-width: 760px){
 .backdrop__photo--night{background-image:url("@@ASSETDIR@@backdrop/night-1280.webp")}
 .backdrop__photo--day{background-image:url("@@ASSETDIR@@backdrop/day-1920.webp")}
}
@media (min-width: 1100px){
 .backdrop__photo--night{background-image:url("@@ASSETDIR@@backdrop/night-1920.webp")}
 .backdrop__photo--day{background-image:url("@@ASSETDIR@@backdrop/day-2560.webp")}
}
@media (min-width: 1100px) and (min-resolution: 2dppx){
 .backdrop__photo--night{background-image:url("@@ASSETDIR@@backdrop/night-2560.webp")}
 .backdrop__photo--day{background-image:url("@@ASSETDIR@@backdrop/day-2560.webp")}
}
@media (min-width: 1900px){
 .backdrop__photo--night{background-image:url("@@ASSETDIR@@backdrop/night-2560.webp")}
 .backdrop__photo--day{background-image:url("@@ASSETDIR@@backdrop/day-2560.webp")}
}

/* --- 交互图容器 --- */
.cy-wrap{border:1px solid var(--border-subtle);border-radius:var(--radius-lg);
 background:var(--surface-raised);overflow:hidden}
#cy{width:100%;height:min(72vh,40rem);display:block}
.cy-bar{display:flex;flex-wrap:wrap;gap:var(--space-2);align-items:center;
 justify-content:space-between;padding:var(--space-1) var(--space-2);
 border-bottom:1px solid var(--border-subtle)}
.cy-bar .hint{color:var(--text-secondary);font-size:var(--fs-label)}
.cy-bar__btn{font:inherit;font-size:var(--fs-label);cursor:pointer;min-height:44px;
 background:var(--surface-subtle);color:var(--text-primary);
 border:1px solid var(--border-line);border-radius:var(--radius);padding:0 var(--space-2)}
.cy-bar__btn[disabled]{cursor:not-allowed;opacity:0.6}

/* --- 动效层：[data-reveal] ★ 用独立 translate 属性，⛔ 不用 transform ---
   ★ 错峰步长 60ms：进场完成时间上界 1800ms 的预算反解。
   ★ **阈值的唯一来源是 `gate_prototype.MOTION_REVEAL_MAX`（当前 32）与 P28 的实读** ——
     本注释**⛔ 不写第二份阈值**（原文写「单页最大 16 个」，与门控常量 32 不符，属「同一名词两个口径」；
     2026-10-16 第 6 轮按 T-4 改为**只引来源、不抄数字**）。
   ★ 另修同族缺陷：本条注释此前**逐字重复了两遍**（第 785/786 行）⇒ 已去重。
   实测：第 6 轮收口时单页最大 [data-reveal] = 10 ⇒ 进场 = 60ms×(10−1) + --dur-4(850ms) = 1390ms ≤ 1800ms。
   该推导同时写进门控 P28 的说明，⛔ 不得只写在这里。 */
html.js-motion [data-reveal]{opacity:0;translate:0 var(--reveal-shift)}
html.js-motion [data-reveal].is-in{
 opacity:1;translate:0 0;
 animation:reveal-in var(--dur-4) var(--ease-out) both;
 animation-delay:calc(var(--i,0) * 60ms)}
@keyframes reveal-in{
 from{opacity:0;translate:0 var(--reveal-shift)}
 to{opacity:1;translate:0 0}
}
/* 熔断一：系统「减少动态效果」 */
@media (prefers-reduced-motion: reduce){
 :root:not([data-motion="on"]) *,
 :root:not([data-motion="on"]) *::before,
 :root:not([data-motion="on"]) *::after{
  animation-duration:0.001s;animation-iteration-count:1;transition-duration:0.001s}
 :root:not([data-motion="on"]) [data-reveal]{opacity:1;translate:0 0}
}
/* 熔断二：显式关闭（三态开关的 off 档） */
:root[data-motion="off"] *,
:root[data-motion="off"] *::before,
:root[data-motion="off"] *::after{
 animation-duration:0.001s;animation-iteration-count:1;transition-duration:0.001s}
:root[data-motion="off"] [data-reveal]{opacity:1;translate:0 0}

/* --- 容器内边距 16 → 24(≥640) → 32(≥1024) --- */
@media (min-width: 640px){
 .layout,.wrap{padding-left:var(--space-4);padding-right:var(--space-4)}
}
@media (min-width: 768px){
 .grid{grid-template-columns:repeat(auto-fit,minmax(17rem,1fr))}
}
@media (min-width: 1024px){
 .layout,.wrap{padding-left:var(--space-5);padding-right:var(--space-5)}
}
/* ★ 导航二选一：≥1180 顶部导航 display:none ＋ 左栏 rail 可见；⛔ 不叠加。
   ★ 显示开关随导航同档切换：<1180 在顶部导航内、≥1180 在 rail 底部（`.rail__foot`）
   ⇒ 任一宽度档下**可见的开关实例恰 1 组**（另一组由 display:none 关闭，不参与交互与
   无障碍树）。rail 自身 align-self:stretch ⇒ 撑满 grid 行高（＝正文 ＋ 页脚，故左栏铺满整页
   竖向）而非止于 100dvh。 */
@media (min-width: 1180px){
 .site-head{display:none}
 .rail{display:block;align-self:stretch;grid-row:1 / span 2}
 .layout{display:grid;grid-template-columns:var(--rail-w) minmax(0,1fr);
  align-items:start;padding-left:0;padding-right:0}
 .layout>main{padding:0 var(--space-5)}
 /* 页脚独占第 2 行、跨两列 ⇒ rail（跨 1–2 行）连同页脚区一并铺满竖向。
    ⛔ 页脚不得留在 .layout 之外：那样左栏只到正文底，页脚旁仍是空档。 */
 .layout>.site-foot{grid-column:1 / -1;padding-left:var(--space-5);padding-right:var(--space-5)}
}
@media (min-width: 1900px){
 .layout{max-width:var(--container)}
}

/* --- 悬停态：★ 全站 :hover 一律包在 @media (hover: hover) 内 --- */
@media (hover: hover){
 a:hover{color:var(--brand-primary);text-decoration:underline}
 .nav__link:hover{color:var(--text-primary)}
 .rail__link:hover{color:var(--text-primary);background:var(--surface-subtle)}
 .switch__btn:hover{border-color:var(--brand-primary);color:var(--text-primary)}
 .cy-bar__btn:hover{border-color:var(--brand-primary);color:var(--text-primary)}
 .card:hover{transform:translateY(-3px);border-color:var(--brand-tint);
  box-shadow:var(--shadow-2),inset 0 1px 0 var(--edge-highlight)}
 .card__title-link:hover{color:var(--brand-primary)}
 .gchip:hover{border-color:var(--border-line);color:var(--text-primary)}
 summary:hover{color:var(--text-primary)}
 .skip:hover{background:var(--brand-primary);color:var(--on-brand)}
}

/* --- 打印 --- */
@media print{
 .site-head,.rail,.switch,.switches,.cy-bar__btn,.backdrop{display:none}
 body{background:var(--surface-raised)}
}
"""


# ---------------------------------------------------------------- 内容阅读单元 v2（契约见 CONTENT-V2.md）

FIG_DIR = os.path.join(DATA_DIR, "figures")
BOUNDARY_MARK = "适用边界是"

_FIGS = None


def load_figures():
    """图件层：读 `10-dag-data/figures/*.svg`（由 gen-figs.py 预渲染入库；⛔ 构建期不调 graphviz）。"""
    global _FIGS
    if _FIGS is None:
        _FIGS = {}
        if os.path.isdir(FIG_DIR):
            for fn in sorted(os.listdir(FIG_DIR)):
                if fn.endswith(".svg"):
                    with open(os.path.join(FIG_DIR, fn), encoding="utf-8") as f:
                        _FIGS[fn[:-4]] = f.read().strip()
    return _FIGS


def sentences(text):
    """句子切分（口径与门控 P05 的 `sentences()` 同源）：按句末标点切，⛔ 不按逗号切。"""
    return [x for x in re.split(r"(?<=[。！？!?])", (text or "").strip()) if x.strip()]


def split_boundary(text):
    """按**显式标记**「适用边界是」切出边界从句。

    ⛔ 不做关键词猜测 —— HANDOFF-R2 §三 记的实测教训：`…而是边界：` 这类**主题词**会被正则误捕。
    只在数据里出现显式引导串时才切；切不出就原样保留（⛔ 不判错、不硬切）。
    """
    t = text or ""
    i = t.find(BOUNDARY_MARK)
    if i < 0:
        return t.strip(), None
    head = t[:i].strip()
    tail = t[i + len(BOUNDARY_MARK):].lstrip("—－-：: \u3000").strip()
    return head, (tail or None)


def split_pair(s):
    """按**全角冒号**切「总结 / 细节」；⛔ 无冒号则整条进总结列、细节留空（不硬切）。"""
    a, sep, b = str(s).partition("：")
    if sep and b.strip():
        return a.strip(), b.strip()
    return str(s).strip(), ""


ENUM_MARK_RE = re.compile(r"其[一二三四五六七八九十][，,、]")
ENUM_LEAD_RE = re.compile(r"^其[一二三四五六七八九十][，,、]\s*")


def split_enum(text):
    """把「…要点有三条：其一，A；其二，B；其三，C。」切成 (引导句, [A, B, C])。

    ★ 用户反馈 #3：*「三处争议就应该分三点，而不是一个大段——靠文字写三点，永远是通过
      位置模块来实现分点的层次结构」*。⇒ 只要数据里出现**显式序号标记**（其一/其二/…），
      就渲染成有序列表（位置化），⛔ 不靠「其一」这两个字本身承担层次。
    ★ 只在显式标记处切；⛔ 不做关键词猜测（切不出就原样返回，不硬切）。
    """
    t = text or ""
    m = ENUM_MARK_RE.search(t)
    if not m:
        return t, []
    head = t[:m.start()].rstrip("：: ，, ")
    items = []
    for seg in re.split(r"[；;]", t[m.start():]):
        seg = ENUM_LEAD_RE.sub("", seg.strip()).strip()
        if seg:
            items.append(seg)
    if len(items) < 2:
        return t, []
    return head, items


def enum_html(head, items):
    return ('%s<ol class="enum-list">%s</ol>'
            % (('<p class="point">%s</p>' % esc(head)) if head else "",
               "".join("<li>%s</li>" % esc(x) for x in items)))


def prose_html(text, boundary=None):
    """散文 → 主张句（加重）+ 展开点（每句一行）+（可选）适用边界块。

    ★ 为什么这样做：用户反馈「大段文字要人自己找句子间的关系、一眼看不到某句说了什么」。
      句子是**最小的可扫单元**；把每句摆成一行，读者可以扫读而不必解析段落。

    ★ 2026-10-16（B-1 / 判据变更 P05，见 `CRITERIA-CHANGE-P05-R5.md`）：`boundary` 已升为
      **一等数据字段**（节点级，`dag.json` 的 `node.boundary`）⇒ 本函数接受显式 `boundary` 参数：
      给了就用它，未给才回退到 `split_boundary(text)`（向后兼容——组页 / 视图页的页级导语与
      其余调用点一个都不改）。⛔ 两条路径都仍是「按**显式标记**切」，⛔ 不做关键词猜测。
    """
    body, inline_boundary = split_boundary(text)
    if boundary is None:
        boundary = inline_boundary
    ss = sentences(body)
    out = []
    if ss:
        head0, items0 = split_enum(ss[0])
        out.append('<p class="claim">%s</p>' % esc(head0))
        if items0:
            out.append(enum_html("", items0))
        rest = ss[1:]
        if rest:
            lis = []
            for x in rest:
                head, items = split_enum(x)
                if items:
                    lis.append("<li>%s</li>" % (esc(head) if head else ""))
                    lis.append('<li class="points__block">%s</li>' % enum_html("", items))
                else:
                    lis.append("<li>%s</li>" % esc(x))
            out.append('<ul class="points">%s</ul>' % "".join(lis))
    if boundary:
        out.append('<div class="boundary"><p class="boundary__label">适用边界</p>'
                   '<p>%s</p></div>' % esc(boundary))
    return "\n".join(out)


def section(title, no, sid):
    """带序号与锚点的区块标题（序号使「先讲什么、再讲什么」显式可见）。"""
    return '<h2 id="%s"><span class="sec-no">%02d</span>%s</h2>' % (esc(sid), no, esc(title))


def figure_html(fid, caption="", reveal=None):
    """内联 SVG 图件（随主题切换）+ 图注 + 自制来源标注。"""
    svg = load_figures().get(fid)
    if not svg:
        return ""
    attrs = ' data-reveal="1" style="--i:%d"' % int(reveal) if reveal is not None else ""
    return ('<figure class="fig" id="fig-%s"%s>%s<figcaption>%s '
            '<span class="fig__src">（本站自制）</span></figcaption></figure>'
            % (esc(fid), attrs, svg, esc(caption)))


def read_map_html(claim, sections, reveal=None):
    """页首导读：先给一句话结论，再给可跳转的结构地图。"""
    lis = "".join('<li><a href="#%s">%02d %s</a></li>' % (esc(sid), no, esc(t))
                  for sid, t, no in sections)
    attrs = ' data-reveal="1" style="--i:%d"' % int(reveal) if reveal is not None else ""
    return ('<section class="read-map" aria-label="本页导读"%s>'
            '<p class="read-map__label">一句话结论</p>'
            '<p class="read-map__claim">%s</p>'
            '<p class="read-map__label">本页结构（可跳转）</p>'
            '<ul class="read-map__nav">%s</ul></section>' % (attrs, esc(claim), lis))


def pair_table(rows, caption=""):
    """对照表：一行一件事（类别 ｜ 场景 / 条件 ｜ 具体做法）。"""
    trs = []
    for cat, s in rows:
        summary, detail = split_pair(s)
        trs.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (esc(cat), esc(summary), esc(detail or "—")))
    return ('<div class="table-scroll"><table class="cmp-table"><caption>%s</caption>'
            "<thead><tr><th>类别</th><th>场景 / 条件（总结）</th><th>具体做法（细节）</th></tr></thead>"
            "<tbody>%s</tbody></table></div>" % (esc(caption), "".join(trs)))


def pair_list(items, cls="pitfall-list"):
    """总结 + 细节 的清单形态（失效模式用）：每点一行「总结」，其下「细节」。"""
    lis = []
    for it in items or []:
        summary, detail = split_pair(it)
        inner = '<span class="pair__sum">%s</span>' % esc(summary)
        if detail:
            inner += '<span class="pair__detail">%s</span>' % esc(detail)
        lis.append("<li>%s</li>" % inner)
    return '<ul class="tight %s pair-list">%s</ul>' % (esc(cls), "".join(lis))


def node_chip(nid, page_exists, base):
    """节点 chip（两态：已落页 ⇒ 真链接；架构在册 ⇒ 徽标）。

    ★ 从 `relchain_html` 的内联函数提取（2026-10-15，G4）：组页与视图页也要用同一种
      节点 chip，⛔ 不复制第二份渲染口径。提取后 `relchain_html` 的输出**逐字节不变**。
    """
    if nid in page_exists:
        return '<a class="gchip" href="%s">%s</a>' % (esc(base + node_page_rel(nid)), esc(nid))
    return ('<span class="gchip"><span class="nid">%s</span> '
            '<span class="badge badge--pending">架构在册</span></span>' % esc(nid))


def relchain_html(nid, prereq, successors, page_exists, base):
    """依赖链：前置 → 本节点 → 后继（一行；节点可点）。"""
    chip = node_chip
    left = "".join(chip(x, page_exists, base) for x in (prereq or [])) or '<span class="tier">无（起点）</span>'
    right = "".join(chip(x, page_exists, base) for x in (successors or [])) or '<span class="tier">无（终点）</span>'
    return ('<div class="relchain"><span class="relchain__label">前置</span>%s'
            '<span class="relchain__arrow">→</span>'
            '<span class="gchip"><span class="nid">%s</span> 本节点</span>'
            '<span class="relchain__arrow">→</span>'
            '<span class="relchain__label">后继</span>%s</div>'
            % (left, esc(nid), right))


def group_relchain_html(gid, prev_g, next_g, base):
    """组间前后继：**一行结构**（上一组 → 本组 → 下一组）。

    ★ 契约 R-05/R-06 的形态要求（2026-10-15，G4）：依赖关系要能**一眼看齐**，
      ⛔ 不用「本组的上一组是 X，下一组是 Y」这类长句罗列。本函数与 `relchain_html`
      共用同一套 `.relchain` 类（⛔ 不新增 CSS、⛔ 不新增 :hover 选择器）。
    """
    left = (group_chip(prev_g["id"], prev_g["name"], base + group_page_rel(prev_g["id"]))
            if prev_g else '<span class="tier">无（本分区起点）</span>')
    right = (group_chip(next_g["id"], next_g["name"], base + group_page_rel(next_g["id"]))
             if next_g else '<span class="tier">无（本分区终点）</span>')
    return ('<div class="relchain"><span class="relchain__label">上一组</span>%s'
            '<span class="relchain__arrow">→</span>'
            '<span class="gchip">%s<span class="gchip__name">本组</span></span>'
            '<span class="relchain__arrow">→</span>'
            '<span class="relchain__label">下一组</span>%s</div>'
            % (left, group_mark(gid), right))


def edge_line_html(dst, src, note, page_exists, base):
    """组内依赖边：**一行结构**（前置 → 本节点），理由作为次级标签随行折行。

    ⛔ 不把多条边拼成一句（原实现是「A ← B：…；A ← C：…」的 run-on 长句，
      读者要自己切分）。一条边一行 ⇒ 每行只干一件事。
    """
    tail = ('<span class="relchain__label">理由：%s</span>' % esc(note)) if note else ""
    return ('<div class="relchain"><span class="relchain__label">前置</span>%s'
            '<span class="relchain__arrow">→</span>%s%s</div>'
            % (node_chip(src, page_exists, base), node_chip(dst, page_exists, base), tail))


def node_name_link(n, page_exists, base):
    """节点中文名链接（**列表**用；英文名由所在区块的竖表承载，⛔ 不在列表行里再挤一遍）。"""
    cn, _en = split_name(n["name"], n.get("en", ""))
    if n["id"] in page_exists:
        return '<a href="%s">%s</a>' % (esc(base + node_page_rel(n["id"])), esc(cn))
    return '%s <span class="badge badge--pending">架构在册</span>' % esc(cn)


def layer_block_html(lv, ns, edges_all, page_exists, base, reveal_index=None, show_group=False):
    """一个依赖层块：层号 + 成员清单 + 每条入边的**一行结构**（前置 → 本节点 + 理由）。

    ★ 组页与学习路径页共用本函数（⛔ 不各写一份，否则两处形态会漂移）：
      · `show_group=False`（组页）：组内节点无需再标分组；
      · `show_group=True`（学习路径页）：跨组页，成员须带分组序号标记。
      · `reveal_index=None`：不挂 `data-reveal`（学习路径页的错峰单元是**章**，
        ⛔ 不让每个层块再挂一次，否则单页实例数会越过动效预算 P28 的上界）。
    ★ 无入边的节点 = 真起点 ⇒ 一行「前置：无（起点层）」，⛔ 不再用「本层节点在本组内无入边」
      这类把「真起点」与「组内无前置」混为一谈的长句。
    """
    items = []
    for n in ns:
        mark = (group_mark(n["group"]) + " ") if show_group else ""
        items.append('<li><span class="nid">%s</span> %s%s</li>'
                     % (esc(n["id"]), mark, node_name_link(n, page_exists, base)))
    lines = []
    for n in ns:
        ins = [e for e in edges_all if e["target"] == n["id"]]
        if ins:
            for e in sorted(ins, key=lambda x: x["source"]):
                lines.append(edge_line_html(n["id"], e["source"], e.get("note", ""),
                                            page_exists, base))
        else:
            lines.append('<div class="relchain"><span class="relchain__label">前置</span>'
                         '<span class="tier">无（起点层）</span>'
                         '<span class="relchain__arrow">→</span>%s</div>'
                         % node_chip(n["id"], page_exists, base))
    attrs = (' data-reveal="1" style="--i:%d"' % int(reveal_index)) if reveal_index is not None else ""
    return ('<div class="layer-block"%s>'
            '<h3>第 %d 层 · %d 个节点</h3><ul class="tight node-list">%s</ul>%s</div>'
            % (attrs, lv, len(ns), "".join(items), "".join(lines)))


def kv_blocks_html(blocks):
    """竖表（R-11）：每个 block 是 `[(字段名, 值HTML), …]`，字段纵向排列。

    ★ 值一律是**已转义好的 HTML**（可含链接/徽标），故本函数只转义字段名。
    ⛔ 长文字段（节点名、英文名、理由）不进横表：804px 内容列下必然横向滚动。
    """
    out = []
    for rows in blocks:
        cells = "".join(
            '<p class="kv-block__row"><span class="kv-block__k">%s</span>'
            '<span class="kv-block__v">%s</span></p>' % (esc(k), v) for k, v in rows)
        out.append('<article class="kv-block">%s</article>' % cells)
    return '<div class="kv-blocks">%s</div>' % "".join(out)


def lead_sentence(text):
    """散文来源的**首句**（页首导读的结论句；⛔ 与 `sentences` 同一口径，不另写正则）。"""
    ss = sentences(text)
    return ss[0] if ss else ""


def steps_html(lab):
    """实验台：编号步骤 + 代码（折叠）+ 预期观察。"""
    lis = []
    for it in lab or []:
        kind = esc(it.get("kind", ""))
        lang = esc(it.get("lang", ""))
        code = esc(it.get("text", ""))
        expect = esc(it.get("expect", ""))
        lis.append('<li><p class="meta-line"><span class="badge">%s</span><span class="tier">%s</span></p>'
                   '<details class="acc"><summary>查看代码</summary><pre><code>%s</code></pre></details>'
                   '<p class="lede">预期观察：%s</p></li>' % (kind, lang, code, expect))
    return '<ol class="steps">%s</ol>' % "".join(lis)


def ev_table_html(evs):
    """证据 → **竖表**（字段名在上、值在下，长文自动换行）。

    ★ 用户反馈 #1：*「表格设计不合格，长文字段应允许换行…尽可能不要有左右翻动的需求
      ——横表如果不能一眼看齐，那就相当于没有优势，不如转竖表」*。原 4 列横表（主张｜分级｜
      来源｜原文）在 804px 内容列里必然横向滚动 ⇒ 改为竖表：每条证据一个块，字段纵向排列。
    """
    blocks = []
    for ev in evs or []:
        trunc = ' <span class="tier">原文截断</span>' if ev.get("quote_truncated") else ""
        blocks.append(
            '<article class="kv-block">'
            '<p class="kv-block__row"><span class="kv-block__k">主张</span>'
            '<span class="kv-block__v">%s</span></p>'
            '<p class="kv-block__row"><span class="kv-block__k">分级</span>'
            '<span class="kv-block__v"><span class="tier">%s</span></span></p>'
            '<p class="kv-block__row"><span class="kv-block__k">来源</span>'
            '<span class="kv-block__v"><span class="nid">%s</span> '
            '<a href="%s" rel="noopener noreferrer">%s</a></span></p>'
            '<p class="kv-block__row"><span class="kv-block__k">原文</span>'
            '<span class="kv-block__v"><details class="acc"><summary>展开原文关键句%s</summary>'
            '<blockquote class="quote">%s</blockquote></details></span></p>'
            '</article>'
            % (esc(ev.get("claim", "")), esc(ev.get("tier", "")), esc(ev.get("source_id", "")),
               esc(ev.get("url", "")), esc(ev.get("url", "")), trunc, esc(ev.get("quote", ""))))
    return '<div class="kv-blocks">%s</div>' % "".join(blocks)


def _term_parts(t):
    """`术语（English）：界定` → (术语, English, 界定)。"""
    s = str(t)
    m = re.match(r"^(.*?)（(.+?)）\s*[:：]\s*(.*)$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    a, _sep, b = s.partition("：")
    return a.strip(), "", b.strip()


def terms_table_html(terms, glossary, base, page_exists):
    """术语 → **竖表**（术语 / 英文 / 界定 / 相关节点 逐行纵向排列）。

    ★ 同反馈 #1：界定的文本很长，横表的四列会横向滚动 ⇒ 转竖表。
    ★ 界定仍以 `glossary.json` 为**单一真相源**（P07 的断言不变）。
    """
    idx = {}
    for t in (glossary or {}).get("terms", []):
        idx[t.get("term", "")] = t
    blocks = []
    for t in terms or []:
        term, en, definition = _term_parts(t)
        g = idx.get(term) or {}
        definition = g.get("definition") or definition
        en = g.get("en") or en
        refs = []
        for r in g.get("node_refs", []) or []:
            if r in page_exists:
                refs.append('<a href="%s">%s</a>' % (esc(base + node_page_rel(r)), esc(r)))
            else:
                refs.append('<span class="nid">%s</span>' % esc(r))
        blocks.append(
            '<article class="kv-block">'
            '<p class="kv-block__row"><span class="kv-block__k">术语</span>'
            '<span class="kv-block__v"><strong>%s</strong>%s</span></p>'
            '<p class="kv-block__row"><span class="kv-block__k">界定</span>'
            '<span class="kv-block__v">%s</span></p>'
            '<p class="kv-block__row"><span class="kv-block__k">相关节点</span>'
            '<span class="kv-block__v">%s</span></p>'
            '</article>'
            % (esc(term), ('　' + esc(en)) if en else "", esc(definition), " ".join(refs) or "—"))
    return '<div class="kv-blocks">%s</div>' % "".join(blocks)


def split_name(name, en):
    """`中文名（English Name）` → (中文名, English)。

    ★ 反馈 #4 的成因：`name` 字段本身就把英文写在括号里，而页面又另渲染了 `en` 字段
      ⇒ 英文出现两次、中文与英文挤在同一行、h1 被撑成两三行。这里**只在渲染层拆分**，
      ⛔ 不动数据（`name` 的契约形态仍是「中文名（English Name）」）。
    """
    m = re.match(r"^(.*?)（(.+?)）\s*$", name or "")
    if m:
        return m.group(1).strip(), (en or m.group(2)).strip()
    return (name or "").strip(), (en or "").strip()


def base_css(base=""):
    """全站**逐字节一致**的外壳样式块（模板唯一性要求）。

    ★ 为什么资源路径写死为 `../assets/…` 而**不按页面深度参数化**（2026-10-15 修正）：
      本站**每个页面都恰好位于站点根下一层**——根入口在站点根，其余全部在 `11-node-pages/`
      `12-groups/` `13-interactive/` `14-views/` 四个子目录里，深度都是 1。于是：
        · 子目录页：`../assets/…` ⇒ `<repo>/assets/…` ✓
        · 站点根页：`../assets/…` ⇒ `<repo>/assets/…` ✓（`..` 已在根上，按 URL 语义是 no-op）
      两种页面对同一串文本解析到**同一个位置**，因此样式块可以做到逐字节一致。
      ⛔ 参数化（根页写 `assets/`、子目录页写 `../assets/`）会产出**两种样式块** ⇒ 与
        「全站唯一外壳/唯一样式块」直接冲突（本轮实测：样式块 2 种，P15 FAIL）。
      ⛔ 也不用根绝对路径 `/assets/…`：本站是 GitHub Pages **项目站**（发布在
        `<user>.github.io/<repo>/` 之下），根绝对路径会 404。
      ⚠ 已知代价（如实登记）：本形态要求站点以**站点根为文档根**提供（本地预览需起一个静态服务器，
        `python3 -m http.server` 即可）。⛔ 直接以 `file://` 打开单个 HTML 时背景素材取不到——
        这与「发布级站点」的实际用法一致，且 v1 的 `../` 相对链接同样不支持 `file://` 浏览。
    """
    return BASE_CSS.replace("@@ASSETDIR@@", "../assets/")


# ---------------------------------------------------------------- 脚本（全站逐字节一致）

SCRIPT_MARK = "/* ui-bootstrap v2 */"


def theme_script():
    """全站唯一引导脚本：主题三态 pre-paint ＋ 动效三态 ＋ 无 JS 兜底双保险。

    ★ 依据 H1 §2.3 / §6.3 / §6.4：
      - 主题：读 `localStorage['ui-theme']`，`light`/`dark` 落属性，其余（跟随系统）
        **移除属性**；切换只改属性，⛔ 不接管 `color-scheme`（避免双真相源）。
      - 动效：`on` **必须落属性**（否则在 OS 开了 reduce 的机器上被静默压掉）；
        `system` 与 `off` 的区分在于 `off` 落属性、`system` 不落。
      - 无 JS 兜底双保险：① 隐藏态挂在 `html.js-motion` 之下（无 JS ⇒ 默认可见）；
        ② 1800ms 一次性定时器，未落 `data-motion-ready` 就把全部 [data-reveal] 置终态。
    """
    return (
        "<script>" + SCRIPT_MARK + "\n"
        "(function(){var K=\"ui-theme\",M=\"ui-motion\",B=\"ui-backdrop\",F=\"ui-fontsize\","
        "R=document.documentElement;"
        "function ap(t){if(t===\"light\"||t===\"dark\"){R.setAttribute(\"data-theme\",t);}"
        "else{R.removeAttribute(\"data-theme\");}"
        "var bs=document.querySelectorAll(\"[data-theme-set]\");"
        "for(var i=0;i<bs.length;i++){bs[i].setAttribute(\"aria-pressed\","
        "String(bs[i].getAttribute(\"data-theme-set\")===t));}}"
        "function am(v){if(v===\"on\"||v===\"off\"){R.setAttribute(\"data-motion\",v);}"
        "else{R.removeAttribute(\"data-motion\");}"
        "var bs=document.querySelectorAll(\"[data-motion-set]\");"
        "for(var i=0;i<bs.length;i++){bs[i].setAttribute(\"aria-pressed\","
        "String(bs[i].getAttribute(\"data-motion-set\")===v));}}"
        # ★ 背景素材开关（2026-10-15 用户反馈轮新增）：off **落属性**、on **不落属性**
        #   （默认即开 ⇒ 与主题的「跟随系统不落属性」同规：默认态不留属性、不留 localStorage 键）。
        "function ab(v){if(v===\"off\"){R.setAttribute(\"data-backdrop\",\"off\");}"
        "else{R.removeAttribute(\"data-backdrop\");}"
        "var bs=document.querySelectorAll(\"[data-backdrop-set]\");"
        "for(var i=0;i<bs.length;i++){bs[i].setAttribute(\"aria-pressed\","
        "String(bs[i].getAttribute(\"data-backdrop-set\")===v));}}"
        # ★ 正文字号开关（同上）：large 落属性、standard 不落属性。
        "function af(v){if(v===\"large\"){R.setAttribute(\"data-fontsize\",\"large\");}"
        "else{R.removeAttribute(\"data-fontsize\");}"
        "var bs=document.querySelectorAll(\"[data-fontsize-set]\");"
        "for(var i=0;i<bs.length;i++){bs[i].setAttribute(\"aria-pressed\","
        "String(bs[i].getAttribute(\"data-fontsize-set\")===v));}}"
        "var t=\"system\",v=\"system\",bk=\"on\",fz=\"standard\";"
        "try{t=localStorage.getItem(K)||\"system\";v=localStorage.getItem(M)||\"system\";"
        "bk=localStorage.getItem(B)||\"on\";fz=localStorage.getItem(F)||\"standard\";}catch(e){}"
        "if(t!==\"light\"&&t!==\"dark\"){t=\"system\";}"
        "if(v!==\"on\"&&v!==\"off\"){v=\"system\";}"
        "if(bk!==\"on\"&&bk!==\"off\"){bk=\"on\";}"
        "if(fz!==\"standard\"&&fz!==\"large\"){fz=\"standard\";}"
        "ap(t);am(v);ab(bk);af(fz);"
        "R.className+=(R.className?\" \":\"\")+\"js-motion\";"
        "function fin(){var els=document.querySelectorAll(\"[data-reveal]\");"
        "for(var i=0;i<els.length;i++){els[i].className+=\" is-in\";}}"
        "function ready(){R.setAttribute(\"data-motion-ready\",\"1\");"
        "if(!(\"IntersectionObserver\" in window)){fin();return;}"
        "var io=new IntersectionObserver(function(es){for(var i=0;i<es.length;i++){"
        "if(es[i].isIntersecting){es[i].target.className+=\" is-in\";io.unobserve(es[i].target);}}},"
        "{rootMargin:\"0px 0px -8% 0px\"});"
        "var els=document.querySelectorAll(\"[data-reveal]\");"
        "for(var i=0;i<els.length;i++){io.observe(els[i]);}}"
        "function boot(){"
        "var els=document.querySelectorAll(\"[data-reveal]\");"
        "for(var i=0;i<els.length;i++){els[i].style.setProperty(\"--i\",String(i));}"
        "if(v===\"off\"){R.setAttribute(\"data-motion-ready\",\"1\");return;}"
        "try{ready();}catch(e){fin();}}"
        "if(document.readyState===\"loading\"){"
        "document.addEventListener(\"DOMContentLoaded\",boot);}else{boot();}"
        "setTimeout(function(){if(!R.getAttribute(\"data-motion-ready\")){fin();}},1800);"
        "document.addEventListener(\"click\",function(e){"
        "var n=e.target;while(n&&n!==document.body&&!n.getAttribute){n=n.parentNode;}"
        "if(!n||!n.getAttribute){return;}"
        "var ts=n.getAttribute(\"data-theme-set\"),ms=n.getAttribute(\"data-motion-set\"),"
        "bs=n.getAttribute(\"data-backdrop-set\"),fs=n.getAttribute(\"data-fontsize-set\");"
        "if(!ts&&!ms&&!bs&&!fs){return;}e.preventDefault();"
        "if(ts){try{if(ts===\"system\"){localStorage.removeItem(K);}else{localStorage.setItem(K,ts);}}"
        "catch(err){}ap(ts);}"
        "if(ms){try{if(ms===\"system\"){localStorage.removeItem(M);}else{localStorage.setItem(M,ms);}}"
        "catch(err2){}am(ms);}"
        "if(bs){try{if(bs===\"on\"){localStorage.removeItem(B);}else{localStorage.setItem(B,bs);}}"
        "catch(err3){}ab(bs);}"
        "if(fs){try{if(fs===\"standard\"){localStorage.removeItem(F);}"
        "else{localStorage.setItem(F,fs);}}catch(err4){}af(fs);}});})();</script>"
    )


# ---------------------------------------------------------------- 背景层与页脚署名

def backdrop_html():
    """背景层：容器 fixed + 负 z-index + pointer-events:none + aria-hidden。

    ★ 子树内 ⛔ 不得有任何可聚焦元素（门控 P27 断言）。
    DOM 顺序即堆叠顺序：照片 → 纱幕 → 局部 scrim。
    """
    return (
        '<div class="backdrop" aria-hidden="true">'
        '<div class="backdrop__photo backdrop__photo--day"></div>'
        '<div class="backdrop__photo backdrop__photo--night"></div>'
        '<div class="backdrop__veil backdrop__veil--day"></div>'
        '<div class="backdrop__veil backdrop__veil--night"></div>'
        '<div class="backdrop__scrim"></div>'
        '</div>'
    )


def credits_html(base):
    """页脚许可署名：独占一行的 .footer__credits，逐素材给出名称/作者/许可/链接。

    ★ CC BY 4.0 素材**须署名**；CC0 1.0 不要求署名但本站仍登记出处。
    登记表与 `assets/backdrop/` 的实际文件集由门控 P30/P32 双向断言。
    """
    by_src = {}
    for fn, c in sorted(BACKDROP_CREDITS.items()):
        by_src.setdefault((c["name"], c["author"], c["license"], c["url"]), []).append(fn)
    items = []
    for (name, author, license_, url), files in sorted(by_src.items()):
        items.append(
            '<li><span class="credits__name">%s</span> · <span class="credits__author">%s</span> · '
            '<span class="credits__license">%s</span> · '
            '<a href="%s" rel="noopener noreferrer">%s</a> '
            '<span class="credits__files">（本站副本：%s）</span></li>'
            % (esc(name), esc(author), esc(license_), esc(url), esc(url),
               esc("、".join(files))))
    ledger = "、".join("%s（%s）" % (fn, c["note"]) for fn, c in sorted(BACKDROP_LEDGER.items()))
    return (
        '<div class="footer__credits">'
        '<h2>背景素材与许可</h2>'
        '<p>本页背景为真实摄影素材（非自绘）。夜间帧取自 ESO 公开影像，'
        '许可 CC BY 4.0，须署名；日间帧取自 Wikimedia Commons 收录的 Unsplash 作品，'
        '许可 CC0 1.0，不要求署名。素材按视口宽度与像素密度分档加载，'
        '仅当前主题的帧被渲染。许可台账随素材同目录存放：%s</p>'
        '<ul class="credits">%s</ul>'
        '</div>' % (esc(ledger), "".join(items))
    )


# ---------------------------------------------------------------- 唯一外壳

def _switch_html():
    """四枚显示偏好开关（★ 2026-10-15 用户反馈轮：由 2 枚扩为 4 枚）。

    ① 主题（三态）② 动效（三态）③ 背景素材（开 / 关）④ 正文字号（标准 / 大）。
    ★ 可见文本**一律加类型前缀**——四组开关在顶部导航里相邻，默认态文本不得逐字相同。
    ★ 同一份标记在站内有**两个副本**：顶部导航（<1180px，包在 `<details>` 折叠里）与左栏
      rail（≥1180px）。两者由 display:none 互斥 ⇒ 任一宽度档下可见实例恰 1 组。
    """
    return (
        '<div class="switches">'
        '<div class="switch" role="group" aria-label="配色主题">'
        '<span class="switch__legend" aria-hidden="true">主题</span>'
        '<button type="button" class="switch__btn" data-theme-set="system" aria-pressed="true">主题：跟随系统</button>'
        '<button type="button" class="switch__btn" data-theme-set="light" aria-pressed="false">主题：浅色</button>'
        '<button type="button" class="switch__btn" data-theme-set="dark" aria-pressed="false">主题：深色</button>'
        '</div>'
        '<div class="switch" role="group" aria-label="动效偏好">'
        '<span class="switch__legend" aria-hidden="true">动效</span>'
        '<button type="button" class="switch__btn" data-motion-set="system" aria-pressed="true">动效：跟随系统</button>'
        '<button type="button" class="switch__btn" data-motion-set="on" aria-pressed="false">动效：开</button>'
        '<button type="button" class="switch__btn" data-motion-set="off" aria-pressed="false">动效：关</button>'
        '</div>'
        '<div class="switch" role="group" aria-label="背景素材">'
        '<span class="switch__legend" aria-hidden="true">背景</span>'
        '<button type="button" class="switch__btn" data-backdrop-set="on" aria-pressed="true">背景：开</button>'
        '<button type="button" class="switch__btn" data-backdrop-set="off" aria-pressed="false">背景：关</button>'
        '</div>'
        '<div class="switch" role="group" aria-label="正文字号">'
        '<span class="switch__legend" aria-hidden="true">字号</span>'
        '<button type="button" class="switch__btn" data-fontsize-set="standard" aria-pressed="true">字号：标准</button>'
        '<button type="button" class="switch__btn" data-fontsize-set="large" aria-pressed="false">字号：大</button>'
        '</div>'
        '</div>'
    )


def _nav_html(base, nav_extra=()):
    """顶部导航（<1180px 形态）。"""
    items = []
    for href, label in NAV_ITEMS:
        if href == "index.html":
            continue
        items.append('<a class="nav__link" href="%s">%s</a>' % (esc(base + href), esc(label)))
    for href, label in nav_extra:
        items.append('<a class="nav__link" href="%s">%s</a>' % (esc(href), esc(label)))
    return '<nav class="nav" aria-label="站内导航">%s</nav>' % "".join(items)


def _rail_html(base, page_id, nav_extra=()):
    """左栏 rail（≥1180px 形态）。承载与顶部导航**同一组路由** ＋ **同一组显示开关**，
    二选一不叠加（<1180 顶部导航可见、rail 隐藏；≥1180 反之）。

    ★ 形态调整（2026-10-15，用户反馈 #2）：侧栏改为「导航在上 / 显示设置锚底」两段，
      并把主题与动效开关一并搬进来——此前 ≥1180 档 `.site-head{display:none}` 会把
      开关一起藏掉，宽屏用户**没有任何切换主题/动效的入口**（本轮实测的既有缺陷）。
      ⛔ 开关不是路由：与「同一组路由不得出现两处可交互实例」不冲突——两处副本由
      display:none 互斥，任一宽度档下可见实例恰 1 组（由门控 P34 断言）。
    """
    items = []
    home_cur = ' aria-current="page"' if page_id == "ROOT" else ""
    items.append('<li><a class="rail__link" href="%s"%s>首页</a></li>'
                 % (esc(base + "index.html"), home_cur))
    for href, label in NAV_ITEMS:
        if href == "index.html":
            continue
        cur = ' aria-current="page"' if page_id == _page_id_of(href) else ""
        items.append('<li><a class="rail__link" href="%s"%s>%s</a></li>'
                     % (esc(base + href), cur, esc(label)))
    for href, label in nav_extra:
        items.append('<li><a class="rail__link" href="%s">%s</a></li>' % (esc(href), esc(label)))
    return ('<aside class="rail" aria-label="站点侧栏：站内导航与显示设置（宽屏形态）">'
            '<div class="rail__in">'
            '<p class="rail__title">站内导航</p><ul class="rail__list">%s</ul>'
            '<div class="rail__foot"><p class="rail__title">显示设置</p>%s</div>'
            '</div></aside>' % ("".join(items), _switch_html()))


def _page_id_of(href):
    """导航 href → 承载它的页面标识（供 rail 标注当前页）。"""
    m = re.match(r"^(?:%s|%s|%s)/([^/]+)\.html$" % (DIR_INTERACTIVE, DIR_VIEWS, DIR_GROUPS), href)
    if not m:
        return href
    return "INTERACTIVE" if href.startswith(DIR_INTERACTIVE) else m.group(1)


def page_shell(base, kind, page_id, title, body, head_extra="", nav_extra=(), backdrop=True):
    """★ 全站唯一外壳函数。

    base      —— 本页相对本站根的路径前缀（"../" 或 ""）
    kind      —— 页面类型标识（node / group / view / root / interactive）
    page_id   —— 页面标识（写入 body 的 data-page-id，便于门控定位）
    title     —— <title> 与页头标题
    body      —— <main> 内的正文 HTML
    head_extra—— 追加进 <head> 的片段（仅交互入口用于同目录 vendor 脚本）
    nav_extra —— 追加到页眉导航的条目
    backdrop  —— 是否渲染背景层（全站一致开启；留参数以便未来按页裁剪）
    """
    root_href = (base + "index.html") if base else "index.html"
    rail = _rail_html(base, page_id, nav_extra)
    return "".join([
        "<!DOCTYPE html>\n",
        '<html lang="zh-CN" data-theme="auto">\n',
        "<head>\n",
        '<meta charset="utf-8">\n',
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
        "<title>%s · %s</title>\n" % (esc(title), esc(SITE_TITLE)),
        "<!-- base: %s (相对本站根) -->\n" % esc(base if base else "./"),
        "<!-- template: %s -->\n" % TEMPLATE_ID,
        # ★ theme-color 两条 meta 按媒体查询分档，值必须与 --surface-page 的浅/深值同步
        '<meta name="theme-color" content="%s" media="(prefers-color-scheme: light)">\n'
        % esc(palette_css_value("surface.page", "light")),
        '<meta name="theme-color" content="%s" media="(prefers-color-scheme: dark)">\n'
        % esc(palette_css_value("surface.page", "dark")),
        '<link rel="icon" type="image/svg+xml" href="%s">\n' % esc(base + DIR_ASSETS + "/favicon.svg"),
        # ★ pre-paint 引导脚本：必须在 <head> 内、先于任何样式表与可视内容
        theme_script(), "\n",
        "<style>\n", tokens_css(), "\n", base_css(base), "</style>\n",
        head_extra,
        "</head>\n",
        '<body class="page-%s" data-page-kind="%s" data-page-id="%s">\n'
        % (esc(kind), esc(kind), esc(page_id)),
        '<a class="skip" href="#main">跳到正文</a>\n',
        backdrop_html() + "\n",
        '<header class="site-head"><div class="wrap head-in">\n',
        '<a class="brand" href="%s">%s<span>%s</span></a>\n'
        % (esc(root_href), esc(SITE_TITLE), esc(SITE_TAGLINE)),
        _nav_html(base, nav_extra), "\n",
        # ★ 窄屏档（<1180）的显示开关收进原生 <details> 折叠件（2026-10-15 用户反馈轮）：
        #   四组共 10 枚开关横排会把 sticky 头部撑成三四行；折叠后头部只多一枚 44px 的钮。
        #   ≥1180 档整个 .site-head 被 display:none，开关改由左栏 rail 承载。
        '<details class="settings"><summary class="settings__summary">显示设置</summary>',
        _switch_html(), "</details>\n",
        "</div></header>\n",
        '<div class="layout">\n', rail, "\n",
        '<main id="main">\n', body, "\n</main>\n",
        # ★ 页脚移入 .layout 之内（2026-10-15，用户反馈 #2 的补全）：页脚若留在 .layout 之外，
        #   宽屏左栏只覆盖到正文底、页脚旁边仍是空档 ⇒ 与「侧栏占满整个竖直空间」相抵。
        #   ≥1180 档：rail 跨第 1–2 行、页脚 grid-column:1 / -1 独占第 2 行（见 BASE_CSS）。
        '<footer class="site-foot"><div class="wrap">\n',
        "<p>本站为原型产物：结构由生成器统一产出，内容按两态登记（已写满 / 架构在册）。"
        "读者锚点：%s。</p>\n" % esc(SITE_TAGLINE),
        '<p class="footer__nav"><a href="%s">回到首页</a> · <a href="%s">交互全景图</a> · '
        '<a href="%s">学习路径</a></p>\n'
        % (esc(root_href), esc(base + DIR_INTERACTIVE + "/index.html"),
           esc(base + DIR_VIEWS + "/01-learning-path.html")),
        credits_html(base), "\n",
        "</div></footer>\n",
        "</div>\n",
        "</body>\n</html>\n",
    ])


def crumbs(base, items):
    """items: [(label, href|None)]；href 相对本站根。"""
    lis = []
    for label, href in items:
        if href:
            lis.append('<li><a href="%s">%s</a></li>' % (esc(base + href), esc(label)))
        else:
            lis.append('<li aria-current="page">%s</li>' % esc(label))
    return '<nav class="crumbs" aria-label="面包屑"><ol>%s</ol></nav>' % "".join(lis)


def card(inner, reveal_index=None, flat=False, links=None):
    """卡片四件套的唯一构造入口（★ 拉伸层成对：卡内其它真链接须置于 .card__links）。

    inner        —— 卡片内容 HTML；其中**必须**恰有 1 个 `.card__title-link`
    reveal_index —— 非 None 时挂 `data-reveal` 与 `--i`（错峰序号）
    links        —— 卡内其它真链接的 HTML（会被抬升到 z-index:2）
    """
    attrs = []
    if reveal_index is not None:
        attrs.append('data-reveal="1" style="--i:%d"' % int(reveal_index))
    cls = "card card--flat" if flat else "card"
    links_html = ('<p class="card__links">%s</p>' % links) if links else ""
    return '<section class="%s"%s>%s%s</section>' % (
        cls, (" " + " ".join(attrs)) if attrs else "", inner, links_html)


def reveal_seq():
    """错峰序号分配器（每页独立，从 0 起）。"""
    n = [0]

    def nxt():
        v = n[0]
        n[0] += 1
        return v
    return nxt


def head_nav_footer_note():
    return ""
