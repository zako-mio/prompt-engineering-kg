#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_render.py —— 04-prototype 站点的**真实渲染**通道（headless Chromium → PNG）。

为什么需要它
------------
本机 chromium 是 **snap 包**（/snap/bin/chromium → /usr/bin/snap），其 confinement
强制要求 `/run/user/1000/snap.chromium` 可写，而该路径在沙箱内**只读**，因此
`chromium --headless --screenshot` 与 agent-browser 全部失败。本脚本改用
**非 snap** 的 playwright 自带 chromium：
    ~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome   (ELF, 153.0.8010.12)
配合本机已装的 Python playwright 1.63.0（~/.local/lib/python3.12/site-packages），
完全绕开 snap confinement。

用法
----
    python3 _render.py --html 04-prototype/index.html --width 1440 --height 900 \
                       --out 04-prototype/16-checkpoint/_render-proof/index.png

参数
----
    --html     HTML 文件路径（绝对，或相对于当前工作目录）
    --out      输出 PNG 路径
    --width    视口宽（默认 1440）
    --height   视口高（默认 900）
    --dsf      设备像素比（默认 1）
    --theme    light | dark（默认 light）——显式固定 prefers-color-scheme，
               否则同一页面会在浅/深色下产出不同 PNG（不可复现）
    --root     站点文档根（默认自动探测：含 assets/ 的祖先目录）
    --full     截整页（默认只截视口）
    --json     额外写出证据 manifest（资源加载清单 + sha256）
    --quiet    不打印资源清单

确定性保证
----------
* 固定视口 + 固定 dsf + 固定 colorScheme(light) + prefers-reduced-motion: reduce
* 无时钟、无随机、无网络外部依赖（全部资源来自本地静态服务器）
* 等待 `document.fonts.ready` + 所有 <img> complete + `networkidle`
* 注入 CSS 把 animation/transition 冻到终态（该站有 reveal-in 入场动画，
  不冻结会截到动画中途帧）
* 页面脚本自身无 Date()/Math.random()（已核查）

站点必须以**站点根为文档根**提供：样式块里写的是 `../assets/backdrop/*.webp`，
所以本脚本内部起一个临时静态服务器（root=04-prototype），
⛔ 不用 file:// 直开（背景素材会 404）。
"""
import argparse
import hashlib
import http.server
import json
import os
import socketserver
import sys
import threading
import time

CHROME = os.path.expanduser(
    "~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome")

# 冻结动效：让截图落在终态，而不是入场动画的中间帧
FREEZE_CSS = """
*,*::before,*::after{
  animation-duration:0s !important;
  animation-delay:0s !important;
  animation-iteration-count:1 !important;
  animation-fill-mode:forwards !important;
  transition-duration:0s !important;
  transition-delay:0s !important;
  caret-color:transparent !important;
}
"""


def log(*a):
    print(*a, flush=True)


def find_site_root(html_path):
    """从 html 所在目录向上找含 assets/ 的目录 = 站点文档根。"""
    d = os.path.dirname(os.path.abspath(html_path))
    while True:
        if os.path.isdir(os.path.join(d, "assets")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit(f"[render] 找不到站点根（无 assets/ 祖先）: {html_path}")
        d = parent


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """静态服务器：记录 200/404，便于证明 CSS/背景图真的加载到了。"""
    hits = []

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        rc = None
        try:
            rc = super().do_GET()
        finally:
            QuietHandler.hits.append((self.path, rc))
            if rc is None:  # SimpleHTTPRequestHandler 直接写了响应，没返回码
                QuietHandler.hits[-1] = (self.path, getattr(self, "_rc", 200))

    def send_response(self, code, message=None):
        self._rc = code
        super().send_response(code, message)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server(root):
    handler = lambda *a, **kw: QuietHandler(*a, directory=root, **kw)
    srv = Server(("127.0.0.1", 0), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, srv.server_address[1]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="真实渲染 04-prototype 站点为 PNG")
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--dsf", type=float, default=1)
    ap.add_argument("--theme", choices=["light", "dark"], default="light")
    ap.add_argument("--root", default=None)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--json", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    html_abs = os.path.abspath(args.html)
    if not os.path.isfile(html_abs):
        raise SystemExit(f"[render] HTML 不存在: {html_abs}")
    out_abs = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)

    root = os.path.abspath(args.root) if args.root else find_site_root(html_abs)
    rel = os.path.relpath(html_abs, root)
    if rel.startswith(".."):
        raise SystemExit(f"[render] HTML 不在站点根内: {html_abs} vs root {root}")

    if not os.path.isfile(CHROME):
        raise SystemExit(f"[render] 非 snap chromium 不存在: {CHROME}")

    # ---- 必须先把 playwright 的 browsers 路径固定住 ----
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH",
                          os.path.expanduser("~/.cache/ms-playwright"))

    srv, port = start_server(root)
    url = f"http://127.0.0.1:{port}/{rel}"
    log(f"[render] docroot = {root}")
    log(f"[render] url     = {url}")
    log(f"[render] chrome  = {CHROME}")

    from playwright.sync_api import sync_playwright

    resources = []
    console_errors = []
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--force-color-profile=srgb",
                "--hide-scrollbars",
                "--font-render-hinting=none",
                "--disable-lcd-text",
                "--deterministic-mode",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--force-device-scale-factor=%s" % args.dsf,
            ],
        )
        ctx = browser.new_context(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.dsf,
            color_scheme=args.theme,          # 固定主题，消除不可复现
            reduced_motion="reduce",          # 固定动效偏好
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            storage_state=None,               # 空 localStorage ⇒ 站点默认态
        )
        ctx.add_init_script("try{localStorage.clear()}catch(e){}")

        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(f"{m.type}: {m.text}")
                if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(f"pageerror: {e}"))
        page.on("requestfailed", lambda r: resources.append(
            {"url": r.url, "status": "FAILED", "err": (r.failure or "")}))

        resp = page.goto(url, wait_until="load", timeout=45000)
        page.add_style_tag(content=FREEZE_CSS)

        # 等字体 + 等所有 <img> 解码完成 + 等网络静默
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            log("[render] networkidle 超时（继续）")
        page.evaluate("""async () => {
            if (document.fonts && document.fonts.ready) { await document.fonts.ready; }
            const imgs = Array.from(document.images || []);
            await Promise.all(imgs.map(i => i.complete ? Promise.resolve()
                : new Promise(r => { i.addEventListener('load', r, {once:true});
                                     i.addEventListener('error', r, {once:true}); })));
        }""")
        page.wait_for_timeout(400)

        # 资源清单：证明样式表与背景图真的 200 了
        for r in page.evaluate("""() => performance.getEntriesByType('resource')
            .map(e => ({name: e.name, type: e.initiatorType,
                        size: e.transferSize || e.decodedBodySize || 0}))"""):
            resources.append(r)
        css_rules = page.evaluate("""() => {
            let n = 0, sheets = 0;
            for (const s of document.styleSheets) {
                sheets++;
                try { n += s.cssRules.length; } catch (e) {}
            }
            return {sheets, rules: n};
        }""")
        probe = page.evaluate("""() => {
            const cs = getComputedStyle(document.body);
            const h1 = document.querySelector('h1');
            const bd = document.querySelector('.backdrop__photo--day');
            return {
              bodyBg: cs.backgroundColor, bodyFont: cs.fontFamily,
              bodySize: cs.fontSize, bodyColor: cs.color,
              h1Size: h1 ? getComputedStyle(h1).fontSize : null,
              h1Font: h1 ? getComputedStyle(h1).fontFamily : null,
              backdropImg: bd ? getComputedStyle(bd).backgroundImage.slice(0,120) : null,
              backdropDisplay: bd ? getComputedStyle(bd).display : null,
              theme: document.documentElement.getAttribute('data-theme'),
              htmlClass: document.documentElement.className,
              title: document.title,
              textLen: (document.body.innerText || '').length,
            };
        }""")

        page.screenshot(path=out_abs, full_page=args.full)
        bver = browser.version
        ctx.close()
        browser.close()

    srv.shutdown()
    dt = time.time() - t0

    manifest = {
        "html": html_abs, "docroot": root, "url": url, "out": out_abs,
        "viewport": {"width": args.width, "height": args.height, "dsf": args.dsf},
        "theme": args.theme, "full_page": args.full,
        "browser": {"executable": CHROME, "version": bver,
                    "engine": "playwright-python/chromium (non-snap)"},
        "png_sha256": sha256(out_abs),
        "png_bytes": os.path.getsize(out_abs),
        "http_status": resp.status if resp else None,
        "css": css_rules, "probe": probe,
        "console_errors": console_errors,
        "resources": resources,
        "server_hits": QuietHandler.hits,
        "seconds": round(dt, 2),
    }
    if args.json:
        with open(os.path.abspath(args.json), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1)

    if not args.quiet:
        log("[render] ---- HTTP 命中（服务器侧）----")
        for path, rc in QuietHandler.hits:
            log(f"   {rc}  {path}")
        log("[render] ---- 计算样式探针 ----")
        log(json.dumps(probe, ensure_ascii=False, indent=1))
        log(f"[render] stylesheets={css_rules['sheets']} rules={css_rules['rules']}")
        if console_errors:
            log("[render] console errors:", console_errors)
    log(f"[render] OK  {out_abs}  ({manifest['png_bytes']} bytes, "
        f"sha256={manifest['png_sha256'][:16]}…, {dt:.2f}s)")


if __name__ == "__main__":
    main()
