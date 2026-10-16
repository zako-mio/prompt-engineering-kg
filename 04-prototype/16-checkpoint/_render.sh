#!/usr/bin/env bash
# 便捷入口：真实渲染 04-prototype 站点为 PNG
#
#   ./_run.sh 04-prototype/index.html 1440 900 out.png
#
# 或直接调用通道本体：
#   python3 _render.py --html 04-prototype/index.html --width 1440 --height 900 --out out.png
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="${1:?用法: _run.sh <html> [width] [height] [out.png]}"
W="${2:-1440}"; H="${3:-900}"
OUT="${4:-$HERE/_render-proof/$(basename "${HTML%.html}").png}"
exec python3 "$HERE/_render.py" --html "$HTML" --width "$W" --height "$H" \
     --out "$OUT" --json "${OUT%.png}.manifest.json"
