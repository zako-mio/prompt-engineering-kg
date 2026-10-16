#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-meta.py —— 发布级站点级元数据产物（sitemap.xml / robots.txt）

★ 为什么单独一个生成器（2026-10-16 第 8 轮，SH4 标准档）：
  `sitemap.xml` 与 `robots.txt` 是**全站级**产物 —— 它们的内容不是任何单一页面的函数，
  而是「本次构建**全部产出页面的集合**」的函数。若把它塞进 `gen-root.py`，就会变成
  「根入口生成器顺带知道全站有哪些页」，那是跨职责的隐式耦合。
  ⇒ 它必须由**构建层**（`build-all.py`）把「本次产出的页面清单」传进来。

★ 幂等与新鲜度：
  · ⛔ 不写 `<lastmod>` —— 墙钟时间戳会让「连续两次 --write 逐文件 sha256 一致」这条硬要求失效
    （与姊妹站 `algorithm-knowledge-graph` 的 `site_meta.sitemap_xml()` 同口径）。
  · 产物是**纯函数**：输入 = 页面清单（已排序）＋ 站点基址，输出 = 确定的字节。

★ 判据对应：`gate_seo_meta.py` 的 S8（robots 含 `Sitemap:` 行）/ S9（sitemap 覆盖全部页且无孤儿）
  / S10（sitemap 是合法 XML 且 `loc` 全部为本站绝对 URL）。同批登记件 `CRITERIA-CHANGE-R08.md`。
"""

import argparse
import html
import importlib.util
import os
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _imp(os.path.join(HERE, "gen-common.py"), "pekg_gen_common")

SITEMAP_REL = "sitemap.xml"
ROBOTS_REL = "robots.txt"


def page_inventory(root=None):
    """兜底路径：由**真相源**推出「本次应当产出的页面集合」（⭐ 权威来源仍是 build-all 的实产出）。

    ★ 为什么要有兜底：`gen-meta.py` 可以脱离 `build-all.py` 单独跑（调试用）。
      ⛔ 但它**不是**第二份真相 —— `build-all.py` 传进来的清单优先；本函数只在未传时兜底，
      且判据 S9 会拿**磁盘上的真实 HTML 集合**与 sitemap 对账 ⇒ 两份一旦分叉当场 FAIL。
    """
    root = root or C.SITE_ROOT
    data = C.load_sources()
    pages = ["index.html", "%s/index.html" % C.DIR_INTERACTIVE]
    pages += ["%s/%s.html" % (C.DIR_NODES, C.id_slug(n["id"]))
              for n in data["dag"]["nodes"] if n["content_status"] == "complete"]
    pages += ["%s/index.html" % C.DIR_GROUPS]
    pages += ["%s/%s.html" % (C.DIR_GROUPS, g["id"].lower()) for g in data["dag"]["groups"]]
    pages += ["%s/%s" % (C.DIR_VIEWS, fn) for fn in sorted(os.listdir(os.path.join(root, C.DIR_VIEWS)))
              if fn.endswith(".html")]
    return sorted(set(pages))


def sitemap_xml(pages):
    """覆盖**全部**已发布 HTML 的 `sitemap.xml`。⛔ 无 `<lastmod>`（见模块 docstring）。"""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel in sorted(pages):
        # ★ XML 转义用 html.escape（站内路径不含 `&`，但**不允许**因此省略转义 —— 那是「知道今天不会错」）
        lines.append("  <url><loc>%s</loc></url>" % html.escape(C._abs_url(rel), quote=True))
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def robots_txt():
    """`robots.txt` —— ★ 必须含 `Sitemap:` 行（判据 S8 硬判它，⛔ 不接受「语义等价」）。"""
    return ("User-agent: *\n"
            "Allow: /\n"
            "Sitemap: %s\n" % C._abs_url(SITEMAP_REL))


def generate(pages=None, root=None):
    """返回 {相对路径: 内容}。`pages` 为空时走 `page_inventory()` 兜底。"""
    pages = sorted(set(pages if pages else page_inventory(root)))
    if not pages:
        # ★ 空集守卫：宁可在生成期炸掉，也不产出一份「空 sitemap」（那会让 S9 以为自己通过了）
        raise SystemExit("[FAIL] gen-meta：页面清单为空 ⇒ 拒绝产出空 sitemap（空集守卫）")
    bad = [p for p in pages if not p.endswith(".html")]
    if bad:
        raise SystemExit("[FAIL] gen-meta：页面清单含非 HTML 项 %s" % bad[:5])
    return {SITEMAP_REL: sitemap_xml(pages), ROBOTS_REL: robots_txt()}


def main():
    ap = argparse.ArgumentParser(description="站点级元数据产物（sitemap.xml / robots.txt）")
    ap.add_argument("--list", action="store_true", help="打印当前清单覆盖的页面")
    ap.add_argument("--root", default=None, help="产物根（兜底清单用；默认 04-prototype/）")
    a = ap.parse_args()
    pages = page_inventory(a.root)
    if a.list:
        print("清单页数 %d；sitemap 行数 %d" % (len(pages), len(sitemap_xml(pages).splitlines())))
        for p in pages:
            print("   %s" % p)
        return 0
    for rel, text in sorted(generate(pages).items()):
        print("%s  %d 字节" % (rel, len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
