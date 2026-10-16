#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_thresholds.py —— B-2 **阈值重导**的一次性取证脚本（⛔ 不是判据、⛔ 不落任何产物）。

## 为什么需要它
`CONTINUE-PROMPT-D4.md` §B-2 要求：`why` 上限与 `intro` 下限**按真实渲染重导**，⛔ 不得再凭直觉给数。
`_probe_metrics.py` 给的是**静态模型**读数（不折行、PIL 逐字量宽），按 `report.md §7.2` 的交叉印证，
静态模型会把 4 张真实溢出为 0 的表判成 OVER ⇒ **静态模型不能当判据**。本件改用**真实渲染**
（非 snap Chrome for Testing + playwright，与 `_render.py` / `_probe_channel.py` 同一通道）。

## 它量什么
在 1440×900（一屏可读量的口径）下，对**已有节点页**逐页量：
  A. 内容列宽与正文行高（真实字体 + 真实版式）；
  B. `#sec-why` / `#sec-intro` 的**正文块**（`.claim` + `.points`，⛔ 不含 `.boundary`）的
     渲染行数、总高、每行 caliber —— 由此得 **px/caliber**；
  C. 由 B 反解**一屏可读量** `N_screen = 视口高 / (px/caliber)`（caliber 口径）。

## ⛔ 它**不**声称什么
* **上限**：只影响版式首屏，与正确性无因果关联 ⇒ 按 `SCHEMA.md` §3 的判据分档原则**只能作报告项**
  （`CRITERIA-CHANGE-P05.md` §6 的判别句：改成符合它不会改善内容）。
* **`intro` 下限**：渲染只能给出「一屏容量」这一**上界**；下界的因果在**内容侧**（机制叙述需要
  展开空间），⛔ 渲染**不能**导出它。本件如实打印这一点，⛔ 不硬凑一个数字。

用法：`python3 _probe_thresholds.py`（退出码恒 0：本件是取证，不是判据）
"""
import http.server
import importlib.util
import json
import os
import re
import socketserver
import sys
import threading

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.normpath(os.path.join(HERE, ".."))
DAG = os.path.join(SITE_ROOT, "10-dag-data", "dag.json")
CHROME = os.path.expanduser("~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome")

CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-'.]*")
VIEWPORT_H = 900          # 一屏可读量的口径（与 _probe_channel 的 1440×900 同源）
VIEWPORT_W = 1440

# 已有节点页（= 当前 complete 节点）
# ★ 2026-10-16（T-1 修）：原为**硬编码 3 页**（只有 3 个节点页时的快照）—— 第 5 轮末已 8 页、
#   第 6 轮波次 2 后 13 页 ⇒ 硬编码会让「一屏可读量」的取样**一直**是 3/N
#   （正是「有保质期的读数被固化进设备」这一族缺陷）。改为**扫描目录**：
#   读得到几页就量几页；一页都读不到 ⇒ 显式报错（fail-closed，⛔ 不静默跑空集）。
def _node_pages():
    d = os.path.join(SITE_ROOT, "11-node-pages")
    rels = sorted("11-node-pages/" + fn for fn in os.listdir(d) if fn.endswith(".html"))
    if not rels:
        raise SystemExit("[FAIL] %s 下没有节点页 ⇒ 本件无对象（⛔ 不静默跑空集）" % d)
    return tuple(rels)


PAGES = _node_pages()


def caliber(s):
    """唯一口径（SCHEMA §3）：汉字数 + 拉丁词数。"""
    return len(CJK.findall(s or "")) + len(LATIN_WORD.findall(s or ""))


# ---------------------------------------------------------------- 页内实测
MEASURE_JS = r"""
() => {
  // ★ 注意：区块 id 挂在 **`<h2 id="sec-…">`** 上（见 gen-common.section），⛔ 不是挂在 <section> 容器上
  //   ⇒ 必须从 h2 出发取**后续兄弟节点**直到下一个 h2，才能拿到该区块的正文块。
  //   （首版写成 `document.getElementById('sec-why').querySelector('.claim')`，实测恒为空集——
  //    这正是「判据/探测的作用域必须与对象对齐」的同型坑。）
  const prose = (id) => {
    const h = document.getElementById(id);
    if (!h) return null;
    const els = [];
    for (let n = h.nextElementSibling; n && n.tagName !== 'H2'; n = n.nextElementSibling) els.push(n);
    return els;
  };
  const out = {};
  for (const sid of ['sec-why', 'sec-intro']) {
    const els = prose(sid);
    let lines = 0, h = 0, w = 0, lh = null, boundaryH = 0, nBlk = 0;
    if (els) {
      for (const el of els) {
        if (el.classList.contains('boundary')) { boundaryH = el.getBoundingClientRect().height; continue; }
        const rects = [];
        if (el.classList.contains('claim')) { rects.push(el.getBoundingClientRect()); }
        else if (el.classList.contains('points')) {
          for (const li of el.querySelectorAll(':scope > li')) rects.push(li.getBoundingClientRect());
        } else { continue; }
        for (const r of rects) {
          h += r.height; w = Math.max(w, r.width);
          if (lh === null) lh = parseFloat(getComputedStyle(el).lineHeight);
          if (lh) lines += Math.round(r.height / lh);
        }
        nBlk += 1;
      }
    }
    out[sid] = {lines, lineHeight: lh, blockH: h, blockW: w, boundaryH, blocks: nBlk,
                sectionH: els ? els.reduce((a, e) => a + e.getBoundingClientRect().height, 0) : 0};
  }
  const main = document.querySelector('main') || document.body;
  const cs = getComputedStyle(main);
  const col = document.querySelector('.claim') || document.querySelector('.points');
  out.main = {contentW: main.getBoundingClientRect().width,
              columnW: col ? col.getBoundingClientRect().width : null,
              fontSize: cs.fontSize, lineHeight: cs.lineHeight};
  out.docH = document.documentElement.scrollHeight;
  return out;
}
"""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # noqa: A003
        pass

    def handle_one_request(self):
        try:
            http.server.SimpleHTTPRequestHandler.handle_one_request(self)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True


def serve(root):
    handler = lambda *a, **k: _Quiet(*a, directory=root, **k)  # noqa: E731
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def main():
    from playwright.sync_api import sync_playwright

    doc = json.load(open(DAG, encoding="utf-8"))
    by_slug = {n["id"].lower(): n for n in doc["nodes"]}
    if not os.path.exists(CHROME):
        print("== 结论：SKIP ==（非 snap 内核不在盘：%s）—— ⛔ 本件不做任何推算" % CHROME)
        return 0

    httpd, port = serve(SITE_ROOT)
    rows = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME,
                                         args=["--force-device-scale-factor=1"])
            for rel in PAGES:
                pg = browser.new_page(viewport={"width": VIEWPORT_W, "height": VIEWPORT_H},
                                      device_scale_factor=1, color_scheme="light",
                                      reduced_motion="reduce")
                pg.add_init_script("try{localStorage.clear()}catch(e){}")
                pg.goto("http://127.0.0.1:%d/%s" % (port, rel), wait_until="networkidle")
                pg.add_style_tag(content="*,*::before,*::after{animation:none!important;"
                                         "transition:none!important}")
                try:
                    pg.evaluate("document.fonts.ready")
                except Exception:  # noqa: BLE001
                    pass
                pg.wait_for_timeout(400)
                m = pg.evaluate(MEASURE_JS)
                slug = os.path.basename(rel).replace(".html", "")
                node = by_slug.get(slug, {})
                rows.append({"rel": rel, "id": node.get("id"), "m": m,
                             "why_cal": caliber(node.get("why", "")),
                             "intro_cal": caliber(node.get("intro", ""))})
                pg.close()
            browser.close()
    finally:
        httpd.server_close()

    print("== _probe_thresholds.py：阈值重导取证（真实渲染；%dx%d；⛔ 不落产物）=="
          % (VIEWPORT_W, VIEWPORT_H))
    print("内核：%s" % CHROME)
    print()
    print("-- A. 版式实测（★ 口径已更正，见下）--")
    print("   ★ 命名更正（2026-10-16，第 5 轮审核当场指出）：此前把 main 的 **border-box 宽** 印成"
          "「内容列宽」是**同名两口径**——`box-sizing:border-box` + `.layout>main{padding:0 var(--space-5)}`"
          "（2×32px）⇒ **内容列内宽 = border-box 宽 − 64px**，即 R-08 / P34 的 **804px**。")
    for r in rows:
        mm = r["m"]["main"]
        inner = (mm["contentW"] - 64.0) if mm["contentW"] else None
        print("   %-30s main border-box %6.1fpx → 内容列内宽 %s px · 根字号 %s · 行高 %s"
              % (r["rel"], mm["contentW"],
                 ("%6.1f" % inner) if inner is not None else "  n/a",
                 mm["fontSize"], mm["lineHeight"]))
    print()
    print("-- B/C. 逐区块：行数 / 块高 / 每行 caliber / px per caliber / 一屏可读量（视口 %dpx）--"
          % VIEWPORT_H)
    caps = {"why": [], "intro": []}
    for r in rows:
        for sid, cal in (("sec-why", r["why_cal"]), ("sec-intro", r["intro_cal"])):
            b = r["m"][sid]
            if not b or not b["lines"] or not b["lineHeight"]:
                print("   %-30s %-10s（无正文块）" % (r["rel"], sid))
                continue
            px_per_cal = b["blockH"] / float(cal) if cal else 0
            n_screen = int(VIEWPORT_H // px_per_cal) if px_per_cal else 0
            per_line = cal / float(b["lines"])
            caps[sid[4:]].append((r["id"], n_screen, round(px_per_cal, 3), round(per_line, 1)))
            print("   %-30s %-10s 行 %3d · 块高 %6.1fpx · caliber %4d · 每行 %5.1f · "
                  "px/caliber %6.3f · 一屏 %5d caliber"
                  % (r["rel"], sid, b["lines"], b["blockH"], cal, per_line, px_per_cal, n_screen))
    print()
    print("-- D. 反解 --")
    for k in ("why", "intro"):
        if caps[k]:
            vals = [x[1] for x in caps[k]]
            print("   %-6s 一屏容量：min %d / max %d caliber（逐页 %s）"
                  % (k, min(vals), max(vals), caps[k]))
    print()
    print("   ★ 由 D 可导出的**只有上限**（一屏可读量）。按 SCHEMA.md 的判据分档原则，上限"
          "只影响版式首屏 ⇒ **只能作报告项**，⛔ 不得升为硬判据。")
    print("   ★ **`intro` 下限无法由渲染导出**：下界的因果在内容侧（机制叙述需要展开空间），"
          "渲染只能给上界 ⇒ 如实登记，⛔ 不硬凑数字。")
    print()
    print("== 结论：取证完成（退出码 0；本件是取证不是判据）==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
