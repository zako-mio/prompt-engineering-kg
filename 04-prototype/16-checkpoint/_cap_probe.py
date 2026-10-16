#!/usr/bin/env python3
"""_cap_probe.py —— 本会话能力/可写性实测（VERIFY-CONSTRAINT 更正用的第一手读数）。

为什么需要：`VERIFY-CONSTRAINT.md` 原件把 snap chromium 失败归因于
「`/run/user/1000/snap.chromium` 只读」。留档轮要求**复核**该结论 —— 故必须自己测，
⛔ 不得抄他人转述。

实测四项：
  A. `/proc/self/status` 的 CapEff / CapPrm / CapBnd / NoNewPrivs
  B. `/run/user/1000/snap.chromium` 是否存在、是否可写（真建一个临时文件再删）
  C. `snap-confine` 的 file capability（getcap 口径：读扩展属性 security.capability）
  D. 直接调用 snap chromium 的原始报错首行（负对照）

用法：python3 _cap_probe.py
退出码：恒 0（本件是**取证**，不是判据）。
⛔ 只读（B 项建一个临时文件后立即删除，不残留）。
"""
import os
import subprocess
import sys

print("== A. 进程能力集（/proc/self/status）==")
keep = ("CapInh", "CapPrm", "CapEff", "CapBnd", "NoNewPrivs", "Seccomp")
try:
    for line in open("/proc/self/status", encoding="utf-8"):
        if line.split(":")[0] in keep:
            print("   " + line.rstrip())
except OSError as exc:
    print("   读取失败:", exc)

print("\n== B. /run/user/1000/snap.chromium 存在性与可写性 ==")
d = "/run/user/1000/snap.chromium"
print(f"   exists={os.path.isdir(d)}")
if os.path.isdir(d):
    st = os.stat(d)
    print(f"   mode={oct(st.st_mode)} uid={st.st_uid} gid={st.st_gid}")
    probe = os.path.join(d, ".cap_probe_tmp")
    try:
        with open(probe, "w", encoding="utf-8") as f:
            f.write("x")
        os.remove(probe)
        print("   WRITABLE = YES  （建临时文件成功并已删除）")
    except OSError as exc:
        print(f"   WRITABLE = NO   ({exc})")
else:
    print("   （目录不存在）")

print("\n== C. snap-confine 的 file capability ==")
sc = "/usr/lib/snapd/snap-confine"
print(f"   exists={os.path.isfile(sc)}")
if os.path.isfile(sc):
    try:
        val = os.getxattr(sc, "security.capability")
        print(f"   security.capability = {val.hex()}")
        print("   （非空即说明该二进制带 file capability，需被提升进 CapEff 才能运行）")
    except OSError as exc:
        print(f"   getxattr 失败: {exc}")

print("\n== D. snap chromium 负对照（原始报错）==")
for cmd in (["/snap/bin/chromium", "--version"],
            ["/usr/bin/chromium-browser", "--headless", "--disable-gpu",
             "--no-sandbox", "--screenshot=/tmp/_cap_probe.png", "about:blank"]):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        out = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        print(f"   $ {' '.join(cmd[:2])} …  rc={r.returncode}")
        for ln in out[:4]:
            print("      " + ln)
    except Exception as exc:  # noqa: BLE001
        print(f"   $ {' '.join(cmd[:2])} …  EXC {exc}")

sys.exit(0)
