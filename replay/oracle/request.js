'use strict';
/*
 * One determine-basal request, run through the real oref0. Shared by the Node oracle
 * (determine.js) and the browser bundle (browser-entry.mjs) so the two cannot drift.
 *
 * determine-basal walks a 48-step insulin-on-board projection to build its predicted-glucose
 * curves. Given a single IOB object it throws inside a try block, leaves minPredBG and
 * minGuardBG at 999 and so switches off its own low-glucose guard. The projection is
 * therefore built here by oref0's own lib/iob from `iob_inputs` (pump history, the insulin
 * profile and the clock). A request that carries only a single `iob_data` object is refused
 * rather than run.
 */

const determine_basal = require('oref0/lib/determine-basal/determine-basal');
const tempBasalFunctions = require('oref0/lib/basal-set-temp');
const iobGenerate = require('oref0/lib/iob');

function iobArray(req) {
  const inputs = req.iob_inputs;
  if (inputs) {
    // lib/iob splits temp basals on the basal schedule by local clock hour, so the runtime's
    // zone must be the user's. Node honours a runtime change to TZ; a browser runs in its own.
    if (inputs.tz && typeof process !== 'undefined' && process.env && process.versions &&
        process.versions.node) {
      process.env.TZ = inputs.tz;
    }
    return iobGenerate({ history: inputs.history || [], profile: inputs.profile,
                         clock: inputs.clock });
  }
  if (Array.isArray(req.iob_data) && req.iob_data.length > 1) {
    return req.iob_data;
  }
  throw new Error('no insulin-on-board projection: send iob_inputs (pump history), '
                  + 'not a single iob_data object, or oref disables its low-glucose guard');
}

function runOne(req) {
  const currentTime = req.currentTime != null ? new Date(req.currentTime) : new Date();
  const iob = iobArray(req);
  const rt = determine_basal(
    req.glucose_status,
    req.currenttemp,
    iob,
    req.profile,
    req.autosens_data || { ratio: 1.0 },
    req.meal_data || {},
    tempBasalFunctions,
    req.microBolusAllowed === true,
    req.reservoir_data,
    currentTime
  );
  return { rt, iob_rebuilt: iob[0] ? iob[0].iob : null, iob_steps: iob.length };
}

function runAll(requests) {
  return (requests || []).map((req, i) => {
    try {
      const out = runOne(req);
      return { ok: true, rt: out.rt, iob_rebuilt: out.iob_rebuilt, iob_steps: out.iob_steps };
    } catch (e) {
      return { ok: false, index: i, error: String(e && e.message ? e.message : e) };
    }
  });
}

// --- Closed-loop scenario simulation -------------------------------------------------
//
// determine-basal answers "what would the loop do now", given the glucose and insulin on board
// it sees. A settings scenario changes that answer at every cycle, and the changed doses change
// the glucose and insulin on board the loop sees at the next one. simulate() walks the cycles
// in time order and carries both forward:
//
//   * the insulin difference from every earlier cycle is added to the insulin-on-board
//     projection with oref0's own insulin curve (lib/iob/calculate), and
//   * it shifts glucose by (units x ISF x the fraction of that insulin's action already
//     done), the same arithmetic oref uses for its own BGI.
//
// The glucose shift is a model, not a measurement: it takes the profile ISF (adjusted by
// autosens, as oref does) as the body's real sensitivity and assumes meals, exercise and the
// person's own treatments would have been the same. Nothing here is a glucodynamic simulator.
//
// Insulin on board is the expensive part (oref0 lib/iob, about 5.6 ms a cycle against 0.03 ms
// for determine-basal) and it is linear in the basal schedule: lib/iob nets each temp basal
// against the scheduled rate, so with the schedule scaled by k, very nearly
//     X(k) = X(1) + (k - 1) * X0,
// where X0 is lib/iob run on the same history with every bolus removed and every temp rate set
// to zero (it holds for iob, activity and the zero-temp projection alike). Each cycle therefore
// costs two lib/iob runs however many scenarios are tried.

function insulinDefaults(iobProfile) {
  // Mirrors lib/iob/total.js: the curve, the minimum DIA it forces and the default peak.
  let curve = String(iobProfile.curve || 'bilinear').toLowerCase();
  const defaults = { bilinear: [false, 75], 'rapid-acting': [true, 75], 'ultra-rapid': [true, 55] };
  if (!(curve in defaults)) curve = 'rapid-acting';
  let dia = Math.max(iobProfile.dia || 3, 3);
  if (defaults[curve][0] && dia < 5) dia = 5;
  return { curve, dia, peak: defaults[curve][1] };
}

// Per-minute tables for one unit: insulin still on board, and activity (U/min).
function curveTables(iobProfile) {
  const iobCalc = require('oref0/lib/iob/calculate');
  const { curve, dia, peak } = insulinDefaults(iobProfile);
  const n = Math.round(dia * 60);
  const left = new Float64Array(n + 1);
  const act = new Float64Array(n + 1);
  for (let m = 0; m <= n; m++) {
    const r = iobCalc({ insulin: 1, date: 0 }, new Date(m * 60000), curve, dia, peak, iobProfile);
    left[m] = r.iobContrib || 0;
    act[m] = r.activityContrib || 0;
  }
  return { left, act, n };
}

function zeroHistory(history) {
  return (history || []).filter((h) => h._type !== 'Bolus')
    .map((h) => (h._type === 'TempBasal' ? { ...h, rate: 0 } : h));
}

function iobFor(inputs, history) {
  if (inputs.tz && typeof process !== 'undefined' && process.env && process.versions &&
      process.versions.node) {
    process.env.TZ = inputs.tz;
  }
  return iobGenerate({ history, profile: inputs.profile, clock: inputs.clock });
}

// Insulin delivered from this decision until the next cycle, `gapMin` minutes later. A
// decision without a running temp leaves the scheduled basal on.
function delivered(rt, scheduled, gapMin) {
  const smb = (rt && typeof rt.units === 'number') ? rt.units : 0;
  if (rt && typeof rt.rate === 'number' && rt.duration > 0) {
    const d = Math.min(rt.duration, gapMin);
    return { smb, basal: (rt.rate * d + scheduled * Math.max(gapMin - d, 0)) / 60 };
  }
  return { smb, basal: scheduled * gapMin / 60 };
}

function applyScenario(profile, sc) {
  const p = { ...profile };
  const k = sc.basal_scale || 1;
  if (k !== 1) {
    p.current_basal = profile.current_basal * k;
    p.max_daily_basal = profile.max_daily_basal * k;
  }
  if (sc.isf_scale && sc.isf_scale !== 1) p.sens = profile.sens * sc.isf_scale;
  if (sc.cr_scale && sc.cr_scale !== 1) p.carb_ratio = profile.carb_ratio * sc.cr_scale;
  if (sc.target_offset) {
    for (const f of ['min_bg', 'max_bg', 'target_bg']) p[f] = profile[f] + sc.target_offset;
  }
  Object.assign(p, sc.profile_set || {});
  return p;
}

let simCache = null;

function simulate(payload) {
  // Calls that share a cache_key may omit the cycles after the first; they are kept here.
  const key = payload.cache_key || null;
  if (!key || !simCache || simCache.key !== key) {
    simCache = { key, cycles: payload.cycles || [], iob1: null, iob0: null };
  }
  const cycles = payload.cycles || simCache.cycles;
  const scenarios = payload.scenarios || [];
  const maxGap = payload.max_gap_min || 30;
  if (!cycles.length) return { baseline: [], scenarios: [] };
  const tab = curveTables(cycles[0].iob_inputs.profile);
  const t = cycles.map((c) => c.currentTime);
  const gap = t.map((ti, i) => (i + 1 < t.length ? Math.min((t[i + 1] - ti) / 60000, maxGap) : 5));
  // the body's sensitivity at each cycle, as oref itself would take it
  const isf = cycles.map((c) => c.profile.sens / ((c.autosens_data && c.autosens_data.ratio) || 1));

  // The two lib/iob runs per cycle are kept between calls that share a cache_key, which is
  // what lets a report run its stages one after another without repeating them.
  if (!simCache.iob1) simCache.iob1 = cycles.map((c) => iobFor(c.iob_inputs, c.iob_inputs.history));
  const iob1 = simCache.iob1;
  const needZero = scenarios.some((s) => (s.basal_scale || 1) !== 1);
  if (needZero && !simCache.iob0) {
    simCache.iob0 = cycles.map((c) => iobFor(c.iob_inputs, zeroHistory(c.iob_inputs.history)));
  }
  const iob0 = needZero ? simCache.iob0 : null;

  function decide(i, gs, iobArr, profile) {
    try {
      return determine_basal(gs, cycles[i].currenttemp, iobArr, profile,
        cycles[i].autosens_data || { ratio: 1.0 }, cycles[i].meal_data || {},
        tempBasalFunctions, cycles[i].microBolusAllowed === true, cycles[i].reservoir_data,
        new Date(cycles[i].currentTime));
    } catch (e) {
      return null;
    }
  }

  const base = cycles.map((c, i) => {
    const rt = decide(i, c.glucose_status, iob1[i], c.profile);
    return rt ? delivered(rt, c.profile.current_basal, gap[i]) : null;
  });

  const out = scenarios.map((sc) => {
    const k = sc.basal_scale || 1;
    // doses the scenario adds or removes: {t, u, bolus, isf}
    const doses = (sc.extra_doses || []).map((d) => ({ t: d.t, u: d.u, bolus: true, isf: null }));
    let settled = 0;            // glucose effect of doses whose action is complete
    let live = [];
    let next = 0;               // extra doses not yet admitted, kept in time order
    doses.sort((a, b) => a.t - b.t);
    const isfAt = (time) => {
      let j = 0;
      while (j + 1 < t.length && t[j + 1] <= time) j++;
      return isf[j];
    };
    for (const d of doses) d.isf = isfAt(d.t);

    function effectAt(time) {
      let e = 0;
      for (const d of live) {
        if (d.t > time) continue;
        const m = Math.round((time - d.t) / 60000);
        e -= d.u * d.isf * (1 - (m <= tab.n ? tab.left[m] : 0));
      }
      return e;
    }

    const du = new Array(cycles.length).fill(null);
    const dbg = new Array(cycles.length).fill(null);
    let failed = 0;
    for (let i = 0; i < cycles.length; i++) {
      const c = cycles[i];
      const now = t[i];
      while (next < doses.length && doses[next].t <= now) live.push(doses[next++]);
      // retire doses whose action is complete into the settled sum
      const keep = [];
      for (const d of live) {
        if ((now - d.t) / 60000 > tab.n + 60) settled -= d.u * d.isf; else keep.push(d);
      }
      live = keep;

      const shift = settled + effectAt(now);
      const gs0 = c.glucose_status;
      // Left untouched when nothing has shifted, so a scenario that changes nothing gives the
      // baseline decision exactly.
      const gs = shift === 0 ? gs0 : {
        ...gs0,
        glucose: Math.max(39, gs0.glucose + shift),
        delta: gs0.delta + shift - (settled + effectAt(now - 5 * 60000)),
        short_avgdelta: gs0.short_avgdelta + (shift - (settled + effectAt(now - 15 * 60000))) / 3,
        long_avgdelta: gs0.long_avgdelta + (shift - (settled + effectAt(now - 45 * 60000))) / 9,
      };

      // insulin on board: the logged history at this basal scale, plus every dose difference
      const arr = iob1[i].map((tick, s) => {
        const z = iob0 ? iob0[i][s] : null;
        const at = now + s * 5 * 60000;
        let di = 0, da = 0, dBolus = 0;
        for (const d of live) {
          if (d.t > at) continue;
          const m = Math.round((at - d.t) / 60000);
          if (m > tab.n) continue;
          di += d.u * tab.left[m];
          da += d.u * tab.act[m];
          if (d.bolus) dBolus += d.u * tab.left[m];
        }
        const lin = (field, src, zsrc) => (src[field] || 0) + (k - 1) * (zsrc ? (zsrc[field] || 0) : 0);
        const zt = tick.iobWithZeroTemp || {};
        const zz = z ? (z.iobWithZeroTemp || {}) : null;
        const res = {
          ...tick,
          iob: lin('iob', tick, z) + di,
          activity: lin('activity', tick, z) + da,
          basaliob: lin('basaliob', tick, z) + (di - dBolus),
          bolusiob: lin('bolusiob', tick, z) + dBolus,
          iobWithZeroTemp: { ...zt, iob: lin('iob', zt, zz) + di, activity: lin('activity', zt, zz) + da },
        };
        return res;
      });

      const profile = applyScenario(c.profile, sc);
      const rt = decide(i, gs, arr, profile);
      dbg[i] = Math.round(shift * 10) / 10;
      if (!rt || !base[i]) { failed++; continue; }
      const alt = delivered(rt, profile.current_basal, gap[i]);
      const dSmb = alt.smb - base[i].smb;
      const dBasal = alt.basal - base[i].basal;
      du[i] = Math.round((dSmb + dBasal) * 1000) / 1000;
      if (Math.abs(dSmb) > 1e-4) live.push({ t: now, u: dSmb, bolus: true, isf: isf[i] });
      // a basal difference is spread over the gap; it is entered at the gap's midpoint
      if (Math.abs(dBasal) > 1e-4) live.push({ t: now + gap[i] * 30000, u: dBasal, bolus: false, isf: isf[i] });
    }
    return { label: sc.label, du, dbg, failed };
  });

  return {
    t,
    baseline: base.map((b) => (b ? Math.round((b.smb + b.basal) * 1000) / 1000 : null)),
    scenarios: out,
  };
}

module.exports = { runOne, runAll, simulate };
