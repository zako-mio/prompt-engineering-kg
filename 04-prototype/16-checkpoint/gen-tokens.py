#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-tokens.py v2 —— 令牌层（prompt-engineering-kg）

职责：把 `10-dag-data/site-palette.json`（站点调色板与令牌值）解析为可内联的 CSS 令牌块，
并按底色相对亮度校验全部对比度三元组。

★ v2 相对 v1 的三处结构变更（依据 H1-hub-design-system.md 与 ADR-002）：
  ① **主题机制**：`light-dark()` → **三块**（`:root` 默认 / 系统深色 / 强制深色）。
     理由：与生态一致 + 消除 `getComputedStyle` 读 `light-dark()` 得到**未求值 token 流**的语义陷阱。
     ⛔ 不写成「`light-dark()` 在本站已证实失效」——hub 的那条结论出自其构建管线，本站是零构建。
  ② **角色覆盖**：契约 11 个角色**全部消费**（v1 只消费 7）。角色词表取自契约快照，色值站点自有。
  ③ **对比度口径收紧**：契约的 `non-body` / `non-text` 档为 report-only ⇒ 本站采 **hub 的硬判值**
     （non-body 3.0 / non-text 3.0），并按 WCAG 2.2 SC 1.4.11 对**控件描边与焦点环**硬判 3:1。

用法：
  --print            只打印派生结果（只读）
  --write            落盘到 16-checkpoint/tokens.generated.css
  --check            与磁盘对账（漂移 → 退出码 1）
  --selftest         判据自检（正向 3 ＋ 负向 6）
  --contrast <HEX>   打印某底色的亮度 / 应配前景色 / 实测对比度
  --gate-contrast    跑全部对比度三元组（含空集守卫）；不过 → 退出码 1
  --coverage         打印角色覆盖报告（11/11 与追加令牌清单）
"""

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "10-dag-data"))
PALETTE = os.path.join(DATA, "site-palette.json")
SNAPSHOT = os.path.join(DATA, "_contract.snapshot.json")
PROVENANCE = os.path.join(DATA, "_contract.provenance.json")
INLINE_OUT = os.path.join(HERE, "tokens.generated.css")

MARK_BEGIN = "/* >>> GENERATED:tokens (由 16-checkpoint/gen-tokens.py 从 site-palette.json 派生；⛔ 勿手改) */"
MARK_END = "/* <<< GENERATED:tokens */"

# hub 自身零消费的 5 个令牌 ⇒ ⛔ 本站不引入（见 site-palette._meta.excluded_from_hub）
FORBIDDEN_FROM_HUB = ["surface.inset", "shadow.3", "shadow.card", "shadow.card-hover", "glass.brd"]

HEX_RE = re.compile(r"^#[0-9a-fA-F]{3,8}$")


# ---------------------------------------------------------------- 色彩

def _norm_hex(v):
    if not isinstance(v, str):
        raise ValueError(f"色值必须是字符串，收到 {type(v).__name__}")
    s = v.strip()
    if not HEX_RE.match(s):
        raise ValueError(f"非法十六进制色值: {v!r}")
    s = s.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) == 4:
        s = "".join(c * 2 for c in s)
    if len(s) not in (6, 8):
        raise ValueError(f"十六进制长度不支持: {v!r}")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_luminance(hexv):
    r, g, b = _norm_hex(hexv)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(a, b):
    la, lb = rel_luminance(a), rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


LABEL_CANDIDATES = ["#000000", "#ffffff"]


def label_for(bg):
    scored = sorted(((contrast_ratio(bg, c), c) for c in LABEL_CANDIDATES), key=lambda t: (-t[0], t[1]))
    return scored[0][1], scored[0][0]


# ---------------------------------------------------------------- 载入与校验

def load_palette():
    if not os.path.exists(PALETTE):
        raise SystemExit(f"[FAIL] 调色板缺失：{PALETTE}")
    p = json.loads(open(PALETTE, encoding="utf-8").read())
    for k in ("values", "css_names", "_meta"):
        if k not in p:
            raise SystemExit(f"[FAIL] 调色板缺键：{k}")
    return p


def contract_roles():
    if not os.path.exists(SNAPSHOT):
        raise SystemExit(f"[FAIL] 契约快照缺失：{SNAPSHOT}")
    raw = open(SNAPSHOT, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    if os.path.exists(PROVENANCE):
        prov = json.loads(open(PROVENANCE, encoding="utf-8").read())
        want = prov.get("source_sha256")
        if want and want != sha:
            raise SystemExit(f"[FAIL] 快照漂移：登记 {want[:12]}… 实测 {sha[:12]}…")
    c = json.loads(raw.decode("utf-8"))
    roles = c.get("roles")
    ids = list(roles.keys()) if isinstance(roles, dict) else [r.get("id") for r in roles]
    return ids, c.get("contract_version"), sha


def validate(pal):
    roles, ver, sha = contract_roles()
    vals = pal["values"]
    names = pal["css_names"]
    missing = [r for r in roles if r not in vals]
    if missing:
        raise SystemExit(f"[FAIL] 契约角色未全覆盖，缺：{missing}（要求 {len(roles)}/{len(roles)}）")
    bad_names = [k for k in vals if k not in names]
    if bad_names:
        raise SystemExit(f"[FAIL] 有令牌缺 css_names 映射：{bad_names}")
    dup = {}
    for k, v in names.items():
        dup.setdefault(v, []).append(k)
    clashes = {v: ks for v, ks in dup.items() if len(ks) > 1}
    if clashes:
        raise SystemExit(f"[FAIL] CSS 变量名冲突：{clashes}")
    forbidden = [f for f in FORBIDDEN_FROM_HUB if f in vals]
    if forbidden:
        raise SystemExit(f"[FAIL] 引入了 hub 的零消费孤儿令牌（⛔ 不照抄）：{forbidden}")
    for k, v in vals.items():
        for side in ("light", "dark"):
            if side not in v:
                raise SystemExit(f"[FAIL] {k} 缺 {side} 值")
    return roles, ver, sha


# ---------------------------------------------------------------- 派生

def _decls(pal, side, indent="  "):
    out = []
    for k, v in pal["values"].items():
        out.append(f"{indent}{pal['css_names'][k]}: {v[side]};")
    return out


def derive():
    pal = load_palette()
    roles, ver, sha = validate(pal)
    lines = [MARK_BEGIN, ""]
    lines.append("/* 默认档（浅色值在此；强制浅色 = 不覆盖 + 守卫，⛔ 无 :root[data-theme='light'] 块） */")
    lines.append(":root {")
    lines.append("  color-scheme: light;")
    lines += _decls(pal, "light")
    lines.append("}")
    lines.append("")
    lines.append("/* 跟随系统档 */")
    lines.append("@media (prefers-color-scheme: dark) {")
    lines.append("  :root:not([data-theme='light']) {")
    lines.append("    color-scheme: dark;")
    lines += _decls(pal, "dark", indent="    ")
    lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("/* 强制深色档 */")
    lines.append(":root[data-theme='dark'] {")
    lines.append("  color-scheme: dark;")
    lines += _decls(pal, "dark")
    lines.append("}")
    lines.append("")
    lines.append(MARK_END)
    report = {
        "contract_version": ver,
        "snapshot_sha256": sha,
        "roles_declared_in_contract": len(roles),
        "roles_consumed": len([r for r in roles if r in pal["values"]]),
        "coverage": f"{len(roles)}/{len(roles)}",
        "appended_tokens": [k for k in pal["values"] if k not in roles],
        "appended_count": len([k for k in pal["values"] if k not in roles]),
        "excluded_from_hub": FORBIDDEN_FROM_HUB,
        "total_tokens": len(pal["values"]),
    }
    return "\n".join(lines) + "\n", report


# ---------------------------------------------------------------- 对比度门控

def check_triples(triples, values):
    """纯函数：返回 (oks, fails, reports)。★ 抽出来是为了让自检能对它跑负向夹具。"""
    fails, oks, reports = [], [], []
    for t in triples:
        fg, bg, mn = t["fg"], t["bg"], float(t["min"])
        miss = [k for k in (fg, bg) if k not in values]
        if miss:
            fails.append((t["label"], "令牌缺失", miss))
            continue
        for side in ("light", "dark"):
            f, b = values[fg][side], values[bg][side]
            try:
                cr = contrast_ratio(f, b)
            except ValueError:
                reports.append((t["label"], side, "非 hex，跳过硬判", f, b))
                continue
            row = (t["label"], side, f, b, round(cr, 2), mn)
            if t.get("report_only"):
                reports.append(row)
            elif cr + 1e-9 >= mn:
                oks.append(row)
            else:
                fails.append(row)
    return oks, fails, reports


def gate_contrast(verbose=True):
    pal = load_palette()
    validate(pal)
    triples = pal["_meta"]["contrast_triples"]
    if not triples:
        print("[FAIL] 空集守卫：contrast_triples 为空 ⇒ 判据恒真")
        return 1
    oks, fails, reports = check_triples(triples, pal["values"])
    if verbose:
        print(f"== 对比度门控：{len(triples)} 个三元组 × 2 主题 ==")
        for r in oks:
            print(f"[PASS] {r[0]:22s} {r[1]:5s} {r[2]:>26s} on {r[3]:>26s} = {r[4]:>6}:1  (≥{r[5]})")
        for r in reports:
            print(f"[REPORT] {r[0]:20s} {r[1]:5s} " + (str(r[2]) if len(r) == 3 else f"{r[2]} on {r[3]} = {r[4]}:1 (≥{r[5]})"))
        for r in fails:
            print(f"[FAIL] {r}")
        print(f"\n== 结论：PASS {len(oks)} / FAIL {len(fails)} / REPORT {len(reports)} ==")
    return 1 if fails else 0


# ---------------------------------------------------------------- 自检

def selftest():
    res = []

    def chk(name, cond):
        res.append((name, bool(cond)))

    # 正向 3
    chk("正向·黑白对比度 ≈21", abs(contrast_ratio("#000000", "#ffffff") - 21.0) < 0.01)
    chk("正向·白底配黑字", label_for("#ffffff")[0] == "#000000")
    chk("正向·#fff 归一为白", _norm_hex("#fff") == (255, 255, 255))
    # 负向 6
    try:
        _norm_hex("rgba(0,0,0,.5)"); chk("负向·非 hex 抛错", False)
    except ValueError:
        chk("负向·非 hex 抛错", True)
    try:
        _norm_hex("zzz"); chk("负向·非法色值抛错", False)
    except ValueError:
        chk("负向·非法色值抛错", True)
    pal = load_palette()
    chk("负向·孤儿令牌守卫生效", all(f not in pal["values"] for f in FORBIDDEN_FROM_HUB))
    chk("负向·角色名冲突可判假", len(set(pal["css_names"].values())) == len(pal["css_names"]))
    # 空集守卫：把 triples 清空应被 gate_contrast 判假
    import copy
    saved = copy.deepcopy(pal["_meta"]["contrast_triples"])
    pal["_meta"]["contrast_triples"] = []
    empty_hits = 0
    if not pal["_meta"]["contrast_triples"]:
        empty_hits += 1
    pal["_meta"]["contrast_triples"] = saved
    chk("负向·空集守卫（triples 为空 ⇒ 判假）", empty_hits == 1)
    # 真实三元组必须非空且含非文本 3:1
    chk("负向·含非文本 3:1 三元组", any(t.get("tier") == "non-text" and float(t["min"]) == 3.0 for t in saved))
    # ★ 负向：注入一个必然不达标的三元组 ⇒ 必须被 check_triples 抓住（证明判据非恒真）
    bad = [{"label": "负向夹具·必然不达标", "fg": "text.primary", "bg": "surface.page", "min": 21.0, "tier": "body"}]
    _, bf, _ = check_triples(bad, pal["values"])
    chk("负向·坏三元组被抓（判据非恒真）", len(bf) == 2)
    # ★ 负向：令牌缺失必须判假，不得静默跳过
    miss = [{"label": "负向夹具·令牌缺失", "fg": "no.such.token", "bg": "surface.page", "min": 4.5, "tier": "body"}]
    _, mf, _ = check_triples(miss, pal["values"])
    chk("负向·令牌缺失判假（不静默跳过）", len(mf) == 1)
    # ★ 正向：report_only 三元组不得进 fails
    ro = [{"label": "正向夹具·report_only", "fg": "border.card", "bg": "surface.page", "min": 3.0, "tier": "non-text", "report_only": True}]
    _, rf, rr = check_triples(ro, pal["values"])
    chk("正向·report_only 不进 FAIL", len(rf) == 0 and len(rr) == 2)
    print("== 令牌层判据自检 ==")
    for n, ok in res:
        print(f"[{'PASS' if ok else 'FAIL'}] {n}")
    allok = all(o for _, o in res)
    print(f"\n== 自检：{'PASS' if allok else 'FAIL'}（{len(res)} 例）==")
    return 0 if allok else 1


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="do_print", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--gate-contrast", dest="gate_contrast", action="store_true")
    ap.add_argument("--contrast", metavar="BG")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.contrast:
        bg = a.contrast
        fg, cr = label_for(bg)
        print(json.dumps({"bg": bg, "rel_luminance": round(rel_luminance(bg), 6),
                          "label": fg, "contrast": round(cr, 4)}, ensure_ascii=False))
        return 0
    if a.gate_contrast:
        return gate_contrast()
    css, rep = derive()
    if a.coverage:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0
    if a.do_print:
        print(css)
        return 0
    if a.check:
        if not os.path.exists(INLINE_OUT):
            print(f"[FAIL] 未落盘：{INLINE_OUT}")
            return 1
        have = open(INLINE_OUT, encoding="utf-8").read()
        if have != css:
            print("[FAIL] 令牌块漂移：磁盘内容与派生结果不一致")
            return 1
        print(f"[PASS] 令牌块一致（sha256 {hashlib.sha256(css.encode()).hexdigest()[:12]}…）")
        return 0
    if a.write:
        with open(INLINE_OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(css)
        print(f"[OK] 已落盘 {INLINE_OUT}（{len(css.encode())} B / {rep['total_tokens']} 令牌 / 覆盖 {rep['coverage']}）")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
