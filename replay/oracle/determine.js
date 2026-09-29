'use strict';
/*
 * oref oracle — runs the REAL oref0 determine-basal as a pure decision function.
 *
 * We do not reimplement determine-basal (DESIGN §2); we call the pinned oref0 package
 * (see package.json) so every counterfactual is produced by the same code the user runs.
 *
 * Protocol: read one JSON object from stdin of the form
 *     { "requests": [ <req>, ... ] }
 * where each <req> has the determine_basal inputs:
 *     { glucose_status, currenttemp, iob_inputs, profile, autosens_data,
 *       meal_data, microBolusAllowed, reservoir_data, currentTime }
 * where iob_inputs = { history, profile, clock, tz } is handed to oref0's lib/iob (see
 * request.js),
 * and write { "results": [ <rT>, ... ] } (or { "error": "..."} ) to stdout.
 *
 * `currentTime` may be epoch-ms (number) or an ISO string; it is coerced to a Date.
 */

const { runAll } = require('./request');

function readStdin() {
  return new Promise((resolve, reject) => {
    let buf = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (d) => { buf += d; });
    process.stdin.on('end', () => resolve(buf));
    process.stdin.on('error', reject);
  });
}

(async () => {
  try {
    const raw = await readStdin();
    const payload = JSON.parse(raw);
    const requests = Array.isArray(payload) ? payload : (payload.requests || []);
    const results = runAll(requests);
    process.stdout.write(JSON.stringify({ results }));
  } catch (e) {
    process.stdout.write(JSON.stringify({ error: String(e && e.message ? e.message : e) }));
    process.exitCode = 1;
  }
})();
