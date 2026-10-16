#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build-all.py —— 生成层主入口（幂等落盘 + 孤儿产物清理）

用法：
  python3 build-all.py --dry-run            只输出新增 / 修改 / 删除清单，不写盘
  python3 build-all.py --write              幂等落盘，并清理真相源中已不存在对象对应的孤儿产物
  python3 build-all.py --dry-run --json     机器可读输出（门控 P17 消费）
  python3 build-all.py --root <dir> ...     指定产物根（门控在临时沙箱里复跑时使用）
  python3 build-all.py                      打印帮助

幂等硬要求：连续两次 --write 后全部产物逐文件 sha256 一致；--dry-run 的差异清单与实际
落盘清单差集 = 0；已删除对象的产物文件残留数 = 0。
"""

import argparse
import hashlib
import importlib.util
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.normpath(os.path.join(HERE, ".."))

GENERATORS = ("gen-nodes.py", "gen-groups.py", "gen-views.py", "gen-root.py",
              "gen-md.py", "gen-interactive.py", "gen-state.py")

OWNED_DIRS = ("11-node-pages", "12-groups", "14-views", "15-md", "13-interactive")
OWNED_ROOT_FILES = ("index.html", "PUBLISH-STATE.json")
OWNED_SKIP_PREFIX = ("13-interactive/vendor/",)


def _imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def generate_all():
    """把全部生成器的产物合并为 {相对路径: 文本}；重复路径即报错（防两套生成源）。"""
    out = {}
    origin = {}
    for g in GENERATORS:
        mod = _imp(os.path.join(HERE, g), "pekg_" + g.replace(".py", "").replace("-", "_"))
        files = mod.generate()
        for rel, text in files.items():
            if rel in out:
                raise SystemExit("[FAIL] 产物路径冲突：%s 由 %s 与 %s 同时产出"
                                 % (rel, origin[rel], g))
            out[rel] = text
            origin[rel] = g
    return out


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def disk_files(root):
    """当前磁盘上的受管产物：{相对路径: sha256}。"""
    found = {}
    for d in OWNED_DIRS:
        base = os.path.join(root, d)
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, root).replace(os.sep, "/")
                if any(rel.startswith(pre) for pre in OWNED_SKIP_PREFIX):
                    continue
                found[rel] = sha(open(p, encoding="utf-8").read())
    for fn in OWNED_ROOT_FILES:
        p = os.path.join(root, fn)
        if os.path.exists(p):
            found[fn] = sha(open(p, encoding="utf-8").read())
    return found


def diff(expected, root):
    """差异清单：added / modified / deleted / unchanged。"""
    have = disk_files(root)
    exp = {k: sha(v) for k, v in expected.items()}
    added = sorted(k for k in exp if k not in have)
    modified = sorted(k for k in exp if k in have and have[k] != exp[k])
    deleted = sorted(k for k in have if k not in exp)
    unchanged = sorted(k for k in exp if k in have and have[k] == exp[k])
    return {"added": added, "modified": modified, "deleted": deleted, "unchanged": unchanged}


def apply_write(expected, root):
    wrote = []
    for rel, text in sorted(expected.items()):
        p = os.path.join(root, rel)
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        old = None
        if os.path.exists(p):
            old = open(p, encoding="utf-8").read()
        if old != text:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            wrote.append(rel)
    removed = []
    for rel in diff(expected, root)["deleted"]:
        os.remove(os.path.join(root, rel))
        removed.append(rel)
    # 清理空目录（只清受管目录下的空子目录）
    for d in OWNED_DIRS:
        base = os.path.join(root, d)
        for dirpath, dirnames, filenames in os.walk(base, topdown=False):
            if dirpath == base:
                continue
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
    return sorted(wrote), sorted(removed)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--dry-run", dest="dry", action="store_true", help="只输出差异清单，不写盘")
    ap.add_argument("--write", dest="write", action="store_true", help="幂等落盘并清理孤儿产物")
    ap.add_argument("--json", dest="as_json", action="store_true", help="机器可读输出")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="产物根（默认 04-prototype/）")
    a = ap.parse_args()

    if not a.dry and not a.write:
        ap.print_help()
        return 0

    root = os.path.abspath(a.root)
    expected = generate_all()
    plan = diff(expected, root)

    if a.write:
        wrote, removed = apply_write(expected, root)
        plan_after = diff(expected, root)
        result = {"mode": "write", "root": root, "files": len(expected),
                  "added": plan["added"], "modified": plan["modified"], "deleted": plan["deleted"],
                  "unchanged": plan["unchanged"],
                  "written": wrote, "removed": removed,
                  "residual_orphans": plan_after["deleted"],
                  "second_pass_clean": not (plan_after["added"] or plan_after["modified"] or plan_after["deleted"])}
    else:
        result = {"mode": "dry-run", "root": root, "files": len(expected),
                  "added": plan["added"], "modified": plan["modified"], "deleted": plan["deleted"],
                  "unchanged": plan["unchanged"]}

    if a.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== build-all %s ==  产物根 %s" % (result["mode"], root))
        print("预期产物 %d 个文件" % result["files"])
        for k in ("added", "modified", "deleted", "unchanged"):
            v = result.get(k, [])
            print("  %-10s %d" % (k, len(v)))
            for rel in v[:200]:
                print("      %s" % rel)
        if a.write:
            print("  实际写入 %d 个 / 实际删除 %d 个 / 孤儿残留 %d 个"
                  % (len(result["written"]), len(result["removed"]), len(result["residual_orphans"])))
            print("  二次比对干净：%s" % result["second_pass_clean"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
