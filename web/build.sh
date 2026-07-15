#!/usr/bin/env bash
# Bundle the pure-Python packages Pyodide loads in the browser.
# Produces web/odt-packages.zip (gitignored — a build artifact).
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="web/odt-packages.zip"
rm -f "$OUT"

# report/ pulls in ingestion, variant, diagnostics; settings is included for completeness.
# replay/ is intentionally excluded — its counterfactual needs oref0 (JS), a documented
# follow-up to run in-browser. Tests and bytecode are excluded.
zip -r "$OUT" ingestion variant diagnostics report settings \
    -x '*/tests/*' '*/__pycache__/*' '*.pyc' >/dev/null

echo "wrote $OUT"
