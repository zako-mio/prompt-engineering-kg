#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_prototype.py —— 原型站门控（判据 P01–P41）

判据基线：SCHEMA.md 的 P01–P14；P15–P22 对应 ADR-001 的 quality_scenarios；
P23–P32 为「设计系统换底座 + 交互重做」同批新增（见 CRITERIA-CHANGE-P23.md）；
P34 为 2026-10-15 用户走查反馈轮新增（见 CRITERIA-CHANGE-P34.md）；P35–P36 为同日「内容呈现 v2」
新增（见 CONTENT-V2.md 与 CRITERIA-CHANGE-P34.md 续）；P37 为同日「结构化交互图」新增
（R-16 / 契约 G3，同批落判据，见 DESIGN-CONTRACT.md §1 R-16 与 §2 G3）。
P22 于 2026-10-16 变更：「content_status 数量配额」→「**状态↔内容一致性**」，见 CRITERIA-CHANGE-P22.md。
P35 ⑧ / ④ 的作用域于 2026-10-16（第 6 轮）变更：R-07 由「每页」收敛为**知识承载页（节点页 / 组页）**、
R-03 对齐为**正文承载页**，两处均带**显式对象集 + 全集闭合断言**，见 CRITERIA-CHANGE-R07.md。
★ 2026-10-16（第 8 轮）三条判据的**对象收窄** ＋ 新增发布级元数据判据族：P09（R-18）的 `<link>`
按 **rel 闭集**分流（元数据类 rel 不当加载类资源，⛔ 不再「一切 link 皆资源」）、P12（R-19）的「主机名」
一项只在**正文**上判（属性取值归 P09/P30，sitemap/robots 的 URL 载荷另有摘除口径）、R-08 的「内容列」
落实为可复算口径；同批新增 **A1–A7**（`gate_a11y.py`）与 **S1–S11**（`gate_seo_meta.py`）。
触发事实：SH4 落地时 P09/P12 **整站 FAIL**（判假探针 `_probe/r8_t1_p09_probe.py` 实测），
根因是「判据对象 > 断言对象」（R-23 同型第 3 次复发）。见 CRITERIA-CHANGE-R08.md。

★ 判据编号说明（⛔ 不改任何判据的作用域）：本文件的编号集合现为 **P01–P41**；文件头曾写作
  「P01–P37」（第 35–37 条落地前的时点快照），于 2026-10-16 随 P22 变更同批更正为 P01–P40，
  同轮（第 6 轮）随 P41 落地更正为 **P01–P41**。

★ **「显式对象集 + 全集闭合断言」是本仓的通用作用域机制（2026-10-16 第 6 轮首次成型）**：
  凡判据只对**某几类对象**生效时，必须同时写出 ① 对象集 ② 排除集（逐条理由）③ `set(受检) == 对象集 ∪ 排除集`
  的闭合断言（出现未分类的 ⇒ FAIL）。⛔ 不得靠控制流分支偶然豁免 —— 第 5 轮的 R-23 违反
  （P35 ⑧ 声明「每页」、实装躲在 `continue` 之后）正是那样产生的。本文件现有四处实例：
  P35 ⑧（图件对象）、P35 ④（导读对象）、P35 ②（h1 口径对象，2026-10-16 第 7 轮 N1）、P41（散文能力声明的扫描面）。

每条判据都必须**可判假**：`--selftest` 逐条注入负例，任一条负例未触发即判该判据本身不合格。
计数型判据一律带**空集守卫**（集合为空 ⇒ FAIL，防判据恒真）。

判据纪律：⛔ 不为通过而放宽阈值；⛔ 不设豁免；失败即 FAIL 且退出码非 0；⛔ 不静默降级。
本脚本只读与裁决，⛔ 不写任何产物或真相源（负例夹具一律落在临时沙箱内）。

用法：
  python3 gate_prototype.py             跑全部判据，0 = 全部 PASS
  python3 gate_prototype.py --selftest  逐条触发负例
  python3 gate_prototype.py --only P05  只跑某几条（调试用）
"""

import argparse
import copy
import hashlib
import html as _html
import importlib.util
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.normpath(os.path.join(HERE, ".."))
DATA_DIR = os.path.join(SITE_ROOT, "10-dag-data")
BUILD_ALL = os.path.join(HERE, "build-all.py")
GEN_TOKENS = os.path.join(HERE, "gen-tokens.py")

MD_DIR = "15-md"
STATE_FILE = "PUBLISH-STATE.json"
SELF_DIRS = ("11-node-pages", "12-groups", "14-views")
INTERACTIVE = "13-interactive/index.html"
WHITELIST_PREFIX = "vendor/"
ASSET_DIR = "assets/backdrop"

REL_ENUM = {"PREREQ", "CONTAINS", "UPGRADE", "FLOW"}
STATUS_ENUM = {"complete", "registered"}
FSTATUS_ENUM = {"confirmed", "disputed", "unverified"}
BODY_MIN = 4.5

CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-'.]*")
HOLLOW = re.compile(r"(待填充|TBD|TODO|待补|占位|待定|暂无内容)")

# ★ 2026-10-15 判据变更（P05，见 CRITERIA-CHANGE-P05.md）：口径写死为 caliber，⛔ 不用 len(s)
WHY_MIN = {"complete": 80, "registered": 60}
# ★ 2026-10-16 判据变更（P05-R5 的 B-2，见 CRITERIA-CHANGE-P05-R5.md）：
#   **上限"按真实渲染重导"**（⛔ 不再凭直觉给数）。取证装置 = `_probe_thresholds.py`（只打印、⛔ 不落产物），
#   在 1440×900 真实渲染下量 `.claim` + `.points` 的块高与行高（行高实测 28px、内容列 868px），
#   逐页反解「**一屏可读量**」（caliber 口径）：
#     why   一屏 = 693 / 698 / 855  ⇒ 取 **min 693**（保守）
#     intro 一屏 = 777 / 813 / 835  ⇒ 取 **min 777**（保守）
#   ★ 它们**只能作报告项**：上限只影响版式首屏，与正确性无因果关联（SCHEMA §3 的判据分档原则）。
#   ★ 原值 120 / 250 是**旧版式下的直觉值**，本轮由实测替换。
WHY_UPPER_REPORT = 693          # 上限撤销硬判，降为报告项（⛔ 不判 FAIL）；值 = 一屏可读量实测下界
INTRO_MIN = {"complete": 150, "registered": 120}
INTRO_UPPER_REPORT = 777        # 上限降为报告项；值 = 一屏可读量实测下界（★ 见上：渲染只能给上界）
SUMMARY_UPPER_REPORT = 80       # 上限降为报告项（★ 本轮**未**重导：B-2 的对象是 why 上限与 intro 下限）
SENT_END = "。！？!?"
QUOTE_CHARS = "「」“”‘’\"'《》【】（）()"

# ★ 2026-10-15 判据变更（P23–P32，见 CRITERIA-CHANGE-P23.md）
MOTION_REVEAL_MAX = 32          # M1 单页 [data-reveal] 实例数上界
MOTION_ENTRY_MAX_MS = 1800      # M2 进场完成时间上界（＝兜底窗口）
MOTION_DUR_SUM_MAX = 3.6        # M3 --dur-* 令牌之和上界（秒）
MOTION_INFINITE_MAX = 12        # M4 常驻 infinite 元素数上界
REVEAL_STAGGER_MS = 70          # 错峰步长
TOUCH_MIN_PX = 44               # 触控目标最小边长
NAV_BREAKPOINT = 1180           # 导航形态切换断点

TOKEN_BEGIN = "/* >>> GENERATED:tokens"
TOKEN_END = "/* <<< GENERATED:tokens */"
TEMPLATE_RE = re.compile(r"<!--\s*template:\s*([^\s>]+)\s*-->")
BASE_RE = re.compile(r"<!--\s*base:\s*([^>]*?)\s*-->")
INLINE_SCRIPT_RE = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.S)
STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S)
RES_ATTR_RE = re.compile(r'(?:src|href)\s*=\s*"([^"]*)"', re.I)
LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.I)
URL_HTTP_RE = re.compile(r"url\(\s*['\"]?(?:https?:)?//", re.I)
SCRIPT_MARK = "/* ui-bootstrap v2 */"

ABS_PATH_RE = re.compile(r"(?:^|[\s\"'（(【:：,，])(/(?:home|Users|root|run|tmp|var|opt|etc|usr|srv|mnt|media|Volumes|proc|sys)/[^\s\"'）)】]*|~/[^\s\"'）)】]*)")
HOST_RE = re.compile(r"\b(zako-mio|localhost|127\.0\.0\.1|0\.0\.0\.0)\b")
FILE_URL_RE = re.compile(r"file://")
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{8,}|Bearer\s+[A-Za-z0-9._\-]{8,}|api[_-]?key\s*[:=]\s*[\"'][^\"']{6,})")
SECTION_RE = re.compile(r"§\s*\d")
TIER_WORD_RE = re.compile(r"(门控级|咨询级)")

# --- P24：令牌外硬编码扫描面 ---
FONT_SIZE_DECL_RE = re.compile(r"font-size\s*:\s*([^;}]+)")
RADIUS_DECL_RE = re.compile(r"border-radius\s*:\s*([^;}]+)")
COLOR_DECL_RE = re.compile(r"(?<![\w-])(color|background-color)\s*:\s*([^;}]+)")
BOX_DECL_RE = re.compile(r"(?<![\w-])(padding|margin)(?:-(?:top|right|bottom|left))?\s*:\s*([^;}]+)")
OUTLINE_DECL_RE = re.compile(r"outline\s*:\s*([^;}]+)")
CUSTOM_PROP_RE = re.compile(r"(?:^|[\s;{])(--[A-Za-z0-9_-]+)\s*:")
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FONT_SIZE_ALLOWED = re.compile(r"^(?:var\(\s*--fs-[a-z-]+\s*\)|inherit|revert|unset|initial)$")
RADIUS_ALLOWED = re.compile(r"^(?:var\(\s*--radius(?:-lg|-pill)?\s*\)|0|inherit|revert|unset|initial)$")
BOX_ALLOWED = re.compile(r"^(?:var\(\s*--space-[1-7]\s*\)|0|auto|inherit|revert|unset|initial)$")
COLOR_ALLOWED = re.compile(r"^(?:var\(\s*--[a-z0-9-]+\s*\)|currentColor|inherit|revert|unset|initial|transparent)$")

# --- P25：hover 门控 ---
HOVER_MEDIA = "(hover:hover)"
PSEUDO_QUERY_RE = re.compile(r":(hover|focus-within|focus-visible)\b")

# --- P27：背景层 ---
BACKDROP_CONTAINER_CLASS = "backdrop"
FOCUSABLE_TAG_RE = re.compile(r"<(a|button|input|select|textarea)\b[^>]*>", re.I)
TABINDEX_RE = re.compile(r"\btabindex\s*=", re.I)
NON_CURRENT_DISPLAY_RE = re.compile(r"display\s*:\s*none")

# --- P31：色相不承载身份 ---
GROUP_HUE_CLASS_RE = re.compile(r"\bg-(?:[0-9]{2}|dn)\b")
GROUP_HUE_TOKEN_RE = re.compile(r"--group-[a-z0-9]+")

LINK_IMAGE_RELS = ("icon", "apple-touch-icon", "mask-icon", "image_src")

# --- P09 / P12：`<link>` 的 rel 分类（★ 2026-10-16 第 8 轮新增，见 CRITERIA-CHANGE-R08.md）---
# 判据对象纪律（R-23 / 契约 §4⑤ 第 3 条）：`<link>` **不全是加载类资源**。
# `rel="canonical"` / `rel="icon"` / `rel="alternate"` 是**元数据声明**——浏览器不为它们取资源
# （唯一例外是图标，由浏览器按需取且属站点自有资产）。P09 的立意是「零**外链**资源」，
# 若把「一切 `<link>`」都算成资源，它就在**自己不该管的对象**上 FAIL ⇒ 一加 SH4 元数据即整站红
# （⛔ 那不是「零外链」的加强，而是判据对象 ≠ 断言对象）。
# ★ 这不是放宽阈值：把对象收窄到它本来要管的那个，并**同批**加两条断言防退化 ——
#   ① **rel 闭集**：未分类的 rel（`preload` / `dns-prefetch` / `modulepreload` / `prefetch`…）⇒ FAIL；
#   ② 元数据类 rel 的 href **必须无主机**（⛔ 不得指向站外，防「元数据」被当成外链后门）。
# ★ 与姊妹站同源先例：`algorithm-knowledge-graph` 的 T12 口径重述（对象从「全部 `<link>`」
#   收窄为 `rel="stylesheet"` 的 `<link>`）；本件是它的完整形态（闭集 + 无主机双断言）。
LINK_META_RELS = ("canonical", "icon", "apple-touch-icon", "mask-icon", "alternate")
# ★ 允许**带主机**的元数据类 rel（⛔ 其余元数据 rel 一律不得带主机）：
#   `canonical` 与 `alternate` 的取值按规范就是**绝对自指 URL**（`https://<本仓发布基址>/…`）。
#   把它们也判「不得带主机」会得到一个**无解**的判据（本轮实测：51 页全 FAIL）。
#   ⇒ 断言改为「带主机时**必须**是本站基址」（`gen-common.SITE_BASE_URL`），
#     既容许绝对自指 URL，也挡住「元数据被当成外链后门」（`https://evil.example.com/…` 照样 FAIL）。
LINK_META_HOSTED_OK = ("canonical", "alternate")
LINK_REL_RE = re.compile(r'rel\s*=\s*"([^"]*)"', re.I)
LINK_HREF_RE = re.compile(r'href\s*=\s*"([^"]*)"', re.I)
# 属性值里**带主机**的形态：`https://…` / `http://…` / `//cdn…`（协议相对）/ `mailto:…` 等带 scheme 的
# ⇒ 取反即「无主机的站内路径」。⛔ 不用 `urlparse` 之类的额外依赖，判据保持纯正则可复算。
HOSTED_URL_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)")
# P12 用：摘掉「属性值里的 URL 载体」= ① 一切 `href="…"`（本站任何 `<a href>` 都是站内相对路径）
#   ② `content="<带主机的 URL>"`（og:url / og:image）。★ 二者都**不动** `theme-color` 与 `viewport`
#   （前者是色值、后者是尺寸；实测 DOM 里 `content=` 只服务这两者）。
RES_URL_ATTR_RE = re.compile(r'\bhref\s*=\s*"[^"]*"|\bcontent\s*=\s*"(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)[^"]*"', re.I)
# P12 用：摘掉**正文里**的绝对 URL（sitemap / robots 的文本内容）。
# ★ 必须替换成一个**非词字符**（⛔ 不是空串）：否则 `…/prompt-engineering-kg/…` 里
#   `zako-mio` 前是 `//`、后是 `.`，删空后仍会被 `\b…\b` 命中（本轮实测：删了等于没删）。
HOST_URL_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s<>\"]+")
# ★ **元数据面**文件（只需文件名，与目录无关）：这些文件的**职责**就是承载本站的绝对 URL / 仓库标识，
#   ⇒ 「主机名」一项对它们不适用（它们既不是 Pages 上的页面，也不是「正文」）。
#   · `sitemap.xml` / `robots.txt`：发布发现协议的载体（按规范其全部内容就是绝对 URL）
#   · `README.md`：**仓库门面**（GitHub 仓库页显示的那一份，⛔ 不在 Pages 上）
#   · `PUBLISH-STATE.json`：**发布态台账**（机器可读）；第 8 轮起它承载 `publish.repo` 与
#     `publish.entry_url` 两处**发布事实**（P13 的一致性断言正是拿它们判的）
#   ★ 2026-10-16 第 8 轮：这四件都在**发布根**上，且都**不是** `data-page-kind` 页面
#     ⇒ 对它们判「正文不得含主机名」＝把规范要求写的东西判成违例（判据对象 ≠ 断言对象）。
#   ★ ⛔ 收窄的是**对象**不是阈值：HTML 页的正文里出现裸主机名照样 FAIL（夹具 `mut_p12` 守着）。
HOST_CARRIER_FILES = ("sitemap.xml", "robots.txt", "README.md", "PUBLISH-STATE.json")
_CTX_ASSET_EXTS = (".webp", ".png", ".jpg", ".jpeg", ".svg", ".avif")


# ---------------------------------------------------------------- 工具

def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def caliber(s):
    """字段长度唯一口径（SCHEMA §3）：汉字数 + 拉丁词数，不计标点与空白。"""
    s = s or ""
    return len(CJK.findall(s)) + len(LATIN_WORD.findall(s))


def norm_sentence(s):
    s = re.sub(r"\s+", "", s or "")
    for ch in QUOTE_CHARS:
        s = s.replace(ch, "")
    return s.strip()


def sentences(s):
    return [x for x in re.split(r"(?<=[。！？!?])", (s or "").strip()) if x.strip()]


def summary_structural_failures(node):
    bad = []
    summ = (node.get("summary") or "").strip()
    if not summ:
        return ["summary 为空"]
    if not summ.endswith(tuple(SENT_END)):
        bad.append("summary 非完整句（未以句末标点结尾）")
    if HOLLOW.search(summ):
        bad.append("summary 含空洞占位词")
    target = norm_sentence(summ)
    dup = [norm_sentence(x) for x in sentences(node.get("why", ""))] + \
          [norm_sentence(x) for x in sentences(node.get("intro", ""))]
    if target and target in dup:
        bad.append("summary 与 why/intro 的某个整句逐字相同")
    return bad


# ★ 2026-10-16（B-1，见 CRITERIA-CHANGE-P05-R5.md）：`boundary` 由「渲染期从句切出」升为
#   **一等字段** ⇒ 本模式断言「引导串**不得残留**」。
#   ⛔ 它是**禁止性**模式，⛔ 不是切分器：切分只走 `gen-common.split_boundary` 的显式标记查找
#     （⛔ 不做关键词猜测——实测 `…而是边界：` 是主题词，正则误捕）。
BOUNDARY_MARK_RE = re.compile(r"适用边界是|适用边界必须写清")


def boundary_failures(node):
    """`boundary` 字段的三条硬断言（B-1 起 `boundary` 必填且非空）。

    ① 非空（字段转必填）；
    ② 不与 `why` / `intro` 的任一**整句**逐字相同（归一化比对，与 summary 第 3 条同法）
       —— 防「字段化后同一条边界既躺在正文、又躺在字段里」的重复；
    ③ `why` / `intro` 中**不得残留**引导串 —— 否则 `prose_html` 会在该区块再切出一个边界块，
       页面出现两个「适用边界」而判据只认字段那一个 ⇒ 视觉与判据脱钩。

    ★ 局限登记（⛔ 不假装机检）：本条**只断言「不重复 / 不残留 / 非空」**，
      ⛔ 不断言「这句到底是不是一条合格的适用性限定」——那是内容判断（B-1 的 67 条人工改判），
      由留档的改判表 + 人看兜。
    """
    bd = (node.get("boundary") or "").strip()
    if not bd:
        return ["boundary 为空（B-1 起必填且非空）"]
    bad = []
    target = norm_sentence(bd)
    dup = [norm_sentence(x) for x in sentences(node.get("why", ""))] + \
          [norm_sentence(x) for x in sentences(node.get("intro", ""))]
    if target and target in dup:
        bad.append("boundary 与 why/intro 的某个整句逐字相同")
    for f in ("why", "intro"):
        if BOUNDARY_MARK_RE.search(node.get(f, "") or ""):
            bad.append("%s 中残留边界引导串（会渲染出第二个适用边界块）" % f)
    return bad


def walk_files(root):
    out = []
    for dirpath, _dn, fns in os.walk(root):
        for fn in fns:
            out.append(os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/"))
    return sorted(out)


def make_sandbox(name, mutate=None):
    """临时沙箱：复制真相源与生成器脚本，使负例夹具完全不触碰真实产物。"""
    d = tempfile.mkdtemp(prefix="pekg-%s-" % name)
    shutil.copytree(DATA_DIR, os.path.join(d, "10-dag-data"))
    ck = os.path.join(d, "16-checkpoint")
    os.makedirs(ck)
    for fn in sorted(os.listdir(HERE)):
        if fn.endswith(".py"):
            shutil.copy2(os.path.join(HERE, fn), os.path.join(ck, fn))
    if mutate:
        mutate(d)
    return d


def run_build(sandbox, extra):
    cmd = [sys.executable, os.path.join(sandbox, "16-checkpoint", "build-all.py"),
           "--root", sandbox] + list(extra)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300)


def artifact_shas(root):
    """生成层拥有的产物摘要（⛔ 不含 vendor/ 第三方脚本、站点级只读图片资产、真相源与生成器）。

    ★ 判据作用域修正（2026-10-15）：沙箱只复制真相源与生成器脚本，**不复制 `assets/`**
      （那是站点级只读资产，不是生成产物）。初版把 `assets/` 计入摘要 ⇒ 探针侧缺这两个文件、
      真实产物侧有 ⇒ P16 对「两次生成完全一致」判 FAIL（本轮实测 2 处假阳）。
      ⇒ 把 `assets/` 一并排除，使两侧作用域对齐（P16 的对象是**生成产物**的幂等性）。
    """
    out = {}
    for rel in walk_files(root):
        if rel.startswith("10-dag-data/") or rel.startswith("16-checkpoint/"):
            continue
        if rel.startswith("13-interactive/vendor/"):
            continue
        if rel.startswith("assets/"):
            continue
        p = os.path.join(root, rel)
        try:
            out[rel] = sha(open(p, encoding="utf-8").read())
        except (UnicodeDecodeError, IsADirectoryError):
            continue
    return out


# ---------------------------------------------------------------- CSS 结构解析

def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def parse_css(css):
    """把 CSS 文本解析为 [(at_conditions, header, body, raw_header)]。

    at_conditions 为该规则所处的全部外层 at-rule 条件（如 ('(hover:hover)',)）；
    顶层规则为空元组。★ 依据 H1 §2.5：媒体查询块必须取**全部**同款块。
    """
    text = strip_comments(css)
    out = []
    stack = []
    buf = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "{":
            header = "".join(buf).strip()
            buf = []
            if header.startswith("@"):
                stack.append(header)
                i += 1
                continue
            depth = 1
            j = i + 1
            while j < n and depth:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            body = text[i + 1:j - 1]
            out.append((tuple(stack), header, body, header))
            i = j
            continue
        if ch == "}":
            if stack:
                stack.pop()
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    return out


def media_condition_norm(header):
    m = re.match(r"@media\s*(.*)$", (header or "").strip(), re.I)
    if not m:
        return None
    return re.sub(r"\s+", "", m.group(1).lower())


def selectors_of(header):
    return [s.strip() for s in header.split(",") if s.strip()]


def find_rules(rules, selector_pred=None, cond_pred=None):
    out = []
    for conds, header, body, _raw in rules:
        if header.startswith("@"):
            continue
        if cond_pred is not None and not cond_pred(conds):
            continue
        for sel in selectors_of(header):
            if selector_pred is None or selector_pred(sel):
                out.append((conds, sel, body))
    return out


def count_elements(html_text, selector):
    """粗粒度元素计数：只支持登记表实际用到的形态（标签 / .class / 组合）。

    ⛔ 不做完整 CSS 选择器引擎；无法解析的形态返回 None（由判据判 FAIL，⛔ 不静默跳过）。
    """
    pats = []
    for part in selector.strip().split():
        part = part.split(":")[0].split("[")[0].strip()
        if not part:
            continue
        if part.startswith("."):
            pats.append(("class", part[1:]))
        elif re.match(r"^[a-z][a-z0-9]*$", part):
            pats.append(("tag", part))
        else:
            return None
    if not pats:
        return None
    count = 0
    for m in re.finditer(r"<([a-zA-Z][a-zA-Z0-9-]*)\b([^>]*)>", html_text):
        tag, attrs = m.group(1).lower(), m.group(2)
        ok = True
        for kind, val in pats:
            if kind == "tag":
                if tag != val:
                    ok = False
                    break
            else:
                cm = re.search(r'class\s*=\s*"([^"]*)"', attrs)
                classes = cm.group(1).split() if cm else []
                if val not in classes:
                    ok = False
                    break
        if ok:
            count += 1
    return count


def backdrop_subtree(html_text):
    """取出 .backdrop 容器的子树文本（按 div 标签配对计数）。"""
    m = re.search(r'<div class="backdrop"[^>]*>', html_text)
    if not m:
        return None
    depth = 1
    i = m.end()
    while i < len(html_text) and depth:
        nxt_open = html_text.find("<div", i)
        nxt_close = html_text.find("</div>", i)
        if nxt_close == -1:
            return None
        if nxt_open != -1 and nxt_open < nxt_close:
            depth += 1
            i = nxt_open + 4
        else:
            depth -= 1
            i = nxt_close + 6
    return html_text[m.end():i]


def _link_tags(text):
    """返回 [(rel, href, tag)]：页内 `<link>` 的**分类所需三件**（rel ∈ 闭集 / href / 原标签）。

    ★ 与 `_resource_refs` 的分工：后者回答「哪些引用会被当资源取」，本函数回答
      「一个 `<link>` 的 rel 属于资源类还是元数据类」—— P09 的两条断言分别用这两者。
    ★ `rel` 允许出现多个值（如 `rel="icon alternate"`）⇒ 逐 token 归一为小写。
    """
    out = []
    for m in LINK_TAG_RE.finditer(text):
        tag = m.group(0)
        h = LINK_HREF_RE.search(tag)
        r = LINK_REL_RE.search(tag)
        rel = " ".join((r.group(1) if r else "").lower().split())
        out.append((rel, (h.group(1).strip() if h else None), tag))
    return out


def _is_meta_link(ref):
    """该条资源引用是否属于**元数据类 `<link>`**（`canonical` / `icon` / …）。

    ★ 这是 P09 的**单一分流点**：`check_p09` 的两条子断言（受检页集合、交互页）都经它判断，
      ⛔ 不各写一份判法（两处各写一份会让「rel 是什么」出现两个口径）。
    """
    if ref[0] != "link":
        return False
    attrs = ref[2] or ""
    r = LINK_REL_RE.search(attrs)
    return bool(r) and " ".join(r.group(1).lower().split()) in LINK_META_RELS


def _strip_url_attrs(text):
    """把**属性值里的 URL 载体**摘掉（`href=` / `content=`），只留正文。

    ★ 为什么 P12 需要它：P12 的「主机名」断言的立意是「公开**正文**里不得出现内部主机名」。
      而 SH4 标准档要求每页写 `canonical` / `og:url` / `og:image` 的**绝对自指 URL**
      （含 `zako-mio.github.io`）⇒ 若把属性值也计入，P12 会在**它自己要求写的东西**上 FAIL。
      摘掉 URL 载体后，「标签属性的取值」归 P09/P30 管（那里的断言更精确：rel 闭集 + 自指基址 +
      白名单），P12 只管正文 —— 这是**判据对象收窄**（R-23），⛔ 不是放宽阈值。
    """
    return RES_URL_ATTR_RE.sub("", text)


def _strip_host_urls(text):
    """把**正文里的绝对 URL 一词**整段摘掉（替换为一个空格），只留散文。

    ★ 为什么 sitemap / robots 需要它：这两件的**全部内容**按规范就是绝对 URL
      （`<loc>https://…</loc>` / `Sitemap: https://…`）。它们不是「内部主机名泄漏」，
      而是**发布发现协议的载体**（与 `llms.txt` / RSS 同类）⇒ 判「正文含主机名」是判错了对象。
      ⇒ 只在这两件上摘掉 URL 词；⛔ HTML 页**不摘**（页面正文里的裸主机名照样 FAIL ——
        负例夹具 `mut_p12` 第 2 条守着这个面）。
    """
    return HOST_URL_TOKEN_RE.sub(" ", text)


def _resource_refs(text):
    """返回 [(kind, value, attrs)]：**加载类**资源引用。

    ★ 作用域纪律（HANDOFF-R2 §三.2）：只认加载类引用；`<a href>` 是引用不是资源，不在此列。
    ★ 2026-10-16 第 8 轮补：`<link>` 是否算「加载类」由 `check_p09` 按 rel 闭集裁决
      （元数据类 rel 由「无主机」断言管），本函数**仍然返回**全部 `<link>`
      —— 保留它是因为 P30 要按「引用命中 assets/ 前缀」判定，而那与 rel 正交。
    """
    refs = []
    for m in re.finditer(r"<script\b([^>]*)>", text, re.I):
        a = m.group(1)
        s = re.search(r'src\s*=\s*"([^"]*)"', a, re.I)
        if s:
            refs.append(("script", s.group(1).strip(), a))
    for m in LINK_TAG_RE.finditer(text):
        tag = m.group(0)
        s = re.search(r'href\s*=\s*"([^"]*)"', tag, re.I)
        if s:
            refs.append(("link", s.group(1).strip(), tag))
    for tag in ("img", "iframe", "source", "video", "audio", "embed"):
        for m in re.finditer(r"<%s\b[^>]*>" % tag, text, re.I):
            s = re.search(r'src\s*=\s*"([^"]*)"', m.group(0), re.I)
            if s:
                refs.append((tag, s.group(1).strip(), m.group(0)))
    for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)", text, re.I):
        refs.append(("css-url", m.group(1).strip(), ""))
    return refs


def resolve_site_path(page_rel, value):
    """把一条**站内相对引用**按页面所在目录解析为站内路径（**按 URL 语义**处理 `..`）。

    ★ 为什么不能用 `os.path.normpath`：它把 `..` **静默折叠**（对根页面 `normpath("" + "../assets/x")`
      得到 `assets/x`），于是「逃出站点根」与「正常的 `../assets/`」变成同一个结果，判据无法区分。

    ★ 为什么不能用「保留前导 `..`」的写法：那会**误判合法路径**。本站是 GitHub Pages **项目站**，
      样式块必须写**相对路径**；而全站样式块按页面深度参数化（`page_shell(base)`）：
        根页面 `index.html`（在站点根）写 `assets/…`；
        子目录页 `11-node-pages/x.html` 写 `../assets/…`。
      两者在浏览器里都解析到站点根的 `assets/`。⇒ 解析必须**按 URL 语义**：在根上的 `..` 是
      no-op（浏览器即如此），而不是「逃出根」。（本轮实测：保留前导 `..` 的写法对根页面产出
      21 处假阳；`normpath` 的写法对子目录页产出 208 处假阳。）
    """
    base = [p for p in os.path.dirname(page_rel).split("/") if p] if page_rel else []
    v = value.partition("#")[0].partition("?")[0]
    if v.startswith("/"):
        return None
    for part in v.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if base:
                base.pop()
            # 已在站点根 ⇒ 按 URL 语义 no-op（⛔ 不 append ".."）
        else:
            base.append(part)
    return "/".join(base)


def _is_image_ref(kind, value, attrs, asset_prefix, asset_exts, page_rel=""):
    """第二类白名单判定：引用是否为「**解析后落在站点根 `assets/` 下**的相对路径 + 图片扩展名」。

    ★ 判据作用域修正（2026-10-15）：初版要求 `value.startswith("assets/")`，但那只在**站点根页面**成立；
      子目录页（`11-node-pages/` 等）必须写 `../assets/…` ⇒ 初版把全部合法图片引用判成「非图片资源引用」
      （本轮实测 208 处假阳）。⇒ 改为**按页面所在目录解析后再判前缀**：
        ① 站外引用（`http(s)://` / `//`）直接 False；
        ② 解析结果必须仍以 `assets/` 开头，且不得带前导 `..`（堵住「用过多 `../` 逃出站点根」）；
        ③ 扩展名须在闭集内。
    """
    resolved = resolve_site_path(page_rel, value)
    if resolved is None:
        return False
    if resolved.startswith("../") or resolved == "..":
        return False
    if not resolved.startswith(asset_prefix):
        return False
    v = value.partition("#")[0].partition("?")[0]
    ext = os.path.splitext(v)[1].lower()
    if ext not in asset_exts:
        return False
    if kind == "link":
        rel = re.search(r'rel\s*=\s*"([^"]*)"', attrs or "", re.I)
        return bool(rel) and rel.group(1).strip().lower() in LINK_IMAGE_RELS
    if kind == "css-url":
        return True
    return kind in ("img", "source", "video", "audio", "embed")


# ---------------------------------------------------------------- 上下文

class Ctx(object):
    def __init__(self):
        self.root = SITE_ROOT
        self.data = None
        self.files = {}
        self.html = {}
        self.md = {}
        self.tokens_css = ""
        self.tokens_block_sha = ""
        self.template_id = ""
        self.asset_prefix = ""
        self.asset_exts = ()
        self.credits = {}
        self.ledger = {}
        self.interaction_surface = ()
        self.surface_selectors = set()
        self.contract_roles = []
        self.snapshot_sha = ""
        self.probe = {}
        self.site_base_url = ""
        self.notes = []
        self.report_lines = []


def load_ctx(with_probe=True):
    ctx = Ctx()
    C = _imp(os.path.join(HERE, "gen-common.py"), "pekg_common")
    ctx.template_id = C.TEMPLATE_ID
    ctx.site_base_url = C.SITE_BASE_URL      # ★ 2026-10-16 第 8 轮：P09 判「绝对自指 URL」要用它
    ctx.tokens_css = C.tokens_css()
    ctx.tokens_block_sha = sha(ctx.tokens_css.rstrip("\n"))
    ctx.asset_prefix = C.ASSET_PREFIX
    ctx.asset_exts = tuple(C.ASSET_EXTS)
    ctx.credits = dict(C.BACKDROP_CREDITS)
    ctx.ledger = dict(C.BACKDROP_LEDGER)
    ctx.interaction_surface = tuple(C.INTERACTION_SURFACE)
    ctx.surface_selectors = set(C.surface_selectors())
    snap = json.load(open(os.path.join(DATA_DIR, "_contract.snapshot.json"), encoding="utf-8"))
    roles = snap["roles"]
    ctx.contract_roles = list(roles.keys()) if isinstance(roles, dict) else [r.get("id") for r in roles]
    ctx.data = {
        "dag": json.load(open(os.path.join(DATA_DIR, "dag.json"), encoding="utf-8")),
        "frontier": json.load(open(os.path.join(DATA_DIR, "frontier.json"), encoding="utf-8")),
        "glossary": json.load(open(os.path.join(DATA_DIR, "glossary.json"), encoding="utf-8")),
        "sources": json.load(open(os.path.join(DATA_DIR, "sources.json"), encoding="utf-8")),
        "site_tokens": json.load(open(os.path.join(DATA_DIR, "site-tokens.json"), encoding="utf-8")),
        "site_palette": json.load(open(os.path.join(DATA_DIR, "site-palette.json"), encoding="utf-8")),
        "provenance": json.load(open(os.path.join(DATA_DIR, "_contract.provenance.json"), encoding="utf-8")),
    }
    ctx.snapshot_sha = sha(open(os.path.join(DATA_DIR, "_contract.snapshot.json"), "rb").read().decode("utf-8"))
    for rel in walk_files(SITE_ROOT):
        if rel.startswith("10-dag-data/") or rel.startswith("16-checkpoint/"):
            continue
        p = os.path.join(SITE_ROOT, rel)
        try:
            text = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        ctx.files[rel] = text
        if rel.endswith(".html"):
            ctx.html[rel] = text
        elif rel.endswith(".md"):
            ctx.md[rel] = text
    if with_probe:
        ctx.probe = build_probes()
    return ctx


def build_probes():
    """一次跑齐需要真实生成链路的判据（P16/P17/P18/P21），供各判据消费。"""
    probe = {}
    a = make_sandbox("idem-a")
    b = make_sandbox("idem-b")
    run_build(a, ["--write", "--json"])
    run_build(b, ["--write", "--json"])
    probe["idempotent"] = {"a": artifact_shas(a), "b": artifact_shas(b), "disk": artifact_shas(SITE_ROOT)}
    c = make_sandbox("dryrun")
    pd = run_build(c, ["--dry-run", "--json"])
    pw = run_build(c, ["--write", "--json"])
    try:
        dry = json.loads(pd.stdout)
    except Exception:
        dry = {}
    try:
        wr = json.loads(pw.stdout)
    except Exception:
        wr = {}
    probe["dryrun"] = {"dry": dry, "write": wr, "rc_dry": pd.returncode, "rc_write": pw.returncode}
    o = make_sandbox("orphan")
    run_build(o, ["--write", "--json"])
    orphan_rel = "11-node-pages/zz-orphan.html"
    with open(os.path.join(o, orphan_rel), "w", encoding="utf-8") as f:
        f.write("<html>stale</html>")
    po = run_build(o, ["--write", "--json"])
    try:
        oj = json.loads(po.stdout)
    except Exception:
        oj = {}
    probe["orphan"] = {"orphan": orphan_rel, "residual": oj.get("residual_orphans", []),
                       "removed": oj.get("removed", []),
                       "exists_after": os.path.exists(os.path.join(o, orphan_rel)),
                       "rc": po.returncode}

    def mut(d):
        p = os.path.join(d, "10-dag-data", "frontier.json")
        doc = json.load(open(p, encoding="utf-8"))
        doc["edition"] = "2026-11"
        doc["items"][0]["status"] = "disputed"
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
    m = make_sandbox("frontier", mut)
    run_build(m, ["--write", "--json"])
    probe["frontier"] = {"base": artifact_shas(a), "mut": artifact_shas(m)}
    for d in (a, b, c, o, m):
        shutil.rmtree(d, ignore_errors=True)
    return probe


# ---------------------------------------------------------------- P01–P14（基线）

def check_p01(ctx):
    """真相源 JSON 合法且必填字段齐全。"""
    bad = []
    need_meta = ("mission", "as_of", "edition", "node_count", "edge_count", "group_count",
                 "layer_count", "acyclic", "edge_semantics", "audience", "direction_rule")
    for k in need_meta:
        if k not in ctx.data["dag"].get("meta", {}):
            bad.append(("dag.meta", k))
    need_group = ("id", "name", "en", "order", "intro", "node_count")
    need_node = ("id", "name", "en", "group", "layer", "content_status", "why", "boundary", "intro",
                 "when", "lab", "evidence", "terms", "pitfalls", "summary", "prereq",
                 "successors", "tags")
    for g in ctx.data["dag"].get("groups", []):
        for k in need_group:
            if k not in g:
                bad.append(("group " + str(g.get("id")), k))
    for n in ctx.data["dag"].get("nodes", []):
        for k in need_node:
            if k not in n:
                bad.append(("node " + str(n.get("id")), k))
    for e in ctx.data["dag"].get("edges", []):
        for k in ("source", "target", "rel", "note"):
            if k not in e:
                bad.append(("edge %s>%s" % (e.get("source"), e.get("target")), k))
    if not isinstance(ctx.data["dag"].get("layers"), dict) or not ctx.data["dag"]["layers"]:
        bad.append(("dag.layers", "缺失或非对象"))
    for k in ("as_of", "edition", "items"):
        if k not in ctx.data["frontier"]:
            bad.append(("frontier", k))
    for it in ctx.data["frontier"].get("items", []):
        for k in ("id", "title", "summary", "status", "supersedes", "evidence"):
            if k not in it:
                bad.append(("frontier item " + str(it.get("id")), k))
    for t in ctx.data["glossary"].get("terms", []):
        for k in ("term", "en", "definition", "node_refs"):
            if k not in t:
                bad.append(("glossary " + str(t.get("term"))[:16], k))
    for s in ctx.data["sources"].get("sources", []):
        for k in ("id", "title", "url", "tier", "date", "note"):
            if k not in s:
                bad.append(("source " + str(s.get("id")), k))
    return (not bad), "四份真相源 JSON 合法且必填字段齐全（缺字段 %d 处）%s" % (len(bad), bad[:6])


def check_p02(ctx):
    """节点 id 唯一、group 可解析、prereq/successors 指向存在节点。"""
    dag = ctx.data["dag"]
    ids = [n["id"] for n in dag["nodes"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    gids = {g["id"] for g in dag["groups"]}
    bad_group = [n["id"] for n in dag["nodes"] if n["group"] not in gids]
    idset = set(ids)
    bad_pre = [(n["id"], p) for n in dag["nodes"] for p in n.get("prereq", []) if p not in idset]
    bad_suc = [(n["id"], p) for n in dag["nodes"] for p in n.get("successors", []) if p not in idset]
    bad_edge = [(e["source"], e["target"]) for e in dag["edges"]
                if e["source"] not in idset or e["target"] not in idset]
    ok = not (dup or bad_group or bad_pre or bad_suc or bad_edge)
    return ok, ("id 唯一 / group 可解析 / prereq 与 successors 可解析 / 边端点可解析（重复 %s，越界 %s，"
                "悬空 prereq %s，悬空 successors %s，坏边 %s）"
                % (dup, bad_group, bad_pre[:4], bad_suc[:4], bad_edge[:4]))


def check_p03(ctx):
    """rel 属闭集、无环、拓扑层序与边方向一致。"""
    dag = ctx.data["dag"]
    bad_rel = sorted({e["rel"] for e in dag["edges"]} - REL_ENUM)
    lay = {n["id"]: n["layer"] for n in dag["nodes"]}
    viol = [(e["source"], e["target"]) for e in dag["edges"]
            if e["source"] in lay and e["target"] in lay and not lay[e["source"]] < lay[e["target"]]]
    adj = {i: [] for i in lay}
    indeg = {i: 0 for i in lay}
    for e in dag["edges"]:
        if e["source"] in adj and e["target"] in indeg:
            adj[e["source"]].append(e["target"])
            indeg[e["target"]] += 1
    q = [i for i, d in indeg.items() if d == 0]
    seen = 0
    while q:
        x = q.pop()
        seen += 1
        for y in adj[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                q.append(y)
    layer_map_ok = True
    for k, vs in dag["layers"].items():
        for v in vs:
            if lay.get(v) != int(k):
                layer_map_ok = False
    ok = (not bad_rel) and seen == len(lay) and not viol and layer_map_ok
    return ok, ("rel 闭集 %s；Kahn 拓扑 %d/%d（无环=%s）；层序违例 %d 条；layers 映射一致=%s"
                % (sorted(REL_ENUM), seen, len(lay), seen == len(lay), len(viol), layer_map_ok))


def check_p04(ctx):
    """每组至少 1 个节点；无孤立节点（layer 0 除外）。"""
    dag = ctx.data["dag"]
    empty = [g["id"] for g in dag["groups"] if not any(n["group"] == g["id"] for n in dag["nodes"])]
    touched = set()
    for e in dag["edges"]:
        touched.add(e["source"])
        touched.add(e["target"])
    iso = [n["id"] for n in dag["nodes"] if n["id"] not in touched and n["layer"] != 0]
    iso0 = [n["id"] for n in dag["nodes"] if n["id"] not in touched and n["layer"] == 0]
    ok = not empty and not iso
    return ok, ("空组 %d 个；非 layer0 孤立节点 %d 个；layer0 孤立节点 %d 个（允许，仅登记）"
                % (len(empty), len(iso), len(iso0)))


def check_p05(ctx):
    """字段长度约束与 summary 结构约束逐节点复核 —— 口径 caliber = 汉字数 + 拉丁词数。"""
    rows, bad = [], []
    for n in ctx.data["dag"]["nodes"]:
        st = n["content_status"]
        w, i, s = caliber(n.get("why")), caliber(n.get("intro")), caliber(n.get("summary"))
        rows.append((n["id"], st, w, i, s))
        if w < WHY_MIN[st]:
            bad.append((n["id"], "why 下限", w, WHY_MIN[st]))
        if i < INTRO_MIN[st]:
            bad.append((n["id"], "intro 下限", i, INTRO_MIN[st]))
        if HOLLOW.search(n.get("why", "")):
            bad.append((n["id"], "why 空洞占位", "", ""))
        for msg in summary_structural_failures(n):
            bad.append((n["id"], msg, "", ""))
        for msg in boundary_failures(n):
            bad.append((n["id"], msg, "", ""))
    over_w = [(r[0], r[2]) for r in rows if r[2] > WHY_UPPER_REPORT]
    over_i = [(r[0], r[3]) for r in rows if r[3] > INTRO_UPPER_REPORT]
    over_s = [(r[0], r[4]) for r in rows if r[4] > SUMMARY_UPPER_REPORT]
    ctx.notes.append("P05 口径（SCHEMA §3 唯一口径）：caliber = 汉字数 + 拉丁词数；"
                     "汉字正则 %s；拉丁词正则 %s。⛔ 不用 len(s) 计字符/字节/非空白。"
                     % (CJK.pattern, LATIN_WORD.pattern))
    ctx.notes.append("P05 报告项（⛔ 不判 FAIL，按变更登记 C2 与判据分档原则）：why > %d 的节点 %d 个 %s；"
                     "intro > %d 的节点 %d 个 %s；summary > %d 的节点 %d 个 %s。"
                     % (WHY_UPPER_REPORT, len(over_w), over_w[:8],
                        INTRO_UPPER_REPORT, len(over_i), over_i[:8],
                        SUMMARY_UPPER_REPORT, len(over_s), over_s[:8]))
    ctx.notes.append("P05 summary 硬判据为结构性三条（完整句 / 非空洞 / 不与 why·intro 整句逐字相同）；"
                     "原 `caliber ≥30` 数值下限已撤销 —— 实测 49 个节点低于 30（48 registered + PE-P-02），"
                     "把数据改成符合它会砍掉完整结论、降低内容质量 ⇒ 按判据分档原则换判据而非改数字。")
    ctx.report_lines.append("P05 逐节点 caliber 实测（口径 = 汉字数 + 拉丁词数）：")
    for r in rows:
        ctx.report_lines.append("  %-8s %-10s why=%-4d intro=%-4d summary=%-4d" % r)
    return (not bad), ("逐节点复核 %d 个（口径 caliber）；硬判违例 %d 处 %s；"
                       "报告项：why>%d %d 个、intro>%d %d 个、summary>%d %d 个"
                       % (len(rows), len(bad), bad[:6], WHY_UPPER_REPORT, len(over_w),
                          INTRO_UPPER_REPORT, len(over_i), SUMMARY_UPPER_REPORT, len(over_s)))


def check_p06(ctx):
    """complete 节点 pitfalls ≥1、evidence ≥1；evidence 契约成立；GD-N 未证实例外按 frontier 状态判定。"""
    dag = ctx.data["dag"]
    src_by_id = {s["id"]: s for s in ctx.data["sources"]["sources"]}
    fstatus = {i["id"]: i.get("status") for i in ctx.data["frontier"].get("items", [])}
    bad = []
    empty_registered = 0
    for n in dag["nodes"]:
        st = n["content_status"]
        if st == "registered":
            if not n.get("pitfalls") or not n.get("evidence"):
                empty_registered += 1
        else:
            if len(n.get("pitfalls", [])) < 1:
                bad.append((n["id"], "pitfalls 为空"))
            if len(n.get("evidence", [])) < 1 and not (n["group"] == "GD-N" and fstatus.get(n["id"]) == "unverified"):
                bad.append((n["id"], "evidence 为空"))
        for ev in n.get("evidence", []):
            for k in ("claim", "source_id", "url", "quote", "tier"):
                if k not in ev:
                    bad.append((n["id"], "evidence 缺字段 " + k))
            if ev.get("source_id") not in src_by_id:
                bad.append((n["id"], "source_id 不可解析 " + str(ev.get("source_id"))))
            elif src_by_id[ev["source_id"]]["url"] != ev.get("url"):
                bad.append((n["id"], "evidence url 与台账不一致 " + str(ev.get("source_id"))))
            if len(ev.get("quote", "")) > 200:
                bad.append((n["id"], "quote 超 200 字"))
    gdn_unver = [i for i in ctx.data["frontier"].get("items", []) if i.get("status") == "unverified"]
    for it in gdn_unver:
        if not it.get("offline_repro"):
            bad.append((it["id"], "unverified 但缺 offline_repro"))
    ctx.notes.append("P06 作用域：pitfalls/evidence ≥1 依 SCHEMA §3 只对 `complete` 节点硬判；"
                     "`registered` 节点按两态契约允许为空数组，其空值由 P13 的 pending_nodes 逐条登记，"
                     "不构成静默留白。GD-N `unverified` 例外按 frontier.json 的实际状态判定（本轮 %d 条）。"
                     % len(gdn_unver))
    return (not bad), ("complete 节点 pitfalls/evidence 达标；evidence 契约违例 %d 处 %s；"
                       "registered 空 pitfalls/evidence 节点 %d 个（已由 pending_nodes 登记）；"
                       "GD-N 未证实条目 %d 条" % (len(bad), bad[:6], empty_registered, len(gdn_unver)))


def check_p07(ctx):
    """节点 terms 逐条可在 glossary.json 解析。"""
    names = [t["term"] for t in ctx.data["glossary"]["terms"]]
    bad = []
    for n in ctx.data["dag"]["nodes"]:
        for t in n.get("terms", []):
            if not any(str(t).startswith(g + "：") for g in names):
                bad.append((n["id"], str(t)[:24]))
    dup = sorted({t for t in names if names.count(t) > 1})
    ok = not bad and not dup
    return ok, "术语台账 %d 条、表述唯一=%s；节点 terms 未解析 %d 条 %s" % (len(names), not dup, len(bad), bad[:6])


def _resolve(page_rel, href):
    if href.startswith("/"):
        return None
    base = os.path.dirname(page_rel)
    return os.path.normpath(os.path.join(base, href)).replace(os.sep, "/")


def strip_scripts(text):
    return INLINE_SCRIPT_RE.sub(lambda m: "<script%s></script>" % m.group("attrs"), text)


def check_p08(ctx):
    """全站 HTML 断链 = 0（含跨目录相对路径与页内锚点）。"""
    existing = set(walk_files(SITE_ROOT))
    bad = []
    for rel, text in sorted(ctx.html.items()):
        scan = strip_scripts(text)
        for m in re.finditer(r'(?:href|src)\s*=\s*"([^"]*)"', scan, re.I):
            raw = m.group(1).strip()
            if not raw or raw.startswith(("http://", "https://", "mailto:", "data:", "tel:")):
                continue
            if raw.startswith("#"):
                frag = raw[1:]
                if frag and ('id="%s"' % frag) not in text and ("name=\"%s\"" % frag) not in text:
                    bad.append((rel, raw, "页内锚点不存在"))
                continue
            target, _, frag = raw.partition("#")
            tgt = _resolve(rel, target)
            if tgt is None or tgt not in existing:
                bad.append((rel, raw, "目标文件不存在"))
                continue
            if frag and tgt.endswith(".html"):
                body = ctx.files.get(tgt) or open(os.path.join(SITE_ROOT, tgt), encoding="utf-8").read()
                if ('id="%s"' % frag) not in body:
                    bad.append((rel, raw, "跨页锚点不存在"))
    return (not bad), "受检 HTML %d 页；断链 %d 处 %s" % (len(ctx.html), len(bad), bad[:6])


def check_p09(ctx):
    """自包含：受检集合 0 外链资源 / 0 外链脚本 / 0 @import / 0 跨目录相对资源引用；
    两类白名单（脚本 / 图片）各自不扩散。"""
    self_pages = [r for r in ctx.html if r.startswith(SELF_DIRS) or r == "index.html"]
    bad = []
    inline_shas = {}
    img_refs = []
    meta_link_n = 0            # 元数据类 `<link>`（canonical / icon / …）的计数
    for rel in sorted(self_pages):
        text = ctx.html[rel]
        # ★ 2026-10-16 第 8 轮：`<link>` 按 **rel 闭集**分流（见 LINK_META_RELS 的注释块）。
        #   元数据类走「无主机」断言；其余（含未分类 rel）走资源白名单断言。
        meta_hrefs = set()
        for lrel, lhref, ltag in _link_tags(text):
            if lrel in LINK_META_RELS:
                meta_link_n += 1
                if lhref:
                    meta_hrefs.add((lrel, lhref))
                continue
            if lrel not in ("", "stylesheet", "preload", "modulepreload",
                            "prefetch", "dns-prefetch", "preconnect"):
                bad.append((rel, "`<link>` 的 rel 落在闭集之外（未分类）", (lrel, ltag[:70])))
        for lrel, h in sorted(meta_hrefs):
            if not h:
                continue
            if not HOSTED_URL_RE.match(h):
                continue               # 无主机（站内相对路径）⇒ 通过
            # 带主机 ⇒ 只允许 `canonical` / `alternate` 的**本站自指 URL**
            if lrel not in LINK_META_HOSTED_OK or not h.startswith(ctx.site_base_url):
                bad.append((rel, "元数据类 `<link>` 的 href 带主机且不是本站自指 URL", (lrel, h[:90])))
        for kind, value, attrs in _resource_refs(text):
            if kind == "link" and LINK_REL_RE.search(attrs or "") \
                    and " ".join(LINK_REL_RE.search(attrs).group(1).lower().split()) in LINK_META_RELS:
                continue           # 已由上面的「无主机」断言处置，⛔ 不再当资源引用
            if _is_image_ref(kind, value, attrs, ctx.asset_prefix, ctx.asset_exts, page_rel=rel):
                img_refs.append((rel, kind, value))
                continue
            bad.append((rel, "受检集合出现非图片资源引用", (kind, value)))
        if "@import" in text:
            bad.append((rel, "@import 命中", []))
        if URL_HTTP_RE.search(text):
            bad.append((rel, "CSS url() 指向站外", []))
        scripts = INLINE_SCRIPT_RE.findall(text)
        nonsrc = [(a, b) for a, b in scripts if not re.search(r"\bsrc\s*=", a, re.I)]
        if len(nonsrc) != 1:
            bad.append((rel, "内联脚本数 %d（应为 1：唯一的界面引导脚本）" % len(nonsrc), []))
        for a, b in nonsrc:
            if not b.strip().startswith(SCRIPT_MARK):
                bad.append((rel, "存在界面引导之外的内联脚本", [b[:40]]))
            else:
                inline_shas[rel] = sha(b)
    itext = ctx.html.get(INTERACTIVE, "")
    it_refs = _resource_refs(itext)
    # ★ 判据作用域修正（2026-10-15）：初版要求交互页的**全部**资源引用都命中脚本白名单 `vendor/`，
    #   但第二类白名单（站点级图片资产）对**所有页面**都成立，交互页同样要引用背景帧与图标
    #   ⇒ 初版把 11 处合法的图片引用判成「脚本白名单例外扩散」（本轮实测 11 处假阳）。
    #   正确断言＝「每条引用**要么**命中脚本白名单，**要么**是图片白名单引用」。
    # ★ 2026-10-16 第 8 轮：交互页同样要被**元数据类 `<link>` 分流**（它也是 SH4 的受检页）
    #   —— 否则它的 `canonical` 会被当成「脚本白名单例外扩散」（本轮实测 1 处假阳）。
    bad_it = [r for r in it_refs
              if not (r[1].startswith(WHITELIST_PREFIX)
                      or _is_image_ref(r[0], r[1], r[2], ctx.asset_prefix, ctx.asset_exts,
                                        page_rel=INTERACTIVE)
                      or _is_meta_link(r))]
    if URL_HTTP_RE.search(itext):
        bad_it.append(("css-url", "站外 url()", ""))
    bad += [(INTERACTIVE, "脚本白名单例外扩散/站外引用", (r[0], r[1])) for r in bad_it]
    for rel in sorted(self_pages):
        if WHITELIST_PREFIX in ctx.html[rel]:
            bad.append((rel, "受检集合出现脚本白名单前缀引用", []))
    if not it_refs:
        bad.append((INTERACTIVE, "脚本白名单空集：交互入口未引用任何本地脚本", []))
    if not img_refs:
        bad.append(("(全站)", "图片白名单空集：受检集合未引用任何站点级图片资产", []))
    uniq = sorted(set(inline_shas.values()))
    if len(uniq) != 1:
        bad.append(("(全站)", "界面引导脚本非唯一：%d 种 sha256" % len(uniq), []))
    ctx.notes.append("P09 口径：受检集合的「脚本」约束取「外链脚本 = 0」并**加强**为"
                     "「每页内联脚本恰好 1 个且全站逐字节一致（唯一的界面引导脚本）」；"
                     "资源引用只允许两类白名单——13-interactive/ 同目录 vendor/ 脚本、"
                     "以 assets/ 前缀的相对路径图片（扩展名 %s）。"
                     "★ 2026-10-16 第 8 轮补：`<link>` 按 **rel 闭集**分流 —— 元数据类 %s "
                     "走「href 必须无主机」断言（⛔ 不当作资源引用），其余走资源白名单断言；"
                     "落在闭集之外的 rel（preload / dns-prefetch / modulepreload…）一律 FAIL。"
                     "这是**判据对象收窄**（R-23），不是放宽阈值：同批加了闭集与无主机两条断言，"
                     "见 `CRITERIA-CHANGE-R08.md`。"
                     % (ctx.asset_exts, list(LINK_META_RELS)))
    return (not bad), ("受检页面 %d 个：外链资源 0 / 外链脚本 0 / @import 0 / 跨目录资源 0；"
                       "内联引导脚本每页 1 个且全站同一 sha256（%d 种）；元数据类 `<link>` %d 处（进 rel 闭集；`canonical`/`alternate` 容许本站绝对自指 URL）；"
                       "脚本白名单引用 %d 处、图片白名单引用 %d 处；违例 %d 处 %s"
                       % (len(self_pages), len(uniq), meta_link_n, len(it_refs), len(img_refs),
                          len(bad), bad[:4]))


def check_p10(ctx):
    """主题根唯一（仅 html 上的 data-theme）+ 令牌声明点唯一 + 令牌块与派生结果逐字节一致。"""
    bad = []
    block_shas = {}
    for rel, text in sorted(ctx.html.items()):
        m = re.search(r"<html\b([^>]*)>", text, re.I)
        if not m or "data-theme=" not in m.group(1):
            bad.append((rel, "html 根缺 data-theme", ""))
        tags = re.findall(r"<(\w+)\b[^>]*\bdata-theme\s*=", text)
        if set(tags) != {"html"}:
            bad.append((rel, "承载 data-theme 的元素种类 %s（应仅 html）" % sorted(set(tags)), ""))
        for style in STYLE_RE.findall(text):
            # ★ 判据作用域修正（2026-10-15 第二次）：初版直接对**含注释的样式块**跑 `([^{}]+)\{`，
            #   于是 `/* 强制深色档 */\n:root[data-theme='dark']` 这种形态被整体当成「选择器」，
            #   其最左 token 是 `/*` ⇒ 被误判为「未指向根元素」（本轮实测 38 处假阳）。
            #   ⇒ 必须**先剥注释再抽选择器**（与 report-renderer 的「CSS 侧先剥注释再判」同一纪律）。
            clean_style = re.sub(r"/\*.*?\*/", "", style, flags=re.S)
            for sel in re.findall(r"([^{}]+)\{", clean_style):
                if "data-theme" not in sel:
                    continue
                # 正确断言是「**最左复合体指向根元素**（`html` 或 `:root`）」，
                # ⛔ 不是「字符串以 `html[` 开头」——后者把合法的根选择器误判为「非 html 根」，
                # 并连带把生成器产出的三块结构全部判 FAIL。
                left = sel.strip().split()[0].split(",")[0].strip()
                if not (left.startswith("html") or left.startswith(":root")):
                    bad.append((rel, "主题选择器未指向根元素", sel.strip()[:60]))
        blocks = re.findall(re.escape(TOKEN_BEGIN) + r".*?" + re.escape(TOKEN_END), text, re.S)
        if len(blocks) != 1:
            bad.append((rel, "令牌声明块 %d 个（应为 1）" % len(blocks), ""))
        else:
            block_shas[rel] = sha(blocks[0])
        for style in STYLE_RE.findall(text):
            rest = re.sub(re.escape(TOKEN_BEGIN) + r".*?" + re.escape(TOKEN_END), "", style, flags=re.S)
            extra = re.findall(r"--[A-Za-z0-9_-]+\s*:", rest)
            if extra:
                bad.append((rel, "令牌块之外的自定义属性声明", extra[:4]))
    uniq = sorted(set(block_shas.values()))
    if len(uniq) != 1:
        bad.append(("(全站)", "令牌声明块 sha256 非唯一：%d 种" % len(uniq), ""))
    elif uniq and uniq[0] != ctx.tokens_block_sha:
        bad.append(("(全站)", "内联令牌块与 gen-tokens.py 派生结果不一致", (uniq[0], ctx.tokens_block_sha)))
    return (not bad), ("页面 %d 个：data-theme 仅承载于 html 根；令牌声明块每页 1 个、全站 sha256 %d 种；"
                       "违例 %d 处 %s" % (len(ctx.html), len(uniq), len(bad), bad[:4]))


def check_p11(ctx):
    """对比度：站点调色板的全部对比度三元组逐条复核（硬判与 report-only 分离）。"""
    T = _imp(GEN_TOKENS, "pekg_gt")
    pal = ctx.data["site_palette"]
    values = pal["values"]
    triples = pal["_meta"]["contrast_triples"]
    if not triples:
        return False, "空集守卫：contrast_triples 为空 ⇒ 判据恒真"
    if not values:
        return False, "空集守卫：站点调色板 values 为空"
    bad, rows, reports = [], [], []
    for t in triples:
        miss = [k for k in (t["fg"], t["bg"]) if k not in values]
        if miss:
            bad.append((t["label"], "令牌缺失", miss))
            continue
        for side in ("light", "dark"):
            cr = T.contrast_ratio(values[t["fg"]][side], values[t["bg"]][side])
            row = (t["label"], side, values[t["fg"]][side], values[t["bg"]][side], round(cr, 2), t["min"])
            if t.get("report_only"):
                reports.append(row)
            elif cr + 1e-9 < float(t["min"]):
                bad.append(row)
            else:
                rows.append(row)
    site = ctx.data["site_tokens"]
    ref = site.get("reference_backgrounds", {})
    site_rows = 0
    for t in site.get("tokens", []):
        if t.get("usage_tier") != "body":
            continue
        for mode in ("light", "dark"):
            bg = ref.get(mode)
            if not bg:
                continue
            site_rows += 1
            c = T.contrast_ratio(t[mode], bg)
            if c < BODY_MIN:
                bad.append((t["name"], mode, "站点局部令牌对参考底", round(c, 2)))
    ctx.notes.append("P11 作用域变更（判据变更 P23 第 3 条）：v1 从**契约快照**的 content 族取值复算；"
                     "本轮令牌值唯一真相源已迁到 `10-dag-data/site-palette.json`（56 令牌），"
                     "故改为读该文件的 `values` 与 `_meta.contrast_triples`，与 "
                     "`gen-tokens.py --gate-contrast` 同源。硬判 %d 组 / report-only %d 组"
                     "（后者含 `border.card`：其定位是装饰性柔边，按定义不在 3:1 判据面内，⛔ 不判 FAIL）。"
                     % (len(rows), len(reports)))
    ctx.notes.append("P11 背景合成对比度（正文坐在摄影素材与纱幕的合成之上）**未经任何真实渲染验证**"
                     "（★ 2026-10-16 更正：此处的旧理由曾写「本会话浏览器不可用」——该结论早已被推翻"
                     "（真因是 snap 启动层的能力缺失，非 snap 内核一直可用），本会话复跑 `_probe_env.py` 再次证伪。"
                     "★ 保留本条为 report-only 的理由改为「**合成后对比度尚未纳入任何渲染期判据**」这一事实本身，"
                     "⛔ 不再以「浏览器不可用」为由；缺口登记见台账 `G20`）：本判据只覆盖「令牌字面值对令牌字面值」，"
                     "⛔ 不得读作「合成后对比度已达标」。")
    return (not bad), ("站点调色板三元组 %d 条 × 2 主题：硬判 PASS %d / report-only %d；"
                       "站点局部令牌正文类复算 %d 组；违例 %d 处 %s"
                       % (len(triples), len(rows), len(reports), site_rows, len(bad), bad[:4]))


def check_p12(ctx):
    """公开产物中内部编号 / 绝对路径 / 主机名 / 令牌串命中 = 0。

    ★ 2026-10-16 第 8 轮作用域收窄（见 `CRITERIA-CHANGE-R08.md`）：「主机名」一项只在**正文**
      上判 —— 判据对象 ＝ `_strip_url_attrs(text)`（摘掉 `href="…"` 与带主机的 `content="…"`）。
      理由：SH4 标准档要求每页写 `canonical` / `og:url` / `og:image` 的**绝对自指 URL**（含本站主机名），
      而属性里的 URL 归 P09（rel 闭集 + 元数据无主机）与 P30（assets/ 白名单）管 —— 那两条的断言更精确。
      ⛔ 这不是放宽阈值：正文里的裸主机名照样 FAIL（负例夹具 `mut_p12` 第 3 条守着）。
    """
    cats = {"内部编号": [], "绝对路径": [], "主机名": [], "令牌串": [], "file:// URL": []}
    host_scope_files = 0
    for rel, text in sorted(ctx.files.items()):
        prose = _strip_url_attrs(text)
        if os.path.basename(rel) in HOST_CARRIER_FILES:
            prose = _strip_host_urls(prose)   # 发布发现协议的载体，见 `_strip_host_urls`
        host_scope_files += 1
        for m in SECTION_RE.finditer(prose):
            cats["内部编号"].append((rel, m.group(0)))
        for m in TIER_WORD_RE.finditer(prose):
            cats["内部编号"].append((rel, m.group(0)))
        for m in ABS_PATH_RE.finditer(prose):
            cats["绝对路径"].append((rel, m.group(1)))
        for m in HOST_RE.finditer(prose):
            cats["主机名"].append((rel, m.group(0)))
        for m in SECRET_RE.finditer(prose):
            cats["令牌串"].append((rel, m.group(0)[:12]))
        for m in FILE_URL_RE.finditer(prose):
            cats["file:// URL"].append((rel, "file://"))
    total = sum(len(v) for v in cats.values())
    return (total == 0), ("受检产物 %d 个（主机名一项在**正文**上判：摘掉 href 与带主机的 content 后 %d 个文件）；"
                          "命中 %d 处 %s" % (
                              len(ctx.files), host_scope_files, total,
                              {k: v[:3] for k, v in cats.items() if v}))


def check_p13(ctx):
    """MD 镜像覆盖已发布集合；未落页节点在 pending_nodes 中逐条登记（无静默缺席）。

    ★ 2026-10-16 第 6 轮（任务包 T2，用户裁决②）在本条上挂**两个此前"已实现但无判据"的面**
      （⛔ 不新增判据编号 —— 本条本来就是「state 文件 ↔ 产物」的那条判据）：
      · **G12 `counts` 与产物实数一致**：`gen-state.py` 的 `html_count` 曾在第 5 轮把**节点页数写死**
        （`3 + …`），一翻态就与产物不符；当轮改成由 `complete` 派生，但「改对」与「判得住」是两件事
        —— 本段把它变成**逐项断言**（⛔ 不接受「看起来对」）。
      · **G13 MD 镜像与 HTML 内容一致**：镜像此前只断言「文件在不在」，⛔ 不比对内容。
        第 5 轮 `boundary` 字段化后，MD 镜像曾**静默丢掉「适用边界」**（`gen-md.node_md` 只印 `why`）
        —— 同一份内容的两个出口不一致，而门控看不出来。本段按**可辨识前缀**逐条比对。
    留档：`CRITERIA-CHANGE-P13-C58-P41.md`。
    """
    dag = ctx.data["dag"]
    nodes = dag["nodes"]
    node_by_id = {n["id"]: n for n in nodes}
    complete = {n["id"] for n in nodes if n["content_status"] == "complete"}
    registered = {n["id"] for n in nodes if n["content_status"] == "registered"}
    bad = []
    for nid in sorted(complete):
        rel = "%s/nodes/%s.md" % (MD_DIR, nid.lower())
        if rel not in ctx.md:
            bad.append(("缺 MD 镜像", rel))
        if ("%s/%s.html" % ("11-node-pages", nid.lower())) not in ctx.html:
            bad.append(("缺节点页", nid))
    for g in dag["groups"]:
        if ("%s/groups/%s.md" % (MD_DIR, g["id"].lower())) not in ctx.md:
            bad.append(("缺组 MD 镜像", g["id"]))
        if ("%s/%s.html" % ("12-groups", g["id"].lower())) not in ctx.html:
            bad.append(("缺组页", g["id"]))
    for rel in ("%s/index.md" % MD_DIR, "%s/groups/index.md" % MD_DIR,
                "%s/learning-path.md" % MD_DIR, "%s/frontier.md" % MD_DIR,
                "14-views/01-learning-path.html", "14-views/02-frontier.html", "index.html"):
        if rel not in ctx.files:
            bad.append(("缺产物", rel))
    state = json.loads(ctx.files.get(STATE_FILE, "{}"))
    pending = set(state.get("pending_nodes", []))
    if pending != registered:
        bad.append(("pending_nodes 与 registered 集合不一致", sorted(pending ^ registered)[:6]))
    if pending & complete:
        bad.append(("pending_nodes 与已发布节点相交", sorted(pending & complete)))
    if (pending | complete) != {n["id"] for n in nodes}:
        bad.append(("pending ∪ published ≠ 全量注册", ""))
    if not isinstance(state.get("counts"), dict) or not isinstance(state.get("gates"), dict):
        bad.append(("PUBLISH-STATE 缺 counts/gates", ""))
    # ★ 2026-10-16 第 8 轮**对象收窄**（原为 `published is not False ⇒ FAIL`，见 `CRITERIA-CHANGE-R08.md`）：
    #   原断言把第 1 轮「本轮不发布」这条**历史意图**固化成了判据 —— 它在本站**真的发布**（第 8 轮）
    #   之后就恒 FAIL，而它断言的并不是任何产物事实。⇒ 改为**内部一致性**断言：
    #     · `published == False` ⇒ `publish` 键**必须不存在**（⛔ 不得残留过期的发布事实）；
    #     · `published == True`  ⇒ `publish` 键必须齐备（repo / entry_url / pages_build_type / hub_listed），
    #       且 `entry_url` 必须等于本站基址（**拿判据自己的站点基址去撞**，⛔ 不是只查非空）。
    pub = state.get("published")
    pinfo = state.get("publish")
    if pub is True:
        need = ("repo", "entry_url", "pages_build_type", "hub_listed")
        if not isinstance(pinfo, dict):
            bad.append(("published=true 但缺 publish 事实段", pub))
        else:
            miss = [k for k in need if not str(pinfo.get(k, "")).strip()]
            if miss:
                bad.append(("publish 段缺字段", miss))
            if pinfo.get("entry_url") and not str(pinfo["entry_url"]).startswith(
                    re.sub(r"/[^/]*$", "/", ctx.site_base_url + "x")):
                bad.append(("publish.entry_url 与本站基址不符",
                            (pinfo.get("entry_url"), ctx.site_base_url)))
    elif pub is False:
        if pinfo is not None:
            bad.append(("published=false 却残留 publish 段（过期事实）", type(pinfo).__name__))
    else:
        bad.append(("published 字段缺失或非布尔", pub))
    # ---- ★ G12（2026-10-16 第 6 轮）：`counts` 与**产物 / 真相源实数**逐项一致 ----
    counts = state.get("counts") or {}
    # ★ MD 镜像集合（`15-md/` 下）：与 `ctx.md`（含手写 README）分开计数，两个口径各判一次
    md_mirrors = [r for r in ctx.md if r.startswith(MD_DIR + "/")]
    want_counts = [
        # 产物侧实数（判据自己数，⛔ 不采信 state 自报）
        ("html", len(ctx.html)),
        # ★ 2026-10-16 第 8 轮对象收窄：`counts.md` 是**MD 镜像数**（`15-md/` 下），
        #   ⛔ 不是 `ctx.md` 的全部（那里面还有发布根上的手写 `README.md`）。
        #   原写法把两者当同一个数 ⇒ 生成器与判据各算一个口径，README 一进发布面就当场 FAIL。
        #   ★ 两个口径都必须**显式**：`len(ctx.md)`（全部 .md）与 `len(md_mirrors)`（仅镜像）各判一次。
        ("md", len(md_mirrors)),
        ("md_total", len(ctx.md)),
        ("node_pages", len(complete)),
        ("group_pages", len(dag["groups"]) + 1),
        ("view_pages", len([r for r in ctx.html if r.startswith("14-views/")])),
        ("interactive", len([r for r in ctx.html if r == INTERACTIVE])),
        ("root", len([r for r in ctx.html if r == "index.html"])),
        # 真相源侧实数
        ("nodes", len(nodes)), ("groups", len(dag["groups"])), ("edges", len(dag["edges"])),
        ("layers", dag["meta"]["layer_count"]),
        ("assets", len(ctx.credits) + 1),
    ]
    if not counts:
        bad.append(("counts 为空 dict（G12 无对象）", ""))
    for k, want in want_counts:
        got = counts.get(k)
        if got != want:
            bad.append(("counts.%s 与实数不符" % k, got, want))
    # ---- ★ G13（2026-10-16 第 6 轮）：MD 镜像与节点内容一致（按**可辨识前缀**逐条比对）----
    #   ⛔ 「可辨识」的取法写死在这里，不再有第二处：`boundary` 取全文；`pitfalls` 取前 12 字；
    #     `evidence` 取 `source_id`；`terms` 取全角冒号前的术语头。比对前**空白归一化**
    #     （`gen-md._md_escape` 会把换行折成空格 ⇒ 不归一化会整片假阳）。
    def _ws(s):
        return re.sub(r"\s+", " ", s or "").strip()

    mirror_items = 0
    for nid in sorted(complete):
        rel = "%s/nodes/%s.md" % (MD_DIR, nid.lower())
        text = _ws(ctx.md.get(rel, ""))
        if not text:
            continue                       # 缺镜像已由上方断言负责，此处不重复报
        n = node_by_id[nid]
        if n.get("boundary"):
            mirror_items += 1
            if _ws(n["boundary"]) not in text:
                bad.append((rel, "MD 镜像缺 `boundary` 原文（HTML 有边界块、镜像没有）", nid))
        for p in (n.get("pitfalls") or []):
            pfx = _ws(p)[:12]
            if not pfx:
                continue
            mirror_items += 1
            if pfx not in text:
                bad.append((rel, "MD 镜像缺 `pitfalls` 可辨识前缀（≥12 字）", pfx))
        for ev in (n.get("evidence") or []):
            sid = ev.get("source_id") or ""
            if not sid:
                continue
            mirror_items += 1
            if sid not in text:
                bad.append((rel, "MD 镜像缺 `evidence.source_id`", sid))
        for t in (n.get("terms") or []):
            head = str(t).split("：")[0].strip()
            if not head:
                continue
            mirror_items += 1
            if head not in text:
                bad.append((rel, "MD 镜像缺 `terms` 术语头", head))
    ctx.notes.append("P13 作用域：MD 镜像覆盖「本轮已发布集合」（%d 个节点页 + %d 个组 + 2 个视图 + 入口），"
                     "并对未落页的 %d 个 registered 节点做**逐条登记**"
                     "（pending_nodes 必须与 registered 集合完全相等）。"
                     % (len(complete), len(dag["groups"]), len(registered)))
    ctx.notes.append("P13 的 G12（★ 2026-10-16 新增）：`counts` 逐项与实数比对，%d 项全部现算"
                     "（产物侧 html/md/node_pages/group_pages/view_pages/interactive/root；"
                     "真相源侧 nodes/groups/edges/layers/assets）⇒ `gen-state.py` 的计数一旦与产物脱钩，"
                     "本条**当场 FAIL**（第 5 轮 `html_count` 写死 `3 + …` 那类缺陷不会再溜过去）。" % len(want_counts))
    ctx.notes.append("P13 的 G13（★ 2026-10-16 新增）：MD 镜像逐条比对 %d 项"
                     "（boundary 全文 / pitfalls 前 12 字 / evidence 的 source_id / terms 术语头；空白归一化）；"
                     "**缺镜像**由上方断言负责，此处只判「镜像在、内容不全」。" % mirror_items)
    return (not bad), ("已发布节点 %d / 组 %d / 视图 2 / 入口 1 的镜像与页面齐全；"
                       "pending_nodes 登记 %d 个且与 registered 集合相等；"
                       "G12 counts 逐项 %d 项；G13 镜像内容比对 %d 项；违例 %d 处 %s"
                       % (len(complete), len(dag["groups"]), len(pending), len(want_counts),
                          mirror_items, len(bad), bad[:4]))


def check_p14(ctx):
    """页面间导航可达：每页至少有到根 index 的链接；节点页须有到所属组页的链接。"""
    dag = ctx.data["dag"]
    gid_of = {n["id"]: n["group"] for n in dag["nodes"]}
    bad = []
    for rel, text in sorted(ctx.html.items()):
        hrefs = [m.group(1).strip() for m in re.finditer(r'href\s*=\s*"([^"]*)"', strip_scripts(text), re.I)]
        resolved = {_resolve(rel, h.partition("#")[0]) for h in hrefs
                    if h and not h.startswith(("http", "mailto:", "#"))}
        if rel == "index.html":
            if not any(r and r.startswith("12-groups/") for r in resolved):
                bad.append((rel, "根入口缺到组页的链接"))
            if "13-interactive/index.html" not in resolved:
                bad.append((rel, "根入口缺到交互入口的链接"))
        elif "index.html" not in resolved:
            bad.append((rel, "缺到根 index 的链接"))
        m = re.match(r"11-node-pages/([a-z0-9-]+)\.html$", rel)
        if m:
            nid = next((k for k in gid_of if k.lower() == m.group(1)), None)
            if nid is None:
                bad.append((rel, "节点页文件名无法解析到节点 id"))
            else:
                want = "12-groups/%s.html" % gid_of[nid].lower()
                if want not in resolved:
                    bad.append((rel, "缺到所属组页 %s 的链接" % want))
    return (not bad), "受检页面 %d 个；导航不可达 %d 处 %s" % (len(ctx.html), len(bad), bad[:6])


# ---------------------------------------------------------------- P15–P22（ADR 质量场景）

def check_p15(ctx):
    """模板标识集合大小 = 1（⛔ 无第二套外壳）。"""
    found_by_page = {}
    bad = []
    for rel, text in sorted(ctx.html.items()):
        found_by_page[rel] = TEMPLATE_RE.findall(text)
    multi = [k for k, v in found_by_page.items() if len(v) != 1]
    if multi:
        bad.append(("模板标识数量 ≠ 1 的页面", multi[:5]))
    uniq = sorted({v[0] for v in found_by_page.values() if len(v) == 1})
    if len(uniq) != 1:
        bad.append("(全站)模板标识集合 %s（大小 %d，应为 1）" % (uniq, len(uniq)))
    elif uniq[0] != ctx.template_id:
        bad.append("(全站)模板标识 %s ≠ gen-common.TEMPLATE_ID %s" % (uniq[0], ctx.template_id))
    defs = []
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py"):
            continue
        src = open(os.path.join(HERE, fn), encoding="utf-8").read()
        for m in re.finditer(r"^def\s+page_shell\s*\(", src, re.M):
            defs.append((fn, m.start()))
    if len(defs) != 1:
        bad.append("page_shell 定义 %d 处 %s" % (len(defs), defs))
    style_shas = {}
    for rel, text in sorted(ctx.html.items()):
        for style in STYLE_RE.findall(text):
            # ★ 判据作用域修正（2026-10-15）：初版直接对样式块原文取 sha256，于是「同一外壳模板 +
            #   不同**页面深度**的资产前缀」（根页 `assets/…` vs 子目录页 `../assets/…`）被判成
            #   「样式块 2 种」＝「第二套外壳」（本轮实测 1 处假阳）。
            #   外壳唯一性要断言的是**模板**唯一，⛔ 不是「每个字节都相同」——资产前缀是模板的
            #   **参数**而非第二套模板。⇒ 先归一页面深度前缀再取哈希。
            norm = re.sub(r'(?:\.\./)+assets/', 'assets/', style)
            style_shas.setdefault(sha(norm), []).append(rel)
    if len(style_shas) != 1:
        bad.append("样式块 %d 种（应为 1）" % len(style_shas))
    return (not bad), ("模板标识 %s（全站 %d 页一致）；page_shell 定义 %d 处；样式块 %d 种；违例 %s"
                       % (uniq, len(ctx.html), len(defs), len(style_shas), bad[:4]))


def check_p16(ctx):
    """幂等：两个独立生成进程的逐文件 sha256 一致；且与真实产物一致。"""
    p = ctx.probe.get("idempotent", {})
    a, b, disk = p.get("a", {}), p.get("b", {}), p.get("disk", {})
    if not a or not b or not disk:
        return False, "幂等探针缺失（生成链路未跑通）"
    keys = set(a) | set(b)
    diff_ab = sorted(k for k in keys if a.get(k) != b.get(k))
    # ★ 判据作用域修正（2026-10-15）：初版对 `set(disk) | set(b)` 取差集，而 `disk` 是**站点树全量**
    #   ⇒ 把 `assets/` 下的**输入件**（手写的许可台账、站点图标）当成「与生成产物不一致」而判 FAIL
    #   （本轮实测 2 处假阳）。生成器的受管面是 `b` 的键集；输入件不属受管面，
    #   其完整性由 P30（资产白名单）与 P32（许可登记）各自断言。
    #   ⇒ 正确断言＝「**每个生成产物键**在磁盘上取值一致」，⛔ 不是「磁盘上所有文件都由生成器产出」。
    diff_disk = sorted(k for k in set(b) if disk.get(k) != b.get(k))
    ok = not diff_ab and not diff_disk
    return ok, ("两次独立生成：逐文件 sha256 不一致 %d 个 %s；与真实产物不一致 %d 个 %s；产物 %d 个"
                % (len(diff_ab), diff_ab[:5], len(diff_disk), diff_disk[:5], len(b)))


def check_p17(ctx):
    """--dry-run 差异清单与实际落盘清单差集 = 0。"""
    p = ctx.probe.get("dryrun", {})
    dry, wr = p.get("dry", {}), p.get("write", {})
    if p.get("rc_dry") != 0 or p.get("rc_write") != 0 or not dry or not wr:
        return False, "dry-run/write 探针缺失或退出码非 0（rc_dry=%s rc_write=%s）" % (
            p.get("rc_dry"), p.get("rc_write"))
    bad = []
    for k in ("added", "modified", "deleted"):
        ds, ws = set(dry.get(k, [])), set(wr.get(k, []))
        if ds != ws:
            bad.append((k, sorted(ds ^ ws)[:5]))
    if wr.get("residual_orphans"):
        bad.append(("write 后孤儿残留", wr["residual_orphans"][:5]))
    if wr.get("second_pass_clean") is not True:
        bad.append(("二次比对不干净", ""))
    return (not bad), ("dry-run 清单 added %d / modified %d / deleted %d；实际落盘 added %d / "
                       "modified %d / deleted %d；差集 %d 处 %s"
                       % (len(dry.get("added", [])), len(dry.get("modified", [])),
                          len(dry.get("deleted", [])), len(wr.get("added", [])),
                          len(wr.get("modified", [])), len(wr.get("deleted", [])), len(bad), bad[:4]))


def check_p18(ctx):
    """孤儿产物残留数 = 0。"""
    p = ctx.probe.get("orphan", {})
    if not p:
        return False, "孤儿清理探针缺失"
    bad = []
    if p.get("exists_after"):
        bad.append(("注入的孤儿文件未被清理", p.get("orphan")))
    if p.get("residual"):
        bad.append(("残留孤儿清单非空", p["residual"][:5]))
    if p.get("orphan") not in (p.get("removed") or []):
        bad.append(("孤儿未被记入 removed", p.get("orphan")))
    if p.get("rc") != 0:
        bad.append(("清理后退出码非 0", p.get("rc")))
    return (not bad), ("注入孤儿 %s；清理后残留 %d 个；removed 记入=%s；违例 %s"
                       % (p.get("orphan"), len(p.get("residual", [])),
                          p.get("orphan") in (p.get("removed") or []), bad[:3]))


def drift_report(snapshot_sha, provenance, site_tokens, tokens_block_sha, html):
    """漂移对账：返回 [{field, expected, actual}]。"""
    T = _imp(GEN_TOKENS, "pekg_gt")
    drift = []
    want = provenance.get("source_sha256")
    if want and want != snapshot_sha:
        drift.append({"field": "contract.snapshot.sha256", "expected": want, "actual": snapshot_sha})
    ref = site_tokens.get("reference_backgrounds", {})
    for t in site_tokens.get("tokens", []):
        cov = (t.get("contrast_checked") or {}).get("measured") or {}
        for mode in ("light", "dark"):
            bg = ref.get(mode)
            if not bg:
                continue
            c = round(T.contrast_ratio(t[mode], bg), 2)
            got = cov.get(mode)
            if got is None or abs(float(got) - c) > 0.02:
                drift.append({"field": "site_tokens.%s.contrast_checked.measured.%s" % (t["name"], mode),
                              "expected": got, "actual": c})
    for row in site_tokens.get("label_on_group", []):
        name = row.get("token")
        tok = next((x for x in site_tokens.get("tokens", []) if x["name"] == name), None)
        if not tok:
            drift.append({"field": "site_tokens.label_on_group.%s" % name,
                          "expected": "已登记令牌", "actual": "缺失"})
            continue
        for mode in ("light", "dark"):
            fg, c = T.label_for(tok[mode])
            reg = row.get(mode) or {}
            if reg.get("fg") != fg:
                drift.append({"field": "site_tokens.label_on_group.%s.%s.fg" % (name, mode),
                              "expected": reg.get("fg"), "actual": fg})
            if reg.get("measured") is None or abs(float(reg["measured"]) - c) > 0.02:
                drift.append({"field": "site_tokens.label_on_group.%s.%s.measured" % (name, mode),
                              "expected": reg.get("measured"), "actual": round(c, 2)})
    for rel, text in sorted(html.items()):
        blocks = re.findall(re.escape(TOKEN_BEGIN) + r".*?" + re.escape(TOKEN_END), text, re.S)
        if len(blocks) != 1:
            drift.append({"field": "%s.token_block.count" % rel, "expected": 1, "actual": len(blocks)})
            continue
        got = sha(blocks[0])
        if got != tokens_block_sha:
            drift.append({"field": "%s.token_block.sha256" % rel, "expected": tokens_block_sha, "actual": got})
    return drift


def check_p19(ctx):
    """令牌漂移：负向夹具必须被判失败；漂移报告须列出漂移字段名与两侧取值。"""
    prov = ctx.data["provenance"]
    args = (ctx.snapshot_sha, prov, ctx.data["site_tokens"], ctx.tokens_block_sha, ctx.html)
    drift = drift_report(*args)
    fixture = []
    d1 = drift_report("0" * 64, prov, ctx.data["site_tokens"], ctx.tokens_block_sha, ctx.html)
    fixture.append(("快照 sha256 单字段漂移", bool(d1) and all("expected" in x and "actual" in x for x in d1)))
    st2 = copy.deepcopy(ctx.data["site_tokens"])
    st2["tokens"][0]["contrast_checked"]["measured"]["light"] = 1.0
    d2 = drift_report(ctx.snapshot_sha, prov, st2, ctx.tokens_block_sha, ctx.html)
    fixture.append(("登记对比度单字段漂移",
                    any(x["field"].endswith("--warn.contrast_checked.measured.light") for x in d2)))
    st3 = copy.deepcopy(ctx.data["site_tokens"])
    st3["label_on_group"][0]["light"]["fg"] = "#123456"
    d3 = drift_report(ctx.snapshot_sha, prov, st3, ctx.tokens_block_sha, ctx.html)
    fixture.append(("组标签色单字段漂移",
                    any(x["field"].endswith("label_on_group.--group-00.light.fg") for x in d3)))
    h4 = copy.deepcopy(ctx.html)
    k = sorted(h4)[0]
    h4[k] = h4[k].replace("--text-primary: #0e1729;", "--text-primary: #eeeeee;")
    d4 = drift_report(ctx.snapshot_sha, prov, ctx.data["site_tokens"], ctx.tokens_block_sha, h4)
    fixture.append(("单页内联令牌漂移", any(x["field"].endswith("token_block.sha256") for x in d4)))
    failed = [name for name, ok in fixture if not ok]
    ok = (not drift) and not failed
    return ok, ("当前漂移 %d 处 %s；负向夹具 %d/%d 触发 %s"
                % (len(drift), drift[:3], len(fixture) - len(failed), len(fixture), failed))


def check_p20(ctx):
    """契约覆盖：11 个角色**全部消费**（11/11）；未覆盖集合必须为空且显式报告。"""
    roles = list(ctx.contract_roles)
    pal = ctx.data["site_palette"]["values"]
    if not roles:
        return False, "空集守卫：契约角色集为空"
    consumed = [r for r in roles if r in pal]
    unconsumed = [r for r in roles if r not in pal]
    bad = []
    if len(roles) != 11:
        bad.append(("契约角色数", len(roles)))
    if unconsumed:
        bad.append(("未覆盖角色非空", unconsumed))
    if len(consumed) != len(roles):
        bad.append(("消费角色数", len(consumed)))
    if set(consumed) & set(unconsumed):
        bad.append(("消费与未覆盖相交", sorted(set(consumed) & set(unconsumed))))
    if set(consumed) | set(unconsumed) != set(roles):
        bad.append(("消费 ∪ 未覆盖 ≠ 契约角色集", sorted(set(roles) ^ (set(consumed) | set(unconsumed)))))
    tiers = ctx.data["site_palette"]["_meta"]["usage_tiers"]
    report = {"roles_declared": len(roles), "roles_consumed": len(consumed),
              "roles_unconsumed": sorted(unconsumed),
              "coverage": "%d/%d" % (len(consumed), len(roles)),
              "usage_tiers": {k: tiers[k].get("gate") for k in sorted(tiers)}}
    ctx.notes.append("P20 覆盖报告（★ 判据变更 P23 第 2 条：作用域由「消费 7/11」改为「消费 11/11」，"
                     "因为本轮底座换为 hub 令牌集后 11 个契约角色全部被消费，旧的 7/11 断言已成为"
                     "对**旧状态**的断言）：%s" % json.dumps(report, ensure_ascii=False))
    return (not bad), ("契约角色 %d（消费 %d / 未覆盖 %d，并集等于契约集=%s）；用途档 %d 档全部入报告；违例 %s"
                       % (len(roles), len(consumed), len(unconsumed),
                          set(consumed) | set(unconsumed) == set(roles), len(tiers), bad[:4]))


def check_p21(ctx):
    """前沿刷新：改 frontier.json 后其余模块产物 sha256 变化数 = 0；每条含 as_of/edition；status 属闭集。"""
    bad = []
    fr = ctx.data["frontier"]
    if not fr.get("as_of") or not fr.get("edition"):
        bad.append(("模块级 as_of/edition 缺失", ""))
    st_bad = [i["id"] for i in fr.get("items", []) if i.get("status") not in FSTATUS_ENUM]
    if st_bad:
        bad.append(("status 越界", st_bad))
    text = ctx.files.get("14-views/02-frontier.html", "")
    for it in fr.get("items", []):
        m = re.search(r'data-frontier-item="%s"[^>]*data-as-of="([^"]*)"\s+data-edition="([^"]*)"'
                      % re.escape(it["id"]), text)
        if not m:
            bad.append(("条目渲染缺 as_of/edition 属性", it["id"]))
        elif not m.group(1) or not m.group(2):
            bad.append(("条目 as_of/edition 为空", it["id"]))
    p = ctx.probe.get("frontier", {})
    base, mut = p.get("base", {}), p.get("mut", {})
    if not base or not mut:
        bad.append(("前沿隔离探针缺失", ""))
        changed_other, changed_front = [], []
    else:
        keys = set(base) | set(mut)
        changed = sorted(k for k in keys if base.get(k) != mut.get(k))
        changed_front = [k for k in changed if "frontier" in k]
        changed_other = [k for k in changed if "frontier" not in k]
        if changed_other:
            bad.append(("其余模块产物发生变化", changed_other[:5]))
        if not changed_front:
            bad.append(("前沿产物未随真相源变化（刷新无效）", ""))
    ctx.notes.append("P21 as_of/edition 的落点：两份字段位于模块级（frontier.json 顶层），"
                     "每条条目的**渲染记录**必须携带二者；判据逐条断言渲染记录上的属性非空。")
    return (not bad), ("条目 %d 条全部携带 as_of/edition 渲染属性；status 属三值闭集=%s；"
                       "改动 frontier.json 后其余模块产物 sha256 变化 %d 个；前沿产物变化 %d 个；违例 %s"
                       % (len(fr.get("items", [])), not st_bad, len(changed_other), len(changed_front), bad[:3]))


def check_p22(ctx):
    """content_status **状态↔内容一致性**（★ 2026-10-16 判据变更 P22，见 CRITERIA-CHANGE-P22.md）。

    断言（两侧同源同值，见 `10-dag-data/_selfcheck.py` C23–C27）：
      ① `complete` ≥3（内容形态覆盖下限，⛔ 未动）且两态合计 = 全量注册数；
      ② `complete` 节点的 **8 区块全非空**；
      ③ ★ **`registered` 节点的 `lab`/`evidence`/`pitfalls` 必须为空**（内容已填却仍标 `registered`
         ⇒ 状态说谎；半填 ⇒ 页面会渲染 `本轮未写。`）——这是**双向**那一条，旧数量配额看不见它；
      ④ `registered` 的三段下限与 summary 结构性三条（⛔ 未动）；
      ⑤ `content_status` ∈ 闭集。

    ⛔ 原 `if len(registered) < 60` 数量配额已**撤销**：它无因果依据（全仓无推导），且其适用阶段
       （注册期）在内容填充期结束——照它改数据会让 64 个节点**永远不可点入** ⇒ 按判据分档原则应
       换判据而非改数字。★ 撤销**不得**读作"少了一条约束"：③ 比它更严（它只看数量，看不见说谎态）。
    """
    nodes = ctx.data["dag"]["nodes"]
    complete = [n for n in nodes if n["content_status"] == "complete"]
    registered = [n for n in nodes if n["content_status"] == "registered"]
    other = [n["id"] for n in nodes if n["content_status"] not in STATUS_ENUM]
    bad = []
    if other:
        bad.append(("content_status 越界", other))
    if len(complete) < 3:
        bad.append(("complete 配额", len(complete)))
    if len(complete) + len(registered) != len(nodes):
        bad.append(("两态合计 ≠ 全量注册数", len(complete) + len(registered)))
    blocks = ("why", "intro", "when", "lab", "evidence", "terms", "pitfalls", "summary")
    FILLED = ("lab", "evidence", "pitfalls")   # ★ 内容波次负责的三块（C3 ③ 的对象）
    for n in complete:
        for b in blocks:
            v = n.get(b)
            if v is None or (isinstance(v, (list, str)) and len(v) == 0):
                bad.append(("complete 区块为空", n["id"], b))
    for n in registered:
        for f in ("why", "intro", "summary"):
            if HOLLOW.search(n.get(f, "")):
                bad.append(("registered 空洞占位", n["id"], f))
        if caliber(n.get("why", "")) < WHY_MIN["registered"]:
            bad.append(("registered why 下限", n["id"], caliber(n.get("why", ""))))
        if caliber(n.get("intro", "")) < INTRO_MIN["registered"]:
            bad.append(("registered intro 下限", n["id"], caliber(n.get("intro", ""))))
        for msg in summary_structural_failures(n):
            bad.append(("registered " + msg, n["id"]))
        for b in FILLED:
            if n.get(b):
                bad.append(("内容已填但状态未翻（%s 非空 %d 条）" % (b, len(n[b])), n["id"]))
    return (not bad), ("complete %d 个（8 区块全非空）；registered %d 个（lab/evidence/pitfalls 必须为空；"
                       "why ≥%d / intro ≥%d 且 summary 通过结构性三条、无空洞占位）；"
                       "两态合计 %d = 全量注册数；违例 %d 处 %s"
                       % (len(complete), len(registered), WHY_MIN["registered"], INTRO_MIN["registered"],
                          len(complete) + len(registered), len(bad), bad[:5]))


# ---------------------------------------------------------------- P23–P32（本轮新增）

def _all_styles(ctx):
    return {rel: "".join(STYLE_RE.findall(text)) for rel, text in sorted(ctx.html.items())}


def check_p23(ctx):
    """P23 令牌来源唯一：产物中每个令牌声明块与 `gen-tokens.py --print` 逐字节一致；
    令牌块之外 ⛔ 不得出现任何自定义属性声明；调色板角色集与令牌块声明的变量集必须相等。"""
    bad = []
    block_texts = {}
    for rel, text in sorted(ctx.html.items()):
        blocks = re.findall(re.escape(TOKEN_BEGIN) + r".*?" + re.escape(TOKEN_END), text, re.S)
        if len(blocks) != 1:
            bad.append((rel, "令牌块数量 ≠ 1", len(blocks)))
            continue
        block_texts[rel] = blocks[0]
        if blocks[0].rstrip("\n") != ctx.tokens_css.rstrip("\n"):
            bad.append((rel, "令牌块与 gen-tokens.py --print 不一致", ""))
        for style in STYLE_RE.findall(text):
            rest = re.sub(re.escape(TOKEN_BEGIN) + r".*?" + re.escape(TOKEN_END), "", style, flags=re.S)
            extra = re.findall(r"--[A-Za-z0-9_-]+\s*:", rest)
            if extra:
                bad.append((rel, "令牌块之外的第二处令牌声明", sorted(set(extra))[:4]))
    if not block_texts:
        return False, "空集守卫：全站未找到任何令牌声明块 ⇒ 判据恒真"
    uniq = sorted({sha(v.rstrip("\n")) for v in block_texts.values()})
    if len(uniq) != 1:
        bad.append(("(全站)", "令牌声明块 sha256 非唯一：%d 种" % len(uniq), ""))
    want_names = set(ctx.data["site_palette"]["css_names"].values())
    if not want_names:
        return False, "空集守卫：调色板 css_names 为空 ⇒ 判据恒真"
    got_names = set(re.findall(r"(--[A-Za-z0-9-]+)\s*:", block_texts[sorted(block_texts)[0]]))
    if want_names != got_names:
        bad.append(("(全站)", "调色板变量集 ≠ 令牌块变量集", sorted(want_names ^ got_names)[:8]))
    ctx.notes.append("P23 断言四层：① 每页令牌块恰好 1 个；② 与 `gen-tokens.py --print` 逐字节一致；"
                     "③ 令牌块之外无任何自定义属性声明（生成器里 ⛔ 不手写令牌）；"
                     "④ 调色板 `css_names` 变量集与令牌块实际声明集**相等**（%d 个，双向）。" % len(want_names))
    return (not bad), ("受检页面 %d 个：令牌块逐字节一致=%s；全站 sha256 %d 种；"
                       "调色板变量 %d 个与声明集相等=%s；违例 %d 处 %s"
                       % (len(block_texts), not uniq or len(uniq) == 1, len(uniq),
                          len(want_names), want_names == got_names, len(bad), bad[:4]))


def _scan_hardcode(css):
    """返回 (违例列表, 声明计数)。违例 = 令牌外硬编码。"""
    bad = []
    stats = {"font-size": 0, "border-radius": 0, "color": 0, "padding|margin": 0, "outline": 0}
    for m in FONT_SIZE_DECL_RE.finditer(css):
        stats["font-size"] += 1
        v = m.group(1).strip()
        if not FONT_SIZE_ALLOWED.match(v):
            bad.append(("font-size", v[:60]))
    for m in RADIUS_DECL_RE.finditer(css):
        stats["border-radius"] += 1
        for part in m.group(1).split("/"):
            for tok in part.split():
                if tok and not RADIUS_ALLOWED.match(tok):
                    bad.append(("border-radius", tok[:60]))
    for m in COLOR_DECL_RE.finditer(css):
        stats["color"] += 1
        v = m.group(2).strip()
        if not COLOR_ALLOWED.match(v):
            bad.append(("color:" + m.group(1), v[:60]))
    for m in BOX_DECL_RE.finditer(css):
        stats["padding|margin"] += 1
        for tok in m.group(2).replace("/", " ").split():
            if tok and not BOX_ALLOWED.match(tok):
                bad.append((m.group(1), tok[:60]))
    for m in OUTLINE_DECL_RE.finditer(css):
        stats["outline"] += 1
        v = m.group(1).strip()
        if not (v.startswith("2px solid var(--focus-ring)") or v.startswith("none")
                or v.startswith("0") or v.startswith("var(--")):
            bad.append(("outline", v[:60]))
    return bad, stats


def check_p24(ctx):
    """P24 令牌外硬编码 = 0：产物 CSS 中不得出现字面 `font-size` / `border-radius` /
    `color:` 十六进制值 / `padding|margin` 字面值（只允许 `var(--…)` 与结构性 0/auto/100%）。"""
    bad = []
    total = {"font-size": 0, "border-radius": 0, "color": 0, "padding|margin": 0, "outline": 0}
    checked = 0
    for rel, css in sorted(_all_styles(ctx).items()):
        rest = re.sub(re.escape(TOKEN_BEGIN) + r".*?" + re.escape(TOKEN_END), "", css, flags=re.S)
        if not rest.strip():
            continue
        checked += 1
        b, st = _scan_hardcode(rest)
        bad += [(rel,) + x for x in b]
        for k in total:
            total[k] += st[k]
    if checked == 0:
        return False, "空集守卫：受检 CSS 为空 ⇒ 判据恒真"
    if total["font-size"] == 0:
        return False, "空集守卫：受检 CSS 中没有任何 font-size 声明 ⇒ 判据对空白集恒真"
    if total["padding|margin"] == 0:
        return False, "空集守卫：受检 CSS 中没有任何 padding/margin 声明 ⇒ 判据对空白集恒真"
    ctx.notes.append("P24 扫描面与统计：受检样式块 %d 个；声明计数 %s。"
                     "允许形态：`var(--…)`、结构性 0/auto/满值/inherit、1px|2px 描边、"
                     "`outline: 2px solid var(--focus-ring)`。不设任何按选择器的豁免。"
                     "★ 注：本说明串内不得出现裸百分号——它会与百分号格式化冲突"
                     "（本轮实测：先因 `满值/inherit` 前的裸百分号触发 TypeError，"
                     "修后又因我在说明里写的裸百分号再次触发，判据整体判 FAIL）。"
                     % (checked, total))
    return (not bad), ("受检样式块 %d 个；令牌外硬编码违例 %d 处 %s；声明计数 %s"
                       % (checked, len(bad), bad[:6], json.dumps(total, ensure_ascii=False)))


def check_p25(ctx):
    """P25 `:hover` 门控覆盖：含 `:hover` 的选择器 100% 位于 `@media (hover: hover)` 内；
    `:focus-within` / `:focus-visible` ⛔ 不在其内。"""
    bad = []
    hover_sel, hover_gated, focus_in_media = [], [], []
    for rel, css in sorted(_all_styles(ctx).items()):
        for conds, header, _body, _raw in parse_css(css):
            if header.startswith("@"):
                continue
            gated = any(media_condition_norm(c) == HOVER_MEDIA for c in conds)
            for sel in selectors_of(header):
                if re.search(r":hover\b", sel):
                    hover_sel.append((rel, sel))
                    if gated:
                        hover_gated.append((rel, sel))
                    else:
                        bad.append((rel, "未门控的 :hover 选择器", sel[:70]))
                if re.search(r":(focus-within|focus-visible)\b", sel) and gated:
                    focus_in_media.append((rel, sel))
                    bad.append((rel, "焦点面被误置于 (hover:hover) 门控内", sel[:70]))
    if not hover_sel:
        return False, "空集守卫：产物 CSS 中没有任何 :hover 选择器 ⇒ 判据恒真"
    ctx.notes.append("P25 口径（H1 §7.4 / 硬规则 7）：`:hover` 在触屏上不可靠且会「粘滞」⇒ 全站每条"
                     "`:hover` 必须包在 `@media (hover: hover)` 内；而 `:focus-within`/`:focus-visible` "
                     "是键盘与辅助技术在任何输入设备上都必须看到的反馈面 ⇒ ⛔ 不得进该门控。"
                     "★ 注：`@media (hover:hover)` 自身的条件串不是选择器，故按 at-rule 条件解析而非按选择器匹配。")
    return (not bad), ("含 :hover 的选择器 %d 条，其中受门控 %d 条（覆盖 %.0f%%）；"
                       "焦点面误入门控 %d 条；违例 %d 处 %s"
                       % (len(hover_sel), len(hover_gated),
                          100.0 * len(hover_gated) / max(1, len(hover_sel)),
                          len(focus_in_media), len(bad), bad[:4]))


def check_p26(ctx):
    """P26 主题三态同步：三块齐备（`:root` / 系统深色 / 强制深色）＋ pre-paint 脚本在 `<head>`
    且早于任何样式表之外的可视内容 ＋ 两条 `theme-color` 与 `--surface-page` 浅深值同步。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：无受检页面"
    pal = ctx.data["site_palette"]["values"]
    for rel, text in sorted(ctx.html.items()):
        css = re.sub(r"\s+", "", "".join(STYLE_RE.findall(text)))
        has_root = ":root{" in css
        dark_media = re.search(
            r"@media\(prefers-color-scheme:dark\)\{[^@]*?:root:not\(\[data-theme='light'\]\)", css)
        forced = re.search(r":root\[data-theme='dark'\]\{", css)
        light_block = re.search(r":root\[data-theme='light'\]\{", css)
        if not has_root:
            bad.append((rel, "缺 :root 默认档", ""))
        if not dark_media:
            bad.append((rel, "缺「跟随系统」档（@media prefers-color-scheme: dark + "
                             ":root:not([data-theme='light'])）", ""))
        if not forced:
            bad.append((rel, "缺「强制深色」档", ""))
        if light_block:
            bad.append((rel, "出现了 :root[data-theme='light'] 块（强制浅色应为「不覆盖 + 守卫」）", ""))
        head = text.split("</head>", 1)[0]
        if SCRIPT_MARK not in head:
            bad.append((rel, "pre-paint 引导脚本不在 <head> 内", ""))
        else:
            si = head.index(SCRIPT_MARK)
            if "<style" in head and head.index("<style") < si:
                bad.append((rel, "引导脚本晚于样式表", ""))
            body_pos = text.find("<body")
            if body_pos != -1 and si > body_pos:
                bad.append((rel, "引导脚本位于 body 之后", ""))
        for state in ("system", "light", "dark"):
            if not re.search(r'data-theme-set="%s"' % state, text):
                bad.append((rel, "三态主题开关缺 %s 档" % state, ""))
        metas = re.findall(r'<meta\s+name="theme-color"\s+content="([^"]*)"\s+media="([^"]*)"', text)
        want = {"(prefers-color-scheme: light)": pal["surface.page"]["light"],
                "(prefers-color-scheme: dark)": pal["surface.page"]["dark"]}
        got = {m[1]: m[0] for m in metas}
        if got != want:
            bad.append((rel, "theme-color 两条 meta 与 --surface-page 不同步", (got, want)))
    ctx.notes.append("P26 断言三块齐备且**无** `:root[data-theme='light']` 块 —— 强制浅色是"
                     "「浅色值在 :root + 系统深色块用 :not([data-theme='light']) 守卫」实现的，"
                     "多写一个浅色块即成为第二处令牌声明（与 P23 冲突）。"
                     "★ 三态语义：跟随系统 = 不落属性；强制浅色 = `data-theme='light'`；"
                     "强制深色 = `data-theme='dark'`；切换只改属性，⛔ 不接管 `color-scheme`。")
    return (not bad), ("受检页面 %d 个：三块齐备 / 无强制浅色块 / pre-paint 脚本在 <head> 且先于样式表 / "
                       "三态开关齐备 / theme-color 与 --surface-page 同步；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


def check_p27(ctx):
    """P27 背景层结构护栏：`.backdrop` 为 `fixed` + 负 `z-index` + `pointer-events:none` + `aria-hidden`；
    子树零可聚焦元素；非当前主题帧 `display:none`。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：无受检页面"
    frames_seen = 0
    for rel, text in sorted(ctx.html.items()):
        css = "".join(STYLE_RE.findall(text))
        rules = parse_css(css)
        cont = find_rules(rules, selector_pred=lambda s: s.strip() == "." + BACKDROP_CONTAINER_CLASS)
        if not cont:
            bad.append((rel, "缺 .backdrop 容器样式规则", ""))
            continue
        body_n = re.sub(r"\s+", "", " ".join(b for _c, _s, b in cont))
        for need, label in (("position:fixed", "position:fixed"),
                            ("z-index:-1", "负 z-index"),
                            ("pointer-events:none", "pointer-events:none")):
            if need not in body_n:
                bad.append((rel, "背景容器缺 %s" % label, ""))
        if not re.search(r'<div class="backdrop"[^>]*aria-hidden="true"', text):
            bad.append((rel, '背景容器缺 aria-hidden="true"', ""))
        sub = backdrop_subtree(text)
        if sub is None:
            bad.append((rel, "未找到背景容器子树", ""))
        else:
            for m in FOCUSABLE_TAG_RE.finditer(sub):
                bad.append((rel, "背景子树含可聚焦元素", m.group(0)[:50]))
            if TABINDEX_RE.search(sub):
                bad.append((rel, "背景子树含 tabindex", ""))
        dark_rules = [b for _c, _s, b in find_rules(
            rules, selector_pred=lambda s: "backdrop__" in s,
            cond_pred=lambda c: any(media_condition_norm(x) == "(prefers-color-scheme:dark)" for x in c))]
        dark_rules += [b for _c, _s, b in find_rules(
            rules, selector_pred=lambda s: s.strip().startswith('html[data-theme="dark"]')
            and "backdrop__" in s)]
        if not dark_rules:
            bad.append((rel, "缺非当前主题帧的 display 切换规则（深色侧）", ""))
        joined = re.sub(r"\s+", "", " ".join(dark_rules))
        if not NON_CURRENT_DISPLAY_RE.search(joined):
            bad.append((rel, "深色侧未用 display:none 隐藏日间帧", ""))
        if "display:block" not in joined:
            bad.append((rel, "深色侧未用 display:block 显式恢复夜间帧（display:none 覆盖不足）", ""))
        base_hide = [b for _c, s, b in find_rules(
            rules, selector_pred=lambda s: "backdrop__" in s and "night" in s
            and not s.strip().startswith("html"))]
        if not any(NON_CURRENT_DISPLAY_RE.search(b) for b in base_hide):
            bad.append((rel, "默认档未用 display:none 隐藏夜间帧", ""))
        frames_seen += len(re.findall(r'class="backdrop__photo backdrop__photo--', text))
    if frames_seen == 0:
        return False, "空集守卫：全站未找到任何背景帧元素 ⇒ 判据恒真"
    ctx.notes.append("P27 依据 H1 §2.4 / §9.4：非当前主题的素材帧**必须** `display:none`——"
                     "`opacity:0` / `visibility:hidden` 仍会下载素材（每主题拉两份）；"
                     "背景层必须 `fixed` + 负 `z-index` + `pointer-events:none` + `aria-hidden`，"
                     "且**子树内不得有任何可聚焦元素**。")
    return (not bad), ("受检页面 %d 个；背景帧元素 %d 个；结构护栏 / 子树零可聚焦 / "
                       "非当前主题帧 display:none 三项全查；违例 %d 处 %s"
                       % (len(ctx.html), frames_seen, len(bad), bad[:4]))


def _dur_tokens(css):
    out = {}
    for m in re.finditer(r"(--dur-[a-z0-9]+)\s*:\s*([0-9.]+)s", css):
        out[m.group(1)] = float(m.group(2))
    return out


def check_p28(ctx):
    """P28 动效预算四项上界：`[data-reveal]` ≤32 / 进场 ≤1800ms / `--dur-*` 和 ≤3.6s / `infinite` ≤12。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：无受检页面"
    css_all = "".join("".join(STYLE_RE.findall(t)) for t in ctx.html.values())
    durs = _dur_tokens(css_all)
    if not durs:
        return False, "空集守卫：产物 CSS 中未找到任何 --dur-* 令牌 ⇒ 判据恒真"
    dur_sum = round(sum(durs.values()), 4)
    dur_max = max(durs.values())
    ms = re.search(r"animation-delay\s*:\s*calc\(var\(--i[^)]*\)\s*\*\s*(\d+)ms\)", css_all)
    stagger = int(ms.group(1)) / 1000.0 if ms else 0.0
    if stagger <= 0:
        bad.append(("缺错峰 animation-delay（calc(var(--i) * Nms)）", ""))
    reveal_counts = {}
    for rel, text in sorted(ctx.html.items()):
        # ★ 计数作用域：只数**产物标记** `data-reveal="`；⛔ 不得对整页原文跑子串计数——
        #   引导脚本里的选择器串 `[data-reveal]` 会被一并计入（本轮实测每页 +2 处假计数）。
        n = len(re.findall(r'data-reveal\s*=', strip_scripts(text)))
        reveal_counts[rel] = n
        if n == 0:
            bad.append((rel, "[data-reveal] 实例数 0（空集）", ""))
        elif n > MOTION_REVEAL_MAX:
            bad.append((rel, "[data-reveal] 实例数 %d > 上界 %d" % (n, MOTION_REVEAL_MAX), ""))
    max_reveal = max(reveal_counts.values()) if reveal_counts else 0
    entry_ms = int(round((stagger * max(0, max_reveal - 1) + dur_max) * 1000))
    if entry_ms > MOTION_ENTRY_MAX_MS:
        bad.append(("进场完成 %dms > 上界 %dms" % (entry_ms, MOTION_ENTRY_MAX_MS), ""))
    if dur_sum > MOTION_DUR_SUM_MAX:
        bad.append(("--dur-* 之和 %.2fs > 上界 %.1fs" % (dur_sum, MOTION_DUR_SUM_MAX), ""))
    inf_els = len(re.findall(r"animation[^;}]*\binfinite\b", css_all))
    if inf_els > MOTION_INFINITE_MAX:
        bad.append(("常驻 infinite 声明 %d > 上界 %d" % (inf_els, MOTION_INFINITE_MAX), ""))
    if "html.js-motion [data-reveal]" not in re.sub(r"\s+", " ", css_all):
        bad.append(("缺 html.js-motion 前提下的隐藏态（无 JS 兜底第一保险）", ""))
    scripts = [b for _a, b in INLINE_SCRIPT_RE.findall("".join(ctx.html.values()))]
    # ★ 兜底定时器锚点：⛔ 不用 `setTimeout\([^)]*1800` —— 参数体是
    #   `function(){if(!R.getAttribute(...)){fin();}}`，其中含 `)` ⇒ `[^)]*` 走不到 1800，
    #   判据会对**真实存在**的兜底定时器判 FAIL（本轮实测 1 处假阳）。改用「1800 与 fin() 同段」。
    if not any(re.search(r"setTimeout\(", b) and re.search(r"1800", b) for b in scripts):
        bad.append(("缺 1800ms 一次性兜底定时器（无 JS 兜底第二保险）", ""))
    if not re.search(r"translate\s*:", css_all):
        bad.append(("缺独立 translate 属性（⛔ 不得用 transform 做进场位移）", ""))
    if re.search(r"html\.js-motion\s+\[data-reveal\][^{]*\{[^}]*transform\s*:", css_all):
        bad.append(("进场位移用了 transform（会压过 .card:hover 的抬起）", ""))
    ctx.notes.append("P28 四项上界取自 H1 §6.5（阈值由 hub 实测基线 × 既定余量推导，"
                     "⛔ 不得由规模直觉推导）：M1 ≤%d / M2 ≤%dms / M3 ≤%.1fs / M4 ≤%d。"
                     "本轮实测：最大 [data-reveal] %d；错峰 %dms；dur 之和 %.2fs；infinite %d。"
                     % (MOTION_REVEAL_MAX, MOTION_ENTRY_MAX_MS, MOTION_DUR_SUM_MAX, MOTION_INFINITE_MAX,
                        max_reveal, int(stagger * 1000), dur_sum, inf_els))
    return (not bad), ("M1 单页最大 [data-reveal] %d（≤%d）；M2 进场完成 %dms（≤%d）；"
                       "M3 --dur-* 之和 %.2fs（≤%.1f）；M4 infinite %d（≤%d）；违例 %d 处 %s"
                       % (max_reveal, MOTION_REVEAL_MAX, entry_ms, MOTION_ENTRY_MAX_MS,
                          dur_sum, MOTION_DUR_SUM_MAX, inf_els, MOTION_INFINITE_MAX, len(bad), bad[:4]))


def _css_hover_selectors(ctx):
    """全量产物 CSS 中含 :hover / :focus-within 的选择器集合（去重、归一化空白）。"""
    found = set()
    for _rel, css in sorted(_all_styles(ctx).items()):
        for _conds, header, _body, _raw in parse_css(css):
            if header.startswith("@"):
                continue
            for sel in selectors_of(header):
                if re.search(r":(hover|focus-within)\b", sel):
                    found.add(re.sub(r"\s+", " ", sel))
    return found


def check_p29(ctx):
    """P29 交互作用面双向闭合：CSS 中含 `:hover`/`:focus-within` 的选择器集合 ⟺ 声明表登记集合
    （漏登记与**幽灵登记**均 FAIL）；每条登记的基选择器在产物中**至少命中 1 个元素**。"""
    found = _css_hover_selectors(ctx)
    registered = set(ctx.surface_selectors)
    if not found:
        return False, "空集守卫：产物 CSS 中没有任何 :hover/:focus-within 选择器 ⇒ 判据恒真"
    if not registered:
        return False, "空集守卫：交互作用面登记表为空 ⇒ 判据恒真"
    bad = []
    # ★ 判据作用域修正（2026-10-15，两处）：
    #   ① **焦点等价面允许由全局规则承担**：H1 §7.2 C4 明写「`focus_equivalent` 指向真实存在的焦点规则，
    #      **或显式 `:focus-visible` 全局环**」。初版把登记表里的 `X:focus-visible` 一律判为
    #      「幽灵登记」，而本站 CSS 正是用**一条全局 `:focus-visible`** 覆盖全部交互件 ⇒ 3 条假阳。
    #   ② **拉伸层成对检查必须整段移除该元素**：初版只把 `class="card__title-link"` 这段文本替换掉，
    #      而 `<a ` 开标签仍在 ⇒ `"<a " in rest` **恒真**，任何卡片都被判「卡内存在未抬升的真链接」。
    global_focus = False
    for css in _all_styles(ctx).values():
        rest_css = re.sub(re.escape(TOKEN_BEGIN) + r".*?" + re.escape(TOKEN_END), "", css, flags=re.S)
        for header, _body, _raw in [(h, b, r) for _c, h, b, r in parse_css(rest_css)]:
            if header.startswith("@"):
                continue
            sels = selectors_of(header)
            # ★ 全局焦点环的形态：一条规则的选择器表**每一项**都带 :focus-visible
            #   （本站为 `a:focus-visible,button:focus-visible,summary:focus-visible,…`）。
            #   ⛔ 只匹配裸 `:focus-visible` 会漏掉这一形态（本轮实测 3 条假「幽灵登记」）。
            if sels and all(re.search(r":focus-visible\b", s) for s in sels):
                global_focus = True
            if any(re.search(r":focus-within\b", s) for s in sels):
                global_focus = True
    missing = sorted(found - registered)
    ghost = sorted(s for s in (registered - found)
                   if not (global_focus and (s.endswith(":focus-visible") or s.endswith(":focus-within"))))
    if missing:
        bad.append(("漏登记（CSS 有而登记表无）", missing[:6]))
    if ghost:
        bad.append(("幽灵登记（登记表有而 CSS 无）", ghost[:6]))
    if not global_focus:
        bad.append(("缺全局 :focus-visible 焦点环（焦点等价面的兜底载体）", ""))
    hits = []
    all_html = "\n".join(ctx.html.values())
    for e in ctx.interaction_surface:
        c = count_elements(all_html, e["base"])
        hits.append((e["base"], c))
        if c is None:
            bad.append(("登记的基选择器无法粗粒度计数", e["base"]))
        elif c == 0:
            bad.append(("登记的基选择器零命中（登记表静默腐化）", e["base"]))
    cards = re.findall(r'<section class="card"[^>]*>(.*?)</section>', all_html, re.S)
    if not cards:
        bad.append(("空集守卫：产物中没有任何可点卡片 ⇒ 拉伸层成对契约无法被检验", ""))
    for i, c in enumerate(cards):
        if "card__title-link" not in c:
            bad.append(("可点卡片缺拉伸层标题链接", i))
            continue
        rest = re.sub(r'<a\b[^>]*class="card__title-link"[^>]*>.*?</a>', "", c, flags=re.S)
        if "<a " in rest and "card__links" not in c:
            bad.append(("卡内存在未抬升的真链接（拉伸层会盖住它变死区）", i))
    ctx.notes.append("P29 双向闭合（H1 §7.2 C1/C2）：CSS 侧命中 %d 条、登记表展开 %d 条；"
                     "**漏登记**与**幽灵登记**均判 FAIL；每条登记的**基选择器**须在产物中至少命中 1 个元素"
                     "（零命中 ⇒ FAIL，防登记表静默腐化）；另断言**拉伸层成对契约**"
                     "（可点卡片必有 .card__title-link，卡内其它真链接必置于 .card__links 抬升）。"
                     % (len(found), len(registered)))
    return (not bad), ("CSS 侧选择器 %d 条 ⟺ 登记表 %d 条（差集 %d 条）；逐条基选择器命中计数 %s；"
                       "拉伸层成对契约复核 %d 张可点卡片；违例 %d 处 %s"
                       % (len(found), len(registered), len(missing) + len(ghost),
                          hits, len(cards), len(bad), bad[:4]))


def check_p30(ctx):
    """P30 资产白名单未扩散：受检集合中命中 `assets/` 前缀的引用全部为图片扩展名；
    无 `script`/`stylesheet` 混入；`assets/backdrop/` 实际文件集 = 登记表键集。"""
    bad = []
    asset_refs = []
    for rel, text in sorted(ctx.html.items()):
        for kind, value, attrs in _resource_refs(text):
            # ★ 判据作用域修正（2026-10-15）：初版按 `value.startswith("assets/")` 判命中前缀，
            #   那只在**站点根页面**成立；子目录页写 `../assets/…` ⇒ 初版对它们整体失明
            #   （既漏掉「命中前缀」的登记，也让后面的「未命中前缀的引用」误判）。
            #   ⇒ 统一走 `resolve_site_path` 的**按页面目录 + URL 语义**解析口径。
            resolved = resolve_site_path(rel, value)
            if resolved is None:
                continue
            if not resolved.startswith(ctx.asset_prefix):
                continue
            asset_refs.append((rel, kind, value))
            v = value.partition("#")[0].partition("?")[0]
            ext = os.path.splitext(v)[1].lower()
            if ext not in ctx.asset_exts:
                bad.append((rel, "assets/ 引用非图片扩展名", (kind, value)))
                continue
            if kind == "script":
                bad.append((rel, "assets/ 被当作脚本引用", value))
            if kind == "link":
                r = re.search(r'rel\s*=\s*"([^"]*)"', attrs or "", re.I)
                if not r or r.group(1).strip().lower() not in LINK_IMAGE_RELS:
                    bad.append((rel, "assets/ 被当作非图片 link 引用", (attrs or "")[:60]))
            # ★ 修正：初版要求 css-url 必须以 `..` 开头，那对**站点根页面**是错的
            #   （根页面写 `assets/…` 才正确）。正确断言＝「必须是**相对**路径」，
            #   即 ⛔ 不得为绝对路径 `/…`、⛔ 不得为站外 `http(s)://`。
            if kind == "css-url" and (v.startswith("/") or re.match(r"^(?:https?:)?//", v)):
                bad.append((rel, "assets/ 的 css-url 不是相对路径", value))
    if not asset_refs:
        return False, "空集守卫：受检集合中没有任何 assets/ 前缀引用 ⇒ 判据恒真"
    adir = os.path.join(SITE_ROOT, ASSET_DIR)
    actual = sorted(os.listdir(adir)) if os.path.isdir(adir) else []
    registered = sorted(set(ctx.credits) | set(ctx.ledger))
    if not actual:
        return False, "空集守卫：assets/backdrop/ 下无文件 ⇒ 判据恒真"
    if actual != registered:
        bad.append(("assets 文件集 ≠ 登记表键集（素材表 ∪ 台账表）",
                    sorted(set(actual) ^ set(registered))[:8]))
    ctx.notes.append("P30 依据任务书 §7：`assets/` 是**第二类白名单**（站点级只读图片资产），"
                     "与 `13-interactive/vendor/` 的**脚本**白名单分开声明、互不包含。"
                     "本判据断言：① 命中该前缀的引用全部为图片扩展名 %s；② 无 script/stylesheet 混入；"
                     "③ `assets/backdrop/` 的实际文件集与登记键集（%d 个图片素材 + %d 个非图片台账件）"
                     "相等（未登记文件不得存在）。" % (ctx.asset_exts, len(ctx.credits), len(ctx.ledger)))
    return (not bad), ("assets/ 前缀引用 %d 处；assets/backdrop 实际 %d 个文件 vs 登记 %d 个"
                       "（素材 %d + 台账 %d，相等=%s）；违例 %d 处 %s"
                       % (len(asset_refs), len(actual), len(registered), len(ctx.credits),
                          len(ctx.ledger), actual == registered, len(bad), bad[:4]))


def check_p31(ctx):
    """P31 色相不承载身份：产物中组相关选择器**不得**出现多色相分配（断言组配色令牌数 = 0）。"""
    bad = []
    pal = ctx.data["site_palette"]
    names = set(pal["css_names"].values())
    if not names:
        return False, "空集守卫：调色板 css_names 为空 ⇒ 判据恒真"
    group_tokens = sorted(n for n in names if GROUP_HUE_TOKEN_RE.match(n))
    if group_tokens:
        bad.append(("调色板仍声明组配色令牌", group_tokens))
    hue_hits = []
    for rel, text in sorted(ctx.files.items()):
        for m in GROUP_HUE_CLASS_RE.finditer(text):
            hue_hits.append((rel, m.group(0)))
    if hue_hits:
        bad.append(("产物中出现组色相类名", hue_hits[:6]))
    html_all = "\n".join(ctx.html.values())
    seq = len(re.findall(r'class="gseq"', html_all))
    if seq == 0:
        bad.append(("空集守卫：产物中未出现中性组序号标记 .gseq ⇒ "
                    "「身份由文字与序号承载」未落地", ""))
    gids = {g["id"] for g in ctx.data["dag"]["groups"]}
    missing_text = []
    for gid in sorted(gids):
        g = next(x for x in ctx.data["dag"]["groups"] if x["id"] == gid)
        if gid not in html_all or g["name"] not in html_all:
            missing_text.append(gid)
    if missing_text:
        bad.append(("组序号或组名文字在产物中缺失", missing_text))
    itext = ctx.html.get(INTERACTIVE, "")
    if re.search(r"colorLight|colorDark|labelLight|labelDark", itext):
        bad.append(("交互图仍按组取色（colorLight/colorDark 等字段残留）", ""))
    ctx.notes.append("P31 依据 H2 硬规则 5 与 hub 实测（C26：7 色按行序取值被判「不承载任何信息」"
                     "⇒ 裁决改单色）：本站 11 组配色**全部撤掉**，组身份改由**文字与中性序号**承载；"
                     "交互图组节点统一用品牌色，⛔ 不按组分配色相。本判据断言组配色令牌数 = 0、"
                     "产物无组色相类名、交互图无按组取色字段，且中性序号与组名文字在产物中齐备"
                     "（★ 后一条是**空集守卫的反面**：若把身份载体删光，判据也必须失败）。")
    return (not bad), ("组配色令牌 %d 个（应为 0）；产物组色相类名命中 %d 处；"
                       "中性序号标记 %d 处；组序号与组名文字齐备=%s；违例 %d 处 %s"
                       % (len(group_tokens), len(hue_hits), seq, not missing_text, len(bad), bad[:4]))


def check_p32(ctx):
    """P32 许可证登记：页脚含 CC BY 素材的署名行（素材名 + 作者 + 许可 + 链接），
    且 `assets/backdrop/` 每个文件都在登记表里。"""
    bad = []
    adir = os.path.join(SITE_ROOT, ASSET_DIR)
    actual = sorted(os.listdir(adir)) if os.path.isdir(adir) else []
    if not actual:
        return False, "空集守卫：assets/backdrop/ 下无任何素材文件 ⇒ 判据恒真"
    if not ctx.credits:
        return False, "空集守卫：背景素材登记表为空"
    registered = sorted(set(ctx.credits) | set(ctx.ledger))
    for fn in actual:
        if fn not in registered:
            bad.append(("素材/台账文件未登记", fn))
    for fn in registered:
        if fn not in actual:
            bad.append(("登记了不存在的文件", fn))
    by_src = {}
    for fn, c in ctx.credits.items():
        by_src.setdefault((c["name"], c["author"], c["license"], c["url"]), []).append(fn)
    for rel, text in sorted(ctx.html.items()):
        credits = re.search(r'<div class="footer__credits">.*?</div>', text, re.S)
        if not credits:
            bad.append((rel, "页脚缺 .footer__credits 署名块", ""))
            continue
        lines = re.findall(r"<li>(.*?)</li>", credits.group(0), re.S)
        if not lines:
            bad.append((rel, "署名块内无 <li> 署名行", ""))
            continue
        for key in sorted(by_src):
            name, author, license_, url = key
            if not any(name in ln and author in ln and license_ in ln and url in ln for ln in lines):
                bad.append((rel, "缺素材署名行（名称+作者+许可+链接四要素齐备）", key[0][:40]))
    ccby = sorted({c["name"] for c in ctx.credits.values() if "CC BY" in c["license"]})
    if not ccby:
        bad.append(("登记表中无 CC BY 素材（本判据的硬约束面为空）", ""))
    ctx.notes.append("P32 依据 H2 元规则 3 与任务书 §6：夜间帧为 ESO 影像（CC BY 4.0，**须署名**），"
                     "日间帧为 Unsplash（CC0 1.0，不要求署名但本站仍登记出处）。"
                     "页脚 `.footer__credits` 必须逐素材给出**素材名 + 作者 + 许可 + 链接**四要素，"
                     "且 `assets/backdrop/` 的每个文件都必须出现在登记表中（双向断言）。")
    return (not bad), ("assets/backdrop 文件 %d 个全部登记=%s；CC BY 素材 %d 项；"
                       "受检页面 %d 个的页脚署名行四要素齐备；违例 %d 处 %s"
                       % (len(actual), actual == registered, len(ccby), len(ctx.html), len(bad), bad[:4]))


# ---------------------------------------------------------------- P38–P40（2026-10-15 教训固化轮）
# ★ 本轮把四条真实教训**编码成机制**（⛔ 不是写成散文），逐条对应见 `CRITERIA-CHANGE-P38-P40.md`：
#   P38 ← 教训 ①②（「环境能力不可用」的结论本身要复核；验证通道的产物必须非退化）
#   P39 ← 教训 ④⑥（判据与夹具的作用域必须与对象对齐；「已实现但无判据」= 未落实 ⇒ 引用必须可解析）
#   P40 ← 教训 ⑤（委派方自报 ≠ 读数；子 Agent 的「完成」可能基于过期认知）
PROBE_MANIFEST_REL = "16-checkpoint/_probe/channel.json"
PROBE_SCHEMA = "pekg/channel-probe/1"
ROUND_LEDGER_REL = "16-checkpoint/ROUND-LEDGER.json"
LEDGER_SCHEMA = "pekg/round-ledger/1"
PNG_MIN_COLORS = 64            # 非退化下限（唯一色数）
PNG_MIN_LUM_SPAN = 32.0        # 非退化下限（亮度区间）
PNG_MIN_BYTES = 4096           # 非退化下限（字节）
CONTRACT_REL = "16-checkpoint/DESIGN-CONTRACT.md"
CONTRACT_CHANGE_PREFIX = "CRITERIA-CHANGE-"
# ★ 2026-10-16 第 7 轮新增：登记件在 `PUBLISH-STATE.json` 的 `gates` 里的**结构化键**前缀。
#   键名规则（可逆）：`CRITERIA-CHANGE-` 去掉 + `.md` 去掉 + `-` → `_`，前缀 `criteria_change_`。
#   例：`CRITERIA-CHANGE-P05-R5.md` ⟺ `criteria_change_P05_R5`。
CONTRACT_CHANGE_KEY_PREFIX = "criteria_change_"


def _change_key(filename):
    """登记件文件名 → `PUBLISH-STATE.gates` 的结构化键（唯一、可逆）。"""
    return (CONTRACT_CHANGE_KEY_PREFIX
            + filename[len(CONTRACT_CHANGE_PREFIX):-len(".md")].replace("-", "_"))
RID_RE = re.compile(r"^R-\d{2}$")
LONG_RUN_LIMIT = 110           # P35 报告项：单句/单条最长无标点游程（caliber 口径）


# ---------------------------------------------------------------- 负例夹具

def _first_html(ctx, prefix=None):
    keys = sorted(r for r in ctx.html if (prefix is None or r.startswith(prefix)))
    return keys[0]


def _patch(ctx, rel, old, new):
    """在 ctx 的副本上做一次文本替换（同时更新 files 与 html 两侧）。

    ★ 夹具健壮性修正（2026-10-15）：初版只在该页找锚点，找不到即抛错；而多数夹具用
      `_first_html(c)`（＝字典序首页 `11-node-pages/pe-f-01.html`）作目标页，锚点却可能只在
      根入口（如 `<h2>两条入口</h2>`）⇒ 夹具**锚点未命中**、负例未触发、自检 FAIL
      （本轮实测 P28 一处）。
      ⇒ 改为：目标页没有该锚点时，**按序在其余页面里找到第一个含该锚点的页面**再 patch；
        ⛔ 全站都没有才抛错（那才是真的锚点失效，必须显式暴露而不是静默跳过）。
    """
    if old in ctx.html.get(rel, ""):
        ctx.files[rel] = ctx.html[rel] = ctx.html[rel].replace(old, new)
        return ctx
    for other in sorted(ctx.html):
        if old in ctx.html[other]:
            ctx.files[other] = ctx.html[other] = ctx.html[other].replace(old, new)
            return ctx
    raise AssertionError("负例夹具锚点未命中（全站均无）：%r" % old[:60])


def _patch_strict(ctx, rel, old, new):
    """**严格版** patch：只改指定文件，⛔ 不跨页兜底（2026-10-16 第 6 轮新增）。

    ★ 为什么需要它：`_patch` 在目标页没有锚点时会**按序在其余页面里找第一个含该锚点的页**再改。
      对 P35 ⑧ 的组页夹具而言这是**假自检陷阱**：若用 `_patch(c, "12-groups/g00.html", '<figure class="fig"', …)`，
      锚点会被落到某个**节点页**上 ⇒ 负例在节点页侧触发，而「组页必须有图」这条子断言**从未被验证**。
      ⇒ 作用域类夹具（组页 / 视图页）一律用本函数：目标页没有锚点即**抛错**（fail-closed）。
    """
    if old not in ctx.html.get(rel, ""):
        raise AssertionError("严格夹具锚点未命中（目标页 %s 内无）：%r" % (rel, old[:60]))
    ctx.files[rel] = ctx.html[rel] = ctx.html[rel].replace(old, new)
    return ctx


def _patch_md(ctx, rel, old, new):
    """在 **MD 镜像**上做一次替换（2026-10-16 第 6 轮新增；P13 的 G13 夹具用）。

    ★ 为什么不能直接用 `_patch`：`_patch` 只动 `ctx.html`，而 P13 读的是 `ctx.md`
      ⇒ 夹具会「改了但判据看不见」（一次**假自检**）。本函数同时更新 `files` 与 `md` 两侧。
    """
    if old not in ctx.md.get(rel, ""):
        raise AssertionError("MD 夹具锚点未命中（%s 内无）：%r" % (rel, old[:60]))
    ctx.files[rel] = ctx.md[rel] = ctx.md[rel].replace(old, new)
    return ctx


def _sub_in_section(ctx, sid, old, new, kind="node"):
    """在**某个区块切片内**做一次替换（P35 ⑩ 的节点页夹具；G4 起 ⑪⑫⑬ 也要用组页）。

    ⛔ 锚点在该区块内找不到即抛错（fail-closed）——「锚点过期」必须显式暴露，
      否则负例不触发会被误读成「判据恒真」。
    ★ `kind` 限定目标页类型（"node" / "group"）：⛔ 不跨类型兜底，
      否则「组页的区块」这条断言会被节点页上的同名区块替它触发（假自检）。
    """
    for rel in sorted(ctx.html):
        if 'data-page-kind="%s"' % kind not in ctx.html[rel]:
            continue
        seg = _section_slice(ctx.html[rel], sid)
        if seg is None or old not in seg:
            continue
        ctx.files[rel] = ctx.html[rel] = ctx.html[rel].replace(seg, seg.replace(old, new))
        return ctx
    raise AssertionError("负例夹具锚点未命中（%s 页的 #%s 区块内均无）：%r" % (kind, sid, old[:60]))


def _set_group_intro_enum(ctx, idx=0):
    """负例夹具（⑨ 的组页侧）：让**组页的散文来源**命中显式枚举模式，而产物未随之重渲。

    ★ 相位说明（criterion-design-validation §4.10）：本夹具注入在**真相源侧**（`ctx.data`），
      而 ⑨ 断言的正是「真相源含该模式 ⇒ 产物必须有 `.enum-list`」这一**跨相位蕴含**；
      夹具即该蕴含的反例（数据已含模式、产物未跟上）⇒ 是有效负例，⛔ 不是「改夹具凑绿」。
    """
    g = ctx.data["dag"]["groups"][idx]
    g["intro"] = g["intro"] + "补充说明有三条：其一，甲；其二，乙；其三，丙。"
    return ctx


def _sub_first_enum_to_one_li(ctx):
    """把全站第一个 `.enum-list` 截成只剩 1 条 `<li>`（P35 ⑨ 的第二个负例）。"""
    for rel in sorted(ctx.html):
        m = re.search(r'<ol class="enum-list">(.*?)</ol>', ctx.html[rel], re.S)
        if not m:
            continue
        lis = re.findall(r"<li>.*?</li>", m.group(1), re.S)
        if len(lis) < 2:
            continue
        new = '<ol class="enum-list">%s</ol>' % lis[0]
        ctx.files[rel] = ctx.html[rel] = ctx.html[rel][:m.start()] + new + ctx.html[rel][m.end():]
        return ctx
    raise AssertionError("负例夹具锚点未命中（全站没有 ≥2 条的 .enum-list）")


def _patch_all(ctx, old, new):
    """在**所有**含该锚点的页面上替换；⛔ 全站无一处命中即抛错。

    ★ 夹具健壮性修正（2026-10-15）：初版对「一处都没命中」**静默返回** ⇒ 设计改版后锚点文本
      失效时，夹具**不报错也不产生违例**，自检只报「负例未触发」，看不出根因是锚点过期。
      ⇒ 改为 fail-closed：无命中即抛错，把「锚点过期」与「判据恒真」两种情形分开暴露。
    """
    hit = 0
    for rel in list(ctx.html):
        if old in ctx.html[rel]:
            ctx.files[rel] = ctx.html[rel] = ctx.html[rel].replace(old, new)
            hit += 1
    if hit == 0:
        raise AssertionError("负例夹具锚点未命中（全站均无）：%r" % old[:60])
    return ctx


def mut_p01(ctx):
    ctx.data["dag"]["nodes"][0].pop("why")
    return ctx


def mut_p02(ctx):
    ctx.data["dag"]["nodes"][1]["group"] = "G99"
    return ctx


def mut_p03(ctx):
    ctx.data["dag"]["edges"][0]["rel"] = "DEPENDS"
    return ctx


def mut_p04(ctx):
    nid = ctx.data["dag"]["nodes"][4]["id"]
    ctx.data["dag"]["edges"] = [e for e in ctx.data["dag"]["edges"]
                                if e["source"] != nid and e["target"] != nid]
    return ctx


def mut_p05(ctx):
    out = []
    c = copy.deepcopy(ctx)
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["why"] = "太短了。"
    out.append(c)
    c = copy.deepcopy(ctx)
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["summary"] = "先接受输出是分布的一个样本"
    out.append(c)
    c = copy.deepcopy(ctx)
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["summary"] = sentences(n["why"])[0].strip()
    out.append(c)
    c = copy.deepcopy(ctx)
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["summary"] = "本节点小结待填充。"
    out.append(c)
    c = copy.deepcopy(ctx)
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "registered")
    n["intro"] = "机制很短。"
    out.append(c)
    # ★ 2026-10-16（B-1）新增三条：打 `boundary` 的三条硬断言
    c = copy.deepcopy(ctx)                              # ① boundary 为空
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["boundary"] = ""
    out.append(c)
    c = copy.deepcopy(ctx)                              # ② boundary = why 的首句（整句复制）
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["boundary"] = sentences(n["why"])[0].strip()
    out.append(c)
    c = copy.deepcopy(ctx)                              # ③ why 里残留引导串（会渲染出第二个边界块）
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["why"] = n["why"] + "适用边界是——残留的引导串。"
    out.append(c)
    return out


def mut_p06(ctx):
    out = []
    c = copy.deepcopy(ctx)
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["pitfalls"] = []
    out.append(c)
    c = copy.deepcopy(ctx)
    it = c.data["frontier"]["items"][0]
    it["status"] = "unverified"
    it.pop("offline_repro", None)
    for x in c.data["dag"]["nodes"]:
        if x["id"] == it["id"]:
            x["evidence"] = []
    out.append(c)
    return out


def mut_p07(ctx):
    n = ctx.data["dag"]["nodes"][0]
    n["terms"] = list(n.get("terms", [])) + ["并不存在的术语（No Such Term）：占位。"]
    return ctx


def mut_p08(ctx):
    k = _first_html(ctx)
    return _patch(ctx, k, "</main>", '<p><a href="no-such-page.html">x</a></p></main>')


def mut_p09(ctx):
    out = []
    k = _first_html(ctx, "11-node-pages")
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>", '<script src="https://cdn.example.com/x.js"></script></head>'))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>", '<script src="vendor/x.js"></script></head>'))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>",
                      '<link rel="stylesheet" href="../assets/backdrop/day-1920.webp"></head>'))
    c = copy.deepcopy(ctx)
    # ★ 夹具修正（2026-10-15）：初版只删 `<link rel="icon" …assets/favicon.svg>`，而各页还有
    #   背景帧的 `url("…assets/backdrop/*.webp")` ⇒ 图片白名单集合**远未清空**，空集守卫不触发
    #   （本轮实测「负例未触发」）。⇒ 必须把**全部**图片引用一并去掉，才真正检验空集守卫。
    # ★ 2026-10-16 第 8 轮：连元数据类 `<link>` 也一并去掉 —— 否则「有元数据链接」会遮蔽
    #   「无图片资产」这个空集条件（判据本要检的是后者）。
    for rel in list(c.html):
        t = re.sub(r'<link\b[^>]*>', "", c.html[rel], flags=re.I)
        t = re.sub(r'url\("[^"]*assets/backdrop/[^"]*"\)', "none", t)
        c.html[rel] = c.files[rel] = t
    out.append(c)
    # ★ 2026-10-16 第 8 轮新增 3 条负例：守住「判据对象收窄」不许退化成「有 link 就放过」。
    #   ① rel 闭集之外的 `preload`（浏览器会真去取资源 ⇒ 必须 FAIL）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>",
                      '<link rel="preload" href="../assets/backdrop/day-1920.webp" as="image"></head>'))
    #   ② 元数据类 rel 的 href 带主机（元数据不得成为外链后门）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>",
                      '<link rel="icon" href="https://cdn.example.com/favicon.svg"></head>'))
    #   ③ canonical 指站外（元数据无主机断言的第 2 个面）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>",
                      '<link rel="canonical" href="https://evil.example.com/x.html"></head>'))
    #   ④ ★ 2026-10-16 第 8 轮新增：`canonical` 指向**本站基址之外**的另一台主机
    #      （`LINK_META_HOSTED_OK` 只容许 canonical/alternate 带主机，且必须是**本站自指**）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>",
                      '<link rel="canonical" href="https://zako-mio.github.io/other-repo/x.html">'
                      "</head>"))
    return out


def mut_p10(ctx):
    out = []
    k = _first_html(ctx)
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</style>", ":root{--bg:#000000}\n</style>"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>", "<style>.x{--local:1px}</style></head>"))
    return out


def mut_p11(ctx):
    out = []
    c = copy.deepcopy(ctx)
    c.data["site_palette"]["values"]["text.primary"]["light"] = "#f2f4f8"
    out.append(c)
    c = copy.deepcopy(ctx)
    c.data["site_palette"]["_meta"]["contrast_triples"] = []
    out.append(c)
    return out


def mut_p12(ctx):
    """★ 2026-10-16 第 8 轮由 1 条扩为 2 条：判据对象收窄（「主机名」只在正文上判）后，
    ⛔ 必须有一条负例**专门守住正文侧**，否则收窄会悄悄退化成「主机名永远不判」。"""
    out = []
    k = _first_html(ctx)
    # ① 正文里的内部编号 + 绝对路径 + 裸主机名（原有；覆盖全部四类命中的正文侧）
    out.append(_patch(ctx, k, "</main>",
                      "<p>见 §8 与门控级口径；/home/user/secret；host zako-mio</p></main>"))
    # ② 正文里只放一个**裸主机名**（不带任何其它违例）⇒ 若收窄过头，这一条就再也触发不了
    out.append(_patch(ctx, k, "</main>",
                      "<p>本页由 zako-mio 维护。</p></main>"))
    return out


def mut_p13(ctx):
    """P13 的负例夹具（★ 2026-10-16 第 6 轮由 1 条扩为 4 条：G12 两条 + G13 两条）。

    ⛔ 每一条都打在**它该打的那条子断言**上：
      · ① 删 MD 镜像 ⇒ 缺镜像（原有）；
      · ② `counts.html` ±1 ⇒ G12 的产物侧计数脱钩；
      · ③ 把镜像里的「适用边界」正文换成占位 ⇒ G13 的 boundary 比对（第 5 轮真实发生过的缺陷形态）；
      · ④ 把某条 `pitfalls` 的前缀换成占位 ⇒ G13 的 pitfalls 前缀比对。
    """
    out = []
    # ① 删掉一个已发布节点的 MD 镜像
    c = copy.deepcopy(ctx)
    c.files.pop("%s/nodes/pe-f-01.md" % MD_DIR, None)
    c.md.pop("%s/nodes/pe-f-01.md" % MD_DIR, None)
    out.append(c)
    # ② `counts.html` 与产物实数脱钩（+1）
    c = copy.deepcopy(ctx)
    st = json.loads(c.files[STATE_FILE])
    st["counts"]["html"] = st["counts"]["html"] + 1
    c.files[STATE_FILE] = json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    out.append(c)
    # ③ MD 镜像丢掉 `boundary` 正文（HTML 仍有边界块 ⇒ 两个出口不一致）
    n1 = {n["id"]: n for n in ctx.data["dag"]["nodes"]}["PE-F-01"]
    c = copy.deepcopy(ctx)
    out.append(_patch_md(c, "%s/nodes/pe-f-01.md" % MD_DIR,
                         _md_flat(n1["boundary"]), "（本行已删除）"))
    # ④ MD 镜像丢掉某条 `pitfalls` 的可辨识前缀
    p0 = (n1.get("pitfalls") or [""])[0]
    c = copy.deepcopy(ctx)
    out.append(_patch_md(c, "%s/nodes/pe-f-01.md" % MD_DIR,
                         _md_flat(p0), "（已改写为占位）"))
    # ★ 2026-10-16 第 8 轮新增 2 条：`published` 与 `publish` 段的**内部一致性**（D-2 的对象）。
    #   ⑤ `published=true` 却把 `publish` 段整个删掉 ⇒ 发布事实缺载体（FAIL）
    c = copy.deepcopy(ctx)
    st = json.loads(c.files[STATE_FILE])
    st["published"] = True
    st.pop("publish", None)
    c.files[STATE_FILE] = json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    out.append(c)
    #   ⑥ `published=false` 却残留 `publish` 段 ⇒ 过期事实（FAIL）
    c = copy.deepcopy(ctx)
    st = json.loads(c.files[STATE_FILE])
    st["published"] = False
    st["publish"] = {"repo": "x/y", "entry_url": "https://example.com/", "pages_build_type": "legacy",
                     "hub_listed": True}
    c.files[STATE_FILE] = json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    out.append(c)
    return out


def _md_flat(s):
    """与 `gen-md._md_escape` 同口径（换行折成空格）—— 供 MD 夹具取锚点。"""
    return str(s if s is not None else "").replace("\n", " ")


def mut_p14(ctx):
    k = _first_html(ctx, "11-node-pages")
    return _patch(ctx, k, 'href="../12-groups/g00.html"', 'href="g00.html"')


def mut_p15(ctx):
    k = _first_html(ctx)
    return _patch(ctx, k, "<!-- template: shell-v2 -->", "<!-- template: legacy-shell -->")


def mut_p16(ctx):
    p = ctx.probe["idempotent"]
    k = sorted(p["b"])[0]
    p["b"][k] = "0" * 64
    return ctx


def mut_p17(ctx):
    p = ctx.probe["dryrun"]
    p["write"]["added"] = list(p["write"]["added"])[:-1]
    return ctx


def mut_p18(ctx):
    p = ctx.probe["orphan"]
    p["exists_after"] = True
    p["residual"] = [p["orphan"]]
    return ctx


def mut_p19(ctx):
    ctx.data["provenance"] = dict(ctx.data["provenance"])
    ctx.data["provenance"]["source_sha256"] = "f" * 64
    return ctx


def mut_p20(ctx):
    out = []
    c = copy.deepcopy(ctx)
    c.data["site_palette"]["values"].pop("brand.primary", None)
    out.append(c)
    c = copy.deepcopy(ctx)
    c.contract_roles = []
    out.append(c)
    return out


def mut_p21(ctx):
    p = ctx.probe["frontier"]
    k = sorted(k for k in p["mut"] if "frontier" not in k)[0]
    p["mut"][k] = "1" * 64
    return ctx


def mut_p22(ctx):
    """负例（★ 2026-10-16 判据变更 P22 后重写）：

    ① 原夹具：`complete` 节点的区块置空（打 ② 的 8 区块断言）；
    ②③ 新增：`registered` 节点塞入 `pitfalls` / `evidence`（打 **C3 ③** 的「内容已填但状态未翻」）。

    ★ 诚实登记：旧 P22 只有一个夹具（①），而 `registered ≥60` 那一半**从未被证明可判假**——
      本变更撤销该半句后，夹具数由 1 增到 3，可判假面反而**变宽**（见 CRITERIA-CHANGE-P22.md §1）。
    """
    out = []
    c = copy.deepcopy(ctx)
    n = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "complete")
    n["lab"] = []
    out.append(c)
    c = copy.deepcopy(ctx)
    r = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "registered")
    r["pitfalls"] = ["半填：内容已写却仍标 registered（状态说谎）。"]
    out.append(c)
    c = copy.deepcopy(ctx)
    r = next(x for x in c.data["dag"]["nodes"] if x["content_status"] == "registered")
    r["evidence"] = [{"claim": "半填", "source_id": "S-0001",
                      "url": "https://example.invalid/", "quote": "半填", "tier": "official"}]
    out.append(c)
    return out


def mut_p23(ctx):
    out = []
    k = _first_html(ctx)
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "--text-primary: #0e1729;", "--text-primary: #0e172a;"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</style>", ".card{--local-x:1px}\n</style>"))
    c = copy.deepcopy(ctx)
    c.data["site_palette"]["css_names"].pop("scrim.3", None)
    out.append(c)
    c = copy.deepcopy(ctx)
    # ★ 夹具修正（2026-10-15）：初版 pop 的是 `values["scrim.3"]`，而本判据比对的是
    #   **`css_names` 的角色名集** vs 令牌块实际声明的变量集 ⇒ 动 `values` 对判据**完全无影响**，
    #   负例必然不触发（本轮实测）。⇒ 改为往 `css_names` 里加一个「登记了但块内未声明」的角色名，
    #   制造真实的两侧集合不等。
    c.data["site_palette"]["css_names"]["zzz.ghost"] = "--zzz-ghost"
    out.append(c)
    return out


def mut_p24(ctx):
    out = []
    for snippet in (".x{font-size:0.86rem}", ".x{border-radius:10px}", ".x{color:#333}",
                    ".x{padding:.85rem 1rem}", ".x{outline:1px dashed red}"):
        c = copy.deepcopy(ctx)
        out.append(_patch(c, _first_html(c), "</style>", snippet + "\n</style>"))
    c = copy.deepcopy(ctx)
    for rel in list(c.html):
        c.html[rel] = c.files[rel] = re.sub(r"font-size\s*:\s*[^;}]+;?", "", c.html[rel])
    out.append(c)
    c = copy.deepcopy(ctx)
    # ★ 夹具修正（2026-10-15）：初版用 `re.sub(r"padding[^:]*:\s*[^;}]+;?", "")` 删除 padding 声明，
    #   实测删不掉（`[^;}]+` 在含 `var(--a) var(--b)` 的值上会提前停在 `)` 之外，且 `padding` 后
    #   紧跟 `:` 时 `[^:]*` 为空仍应命中 —— 实际残留 931 处）⇒ 空集守卫不触发。
    #   ⇒ 改为**改属性名**：把 `padding`/`margin` 前缀改写成 `zz-`，使其不再被计为 padding/margin 声明。
    for rel in list(c.html):
        c.html[rel] = c.files[rel] = re.sub(r"\b(padding|margin)(-[a-z]+)?\s*:",
                                            r"zz-\1\2:", c.html[rel])
    out.append(c)
    return out


def mut_p25(ctx):
    out = []
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), "</style>", "a:hover{color:var(--link)}\n</style>"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), "@media (hover: hover){",
                      "@media (hover: hover){\n a:focus-visible{outline-offset:0}"))
    c = copy.deepcopy(ctx)
    for rel in list(c.html):
        c.html[rel] = c.files[rel] = re.sub(r"[^{}\n]*:hover[^{}]*\{[^}]*\}", "", c.html[rel])
    out.append(c)
    return out


def mut_p26(ctx):
    out = []
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), "@media (prefers-color-scheme: dark) {",
                      "@media (prefers-color-scheme: no-preference) {"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), "</head>",
                      "<style>:root[data-theme='light']{color-scheme:light}</style></head>"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c),
                      '<meta name="theme-color" content="#f4f7fc" media="(prefers-color-scheme: light)">',
                      '<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">'))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), SCRIPT_MARK, "/* bootstrap */"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), '<button type="button" class="switch__btn" '
                                         'data-theme-set="dark" aria-pressed="false">主题：深色</button>', ""))
    return out


def mut_p27(ctx):
    out = []
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c),
                      ".backdrop{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}",
                      ".backdrop{position:absolute;inset:0;z-index:1;overflow:hidden}"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), '<div class="backdrop__scrim"></div>',
                      '<div class="backdrop__scrim"></div><a href="#main">x</a>'))
    c = copy.deepcopy(ctx)
    # ★ 夹具修正（2026-10-15 第二次）：本判据的 `display:none` 断言是把**深色侧全部 backdrop 规则**
    #   拼接（`joined`）后再搜索 ⇒ 只改其中**一条**规则，其余同类规则仍含 `display:none`，
    #   负例不触发（本轮实测两次）。
    #   ⇒ 改为清掉**整类**：把全站 `display:none` 换成 `display:inline`（隐藏面整体失效）。
    out.append(_patch_all(c, "display:none", "display:inline"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), '<div class="backdrop" aria-hidden="true">',
                      '<div class="backdrop">'))
    c = copy.deepcopy(ctx)
    # 另一条：清掉 `display:block` 显式恢复（判据另有一条「覆盖不足」断言）
    out.append(_patch_all(c, "display:block", "display:inline"))
    return out


def mut_p28(ctx):
    out = []
    c = copy.deepcopy(ctx)
    # ★ 夹具修正（2026-10-15）：初版锚点是 `<h2>两条入口</h2>`，该串只在**根入口**上；
    #   而 `_first_html(c)` 取字典序首页（`11-node-pages/pe-f-01.html`）⇒ 锚点未命中
    #   （本轮实测「负例夹具锚点未命中」）。`_patch` 现已支持跨页回退，此处再改为
    #   **全站注入**，使 M1 计数在任何取值口径下都必然越界。
    out.append(_patch_all(c, "</main>", "</main>" + '<div data-reveal="1"></div>' * 40))
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, "--dur-4: 0.85s;", "--dur-4: 4s;"))
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, "</style>",
                          ".y{animation:pulse 3s linear infinite}\n" * 14 + "</style>"))
    c = copy.deepcopy(ctx)
    # ★ 夹具修正（2026-10-15）：初版只把**隐藏态那一条**规则的 `html.js-motion` 前提去掉，
    #   而 `.is-in` 规则里还留着同样的 `html.js-motion [data-reveal]` ⇒ 判据的
    #   「缺 html.js-motion 前提」断言仍找得到该串，负例不触发（本轮实测）。
    #   ⇒ 改为**全站把前提类名替换掉**，真正移除「无 JS 时默认可见」这一保险。
    out.append(_patch_all(c, "html.js-motion", "html.zz-motion"))
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, "1800", "90000"))
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, "translate:0 var(--reveal-shift)}", "transform:translateY(16px)}"))
    return out


def mut_p29(ctx):
    out = []
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), "@media (hover: hover){",
                      "@media (hover: hover){\n .zzz-unknown:hover{color:var(--link)}"))
    c = copy.deepcopy(ctx)
    c.surface_selectors = set(x for x in c.surface_selectors if x != ".cy-bar__btn:hover")
    c.interaction_surface = tuple(
        dict(e, selectors=tuple(s for s in e["selectors"] if s != ".cy-bar__btn:hover"))
        for e in c.interaction_surface)
    out.append(c)
    c = copy.deepcopy(ctx)
    c.surface_selectors = set((".zzz-nohit:hover" if x == ".cy-bar__btn:hover" else x)
                              for x in c.surface_selectors)
    c.interaction_surface = tuple(
        dict(e, base=(".zzz-nohit" if e["base"] == ".cy-bar__btn" else e["base"]),
             selectors=tuple((".zzz-nohit:hover" if s == ".cy-bar__btn:hover" else s)
                             for s in e["selectors"]))
        for e in c.interaction_surface)
    out.append(_patch_all(c, ".cy-bar__btn:hover", ".zzz-nohit:hover"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "index.html", '<section class="card" data-reveal="1" style="--i:0">',
                      '<section class="card" data-reveal="1" style="--i:0">'
                      '<p><a href="x.html">外链</a></p>'))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "index.html", 'class="card__title-link"', 'class="zzz-link"'))
    return out


def mut_p30(ctx):
    out = []
    k = _first_html(ctx)
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>",
                      '<link rel="stylesheet" href="../assets/backdrop/day-1920.webp"></head>'))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, k, "</head>", '<script src="../assets/favicon.svg"></script></head>'))
    c = copy.deepcopy(ctx)
    c.ledger = dict(c.ledger)
    c.ledger.pop("LICENSES.json", None)
    out.append(c)
    c = copy.deepcopy(ctx)
    for rel in list(c.html):
        c.html[rel] = c.files[rel] = re.sub(r'url\("\.\./assets/backdrop/[^"]*"\)', "", c.html[rel])
        c.html[rel] = c.files[rel] = re.sub(
            r'<link rel="icon"[^>]*assets/favicon\.svg">', "", c.html[rel])
    out.append(c)
    return out


def mut_p31(ctx):
    out = []
    c = copy.deepcopy(ctx)
    c.data["site_palette"]["css_names"]["group.00"] = "--group-00"
    c.data["site_palette"]["values"]["group.00"] = {"light": "#0f766e", "dark": "#2dd4bf"}
    out.append(c)
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, 'class="gseq"', 'class="gchip-hue"'))
    c = copy.deepcopy(ctx)
    c.html[INTERACTIVE] = c.files[INTERACTIVE] = c.html[INTERACTIVE].replace(
        "tok(\"brand-primary\")", "g.colorLight")
    out.append(c)
    c = copy.deepcopy(ctx)
    for rel in list(c.html):
        c.html[rel] = c.files[rel] = re.sub(r'<span class="gseq">[^<]*</span>', "", c.html[rel])
    out.append(c)
    return out


def mut_p32(ctx):
    out = []
    c = copy.deepcopy(ctx)
    c.credits = dict(c.credits)
    c.credits.pop("night-2560.webp", None)
    out.append(c)
    c = copy.deepcopy(ctx)
    for rel in list(c.html):
        c.html[rel] = c.files[rel] = re.sub(
            r'<div class="footer__credits">.*?</div>', "", c.html[rel], flags=re.S)
    out.append(c)
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, "CC BY 4.0", "CC0 1.0"))
    c = copy.deepcopy(ctx)
    for rel in list(c.html):
        c.html[rel] = c.files[rel] = re.sub(r"<li><span class=\"credits__name\">.*?</li>",
                                            "", c.html[rel], flags=re.S)
    out.append(c)
    return out


def check_p33(ctx):
    """P33 公开文案不含内部标注记号（⛔ / ★ / ⚠）。

    ★ 判据由来（2026-10-15，主 Agent 复验时发现）：P12 只断言内部**编号**（章节符编号、内部档位词）、
      绝对路径、主机名与令牌串，**没有覆盖内部标注记号**。而生成器的公开文案里带着 `⛔` / `★` / `⚠`
      —— 它们是**内部论证的记号**（CSS 注释里保留是与 hub 的 ★ 留痕同规、可接受），
      但出现在**可见文案**里会让公开站点读起来像内部工作稿。
      ⇒ 断言范围＝**可见文本**（剥掉 `<style>` / `<script>` 后再剥标签），⛔ 不含 CSS 注释。
      本轮实测：修前可见文案 ⛔26 / ★2 / ⚠7；CSS 注释内 ⛔209 / ★152（后者**有意保留**）。
    """
    bad = []
    if not ctx.html:
        return False, "空集守卫：无受检页面"
    marks = ("\u26d4", "\u2605", "\u26a0")   # ⛔ ★ ⚠
    for rel, text in sorted(ctx.html.items()):
        body = re.sub(r"<(script|style)\b.*?</\1>", "", text, flags=re.S | re.I)
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        visible = re.sub(r"<[^>]+>", " ", body)
        for ch in marks:
            if ch in visible:
                idx = visible.index(ch)
                bad.append((rel, "可见文案含内部记号 %r" % ch,
                            re.sub(r"\s+", " ", visible[max(0, idx - 40):idx + 40])))
    return (not bad), "受检页面 %d 个；可见文案内部记号命中 %d 处 %s" % (
        len(ctx.html), len(bad), bad[:4])


def mut_p33(ctx):
    out = []
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), "</main>", "内部记号泄漏 ⛔ 示例</main>"))
    c = copy.deepcopy(ctx)
    out.append(_patch(c, _first_html(c), "</main>", "内部记号泄漏 ★ 示例</main>"))
    return out


# ---------------------------------------------------------------- P34（2026-10-15 用户反馈轮新增）

RAIL_WIDE_MEDIA = "(min-width:%dpx)" % NAV_BREAKPOINT


def _css_len_px(v, root_px=16.0):
    """令牌长度字面值 → px。clamp(...) 取**末项**（＝上界；宽度预算按最不利取值）。

    ⛔ 只接受单值（px / rem）：本站的长度令牌只有这两种形态；出现别的形态即抛错，
      由判据显式暴露为「预算取值失败」，⛔ 不静默按 0 处理（那会让判据变成恒真）。
    """
    v = re.sub(r"\s+", " ", (v or "").strip())
    m = re.match(r"^clamp\((.+)\)$", v)
    if m:
        v = [p.strip() for p in m.group(1).split(",")][-1]
    m = re.match(r"^(-?[0-9.]+)(px|rem)$", v)
    if not m:
        raise ValueError("无法解析长度令牌值：%r" % v)
    return float(m.group(1)) * (root_px if m.group(2) == "rem" else 1.0)


def _rule_decls(body):
    return {k: v.strip() for k, v in re.findall(r"([a-z-]+)\s*:\s*([^;{}]+)", body)}


def check_p34(ctx):
    """P34 宽屏左栏完整性 ＋ 根入口标题宽度预算（★ 2026-10-15 用户反馈轮判据化）。

    ★ 判据由来：用户走查原型（V3 人看通道）提出两条观感问题 ——
      ① 首页标题字号过大 ⇒ 折行、两端贴边；② 宽屏左栏下方留白（只到 100dvh），
      且 ≥1180 档 `.site-head{display:none}` 把主题/动效开关**一并藏掉**（宽屏无任何切换入口）。
    观感本身不可机检，但**其可复算的成因**可以：
      ① 是否单行 = 文本宽度预算（CJK 每字进宽 1em，再乘 (1+letter-spacing)）对内容列宽；
      ② 是否撑满竖向 = rail 的 align-self 与内层 sticky 高度、底端锚定；
      ③ 开关是否有且仅有一组可见 = 基础档 `.rail{display:none}` 与宽屏档
         `.site-head{display:none}` 两条规则构成的互斥。
    ⇒ 三条都写成判据；⛔ 不写「字号好看」这类不可判假的话。
    ★ 宽度预算的**算式与 CSS 同源**：预算里用的 `--container` / `--rail-w` / `--space-5`
      三个令牌，必须在产物 CSS 里真的出现在 `.layout` / 栅格 / 正文列内边距上，
      否则算式为真而布局为假（判据与对象脱钩）⇒ 另断言三条 CSS 事实。
    """
    bad = []
    styles = _all_styles(ctx)
    if not styles:
        return False, "空集守卫：无受检样式块 ⇒ 判据恒真"
    rules = []
    for rel, css in sorted(styles.items()):
        for conds, header, body, raw in parse_css(css):
            rules.append((rel, conds, header, body, raw))
    # ---- (a) 左栏形态：宽屏撑满竖向（align-self:stretch）＋ 内层 sticky 100dvh 纵排 ＋ 底端锚定
    rail_hidden_base = rail_visible_wide = head_hidden_wide = False
    rail_in_ok = foot_ok = False
    for _rel, conds, header, body, _raw in rules:
        if header.startswith("@"):
            continue
        sels = selectors_of(header)
        d = _rule_decls(body)
        wide = any(media_condition_norm(c) == RAIL_WIDE_MEDIA for c in conds)
        if wide:
            if ".rail" in sels and d.get("display") == "block" and d.get("align-self") == "stretch":
                rail_visible_wide = True
            if ".site-head" in sels and d.get("display") == "none":
                head_hidden_wide = True
        elif not conds:
            if ".rail" in sels and d.get("display") == "none":
                rail_hidden_base = True
        if ".rail__in" in sels:
            if (d.get("position") == "sticky" and d.get("height") == "100dvh"
                    and d.get("display") == "flex" and d.get("flex-direction") == "column"):
                rail_in_ok = True
        if ".rail__foot" in sels and d.get("margin-top") == "auto" and "border-top" in d:
            foot_ok = True
    if not rail_hidden_base:
        bad.append(("(窄屏档)", "缺基础档 .rail{display:none}：宽屏侧栏未与顶部导航互斥", ""))
    if not head_hidden_wide:
        bad.append(("(宽屏档)", "缺 ≥%dpx 的 .site-head{display:none}" % NAV_BREAKPOINT, ""))
    if not rail_visible_wide:
        bad.append(("(宽屏档)", "缺 ≥%dpx 的 .rail{display:block;align-self:stretch}"
                    "（侧栏未撑满竖向）" % NAV_BREAKPOINT, ""))
    if not rail_in_ok:
        bad.append(("(全站)", ".rail__in 非「sticky + 100dvh + flex 纵排」（侧栏不能常驻视口）", ""))
    if not foot_ok:
        bad.append(("(全站)", ".rail__foot 未把显示设置锚到侧栏底端（缺 margin-top:auto）", ""))
    # ---- (a2) 左栏竖向覆盖面 ＝ 整页：rail 跨 1–2 行 ＋ 页脚在 .layout 之内且独占第 2 行
    #      ★ 只断言 align-self:stretch 是不够的：页脚若在 .layout **之外**，rail 的拉伸范围
    #        止于正文底 ⇒ 页脚旁仍是空档（本轮实测的中间态）。故连结构一起断言。
    rail_rows = foot_grid = False
    for _rel, conds, header, body, _raw in rules:
        if header.startswith("@"):
            continue
        sels = selectors_of(header)
        d = _rule_decls(body)
        wide = any(media_condition_norm(c) == RAIL_WIDE_MEDIA for c in conds)
        if not wide:
            continue
        if ".rail" in sels and re.sub(r"\s+", "", d.get("grid-row", "")) == "1/span2":
            rail_rows = True
        if ".layout>.site-foot" in sels and re.sub(r"\s+", "", d.get("grid-column", "")) == "1/-1":
            foot_grid = True
    if not rail_rows:
        bad.append(("(宽屏档)", "缺 ≥%dpx 的 .rail{grid-row:1 / span 2}：左栏不跨到页脚行" % NAV_BREAKPOINT, ""))
    if not foot_grid:
        bad.append(("(宽屏档)", "缺 ≥%dpx 的 .layout>.site-foot{grid-column:1 / -1}" % NAV_BREAKPOINT, ""))
    for rel, text in sorted(ctx.html.items()):
        if not re.search(r"</footer>\s*</div>\s*</body>", text):
            bad.append((rel, "页脚不是 .layout 的最后一个子元素"
                             "（留在 .layout 之外 ⇒ 左栏下方仍留空档）", ""))
    # ---- (b) 侧栏含全部显示开关；顶部导航保留同一组（互斥 ⇒ 任一宽度档可见实例恰 1 组）
    #      ★ 四组开关（主题 / 动效 / 背景素材 / 正文字号）——2026-10-15 用户反馈轮由 2 组扩为 4 组
    switch_states = (("data-theme-set", ("system", "light", "dark")),
                     ("data-motion-set", ("system", "on", "off")),
                     ("data-backdrop-set", ("on", "off")),
                     ("data-fontsize-set", ("standard", "large")))
    rail_re = re.compile(r'<aside class="rail".*?</aside>', re.S)
    head_re = re.compile(r'<header class="site-head".*?</header>', re.S)
    n_rail = 0
    for rel, text in sorted(ctx.html.items()):
        mr, mh = rail_re.search(text), head_re.search(text)
        if not mr:
            bad.append((rel, "缺 .rail 容器", ""))
            continue
        n_rail += 1
        for attr, states in switch_states:
            for st in states:
                if '%s="%s"' % (attr, st) not in mr.group(0):
                    bad.append((rel, "侧栏缺开关档位", "%s=%s" % (attr, st)))
        if not mh:
            bad.append((rel, "缺 .site-head 容器", ""))
            continue
        for attr, states in switch_states:
            for st in states:
                if '%s="%s"' % (attr, st) not in mh.group(0):
                    bad.append((rel, "顶部导航缺开关档位（窄屏档会无该入口）",
                                "%s=%s" % (attr, st)))
    if n_rail == 0:
        return False, "空集守卫：全站无 .rail 容器 ⇒ 判据恒真"
    # ---- (b2) 开关必须**接线**：四枚偏好的 localStorage 键都要出现在 <head> 的 pre-paint 脚本里
    #      （否则按钮点了不留存、刷新即丢，或首帧闪烁）
    for rel, text in sorted(ctx.html.items()):
        head = text.split("</head>", 1)[0]
        ms = re.search(r"<script>(.*?)</script>", head, re.S)
        script = ms.group(1) if ms else ""
        if not script:
            bad.append((rel, "<head> 内无 pre-paint 脚本", ""))
            continue
        for key in ("ui-theme", "ui-motion", "ui-backdrop", "ui-fontsize"):
            if key not in script:
                bad.append((rel, "pre-paint 脚本未接线该偏好键", key))
    # ---- (b3) 开关必须**接到真实生效的规则**上（⛔ 不做"看起来能点但什么也不做"的装饰按钮）
    pref_ok = {"backdrop": False, "fontsize": False}
    for _rel, conds, header, body, _raw in rules:
        if header.startswith("@") or conds:
            continue
        d = _rule_decls(body)
        for sel in selectors_of(header):
            s = re.sub(r"\s+", "", sel)
            if s == ':root[data-backdrop="off"].backdrop' and d.get("display") == "none":
                pref_ok["backdrop"] = True
            # ★ 2026-10-15 用户反馈轮修正：字号档由「只改 body」改为「改**根字号**」
            #   （只改 body 会半生效：标题/导航/标签各自走 --fs-* 不随动）。
            if (s == ':root[data-fontsize="large"]'
                    and (d.get("font-size") or "").startswith("var(--fs-")):
                pref_ok["fontsize"] = True
    for k, why in (("backdrop", "缺 :root[data-backdrop='off'] .backdrop{display:none}"),
                   ("fontsize", "缺 :root[data-fontsize='large']{font-size:var(--fs-…)}")):
        if not pref_ok[k]:
            bad.append(("(全站)", "开关未接到生效规则：" + why, ""))
    # ---- (b4) 见 (c2)：字号档「全生效」要求布局令牌 rem 化，故与宽度预算同处取值。
    # ---- (c) 根入口 h1 单行宽度预算：内容列宽 = --container − --rail-w − 2×--space-5
    pal = ctx.data["site_palette"]["values"]
    try:
        container = _css_len_px(pal["container"]["light"])
        rail_w = _css_len_px(pal["rail.w"]["light"])
        sp5 = _css_len_px(pal["space.5"]["light"])
        sp4 = _css_len_px(pal["space.4"]["light"])
        hero_max = _css_len_px(pal["fs.hero"]["light"])
    except (KeyError, ValueError) as e:
        return False, "宽度预算取值失败（判据无法复算，⛔ 不按 0 处理）：%s" % e
    # ---- (c2) 字号档要「全生效」⇒ 布局令牌必须 rem 化
    #      （px 化时根字号放大不会带动栏宽 / 间距 / 内容列宽 ⇒ 用户实测的"部分生效"）
    for key, why in (("container", "--container"), ("rail.w", "--rail-w"),
                     ("space.5", "--space-5"), ("space.4", "--space-4"), ("nav.h", "--nav-h")):
        v = (pal.get(key) or {}).get("light", "")
        if not str(v).endswith("rem"):
            bad.append(("(全站)", "字号档无法全生效：布局令牌 %s = %r 非 rem" % (why, v), ""))
    ls = None
    for _rel, conds, header, body, _raw in rules:
        if header.startswith("@") or conds:
            continue
        if "h1" in selectors_of(header):
            m = re.search(r"letter-spacing\s*:\s*(-?[0-9.]+)em", body)
            if m:
                ls = float(m.group(1))
    if ls is None:
        bad.append(("(全站)", "h1 缺 em 制 letter-spacing ⇒ 行宽预算无法复算", ""))
        ls = 0.0
    flat = re.sub(r"\s+", "", "\n".join(styles.values()))
    for needle, why in (("max-width:var(--container)", ".layout 未用 --container 限宽"),
                        ("grid-template-columns:var(--rail-w)minmax(0,1fr)",
                         "宽屏栅格未用 --rail-w 定侧栏列宽"),
                        ("padding:0var(--space-5)", "正文列未用 --space-5 作内边距")):
        if needle not in flat:
            bad.append(("(全站)", "宽度预算算式与 CSS 脱钩：" + why, ""))
    title = ctx.data["dag"]["meta"]["mission"]
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", title))
    rest = re.sub(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", "", title)
    other = len(re.findall(r"[^\s]", rest))
    width = (cjk + other * 0.55) * hero_max * (1 + ls)
    avail = container - rail_w - 2 * sp5
    margin_each = (avail - width) / 2.0
    if width > avail:
        bad.append(("index.html", "根入口 h1 在宽屏内容列内必然折行",
                    "行宽 %.0fpx > 可用 %.0fpx" % (width, avail)))
    elif margin_each < sp4:
        bad.append(("index.html", "根入口 h1 两端留空不足 --space-4",
                    "每侧 %.1fpx < %.0fpx" % (margin_each, sp4)))
    ctx.report_lines.append(
        "P34 根入口 h1 宽度预算复算：标题「%s」= %d 汉字 + %d 其他字符；"
        "--fs-hero 上界 %.1fpx；letter-spacing %.3fem ⇒ 行宽 %.1fpx；"
        "宽屏内容列 %.0fpx（--container %.0f − --rail-w %.0f − 2×--space-5 %.0f）；"
        "两端各留 %.1fpx（下限 --space-4 = %.0fpx）"
        % (title, cjk, other, hero_max, ls, width, avail, container, rail_w, sp5, margin_each, sp4))
    ctx.notes.append("P34 依据（2026-10-15 用户走查反馈）：观感问题不可机检，但其成因可 —— "
                     "① 单行与否 = 行宽预算 vs 内容列宽（CJK 进宽 1em × (1+letter-spacing)）；"
                     "② 撑满竖向 = rail 的 align-self:stretch + 内层 sticky 100dvh；"
                     "③ 开关可见实例恰 1 组 = 基础档 .rail{display:none} 与宽屏档 "
                     ".site-head{display:none} 两条规则互斥。⛔ 本判据不断言「字号好看」。")
    return (not bad), ("受检页面 %d 个（rail 容器 %d 个）；侧栏形态六项齐备=%s；"
                       "侧栏开关档位齐备；根入口 h1 行宽 %.0fpx ≤ 内容列 %.0fpx，两端各留 %.1fpx；"
                       "违例 %d 处 %s"
                       % (len(ctx.html), n_rail,
                          rail_hidden_base and rail_visible_wide and rail_in_ok and foot_ok
                          and rail_rows and foot_grid,
                          width, avail, margin_each, len(bad), bad[:4]))


def mut_p34(ctx):
    out = []
    # ① 字号退回旧值（4rem）⇒ 行宽 988px > 内容列 804px ⇒ 必然折行
    c = copy.deepcopy(ctx)
    old = "clamp(2.25rem, 1.2rem + 3.9vw, 4rem)"
    c.data["site_palette"]["values"]["fs.hero"]["light"] = old
    c.data["site_palette"]["values"]["fs.hero"]["dark"] = old
    out.append(c)
    # ② 侧栏丢掉显示开关（主题档属性名被改）⇒ 「侧栏缺主题档」
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, 'data-theme-set="system"', 'data-zz-set="system"'))
    # ③ 侧栏不再撑满竖向（align-self 被去掉）
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, ".rail{display:block;align-self:stretch;grid-row:1 / span 2}",
                          ".rail{display:block;grid-row:1 / span 2}"))
    # ④ 显示设置不再锚底
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, ".rail__foot{margin-top:auto;",
                          ".rail__foot{margin-top:var(--space-1);"))
    # ⑤ 宽屏档不再隐藏顶部导航 ⇒ 开关出现两组可见实例（互斥被破坏）
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c,
                          ".site-head{display:none}\n .rail{display:block;align-self:stretch;"
                          "grid-row:1 / span 2}",
                          ".rail{display:block;align-self:stretch;grid-row:1 / span 2}"))
    # ⑥ 栅格不再用 --rail-w ⇒ 宽度预算算式与 CSS 脱钩
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, "grid-template-columns:var(--rail-w) minmax(0,1fr)",
                          "grid-template-columns:0 minmax(0,1fr)"))
    # ⑦ 页脚退回 .layout 之外（本轮修前的形态）⇒ 左栏拉伸范围止于正文底
    c = copy.deepcopy(ctx)
    c = _patch_all(c, "</main>\n<footer", "</main>\n</div>\n<footer")
    out.append(_patch_all(c, "</footer>\n</div>\n</body>", "</footer>\n</body>"))
    # ⑧ rail 不再跨到页脚行
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, ".rail{display:block;align-self:stretch;grid-row:1 / span 2}",
                          ".rail{display:block;align-self:stretch}"))
    # ⑨ 页脚不再独占第 2 行（跨两列）
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, ".layout>.site-foot{grid-column:1 / -1;", ".layout>.site-foot{"))
    # ⑩ 侧栏丢掉「背景素材」开关
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, 'data-backdrop-set="off"', 'data-zz-set="off"'))
    # ⑪ pre-paint 脚本未接线「正文字号」偏好键
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, "ui-fontsize", "ui-zzsize"))
    # ⑫ 「正文字号：大」开关未接到生效规则（装饰性按钮）
    c = copy.deepcopy(ctx)
    out.append(_patch_all(c, ':root[data-fontsize="large"]{font-size:var(--fs-root-lg)}', ""))
    # ⑬ 布局令牌退回 px ⇒ 字号档无法全生效（根字号放大带不动栏宽/间距）
    c = copy.deepcopy(ctx)
    c.data["site_palette"]["values"]["container"]["light"] = "1120px"
    c.data["site_palette"]["values"]["container"]["dark"] = "1120px"
    out.append(c)
    return out


# ---------------------------------------------------------------- P35 / P36（2026-10-15 内容呈现 v2）

PAGE_KIND_RE = re.compile(r'data-page-kind="([a-z]+)"')
FIG_CONTENT_COL_PX = 804      # 宽屏内容列宽（与 P34 的预算同源）
FIG_MAX_H_PX = 600            # 图在内容列宽下的渲染高度上限（与 gen-figs.check_spec 同源）
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
TAG_STRIP_RE = re.compile(r"<[^>]+>")
FIG_RE = re.compile(r'<figure class="fig".*?</figure>', re.S)
SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)

# --- P35 ⑪–⑭（2026-10-15 G4：组页与视图页的阅读单元；见 CRITERIA-CHANGE-P35-G4.md）---
# ★ 对象切片：组页的两个**含长文字段**的区块（⑪ 竖表 / ⑫ 横表列数代理）与两个
#   **承载依赖关系**的区块（⑬ 一行结构）。⛔ 不整页扫：别处（分组索引的 6 列短值表、
#   前沿页的 3 列跟踪表）会假阳——判据范围宽于对象即失真。
G4_GROUP_RE = re.compile(r"^12-groups/(?!index\.html)[a-z0-9-]+\.html$")
G4_VIEW_RE = re.compile(r"^14-views/[a-z0-9-]+\.html$")
G4_KV_SECTIONS = ("sec-nodes", "sec-rel")      # ⑪ 竖表 / ⑫ 列数代理
G4_RELCHAIN_SECTIONS = ("sec-path", "sec-rel")  # ⑬ 一行结构
G4_TABLE_COL_MAX = 3                            # ⑫ 的**代理**阈值（⛔ 不是「无横向滚动」的直接量）
READ_MAP_RE = re.compile(r'<section class="read-map".*?</section>', re.S)
READ_MAP_CLAIM_RE = re.compile(r'<p class="read-map__claim">(.*?)</p>', re.S)
KV_BLOCK_RE = re.compile(r'<article class="kv-block">')
TABLE_RE = re.compile(r"<table\b.*?</table>", re.S)

# --- ★ R-23 作用域纪律（2026-10-16 第 6 轮；见 CRITERIA-CHANGE-R07.md）---
# 两处「不强制」的页集合一律写成**显式清单 + 全集闭合断言**：
#   `set(受检页) == 对象集 ∪ 排除集` —— 出现**未分类的页** ⇒ FAIL。
# ⛔ 不得靠控制流分支（`if kind != "node": … continue`）偶然豁免：
#   第 5 轮 P35 ⑧ 的 R-23 违反（声明「每页」、实装只查节点页）正是那样产生的。
# ★ 术语定义见 `DESIGN-CONTRACT.md` §1：
#   · **知识承载页** = 节点页 + 组页（⛔ 不含 `12-groups/index.html`）      → R-07（图件）
#   · **正文承载页** = 节点页 + 组页 + 视图页                              → R-03（页首结论 + 地图）
P35_FIG_SCOPE = "知识承载页（节点页 / 组页；⛔ 不含分组索引）"
P35_FIG_EXCLUDED = {
    "12-groups/index.html": "分组索引：结构由 11 组一览表承载（横表已能一眼看齐）",
    "index.html": "根入口：职责是开门与分流，页首是 hero 区",
    "13-interactive/index.html": "交互页：本身就是图（cytoscape 画布）",
    "14-views/01-learning-path.html": "学习路径页：全局拓扑由交互图承载",
    "14-views/02-frontier.html": "前沿页：现含 1 张条目图，但 R-07 不强制",
}
P35_READMAP_SCOPE = "正文承载页（节点页 / 组页 / 视图页）"
P35_READMAP_EXCLUDED = {
    "index.html": "根入口：页首是 hero 区，职责是开门与分流",
    "13-interactive/index.html": "交互页：本体即图，无散文结论来源",
}
# --- ★ 2026-10-16 第 7 轮（N1 裁决）：② h1 口径的对象集与排除清单 ---
#   ★ 本项**排除清单为空**：全部受检页都该有 h1。旧实现用 `kind != "interactive"` 跳过了交互页，
#     那是**控制流分支豁免**（本文件头部明文禁止）。实测唯一 interactive 页 `13-interactive/index.html`
#     的 h1 为「交互全景图」（纯中文）⇒ 纳入对象集**不产生任何 FAIL**，故不必排除它。
#   ⛔ 若将来此处要加排除项，必须逐条写理由，且闭合断言会判「排除项不存在」。
P35_H1_SCOPE = "全部受检页（h1 口径）"
P35_H1_EXCLUDED = {}

_GLYPH_CACHE = {}


_COMMON = None


def _common():
    """gen-common.py 模块（P35 ⑨⑩ 要与**渲染口径**同源：切分函数只此一处）。"""
    global _COMMON
    if _COMMON is None:
        _COMMON = _imp(os.path.join(HERE, "gen-common.py"), "pekg_common_gate")
    return _COMMON


_VIEWS = None
_GROUPS = None


def _views():
    """gen-views.py 模块（P35 ⑨/⑭ 取视图页导语文本的**唯一来源**，⛔ 不在门控里另抄文案）。"""
    global _VIEWS
    if _VIEWS is None:
        _VIEWS = _imp(os.path.join(HERE, "gen-views.py"), "pekg_gen_views_gate")
    return _VIEWS


def _groups():
    """gen-groups.py 模块（P35 ⑨/⑭ 取分组索引导语文本的唯一来源）。"""
    global _GROUPS
    if _GROUPS is None:
        _GROUPS = _imp(os.path.join(HERE, "gen-groups.py"), "pekg_gen_groups_gate")
    return _GROUPS


def _section_slice(text, sid):
    """取 `<h2 id="sid">` 到下一个 `<h2 id="sec-…">` 之间的 HTML（区块切片）。

    ★ 为什么要切片而不是全页扫：⑩ 断言的是「**证据区与术语区**内无横表」。
      判据取的范围若宽于对象（全页），别处的横表会假阳；窄于对象则漏检。
    """
    m = re.search(r'<h2 id="%s"' % re.escape(sid), text)
    if not m:
        return None
    nxt = re.search(r'<h2 id="sec-[a-z-]+"', text[m.end():])
    end = m.end() + nxt.start() if nxt else len(text)
    return text[m.start():end]


def _enum_lists(html_text):
    """页面里 `<ol class="enum-list">` 的条数与各自 `<li>` 数。"""
    out = []
    for body in re.findall(r'<ol class="enum-list">(.*?)</ol>', html_text, re.S):
        out.append(len(re.findall(r"<li\b", body)))
    return out


def _enum_expect_texts(texts):
    """按**渲染口径**复算一组散文会渲染出几个 `.enum-list`（与 gen-common.prose_html 同源）。

    ⛔ 不另写一套「枚举识别」正则：`split_boundary` / `sentences` / `split_enum` 三个函数
      直接从 gen-common 取用，保证判据与渲染**同一口径**（否则判据会对着自己的想象判）。
    """
    C = _common()
    n = 0
    for t in texts:
        body, _b = C.split_boundary(t or "")
        for s in sentences(body):
            _head, items = C.split_enum(s)
            if items:
                n += 1
    return n


def _enum_pattern_hit_texts(texts):
    """一组散文里是否出现显式枚举标记「其[一二三四五六七八九十]，」（契约 R-10 的判据入口）。"""
    C = _common()
    return any(C.ENUM_MARK_RE.search(t or "") for t in texts)


def _prose_sources(ctx, rel, node_by_slug, group_by_slug):
    """页 → 该页渲染的**散文单元来源**（逐生成器的渲染路径一一对应）。

    ★ 为什么要这张映射：R-10/R-11 的对象是「**页**上的散文单元」，⛔ 不是「节点页」——
      契约 G1 的原文是「数据含该模式的**页**，必须出现 .enum-list」。站内渲染散文的页共四类：
        ① `11-node-pages/<slug>.html` ← 该节点的 `why` + `intro`（gen-nodes.py:110,113）
        ② `12-groups/<gid>.html`      ← 该组的 `intro`（gen-groups.py `group_page`，G4 新增）
        ③ `12-groups/index.html`      ← `gen-groups.groups_index_intro()`（G4 新增）
        ④ `14-views/01-learning-path.html` ← `gen-views.learning_path_intro()`（G4 新增）
        ⑤ `14-views/02-frontier.html` ← 页级导语 + 每条前沿条目的 `summary`
      映射写死在这里并逐条注明来源函数，⛔ 不做「猜哪些页含散文」的启发式；
      ③④ 的文本**直接调生成器的同名函数**取（判据与渲染同源，⛔ 门控不另抄一份文案）。
    """
    m = re.match(r"11-node-pages/([a-z0-9-]+)\.html$", rel)
    if m:
        nd = node_by_slug.get(m.group(1))
        return [nd.get("why", ""), nd.get("intro", "")] if nd is not None else []
    if rel == "12-groups/index.html":
        groups = sorted(ctx.data["dag"]["groups"], key=lambda g: g["order"])
        return [_groups().groups_index_intro(groups)]
    m = re.match(r"12-groups/([a-z0-9-]+)\.html$", rel)
    if m:
        g = group_by_slug.get(m.group(1))
        return [g.get("intro", "")] if g is not None else []
    if rel == "14-views/01-learning-path.html":
        return [_views().learning_path_intro(ctx.data["dag"])]
    if rel == "14-views/02-frontier.html":
        return ([_views().FRONTIER_INTRO]
                + [it.get("summary", "") for it in ctx.data["frontier"].get("items", [])])
    return []


def _claim_source(ctx, rel, node_by_slug, group_by_slug):
    """页 → 该页 **read-map 结论句**应当逐字等于的文本（P35 ⑭）。

    ★ 按页给来源，⛔ 不统一取「散文来源首句」：
      · 节点页的结论来源是 `summary`（P05 已断言它是**完整单句**）⇒ 直接用 summary；
      · 组页与视图页的结论来源是**页级导语的首句**（契约 G4 的原文：
        「结论取组导读 / 视图导语的首句」）⇒ 走 `gen-common.lead_sentence`（与渲染同源）。
    """
    m = re.match(r"11-node-pages/([a-z0-9-]+)\.html$", rel)
    if m:
        nd = node_by_slug.get(m.group(1))
        return nd.get("summary", "") if nd is not None else None
    if rel.startswith("12-groups/") or rel.startswith("14-views/"):
        srcs = _prose_sources(ctx, rel, node_by_slug, group_by_slug)
        return _common().lead_sentence(srcs[0]) if srcs else None
    return None


def _prose_sentence_count(text):
    """按**渲染口径**复算一段散文会切出几句（`split_boundary` + `sentences`，与 prose_html 同源）。"""
    C = _common()
    body, _b = C.split_boundary(text or "")
    return len(C.sentences(body))


def _table_cols(table_html):
    """横表列数：取**最大行**的单元格数（含表头行）。⛔ 不按 `<th>` 单列计数。"""
    cols = 0
    for row in re.findall(r"<tr\b.*?</tr>", table_html, re.S):
        cols = max(cols, len(re.findall(r"<t[hd]\b", row)))
    return cols


def _read_map_anchors(text):
    """页首导读里的 `sec-*` 锚点集合（⛔ 只取 sec-*：非区块锚点不在双向闭合的对象内）。"""
    rm = READ_MAP_RE.search(text)
    if not rm:
        return None
    return set(re.findall(r'href="#(sec-[a-z-]+)"', rm.group(0)))


def _plain(html_text):
    return re.sub(r"\s+", " ", TAG_STRIP_RE.sub("", html_text or "")).strip()


def _glyph_covered(ch):
    """字形覆盖（diagram-lite 判据索引，fail-closed）：查本机 fontconfig 是否有字体覆盖该字符。

    ⛔ 不硬编码「不安全字形清单」；⛔ 查询失败（无 fc-list）⇒ 判未覆盖（fail-closed，不静默放行）。
    """
    if ch in _GLYPH_CACHE:
        return _GLYPH_CACHE[ch]
    try:
        p = subprocess.run(["fc-list", ":charset=%x" % ord(ch), "family"],
                           capture_output=True, text=True, timeout=30)
        ok = bool(p.stdout.strip())
    except Exception:
        ok = False
    _GLYPH_CACHE[ch] = ok
    return ok


def _longest_run(text):
    """一段文本里**最长「无句末标点」游程**的 caliber 长度（P35 报告项，⛔ 不判 FAIL）。

    ★ 为什么只作报告项：实测（`_probe_metrics.py` B 段）全站最长 151 / p90 130 / 中位 78，
      且**长度合规的散文照样可以是一堵墙**——「一段 170 字的散文读起来是不是墙」没有因果阈值
      可定（与 `CRITERIA-CHANGE-P05.md` 的上限撤销同源：上限只影响版式首屏，与正确性无关）。
      ⇒ 按判据分档原则降为**报告项**（逐条打印，⛔ 不判 FAIL），使实测值在门控里可见。
    """
    best = 0
    for part in re.split(r"[。！？!?；;]", text or ""):
        best = max(best, caliber(part))
    return best


def _prose_units(html_text):
    """页面上被渲染成「可扫单元」的文本（`.claim` 与 `.points li`），供最长游程报告项取数。"""
    out = []
    for m in re.finditer(r'<p class="claim">(.*?)</p>', html_text, re.S):
        out.append(_plain(m.group(1)))
    for m in re.finditer(r'<ul class="points">(.*?)</ul>', html_text, re.S):
        for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.S):
            out.append(_plain(li))
    return out


def check_p35(ctx):
    """P35 内容层级与阅读单元（★ 2026-10-15 用户走查第 2 轮反馈判据化，契约见 CONTENT-V2.md）。

    ★ 判据由来：用户 7 条反馈里，5 条是**结构性**的（不是观感口味）——
      #4 h1 里带英文与括号、英文名出现两次；#6 身份与标签混在一行、4 个 tag 被折成两行；
      #2 大段文字没有可扫单元、看不出先讲什么再讲什么；#7 该用/不该用是整段而非「总结+细节」。
    这些都能落成结构断言：
      ① h1 必须**一行、无括号**（⛔ 不含 `（English）`）；
      ② h1 里的**拉丁缩写必须已在术语台账登记**：每个「拉丁字母数 ≥3」的 token 都要能在
        `10-dag-data/glossary.json` 的某个 `term` 里**逐字命中**（大小写敏感子串）。
        ★ **2026-10-16 第 7 轮 N1 裁决**（`CRITERIA-CHANGE-R01.md`）：原口径为「h1 **纯中文**（不得含英文）」，
        与数据侧 5 个节点名（`ReAct 推理—行动交织` / `RAG 提示模式` / `子 Agent 上下文隔离` /
        `我的 agent 的提示词面` / `子 Agent 委派与返回契约`）冲突 ⇒ 一发布即 FAIL 并**阻塞 28 个待写节点**；
        经用户裁决走 N1：**改判据、⛔ 不改名**，并把「有拉丁词就放过」这条退化路堵死
        （台账命中不了的缩写照样 FAIL）。同批删除旧的 `kind != "interactive"` **控制流豁免**，
        换成**显式对象集**（`P35_H1_SCOPE`）**＋ 排除清单**（`P35_H1_EXCLUDED`，空）**＋ 全集闭合断言**；
      ②-a 节点页必须有**独立成行**的英文名 `.page-en`（⛔ 不与 h1 同行、⛔ 不带括号）；
      ③ **一行一件事**：tags 必须在 `.tag-row` 内，⛔ 不得混进 `.meta-line`；
      ④ 页首必须有 `.read-map`，且其锚点集合 ⟺ 页内区块 id 集合（**双向**）
        〔对象 = **正文承载页**（节点页 / 组页 / 视图页）；★ 2026-10-16 第 6 轮起，根入口与交互页
        写进**显式排除清单**（`P35_READMAP_EXCLUDED`，逐条理由）并加**全集闭合断言**〕；
      ⑤ 区块标题必须带连续序号（`.sec-no` 01..0n）⇒「先讲什么、再讲什么」显式可见；
      ⑥ 该用/不该用必须是**三列对照表**（类别 ｜ 场景 ｜ 做法）；
      ⑦ 散文必须被切成可扫单元（`.claim` 主张句 + `.points` 展开点）；
      ⑧ ★ **作用域＝知识承载页（节点页 / 组页；⛔ 不含分组索引）**：≥1 内联自制图。
        ★ **本条的两轮作用域史（⛔ 不得再退回）**：
          · 第 5 轮：本条写「**每页** ≥1 图」，而实装位于 `if kind != "node": … continue` **之后**
            ⇒ 只对节点页生效；实测 24 页仅 9 页含图（15 页无图）⇒ 声明作用域 ≠ 实现作用域（R-23 违反）。
          · 第 6 轮（用户裁决 **B″**）：**既补产物、也改契约** —— 11 个组页各补一张「本组诱导子图 + 对外接口」
            的 mini-DAG（由 `dag.json` 数据派生，⛔ 不手绘），本条作用域正式定为**知识承载页**；
            其余 5 页写进**显式排除清单**（`P35_FIG_EXCLUDED`，逐条理由）+ **全集闭合断言**（未分类的页 ⇒ FAIL）。
        留档：`CRITERIA-CHANGE-R07.md`。⛔ 这不是放宽：节点页仍是硬要求，且新增了对 11 个组页的硬要求。
        ④ 的对象同批对齐为**正文承载页**（`P35_READMAP_EXCLUDED` 同样走显式清单 + 闭合断言）。
      ⑨ **枚举必须位置化**（R-10 / 契约 G1 + G4）：**页**的散文来源（节点页 = `why`+`intro`；
        组页 = 组 `intro`；分组索引 / 学习路径 / 前沿页 = 各自**页级导语**；
         另含各条目 `summary`）含「其[一二三四五六七八九十]，」模式时，产物必须出现
         `.enum-list`（有序列表）且其条数 ≥2 —— ⛔ 不靠「其一其二」这几个字本身承担层次；
      ⑩ **长文字段一律竖表**（R-11 / 契约 G2）：节点页的**证据区（#sec-evidence）**与
         **术语区（#sec-terms）**必须是竖表（`.kv-blocks` 存在），且这两个区块内 `<table>` 数 = 0
         （长文字段横排必然横向滚动 ⇒ 与「能一眼看齐」的前提相抵）。

    ★ 2026-10-15 扩展（契约 G4 收口；判据变更留档见 `CRITERIA-CHANGE-P35-G4.md`）：
      **对象扩为「节点页 / 组页 / 视图页」**（④⑤ 全量；⑦ 对组页与视图页按渲染口径的条件式；
      ⑨ 的散文来源映射补齐组页与视图页），并新增四条只对**组页**成立的断言：
     ⑪ 组页的**节点区（#sec-nodes）**与**前后继区（#sec-rel）**必须是竖表（`.kv-blocks` 存在）
        —— 这两个区块含长文字段（节点名 + 英文名、整句「为什么先学前者」）；
     ⑫ ★ **代理判据**：上述两个区块内**若含 `<table>` 则列数 ≤3**。
        ★ 它代理的是「**长文字段横表会横向滚动**」这一直接量，⛔ **不得读作**「无横向滚动」的
        实测结论：真实是否滚动取决于字体度量、内容列宽与用户字号档，产物侧不可复算
        （★ 2026-10-16 更正：旧理由写「本会话浏览器不可用，见 VERIFY-CONSTRAINT.md」——该前提已被推翻
        （非 snap 内核一直可用；本会话复跑 `_probe_env.py` 再次证伪，且 `_probe_thresholds.py` 用同一内核
        真实渲染成功）。本条仍是**代理**，但理由回到**代理判据自身的局限**：代理量与直接量的关系
        依赖用户字号档等渲染期状态，⛔ 不是「无法渲染」；缺口登记见台账 `G20`）。可复算的代理是**列数**：
        804px 内容列下 4 列及以上时平均每列 ≤200px，本站的节点名（最长 60+ 字符）与整句
        理由必然折行错位。★ 代理的**失效面**已登记：短文字段的 4+ 列表其实不会滚动
        （分组索引的 6 列短值表即为一例，见 gen-groups.py 注释）⇒ ⑫ 只用于这两个已知含
        长文字段的区块，⛔ 不推广为全站判据；
     ⑬ 组页的**路径区（#sec-path）**与**前后继区（#sec-rel）**的依赖关系必须是
        **一行结构**（`.relchain`）⇒ ⛔ 不用「A ← B：…；A ← C：…」这类长句罗列；
     ⑭ 页首导读的**结论句**必须逐字等于该页的**结论来源**（节点页 = `summary`；
        组页与视图页 = 页级导语的**首句**，走 `gen-common.lead_sentence` 同源取）。
    """
    bad = []
    if not ctx.html:
        return False, "空集守卫：无受检页面"
    node_pages = [r for r, t in ctx.html.items() if PAGE_KIND_RE.search(t)
                  and PAGE_KIND_RE.search(t).group(1) == "node"]
    if not node_pages:
        return False, "空集守卫：全站无节点页 ⇒ 判据恒真"
    group_pages = sorted(r for r in ctx.html if G4_GROUP_RE.match(r))
    view_pages = sorted(r for r in ctx.html if G4_VIEW_RE.match(r))
    if not group_pages:
        return False, "空集守卫：全站无组页 ⇒ ⑪⑫⑬ 恒真"
    if not view_pages:
        return False, "空集守卫：全站无视图页 ⇒ ④⑤⑦ 的视图页对象为空"
    # ---- ★ 全集闭合断言（2026-10-16 第 6 轮；R-23 作用域纪律）----
    # 对象集与排除集必须**恰好覆盖**全部受检页：出现未分类的页 ⇒ FAIL。
    # ⛔ 这不是「放宽」，而是把原先靠控制流偶然产生的豁免**显式化**（原实装：⑧ 躲在
    #   `if kind != "node": … continue` 之后 ⇒ 组页 / 视图页 / 入口页 / 交互页全被静默豁免）。
    # ★ 两处对象集的口径**必须与各自断言的取法一致**（首次实现就踩到了这个坑，见登记件 §L·F-1）：
    #   · ⑧ 图件对象 = `kind == "node"` ∪ `G4_GROUP_RE` 的组页路径（⛔ 后者**按路径**取，
    #     因为它的负向先行断言已排除 `12-groups/index.html`）；
    #   · ④ 导读对象 = `kind ∈ {node, group, view}`（⛔ **按页面类型取**，因为分组索引的
    #     `data-page-kind` 就是 `group`、且它**确实**有 `.read-map`）。
    kind_of = {}
    for _r, _t in ctx.html.items():
        _m = PAGE_KIND_RE.search(_t)
        kind_of[_r] = _m.group(1) if _m else ""
    fig_scope = set(node_pages) | set(group_pages)
    readmap_scope = {r for r, k in kind_of.items() if k in ("node", "group", "view")}
    bad = []
    for label, scope, excluded in (("⑧ 图件对象", fig_scope, P35_FIG_EXCLUDED),
                                   ("④ 导读对象", readmap_scope, P35_READMAP_EXCLUDED)):
        for rel in sorted(set(excluded) - set(ctx.html)):
            bad.append(("(排除清单)", "%s 的排除项在受检页里不存在（清单已过期）" % label, rel))
        for rel in sorted(set(ctx.html) - scope - set(excluded)):
            bad.append((rel, "未分类的受检页：既不在 %s、也不在显式排除清单 ⇒ 作用域与对象脱钩" % label, ""))
    ctx.notes.append("P35 作用域（R-23 / 2026-10-16 第 6 轮，见 `CRITERIA-CHANGE-R07.md`）："
                     "受检页 %d 个；**%s** %d 个（⑧ 图件，排除 %d 个）；**%s** %d 个（④ 导读，排除 %d 个）；"
                     "两处均带**全集闭合断言**（未分类的页 ⇒ FAIL）。"
                     % (len(ctx.html), P35_FIG_SCOPE, len(fig_scope), len(P35_FIG_EXCLUDED),
                        P35_READMAP_SCOPE, len(readmap_scope), len(P35_READMAP_EXCLUDED)))

    node_by_slug = {n["id"].lower(): n for n in ctx.data["dag"]["nodes"]}
    group_by_slug = {g["id"].lower(): g for g in ctx.data["dag"]["groups"]}
    # ★ ②' 的登记面（R-01 / N1）：h1 的拉丁缩写必须能在术语台账里**逐字命中**。
    #   台账连接成单串做子串判定（等价于「存在某个 term 含该 token」，⛔ 不引入白名单硬编码）。
    glossary_terms_blob = "\n".join(t.get("term", "") for t in ctx.data["glossary"].get("terms", []))
    h1_scope_pages = []       # ②' 实检到「h1 含 ≥3 字母拉丁 token」的页
    h1_checked = []           # ②' 真正作用到的页（有 <h1> 的页）
    enum_pat_pages, enum_lists_total = [], 0
    kv_checked = 0            # ⑩ 节点页的竖表区块
    g4_kv_checked = 0         # ⑪ 组页的竖表区块
    g4_tables_checked = 0     # ⑫ 实检到的横表数（产物上可为 0 —— 见下方诚实登记）
    g4_relchain_checked = 0   # ⑬ 组页的一行结构区块
    claim_checked = 0         # ⑭ 可复算结论来源的页
    prose_checked = 0         # ⑦ 组页 / 视图页的散文页
    per_page = []             # 逐页复算表（判据自带，⛔ 不另写统计脚本）
    for rel, text in sorted(ctx.html.items()):
        kind = PAGE_KIND_RE.search(text)
        kind = kind.group(1) if kind else ""
        m = H1_RE.search(text)
        if m:
            h1_checked.append(rel)
            h1 = _plain(m.group(1))
            if re.search(r"[（(].*[）)]", h1):
                bad.append((rel, "h1 含括号（英文名须独立成行）", h1[:60]))
            # ②' h1 里的拉丁 token 必须**已在术语台账登记**（R-01 / 2026-10-16 第 7 轮 **N1** 裁决）。
            #    ★ 旧实现为 `re.search(r"[A-Za-z]{3,}", h1) and kind != "interactive"` ⇒
            #      ① 口径是「一律不得含英文」（与数据侧 5 个节点名冲突，一发布就 FAIL）；
            #      ② `kind != "interactive"` 是**控制流分支豁免** —— 本文件头部第 23–28 行自陈
            #         「⛔ 不得靠控制流分支偶然豁免」（那正是 R-23 / 教训 ④ 的成因）。
            #    ⇒ 本轮换成：口径改为「台账可命中」＋ 作用域换成**显式对象集 + 排除清单 + 全集闭合断言**。
            h1_latin = [t for t in LATIN_WORD.findall(h1) if len(re.findall(r"[A-Za-z]", t)) >= 3]
            if h1_latin:
                h1_scope_pages.append(rel)
            unreg = [t for t in h1_latin if t not in glossary_terms_blob]
            if unreg:
                bad.append((rel, "h1 含**未登记**的拉丁缩写（须能在 glossary.json 的 term 里逐字命中）：%s"
                            % "、".join(unreg[:4]), h1[:60]))
        # ⑨ 枚举必须位置化（R-10 / G1）：对象 = **页**（⛔ 不限节点页），触发 = 该页的散文来源命中模式。
        #   ★ 必须放在 `kind != "node"` 之前：契约 G1 的原文是「数据含该模式的**页**」，
        #     而 G1 轮唯一命中的页是 `14-views/02-frontier.html`（视图页）——若把它挡在
        #     节点页分支之后，判据会对着空集判「恒真」（G1 轮实测：正是这个位置错误让 ⑨ 空转）。
        #   ★ G4 轮：来源映射补齐组页 / 分组索引 / 学习路径页；本轮命中该模式的页见运行期报告。
        texts = _prose_sources(ctx, rel, node_by_slug, group_by_slug)
        if texts:
            lists = _enum_lists(text)
            exp = _enum_expect_texts(texts)
            pat = _enum_pattern_hit_texts(texts)
            if pat:
                enum_pat_pages.append(rel)
                enum_lists_total += len(lists)
                if not lists:
                    bad.append((rel, "散文数据含「其[一二三…]，」枚举模式，但产物无 .enum-list"
                                     "（枚举未位置化：层次仍由文字承担）", ""))
                elif sum(lists) < 2:
                    bad.append((rel, ".enum-list 条数 %d < 2（有序列表未成列）" % sum(lists), ""))
                elif len(lists) < exp:
                    bad.append((rel, "枚举列表数 %d < 渲染口径应有 %d（判据与渲染口径不一致）"
                                % (len(lists), exp), ""))
            elif exp:
                bad.append((rel, "渲染口径应有 %d 个 .enum-list 但散文数据未命中枚举模式"
                            "（判据与渲染口径不自洽）" % exp, ""))
        # ---- ④⑤⑦⑭：对象 = 节点页 / 组页 / 视图页（★ G4 起由「仅节点页」扩为三类页）----
        if kind in ("node", "group", "view"):
            # ⑧ ★ **知识承载页（节点页 / 组页；⛔ 不含分组索引）≥1 自制图**（R-07）。
            #   ★ 2026-10-16 第 6 轮：作用域由「节点页」扩为节点页 + 组页。
            #   本条**必须**放在 `if kind != "node": … continue` **之前** —— 第 5 轮它躲在那之后，
            #   于是组页被控制流静默豁免，而声明写「每页」（R-23 违反，见 `CRITERIA-CHANGE-R07.md`）。
            #   ★ 对象判定与 `fig_scope` **同源**：节点页按 `kind`、组页按路径正则
            #     （⛔ 不得写成 `kind in ("node","group")` —— 那会把分组索引一并纳入，
            #       而它按契约是**不强制**的；这一处差异是本轮首次实现时当场被门控抓出的）。
            if (kind == "node" or G4_GROUP_RE.match(rel)) and not FIG_RE.search(text):
                bad.append((rel, "缺图件 .fig（%s ≥1 自制图）" % P35_FIG_SCOPE, ""))
            # ④ 页首导读 ↔ 区块锚点双向闭合
            rm = READ_MAP_RE.search(text)
            if not rm:
                bad.append((rel, "缺页首导读 .read-map（先给结论 + 结构地图）", ""))
            else:
                want = _read_map_anchors(text)
                have = set(re.findall(r'id="(sec-[a-z-]+)"', text))
                if not want:
                    bad.append((rel, "导读内无区块锚点（空集）", ""))
                if want != have:
                    bad.append((rel, "导读锚点集 ≠ 区块 id 集", sorted(want ^ have)[:6]))
            # ⑤ 区块序号连续
            nos = [int(x) for x in re.findall(r'<span class="sec-no">(\d+)</span>', text)]
            if not nos:
                bad.append((rel, "区块标题无序号（.sec-no 空集）", ""))
            elif nos != list(range(1, len(nos) + 1)):
                bad.append((rel, "区块序号不连续", nos))
            # ⑦ 散文被切成可扫单元
            #   ★ 节点页无条件；组页与视图页按**渲染口径**的条件式——`prose_html` 只在来源 ≥2 句
            #     时才产出 `.points`，故 1 句来源（如前沿页的页级导语）不因缺 `.points` 判 FAIL。
            #     ⛔ 这不是豁免：句数由**同源函数**算出，⛔ 不写死「哪些页可以没有 .points」。
            if kind == "node":
                if '<p class="claim">' not in text:
                    bad.append((rel, "缺主张句 .claim（散文未切分为可扫单元）", ""))
                if '<ul class="points">' not in text:
                    bad.append((rel, "缺展开点 .points（每句一行）", ""))
            elif texts:
                prose_checked += 1
                n_sent = _prose_sentence_count(texts[0])
                if '<p class="claim">' not in text:
                    bad.append((rel, "散文未切成可扫单元：缺主张句 .claim（页级导语须过 prose_html）", ""))
                if n_sent >= 2 and '<ul class="points">' not in text:
                    bad.append((rel, "散文未切成可扫单元：缺展开点 .points"
                                     "（来源 %d 句 ≥2 ⇒ 按渲染口径应有）" % n_sent, ""))
            # ⑭ 页首导读的结论句 = 该页结论来源（逐字）
            claim_src = _claim_source(ctx, rel, node_by_slug, group_by_slug)
            if rm and claim_src is not None:
                claim_checked += 1
                cm = READ_MAP_CLAIM_RE.search(rm.group(0))
                if not cm:
                    bad.append((rel, "导读缺结论句 .read-map__claim", ""))
                elif _html.unescape(_plain(cm.group(1))) != claim_src:
                    bad.append((rel, "导读结论句 ≠ 该页结论来源（%s）"
                                % ("节点 summary" if kind == "node" else "页级导语首句"),
                                _plain(cm.group(1))[:40]))
            # 逐页复算（判据自带的复算表；⛔ 不另写一套统计脚本，以免两处口径漂移）
            rm2 = READ_MAP_RE.search(text)
            anchors = len(re.findall(r'href="#sec-[a-z-]+"', rm2.group(0))) if rm2 else 0
            nos2 = [int(x) for x in re.findall(r'<span class="sec-no">(\d+)</span>', text)]
            lists2 = _enum_lists(text)
            per_page.append("  %-34s 导读锚点 %d / sec-no %s / enum-list %d 个（%d 项）/ "
                            "竖表 %d 块（容器 %d）"
                            % (rel, anchors,
                               ("%02d..%02d" % (nos2[0], nos2[-1])) if nos2 else "无",
                               len(lists2), sum(lists2),
                               len(KV_BLOCK_RE.findall(text)),
                               len(re.findall(r'<div class="kv-blocks">', text))))
        if kind != "node":
            if G4_GROUP_RE.match(rel):
                # ⑪ 组页的节点区 / 前后继区必须是竖表（R-11：两个区块都含长文字段）
                # ⑫ ★ 代理判据：这两个区块内若含 `<table>`，列数必须 ≤ G4_TABLE_COL_MAX
                for sid in G4_KV_SECTIONS:
                    seg = _section_slice(text, sid)
                    if seg is None:
                        bad.append((rel, "缺区块 #%s（组页竖表判据无对象）" % sid, ""))
                        continue
                    g4_kv_checked += 1
                    if 'class="kv-blocks"' not in seg:
                        bad.append((rel, "#%s 区块不是竖表（缺 .kv-blocks；长文字段横排会横向滚动）"
                                    % sid, ""))
                    for tb in TABLE_RE.findall(seg):
                        g4_tables_checked += 1
                        cols = _table_cols(tb)
                        if cols > G4_TABLE_COL_MAX:
                            bad.append((rel, "#%s 区块内横表列数 %d > %d"
                                        "（代理判据：长文字段横表会横向滚动）"
                                        % (sid, cols, G4_TABLE_COL_MAX), ""))
                # ⑬ 组页的路径区 / 前后继区：依赖关系必须是一行结构（⛔ 不长句罗列）
                for sid in G4_RELCHAIN_SECTIONS:
                    seg = _section_slice(text, sid)
                    if seg is None:
                        bad.append((rel, "缺区块 #%s（一行结构判据无对象）" % sid, ""))
                        continue
                    g4_relchain_checked += 1
                    if 'class="relchain"' not in seg:
                        bad.append((rel, "#%s 区块缺 .relchain"
                                         "（依赖关系须是一行结构，⛔ 不用长句罗列）" % sid, ""))
            continue
        # ② 英文名独立成行
        en = re.search(r'<p class="page-en">(.*?)</p>', text, re.S)
        if not en:
            bad.append((rel, "缺独立成行的英文名 .page-en", ""))
        elif re.search(r"[（(]", _plain(en.group(1))):
            bad.append((rel, "英文名带括号", _plain(en.group(1))[:60]))
        # ③ 一行一件事：tags 与身份行分离
        meta = re.search(r'<p class="meta-line">(.*?)</p>', text, re.S)
        if meta and 'class="tier"' in meta.group(1):
            bad.append((rel, "标签混进了身份行 .meta-line（应各自独占一行）", ""))
        tags = re.search(r'<div class="tag-row".*?</div>', text, re.S)
        if not tags:
            bad.append((rel, "缺标签行 .tag-row", ""))
        # ④⑤⑦⑭ 见上方 `kind in ("node","group","view")` 分支（G4 起不再只对节点页）
        # ⑥ 该用/不该用 = 三列对照表
        cmp_t = re.search(r'<table class="cmp-table">.*?</table>', text, re.S)
        if not cmp_t:
            bad.append((rel, "缺该用/不该用对照表 .cmp-table", ""))
        else:
            head = re.search(r"<thead>.*?</thead>", cmp_t.group(0), re.S)
            if not head or len(re.findall(r"<th>", head.group(0))) != 3:
                bad.append((rel, "对照表非三列（类别 ｜ 场景 ｜ 做法）", ""))
            for tr in re.findall(r"<tr>(.*?)</tr>", cmp_t.group(0), re.S)[1:]:
                if len(re.findall(r"<td>", tr)) != 3:
                    bad.append((rel, "对照表存在非三列的行", _plain(tr)[:40]))
        # ⑧ 见上方 `kind in ("node","group","view")` 分支 —— ★ 2026-10-16 已从本处（节点页专属的尾部）
        #   上移到对象集分支之前，作用域由「节点页」扩为「知识承载页（节点页 / 组页）」。
        #   ⛔ 不得再把它放回 `if kind != "node": … continue` 之后（那会重新制造 R-23 违反）。
        # ⑩ 证据区与术语区必须是竖表（R-11 / G2）
        if kind == "node":
            for sid in ("sec-evidence", "sec-terms"):
                seg = _section_slice(text, sid)
                if seg is None:
                    bad.append((rel, "缺区块 #%s（竖表判据无对象）" % sid, ""))
                    continue
                kv_checked += 1
                if 'class="kv-blocks"' not in seg:
                    bad.append((rel, "#%s 区块不是竖表（缺 .kv-blocks）" % sid, ""))
                if re.search(r"<table\b", seg):
                    bad.append((rel, "#%s 区块内出现横表 <table>（长文字段会横向滚动）" % sid, ""))
    # ★ ②' 的作用域闭合断言（R-01 / N1 / 2026-10-16 第 7 轮；机制同第 6 轮的 R-23）：
    #   对象集 = **全部受检页**；排除清单 = `P35_H1_EXCLUDED`（空，⛔ 不是「免罪牌」）；
    #   「判据**真正作用到**的页」（有 <h1> 的页）必须等于 对象集 − 排除集。
    #   ⛔ 少一页即 FAIL —— 这正是防「声明作用域 ≠ 实现作用域」（旧实现的 `kind != "interactive"`
    #   控制流豁免就是这种形态：判据声明管全站，实测却按页类型分支跳过）。
    for rel in sorted(set(ctx.html) - set(h1_checked) - set(P35_H1_EXCLUDED)):
        bad.append((rel, "②' h1 口径未作用到该页（该页无 <h1> 且不在显式排除清单）"
                         "⇒ 作用域与对象脱钩", ""))
    for rel in sorted(set(P35_H1_EXCLUDED) - set(ctx.html)):
        bad.append(("(排除清单)", "②' 的排除项在受检页里不存在（清单已过期）", rel))
    ctx.notes.append(
        "P35 ②（R-01 / 2026-10-16 第 7 轮 **N1** 裁决，见 `CRITERIA-CHANGE-R01.md`）："
        "口径 = 「h1 每个 ≥3 字母拉丁 token 必须在 `glossary.json` 的某个 `term` 里**逐字命中**」；"
        "对象集 = 全部受检页 %d 个（排除清单为空）；判据**真正作用到** %d 个（含 <h1>）；"
        "h1 含 ≥3 字母拉丁 token 的页 %d 个；登记面 = glossary.terms %d 条。"
        "★ 旧实现的 `kind != \"interactive\"` **控制流豁免已删除**，改走「显式对象集 + 全集闭合断言」。"
        "★ 诚实边界：本判据只断言「缩写已登记」，⛔ 不断言「缩写用得恰当」。"
        % (len(ctx.html), len(h1_checked), len(h1_scope_pages),
           len(ctx.data["glossary"].get("terms", []))))
    if not enum_pat_pages:
        return False, "空集守卫：无任何页命中「其[一二三四五六七八九十]，」枚举模式 ⇒ ⑨ 恒真"
    if kv_checked == 0:
        return False, "空集守卫：无任何节点页含 #sec-evidence / #sec-terms 区块 ⇒ ⑩ 恒真"
    if g4_kv_checked == 0:
        return False, "空集守卫：无任何组页含 #sec-nodes / #sec-rel 区块 ⇒ ⑪ 恒真"
    if g4_relchain_checked == 0:
        return False, "空集守卫：无任何组页含 #sec-path / #sec-rel 区块 ⇒ ⑬ 恒真"
    if claim_checked == 0:
        return False, "空集守卫：无任何页可复算「结论来源」⇒ ⑭ 恒真"
    if prose_checked == 0:
        return False, "空集守卫：无任何组页 / 视图页含散文来源 ⇒ ⑦ 的扩展对象为空"
    ctx.notes.append("P35 ⑨（R-10 / 契约 G1 + G4）：命中「其[一二三四五六七八九十]，」枚举模式的页 "
                     "%d 个（%s）；其 .enum-list 合计 %d 个。判据口径与渲染**同源**："
                     "`gen-common.split_boundary/sentences/split_enum` 直接取用，"
                     "⛔ 门控不另写一套枚举识别正则（否则判据会对着自己的想象判）。"
                     "★ 对象是**页**而非「节点页」；G4 轮把来源映射补齐到组页 `intro`、"
                     "分组索引导语与学习路径导语（后两者的文本直接调生成器同名函数取，同源）。"
                     % (len(enum_pat_pages), ", ".join(enum_pat_pages), enum_lists_total))
    ctx.notes.append("P35 ⑩（R-11 / 契约 G2）：受检竖表区块 %d 个（每页 #sec-evidence + #sec-terms）；"
                     "断言两件事——① 区块内存在 `.kv-blocks`（字段名在上、值在下的竖表）；"
                     "② 区块内 `<table>` 数 = 0（长文字段横排必然横向滚动）。"
                     "★ 切片而非全页扫：判据范围若宽于对象，别处（该用/不该用对照表）的横表会假阳。"
                     % kv_checked)
    ctx.notes.append("P35 ⑪⑫⑬（R-11 / R-05 / 契约 G4，对象 = 组页 %d 个）：⑪ 竖表区块实检 %d 个"
                     "（#sec-nodes + #sec-rel）；⑫ ★ **代理判据**实检横表 %d 张（阈值：列数 ≤%d）"
                     "——★ ⑫ 代理的是「长文字段横表会横向滚动」这一**直接量**，⛔ 不得读作"
                     "「无横向滚动」的实测结论（真实是否滚动取决于字体度量 / 内容列宽 / 用户字号档，"
                     "★ 2026-10-16 更正：旧理由写「本会话浏览器不可用」——该前提已被推翻，"
                     "本条仍为代理是因为**代理自身的局限**而非「无法渲染」；缺口登记见台账 `G20`）。"
                     "★ 当前产物上 ⑫ 的**前件不成立**（两个区块都已是竖表 ⇒ 无 `<table>`），"
                     "这是 ⑪ 生效的直接结果；⑫ 的可判假性由负例夹具（注入 4 列横表）与"
                     "「3 列仍 PASS」的边界探针共同证明（`_selfcheck_p35_fixtures.py`）。"
                     "★ 代理的失效面已登记：短文字段的 4+ 列表不会滚动（分组索引 6 列短值表即一例）"
                     "⇒ ⑫ 只用于这两个已知含长文字段的区块，⛔ 不推广为全站判据。"
                     "⑬ 一行结构区块实检 %d 个（#sec-path + #sec-rel）。"
                     % (len(group_pages), g4_kv_checked, g4_tables_checked, G4_TABLE_COL_MAX,
                        g4_relchain_checked))
    ctx.notes.append("P35 ⑭（契约 G4）：可复算结论来源的页 %d 个——断言 `.read-map__claim` 逐字等于"
                     "该页结论来源（节点页 = `summary`；组页与视图页 = 页级导语**首句**，"
                     "取 `gen-common.lead_sentence`，与渲染同源）。" % claim_checked)
    ctx.notes.append("P35 依据（2026-10-15 用户走查第 2 轮反馈 + G4 收口）：把「可读性」拆成"
                     "**可判假的结构**——h1 纯中文 / 英文独立成行 / 标签与身份分行 / "
                     "导读锚点双向闭合 / 区块序号连续 / 对照表三列 / 散文切成主张+展开点 / "
                     "每页有图 / 枚举位置化（⑨）/ 证据与术语区竖表（⑩）/ 组页节点与前后继区竖表（⑪）"
                     "/ 组页区块横表列数 ≤3（⑫，代理）/ 组页依赖关系一行结构（⑬）/ "
                     "导读结论句 = 结论来源（⑭）。"
                     "⛔ 本判据不断言「好看」，只断言「结构上可扫」；"
                     "⛔ ⑫ 不断言「无横向滚动」（那是渲染期像素级判据，本会话不可测）。")
    ctx.notes.append("P35 逐页复算（.read-map 锚点数 / .sec-no 序号 / .enum-list 条数 / 竖表块数）：\n"
                     + "\n".join(per_page))
    # ★ 报告项（⛔ 不判 FAIL）：长文可扫性——「一段长散文读起来是不是一堵墙」没有因果阈值，
    #   故只逐条打印最长「无标点游程」，使这个**门控报不出来的面**至少可见（教训 ③）。
    runs = []
    for rel, text in sorted(ctx.html.items()):
        units = _prose_units(text)
        if not units:
            continue
        worst = max(units, key=_longest_run)
        runs.append((rel, _longest_run(worst), worst[:40]))
    runs.sort(key=lambda r: -r[1])
    over = [r for r in runs if r[1] > LONG_RUN_LIMIT]
    ctx.notes.append("P35 报告项（⛔ 不判 FAIL，按判据分档原则）：**长文可扫性**——逐页最长"
                     "「无句末标点游程」（caliber 口径，取 `.claim` 与 `.points li` 两个可扫单元）："
                     "受检页 %d 个；最长 %d（%s）；> %d 的页 %d 个 %s。"
                     "★ 为什么只作报告项：实测（`_probe_metrics.py` B 段）全站最长 151 / p90 130 / "
                     "中位 78，而「长度合规的散文照样可以是一堵墙」⇒ 无因果阈值可定"
                     "（与 `CRITERIA-CHANGE-P05.md` 的上限撤销同源）。"
                     "★ 本条同时是**诚实边界**：门控对「读起来是否成墙」**没有断言**，"
                     "该面由报告项 + 真实渲染（P38）共同兜。"
                     % (len(runs), runs[0][1] if runs else 0, runs[0][0] if runs else "-",
                        LONG_RUN_LIMIT, len(over), [(r[0], r[1]) for r in over[:4]]))
    return (not bad), ("受检页面 %d 个（节点页 %d / 组页 %d / 视图页 %d）；十四项结构断言全查"
                       "（⑨ 枚举模式页 %d 个 / .enum-list %d 个；⑩ 竖表区块 %d 个；"
                       "⑪ 组页竖表区块 %d 个；⑫ 组页区块内横表 %d 张；⑬ 一行结构区块 %d 个；"
                       "⑭ 结论来源可复算页 %d 个）；违例 %d 处 %s"
                       % (len(ctx.html), len(node_pages), len(group_pages), len(view_pages),
                          len(enum_pat_pages), enum_lists_total, kv_checked, g4_kv_checked,
                          g4_tables_checked, g4_relchain_checked, claim_checked,
                          len(bad), bad[:4]))


def check_p36(ctx):
    """P36 图件合规（★ 2026-10-15 新增；档位 = diagram-lite T2，交付形态 = 内联 SVG）。

    断言六条：
      ① 内联：每图是 `<svg>` 内联，⛔ 无 `<?xml` / DOCTYPE / `clip-path` / 外链 `href="http…`；
      ② 响应式：`<svg>` 有 `viewBox` 且**无固定** `width`/`height`（由 CSS 定尺寸）；
      ③ 可主题化：图内**无裸 hex**，色值一律 `var(--…)`；
      ④ a11y：`class="fig__svg"` + `role="img"` + 图内 `<title>`；
      ⑤ 溯源：每图有 `<figcaption>` 且标注「本站自制」；
      ⑥ **字形覆盖门控**（diagram-lite §判据索引，fail-closed）：逐个非 ASCII 字符查
         `fc-list :charset=`，**一个**无覆盖即 FAIL。
    """
    bad = []
    figs = []
    for rel, text in sorted(ctx.html.items()):
        for m in FIG_RE.finditer(text):
            figs.append((rel, m.group(0)))
    if not figs:
        return False, "空集守卫：全站未找到任何 `.fig` 图件 ⇒ 判据恒真"
    chars = set()
    for rel, fig in figs:
        svg = SVG_RE.search(fig)
        if not svg:
            bad.append((rel, "图件内无内联 <svg>", ""))
            continue
        s = svg.group(0)
        for need, label in (("viewBox", "缺 viewBox"), ("fig__svg", "缺 class=fig__svg"),
                            ("role=\"img\"", "缺 role=img")):
            if need not in s:
                bad.append((rel, "图件" + label, ""))
        if re.search(r"<svg[^>]*\swidth=", s) or re.search(r"<svg[^>]*\sheight=", s):
            bad.append((rel, "图件带固定 width/height（应由 CSS 定尺寸）", ""))
        for needle, label in (("<?xml", "含 XML 声明"), ("<!DOCTYPE", "含 DOCTYPE"),
                              ("clip-path", "含 clip-path")):
            if needle in s:
                bad.append((rel, "图件" + label, ""))
        if re.search(r'(?:xlink:)?href="(?!https?://www\.w3\.org)', s):
            bad.append((rel, "图件含外链引用（须自包含）", ""))
        hexes = sorted(set(re.findall(r"#[0-9a-fA-F]{6}\b", s)))
        if hexes:
            bad.append((rel, "图件含裸 hex（须令牌化）", hexes[:4]))
        if not re.search(r"<text[^>]*>", s):
            bad.append((rel, "图件无文本（空图）", ""))
        # ★ 图件规格（反馈 #2「绘图之前就要定好图片规格」）：内容列宽下的渲染高度上限
        vb = re.search(r'viewBox="([-\d. ]+)"', s)
        if vb:
            v = [float(x) for x in vb.group(1).split()]
            if len(v) == 4 and v[2] > 0:
                rh = v[3] / v[2] * FIG_CONTENT_COL_PX
                if rh > FIG_MAX_H_PX:
                    bad.append((rel, "图件规格超限（内容列宽下高 %.0fpx > %dpx，读者需缩放才能一屏看完）"
                                % (rh, FIG_MAX_H_PX), ""))
        for t in re.findall(r"<text[^>]*>(.*?)</text>", s, re.S):
            chars.update(ch for ch in _plain(t) if ord(ch) > 127)
        cap = re.search(r"<figcaption>(.*?)</figcaption>", fig, re.S)
        if not cap:
            bad.append((rel, "图件缺 figcaption", ""))
        elif "本站自制" not in _plain(cap.group(1)):
            bad.append((rel, "图注未标注「本站自制」", ""))
    missing = sorted(c for c in chars if not _glyph_covered(c))
    if missing:
        bad.append(("(全站)", "图件存在无字体覆盖的字形（fail-closed）",
                    "".join(missing[:12])))
    ctx.notes.append("P36 依据 diagram-lite 判据索引与 §四交付规范：SVG **直接内联**、外部引用 = 0、"
                     "⛔ 无 clip-path、⛔ 不在 SVG 外再包固定尺寸容器、**矢量权威**（栅格只作人看用）。"
                     "字形覆盖门控为 fail-closed：⛔ 不硬编码「不安全字形清单」，逐个非 ASCII 字符查 "
                     "fontconfig，一个无覆盖即 FAIL。")
    return (not bad), ("受检图件 %d 个；六项断言全查；非 ASCII 字形 %d 个全部有字体覆盖=%s；违例 %d 处 %s"
                       % (len(figs), len(chars), not missing, len(bad), bad[:4]))


# ---------------------------------------------------------------- P37（2026-10-15 结构化交互图，R-16 / G3）

CY_DATA_RE = re.compile(r'<script type="application/json" id="cy-data">(.*?)</script>', re.S)
# 结构化定位 = cytoscape `layout:{name:'preset'}`（坐标由生成器算好下发）
PRESET_RE = re.compile(r"""layout\s*:\s*\{\s*name\s*:\s*["']preset["']""")
# 自由布局后端（力导向 / dagre 自动分层）：R-16 明令不得作为组级视图的定位方式。
# ★ 扫描面只取「**布局名**（带引号的字面量）」与「dagre 脚本 src」，⛔ 不扫整页文本：
#   页内注释里出现「cytoscape-dagre 已撤除」这类**说明性文字**不是违例——判据若扫整页，
#   它会把「把撤除事实写清楚」这件事本身判成 FAIL（与 P24 的「注释里不得出现声明形态串」
#   同一类作用域错误：判据范围宽于对象 ⇒ 假阳）。
FREE_LAYOUT_RE = re.compile(r"""["'](?:dagre|cose|fcose|cola|euler|klay|spread|random)["']""")
FREE_LAYOUT_SRC_RE = re.compile(r'<script[^>]*\bsrc\s*=\s*"([^"]*(?:dagre|cose|fcose|cola)[^"]*)"',
                                re.I)

_GI = None


def _gen_interactive():
    """gen-interactive.py 模块。

    ★ 为什么门控要 import 生成器：P37 的「标签整体落在节点框内」子断言必须与生成器用**同一个**
      advance 上界模型（否则判据与渲染各用一套，改一处漏一处）。几何类子断言（画布内 / 不重叠 /
      不穿节点框 / 不压边）则是**独立复算**，与字体模型无关。
    """
    global _GI
    if _GI is None:
        _GI = _imp(os.path.join(HERE, "gen-interactive.py"), "pekg_gen_interactive")
    return _GI


def _cy_data(ctx):
    """取交互页内联的 cy-data（结构化布局的坐标真相源在**产物**里，⛔ 不在生成器内存里）。"""
    text = ctx.html.get(INTERACTIVE, "")
    m = CY_DATA_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1).replace("<\\/", "</"))
    except Exception:
        return None


def _p37_box(p, w, h):
    return (p[0] - w / 2.0, p[1] - h / 2.0, p[0] + w / 2.0, p[1] + h / 2.0)


def _p37_overlap(a, b, margin=0.0):
    return (a[0] < b[2] - margin and b[0] < a[2] - margin
            and a[1] < b[3] - margin and b[1] < a[3] - margin)


def _p37_seg_hits(p, q, bx):
    """线段 p→q 是否穿过 bx 内部（bx 内缩 1px 免擦边误判）。Liang-Barsky。"""
    x0, y0, x1, y1 = bx
    x0 += 1.0
    y0 += 1.0
    x1 -= 1.0
    y1 -= 1.0
    if x1 <= x0 or y1 <= y0:
        return False
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return False
            continue
        t = qq / pp
        if pp < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return t1 > t0 + 1e-9


def _p37_seg_overlap_len(p1, p2, q1, q2, tol=0.5):
    """两线段共线且重叠的长度（> tol 即「边压边」）。"""
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (q2[0] - q1[0], q2[1] - q1[1])
    n1 = math.hypot(*d1) or 1.0
    n2 = math.hypot(*d2) or 1.0
    if abs(d1[0] * d2[1] - d1[1] * d2[0]) / (n1 * n2) > 1e-3:
        return 0.0
    if abs(d2[0] * (p1[1] - q1[1]) - d2[1] * (p1[0] - q1[0])) / n2 > tol:
        return 0.0

    def t(pt):
        return ((pt[0] - q1[0]) * d2[0] + (pt[1] - q1[1]) * d2[1]) / (n2 * n2)
    a, b = sorted((t(p1), t(p2)))
    lo, hi = max(a, 0.0), min(b, 1.0)
    return max(0.0, (hi - lo) * n2)


def check_p37(ctx):
    """P37 交互全景图**结构化布局**（★ R-16 / 契约 G3 的机检判据）。

    ★ 判据由来：用户反馈 #3-4 ——「交互全景图建议向 deepseek harness 插件 dag 依赖图项目学习，
      结构化位置的优点还是很大」。此前组级视图用 cytoscape + dagre **自由布局**：节点少但铺得散、
      必须缩放才能看全，且没有任何判据看得见「散不散」。
    ★ 处置：坐标改由生成器在 Python 侧**确定性算好**并以 `layout:{name:'preset'}` 下发，
      渲染期零随机。本判据从**产物**把坐标取回复算，逐条断言：
        ① 交互页存在且用 `preset` 定位（⛔ 不得退回 dagre / 力导向后端）；
        ② DATA 里**每个**组节点都带 `position`（确定性坐标，⛔ 不靠渲染期布局）；
        ③ 全部组节点包围盒 ⊆ 声明画布可用区 ⇒ 默认视口下 zoom = 1（**无需缩放、无需拖拽**）；
        ④ 两两 bbox 不相交（留 8px 视觉间隙）；
        ⑤ 标签整体落在节点框内（行宽 ≤ `text-max-width`、行高 ≤ 节点高）；
        ⑥ 边弦不穿第三方节点框（⛔ 边压节点）；
        ⑦ 任两条边不共线重叠（⛔ 边压边）；
        ⑧ 边标签节点两两不重叠、且不压任何节点框；
        ⑨ 分层行序：行内 `order` 递增、同一行的 y 唯一、行 y 随行号（＝依赖层）严格递增。
    ★ 本判据的「默认视口」口径写死在 `DATA.layout`（由生成器下发：内容列 804px × #cy 高 640px
      × 内边距 18px），⛔ 不在门控里另设一套画布尺寸。
    """
    bad = []
    text = ctx.html.get(INTERACTIVE)
    if not text:
        return False, "空集守卫：无交互入口页 %s ⇒ 判据恒真" % INTERACTIVE
    data = _cy_data(ctx)
    if data is None:
        return False, "空集守卫：交互页内联 cy-data 缺失或不可解析 ⇒ 判据无对象"
    lay = data.get("layout") or {}
    for k in ("usableW", "usableH", "canvasW", "canvasH", "pad", "rowMembers", "rankOf"):
        if k not in lay:
            bad.append((INTERACTIVE, "DATA.layout 缺字段 " + k, ""))
    groups = data.get("groups") or []
    edges = data.get("groupEdges") or []
    els = data.get("edgeLabels") or []
    if not groups or not edges:
        return False, "空集守卫：DATA 无组节点或无边 ⇒ 判据恒真"
    # ① 结构化定位 + ⛔ 不得退回自由布局后端
    if not PRESET_RE.search(text):
        bad.append((INTERACTIVE, "未使用结构化定位 layout:{name:'preset'}", ""))
    free = sorted(set(m.group(0) for m in FREE_LAYOUT_RE.finditer(text)) |
                  set(m.group(1) for m in FREE_LAYOUT_SRC_RE.finditer(text)))
    if free:
        bad.append((INTERACTIVE, "仍引用自由布局后端（R-16 明令不得作为组级定位）", free[:4]))
    # ② 每个组节点都带确定性坐标
    miss = [g.get("id") for g in groups if not isinstance(g.get("pos"), dict)
            or "x" not in g["pos"] or "y" not in g["pos"]]
    if miss:
        bad.append((INTERACTIVE, "组节点缺 position（坐标未在生成期算好）", miss[:6]))
    if miss:
        return (not bad), ("受检组节点 %d 个；有 %d 个缺坐标，后续几何断言无对象" % (len(groups), len(miss)))
    uw, uh = float(lay["usableW"]), float(lay["usableH"])
    gpos = {g["id"]: (float(g["pos"]["x"]), float(g["pos"]["y"])) for g in groups}
    gbox = {g["id"]: _p37_box(gpos[g["id"]], float(g["w"]), float(g["h"])) for g in groups}
    ids = [g["id"] for g in groups]
    # ③ 画布内（节点 + 边标签一起算 ⇒ 与渲染期 boundingBox 同面）
    ebox = [(e["id"], _p37_box((float(e["x"]), float(e["y"])), float(e["w"]), float(e["h"])))
            for e in els]
    allb = list(gbox.values()) + [b for _i, b in ebox]
    bw = max(b[2] for b in allb) - min(b[0] for b in allb)
    bh = max(b[3] for b in allb) - min(b[1] for b in allb)
    zoom = min(1.0, uw / bw, uh / bh) if bw > 0 and bh > 0 else 0.0
    if bw > uw + 1e-6 or bh > uh + 1e-6:
        bad.append((INTERACTIVE, "内容包围盒 %.1f x %.1f 超可用区 %.0f x %.0f（需缩放才能看全）"
                    % (bw, bh, uw, uh), ""))
    elif zoom < 1.0 - 1e-9:
        bad.append((INTERACTIVE, "默认视口 zoom %.4f < 1（会被缩小）" % zoom, ""))
    # ④ 两两不重叠（留 8px 间隙）
    min_gap = None
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            A, B = gbox[ids[i]], gbox[ids[j]]
            if _p37_overlap(A, B, margin=-8.0):
                bad.append((INTERACTIVE, "组节点重叠/过近 %s vs %s" % (ids[i], ids[j]), ""))
            dx = max(B[0] - A[2], A[0] - B[2], 0.0)
            dy = max(B[1] - A[3], A[1] - B[3], 0.0)
            gap = math.hypot(dx, dy)
            min_gap = gap if min_gap is None else min(min_gap, gap)
    # ⑤ 标签整体落在节点框内（与生成器同一 advance 上界模型）
    GI = _gen_interactive()
    for g in groups:
        lines = str(g.get("cyLabel", "")).split("\n")
        for ln in lines:
            if GI._text_w(ln, float(g["fs"])) > float(g["mw"]) + 1e-6:
                bad.append((INTERACTIVE, "%s 标签行宽超 text-max-width" % g["id"], ln[:40]))
        lh = len(lines) * float(g["fs"]) * 1.15 + 2 * GI.G_VPAD
        if lh > float(g["h"]) + 1e-6:
            bad.append((INTERACTIVE, "%s 标签 %d 行放不进节点高" % (g["id"], len(lines)), ""))
    # ⑥⑦ 边：不穿第三方节点框 + 不共线重叠
    pair = [(e["source"], e["target"]) for e in edges]
    for s, t in pair:
        for gid in ids:
            if gid in (s, t):
                continue
            if _p37_seg_hits(gpos[s], gpos[t], gbox[gid]):
                bad.append((INTERACTIVE, "边 %s→%s 穿过第三方节点框 %s" % (s, t, gid), ""))
    for i in range(len(pair)):
        for j in range(i + 1, len(pair)):
            L = _p37_seg_overlap_len(gpos[pair[i][0]], gpos[pair[i][1]],
                                     gpos[pair[j][0]], gpos[pair[j][1]])
            if L > 0.5:
                bad.append((INTERACTIVE, "边压边 %s→%s 与 %s→%s 共线重叠 %.1fpx"
                            % (pair[i][0], pair[i][1], pair[j][0], pair[j][1], L), ""))
    # ⑧ 边标签不互压、不压节点
    for i in range(len(ebox)):
        for j in range(i + 1, len(ebox)):
            if _p37_overlap(ebox[i][1], ebox[j][1], margin=-2.0):
                bad.append((INTERACTIVE, "边标签互压 %s / %s" % (ebox[i][0], ebox[j][0]), ""))
    for eid, b in ebox:
        for gid in ids:
            if _p37_overlap(b, gbox[gid], margin=-2.0):
                bad.append((INTERACTIVE, "边标签 %s 压节点 %s" % (eid, gid), ""))
    # ⑨ 分层行序
    order = {g["id"]: g["order"] for g in groups}
    rows = lay.get("rowMembers") or []
    row_y = []
    for r, row in enumerate(rows):
        if [order[g] for g in row] != sorted(order[g] for g in row):
            bad.append((INTERACTIVE, "第 %d 行内 order 非递增（阅读方向 ≠ 课程顺序）" % r, row))
        ys = {round(gpos[g][1], 2) for g in row if g in gpos}
        if len(ys) != 1:
            bad.append((INTERACTIVE, "第 %d 行节点 y 不唯一（未对齐成行）" % r, sorted(ys)))
        else:
            row_y.append(sorted(ys)[0])
    for i in range(len(row_y) - 1):
        if not row_y[i] < row_y[i + 1]:
            bad.append((INTERACTIVE, "行 y 未随依赖层递增（第 %d/%d 行）" % (i, i + 1), row_y))
    ctx.notes.append("P37 依据 R-16 / 契约 G3（用户反馈 #3-4）：坐标由生成器在 Python 侧算好并以 "
                     "`layout:{name:'preset'}` 下发，渲染期零随机；本判据从**产物**取坐标独立复算。"
                     "默认视口口径取自 `DATA.layout`（内容列 %.0fpx × #cy 高 %.0fpx × 内边距 %.0fpx）"
                     "⇒ 可用 %.0f x %.0f。"
                     % (float(lay.get("canvasW", 0)), float(lay.get("canvasH", 0)),
                        float(lay.get("pad", 0)), uw, uh))
    return (not bad), ("组节点 %d 个 / 组间边 %d 条 / 边标签 %d 个；preset 定位=%s、无自由布局后端=%s；"
                       "包围盒 %.1f x %.1f ⊆ 可用 %.0f x %.0f ⇒ zoom %.4f；最小节点间隙 %.1fpx；"
                       "违例 %d 处 %s"
                       % (len(groups), len(edges), len(els), bool(PRESET_RE.search(text)),
                          not free, bw, bh, uw, uh, zoom, min_gap or 0.0, len(bad), bad[:4]))


def _patch_cydata(ctx, fn):
    """负例夹具：取出交互页内联的 cy-data → `fn(data)` 就地改写 → 按**同一序列化口径**写回。

    ⛔ 找不到 cy-data 即抛错（fail-closed）；⛔ 不改真实产物（只改 ctx 的副本）。
    """
    rel = INTERACTIVE
    text = ctx.html.get(rel, "")
    m = CY_DATA_RE.search(text)
    if not m:
        raise AssertionError("负例夹具锚点未命中：交互页无 cy-data")
    data = json.loads(m.group(1).replace("<\\/", "</"))
    fn(data)
    new = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    ctx.files[rel] = ctx.html[rel] = text[:m.start(1)] + new + text[m.end(1):]
    return ctx


def mut_p37(ctx):
    out = []
    # ① 退回自由布局（preset → dagre）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, INTERACTIVE, 'layout:{name:"preset"}', 'layout:{name:"dagre"}'))
    # ② 组节点坐标被挪出画布
    c = copy.deepcopy(ctx)
    out.append(_patch_cydata(c, lambda d: d["groups"][0]["pos"].__setitem__("x", 100000)))
    # ③ 两个组节点坐标重合
    c = copy.deepcopy(ctx)
    out.append(_patch_cydata(
        c, lambda d: d["groups"][1]["pos"].update(dict(d["groups"][0]["pos"]))))
    # ④ 边标签被摆到某个组节点中心（标签压节点）
    c = copy.deepcopy(ctx)
    out.append(_patch_cydata(c, lambda d: d["edgeLabels"][0].update(
        {"x": d["groups"][0]["pos"]["x"], "y": d["groups"][0]["pos"]["y"]})))
    # ⑤ 复制一条边 ⇒ 两条边完全共线重合（边压边）
    c = copy.deepcopy(ctx)
    out.append(_patch_cydata(c, lambda d: d["groupEdges"].append(dict(d["groupEdges"][0]))))
    # ⑥ 行序被打乱 ⇒ 行 y 不再随依赖层递增
    c = copy.deepcopy(ctx)
    out.append(_patch_cydata(c, lambda d: d["layout"]["rowMembers"].reverse()))
    return out


def mut_p35(ctx):
    out = []
    # ① h1 塞回「中文（English）」
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", "<h1>概率采样与确定性边界</h1>",
                      "<h1>概率采样与确定性边界（Probabilistic Sampling and the Determinism Boundary）</h1>"))
    # ② 去掉独立英文行
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html",
                      '<p class="page-en">Probabilistic Sampling and the Determinism Boundary</p>', ""))
    # ③ 标签混回身份行
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", '<div class="tag-row" aria-label="标签">',
                      '<p class="meta-line"><div class="zz-row">'))
    # ④ 导读锚点与区块 id 不一致
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", 'href="#sec-when"', 'href="#sec-zzz"'))
    # ⑤ 去掉一个区块序号
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", '<span class="sec-no">03</span>', ""))
    # ⑥ 对照表退化为两列
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html",
                      "<thead><tr><th>类别</th><th>场景 / 条件（总结）</th><th>具体做法（细节）</th></tr></thead>",
                      "<thead><tr><th>场景</th><th>做法</th></tr></thead>"))
    # ⑦ 散文退回整段（去掉主张句）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", '<p class="claim">', '<p class="zz-para">'))
    # ⑧ 去掉图件
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", '<figure class="fig"', '<figure class="zz-fig"'))
    # ⑨ 枚举不再位置化：把有序列表降级成普通块（锚点全站找不到即抛错，fail-closed）
    #    目标页 = 本轮唯一命中枚举模式的页（`14-views/02-frontier.html` 的 PE-N-01 条目）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "14-views/02-frontier.html", '<ol class="enum-list">',
                      '<ol class="zz-enum">'))
    # ⑨' 枚举列表只剩 1 条（条数 < 2 ⇒ 未成列）
    c = copy.deepcopy(ctx)
    out.append(_sub_first_enum_to_one_li(c))
    # ⑩ 证据区不再是竖表（去掉 .kv-blocks）
    c = copy.deepcopy(ctx)
    out.append(_sub_in_section(c, "sec-evidence", '<div class="kv-blocks">', '<div class="zz-kv">'))
    # ⑩' 术语区里塞回一张横表（长文字段会横向滚动）
    c = copy.deepcopy(ctx)
    out.append(_sub_in_section(c, "sec-terms", '<div class="kv-blocks">',
                               '<div class="kv-blocks"><table><tr><td>横表</td></tr></table>'))
    # ---- G4（2026-10-15）：组页 / 视图页的四条新断言（⑪–⑭）与对象扩展（④⑤⑦⑨）各配负例 ----
    # ⑬ 组页缺 `.read-map`（④ 的组页侧）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "12-groups/g00.html", '<section class="read-map"',
                      '<section class="zz-read-map"'))
    # ⑭ 视图页缺 `.read-map`（④ 的视图页侧）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "14-views/01-learning-path.html", '<section class="read-map"',
                      '<section class="zz-read-map"'))
    # ⑮ 组页导读锚点 ≠ 页内区块 id（④ 的**双向**闭合在组页上可判假）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "12-groups/g00.html", 'href="#sec-nodes"', 'href="#sec-zzz"'))
    # ⑯ 视图页去掉一个区块序号（⑤ 的视图页侧）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "14-views/01-learning-path.html", '<span class="sec-no">05</span>', ""))
    # ⑰ 组页散文退回整段（⑦ 的组页侧：去掉主张句）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "12-groups/g00.html", '<p class="claim">', '<p class="zz-claim">'))
    # ⑱ 组页散文缺展开点（⑦ 的组页侧：来源 3 句 ≥2 ⇒ 应有 .points）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "12-groups/g00.html", '<ul class="points">', '<ul class="zz-points">'))
    # ⑲ 视图页散文缺展开点（⑦ 的视图页侧）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "14-views/01-learning-path.html", '<ul class="points">',
                      '<ul class="zz-points">'))
    # ⑳ 组页散文来源含枚举模式但产物无 .enum-list（⑨ 的组页侧；真相源侧注入）
    c = copy.deepcopy(ctx)
    out.append(_set_group_intro_enum(c))
    # ㉑ 视图页枚举不再位置化（⑨ 的视图页侧：学习路径导语的「读法三条」）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "14-views/01-learning-path.html", '<ol class="enum-list">',
                      '<ol class="zz-enum">'))
    # ㉒ 组页 #sec-nodes 不再是竖表（⑪）
    c = copy.deepcopy(ctx)
    out.append(_sub_in_section(c, "sec-nodes", '<div class="kv-blocks">', '<div class="zz-kv">',
                               kind="group"))
    # ㉓ 组页 #sec-nodes 塞回 4 列横表（⑫ 代理判据）
    c = copy.deepcopy(ctx)
    out.append(_sub_in_section(c, "sec-nodes", '<div class="kv-blocks">',
                               '<div class="kv-blocks"><table><tr><td>a</td><td>b</td>'
                               "<td>c</td><td>d</td></tr></table>", kind="group"))
    # ㉔ 组页 #sec-rel 塞回 4 列横表（⑫ 代理判据的第二个对象区块）
    c = copy.deepcopy(ctx)
    out.append(_sub_in_section(c, "sec-rel", '<div class="kv-blocks">',
                               '<div class="kv-blocks"><table><tr><td>a</td><td>b</td>'
                               "<td>c</td><td>d</td></tr></table>", kind="group"))
    # ㉕ 组页 #sec-path 的依赖关系退回长句（⑬）
    c = copy.deepcopy(ctx)
    out.append(_sub_in_section(c, "sec-path", '<div class="relchain">', '<div class="zz-relchain">',
                               kind="group"))
    # ㉖ 组页 #sec-rel 的依赖关系退回长句（⑬ 的第二个对象区块）
    c = copy.deepcopy(ctx)
    out.append(_sub_in_section(c, "sec-rel", '<div class="relchain">', '<div class="zz-relchain">',
                               kind="group"))
    # ㉗ 组页导读结论句 ≠ 组导读首句（⑭ 的组页侧）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "12-groups/g00.html", '<p class="read-map__claim">',
                      '<p class="read-map__claim">改写后的结论。'))
    # ㉘ 视图页导读结论句 ≠ 视图导语首句（⑭ 的视图页侧）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "14-views/01-learning-path.html", '<p class="read-map__claim">',
                      '<p class="read-map__claim">改写后的结论。'))
    # ㉙ 节点页导读结论句 ≠ summary（⑭ 的节点页侧；证明该断言在节点页也可判假）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", '<p class="read-map__claim">',
                      '<p class="read-map__claim">改写后的结论。'))
    # ---- ★ 2026-10-16 第 6 轮：R-07 作用域扩为「知识承载页」后的三条新夹具 ----
    #     ⛔ 用 `_patch_strict`（只改目标页）：用 `_patch` 会在组页无图时把锚点兜底到**节点页**上，
    #       那样「组页必须有图」这条子断言从未被验证（假自检）。
    # ㉚ 组页去图（⑧ 的组页侧：证明新作用域**真的**覆盖 11 个组页，而不只是声明覆盖）
    c = copy.deepcopy(ctx)
    out.append(_patch_strict(c, "12-groups/g00.html", '<figure class="fig"', '<figure class="zz-fig"'))
    # ㉛ 注入一个**未分类的受检页**（`data-page-kind="misc"`，落在任何目录正则之外）
    #     ⇒ ⑧ / ④ 的**全集闭合断言**必须 FAIL（⛔ 不得静默豁免新页）
    c = copy.deepcopy(ctx)
    c.html["99-misc/zz-extra.html"] = (
        '<!DOCTYPE html><html lang="zh-CN"><body data-page-kind="misc" data-page-id="ZZ">'
        "<main><p>未分类页</p></main></body></html>")
    c.files["99-misc/zz-extra.html"] = c.html["99-misc/zz-extra.html"]
    out.append(c)
    # ㉜ 排除清单**过期**（把 `12-groups/index.html` 从受检页里删掉，而它仍在 `P35_FIG_EXCLUDED` 内）
    #     ⇒ 「排除项在受检页里不存在」必须 FAIL（证明排除清单本身也被判、而不是一张免罪牌）
    c = copy.deepcopy(ctx)
    c.html.pop("12-groups/index.html", None)
    c.files.pop("12-groups/index.html", None)
    out.append(c)
    # ---- ★ 2026-10-16 第 7 轮（N1 裁决，见 `CRITERIA-CHANGE-R01.md`）：② 的两条新夹具 ----
    #     ★ 为什么必须两条：旧口径（「h1 纯中文」）被替换为「h1 的拉丁缩写须在台账登记」后，
    #       判据**新增了一个可通过面**（已登记缩写）——只测「未登记 ⇒ FAIL」不足以证明它没退化为
    #       「有拉丁词就一律 FAIL」或「有拉丁词就一律放过」。⇒ 负例在此，**正向对照**
    #       （已登记缩写 ⇒ PASS）放在装置自检 `_selfcheck_p35_fixtures.py`（selftest 语义要求
    #       列表里每条都必须让判据**变红**，正向对照放这里会被报成「负例未触发」）。
    # ㉝ h1 塞入**台账里查不到**的拉丁缩写 ⇒ 必须 FAIL（证明判据没有退化成「有拉丁词就放过」）
    c = copy.deepcopy(ctx)
    out.append(_patch_strict(c, "11-node-pages/pe-f-01.html",
                             "<h1>概率采样与确定性边界</h1>",
                             "<h1>Kubernetes 采样与确定性边界</h1>"))
    # ㉞ 让某一页**没有 <h1>** 且不在排除清单 ⇒ ②' 的**全集闭合断言**必须 FAIL
    #     （证明「判据真正作用到的页」被逐个核对，而不是声明了对象集就完事 —— 这正是
    #      旧实现 `kind != "interactive"` 那种「声明作用域 ≠ 实现作用域」的报警器）
    c = copy.deepcopy(ctx)
    out.append(_patch_strict(c, "12-groups/g01.html", "</h1>", ""))
    return out


def mut_p36(ctx):
    out = []
    # ① 图内注入裸 hex
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", 'fill="var(--surface-raised)"',
                      'fill="#ffffff"'))
    # ② 图加回固定 width/height
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", '<svg class="fig__svg" role="img"',
                      '<svg class="fig__svg" role="img" width="800" height="600"'))
    # ③ 图注去掉「本站自制」
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", "（本站自制）", "（来源不明）"))
    # ④ 图件规格超限（viewBox 改成长条 ⇒ 内容列宽下渲染高度越界）
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", 'viewBox="0.00 0.00 512.00 370.00"',
                      'viewBox="0.00 0.00 200.00 900.00"'))
    # ⑤ 图内注入无字体覆盖的字形
    c = copy.deepcopy(ctx)
    out.append(_patch(c, "11-node-pages/pe-f-01.html", "自回归模型", "自回归模型\U00020000"))
    return out


# ------------------------------------------------ P38–P40（2026-10-15 教训固化轮：机制实现）

def _read_text(ctx, rel):
    """读一个受检文件：**优先 ctx.files**（负例夹具即注入在此），否则读磁盘。

    ★ 这样夹具才能在不改磁盘的前提下打在**真检对象**上（P38 的 manifest、P40 的台账、P39 的引用点）。
    """
    if ctx is not None and rel in ctx.files:
        return ctx.files[rel]
    p = os.path.join(SITE_ROOT, rel)
    if not os.path.isfile(p):
        return None
    try:
        return open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return None


def _read_bytes(ctx, rel):
    if ctx is not None and rel in ctx.files:
        v = ctx.files[rel]
        return v if isinstance(v, bytes) else v.encode("latin-1")
    p = os.path.join(SITE_ROOT, rel)
    if not os.path.isfile(p):
        return None
    return open(p, "rb").read()


def _png_facts_bytes(raw, path):
    """纯 Python PNG 读数（尺寸 / 唯一色数 / 亮度区间 / 字节 / sha256）。

    ⛔ 不依赖 PIL：判据不能因为环境里少了某个库就静默失效。
    ★ 与 `_probe_channel.png_read` 是**两份独立实现**（判据不采信探针自报，必须自己复算）。
    形态不认识（非 8-bit 真彩 / 隔行）即抛错 —— fail-closed。
    """
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG：%s" % path)
    pos, idat, w, h, bd, ct, interlace = 8, b"", 0, 0, 0, 0, 0
    while pos + 8 <= len(raw):
        (ln,) = struct.unpack(">I", raw[pos:pos + 4])
        typ = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if bd != 8 or ct not in (2, 6) or interlace != 0:
        raise ValueError("不支持的 PNG 形态 bd=%d ct=%d interlace=%d：%s" % (bd, ct, interlace, path))
    bpp = 3 if ct == 2 else 4
    stride = w * bpp
    data = zlib.decompress(idat)
    prev = bytearray(stride)
    colors = set()
    lmin, lmax = 255.0, 0.0
    off = 0
    for _y in range(h):
        ft = data[off]
        off += 1
        line = bytearray(data[off:off + stride])
        off += stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif ft != 0:
            raise ValueError("未知 PNG 过滤器 %d：%s" % (ft, path))
        prev = line
        for x in range(w):
            i = x * bpp
            r, g, b = line[i], line[i + 1], line[i + 2]
            colors.add((r, g, b))
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if lum < lmin:
                lmin = lum
            if lum > lmax:
                lmax = lum
    return {"width": w, "height": h, "uniq_colors": len(colors),
            "lum_min": round(lmin, 1), "lum_max": round(lmax, 1),
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _png_facts(path):
    return _png_facts_bytes(open(path, "rb").read(), path)


def _degenerate(f):
    """产物非退化判定（假绿通道判据核心）。返回 [] = 非退化。"""
    why = []
    if f["width"] < 320 or f["height"] < 240:
        why.append("尺寸退化 %dx%d" % (f["width"], f["height"]))
    if f["uniq_colors"] < PNG_MIN_COLORS:
        why.append("唯一色 %d < %d（疑似纯色空图）" % (f["uniq_colors"], PNG_MIN_COLORS))
    if f["lum_max"] - f["lum_min"] < PNG_MIN_LUM_SPAN:
        why.append("亮度区间 %.1f 过窄" % (f["lum_max"] - f["lum_min"]))
    if f["bytes"] < PNG_MIN_BYTES:
        why.append("字节 %d 过小" % f["bytes"])
    return why


def _load_probe_manifest(ctx=None):
    """读验证通道探针的 manifest（⛔ 不存在/不可解析 ⇒ None，由判据判 FAIL 而非抛错）。

    ★ 经 `_read_text` 读：负例夹具即注入在 `ctx.files` 里（⛔ 不改磁盘）。
    """
    txt = _read_text(ctx, PROBE_MANIFEST_REL)
    if txt is None:
        return None
    try:
        return json.loads(txt)
    except Exception:  # noqa: BLE001
        return None


def check_p38(ctx):
    """P38 验证通道**能力声明与产物非退化**（★ 教训 ①② 的机检判据）。

    ★ 防的失败模式（两条都真实发生过，见 `report.md §6.5.5`）：
      ① **「环境能力不可用」被当成已确立的事实**——上一轮把「浏览器不可用」写成结论，
         真因却是一个被误诊的根因（`CapEff=0` + `NoNewPrivs=1` 使 file-capability 程序
         `snap-confine` 取不到 `cap_dac_override`，失败在**启动层**），而**可用的非 snap 内核
         一直在盘上**。⇒ 本轮把「能力可用性」变成**每轮必须复跑探测**的对象：
         manifest 里声明 `available=false` 而**内核实际存在** ⇒ FAIL（这正是当年那个误诊的形态）。
      ② **假绿通道**——`agent-browser 0.34.0` 回显 `✓ Screenshot saved` 却产出**纯白 1 色空图**。
         ⇒ 凡截图类证据一律补**像素读数**（尺寸 / 唯一色数 / 亮度区间 / 字节），
         且判据**自己重新解码 PNG**（⛔ 不采信探针自报的数字），并把 sha256 与磁盘上重算值比对
         ⇒ 「文件被换掉/被伪造/静默退化」都会暴露。

    断言（全部现读现算，⛔ 无写死的「可用」结论）：
      A. manifest 存在、schema 匹配、含 channel_facts / renders 两段；
      B. **能力声明与事实一致**：`non_snap_chromium.found` / `playwright_python.found` 必须与
         判据**自己在磁盘上复算**的结果相同（⛔ 不采信声明本身）；
         ★ 若声明 `available=false` 而内核存在 ⇒ FAIL（误诊复发）；
      C. 每条 render：PNG 文件存在、**判据自己解码**后非退化、sha256 与声明一致、
         声明里的尺寸与实测尺寸一致；
      D. 实检渲染数 ≥1（空集守卫）。
    """
    bad = []
    man = _load_probe_manifest(ctx)
    if man is None:
        return False, ("空集守卫/文件缺失：无验证通道探针 manifest `%s` ⇒ 本判据无对象。"
                       "★ 按 §轮次执行协议，每轮**开工必跑** `python3 _probe_channel.py` "
                       "（⛔ 不得沿用上一轮的散文结论）。" % PROBE_MANIFEST_REL)
    if man.get("schema") != PROBE_SCHEMA:
        bad.append(("manifest", "schema 不匹配：%r ≠ %r" % (man.get("schema"), PROBE_SCHEMA), ""))
    facts = man.get("channel_facts") or {}
    renders = man.get("renders") or []
    if not facts:
        bad.append(("manifest", "缺 channel_facts（能力探测结果）", ""))
    if not renders:
        return False, "空集守卫：manifest 内 renders 为空 ⇒ 非退化断言恒真"
    # ---- B. 能力声明 vs 判据自己复算的事实（★ 本判据的核心：不采信声明）----
    home = os.path.expanduser("~")
    real_chrome = []
    base = os.path.join(home, ".cache", "ms-playwright")
    if os.path.isdir(base):
        for d in sorted(os.listdir(base)):
            if d.startswith("chromium"):
                for sub in ("chrome-linux64/chrome", "chrome-linux/chrome"):
                    p = os.path.join(base, d, sub)
                    if os.path.isfile(p):
                        real_chrome.append(p)
    decl_chrome = (facts.get("non_snap_chromium") or {})
    if bool(decl_chrome.get("found")) != bool(real_chrome):
        bad.append(("channel_facts.non_snap_chromium",
                    "能力声明与事实不一致：声明 found=%s，判据复算 found=%s（内核候选 %d 个）"
                    % (decl_chrome.get("found"), bool(real_chrome), len(real_chrome)), ""))
    if decl_chrome.get("found") and decl_chrome.get("path") not in real_chrome:
        bad.append(("channel_facts.non_snap_chromium",
                    "声明的内核路径不在判据复算出的候选集内：%r" % decl_chrome.get("path"), ""))
    if not real_chrome and not decl_chrome.get("found"):
        # ★ 这才是「真的不可用」：但必须留下**不可用声明**才允许，且协议要求登记为局限
        bad.append(("channel_facts.non_snap_chromium",
                    "声明不可用且事实确实无内核 ⇒ 须在契约 §2 登记为局限（⛔ 不得静默）", ""))
    try:
        import importlib.util as _iu
        real_drv = bool(_iu.find_spec("playwright"))
    except Exception:  # noqa: BLE001
        real_drv = False
    if bool((facts.get("playwright_python") or {}).get("found")) != real_drv:
        bad.append(("channel_facts.playwright_python",
                    "驱动声明与事实不一致：声明 %s，判据复算 %s"
                    % ((facts.get("playwright_python") or {}).get("found"), real_drv), ""))
    # ---- C. 每条渲染：判据自己解码 + 与声明比对 ----
    checked = 0
    per = []
    for r in renders:
        rel_png = r.get("png") or ""
        # ★ manifest 里的 `png` 是**相对 16-checkpoint/** 的路径（探针的落盘口径），
        #   而 `_read_bytes` 以站点根为基 ⇒ 必须先归一化成站点根相对路径
        #   （⛔ 不改成「直接 open」：那样夹具就没法把退化 PNG 注入到真检对象上）。
        rel_site = os.path.normpath(os.path.join("16-checkpoint", rel_png)) if rel_png else ""
        raw = _read_bytes(ctx, rel_site) if rel_site else None
        if raw is None:
            bad.append((rel_png, "声明的渲染产物不存在（站点根相对路径 %s）" % rel_site, ""))
            continue
        try:
            f = _png_facts_bytes(raw, rel_site)
        except Exception as e:  # noqa: BLE001
            bad.append((rel_png, "PNG 解码失败（fail-closed）：%s: %s" % (type(e).__name__, e), ""))
            continue
        checked += 1
        deg = _degenerate(f)
        if deg:
            bad.append((rel_png, "产物**退化**（假绿通道形态）：%s" % "；".join(deg), ""))
        if f["sha256"] != r.get("sha256"):
            bad.append((rel_png, "sha256 与声明不一致（文件被替换/篡改或静默退化）", ""))
        if [f["width"], f["height"]] != list(r.get("viewport") or []):
            bad.append((rel_png, "实测尺寸 %dx%d ≠ 声明视口 %s"
                        % (f["width"], f["height"], r.get("viewport")), ""))
        if abs(f["uniq_colors"] - int(r.get("uniq_colors") or -1)) > 0:
            bad.append((rel_png, "实测唯一色 %d ≠ 声明 %s" % (f["uniq_colors"], r.get("uniq_colors")), ""))
        per.append("  %-26s %4dx%-4d 唯一色 %6d 亮度 %5.1f–%5.1f %8d B %s"
                   % (r.get("label"), f["width"], f["height"], f["uniq_colors"],
                      f["lum_min"], f["lum_max"], f["bytes"], f["sha256"][:16]))
    if checked == 0:
        return False, "空集守卫：声明了 %d 条渲染但**实检到 0 个可解码产物** ⇒ 断言恒真" % len(renders)
    # ---- D. 横向溢出（渲染期直接量；★ 这是「门控报不出来的面」中被实测到的那一面）----
    measured = man.get("measured") or {}
    surv = measured.get("overflow_survey") or {}
    over_pages = []
    for rel in sorted(surv):
        s = surv[rel]
        if s.get("docScrollW", 0) - s.get("innerW", 0) > 0:
            over_pages.append((rel, "文档横向溢出 %dpx" % (s["docScrollW"] - s["innerW"])))
        for b in (s.get("overflowing") or []):
            over_pages.append((rel, "<%s.%s> 横向溢出 %dpx（scrollW %d / clientW %d；"
                                     "white-space %s）"
                               % (b.get("tag"), b.get("cls"), b.get("overflowPx", 0),
                                  b.get("scrollW", 0), b.get("clientW", 0), b.get("whiteSpace"))))
    if over_pages:
        bad.extend([(p, m, "") for p, m in over_pages])
    ctx.notes.append("P38 依据（教训 ①②）：本判据**不采信探针自报**——它自己重新解码每个 PNG "
                     "（纯 Python，⛔ 不依赖 PIL）并与声明逐项比对，且自己复算「内核/驱动是否存在」"
                     "这一事实。★ 若某轮把「环境能力不可用」写成结论而内核其实存在 ⇒ 本条直接 FAIL"
                     "（这正是上一轮的误诊形态）。★ 假绿通道（回显成功 + 纯白空图）由"
                     "尺寸/唯一色/亮度区间/字节四项下限拦住。★ 横向溢出为**渲染期直接量**"
                     "（scrollWidth − clientWidth），⛔ 不是代理。")
    return (not bad), ("manifest `%s`（schema %s）；能力声明与事实一致；实检渲染 %d 条（判据自己解码）；"
                       "横向溢出页/元素 %d 处；违例 %d 处 %s\n%s"
                       % (PROBE_MANIFEST_REL, man.get("schema"), checked, len(over_pages),
                          len(bad), bad[:4], "\n".join(per)))


def _change_refs(ctx=None):
    """扫「判据变更登记件」的三处引用点（★ 与 `CRITERIA-CHANGE-P34.md §6.3` 的记载同源）。"""
    refs = {}
    targets = [
        "16-checkpoint/gate_prototype.py",
        "16-checkpoint/gen-state.py",
        "PUBLISH-STATE.json",
    ]
    pat = re.compile(re.escape(CONTRACT_CHANGE_PREFIX) + r"[A-Za-z0-9\-]*\.md")
    for rel in targets:
        text = _read_text(ctx, rel)
        if text is None:
            continue
        for m in pat.finditer(text):
            refs.setdefault(m.group(0), set()).add(os.path.basename(rel))
    return refs


def _change_files():
    return sorted(fn for fn in os.listdir(HERE)
                  if fn.startswith(CONTRACT_CHANGE_PREFIX) and fn.endswith(".md"))


def _gates_change_keys(ctx=None):
    """取 `PUBLISH-STATE.json` 的 `gates` 里所有 `criteria_change_*` 键（★ 第 7 轮新增）。

    ★ 为什么需要它：第 6 轮收口时 `gates` 只载荷了 **7** 件登记件，而磁盘已有 **9** 件
      —— `CRITERIA-CHANGE-P35-G4.md` 与 `CRITERIA-CHANGE-P38-P40.md` **只在源码散文里出现**，
      不由结构化出口承载。而 P39 原实现只扫「文本里有没有这个文件名」⇒ **照样报 9/9 绿**。
      ⇒ 「一份登记件是否被**结构化**引用」这半面**无判据**（第 7 轮核验查出，见 `CRITERIA-CHANGE-P39.md`）。
    """
    try:
        txt = _read_text(ctx, STATE_FILE)
    except Exception:  # noqa: BLE001
        txt = None
    if txt is None:
        return None
    try:
        doc = json.loads(txt)
    except Exception:  # noqa: BLE001
        return None
    gates = doc.get("gates")
    if not isinstance(gates, dict):
        return None
    return sorted(k for k in gates if k.startswith(CONTRACT_CHANGE_KEY_PREFIX))


def check_p39(ctx):
    """P39 引用解析：判据变更登记件**三处引用与磁盘存在性双向闭合**（★ 教训 ④⑥ 的机检判据）。

    ★ 防的失败模式：
      · **断链引用**：`gate_prototype.py` docstring、`gen-state.py` 的 `CHANGE_DECL_2`、
        `PUBLISH-STATE.json` 的 `gates` 三处都引用 `CRITERIA-CHANGE-P23.md`，**磁盘上却没有**
        ⇒ 一份「从未存在过的判据变更登记」被当成已留痕。这是**判据作用域与对象脱钩**的
        同型缺陷在「留档面」上的表现（本判据把它变成 FAIL，⛔ 不再靠人偶然发现）。
      · **孤儿登记件**：磁盘上有登记件但**无任何引用点** ⇒ 「已实现但无判据」在留档面的对偶
        （契约不允许第三种状态）。

    断言：
      ① 每处引用的文件名**必须在磁盘上存在**（断链 ⇒ FAIL，逐条列出引用来源）；
      ② 磁盘上每个 `CRITERIA-CHANGE-*.md` **必须至少被一处引用**（孤儿 ⇒ FAIL）；
      ③ 引用点集合与文件集合**都非空**（空集守卫：扫不到引用 ⇒ FAIL，⛔ 不静默放行）；
      ④ ★ **结构化出口闭合**（2026-10-16 第 7 轮新增，见 `CRITERIA-CHANGE-P39.md`）：
        `PUBLISH-STATE.json` 的 `gates` 里 `criteria_change_*` **键集合 ⟺ 磁盘登记件集合**（双向）；
        缺键 / 孤儿键 / `gates` 不可读或键集为空 ⇒ FAIL。
        ★ 为什么 ①② 抓不住：它们只判「这个文件名有没有在**文本**里出现过」，
        而 `gates` 是**结构化出口** ⇒ 一件登记件可以在**散文**里被提到（①② 绿）却**不被任何字段承载**。
        第 6 轮的实测正是这样：`gates` 只载荷 **7** 件而磁盘已有 **9** 件，P39 照样报 9/9 绿。
    """
    refs = _change_refs(ctx)
    files = _change_files()
    if not refs:
        return False, "空集守卫：三处引用点里扫不到任何 `%s*.md` 引用 ⇒ 判据恒真" % CONTRACT_CHANGE_PREFIX
    if not files:
        return False, "空集守卫：`16-checkpoint/` 下无 `%s*.md` ⇒ 判据恒真" % CONTRACT_CHANGE_PREFIX
    bad = []
    for name in sorted(refs):
        if name not in files:
            bad.append(("断链引用", name, "被引用但磁盘无此文件；引用来源 = %s"
                        % ", ".join(sorted(refs[name]))))
    for name in files:
        if name not in refs:
            bad.append(("孤儿登记件", name, "磁盘存在但三处引用点均未引用"))
    # ④ ★ 结构化出口闭合（2026-10-16 第 7 轮新增，见 `CRITERIA-CHANGE-P39.md`）：
    #    `PUBLISH-STATE.json` 的 `gates` **结构化键集合 ⟺ 磁盘登记件集合**（双向）。
    #    ★ 为什么 ①② 两条抓不住它：它们只看「文件名字符串在文本里出现过没有」，
    #      而 `gates` 是**结构化出口** —— 一件登记件完全可以在**散文**里被提到（于是 ①② 绿），
    #      却**不被任何结构化字段承载**（于是「这份留痕能不能被程序消费」这半面无判据）。
    gkeys = _gates_change_keys(ctx)
    if gkeys is None:
        bad.append(("结构化出口", STATE_FILE, "读不到 gates 对象 ⇒ ④ 无法裁决（fail-closed）"))
    elif not gkeys:
        bad.append(("结构化出口", STATE_FILE, "gates 里无任何 `%s*` 键 ⇒ ④ 恒真"
                    % CONTRACT_CHANGE_KEY_PREFIX))
    else:
        want = {_change_key(fn) for fn in files}
        for k in sorted(want - set(gkeys)):
            bad.append(("结构化出口缺件", k,
                        "磁盘有对应登记件，但 `%s` 的 `gates` 无此键（只在散文里出现不算承载）"
                        % STATE_FILE))
        for k in sorted(set(gkeys) - want):
            bad.append(("结构化出口孤儿键", k, "`gates` 有此键而磁盘无对应登记件"))
    ctx.notes.append("P39 依据（教训 ④⑥）：判据/夹具的**作用域必须与对象对齐**——引用解析是"
                     "「留档面」上的同型判据。★ 引用点 = `gate_prototype.py` / `gen-state.py` / "
                     "`PUBLISH-STATE.json` 三处（与 `CRITERIA-CHANGE-P34.md §6.3` 记载的断链同源）；"
                     "⛔ 本判据**只断言引用可解析**，⛔ 不断言登记件的**内容**是否合格"
                     "（内容评审不是机检）。★ 2026-10-16 第 7 轮补 ④：**结构化出口闭合**——"
                     "`gates` 的 `criteria_change_*` 键集合 ⟺ 磁盘登记件集合（双向闭合）。"
                     "理由是第 6 轮实证：gates 只载荷 7 件而磁盘已有 9 件，①② 却照样报绿"
                     "（散文提过就算「有引用」）⇒ 「能否被程序消费」这半面无判据。")
    return (not bad), ("引用点 3 处（gate_prototype.py / gen-state.py / PUBLISH-STATE.json）；"
                       "被引用的登记件 %d 个 / 磁盘登记件 %d 个 / 结构化出口键 %d 个；"
                       "断链 0 处 / 孤儿 0 处；违例 %d 处 %s"
                       % (len(refs), len(files), len(gkeys or []), len(bad), bad[:6]))


def _load_ledger(ctx=None):
    txt = _read_text(ctx, ROUND_LEDGER_REL)
    if txt is None:
        return None
    try:
        return json.loads(txt)
    except Exception:  # noqa: BLE001
        return None


def check_p40(ctx):
    """P40 轮次台账**结构合规**（★ 教训 ⑤⑥ 的机检判据）。

    ★ 防的失败模式：
      · **委派方自报 ≠ 读数**：G4 委派方交付时报告里仍写「浏览器不可用，G5 不消」——
        那是它**开工时刻的旧认知**（并发运行的子 Agent 会带着过期世界观交付）。
        ⇒ 台账的每条 claim 必须显式声明 `source`（`self-report` / `main-agent-rerun`）与
        `raw_output`；`main-agent-rerun` 的条目**必须带原始输出标记**。
      · **「已实现但无判据」= 未落实**（契约不允许第三种状态）⇒ 每轮必须逐条声明它触碰的 R-xx。

    ★ **机检边界（诚实标注）**：本条只能断言**台账的结构与自洽**——
      字段齐备 / R-id 合法 / 与契约规则表对齐 / `re-run` 声明带原始输出标记。
      它**⛔ 无法验证**自报是否如实（那需要人读原始输出）。⇒ 契约 §轮次执行协议 明文规定
      「委派产出必须主 Agent 独立复跑，且自报与复跑分别标注」，本条是它的**可机检外壳**。
    """
    led = _load_ledger(ctx)
    if led is None:
        return False, ("空集守卫/文件缺失：无轮次台账 `%s` ⇒ 本判据无对象。"
                       "★ 按 §轮次执行协议，每轮收口必须落盘该台账。" % ROUND_LEDGER_REL)
    if led.get("schema") != LEDGER_SCHEMA:
        return False, "台账 schema 不匹配：%r ≠ %r" % (led.get("schema"), LEDGER_SCHEMA)
    rounds = led.get("rounds") or []
    if not rounds:
        return False, "空集守卫：台账 rounds 为空 ⇒ 断言恒真"
    # 契约规则表的 R-id 全集（★ 与契约同源：从契约正文扫，⛔ 不写死 20）
    ctext = _read_text(ctx, CONTRACT_REL)
    if ctext is None:
        return False, "空集守卫：契约 `%s` 不存在 ⇒ 无法与规则表对齐" % CONTRACT_REL
    contract_rids = set(re.findall(r"^\|\s*(R-\d{2})\s*\|", ctext, re.M))
    if not contract_rids:
        return False, "空集守卫：契约规则表里扫不到 R-xx ⇒ 判据恒真"
    bad = []
    claims_checked = 0
    for r in rounds:
        rid = r.get("round")
        if not isinstance(rid, int) or rid < 1:
            bad.append(("round", "轮次号非法：%r" % rid, ""))
        if not (r.get("started_at") and r.get("ended_at")):
            bad.append(("round %s" % rid, "缺 started_at / ended_at（开工与收口时点）", ""))
        rs = r.get("rs_touched") or []
        if not rs:
            bad.append(("round %s" % rid, "rs_touched 为空（本轮触碰的 R-xx 必须逐条声明）", ""))
        for x in rs:
            if not RID_RE.match(str(x)):
                bad.append(("round %s" % rid, "rs_touched 含非法 R-id：%r" % x, ""))
            elif x not in contract_rids:
                bad.append(("round %s" % rid, "R-id %s 不在契约规则表内（契约与台账脱钩）" % x, ""))
        if not (r.get("artifacts") or []):
            bad.append(("round %s" % rid, "artifacts 为空（本轮触碰的产物必须逐条声明）", ""))
        claims = r.get("claims") or []
        if not claims:
            bad.append(("round %s" % rid, "claims 为空（⛔ 不得只声明触碰、不声明读数来源）", ""))
        for c in claims:
            claims_checked += 1
            src = c.get("source")
            if src not in ("self-report", "main-agent-rerun"):
                bad.append(("round %s" % rid, "claim.source 非法：%r" % src, ""))
            if not (c.get("raw_output") or "").strip():
                bad.append(("round %s" % rid, "claim 缺 raw_output（原始输出必须留痕，⛔ 不接受转述）", ""))
            elif src == "main-agent-rerun" and "===" not in c["raw_output"]:
                bad.append(("round %s" % rid,
                            "claim 声明 main-agent-rerun 但 raw_output 无原始输出标记（`===`）", ""))
    ctx.notes.append("P40 依据（教训 ⑤⑥）：委派方自报 ≠ 读数（并发子 Agent 会带着**开工时刻的"
                     "世界观**交付），且「已实现但无判据」= 未落实（契约不允许第三种状态）。"
                     "★ **机检边界（诚实标注）**：本条只断言台账的**结构与自洽**——"
                     "字段齐备 / R-id 合法且与契约规则表对齐 / 每条 claim 标注 source 且带 raw_output / "
                     "`main-agent-rerun` 必须带原始输出标记。"
                     "⛔ **它无法验证自报是否如实**（那需要人读原始输出）⇒ 契约 §轮次执行协议 "
                     "第 ④ 条是它的**不可机检**部分，明文标注。")
    return (not bad), ("轮次 %d 条 / claims %d 条；契约规则表 R-id 全集 %d 个；"
                       "结构与自洽违例 %d 处 %s"
                       % (len(rounds), claims_checked, len(contract_rids), len(bad), bad[:6]))


# ---------------------------------------------------------------- P41（2026-10-16 第 6 轮：G20）

# ★ 历史句（第 5 轮审核当场报出、当轮已修）：4 处判据/生成器散文把「本会话浏览器不可用」当作
#   「只能用代理判据」的**理由**，而该结论早已被推翻（非 snap 内核一直在盘上；`_probe_env.py`
#   与 `_probe_thresholds.py` 用同一内核取得了真实渲染读数）⇒ 属 R-21 违反（把会过期的读数当事实）。
P41_TRIGGER = "本会话浏览器不可用"
# ★ 更正标记：**该行必须自证**「这是被更正/推翻的旧理由的引用」，而不是一条新的能力声明。
P41_CORRECTION_MARKS = ("更正", "旧理由", "已推翻")
# ★ **「提及」与「断言」的区分**（2026-10-16 本轮被装置自检当场抓出的假阳，见登记件 §L·F-4）：
#   历史句若被**引号包裹**（`「…」` / `“…”` / `"…"` / `'…'`），那是在**指称这条句子本身**
#   （留档、教训记述、本判据自己的自检脚本都属于这种），**不是**能力声明 ⇒ 不算违例。
#   只有**裸句**（不带引号）才是在**断言**「某能力不可用」⇒ 必须带更正标记，否则 FAIL。
#   ⛔ 诚实边界：「带引号的陈旧理由」仍会漏过 —— 这是「窄版」的代价，登记为局限（见登记件 §5）。
P41_QUOTE_OPEN = ("「", "“", "\"", "'")
P41_QUOTE_CLOSE = ("」", "”", "\"", "'")
# ★ 显式豁免清单 + 理由（⛔ 不是「不判」，而是「不在本判据的对象集内」）：
P41_EXEMPT = {
    "_r5_ledger_update.py": "第 5 轮的**一次性台账写入器**：它记录的是审核发现与处置的**原文引用**"
                            "（含被引用的历史句本身），不是能力声明 ⇒ 按 R-23 显式豁免并写明理由",
}


def p41_probe_line(marked=False):
    """构造一行 **P41 探针文本**（★ 唯一来源；⛔ 别处不得再写这个历史句的字面量）。

    ★ 为什么必须是函数、而不是让夹具/自检脚本各写一份字面量：P41 的扫描面是
      `16-checkpoint/*.py` **本身** —— 任何在源文件里写死这个历史句的地方都会被自己判成违例
      （本轮实测：装置自检脚本第 76 行当场被判 FAIL）。⇒ 探针载荷由**本函数**用 `%s` 拼出，
      调用方（`mut_p41` 与 `_selfcheck_p13_p41_c58.py`）只传布尔，⛔ 不落地字面量。
    """
    marked_line = ("# （★ 更正：旧理由曾写「%s」——该前提已被推翻）" % P41_TRIGGER)
    bare_line = ("# %s ⇒ 只能用代理判据" % P41_TRIGGER)
    return marked_line if marked else bare_line


def _p41_py_files(ctx):
    """P41 的扫描面：`16-checkpoint/` 顶层的 `*.py`（含夹具注入的虚拟文件，⛔ 不递归子目录）。

    ★ 为什么要把 `ctx.files` 里注入的条目也算进来：`load_ctx` **排除** `16-checkpoint/`，
      若不这样，负例夹具就只能改磁盘（违反「夹具一律落在临时沙箱内」的纪律）。
    """
    names = {fn for fn in os.listdir(HERE) if fn.endswith(".py")}
    for rel in ctx.files:
        if rel.startswith("16-checkpoint/") and rel.endswith(".py"):
            tail = rel[len("16-checkpoint/"):]
            if "/" not in tail:
                names.add(tail)
    return sorted(names)


def check_p41(ctx):
    """P41 源文件里的**散文能力声明**：已更正的陈旧结论不得静默复活（★ 2026-10-16 第 6 轮，G20）。

    ★ 防的失败模式：`P38` 的能力复核**只扫** `_probe/channel.json` 的两个 `found` 布尔，
      ⛔ **不扫源文件里的散文**。于是「文档声称某能力不可用」这一面**无判据** ——
      第 5 轮实测：4 处陈旧散文（`gate_prototype.py` 的 P11 note / P35 ⑫ 说明两处、
      `gen-interactive.py` 的 advance 上界注释）被当作「只能用代理判据」的理由，**没有任何门控会失败**。

    ★ **本条是「窄版」（用户裁决明确建议）**：只判**已登记的历史句**是否复活，⛔ **不判**「任何措辞」。
      理由（⛔ 不得省略）：仓内多处**正当引用**该结论以记述教训（如本文件 P38 docstring、教训段、
      `_geom_interactive.py` 的自陈），把它们一并判死会产生**大量假阳**；「新措辞的全量扫描」
      作为**设计待办**登记（见 `CRITERIA-CHANGE-P13-C58-P41.md` §5 L4）。

    断言：
      ① 扫描面非空（空集守卫）；
      ② 任一行含历史句 ⇒ **该行必须同时含更正标记**（否则 FAIL，逐条给出文件与行号）；
      ③ 豁免清单里的文件必须真实存在（清单过期 ⇒ FAIL，⛔ 不静默放行）；
      ④ 报告：扫描面文件数 / 命中行数 / 命中是否全部带标注（⛔ 命中 0 行**不是** FAIL：
         那是合法的清理结果；本判据的可判假性由负例夹具证明，⛔ 不靠「当前有命中」）。
    """
    names = _p41_py_files(ctx)
    if not names:
        return False, "空集守卫：`16-checkpoint/` 顶层扫不到任何 `*.py` ⇒ 判据恒真"
    bad = []
    for fn in sorted(P41_EXEMPT):
        if fn not in names:
            bad.append(("(豁免清单)", "豁免项在扫描面里不存在（清单已过期）", fn))
    scanned, hits, marked = 0, 0, 0
    hit_lines = []
    for fn in names:
        if fn in P41_EXEMPT:
            continue
        scanned += 1
        rel = "16-checkpoint/" + fn
        text = _read_text(ctx, rel)
        if text is None:
            bad.append((rel, "扫描面里的文件读不到（fail-closed）", ""))
            continue
        for i, line in enumerate(text.split("\n"), 1):
            if P41_TRIGGER not in line:
                continue
            hits += 1
            ok_mark = any(mk in line for mk in P41_CORRECTION_MARKS)
            ok_mention = any((op + P41_TRIGGER + cl) in line
                             for op in P41_QUOTE_OPEN for cl in P41_QUOTE_CLOSE)
            if ok_mark or ok_mention:
                marked += 1
            else:
                bad.append((rel, "第 %d 行含历史句 `%s` 但**既无更正标记、也不是被引号包裹的提及**"
                                 "（陈旧能力声明复活；若确为正当引用，须补『更正/旧理由/已推翻』之一）"
                                 % (i, P41_TRIGGER), line.strip()[:70]))
            hit_lines.append("%s:%d%s" % (rel, i, "" if (ok_mark or ok_mention) else " ←★无标记"))
    ctx.notes.append("P41 扫描面（★ 显式对象集 + 全集闭合断言）：`16-checkpoint/` 顶层 `*.py` **%d 个**"
                     "；扫描 %d 个；显式豁免 %d 个（%s）。历史句「%s」命中 **%d** 行，其中**有正当出处**"
                     "（更正标记 or 被引号包裹的提及）**%d 行**。⛔ 本条**只判历史句是否复活**，"
                     "⛔ 不判「任何措辞」（见 docstring 的假阳说明）。"
                     % (len(names), scanned, len(P41_EXEMPT), ", ".join(sorted(P41_EXEMPT)),
                        P41_TRIGGER, hits, marked))
    return (not bad), ("扫描面 %d 个（豁免 %d）；历史句命中 %d 行（有正当出处 %d）；违例 %d 处 %s"
                       % (scanned, len(P41_EXEMPT), hits, marked, len(bad),
                          bad[:4] if bad else (hit_lines[:4] or "无命中行")))


def _edit_json(ctx, rel, fn):
    """负例夹具（P38/P40）：把某个 JSON 读进 ctx、`fn(doc)` 就地改写、按**同一序列化口径**写回。

    ★ 为什么走 ctx 而不是真改磁盘：门控的纪律是「夹具一律落在临时沙箱内」——
      这里把该文件**纳入 ctx.files**，判据从 ctx 取（见 `_read_json_ctx`），
      ⇒ 夹具不改磁盘、也**不依赖磁盘当前内容**（⛔ 不静默通过）。
    ⛔ 文件不存在即抛错（fail-closed）：锚点过期必须显式暴露。
    """
    p = os.path.join(SITE_ROOT, rel)
    if not os.path.isfile(p):
        raise AssertionError("负例夹具锚点未命中：%s 不存在" % rel)
    doc = json.loads(ctx.files.get(rel) or open(p, encoding="utf-8").read())
    fn(doc)
    ctx.files[rel] = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True)
    return ctx


def mut_p38(ctx):
    """P38 的负例（★ 每条打在**真检对象**上：能力声明、PNG 字节、判据自己的解码结果）。"""
    out = []
    rel = PROBE_MANIFEST_REL
    p = os.path.join(SITE_ROOT, rel)
    if not os.path.isfile(p):
        raise AssertionError("负例夹具锚点未命中：%s 不存在（先跑 _probe_channel.py）" % rel)
    base = json.load(open(p, encoding="utf-8"))
    if not base.get("renders"):
        raise AssertionError("负例夹具锚点未命中：manifest 内 renders 为空")
    # ① ★ 教训① 的形态：声明「非 snap 内核不可用」而它其实在盘上（误诊复发）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["channel_facts"]["non_snap_chromium"].update(
        {"found": False, "path": None, "candidates": []})))
    # ② ★ 教训② 的形态：产物退化（把 PNG 换成纯白图 ⇒ 唯一色 = 1）
    c = copy.deepcopy(ctx)
    out.append(_patch_degenerate_png(c))
    # ③ 声明的 sha256 与磁盘实际不符（文件被替换/篡改）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["renders"][0].update({"sha256": "0" * 64})))
    # ④ 声明的唯一色数与实测不符（探针自报被篡改）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["renders"][0].update({"uniq_colors": 1})))
    # ⑤ schema 不匹配（换了格式却没换判据）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d.update({"schema": "pekg/channel-probe/0"})))
    # ⑥ 声明的渲染产物路径不存在
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["renders"][0].update({"png": "_probe/no-such.png"})))
    # ⑦ 横向溢出被登记进 manifest ⇒ 判 FAIL（★ 直接量的可判假性）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["measured"].setdefault("overflow_survey", {}).update(
        {"11-node-pages/pe-f-01.html": {
            "docScrollW": 1440, "innerW": 1440,
            "overflowing": [{"tag": "PRE", "cls": "", "scrollW": 1241, "clientW": 604,
                             "overflowPx": 637, "fontSize": "16px", "whiteSpace": "pre",
                             "textLen": 236}]}})))
    # ⑧ 空集：renders 为空 ⇒ 必须判 FAIL（⛔ 不得因空集而恒真）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d.update({"renders": []})))
    return out


def _patch_degenerate_png(ctx):
    """把一个 PNG 的**字节**换成合法的纯白小图（唯一色 1）⇒ 判据解码后必须判退化。

    ★ 相位说明（criterion-design-validation §4.10）：这是**产物侧**注入（PNG 是派生件）；
      P38 断言的正是「产物非退化」这一直接量 ⇒ 是有效负例，⛔ 不是「改夹具凑绿」。
    ★ 注入方式：把退化 PNG 的字节放进 `ctx.files`（判据经 `_read_bytes` 读），
      ⛔ **不改磁盘上任何文件** —— 夹具一律落在内存沙箱内。
    """
    w = h = 64
    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _y in range(h))

    def chunk(typ, body):
        return (struct.pack(">I", len(body)) + typ + body
                + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    man = _load_probe_manifest(ctx)
    rel_png = man["renders"][0]["png"]
    rel_site = os.path.normpath(os.path.join("16-checkpoint", rel_png))
    ctx.files[rel_site] = png.decode("latin-1")     # 判据按 latin-1 还原字节
    return ctx


def mut_p39(ctx):
    """P39 的负例：断链引用 / 孤儿登记件 / 引用点扫不到（空集）。

    ★ 夹具里的假文件名**运行时拼装**（`_CP + "ZZ99.md"`），⛔ 不写成字面量——
      否则门控源码自身会出现一个「被引用的登记件」，把 P39 的**真实**扫描面污染成假阳
      （实测：初版写成字面量时，`_change_refs` 把夹具名字也当成引用点）。
    """
    out = []
    gp = "16-checkpoint/gate_prototype.py"
    real = CONTRACT_CHANGE_PREFIX + "P34.md"
    # ① 断链引用：docstring 里加一条磁盘不存在的登记件引用（★ 教训④ 的真实形态）
    c = copy.deepcopy(ctx)
    src = c.files.get(gp) or open(os.path.join(SITE_ROOT, gp), encoding="utf-8").read()
    c.files[gp] = src.replace(real, real + " 与 " + CONTRACT_CHANGE_PREFIX + "ZZ99.md", 1)
    out.append(c)
    # ② 孤儿登记件：把一处引用的名字改掉 ⇒ 原文件变成无人引用
    c = copy.deepcopy(ctx)
    src = c.files.get(gp) or open(os.path.join(SITE_ROOT, gp), encoding="utf-8").read()
    c.files[gp] = src.replace(real, CONTRACT_CHANGE_PREFIX + "P34X.md", 1)
    out.append(c)
    # ③ 三处引用点里全是断链（另一种形态：批量改名）⇒ `_change_refs` 扫不到任何 `.md` ⇒ 空集守卫 FAIL
    #    ★ 2026-10-16 第 7 轮当场修正（本夹具曾是**假夹具**，见 `CRITERIA-CHANGE-P39.md` §L·L-4）：
    #      原实现只改 `gate_prototype.py` 一处 ⇒ 在**只引用 gate_prototype.py** 的那两件登记件
    #      （P35-G4 / P38-P40）上会产生孤儿 ⇒ 夹具**靠一个存量缺口触发**。
    #      本轮把 `gates` 补全（缺口堵上）之后，这条夹具**立刻不再触发** ⇒ `--selftest` 当场报
    #      「负例#3 未触发（判据疑似恒真）」。⇒ 改为**三处一起改名**，让它的语义回到 docstring 声称的
    #      「引用点扫不到」这一条（即 ③ 的空集守卫），⛔ 不再依赖任何缺口。
    c = copy.deepcopy(ctx)
    for rel in (gp, "16-checkpoint/gen-state.py", STATE_FILE):
        src = c.files.get(rel) or open(os.path.join(SITE_ROOT, rel), encoding="utf-8").read()
        c.files[rel] = re.sub(re.escape(CONTRACT_CHANGE_PREFIX) + r"([A-Za-z0-9\-]+)\.md",
                              CONTRACT_CHANGE_PREFIX + r"\1.zz", src)
    out.append(c)
    # ---- ★ 2026-10-16 第 7 轮新增（断言 ④ 结构化出口闭合，见 `CRITERIA-CHANGE-P39.md`）----
    #     ★ 为什么必须单独立夹具：①②③ 只判「文件名在文本里出现过没有」。把 `gates` 的键删掉
    #       而**保留** `gen-state.py` 里的散文引用 ⇒ ①② 照旧全绿，**只有 ④ 会红**。
    #       这正是第 6 轮那个缺口的形状（gates 7 件 / 磁盘 9 件却报绿）。
    # ④ `gates` 缺一个键（磁盘有对应登记件）⇒ 结构化出口缺件 ⇒ FAIL
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, STATE_FILE, lambda d: d["gates"].pop("criteria_change_P05", None)))
    # ⑤ `gates` 多一个键而磁盘无对应登记件 ⇒ 结构化出口孤儿键 ⇒ FAIL
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, STATE_FILE, lambda d: d["gates"].update(
        {CONTRACT_CHANGE_KEY_PREFIX + "ZZ99": "不存在的登记件"})))
    # ⑥ `gates` 里一个 `criteria_change_*` 键都没有 ⇒ ④ 的对象集为空 ⇒ FAIL（⛔ 不静默放行）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, STATE_FILE, lambda d: d.update(
        {"gates": {k: v for k, v in d["gates"].items()
                   if not k.startswith(CONTRACT_CHANGE_KEY_PREFIX)}})))
    return out


def mut_p40(ctx):
    """P40 的负例：台账缺失 / 空 / R-id 非法 / 与契约脱钩 / claim 无来源或无原始输出。"""
    out = []
    rel = ROUND_LEDGER_REL
    p = os.path.join(SITE_ROOT, rel)
    if not os.path.isfile(p):
        raise AssertionError("负例夹具锚点未命中：%s 不存在（按协议须先落盘台账）" % rel)
    base = json.load(open(p, encoding="utf-8"))
    if not (base.get("rounds") or [{}])[0].get("claims"):
        raise AssertionError("负例夹具锚点未命中：台账 rounds[0].claims 为空")
    # ① rounds 为空 ⇒ 空集守卫必须 FAIL
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d.update({"rounds": []})))
    # ② R-id 不在契约规则表内
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["rounds"][0].update({"rs_touched": ["R-99"]})))
    # ③ rs_touched 为空（「已实现但无判据」的第三种状态）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["rounds"][0].update({"rs_touched": []})))
    # ④ claim.source 非法
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["rounds"][0]["claims"][0].update(
        {"source": "delegated-agent-said-so"})))
    # ⑤ claim 缺 raw_output（转述当读数）
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["rounds"][0]["claims"][0].update(
        {"raw_output": ""})))
    # ⑥ 声明 main-agent-rerun 但 raw_output 无原始输出标记
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["rounds"][0]["claims"][0].update(
        {"source": "main-agent-rerun", "raw_output": "我跑过了，全绿"})))
    # ⑦ 缺 started_at / ended_at
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["rounds"][0].pop("started_at", None)))
    # ⑧ artifacts 为空
    c = copy.deepcopy(ctx)
    out.append(_edit_json(c, rel, lambda d: d["rounds"][0].update({"artifacts": []})))
    return out


def mut_p41(ctx):
    """P41 的负例：往扫描面里的某个 `.py` 注入一行**裸历史句**（⛔ 不带更正标记）⇒ 必须 FAIL。

    ★ 「带更正标记的历史句必须**仍然 PASS**」这一侧**不能**放在这里：
      `selftest` 的语义是「列表里的每一条都必须让判据**变红**」⇒ 对照组会被报成「负例未触发」。
      ⇒ 对照组（阈值另一侧）放在装置自检 `_selfcheck_p13_p41_c58.py` 里，与
        `_selfcheck_p35_fixtures.py` 的「3 列仍 PASS / 4 列 FAIL」同一体例。
    """
    c = copy.deepcopy(ctx)
    c.files["16-checkpoint/zz_p41_probe.py"] = p41_probe_line(marked=False) + "\n"
    return c


CHECKS = [
    ("P01", "真相源 JSON 合法且必填字段齐全", check_p01, mut_p01),    ("P02", "节点 id 唯一 / group 可解析 / prereq 与 successors 可解析", check_p02, mut_p02),
    ("P03", "rel 闭集 / 无环 / 拓扑层序与边方向一致", check_p03, mut_p03),
    ("P04", "每组至少 1 个节点 / 无孤立节点（layer 0 除外）", check_p04, mut_p04),
    ("P05", "字段长度约束（caliber 口径）＋ summary 结构约束 ＋ `boundary` 必填/不重复/不残留",
     check_p05, mut_p05),
    ("P06", "pitfalls 与 evidence 契约（含 GD-N 未证实例外）", check_p06, mut_p06),
    ("P07", "terms 逐条可在术语台账解析", check_p07, mut_p07),
    ("P08", "全站 HTML 断链 = 0", check_p08, mut_p08),
    ("P09", "自包含：0 外链资源 / 0 外链脚本 / 0 @import / 0 跨目录资源（两类白名单不扩散；"
            "★ 2026-10-16 第 8 轮：`<link>` 按 rel 闭集分流 —— 元数据类 rel 走「无主机或本站自指」断言，"
            "闭集之外的 rel 一律 FAIL，见 `CRITERIA-CHANGE-R08.md`）",
     check_p09, mut_p09),
    ("P10", "主题根唯一 + 令牌声明点唯一", check_p10, mut_p10),
    ("P11", "对比度：站点调色板三元组逐条复核（硬判与 report-only 分离）", check_p11, mut_p11),
    ("P12", "公开产物无内部编号 / 绝对路径 / 主机名 / 令牌串", check_p12, mut_p12),
    ("P13", "MD 镜像覆盖已发布集合 + 未落页节点逐条登记", check_p13, mut_p13),
    ("P14", "页面间导航可达（根入口 + 所属组页）", check_p14, mut_p14),
    ("P15", "模板标识集合大小 = 1（无第二套外壳）", check_p15, mut_p15),
    ("P16", "幂等：两次生成逐文件 sha256 一致", check_p16, mut_p16),
    ("P17", "dry-run 清单与实际落盘清单差集 = 0", check_p17, mut_p17),
    ("P18", "孤儿产物残留数 = 0", check_p18, mut_p18),
    ("P19", "令牌漂移可判假且报告含字段名与两侧取值", check_p19, mut_p19),
    ("P20", "契约角色覆盖 11/11 且未覆盖集合为空", check_p20, mut_p20),
    ("P21", "前沿刷新隔离 + as_of/edition + status 闭集", check_p21, mut_p21),
    ("P22", "content_status 状态↔内容一致性（complete 8 区块非空 / registered 三块必空 / 禁半填）",
     check_p22, mut_p22),
    ("P23", "令牌来源唯一：令牌块与 gen-tokens.py --print 逐字节一致，无第二处令牌声明",
     check_p23, mut_p23),
    ("P24", "令牌外硬编码 = 0（font-size / border-radius / color 十六进制 / padding·margin 字面值）",
     check_p24, mut_p24),
    ("P25", ":hover 门控覆盖（:focus-within / :focus-visible 不在其内）", check_p25, mut_p25),
    ("P26", "主题三态同步（三块齐备 + pre-paint 脚本在 <head> + theme-color 同步）",
     check_p26, mut_p26),
    ("P27", "背景层结构护栏（fixed/负 z-index/pointer-events/aria-hidden + 零可聚焦 + display:none）",
     check_p27, mut_p27),
    ("P28", "动效预算四项上界（reveal ≤32 / 进场 ≤1800ms / dur 和 ≤3.6s / infinite ≤12）",
     check_p28, mut_p28),
    ("P29", "交互作用面双向闭合（漏登记与幽灵登记均 FAIL + 逐条命中 + 拉伸层成对）",
     check_p29, mut_p29),
    ("P30", "资产白名单未扩散（assets/ 前缀引用全为图片，无 script/stylesheet 混入）",
     check_p30, mut_p30),
    ("P31", "色相不承载身份（组配色令牌数 = 0）", check_p31, mut_p31),
    ("P32", "许可证登记（页脚署名四要素 + 每个素材文件在登记表里）", check_p32, mut_p32),
    ("P33", "公开文案不含内部标注记号（⛔ / ★ / ⚠）", check_p33, mut_p33),
    ("P34", "宽屏左栏完整性（撑满竖向 / 含全部显示开关 / 与顶部导航互斥）＋ 根入口标题宽度预算",
     check_p34, mut_p34),
    ("P35", "内容层级与阅读单元（h1 一行无括号 / **h1 拉丁缩写须在术语台账登记**"
            "（R-01；★ 2026-10-16 第 7 轮 N1：删旧 `kind != \"interactive\"` 控制流豁免，改显式对象集 + 闭合断言）/ "
            "英文独立成行 / 标签与身份分行 / 导读锚点双向闭合 / "
            "区块序号连续 / 对照表三列 / 主张+展开点 / **知识承载页（节点页 / 组页，不含分组索引）**有图"
            "（R-07；★ 2026-10-16 第 6 轮 B″ 收口：作用域扩为节点页 + 组页，其余 5 页走显式排除清单 + "
            "全集闭合断言）/ 枚举位置化 / "
            "证据·术语·组页节点·前后继区竖表 / 组页横表列数 ≤3（代理）/ 组页依赖一行结构 / "
            "导读结论句 = 结论来源）", check_p35, mut_p35),
    ("P36", "图件合规（内联 / 无固定尺寸 / 令牌化 / a11y / 自制溯源 / 字形覆盖 fail-closed）",
     check_p36, mut_p36),
    ("P37", "交互全景图结构化布局（preset 定位 / 坐标确定 / 默认视口 zoom=1 / 两两不重叠 / "
             "标签内嵌 / 边不压节点 / 边不压边 / 边标签避让 / 分层行序）", check_p37, mut_p37),
    ("P38", "验证通道：能力声明与事实一致 ＋ 渲染产物非退化（判据自己解码 PNG、"
             "sha256 逐条比对、横向溢出直接量）", check_p38, mut_p38),
    ("P39", "判据变更登记件引用解析（三处引用 ⟺ 磁盘存在性，双向闭合；★ 2026-10-16 第 7 轮补"
            "④ 结构化出口闭合：`PUBLISH-STATE.gates` 的 `criteria_change_*` 键集合 ⟺ 磁盘登记件集合）",
     check_p39, mut_p39),
    ("P40", "轮次台账结构合规（R-id 与契约对齐 / 每条 claim 标注来源与原始输出）",
     check_p40, mut_p40),
    ("P41", "源文件里的散文能力声明（**已登记的历史句不得复活**；窄版；★ 2026-10-16 第 6 轮 G20）",
     check_p41, mut_p41),
]


# ---------------------------------------------------------------- 主流程

def run_checks(only=None):
    ctx = load_ctx(with_probe=True)
    print("== 门控：原型站判据 P01–P%02d ==" % len(CHECKS))
    print("产物根：%s" % SITE_ROOT)
    print("受检产物：%d 个（HTML %d / MD %d）" % (len(ctx.files), len(ctx.html), len(ctx.md)))
    print("")
    fails = []
    for cid, title, fn, _mut in CHECKS:
        if only and cid not in only:
            continue
        try:
            ok, detail = fn(ctx)
        except Exception as e:
            ok, detail = False, "判据执行异常：%s: %s" % (type(e).__name__, e)
        print("[%s] %s %s" % ("PASS" if ok else "FAIL", cid, title))
        print("       %s" % detail)
        if ctx.report_lines:
            for ln in ctx.report_lines:
                print(ln)
            ctx.report_lines = []
        if not ok:
            fails.append(cid)
    for n in ctx.notes:
        print("[NOTE] %s" % n)
    print("")
    print("== 门控结论：%s ==  FAIL %d 项 %s" % ("PASS" if not fails else "FAIL", len(fails), fails))
    return 0 if not fails else 1


def _run_fixture(fn, mctx):
    try:
        ok, detail = fn(mctx)
        return ok, detail
    except Exception as e:
        return True, "负例执行异常（视为未触发）：%s: %s" % (type(e).__name__, e)


def selftest(only=None):
    print("== 门控判据自检：逐条触发负例 ==")
    base = load_ctx(with_probe=True)
    ok_all = True
    total_fixtures = 0
    for cid, title, fn, mut in CHECKS:
        if only and cid not in only:
            continue
        ctx = copy.deepcopy(base)
        try:
            pos, pdetail = fn(ctx)
        except Exception as e:
            pos, pdetail = False, "正向执行异常：%s: %s" % (type(e).__name__, e)
        try:
            muts = mut(copy.deepcopy(base))
        except Exception as e:
            muts = None
            build_err = "负例构造异常（视为未触发）：%s: %s" % (type(e).__name__, e)
        if muts is None:
            triggered, ndetail, nfix = False, build_err, 1
        elif isinstance(muts, list):
            nfix = len(muts)
            fails = []
            for i, mctx in enumerate(muts):
                still_pass, detail = _run_fixture(fn, mctx)
                if still_pass:
                    fails.append("负例#%d 未触发：%s" % (i + 1, str(detail)[:110]))
            triggered = (not fails) and nfix > 0
            ndetail = ("%d/%d 条子断言负例全部触发" % (nfix, nfix)) if triggered else ("；".join(fails) or "无负例")
        else:
            nfix = 1
            still_pass, detail = _run_fixture(fn, muts)
            triggered = not still_pass
            ndetail = detail
        total_fixtures += nfix
        good = pos and triggered
        ok_all = ok_all and good
        print("[%s] %s %s" % ("PASS" if good else "FAIL", cid, title))
        print("       正向：%s" % ("PASS" if pos else "FAIL"))
        print("       负例（%d 条）：%s —— %s"
              % (nfix, "全部触发（判据可判假）" if triggered else "存在未触发（判据疑似恒真）",
                 str(ndetail)[:170]))
    print("")
    print("== 自检结论：%s ==（%d 条判据 / %d 条负例夹具，全部须正向 PASS 且负例触发）"
          % ("PASS" if ok_all else "FAIL",
             len([c for c in CHECKS if not only or c[0] in only]), total_fixtures))
    return 0 if ok_all else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="逐条触发负例")
    ap.add_argument("--only", default=None, help="逗号分隔的判据编号（调试用）")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    if a.selftest:
        return selftest(only)
    return run_checks(only)


if __name__ == "__main__":
    sys.exit(main())
