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

module.exports = { runOne, runAll };
