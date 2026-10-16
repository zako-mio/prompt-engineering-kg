#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_seo_meta.py —— 发布级 head 元数据与站点级发现协议门控（判据 S1–S11，**硬档**）

★ 为什么单独一个门控文件（2026-10-16 第 8 轮，SH0–SH5 的 SH4 基线）：
  head 元数据是**搜索引擎与社交抓取器**的接口，与 `gate_prototype.py` 的 P01–P41（本站自建判据族）
  来源不同；混在一起会让「这条判据出自哪条要求」无法回答。⇒ 分文件、判据编号前缀（S）区分。
  ⛔ 判据实现**不复制**：本文件一律 `import` `gate_prototype` 的工具（`load_ctx`、`_link_tags`、
  `_abs_url` 的真相源 `gen-common`、`SITE_BASE_URL`）。

★ 判据对象（**显式对象集 + 全集闭合断言**，R-23 / 契约 §4⑤ 第 3 条）：
  · 受检 = 发布面全部 `*.html`（＝ `load_ctx()` 读到的 `ctx.html` 全键集）
  · 排除 = ∅（⛔ 本门控**不设** `og_url_image_exempt` / `favicon_exempt` 一类登记豁免 ——
    姊妹站的 profile 把「这两张豁免表必须为空」写成了硬要求；本件直接不提供该字段）
  · 闭合断言 = `S1 != ∅`（空集守卫）＋ 逐页断言 ⇒ 出现未分类的页 ⇒ FAIL

★ **canonical 归一化口径（本门控定的唯一口径，⛔ 不得两处各推一份）**：
  `X/index.html` 与 `X/` 视为**同一页**（两侧都按 `rstrip("index.html")` 归一后比较，再 `rstrip("/")`）。
  理由：GitHub Pages 对 `…/index.html` 会 301 到 `…/`，两者是同一资源的两种写法；
  若判据只认其中一种，就会把**正确的产物**判成错误（那是判据对象与断言对象不一致）。
  ⛔ 本口径只用于**比较**，不用于生成 —— 生成侧一律写显式 `index.html`（`_abs_url` 的原样拼接）。

用法：
  python3 gate_seo_meta.py            只读裁决；退出码 0 = 全 PASS
  python3 gate_seo_meta.py --selftest 逐条触发负例（判据可判假性自检）
  python3 gate_seo_meta.py --only S5  只跑某条（调试用）
"""

import argparse
import copy
import importlib.util
import os
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))


def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _imp(os.path.join(HERE, "gate_prototype.py"), "pekg_gate_prototype")
C = _imp(os.path.join(HERE, "gen-common.py"), "pekg_gen_common_seo")

TITLE_RE = G.re.compile(r"<title>([^<]*)</title>", G.re.I)
META_DESC_RE = G.re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', G.re.I)
OG_RE = G.re.compile(r'<meta\s+property="(og:[a-z]+)"\s+content="([^"]*)"', G.re.I)
CANONICAL_RE = G.re.compile(r'<link\b[^>]*rel="canonical"[^>]*href="([^"]*)"'
                            r'|<link\b[^>]*href="([^"]*)"[^>]*rel="canonical"', G.re.I)
XML_LOC_RE = G.re.compile(r"<loc>([^<]*)</loc>")
# ★ 短描述下限（16 字）：这是**长度护栏**，不是「可读性阈值」——
#   它只说「比这个还短的句子不可能承载一页的摘要」。⛔ 不宣称「≥16 就一定好」（那是另一回事）。
DESC_MIN = 16
OG_REQUIRED = ("og:type", "og:title", "og:description", "og:url", "og:image")


def _norm_url(u):
    """canonical 归一化（见模块 docstring）：`…/index.html` ↔ `…/` 视为同一页。"""
    u = (u or "").strip()
    if u.endswith("/index.html"):
        u = u[: -len("index.html")]
    return u.rstrip("/") if u.endswith("/") else u


def _rel_of(u):
    """把本站绝对 URL 还原成站内相对路径（⛔ 非本站 URL 返回 None）。"""
    base = C.SITE_BASE_URL
    if not (u or "").startswith(base):
        return None
    return u[len(base):] or "index.html"


def _present(ctx):
    """受检对象集（＝ `ctx.html` 全键集）；空集守卫由各判据自己判。"""
    return sorted(ctx.html)


def _expected(ctx):
    """每页的期望站点绝对 URL（由产物相对路径派生，⛔ 不手抄）。"""
    return {rel: C._abs_url(rel) for rel in ctx.html}


# ---------------------------------------------------------------- S1–S11


def check_s1(ctx):
    """S1：每页在 `<head>` 的**元数据区**有且仅有 1 个非空 `<title>`，且其内容**含站点名**。

    ★ 判据对象必须收窄到 head 的元数据区（R-23）：内联 SVG 的**节点标签**也是 `<title>` 元素
      （Graphviz 为每个节点写 `<title>L1</title>`），全页扫 `<title>` 会把它们一并计数
      ⇒ 本轮实测 47 页被判「`<title>` 12 个」（假阳）。
      ⇒ 切片口径 = `</title>` 之后到首个 `<style>` 之前的元数据段（本站 `page_shell` 的固定顺序：
         `charset` → `viewport` → `title` → 注释 → og/canonical/theme-color/icon → `<style>`）。
      ⛔ 这不是放宽阈值：`<title>` 在 `<head>` 里恰好 1 个这一断言一个字节没改，只是不再把
        正文里同名但语义不同的元素算进来。
    """
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel in _present(ctx):
        text = ctx.html[rel]
        head = text.split("</head>", 1)[0]
        # 元数据区 = 首个 </title> 之后 到 首个 <style> 之前；若没有 <style> 则取到 </head>
        cut = head.split("</head>", 1)[0]
        first_title_end = cut.find("</title>")
        region = cut[first_title_end + len("</title>"):] if first_title_end >= 0 else cut
        region = region.split("<style", 1)[0]
        titles = TITLE_RE.findall(text)
        doc_titles = TITLE_RE.findall(head.split("<style", 1)[0])
        if len(doc_titles) != 1:
            bad.append((rel, "head 元数据区 `<title>` %d 个（应为恰 1；全页共 %d 个，"
                             "差额来自内联 SVG 的节点标签）" % (len(doc_titles), len(titles)), ""))
            continue
        if not doc_titles[0].strip():
            bad.append((rel, "<title> 为空", ""))
        if C.SITE_TITLE not in doc_titles[0]:
            bad.append((rel, "<title> 不含站点名", doc_titles[0][:60]))
        if "<title>" in region:
            bad.append((rel, "head 元数据区出现第 2 个 <title>", ""))
    return (not bad), ("受检页面 %d 个：head 元数据区 `<title>` 恰 1 且含站点名「%s」；违例 %d 处 %s"
                       % (len(ctx.html), C.SITE_TITLE, len(bad), bad[:4]))


def check_s2(ctx):
    """S2：每页有且仅有 1 个非空 `<meta name="description">`。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel in _present(ctx):
        ms = META_DESC_RE.findall(ctx.html[rel])
        if len(ms) != 1:
            bad.append((rel, 'meta description %d 个（应为恰 1）' % len(ms), ""))
        elif not ms[0].strip():
            bad.append((rel, "meta description 为空", ""))
    return (not bad), ("受检页面 %d 个：`meta description` 恰 1 且非空；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


def check_s3(ctx):
    """S3：每页 `og:*` 五项齐备（`og:type` / `og:title` / `og:description` / `og:url` / `og:image`）且值非空。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel in _present(ctx):
        got = {k: v for k, v in OG_RE.findall(ctx.html[rel])}
        for k in OG_REQUIRED:
            if k not in got:
                bad.append((rel, "缺 %s" % k, ""))
            elif not got[k].strip():
                bad.append((rel, "%s 值为空" % k, ""))
    return (not bad), ("受检页面 %d 个：og 五项（%s）齐备且非空；违例 %d 处 %s"
                       % (len(ctx.html), " / ".join(OG_REQUIRED), len(bad), bad[:4]))


def check_s4(ctx):
    """S4：每页**恰 1 条** `rel="canonical"` 声明，且值非空。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel in _present(ctx):
        hits = [a or b for a, b in CANONICAL_RE.findall(ctx.html[rel])]
        if len(hits) != 1:
            bad.append((rel, 'rel="canonical" %d 条（应为恰 1）' % len(hits), ""))
        elif not hits[0].strip():
            bad.append((rel, "canonical 值为空", ""))
    return (not bad), ("受检页面 %d 个：`rel=\"canonical\"` 恰 1 且非空；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


def check_s5(ctx):
    """S5：每页 `canonical` **自指**（归一化后等于本页的期望 URL）且其目标**是本仓的现存页**。

    ★ 两半都必要：只判「自指」会放过「指向一个不存在的页」；只判「存在」会放过「指向别的页」。
    """
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    exp = {k: _norm_url(v) for k, v in _expected(ctx).items()}
    known = set(exp.values())
    for rel in _present(ctx):
        hits = [a or b for a, b in CANONICAL_RE.findall(ctx.html[rel])]
        if len(hits) != 1:
            continue                       # 由 S4 处置，⛔ 不在本条重复报同一个缺陷
        c = _norm_url(hits[0])
        if c != exp[rel]:
            bad.append((rel, "canonical 非自指", (hits[0], _expected(ctx)[rel])))
        elif c not in known:
            bad.append((rel, "canonical 指向本仓不存在的页", hits[0]))
    return (not bad), ("受检页面 %d 个：canonical 自指（归一化口径：`X/index.html` ≡ `X/`）"
                       "且目标在现存页集合内（%d 页）；违例 %d 处 %s"
                       % (len(ctx.html), len(known), len(bad), bad[:4]))


def check_s6(ctx):
    """S6：每页 `og:url` **等于** canonical（归一化）—— 否则两个抓取器会看到两个「本页地址」。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel in _present(ctx):
        got = {k: v for k, v in OG_RE.findall(ctx.html[rel])}
        hits = [a or b for a, b in CANONICAL_RE.findall(ctx.html[rel])]
        if "og:url" not in got or len(hits) != 1:
            continue                       # 由 S3 / S4 处置
        if _norm_url(got["og:url"]) != _norm_url(hits[0]):
            bad.append((rel, "og:url ≠ canonical", (got["og:url"], hits[0])))
    return (not bad), ("受检页面 %d 个：`og:url` 与 canonical 一致（归一化后）；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


def check_s7(ctx):
    """S7：每页 `rel="icon"` 声明的**目标在盘上存在**（发布根感知：解析到本仓即算）。

    ★ 与 `gate_a11y` 的 A6 分工：A6 只断「声明存在」；本条断「目标可达」。
      ⛔ 两条不重复报同一个缺陷（A6 判条数，S7 判可达）。
    """
    bad = []
    hits = 0
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel in _present(ctx):
        for lrel, lhref, tag in G._link_tags(ctx.html[rel]):
            if "icon" not in lrel.split() or not lhref:
                continue
            hits += 1
            tgt = G.resolve_site_path(rel, lhref)
            if tgt is None:
                bad.append((rel, "icon 目标不是站内相对路径", lhref))
            elif not os.path.isfile(os.path.join(G.SITE_ROOT, tgt)):
                bad.append((rel, "icon 目标在盘上不存在", (lhref, tgt)))
    if hits == 0:
        return False, "空集守卫：全站没有任何 rel=icon 声明 ⇒ 判据恒真"
    return (not bad), ("受检页面 %d 个：`rel=\"icon\"` 声明 %d 条，逐条解析到盘上存在；违例 %d 处 %s"
                       % (len(ctx.html), hits, len(bad), bad[:4]))


def check_s8(ctx):
    """S8：`robots.txt` 存在、非空，且含 `Sitemap:` 行（⛔ 不接受「语义等价」的其它写法）。"""
    if ROBOTS_REL not in ctx.files:
        return False, "缺失：%s 不在发布面（判据对象不存在 ⇒ 不是 PASS）" % ROBOTS_REL
    text = ctx.files[ROBOTS_REL]
    if not text.strip():
        return False, "%s 为空" % ROBOTS_REL
    bad = []
    sm = [ln for ln in text.splitlines() if ln.strip().lower().startswith("sitemap:")]
    if not sm:
        bad.append(("(全站)", "robots.txt 无 Sitemap: 行", ""))
    else:
        if not any(ln.split(":", 1)[1].strip() for ln in sm):
            bad.append(("(全站)", "Sitemap: 行的值为空", ""))
        if not any(_norm_url(ln.split(":", 1)[1].strip()) == _norm_url(C._abs_url(SITEMAP_REL))
                   for ln in sm):
            bad.append(("(全站)", "Sitemap: 未指向本仓 sitemap.xml", sm[0][:80]))
    if not any(ln.strip().lower().startswith("user-agent:") for ln in text.splitlines()):
        bad.append(("(全站)", "robots.txt 无 User-agent 行", ""))
    return (not bad), ("robots.txt %d 字节 / %d 行；Sitemap 行 %d 条；违例 %d 处 %s"
                       % (len(text.encode("utf-8")), len(text.splitlines()), len(sm), len(bad), bad[:4]))


def check_s9(ctx):
    """S9：`sitemap.xml` 的 `loc` 集合 ⟺ 发布面 HTML 集合（**双向闭合**，⛔ 不抽样）。"""
    if SITEMAP_REL not in ctx.files:
        return False, "缺失：%s 不在发布面（判据对象不存在 ⇒ 不是 PASS）" % SITEMAP_REL
    text = ctx.files[SITEMAP_REL]
    locs = XML_LOC_RE.findall(text)
    if not locs:
        return False, "空集守卫：sitemap.xml 没有任何 <loc> ⇒ 判据恒真"
    bad = []
    listed = {}
    for u in locs:
        rel = _rel_of(u)
        if rel is None:
            bad.append(("(sitemap)", "loc 不是本站绝对 URL", u[:90]))
            continue
        rel = rel[:-len("index.html")] if rel.endswith("index.html") else rel
        listed.setdefault(_norm_url(rel), []).append(u)
    actual = {}
    for rel in ctx.html:
        key = _norm_url(rel[:-len("index.html")] if rel.endswith("index.html") else rel)
        actual.setdefault(key, []).append(rel)
    missing = sorted(k for k in actual if k not in listed)
    orphan = sorted(k for k in listed if k not in actual)
    if missing:
        bad.append(("(sitemap)", "发布面有页但 sitemap 未列（%d 个）" % len(missing), missing[:4]))
    if orphan:
        bad.append(("(sitemap)", "sitemap 列出了不存在的页（%d 个）" % len(orphan), orphan[:4]))
    dup = sorted(k for k, v in listed.items() if len(v) > 1)
    if dup:
        bad.append(("(sitemap)", "同一页被列多次", dup[:4]))
    return (not bad), ("sitemap.xml：<loc> %d 条 ⟺ 发布面 HTML %d 页（双向闭合；"
                       "missing %d / orphan %d / dup %d）；违例 %d 处 %s"
                       % (len(locs), len(ctx.html), len(missing), len(orphan), len(dup),
                          len(bad), bad[:4]))


def check_s10(ctx):
    """S10：`sitemap.xml` 是**良构**的，且⛔ 不含 `<lastmod>`（墙钟时间戳会破坏构建幂等）。"""
    if SITEMAP_REL not in ctx.files:
        return False, "缺失：%s 不在发布面" % SITEMAP_REL
    text = ctx.files[SITEMAP_REL]
    bad = []
    if not text.lstrip().startswith("<?xml"):
        bad.append(("(sitemap)", "缺 XML 声明", ""))
    if "<urlset" not in text:
        bad.append(("(sitemap)", "缺 <urlset> 根元素", ""))
    if 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"' not in text:
        bad.append(("(sitemap)", "<urlset> 缺 sitemaps.org 命名空间", ""))
    opens, closes = text.count("<url>"), text.count("</url>")
    if opens != closes or opens == 0:
        bad.append(("(sitemap)", "<url> 开闭不平衡", (opens, closes)))
    if "<lastmod>" in text:
        bad.append(("(sitemap)", "出现了 <lastmod>（破坏构建幂等：两次 --write 的 sha256 会不同）", ""))
    # 良构性：用内置 XML 解析器**真解析一次**（⛔ 不靠正则假装良构）
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(text)
    except Exception as e:                                        # noqa: BLE001
        bad.append(("(sitemap)", "XML 解析失败：%s" % e, ""))
    return (not bad), ("sitemap.xml %d 字节；<url> %d 对；XML 真解析 + 无 lastmod；违例 %d 处 %s"
                       % (len(text.encode("utf-8")), opens, len(bad), bad[:4]))


def check_s11(ctx):
    """S11：`description` 的**质量护栏**：① 长度 ≥ `DESC_MIN`；② ⛔ 不等于站点标语。

    ★ 这是**长度护栏**而不是「可读性阈值」：它只说「比这更短的句子不可能承载一页摘要」，
      ⛔ 不宣称「达到下限就一定好」。同理，与站点标语**近义**（同一句式）也判 FAIL ——
      本站 2026-10-16 实测到一例真实缺陷：交互页的 description 只取导语首句，而首句恰是受众从句，
      与 `SITE_TAGLINE` 高度近义 ⇒ 对搜索引擎等于没有信息。
    """
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    lens = []
    for rel in _present(ctx):
        ms = META_DESC_RE.findall(ctx.html[rel])
        if len(ms) != 1:
            continue                       # 由 S2 处置
        d = ms[0].strip()
        lens.append(len(d))
        if len(d) < DESC_MIN:
            bad.append((rel, "description 仅 %d 字（下限 %d）" % (len(d), DESC_MIN), d[:50]))
        elif d.rstrip("。.") == C.SITE_TAGLINE.rstrip("。."):
            bad.append((rel, "description 等于站点标语（全站同一句 = 没有描述）", ""))
    return (not bad), ("受检页面 %d 个：description 长度 %d–%d 字（下限 %d），且无「等于站点标语」；"
                       "违例 %d 处 %s"
                       % (len(ctx.html), min(lens) if lens else 0, max(lens) if lens else 0,
                          DESC_MIN, len(bad), bad[:4]))


SITEMAP_REL = "sitemap.xml"
ROBOTS_REL = "robots.txt"

CHECKS = [
    ("S1", "<title> 恰 1 且含站点名", check_s1, None),
    ("S2", "meta description 恰 1 且非空", check_s2, None),
    ("S3", "og 五项齐备且非空", check_s3, None),
    ("S4", "rel=canonical 恰 1 且非空", check_s4, None),
    ("S5", "canonical 自指且目标为本仓现存页", check_s5, None),
    ("S6", "og:url 与 canonical 一致（归一化）", check_s6, None),
    ("S7", "rel=icon 目标在盘上存在", check_s7, None),
    ("S8", "robots.txt 含 Sitemap: 且指向本仓", check_s8, None),
    ("S9", "sitemap loc 集合 ⟺ 发布面 HTML 集合", check_s9, None),
    ("S10", "sitemap 良构且无 lastmod", check_s10, None),
    ("S11", "description 长度下限且不等于站点标语", check_s11, None),
]

# ---------------------------------------------------------------- 负例夹具


def _node(ctx):
    return G._first_html(ctx, "11-node-pages")


def mut_s1(ctx):
    """S1 的负例：① 页名不含站点名（用 `re.sub` **替换**而不是追加第 2 个 `<title>`）；
    ② head 元数据区出现**第 2 个** `<title>`（在 `<style>` 之前插入）。

    ★ 初版夹具往 `</head>` 前插 `<title>`，落点其实在元数据区**之外**（本站的 `<style>` 在前）
      ⇒ 判据看不到、负例不触发（本轮自检当场报出）。夹具的落点必须与判据对象的切片**一致**。
    """
    out = []
    k = _node(ctx)
    c = copy.deepcopy(ctx)
    c.html[k] = c.files[k] = TITLE_RE.sub("<title>只有页名</title>", c.html[k], count=1)
    out.append(c)
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, "<style>", "<title>第二个</title><style>"))
    return out


def mut_s2(ctx):
    out = []
    k = _node(ctx)
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, '<meta name="description"', '<meta data-x="description"'))
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, "</head>", '<meta name="description" content=""></head>'))
    return out


def mut_s3(ctx):
    out = []
    k = _node(ctx)
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, "</head>", '<meta property="og:image" content=""></head>'))
    return out


def mut_s4(ctx):
    out = []
    k = _node(ctx)
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, "</head>", '<link rel="canonical" href="%sindex.html"></head>'
                                      % C.SITE_BASE_URL))
    return out


def mut_s5(ctx):
    out = []
    k = _node(ctx)
    # ① 指向别页（非自指）
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, '<link rel="canonical" href="%s11-node-pages/pe-a-01.html">'
                              % C.SITE_BASE_URL,
                        '<link rel="canonical" href="%s11-node-pages/pe-a-02.html">'
                        % C.SITE_BASE_URL))
    # ② 指向本仓不存在的页
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, '<link rel="canonical" href="%s11-node-pages/pe-a-01.html">'
                              % C.SITE_BASE_URL,
                        '<link rel="canonical" href="%s11-node-pages/nope.html">'
                        % C.SITE_BASE_URL))
    return out


def mut_s6(ctx):
    k = _node(ctx)
    c = copy.deepcopy(ctx)
    return G._patch(c, k, '<meta property="og:url" content="%s11-node-pages/pe-a-01.html">'
                          % C.SITE_BASE_URL,
                    '<meta property="og:url" content="%sindex.html">' % C.SITE_BASE_URL)


def mut_s7(ctx):
    k = _node(ctx)
    c = copy.deepcopy(ctx)
    return G._patch(c, k, '<link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">',
                    '<link rel="icon" type="image/svg+xml" href="../assets/nope.svg">')


def mut_s8(ctx):
    out = []
    c = copy.deepcopy(ctx)
    c.files[ROBOTS_REL] = "User-agent: *\nAllow: /\n"
    out.append(c)
    c = copy.deepcopy(ctx)
    c.files[ROBOTS_REL] = "User-agent: *\nSitemap: https://evil.example.com/sitemap.xml\n"
    out.append(c)
    return out


def mut_s9(ctx):
    out = []
    c = copy.deepcopy(ctx)
    c.files[SITEMAP_REL] = c.files[SITEMAP_REL].replace(
        "  <url><loc>%s</loc></url>\n" % C._abs_url("14-views/02-frontier.html"), "")
    out.append(c)
    c = copy.deepcopy(ctx)
    c.files[SITEMAP_REL] = c.files[SITEMAP_REL].replace(
        "</urlset>", "  <url><loc>%sghost.html</loc></url>\n</urlset>" % C.SITE_BASE_URL)
    out.append(c)
    return out


def mut_s10(ctx):
    out = []
    c = copy.deepcopy(ctx)
    c.files[SITEMAP_REL] = c.files[SITEMAP_REL].replace(
        "</urlset>", "</url>") + "</urlset>\n"
    out.append(c)
    c = copy.deepcopy(ctx)
    c.files[SITEMAP_REL] = c.files[SITEMAP_REL].replace(
        "<url><loc>", "<url><lastmod>2026-10-16</lastmod><loc>")
    out.append(c)
    return out


def mut_s11(ctx):
    """S11 的负例：① 描述过短；② 描述等于站点标语。

    ★ 用 `re.sub` **替换**已有那条的 content（⛔ 不追加第 2 条）—— 追加会连带触发 S2 的条数断言，
      那是**另一条**判据的对象；夹具必须只打在本条上（「一条夹具一个断言」）。
    """
    out = []
    k = _node(ctx)
    c = copy.deepcopy(ctx)
    c.html[k] = c.files[k] = META_DESC_RE.sub(
        '<meta name="description" content="太短">', c.html[k], count=1)
    out.append(c)
    c = copy.deepcopy(ctx)
    c.html[k] = c.files[k] = META_DESC_RE.sub(
        '<meta name="description" content="%s">' % C.SITE_TAGLINE, c.html[k], count=1)
    out.append(c)
    return out


for _cid, _title, _fn, _ in list(CHECKS):
    _fn.__name__ = "check_" + _cid.lower()
CHECKS = [(cid, title, fn, globals().get("mut_" + cid.lower())) for cid, title, fn, _ in CHECKS]


def _run_fixture(fn, ctx):
    try:
        return fn(ctx)
    except Exception as e:                                        # noqa: BLE001
        return False, "%s: %s" % (type(e).__name__, e)


def run_checks(only=None):
    ctx = G.load_ctx(with_probe=False)
    print("== 发布级元数据门控：判据 %s ==" % "–".join(c for c, _, _, _ in CHECKS))
    print("产物根：%s" % G.SITE_ROOT)
    print("受检页面：%d 个（发布面全部 *.html；排除集 = ∅）" % len(ctx.html))
    print("")
    fails = []
    for cid, title, fn, _mut in CHECKS:
        if only and cid not in only:
            continue
        ok, detail = _run_fixture(fn, ctx)
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


def selftest(only=None):
    print("== 发布级元数据门控自检：逐条触发负例 ==")
    base = G.load_ctx(with_probe=False)
    ok_all = True
    total = 0
    for cid, title, fn, mut in CHECKS:
        if only and cid not in only:
            continue
        if mut is None:
            print("[SKIP] %s %s（⛔ 无负例夹具 ⇒ 该判据不可判假，须补）" % (cid, title))
            ok_all = False
            continue
        pos, _ = _run_fixture(fn, copy.deepcopy(base))
        muts = mut(copy.deepcopy(base))
        muts = muts if isinstance(muts, list) else [muts]
        fails = []
        for i, mctx in enumerate(muts):
            still, detail = _run_fixture(fn, mctx)
            if still:
                fails.append("负例#%d 未触发：%s" % (i + 1, str(detail)[:120]))
        triggered = (not fails) and muts
        total += len(muts)
        good = pos and triggered
        ok_all = ok_all and good
        print("[%s] %s %s" % ("PASS" if good else "FAIL", cid, title))
        print("       正向：%s" % ("PASS" if pos else "FAIL"))
        print("       负例（%d 条）：%s" % (len(muts),
                                          "全部触发（判据可判假）" if triggered else "；".join(fails)))
    print("")
    print("== 自检结论：%s ==（%d 条判据 / %d 条负例夹具）"
          % ("PASS" if ok_all else "FAIL", len(CHECKS), total))
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
