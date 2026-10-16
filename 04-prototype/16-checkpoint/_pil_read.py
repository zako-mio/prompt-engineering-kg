#!/usr/bin/env python3
"""_pil_read.py —— 对 PNG 做 PIL 读数（尺寸 + 唯一色数 + 亮度范围），证明非空图。

为什么需要：渲染脚本只负责出图，**不负责判对错**（`RENDER-CHANNEL.md §六.1`）。
「文件存在」不等于「画出来了」——本机实测过一条假绿通道（agent-browser）会回显
「Screenshot saved」却产出纯白 1 色空图。故必须核验像素。

用法：python3 _pil_read.py <png> [png ...]
退出码：0 = 全部非空（uniq_colors > 1）；1 = 存在空图或读取失败
⛔ 只读，不写任何产物。
"""
import sys
import os

try:
    from PIL import Image
except ImportError:
    print("PIL 不可用")
    sys.exit(2)

rc = 0
print(f"{'PNG':<44} {'尺寸':<12} {'唯一色':>8} {'字节':>9}  亮度min..max  判定")
for p in sys.argv[1:]:
    if not os.path.isfile(p):
        print(f"{p:<44} {'-':<12} {'-':>8} {'-':>9}  {'-':<12}  MISSING")
        rc = 1
        continue
    try:
        im = Image.open(p).convert("RGB")
        colors = im.getcolors(maxcolors=1 << 24)
        uniq = len(colors) if colors else -1
        small = im.resize((9, 9))
        lum = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in small.getdata()]
        verdict = "OK(非空)" if uniq > 1 else "EMPTY(单色空图)"
        if uniq <= 1:
            rc = 1
        print(f"{p:<44} {f'{im.width}x{im.height}':<12} {uniq:>8} "
              f"{os.path.getsize(p):>9}  {min(lum):5.1f}..{max(lum):5.1f}  {verdict}")
    except Exception as exc:  # noqa: BLE001
        print(f"{p:<44} READ_ERROR {exc}")
        rc = 1
print(f"\n== PIL 读数结论：{'全部非空' if rc == 0 else '存在空图/缺失'} ==")
sys.exit(rc)
