#!/usr/bin/env bash
# Regenerate web/oref-bundle.js — real oref0 determine-basal bundled for the browser.
# The committed bundle is vendored so Pages/local serving work without a build step; run
# this to refresh it (e.g. after bumping the pinned oref0 version).
set -euo pipefail
cd "$(dirname "$0")/../replay/oracle"

npm install --no-audit --no-fund >/dev/null   # pinned oref0 (see package.json)
# --inject the process shim: oref0 writes its reasoning to process.stderr, which does not
# exist in the browser, and without this every determine-basal call throws immediately.
npx --yes esbuild browser-entry.mjs --bundle --format=iife --platform=browser \
    --inject:./process-shim.mjs \
    --outfile=../../web/oref-bundle.js
echo "wrote web/oref-bundle.js"

# Guard: prove the bundle actually evaluates a request. A textual check is not enough —
# the shim leaves `process.stderr` in the source and merely rebinds `process` to an
# IIFE-scoped var — so run determine-basal for real and require a decision back. The var
# shadows Node's own global, so this exercises the shim rather than bypassing it.
node --input-type=module -e "
  import { readFileSync } from 'node:fs';
  new Function(readFileSync('../../web/oref-bundle.js', 'utf8'))();
  // The regression case from replay/tests/test_oracle_integration.py: 180 mg/dL rising 8 per
  // 5 min, 3 U an hour ago. With oref's own IOB projection the temp is 0.13 U/h; handed a
  // single IOB object oref lost its predictions and ran 2.45 U/h.
  const now = Date.parse('2025-09-20T14:00:00Z');
  const req = {
    glucose_status: { glucose: 180, delta: 8, short_avgdelta: 8, long_avgdelta: 8, date: now },
    currenttemp: { duration: 0, rate: 0, temp: 'absolute' },
    iob_inputs: { history: [{ _type: 'Bolus', amount: 3, timestamp: new Date(now - 3600e3).toISOString() }],
                  profile: { dia: 6, curve: 'rapid-acting', current_basal: 1.0,
                             basalprofile: [{ i: 0, start: '00:00:00', minutes: 0, rate: 1.0 }] },
                  clock: new Date(now).toISOString() },
    profile: { dia: 6, current_basal: 1.0, max_basal: 3, max_daily_basal: 1.0,
               max_daily_safety_multiplier: 3, current_basal_safety_multiplier: 4,
               max_iob: 6, sens: 50, carb_ratio: 10, min_bg: 100, max_bg: 100,
               target_bg: 100, min_5m_carbimpact: 8, type: 'current', enableSMB_always: true,
               maxSMBBasalMinutes: 30, maxUAMSMBBasalMinutes: 30 },
    autosens_data: { ratio: 1.0 }, meal_data: { carbs: 0, mealCOB: 0 },
    microBolusAllowed: true, currentTime: now,
  };
  const [r] = globalThis.orefDetermine([req]);
  if (!r || !r.ok) { console.error('ERROR: bundle failed to evaluate:', r && r.error); process.exit(1); }
  if (r.iob_steps !== 48 || /minPredBG 999/.test(r.rt.reason) || !(r.rt.rate < 0.5)) {
    console.error('ERROR: bundle ran without the IOB projection:', r.iob_steps, r.rt.rate, r.rt.reason);
    process.exit(1);
  }
  console.error('bundle smoke test OK: 48-step IOB, rate ' + r.rt.rate + ', duration ' + r.rt.duration);
"
