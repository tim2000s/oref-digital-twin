#!/usr/bin/env bash
# Regenerate web/oref-bundle.js — real oref0 determine-basal bundled for the browser.
# The committed bundle is vendored so Pages/local serving work without a build step; run
# this to refresh it (e.g. after bumping the pinned oref0 version).
set -euo pipefail
cd "$(dirname "$0")/../replay/oracle"

npm install --no-audit --no-fund >/dev/null   # pinned oref0 (see package.json)
npx --yes esbuild browser-entry.mjs --bundle --format=iife --platform=browser \
    --outfile=../../web/oref-bundle.js
echo "wrote web/oref-bundle.js"
