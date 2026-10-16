#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_metrics.py —— 阈值**推导**用的一次性取证脚本（⛔ 不是判据、⛔ 不落任何产物）。

为什么需要它：`criterion-design-validation` 的纪律是「**阈值不得由规模直觉推导**」。
本轮要新增/收紧的判据（长文可扫性、横表列宽预算、窄视口 zoom）都必须先在**真实产物**
上取数，再反解阈值。本件只打印读数，⛔ 不做任何裁决。

实测四项：
  A. 文字度量标定：本机 Noto CJK 在 16px 下「一个汉字 / 一个小写拉丁字母 / 一个数字」
     的真实 advance（PIL 逐字测量）⇒ 供「横表列宽预算」把 em 系数换成**实测值**。
  B. 散文最长无标点游程（caliber 口径）——节点页 / 组页 / 视图页的**渲染后**文本，
     供「长文可扫性」判据定阈值。
  C. 横表列宽预算：全站每张 `<table>` 的逐列估算宽度 + 是否超内容列宽 804px
     （★ 直接量，用于替换 P35 ⑫ 的**代理判据**）。
  D. 交互图窄视口 zoom：`<1180px` 档下画布可用宽随视口缩小 ⇒ 复算 zoom（本轮局限 L4）。

用法：python3 _probe_metrics.py
退出码：恒 0（本件是取证，不是判据）。
"""
import importlib.util
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.normpath(os.path.join(HERE, ".."))


def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-'.]*")
TAG_STRIP_RE = re.compile(r"<[^>]+>")


def caliber(s):
    return len(CJK.findall(s or "")) + len(LATIN_WORD.findall(s or ""))


def plain(h):
    return re.sub(r"\s+", " ", TAG_STRIP_RE.sub("", h or "")).strip()


# ---------------------------------------------------------------- A. 字体度量
def probe_metrics():
    print("== A. 文字度量标定（PIL 逐字 advance，字号 16px）==")
    try:
        from PIL import ImageFont
    except Exception as exc:  # noqa: BLE001
        print("   PIL 不可用：%s" % exc)
        return None
    cands = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    out = {}
    for path in cands:
        if not os.path.isfile(path):
            continue
        try:
            f = ImageFont.truetype(path, 16)
        except Exception as exc:  # noqa: BLE001
            print("   %s 载入失败：%s" % (path, exc))
            continue
        def adv(ch):
            try:
                return f.getlength(ch)
            except Exception:  # noqa: BLE001
                return f.getsize(ch)[0]
        cjk = adv("新")
        lat = [adv(c) for c in "abcdefghijklmnopqrstuvwxyz"]
        dig = [adv(c) for c in "0123456789"]
        out[path] = {"cjk_px": cjk, "latin_mean": sum(lat) / len(lat),
                     "digit_mean": sum(dig) / len(dig)}
        print("   %s" % path)
        print("     汉字 '新' advance = %.3fpx (%.4f em @16px)" % (cjk, cjk / 16.0))
        print("     拉丁 a-z 平均 advance = %.3fpx (%.4f em)"
              % (out[path]["latin_mean"], out[path]["latin_mean"] / 16.0))
        print("     数字 0-9 平均 advance = %.3fpx (%.4f em)"
              % (out[path]["digit_mean"], out[path]["digit_mean"] / 16.0))
    return out


# ---------------------------------------------------------------- B/C. 产物侧读数
def load_pages():
    pages = {}
    for sub in ("11-node-pages", "12-groups", "14-views", ""):
        d = os.path.join(SITE_ROOT, sub) if sub else SITE_ROOT
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".html"):
                continue
            rel = (sub + "/" + fn) if sub else fn
            pages[rel] = open(os.path.join(d, fn), encoding="utf-8").read()
    return pages


SECTION_RE = re.compile(r'<h2 id="(sec-[a-z-]+)"')
CLAIM_RE = re.compile(r'<p class="claim">(.*?)</p>', re.S)
POINT_RE = re.compile(r"<li>(.*?)</li>", re.S)
TABLE_RE = re.compile(r"<table\b.*?</table>", re.S)
ROW_RE = re.compile(r"<tr\b.*?</tr>", re.S)
CELL_RE = re.compile(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", re.S)


def longest_run(text):
    """最长「无句末标点」连续游程（caliber 口径）。"""
    parts = re.split(r"[。！？!?；;]", text)
    best = ("", 0)
    for p in parts:
        c = caliber(p)
        if c > best[1]:
            best = (p.strip(), c)
    return best


def probe_prose(pages):
    print("\n== B. 散文最长无标点游程（caliber 口径；渲染后文本）==")
    rows = []
    for rel, text in sorted(pages.items()):
        blocks = CLAIM_RE.findall(text)
        units = []
        for b in blocks:
            units.append(("claim", plain(b)))
        for m in re.finditer(r'<ul class="points">(.*?)</ul>', text, re.S):
            for li in POINT_RE.findall(m.group(1)):
                units.append(("point", plain(li)))
        for sid in SECTION_RE.findall(text):
            pass
        if not units:
            continue
        worst = max(units, key=lambda u: caliber(u[1]))
        rows.append((rel, len(units), worst[0], caliber(worst[1]), worst[1][:46]))
    rows.sort(key=lambda r: -r[3])
    print("   %-34s %5s %6s %7s  %s" % ("页", "单元", "类型", "最长游程", "样本"))
    for r in rows:
        print("   %-34s %5d %6s %7d  %s" % r)
    if rows:
        print("   ⇒ 全站最长 = %d caliber（%s）" % (rows[0][3], rows[0][0]))
        vals = sorted(r[3] for r in rows)
        print("   ⇒ 分位：min %d / median %d / p90 %d / max %d"
              % (vals[0], vals[len(vals) // 2], vals[int(len(vals) * 0.9)], vals[-1]))
    return rows


def cell_text(h):
    return plain(h)


def probe_tables(pages):
    print("\n== C. 横表列宽预算（直接量；em 系数取 A 的实测值）==")
    CJK_EM = 1.0
    LAT_EM = 0.52          # 由 A 的实测值反填（见输出）
    FS_PX = 16.0
    BUDGET = 804.0
    for rel, text in sorted(pages.items()):
        for i, tb in enumerate(TABLE_RE.findall(text)):
            rows = ROW_RE.findall(tb)
            ncols = max([len(CELL_RE.findall(r)) for r in rows] or [0])
            if ncols == 0:
                continue
            widths = []
            for c in range(ncols):
                w = 0.0
                for r in rows:
                    cells = CELL_RE.findall(r)
                    if c >= len(cells):
                        continue
                    t = cell_text(cells[c])
                    w = max(w, (len(CJK.findall(t)) * CJK_EM
                                + (len(t) - len(CJK.findall(t))) * LAT_EM) * FS_PX)
                widths.append(w)
            total = sum(widths) + (ncols + 1) * 16.0     # 单元格内边距按 16px/边
            flag = "OK " if total <= BUDGET else "OVER"
            print("   [%s] %-34s 表#%d  %d 列  逐列 %s  合计 %.0fpx (预算 %.0f)"
                  % (flag, rel, i, ncols, ["%.0f" % w for w in widths], total, BUDGET))
    print("   ★ em 系数来源：A 段 PIL 实测（汉字 1.0em / 拉丁均值见上）；"
          "⛔ 不是凭直觉取的 0.55。")


def probe_zoom():
    print("\n== D. 交互图窄视口 zoom（画布可用宽随视口变化）==")
    rel = "13-interactive/index.html"
    p = os.path.join(SITE_ROOT, rel)
    if not os.path.isfile(p):
        print("   缺 %s" % rel)
        return
    text = open(p, encoding="utf-8").read()
    m = re.search(r"<script[^>]*id=\"cy-data\"[^>]*>(.*?)</script>", text, re.S)
    if not m:
        m = re.search(r'id="cy-data"[^>]*>(.*?)</script>', text, re.S)
    if not m:
        print("   找不到 cy-data")
        return
    import json
    data = json.loads(m.group(1).replace("<\\/", "</"))
    lay = data.get("layout") or {}
    uw, uh = float(lay["usableW"]), float(lay["usableH"])
    cw, ch, pad = float(lay["canvasW"]), float(lay["canvasH"]), float(lay["pad"])
    groups = data["groups"]
    els = data.get("edgeLabels") or []
    boxes = []
    for g in groups:
        x, y, w, h = g["pos"]["x"], g["pos"]["y"], g["w"], g["h"]
        boxes.append((x, y, x + w, y + h))
    for e in els:
        boxes.append((e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"]))
    bw = max(b[2] for b in boxes) - min(b[0] for b in boxes)
    bh = max(b[3] for b in boxes) - min(b[1] for b in boxes)
    print("   内容包围盒 %.1f x %.1f；声明画布 %.0f x %.0f（内边距 %.0f）⇒ 可用 %.0f x %.0f"
          % (bw, bh, cw, ch, pad, uw, uh))
    print("   视口宽 → 内容列宽 → 画布可用宽 → zoom：")
    for vw in (1440, 1280, 1180, 1024, 900, 768, 640):
        col = 1120.0 - 252.0 - 2 * 32.0 if vw >= 1180 else vw - 2 * 32.0
        col = min(col, 1120.0)
        avail = col - 2 * pad
        z = min(1.0, avail / bw, uh / bh) if bw > 0 and bh > 0 else 0.0
        print("     %5d → %7.1f → %8.1f → %.4f%s"
              % (vw, col, avail, z, "   ← < 1" if z < 1.0 - 1e-9 else ""))


def main():
    print("_probe_metrics.py —— 阈值推导取证（⛔ 非判据）")
    print("站点根：%s\n" % SITE_ROOT)
    probe_metrics()
    pages = load_pages()
    print("\n   受检页面 %d 个" % len(pages))
    probe_prose(pages)
    probe_tables(pages)
    probe_zoom()
    return 0


if __name__ == "__main__":
    sys.exit(main())
