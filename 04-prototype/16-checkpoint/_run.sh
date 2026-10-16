#!/bin/sh
# _run.sh —— 门控/构建的调用包装。
#
# 为什么需要它：本会话的 run_gate 工具只接受「脚本路径 + argv 数组」，不接受管道/重定向/链式命令，
# 也不解析 shell 语法。故把「切到 16-checkpoint/ 再执行给定命令」这一固定动作固化成脚本，
# 使 `run_gate(path=_run.sh, args=["python3","gate_prototype.py"])` 等价于
# `cd 16-checkpoint && python3 gate_prototype.py`。
#
# ⛔ 本文件不参与产物生成（不在 build-all.GENERATORS 内），也不定义 page_shell（P15 不受影响）。
set -e
cd "$(dirname "$0")" || exit 1
exec "$@"
