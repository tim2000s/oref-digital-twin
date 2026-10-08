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

const { runAll, simulate } = require('./request');

function readStdin() {
  return new Promise((resolve, reject) => {
    let buf = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (d) => { buf += d; });
    process.stdin.on('end', () => resolve(buf));
    process.stdin.on('error', reject);
  });
}

// --serve: one JSON request per stdin line, one JSON reply per stdout line, for as long as
// stdin stays open. The simulator's insulin-on-board cache lives in this process, so a report
// that runs its stages in sequence pays for it once.
if (process.argv.includes('--serve')) {
  const rl = require('readline').createInterface({ input: process.stdin });
  const out = process.stdout;
  rl.on('line', (line) => {
    if (!line.trim()) return;
    let reply;
    try {
      const payload = JSON.parse(line);
      reply = payload.simulate ? { simulation: simulate(payload.simulate) }
                               : { results: runAll(payload.requests || []) };
    } catch (e) {
      reply = { error: String(e && e.message ? e.message : e) };
    }
    out.write(JSON.stringify(reply) + '\n');
  });
  return;
}

(async () => {
  try {
    const raw = await readStdin();
    const payload = JSON.parse(raw);
    if (payload && payload.simulate) {
      process.stdout.write(JSON.stringify({ simulation: simulate(payload.simulate) }));
      return;
    }
    const requests = Array.isArray(payload) ? payload : (payload.requests || []);
    const results = runAll(requests);
    process.stdout.write(JSON.stringify({ results }));
  } catch (e) {
    process.stdout.write(JSON.stringify({ error: String(e && e.message ? e.message : e) }));
    process.exitCode = 1;
  }
})();
