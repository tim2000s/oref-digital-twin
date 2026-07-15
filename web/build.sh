#!/usr/bin/env bash
# Bundle the pure-Python packages Pyodide loads in the browser.
# Produces web/odt-packages.zip (gitignored — a build artifact).
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="web/odt-packages.zip"
rm -f "$OUT"

# report/ pulls in ingestion, variant, diagnostics; settings and replay complete the set.
# replay/oracle/ (Node + oref0) is excluded — the browser runs oref0 via web/oref-bundle.js
# and injects a JS-backed runner. Tests and bytecode are excluded.
zip -r "$OUT" ingestion variant diagnostics report settings replay \
    -x '*/tests/*' '*/__pycache__/*' '*.pyc' 'replay/oracle/*' >/dev/null

echo "wrote $OUT"
