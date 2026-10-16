#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_channel.py —— 验证通道**开工必跑**探针（复跑环境探测 + 产物非退化检查）。

为什么需要它（两条真实教训，见 `report.md §6.5.5` 与 `VERIFY-CONSTRAINT.md` 更正二）：
  ① 「环境能力不可用」这个结论**本身也要复核**：上一轮把「浏览器不可用」写成事实，
     真因却是一个被误诊的根因（`CapEff=0` + `NoNewPrivs=1` 使 file-capability 程序
     `snap-confine` 取不到 `cap_dac_override`，失败在**启动层**），而**可用的非 snap 内核
     一直在盘上**（`~/.cache/ms-playwright/chromium-1243/`）。⇒ 能力可用性必须**每轮复跑探测**，
     ⛔ 不得沿用上一轮的散文结论。
  ② **假绿通道**：`agent-browser 0.34.0` 回显 `✓ Screenshot saved` 却产出**纯白 1 色空图**。
     ⇒ 任何「验证工具」的成功回显都必须用**产物非退化**判据复核（尺寸 + 唯一色数 + 亮度区间 + 字节）。

本件做三件事：
  A. 复跑**通道探测**（非 snap 内核 / playwright python 驱动 / node 驱动）⇒ 逐条落 JSON。
  B. 真实渲染 N 页（默认视口 1440×900 + 窄视口 768×900），对每张 PNG 做**像素读数**：
     尺寸 / 唯一色数 / 亮度区间 / 字节 / sha256。★ 纯 Python PNG 解码，⛔ 不依赖 PIL。
  C. 渲染期**实测**（供阈值标定，⛔ 不是判据）：
     · 横表单元格的真实渲染宽度 vs 静态模型估算（求模型/实测比，用于横表宽度预算标定）；
     · 窄视口下交互图画布容器的真实宽度（校核 P37 的 `zoom=1` 只在 ≥900px 成立这一局限）。

产物：`16-checkpoint/_probe/channel.json`（+ 同目录 PNG）。**门控 P38 消费它**：
       P38 不采信本件的自报，而是**独立复算**（内核路径是否存在 / PNG 是否非退化 / sha256 是否一致）。

用法：python3 _probe_channel.py [--quick] [--keep]
退出码：0 = 全部探测与读数通过；1 = 任一通道不可用或任一产物退化（**必须停下并如实登记**）。
⛔ 本件不写任何站点产物、⛔ 不改任何判据。
"""
import argparse
import hashlib
import http.server
import json
import os
import socketserver
import struct
import sys
import threading
import time
import zlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT_DIR = os.path.join(HERE, "_probe")
MANIFEST = os.path.join(OUT_DIR, "channel.json")

SCHEMA = "pekg/channel-probe/1"

# 待渲染对象：(相对站点根, 标签, 宽, 高, 是否深色)
TARGETS_FULL = [
    ("index.html", "root", 1440, 900, False),
    ("12-groups/g00.html", "group", 1440, 900, False),
    ("11-node-pages/pe-f-01.html", "node", 1440, 900, False),
    ("14-views/02-frontier.html", "view", 1440, 900, False),
    ("13-interactive/index.html", "interactive", 1440, 900, False),
    ("index.html", "root-narrow", 768, 900, False),
    ("13-interactive/index.html", "interactive-narrow", 768, 900, False),
    ("index.html", "root-dark", 1440, 900, True),
]
TARGETS_QUICK = [
    ("index.html", "root", 1440, 900, False),
    ("13-interactive/index.html", "interactive", 1440, 900, False),
]
# 全站横向溢出普查：视口 1440×900（所有页）；只测不存 PNG
SURVEY_DIRS = ("", "11-node-pages", "12-groups", "13-interactive", "14-views")


def survey_pages():
    out = []
    for sub in SURVEY_DIRS:
        d = os.path.join(SITE_ROOT, sub) if sub else SITE_ROOT
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".html"):
                out.append((sub + "/" + fn) if sub else fn)
    return out


# ---------------------------------------------------------------- 纯 Python PNG 读数
def png_read(path):
    """读 PNG 的尺寸 / 唯一色数 / 亮度区间（⛔ 不依赖 PIL：PIL 缺失时判据不能失效）。

    只支持 8-bit 真彩（color type 2/6）与非隔行扫描——本项目渲染产物即此形态；
    遇到不支持的形态**抛错**（fail-closed），⛔ 不静默返回 0 色。
    """
    raw = open(path, "rb").read()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG 文件：%s" % path)
    pos, idat, w, h, bd, ct, interlace = 8, b"", 0, 0, 0, 0, 0
    while pos + 8 <= len(raw):
        (ln,) = struct.unpack(">I", raw[pos:pos + 4])
        typ = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if bd != 8:
        raise ValueError("只支持 8-bit 位深（实际 %d）：%s" % (bd, path))
    if ct not in (2, 6):
        raise ValueError("只支持真彩 color type 2/6（实际 %d）：%s" % (ct, path))
    if interlace != 0:
        raise ValueError("不支持隔行扫描：%s" % path)
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


def degenerate(rec, min_colors=64):
    """产物非退化判定（假绿通道的判据核心）。返回 [] = 非退化。"""
    why = []
    if rec["width"] < 320 or rec["height"] < 240:
        why.append("尺寸退化 %dx%d" % (rec["width"], rec["height"]))
    if rec["uniq_colors"] < min_colors:
        why.append("唯一色 %d < %d（疑似纯色空图）" % (rec["uniq_colors"], min_colors))
    if rec["lum_max"] - rec["lum_min"] < 32:
        why.append("亮度区间 %.1f 过窄（疑似空图）" % (rec["lum_max"] - rec["lum_min"]))
    if rec["bytes"] < 4096:
        why.append("字节 %d 过小（疑似空图）" % rec["bytes"])
    return why


# ---------------------------------------------------------------- A. 通道探测
def probe_channel():
    home = os.path.expanduser("~")
    chrome_cands = []
    base = os.path.join(home, ".cache", "ms-playwright")
    if os.path.isdir(base):
        for d in sorted(os.listdir(base)):
            if d.startswith("chromium"):
                for sub in ("chrome-linux64/chrome", "chrome-linux/chrome"):
                    p = os.path.join(base, d, sub)
                    if os.path.isfile(p):
                        chrome_cands.append(p)
    facts = {
        "non_snap_chromium": {
            "found": bool(chrome_cands),
            "path": chrome_cands[0] if chrome_cands else None,
            "candidates": chrome_cands,
        },
        "snap_chromium": {
            "found": os.path.isfile("/snap/bin/chromium"),
            "path": "/snap/bin/chromium" if os.path.isfile("/snap/bin/chromium") else None,
        },
    }
    # playwright python 驱动
    drv = None
    try:
        import importlib.util as _iu
        spec = _iu.find_spec("playwright")
        drv = spec.origin if spec else None
    except Exception:  # noqa: BLE001
        drv = None
    facts["playwright_python"] = {"found": bool(drv), "path": drv}
    # node 驱动（仅供参考：本通道不依赖它）
    node_drv = None
    for root in (os.path.join(home, ".npm-global", "lib", "node_modules"),
                 os.path.join(home, ".cache", "ms-playwright-go")):
        if os.path.isdir(root):
            node_drv = root
            break
    # ★ 命名更正（2026-10-16，台账 T-3）：本字段**不是** PATH 可达性探测 ——
    #   它只探上面两个**特定目录**；第 5 轮实测它报 `found=false`，而同一台机上 `node` 在盘
    #   且跑通了 37 例开关自检 ⇒ 该布尔**不得**读作「node 不可用」。
    #   判断 node 可达性**只认**：
    #     PATH="$HOME/.nvm/versions/node/v24.19.0/bin:$HOME/.local/bin:$PATH" node -v
    #   保留键名（schema `pekg/channel-probe/1` 兼容）；本字段**无判据复算**，仅供参考。
    facts["node_driver_hint"] = {"found": bool(node_drv), "path": node_drv,
                                 "probe_scope": "only ~/.npm-global & ~/.cache/ms-playwright-go",
                                 "not_a_path_check": True}
    # capability（真因复核：snap 通道结构性不可用的判据面）
    caps = {}
    try:
        for line in open("/proc/self/status", encoding="utf-8"):
            k = line.split(":")[0]
            if k in ("CapEff", "CapPrm", "CapBnd", "NoNewPrivs"):
                caps[k] = line.split(":", 1)[1].strip()
    except OSError:
        pass
    facts["caps"] = caps
    return facts


# ---------------------------------------------------------------- HTTP 服务
class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # noqa: A003
        pass

    def handle_one_request(self):
        """吞掉连接被浏览器提前关闭时的 BrokenPipe（⛔ 不是错误，别让噪声掩盖真错）。"""
        try:
            http.server.SimpleHTTPRequestHandler.handle_one_request(self)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True


def serve(root):
    handler = lambda *a, **k: _Quiet(*a, directory=root, **k)  # noqa: E731
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, httpd.server_address[1]


# ---------------------------------------------------------------- B/C. 渲染 + 实测
def render_all(targets):
    from playwright.sync_api import sync_playwright

    os.makedirs(OUT_DIR, exist_ok=True)
    httpd, port = serve(SITE_ROOT)
    out = {"renders": [], "measured": {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--force-device-scale-factor=1"])
            for rel, label, w, h, dark in targets:
                pg = browser.new_page(viewport={"width": w, "height": h},
                                      device_scale_factor=1,
                                      color_scheme="dark" if dark else "light",
                                      reduced_motion="reduce")
                pg.add_init_script("try{localStorage.clear()}catch(e){}")
                pg.goto("http://127.0.0.1:%d/%s" % (port, rel), wait_until="networkidle")
                pg.add_style_tag(content="*,*::before,*::after{animation:none!important;"
                                         "transition:none!important}")
                try:
                    pg.evaluate("document.fonts.ready")
                except Exception:  # noqa: BLE001
                    pass
                pg.wait_for_timeout(500)
                name = "%s-%dx%d%s.png" % (label, w, h, "-dark" if dark else "")
                path = os.path.join(OUT_DIR, name)
                pg.screenshot(path=path, full_page=False)
                rec = png_read(path)
                rec.update({"rel": rel, "label": label, "viewport": [w, h], "dark": dark,
                            "png": os.path.relpath(path, HERE)})
                rec["degenerate"] = degenerate(rec)
                out["renders"].append(rec)
                # ---- C. 渲染期实测 ----
                if label in ("root", "group", "node", "view"):
                    out["measured"]["overflow_" + label] = pg.evaluate(MEASURE_OVERFLOW_JS)
                    out["measured"].setdefault("tables", {})[label] = pg.evaluate(MEASURE_TABLE_JS)
                if label == "root":
                    out["measured"]["table_cells"] = pg.evaluate(MEASURE_TABLE_JS)
                    out["measured"]["model_compare"] = compare_table_model(
                        out["measured"]["table_cells"])
                if label == "interactive":
                    out["measured"]["canvas_1440"] = pg.evaluate(MEASURE_CY_JS)
                if label == "interactive-narrow":
                    out["measured"]["canvas_768"] = pg.evaluate(MEASURE_CY_JS)
                pg.close()
            # ---- 全站横向溢出普查（★ 这是「门控报不出来的面」的直接量）----
            survey = {}
            for rel in survey_pages():
                pg = browser.new_page(viewport={"width": 1440, "height": 900},
                                      device_scale_factor=1, color_scheme="light",
                                      reduced_motion="reduce")
                pg.add_init_script("try{localStorage.clear()}catch(e){}")
                pg.goto("http://127.0.0.1:%d/%s" % (port, rel), wait_until="networkidle")
                pg.add_style_tag(content="*,*::before,*::after{animation:none!important;"
                                         "transition:none!important}")
                pg.wait_for_timeout(200)
                survey[rel] = pg.evaluate(MEASURE_OVERFLOW_JS)
                pg.close()
            out["measured"]["overflow_survey"] = survey
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    return out


MEASURE_TABLE_JS = """() => {
  const out = [];
  document.querySelectorAll('table').forEach((t, ti) => {
    const cells = [];
    let maxLines = 0, worst = '';
    let maxContent = 0;
    t.querySelectorAll('tr').forEach((r) => {
      r.querySelectorAll('th,td').forEach((c, ci) => {
        const rect = c.getBoundingClientRect();
        const cs = getComputedStyle(c);
        const lh = parseFloat(cs.lineHeight);
        const pad = (parseFloat(cs.paddingLeft) || 0) + (parseFloat(cs.paddingRight) || 0);
        const content = rect.width - pad;
        if (content > maxContent) maxContent = content;
        const inner = rect.height - (parseFloat(cs.paddingTop) || 0)
                                   - (parseFloat(cs.paddingBottom) || 0);
        const lines = (lh && lh > 0) ? Math.max(1, Math.round(inner / lh)) : null;
        const text = (c.textContent || '').trim();
        if (lines !== null && lines > maxLines) { maxLines = lines; worst = text.slice(0, 44); }
        cells.push({row: cells.length, col: ci, w: Math.round(rect.width),
                    contentW: Math.round(content), h: Math.round(rect.height),
                    lh: lh, lines: lines, text: text.slice(0, 44)});
      });
    });
    const cols = [];
    t.querySelectorAll('tr').forEach((r) => {
      r.querySelectorAll('th,td').forEach((c, ci) => {
        const w = c.getBoundingClientRect().width;
        if (cols[ci] === undefined || w > cols[ci]) cols[ci] = w;
      });
    });
    let over = 0, overAt = '';
    const chain = [t];
    let p = t.parentElement;
    for (let i = 0; i < 3 && p; i++, p = p.parentElement) chain.push(p);
    chain.forEach((e) => {
      const d = e.scrollWidth - e.clientWidth;
      if (d > over) { over = d; overAt = e.tagName + '.' + (e.className || ''); }
    });
    out.push({index: ti, tableW: Math.round(t.getBoundingClientRect().width),
              cols: cols.map((x) => Math.round(x || 0)),
              maxContentW: Math.round(maxContent),
              maxLines: maxLines, worstCell: worst,
              overflowPx: over, overflowAt: overAt, cells: cells});
  });
  return out;
}"""

MEASURE_CY_JS = """() => {
  const el = document.querySelector('#cy') || document.querySelector('.cy');
  const host = el ? el.parentElement : null;
  return {
    cyW: el ? Math.round(el.getBoundingClientRect().width) : null,
    cyH: el ? Math.round(el.getBoundingClientRect().height) : null,
    hostW: host ? Math.round(host.getBoundingClientRect().width) : null,
    docScrollW: document.documentElement.scrollWidth,
    innerW: window.innerWidth,
    zoom: (window.__cyZoom !== undefined) ? window.__cyZoom : null
  };
}"""

MEASURE_OVERFLOW_JS = """() => {
  const bad = [];
  document.querySelectorAll('table, pre, .cy, figure, .cmp-table').forEach((e) => {
    const cs = getComputedStyle(e);
    // ⛔ 只算**可见**元素：折叠的 <details> 内元素不该报溢出（否则是假阳）
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    if (e.getClientRects().length === 0) return;
    if (e.scrollWidth > e.clientWidth + 2) {
      bad.push({tag: e.tagName, cls: String(e.className || '').slice(0, 40),
                scrollW: e.scrollWidth, clientW: e.clientWidth,
                overflowPx: e.scrollWidth - e.clientWidth,
                fontSize: cs.fontSize, whiteSpace: cs.whiteSpace,
                textLen: (e.textContent || '').length});
    }
  });
  return {docScrollW: document.documentElement.scrollWidth,
          innerW: window.innerWidth,
          overflowing: bad};
}"""

CJK_RE = None


def compare_table_model(cells):
    """渲染期实测 vs 静态模型估算（★ 标定用：求出模型/实测的比值，⛔ 不是判据）。

    模型 = (汉字数 × 1.0em + 其他字符数 × 0.53em) × 16px（em 系数取自 `_probe_metrics.py` A 段 PIL 实测）。
    """
    global CJK_RE
    if CJK_RE is None:
        import re
        CJK_RE = re.compile(r"[\u4e00-\u9fff]")
    rows = []
    for t in cells:
        for c in t["cells"]:
            txt = c["text"]
            n_cjk = len(CJK_RE.findall(txt))
            model = (n_cjk * 1.0 + max(0, len(txt) - n_cjk) * 0.53) * 16.0
            rows.append({"table": t["index"], "col": c["col"], "rendered": c["w"],
                         "model": round(model, 1),
                         "ratio": round(c["w"] / model, 3) if model > 0 else None})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="只渲染 2 页（冒烟）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    print("== _probe_channel.py：验证通道探测 + 产物非退化读数 ==")
    facts = probe_channel()
    print("\n-- A. 通道探测 --")
    for k, v in facts.items():
        print("   %-22s %s" % (k, json.dumps(v, ensure_ascii=False)))
    targets = TARGETS_QUICK if a.quick else TARGETS_FULL
    print("\n-- B/C. 真实渲染（%d 页）--" % len(targets))
    res = render_all(targets)
    ok = True
    for r in res["renders"]:
        flag = "PASS" if not r["degenerate"] else "FAIL"
        if r["degenerate"]:
            ok = False
        print("   [%s] %-26s %4dx%-4d 唯一色 %6d 亮度 %5.1f–%5.1f %8d B  %s"
              % (flag, r["label"], r["width"], r["height"], r["uniq_colors"],
                 r["lum_min"], r["lum_max"], r["bytes"], r["sha256"][:16]))
        if r["degenerate"]:
            print("          ⇒ %s" % "；".join(r["degenerate"]))
    print("\n-- C. 渲染期实测（标定用，⛔ 非判据）--")
    mm = res["measured"]
    if mm.get("tables"):
        print("   横表逐页直接量（横向滚动 = scrollWidth − clientWidth；行数 = 单元格高 / 行高）：")
        for label, tabs in sorted(mm["tables"].items()):
            for t in tabs:
                print("     [%-5s] 表#%d 总宽 %dpx 逐列 %s 最大单元格内容宽 %dpx "
                      "最多 %s 行 横向溢出 %dpx%s"
                      % (label, t["index"], t["tableW"], t["cols"], t["maxContentW"],
                         t["maxLines"] if t["maxLines"] else "n/a", t["overflowPx"],
                         (" @ " + t["overflowAt"]) if t["overflowPx"] else ""))
                print("              最坏单元格：%s" % t["worstCell"])
    for k in ("canvas_1440", "canvas_768", "overflow_root", "overflow_group",
              "overflow_node", "overflow_view"):
        if mm.get(k):
            print("   %-14s %s" % (k, json.dumps(mm[k], ensure_ascii=False)[:400]))
    surv = mm.get("overflow_survey") or {}
    print("\n-- D. 全站横向溢出普查（视口 1440×900；%d 页）--" % len(surv))
    n_over = 0
    for rel in sorted(surv):
        bad = surv[rel].get("overflowing") or []
        doc = surv[rel]["docScrollW"] - surv[rel]["innerW"]
        if doc > 0:
            n_over += 1
            print("   [FAIL] %-34s 文档横向溢出 %dpx" % (rel, doc))
        for b in bad:
            n_over += 1
            print("   [FAIL] %-34s <%s.%s> 溢出 %dpx（scrollW %d / clientW %d；"
                  "font-size %s / white-space %s / 文本 %d 字）"
                  % (rel, b["tag"], b["cls"], b["overflowPx"], b["scrollW"],
                     b["clientW"], b["fontSize"], b["whiteSpace"], b["textLen"]))
    if n_over == 0:
        print("   [PASS] 全站 %d 页：文档级与元素级横向溢出均为 0" % len(surv))
    else:
        ok = False
    res["measured"]["overflow_total"] = n_over
    doc = {"schema": SCHEMA, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "site_root": SITE_ROOT, "channel_facts": facts,
           "renders": res["renders"], "measured": res["measured"],
           "elapsed_s": round(time.time() - t0, 1),
           "verdict": "PASS" if ok else "FAIL"}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("\n== 结论：%s ==（用时 %.1fs；manifest → %s）"
          % ("PASS" if ok else "FAIL", time.time() - t0,
             os.path.relpath(MANIFEST, SITE_ROOT)))
    if not ok:
        print("   ⛔ 判定 FAIL 的两种情形都要**停下并如实登记**："
              "① 产物退化（尺寸/唯一色/亮度/字节）——该通道是假绿通道，⛔ 不得当证据来源；"
              "② 横向溢出（文档级或元素级）——这是**真实渲染实测到的产物缺陷**，"
              "⛔ 不得用「门控全绿」掩盖。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
