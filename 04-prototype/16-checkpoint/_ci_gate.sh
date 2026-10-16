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

rc=0
step() { printf '\n=== %s ===\n' "$*"; }

step "[$MODE] 幂等复跑：build-all --dry-run（差集必须为 0）"
python3 build-all.py --dry-run | tail -6 || rc=1

if [ "$MODE" = "full" ]; then
  step "[full] gate_prototype P01–P41（全量）"
  python3 gate_prototype.py || rc=1
  step "[full] gate_prototype --selftest（逐条负例）"
  python3 gate_prototype.py --selftest || rc=1
  step "[full] 数据侧自检 10-dag-data/_selfcheck.py"
  python3 10-dag-data/_selfcheck.py || rc=1
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
