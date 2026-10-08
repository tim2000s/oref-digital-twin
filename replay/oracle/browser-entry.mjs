/*
 * Browser entry for the oref oracle. Bundled (esbuild) into web/oref-bundle.js, which
 * exposes globalThis.orefDetermine — the SAME real oref0 determine-basal used server-side,
 * now callable from the Pyodide app. Same request/result shape as oracle/determine.js.
 */
import request from './request.js';

// requests: array of determine-basal input objects. Returns [{ok, rt} | {ok:false, error}].
globalThis.orefDetermine = function orefDetermine(requests) {
  return request.runAll(requests);
};

// payload: {cycles, scenarios, max_gap_min}. Closed-loop scenario simulation (request.js).
globalThis.orefSimulate = function orefSimulate(payload) {
  return request.simulate(payload);
};
