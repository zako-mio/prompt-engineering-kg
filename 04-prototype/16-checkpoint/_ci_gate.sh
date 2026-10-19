#!/usr/bin/env bash
# _ci_gate.sh —— CI 门控入口（★ 分档执行，⛔ 不是「跑全部判据」）
#
# ★ 为什么分档（见 `README.md` §六 偏离 #3 与 `CRITERIA-CHANGE-R08.md` §5·L6）：
#   本仓有**三个**独立门控脚本，全量档包含「渲染证据解码」「本机 playwright 探测」「几何复算」等
#   需要真渲染或真浏览器的面 ⇒ 单次数分钟。⛔ 那不是「更安全」，而是「CI 每次 push 都超时」，
#   结果是所有人绕过它（判据设计的成本治理：**门控的预算帽与它的断言面同样重要**）。
#
#   分档口径：
#     · **fast 档**（默认，每次 push）：只跑**不依赖渲染证据**的判据子集 + A/S 两段全量 + 幂等复跑。
#       ⛔ 排除 P38（它要解码 PNG 并与 `_probe/channel.json` 的事实一致 —— 那是**开工期**的探测，
#          不是每次构建都该重跑的东西）与 P41（源文件散文扫描：那是**轮次收口**的对象）。
#     · **full 档**（`workflow_dispatch` ＋ 每周一次）：跑全部 P01–P41 ＋ `--selftest` ＋ 数据自检 ＋
#       图件规格两侧探针。★ 这才是「全绿」的口径。
#       ★ 2026-10-19 第 9 轮实测补：**P38 有对象条件** —— 它读 `_probe/channel.json`（本机渲染通道
#         探测件），而 `_probe/` 按 `.gitignore` 规则② **整层不入库** ⇒ **CI 上该文件不存在**。
#         第 8 轮把「渲染期像素层未进 CI」写进了 `gate-manifest.json` 的 `not_covered`，但本档
#         **仍然无条件调用 P38** ⇒ 声明与实现相反，且 2026-10-19 的定时任务实测红（run 39225734249）。
#         ⇒ 现改为按对象是否存在分流（见下方 `FULL_ONLY_NO_P38`），⛔ 不是静默通过、⛔ 不是放宽 P38。
#
# ★ 退出码：0 = 本档全过；非 0 = 有 FAIL（⛔ 不吞掉任何一档的失败）。
#
# 用法：cd 04-prototype/16-checkpoint && bash _ci_gate.sh [fast|full]
set -uo pipefail

MODE="${1:-fast}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# ★ 本档显式声明它**跑**哪些判据、**不跑**哪些 —— ⛔ 不用「默认全跑」：
#   排除集必须逐条给理由，否则「漏跑」与「有意不跑」无法区分（这正是本仓 R-23 的纪律）。
FAST_ONLY="P02,P03,P04,P05,P06,P07,P08,P09,P10,P11,P12,P13,P14,P15,P16,P17,P18,P19,P20,P21,P22,P23,P24,P25,P26,P27,P28,P29,P30,P31,P32,P33,P34,P35,P36,P37,P39,P40"
FAST_NOTRUN_REASON="P01 属真相源解析（由 P02–P07 覆盖其后果）；P38 需渲染证据与开工期探测；P41 是轮次收口的对象"

# ★ full 档的 P38 对象条件（见文件头 ★ 2026-10-19 第 9 轮实测补）：
#   对象在 ⇒ 跑全量（含 P38）；对象不在 ⇒ 显式排除 P38 并打印理由（⛔ 不静默通过）。
FULL_ONLY_NO_P38="P01,P02,P03,P04,P05,P06,P07,P08,P09,P10,P11,P12,P13,P14,P15,P16,P17,P18,P19,P20,P21,P22,P23,P24,P25,P26,P27,P28,P29,P30,P31,P32,P33,P34,P35,P36,P37,P39,P40,P41"
FULL_P38_NOTRUN_REASON="P38 的对象 _probe/channel.json 不在库（.gitignore 规则②把过程证据整层排除）⇒ 本环境显式排除 P38；★ 本机存在该文件时 full 档照跑 P38（本档⛔ 不得读作「像素层已验证」）"

# ★ full 档的 **C58 对象条件**（★ 2026-10-19 第 9 轮 CI 对象审计当场报出，见 CRITERIA-CHANGE-R09.md）：
#   数据侧自检的 C58 读 `01-research/evidence/A*.json`，而 `01-research/` 按规则①**整层不入库**
#   ⇒ 任何新 checkout 都没有它。此时 C58 **无对象**：⛔ 既不能静默算通过（假绿），
#     也不能让整条 full 档恒 FAIL（那会让 C01–C57 共 57 条**一并**跑不成）。
#   ⇒ 处置：输入层不在盘上时**显式声明**（环境变量）⇒ 脚本打印 `[SKIP] C58/C58b` 并给出理由；
#     输入层在盘上时**照跑 C58 且必须 PASS**（fail-closed 语义一字未动）。
FULL_C58_NOTRUN_REASON="C58 的对象 01-research/evidence/A*.json 不在库（.gitignore 规则①把私密输入层整层排除）⇒ 本环境由调用方显式声明 PEKG_INPUT_LIBRARY_ABSENT=1，脚本打印 [SKIP] 并给出理由；★ 本机（输入层在盘上）照跑 C58 且必须 PASS，⛔ 本档不得读作「引文回源已在 CI 覆盖」"

rc=0
step() { printf '\n=== %s ===\n' "$*"; }

step "[$MODE] 幂等复跑：build-all --dry-run（差集必须为 0）"
python3 build-all.py --dry-run | tail -6 || rc=1

if [ "$MODE" = "full" ]; then
  if [ -f _probe/channel.json ]; then
    step "[full] gate_prototype P01–P41（全量；本机存在 _probe/channel.json ⇒ 含 P38）"
    python3 gate_prototype.py || rc=1
    step "[full] gate_prototype --selftest（逐条负例）"
    python3 gate_prototype.py --selftest || rc=1
  else
    step "[full] gate_prototype --only（P01–P41 减 P38；本环境无 _probe/channel.json）"
    printf '   （本档有意不跑：%s）\n' "$FULL_P38_NOTRUN_REASON"
    python3 gate_prototype.py --only "$FULL_ONLY_NO_P38" || rc=1
    step "[full] gate_prototype --selftest --only（同一对象集）"
    python3 gate_prototype.py --selftest --only "$FULL_ONLY_NO_P38" || rc=1
  fi
  if ls ../../01-research/evidence/A*.json >/dev/null 2>&1; then
    step "[full] 数据侧自检 ../10-dag-data/_selfcheck.py（输入层在盘上 ⇒ 含 C58 逐片段回源）"
    python3 ../10-dag-data/_selfcheck.py || rc=1
  else
    step "[full] 数据侧自检 ../10-dag-data/_selfcheck.py（本 checkout 无输入层 ⇒ C58 显式声明不适用）"
    printf '   （本档有意不跑：%s）\n' "$FULL_C58_NOTRUN_REASON"
    PEKG_INPUT_LIBRARY_ABSENT=1 python3 ../10-dag-data/_selfcheck.py || rc=1
  fi
  step "[full] 图件规格两侧探针 _selfcheck_figs_spec.py"
  python3 _selfcheck_figs_spec.py || rc=1
else
  step "[fast] gate_prototype --only $FAST_ONLY"
  printf '   （本档有意不跑：%s）\n' "$FAST_NOTRUN_REASON"
  python3 gate_prototype.py --only "$FAST_ONLY" || rc=1
fi

step "[$MODE] 无障碍门控 gate_a11y.py（A1–A7）"
python3 gate_a11y.py || rc=1
step "[$MODE] 无障碍门控 --selftest"
python3 gate_a11y.py --selftest || rc=1

step "[$MODE] 元数据门控 gate_seo_meta.py（S1–S11）"
python3 gate_seo_meta.py || rc=1
step "[$MODE] 元数据门控 --selftest"
python3 gate_seo_meta.py --selftest || rc=1

printf '\n== _ci_gate.sh [%s] 结论：%s ==\n' "$MODE" "$([ $rc -eq 0 ] && echo PASS || echo FAIL)"
exit $rc
