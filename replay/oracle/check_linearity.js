'use strict';
/*
 * How far the simulator's linear basal scaling sits from oref0's own rebuild.
 *
 *   node check_linearity.js requests.json [every]
 *
 * requests.json is a list of determine-basal requests carrying iob_inputs (as built by
 * replay.inputs.from_cycle). For every `every`-th request (default 5) and k = 0.7 and 1.3 it
 * runs lib/iob with the basal schedule scaled by k, and compares that with
 * X(1) + (k - 1) * X0, X0 being the rebuild with boluses removed and temps at zero.
 */
const fs = require('fs');
const iobGenerate = require('oref0/lib/iob');

const reqs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const every = Number(process.argv[3] || 5);
const quiet = () => true;
const realWrite = process.stderr.write.bind(process.stderr);
process.stderr.write = quiet;
console.error = quiet;

const q = (a, p) => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(p * (s.length - 1))]; };
for (const k of [0.7, 1.3]) {
  const eff = [], err = [];
  reqs.forEach((r, i) => {
    if (i % every) return;
    const inp = r.iob_inputs;
    if (inp.tz) process.env.TZ = inp.tz;
    const scaled = { ...inp.profile, current_basal: inp.profile.current_basal * k,
      basalprofile: inp.profile.basalprofile.map((b) => ({ ...b, rate: b.rate * k })) };
    const direct = iobGenerate({ history: inp.history, profile: scaled, clock: inp.clock })[0];
    const one = iobGenerate({ history: inp.history, profile: inp.profile, clock: inp.clock })[0];
    const zero = iobGenerate({ history: inp.history.filter((h) => h._type !== 'Bolus')
      .map((h) => (h._type === 'TempBasal' ? { ...h, rate: 0 } : h)), profile: inp.profile, clock: inp.clock })[0];
    eff.push(Math.abs(direct.iob - one.iob));
    err.push(Math.abs(direct.iob - (one.iob + (k - 1) * zero.iob)));
  });
  process.stdout.write(`k=${k} n=${eff.length}: scaling moved IOB by median ${q(eff, 0.5).toFixed(3)} U; `
    + `linear form off by median ${q(err, 0.5).toFixed(3)} U, p95 ${q(err, 0.95).toFixed(3)} U, `
    + `max ${q(err, 1).toFixed(3)} U\n`);
}
process.stderr.write = realWrite;
