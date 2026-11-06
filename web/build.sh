#!/usr/bin/env bash
# Bundle the pure-Python packages Pyodide loads in the browser.
# Produces web/odt-packages.zip (gitignored — a build artifact).
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="web/odt-packages.zip"
rm -f "$OUT"

# The client-side AAPS decryptor lives in settings/decrypt/ (tested there); copy it next to
# the web app so the browser can import it. (Copy is gitignored.)
cp settings/decrypt/aaps_prefs.mjs web/aaps_prefs.mjs

# The in-browser narrator (narrator.js) runs WebLLM. The page's CSP only allows script from
# its own origin, so the library is fetched here, checked against a pinned SHA-384 and served
# from the site. Regenerate the digest on a version bump:
#   curl -sL <url> | openssl dgst -sha384 -binary | openssl base64 -A
WEBLLM_URL="https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.85/lib/index.js"
WEBLLM_SHA384="rfElDdXnNkSgbLTTGiKHTrsetCVAYzzLZBD96/rZdD9XYvryEyShqz3ph8j+x7HH"
curl -fsSL "$WEBLLM_URL" -o web/web-llm.js
got="$(openssl dgst -sha384 -binary web/web-llm.js | openssl base64 -A)"
if [ "$got" != "$WEBLLM_SHA384" ]; then
  rm -f web/web-llm.js
  echo "web-llm.js failed its integrity check (got $got)" >&2
  exit 1
fi

# report/ pulls in ingestion, variant, diagnostics; settings and replay complete the set.
# replay/oracle/ (Node + oref0) is excluded — the browser runs oref0 via web/oref-bundle.js
# and injects a JS-backed runner. Tests and bytecode are excluded.
zip -r "$OUT" ingestion variant diagnostics report settings replay \
    -x '*/tests/*' '*/__pycache__/*' '*.pyc' 'replay/oracle/*' >/dev/null

echo "wrote $OUT"
