/*
 * The engine, in a Web Worker: the Nightscout fetch, Pyodide with the Python packages, and
 * real oref0 (oref-bundle.js).
 *
 * It used to run on the page's main thread, where the settings tests held the page for about
 * two minutes on a week of data in Chrome and longer in Safari: the status line could not
 * update and the browser offered to stop the page. Here the page stays responsive and
 * receives a progress message as each step starts.
 *
 * Protocol: the page posts {id, op, args}; the worker answers {id, ok, value} or
 * {id, ok: false, error}, and posts {op: 'progress', text} at any time.
 */

const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/';
// The pinned digest of pyodide.js. A worker cannot use a script tag's integrity attribute, so
// the loader is fetched, hashed and only run when it matches. Regenerate on a version bump:
//   curl -sL <url> | openssl dgst -sha384 -binary | openssl base64 -A
const PYODIDE_SRI = 'sha384-tVslJOEkg7nVRW3Y3/ReGX0NnonNrbcmt1R5qFbQXQdGa2chRkoJYHAjAsv3zoTq';

importScripts('./oref-bundle.js', './nightscout.js');

let pyodide = null;
let B = null;

async function importVerified(url, sri) {
  const buf = await (await fetch(url)).arrayBuffer();
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-384', buf));
  const got = 'sha384-' + btoa(String.fromCharCode(...digest));
  if (got !== sri) throw new Error(`${url} failed its integrity check; not loading it.`);
  const blob = URL.createObjectURL(new Blob([buf], { type: 'text/javascript' }));
  try {
    importScripts(blob);
  } finally {
    URL.revokeObjectURL(blob);
  }
}

const progress = (text) => postMessage({ op: 'progress', text: String(text) });

function toJs(proxy) {
  const value = proxy.toJs({ dict_converter: Object.fromEntries });
  proxy.destroy();
  return value;
}

const ops = {
  async boot() {
    await importVerified(PYODIDE_CDN + 'pyodide.js', PYODIDE_SRI);
    pyodide = await loadPyodide({ indexURL: PYODIDE_CDN });
    const buf = await (await fetch('./odt-packages.zip')).arrayBuffer();
    await pyodide.unpackArchive(buf, 'zip');
    pyodide.runPython("import sys; sys.path.insert(0, '.'); import report.browser");
    B = pyodide.pyimport('report.browser');
    return true;
  },

  settings_from_raw({ raw }) {
    const rawPy = pyodide.toPy(raw);
    try {
      return toJs(B.settings_from_raw(rawPy));
    } finally {
      rawPy.destroy();
    }
  },

  // Fetch, then the deterministic report. The raw Nightscout data stays in this worker; the
  // page gets the report and the abstracted findings narration is allowed to see.
  async analyse({ url, token, days, settings, maxIob, jurisdiction }) {
    const raw = await fetchNightscout(url, token, days, progress);
    progress('Analysing…');
    const kwargs = { oref_runner: B.make_js_oref_runner() };
    if (settings) kwargs.settings = pyodide.toPy(settings);
    if (maxIob !== null && maxIob !== undefined) kwargs.max_iob_override = maxIob;
    kwargs.jurisdiction = jurisdiction || 'UK';
    const rawPy = pyodide.toPy(raw);
    let result;
    try {
      result = toJs(B.build_report.callKwargs(rawPy, kwargs));
    } finally {
      rawPy.destroy();
    }
    const resultPy = pyodide.toPy(result);
    try {
      return { report_md: result.report_md, source: toJs(B.abstracted_findings(resultPy)) };
    } finally {
      resultPy.destroy();
    }
  },

  settings_tests({ aim }) {
    return toJs(B.settings_tests.callKwargs({ progress, aim: aim || 'standard' })).report_md;
  },

  gate({ narrative, source }) {
    const sourcePy = pyodide.toPy(source);
    try {
      return toJs(B.gate_narrative(narrative, sourcePy));
    } finally {
      sourcePy.destroy();
    }
  },
};

self.onmessage = async ({ data }) => {
  const { id, op, args } = data;
  try {
    if (!ops[op]) throw new Error(`unknown engine operation ${op}`);
    postMessage({ id, ok: true, value: await ops[op](args || {}) });
  } catch (e) {
    postMessage({ id, ok: false, error: {
      message: String((e && e.message) || e),
      nightscout: typeof NightscoutError !== 'undefined' && e instanceof NightscoutError,
    } });
  }
};
