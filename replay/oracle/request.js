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
  // A temp target replaces the profile target, so a change to the profile target leaves it alone.
  if (sc.target_offset && !profile.temptargetSet) {
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
  // Optional pull-back of each dose's glucose effect, time constant decay_tau_min (off unless
  // given; the page does not set it). Measured in TimSim: glucose follows an insulin difference
  // for an hour or two, then returns with a time constant of about 2.4 h, where the shift without
  // this stays for the rest of the period (validation/DECAY.md).
  // shape[m] is a unit dose's effect m minutes on: its absorption, each part relaxing since.
  const tau = payload.decay_tau_min || 0;
  let shape = null;
  if (tau > 0) {
    const len = tab.n + Math.ceil(10 * tau) + 1;
    shape = new Float64Array(len);
    shape[0] = 1 - tab.left[0];
    const keepFrac = Math.exp(-1 / tau);
    for (let m = 1; m < len; m++) {
      shape[m] = shape[m - 1] * keepFrac + (m <= tab.n ? tab.left[m - 1] - tab.left[m] : 0);
    }
  }
  const absorbed = (m) => (shape ? (m < shape.length ? shape[m] : 0)
    : 1 - (m <= tab.n ? tab.left[m] : 0));
  const t = cycles.map((c) => c.currentTime);
  const gap = t.map((ti, i) => (i + 1 < t.length ? Math.min((t[i + 1] - ti) / 60000, maxGap) : 5));
  // the body's sensitivity at each cycle, as oref itself would take it
  const isf = cycles.map((c) => c.profile.sens / ((c.autosens_data && c.autosens_data.ratio) || 1));
  // Optional scale on the body's sensitivity, payload.body_isf_scale (1 unless given): each dose
  // difference acts with the profile ISF times this, while oref still doses with the profile ISF.
  // Rescue carbohydrate keeps the profile ISF, since its rise is a carbohydrate property.
  const isfScale = payload.body_isf_scale || 1;
  const bodyIsf = isf.map((v) => v * isfScale);
  // Optional body, payload.body = {model: "hovorka"} with any rate below overridden (off unless
  // given). Without it, a dose's effect is kept for the rest of the period. With it, the dose
  // still acts as units x ISF along the insulin curve, but the glucose offset it leaves is then
  // carried by the glucose system of Hovorka et al. 2004 at basal insulin: a plasma and a remote
  // compartment whose exchange and disposal depend on how much glucose there is, uptake not
  // driven by insulin that eases below 81 mg/dL, and renal loss above 162 mg/dL. The rates are
  // the medians of the 68 TimSim Hovorka subjects with titrated settings at their basal steady
  // state (validation/BODY_PLAN.md), per minute; f01 and renal are in mg/dL per minute.
  const H = payload.body ? { x1: 0.02772, x2: 0.00425, k12: 0.066, f01: 1.09125, renal: 0.003,
    ...payload.body } : null;
  if (H && H.model !== 'hovorka') throw new Error(`unknown body model ${H.model}`);
  if (H && tau > 0) throw new Error('body and decay_tau_min are alternatives; give one');
  const obsAt = (time) => {      // the logged glucose at `time`, linear between cycles
    let lo = 0, hi = t.length - 1;
    if (time <= t[0]) return cycles[0].glucose_status.glucose;
    if (time >= t[hi]) return cycles[hi].glucose_status.glucose;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (t[mid] <= time) lo = mid; else hi = mid; }
    const a = cycles[lo].glucose_status.glucose, b = cycles[hi].glucose_status.glucose;
    return a + (b - a) * (time - t[lo]) / (t[hi] - t[lo]);
  };
  // Optional rescue eating, payload.rescue = {grams, threshold, refractory_min, delay, rise_min,
  // mode} (off unless given; the page's settings tests give mode "new", replay/scenarios.py
  // RESCUE). A person below `threshold` eats `grams`
  // of fast carbohydrate, again every `refractory_min` while still low; each rises by grams x ISF
  // / carb ratio at that cycle, after `delay` minutes and over `rise_min`. Mode "both" applies the
  // rule to the real glucose too, so the shifted trace loses the real trace's rescues where its
  // lows are gone (the two cancel exactly when the times agree); mode "new" treats only lows the
  // real glucose did not have.
  const rescue = payload.rescue || null;
  let rescueShape = null;
  const realRescues = [];
  // the spacing allows a minute's slack: loop cycles drift by seconds, so a strict 15 would wait 20
  const rescueRise = (i) => (cycles[i].profile.carb_ratio ? rescue.grams * isf[i] / cycles[i].profile.carb_ratio : 0);
  if (rescue) {
    const delay = Math.round(rescue.delay), riseMin = Math.max(1, Math.round(rescue.rise_min));
    rescueShape = new Float64Array(delay + riseMin + (tau > 0 ? Math.ceil(10 * tau) : 0) + 1);
    const keepFrac = tau > 0 ? Math.exp(-1 / tau) : 1;
    for (let m = 1; m < rescueShape.length; m++) {
      const ramp = (m - 1 >= delay && m - 1 < delay + riseMin) ? 1 / riseMin : 0;
      rescueShape[m] = rescueShape[m - 1] * keepFrac + ramp;
    }
    if (rescue.mode !== 'new') {
      let last = -Infinity;
      cycles.forEach((c, i) => {
        if (c.glucose_status.glucose < rescue.threshold && t[i] - last >= (rescue.refractory_min - 1) * 60000) {
          realRescues.push({ t: t[i], rise: rescueRise(i) });
          last = t[i];
        }
      });
    }
  }
  const rescueEffect = (list, time) => {
    let e = 0;
    for (const r of list) {
      if (r.t > time) break;
      const m = Math.round((time - r.t) / 60000);
      e += r.rise * (m < rescueShape.length ? rescueShape[m] : (tau > 0 ? 0 : 1));
    }
    return e;
  };

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
      return bodyIsf[j];
    };
    for (const d of doses) d.isf = isfAt(d.t);

    const ownRescues = [];
    let lastRescue = -Infinity;

    function effectAt(time) {
      let e = 0;
      for (const d of live) {
        if (d.t > time) continue;
        const m = Math.round((time - d.t) / 60000);
        e -= d.u * d.isf * absorbed(m);
      }
      if (rescue) e += rescueEffect(ownRescues, time) - rescueEffect(realRescues, time);
      return e;
    }

    // The body: offsets b1 (plasma) and b2 (remote) from the logged glucose, integrated in steps
    // of about a minute up to each cycle. The input is each live dose's action in that minute and
    // the rescues' rise, so the offset follows the doses as without the body, while the body pulls
    // it back by how far, and from what level, glucose has been moved.
    let b1 = 0, b2 = 0, bt = null;
    const bHist = [];
    const rescueRate = (list, time) => {
      let e = 0;
      for (const r of list) {
        if (r.t > time) break;
        const m = Math.floor((time - r.t) / 60000) + 1;
        if (m < rescueShape.length) e += r.rise * (rescueShape[m] - rescueShape[m - 1]);
      }
      return e;
    };
    const inputAt = (time) => {
      let r = 0;
      for (const d of live) {
        if (d.t > time) continue;
        const m = Math.floor((time - d.t) / 60000) + 1;
        if (m <= tab.n) r -= d.u * d.isf * (tab.left[m - 1] - tab.left[m]);
      }
      if (rescue) r += rescueRate(ownRescues, time) - rescueRate(realRescues, time);
      return r;
    };
    const advance = (to) => {
      if (bt === null) { bt = to; bHist.push([to, 0]); return 0; }
      const steps = Math.max(1, Math.round((to - bt) / 60000));
      const h = (to - bt) / steps;
      for (let k = 0; k < steps; k++) {
        const tm = bt + h * (k + 0.5);
        const g = obsAt(tm);
        const f = H.f01 * (Math.min(1, Math.max(0, g + b1) / 81) - Math.min(1, g / 81));
        const r = H.renal * (Math.max(0, g + b1 - 162) - Math.max(0, g - 162));
        const d1 = -H.x1 * b1 + H.k12 * b2 - f - r + inputAt(tm);
        const d2 = H.x1 * b1 - (H.k12 + H.x2) * b2;
        b1 += (h / 60000) * d1;
        b2 += (h / 60000) * d2;
      }
      bt = to;
      bHist.push([to, b1]);
      return b1;
    };
    const bodyAt = (time) => {   // the offset at an earlier time, linear between cycles
      let j = bHist.length - 1;
      while (j > 0 && bHist[j][0] > time) j--;
      if (bHist[j][0] > time) return 0;
      if (j === bHist.length - 1) return bHist[j][1];
      const [ta, va] = bHist[j], [tb, vb] = bHist[j + 1];
      return va + (vb - va) * (time - ta) / (tb - ta);
    };
    const past = (time) => (H ? bodyAt(time) : settled + effectAt(time));

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
        const age = (now - d.t) / 60000;
        if (H) {
          if (age <= tab.n + 60) keep.push(d);                 // the body now carries its effect
        } else if (shape) {
          if (age < shape.length + 60) keep.push(d);          // its effect has relaxed to nothing
        } else if (age > tab.n + 60) settled -= d.u * d.isf; else keep.push(d);
      }
      live = keep;

      let shift = H ? advance(now) : settled + effectAt(now);
      const gs0 = c.glucose_status;
      if (rescue && gs0.glucose + shift < rescue.threshold && now - lastRescue >= (rescue.refractory_min - 1) * 60000
          && (rescue.mode !== 'new' || gs0.glucose >= rescue.threshold)) {
        ownRescues.push({ t: now, rise: rescueRise(i) });
        lastRescue = now;
        if (!H) shift = settled + effectAt(now);            // the body takes a rescue as later input
      }
      // Left untouched when nothing has shifted, so a scenario that changes nothing gives the
      // baseline decision exactly.
      const gs = shift === 0 ? gs0 : {
        ...gs0,
        glucose: Math.max(39, gs0.glucose + shift),
        delta: gs0.delta + shift - past(now - 5 * 60000),
        short_avgdelta: gs0.short_avgdelta + (shift - past(now - 15 * 60000)) / 3,
        long_avgdelta: gs0.long_avgdelta + (shift - past(now - 45 * 60000)) / 9,
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
      if (Math.abs(dSmb) > 1e-4) live.push({ t: now, u: dSmb, bolus: true, isf: bodyIsf[i] });
      // a basal difference is spread over the gap; it is entered at the gap's midpoint
      if (Math.abs(dBasal) > 1e-4) live.push({ t: now + gap[i] * 30000, u: dBasal, bolus: false, isf: bodyIsf[i] });
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
