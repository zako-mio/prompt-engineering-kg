#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_a11y.py —— 无障碍门控（判据 A1–A7，**硬档**）

★ 为什么单独一个门控文件（2026-10-16 第 8 轮，SH0–SH5 的 SH2 基线）：
  `gate_prototype.py` 的 P01–P41 是本仓**自建**的判据族；无障碍是**另一条来源**的要求
  （SH2 标准档 + 姊妹站 `algorithm-knowledge-graph` 的 `gate_a11y.py` 同族），
  两者混在一个文件里会让「这条判据出自哪条要求」无法回答。⇒ 分文件、同名判据编号前缀（A）区分。
  ⛔ 判据实现**不复制**：本文件一律 `import` `gate_prototype` 的工具（正则、`load_ctx`、`run`）。

★ 判据对象（**显式对象集 + 全集闭合断言**，R-23 / 契约 §4⑤ 第 3 条）：
  · 受检 = 发布面全部 `*.html`（＝ `load_ctx()` 读到的 `ctx.html` 全键集）
  · 排除 = ∅（⛔ 本门控**不设** `skiplink_exempt` / `main_landmark_exempt` 一类登记豁免）
  · 闭合断言 = `A1 != ∅`（空集守卫）＋ 逐页断言 ⇒ 出现未分类的页 ⇒ FAIL

★ 每条判据都必须**可判假**：`--selftest` 逐条注入负例，任一条未触发即判该判据本身不合格。

用法：
  python3 gate_a11y.py                只读裁决，输出逐条 PASS/FAIL；退出码 0 = 全 PASS
  python3 gate_a11y.py --selftest     逐条触发负例（判据可判假性自检）
  python3 gate_a11y.py --only A3      只跑某条（调试用）
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

# ---------------------------------------------------------------- 判据（A 段）

SKIP_RE = G.re.compile(r'<a\b[^>]*class="skip"[^>]*href="#([^"]+)"[^>]*>', G.re.I)
MAIN_RE = G.re.compile(r"<main\b[^>]*>", G.re.I)
SVG_RE = G.re.compile(r"<svg\b[^>]*>", G.re.I)
CANVAS_RE = G.re.compile(r"<canvas\b[^>]*>", G.re.I)
ATTR_ID_RE = G.re.compile(r'\bid\s*=\s*"([^"]*)"', G.re.I)
ATTR_LABEL_RE = G.re.compile(r'\baria-label\s*=\s*"([^"]*)"', G.re.I)
ATTR_LABELLEDBY_RE = G.re.compile(r'\baria-labelledby\s*=\s*"([^"]*)"', G.re.I)
ATTR_HIDDEN_RE = G.re.compile(r'\baria-hidden\s*=\s*"(true)"', G.re.I)
# ★ `\b` 在 `-` 处**成立**（`-` 不是词字符）⇒ `:focus-visible-x` 会**照旧命中**，
#   负例「把 :focus-visible 改成 :focus-visible-x」就不会触发（本轮实测：自检报「负例未触发」）。
#   ⇒ 右界必须写成 `(?![\w-])` 而不是 `\b`。
FOCUS_VISIBLE_RE = G.re.compile(r":focus-visible(?![\w-])")


def check_a1(ctx):
    """A1：每页**恰 1 个**跳转正文链接（`a.skip`），且其 `href="#id"` 的目标 `id` 在本页存在。

    ★ 判「目标存在」的理由：skip link 指向一个不存在的锚点等于没有回退路径 ——
      而它恰恰是键盘用户**唯一**的绕过导航手段（姊妹站的 `gate_a11y.py` A3 同口径）。
    """
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel, text in sorted(ctx.html.items()):
        hits = SKIP_RE.findall(text)
        if len(hits) != 1:
            bad.append((rel, "跳转正文链接 %d 个（应为恰 1）" % len(hits), ""))
            continue
        tid = hits[0]
        if not G.re.search(r'\bid\s*=\s*"%s"' % G.re.escape(tid), text):
            bad.append((rel, "跳转目标 #%s 在本页不存在" % tid, ""))
    return (not bad), ("受检页面 %d 个：`a.skip` 恰 1 且目标锚点存在；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


def check_a2(ctx):
    """A2：每页**至少 1 条** `:focus-visible` 规则（键盘焦点必须在任何输入设备上都看得见）。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel, text in sorted(ctx.html.items()):
        css = "".join(G.STYLE_RE.findall(text))
        if not FOCUS_VISIBLE_RE.search(css):
            bad.append((rel, ":focus-visible 规则 0 条", ""))
    return (not bad), ("受检页面 %d 个：每页 `:focus-visible` ≥1；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


def check_a3(ctx):
    """A3：每页**恰 1 个** `<main>` 地标。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel, text in sorted(ctx.html.items()):
        n = len(MAIN_RE.findall(text))
        if n != 1:
            bad.append((rel, "`<main>` %d 个（应为恰 1）" % n, ""))
    return (not bad), ("受检页面 %d 个：`<main>` 恰 1；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


def _accessible(tag, text):
    """一个内联图形元素是否**可访问**：非装饰 = 有可访问名；装饰 = `aria-hidden="true"`。"""
    if ATTR_HIDDEN_RE.search(tag):
        return True, "装饰（aria-hidden）"
    named = (ATTR_LABEL_RE.search(tag) and ATTR_LABEL_RE.search(tag).group(1).strip())
    if named:
        return True, "aria-label"
    if ATTR_LABELLEDBY_RE.search(tag):
        ids = ATTR_LABELLEDBY_RE.search(tag).group(1).split()
        if ids and all(G.re.search(r'\bid\s*=\s*"%s"' % G.re.escape(i), text) for i in ids):
            return True, "aria-labelledby（目标为本页 id）"
        return False, "aria-labelledby 指向本页不存在的 id"
    return False, "既无可访问名也未标 aria-hidden"


NAMING = "aria-label|aria-labelledby"


def _decorative_but_exposed(text):
    """装饰图形却被**暴露**的实例：同一元素既有 `aria-hidden="true"` 又有可访问名。

    ★ 为什么这是 FAIL 而不是唠叨：`aria-hidden="true"` 与 `role="img" aria-label` 语义相反，
      同时出现属**冲突声明** —— 不同 ATS 会给出不同结果（有的念、有的不念），
      而作者的本意无从判断。这一个面连在真实的 axe 类工具里都要人工复核。
    """
    bad = []
    for rx, kind in ((SVG_RE, "svg"), (CANVAS_RE, "canvas")):
        for m in rx.finditer(text):
            tag = m.group(0)
            if ATTR_HIDDEN_RE.search(tag) and G.re.search(NAMING, tag, G.re.I):
                bad.append((kind, tag[:80]))
    return bad


def check_a4(ctx):
    """A4：每个**内联** `<svg>` / `<canvas>` 必须**可访问**：
    ① 非装饰 ⇒ 必须有可访问名（`aria-label` 或指向本页存在 id 的 `aria-labelledby`）；
    ② 装饰（`aria-hidden="true"`）⇒ ⛔ 不得同时又声明可访问名（冲突声明）：
       `aria-hidden` 与 `role="img" aria-label` 语义相反，同现会让不同 ATS 给出不同结果。

    ★ 为什么只认元素自带的三条通道，⛔ 不认祖先 `<figcaption>`：ATS 对 `<figure>` 命名支持不一致，
      「靠祖先命名」会得到一个「在自己机器上对、在别人机器上错」的结论。
    """
    bad = []
    total = 0
    decor = 0
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel, text in sorted(ctx.html.items()):
        for rx, kind in ((SVG_RE, "svg"), (CANVAS_RE, "canvas")):
            for m in rx.finditer(text):
                total += 1
                tag = m.group(0)
                if ATTR_HIDDEN_RE.search(tag):
                    decor += 1
                ok, why = _accessible(tag, text)
                if not ok:
                    bad.append((rel, "%s 不可访问" % kind, why))
        for kind, tag in _decorative_but_exposed(text):
            bad.append((rel, "%s 装饰声明与可访问名冲突" % kind, tag))
    if total == 0:
        return False, "空集守卫：发布面没有任何内联 svg/canvas ⇒ 判据恒真"
    ctx.notes.append("A4 口径（SH2 §4.2 + 姊妹站 gate_a11y 同族）：判据对象 = 页面里的**内联** "
                     "`<svg>` / `<canvas>`；断言 = ① 非装饰必须有可访问名（`aria-label` 或指向本页存在 id 的 "
                     "`aria-labelledby`）② 装饰必须显式 `aria-hidden=\"true\"` 且⛔ 不得同带可访问名。"
                     "⛔ 不认「祖先有 figcaption」这类间接命名 —— 那在不同 ATS 上行为不一致。")
    return (not bad), ("受检页面 %d 个：内联图形元素 %d 个（其中装饰 %d 个）；违例 %d 处 %s"
                       % (len(ctx.html), total, decor, len(bad), bad[:4]))


def check_a5(ctx):
    """A5：每页 `<html lang>` 非空（语言缺失会让读屏用错误发音规则念中文）。"""
    bad = []
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel, text in sorted(ctx.html.items()):
        m = G.re.search(r"<html\b([^>]*)>", text, G.re.I)
        lang = G.re.search(r'\blang\s*=\s*"([^"]*)"', m.group(1), G.re.I) if m else None
        if not m or not lang or not lang.group(1).strip():
            bad.append((rel, "<html lang> 缺失或为空", ""))
    return (not bad), ("受检页面 %d 个：`<html lang>` 非空；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


def check_a6(ctx):
    """A6：每页**至少 1 条** `rel="icon"` 声明（favicon 是浏览器标签/书签的识别面）。

    ★ 判据对象的边界（⛔ 不越界）：本判据只断言「**声明存在**」——
      声明的 URL 是否**无主机**、其 target 是否**在盘上存在**，属 P09（元数据类 rel 的无主机断言）
      与 `gate_seo_meta.py` 的 S7（图标可达）的对象。⛔ 不在这里重判一遍（那是三份真相）。
    """
    bad = []
    hits = 0
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel, text in sorted(ctx.html.items()):
        n = sum(1 for (lr, _h, _t) in G._link_tags(text) if "icon" in lr.split())
        hits += n
        if n < 1:
            bad.append((rel, 'rel="icon" 声明 0 条', ""))
    if hits == 0:
        return False, "空集守卫：全站没有任何 rel=icon 声明 ⇒ 判据恒真"
    return (not bad), ("受检页面 %d 个：`rel=\"icon\"` 声明 %d 条（每页 ≥1）；违例 %d 处 %s"
                       % (len(ctx.html), hits, len(bad), bad[:4]))


def check_a7(ctx):
    """A7：`a.skip` 必须是页面里**第一个可聚焦元素**（WCAG 2.4.1 绕过块的实现前提）。

    ★ 为什么这条值钱：skip link 只在**它是第一个 Tab 停点**时才起作用。若它前面还有别的
      可聚焦元素（本站的 rail / 页头导航都在 `<main>` 之前，一旦顺序改动就会踩到），
      键盘用户得先 Tab 过若干项才拿到「跳到正文」——那等于没有回绕导航的手段。
      而这条**没有任何其它判据会失败**（A1 只数它有几个）。
    """
    bad = []
    focusable = G.re.compile(r"<(a|button|input|select|textarea)\b[^>]*>", G.re.I)
    if not ctx.html:
        return False, "空集守卫：没有受检页面 ⇒ 判据恒真"
    for rel, text in sorted(ctx.html.items()):
        body = G.re.search(r"<body\b[^>]*>", text, G.re.I)
        if not body:
            bad.append((rel, "无 <body>", ""))
            continue
        rest = text[body.end():]
        first_f = focusable.search(rest)
        skip = SKIP_RE.search(rest)
        if not skip:
            bad.append((rel, "正文内无 a.skip（A1 已判，此处只作顺序前提）", ""))
            continue
        if first_f and first_f.start() < skip.start():
            bad.append((rel, "a.skip 之前还有可聚焦元素", first_f.group(0)[:60]))
    return (not bad), ("受检页面 %d 个：`a.skip` 均为正文内第一个可聚焦元素；违例 %d 处 %s"
                       % (len(ctx.html), len(bad), bad[:4]))


CHECKS = [
    ("A1", "跳转正文链接恰 1 且目标锚点存在", check_a1, None),
    ("A2", "每页 :focus-visible ≥1", check_a2, None),
    ("A3", "每页 <main> 恰 1", check_a3, None),
    ("A4", "内联 svg/canvas 可访问（命名或 aria-hidden，且无冲突声明）", check_a4, None),
    ("A5", "每页 <html lang> 非空", check_a5, None),
    ("A6", "每页 rel=icon 声明 ≥1（只断声明存在，可达性归 S7）", check_a6, None),
    ("A7", "a.skip 是正文内第一个可聚焦元素（WCAG 2.4.1 的实现前提）", check_a7, None),
]

# ---------------------------------------------------------------- 负例夹具
# ★ 每条夹具打在**它该打的那条子断言**上；⛔ 不得靠「改坏别的什么」顺带触发。


def _first(page_kind="node"):
    def f(ctx):
        pre = {"node": "11-node-pages", "group": "12-groups", "view": "14-views",
               "root": "index.html", "interactive": "13-interactive"}[page_kind]
        return G._first_html(ctx, pre if page_kind not in ("root", "interactive") else None)
    return f


def mut_a1(ctx):
    out = []
    k = _first("node")(ctx)
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, "</head>", '<a class="skip" href="#main">跳到正文</a></head>'))
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, "</head>", '<a class="skip" href="#nope">跳到正文</a></head>'))
    return out


def mut_a2(ctx):
    c = copy.deepcopy(ctx)
    k = _first("node")(ctx)
    return G._patch(c, k, ":focus-visible", ":focus-visible-x")


def mut_a3(ctx):
    """A3 的负例：再插一个 `<main>` ⇒ 2 个 ⇒ FAIL。

    ★ 锚点必须落在**开标签**上：`MAIN_RE` 匹配的是 `<main …>`，而初版夹具改的是 `</main>`
      ⇒ 判据看不到任何变化、负例不触发（本轮自检当场报出）。这正是「夹具必须打在它该打的那条断言上」。
    """
    c = copy.deepcopy(ctx)
    k = _first("node")(ctx)
    return G._patch(c, k, "</head>", "</head><main>")


def mut_a4(ctx):
    out = []
    k = _first("node")(ctx)
    # ① 非装饰图形抹掉可访问名（★ 锚点只命中**图件**的 `role="img" aria-label=…`）
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, 'role="img" aria-label="', 'data-x="'))
    # ② 装饰图形抹掉 aria-hidden —— 仅当盘上真有装饰图形时才有锚点；
    #    ⛔ 本站在 2026-10-16 的实测是**发布面无装饰图形** ⇒ 此夹具用 `_patch_strict` 会 fail-closed。
    #    改用「造一个装饰图形出来」：给某个已有图形同时加 aria-hidden 与可访问名 ⇒ 命中冲突声明断言。
    c = copy.deepcopy(ctx)
    out.append(G._patch(c, k, 'role="img" aria-label="',
                        'role="img" aria-hidden="true" aria-label="'))
    return out


def mut_a5(ctx):
    c = copy.deepcopy(ctx)
    k = _first("node")(ctx)
    return G._patch(c, k, '<html lang="zh-CN"', "<html")


def mut_a6(ctx):
    """A6 的负例：抹掉某一页的 `rel="icon"` 声明 ⇒ 该页 0 条 ⇒ FAIL。"""
    k = _first("node")(ctx)
    c = copy.deepcopy(ctx)
    c.html[k] = c.files[k] = G.re.sub(r'<link rel="icon"[^>]*>', "", c.html[k])
    return c


def mut_a7(ctx):
    """A7 的负例：在 `.skip` **之前**插一个可聚焦元素 ⇒ 它不再是第一个 Tab 停点 ⇒ FAIL。"""
    k = _first("node")(ctx)
    c = copy.deepcopy(ctx)
    return G._patch(c, k, '<a class="skip"',
                    '<a class="pre-focus" href="#x">x</a><a class="skip"')


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
    print("== 无障碍门控：判据 %s ==" % "–".join(c for c, _, _, _ in CHECKS))
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
    print("== 无障碍门控自检：逐条触发负例 ==")
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
        pos, pdetail = _run_fixture(fn, copy.deepcopy(base))
        muts = mut(copy.deepcopy(base))
        muts = muts if isinstance(muts, list) else [muts]
        fails = []
        for i, mctx in enumerate(muts):
            still, detail = _run_fixture(fn, mctx)
            if still:
                fails.append("负例#%d 未触发：%s" % (i + 1, str(detail)[:110]))
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
