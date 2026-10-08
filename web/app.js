/*
 * Browser glue for the oref digital twin.
 *
 * Everything runs client-side: the browser fetches Nightscout directly (token + CORS stay
 * here), Pyodide runs the read-only Python pipeline, and the deterministic report renders
 * with no network. Optional narration goes to the Cloudflare Worker, and its response is
 * re-verified by the grounding gate (also in Pyodide) before it is shown.
 */

import { NARRATOR_URL } from './config.js';
import { loadSettingsFromFile } from './settings.js';

const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/';
const PACKAGES_ZIP = './odt-packages.zip';

const DAY_MS = 86_400_000;
const $ = (id) => document.getElementById(id);
const setStatus = (t) => ($('status').textContent = t);

let pyodide = null;

async function boot() {
  pyodide = await loadPyodide({ indexURL: PYODIDE_CDN });
  const buf = await (await fetch(PACKAGES_ZIP)).arrayBuffer();
  await pyodide.unpackArchive(buf, 'zip');           // unpacks package dirs into the cwd
  pyodide.runPython("import sys; sys.path.insert(0, '.'); import report.browser");
  setStatus('Ready.');
  $('run').disabled = false;
}

// --- Nightscout fetch ---
//
// Self-hosted Nightscout is often slow (a two-day devicestatus query was measured at 10 s
// on one try and 57 s on the next, on the same site) and usually sits behind nginx, whose
// default upstream timeout is 60 s. When nginx gives up it answers with its own 504 page,
// which carries no CORS header, so the browser reports a bare "Failed to fetch" even
// though CORS is enabled on Nightscout itself. The fetch is therefore built to keep every
// request small, to retry a failed one, and to split a window that keeps failing.
// devicestatus is the heavy stream (about 20 MB a day uncompressed for one AAPS user).

const STREAMS = [
  { key: 'entries', path: 'entries.json', field: 'date', iso: false, windowDays: 2 },
  { key: 'treatments', path: 'treatments.json', field: 'created_at', iso: true, windowDays: 7 },
  { key: 'devicestatus', path: 'devicestatus.json', field: 'created_at', iso: true, windowDays: 1 },
];
const PER_WINDOW_COUNT = 50000;
const MAX_ATTEMPTS = 3;                  // per window, before it is split
const MIN_WINDOW_MS = 3 * 3600_000;      // stop splitting below three hours
const REQUEST_TIMEOUT_MS = 120_000;      // longer than any proxy timeout we expect to meet
const CONCURRENCY = 2;                   // concurrent queries slow a small server further

class NightscoutError extends Error {
  constructor(message, { retryable = false } = {}) {
    super(message);
    this.retryable = retryable;
  }
}

// Accepts what people actually paste: no scheme, a capitalised scheme, a trailing slash or
// a copied #fragment. http:// cannot work from an https page, so say so.
function normaliseBase(input) {
  let s = input.trim();
  if (!s) throw new NightscoutError('Enter your Nightscout address.');
  if (!/^[a-z]+:\/\//i.test(s)) s = 'https://' + s;
  let u;
  try { u = new URL(s); } catch { throw new NightscoutError(`"${input}" is not a web address.`); }
  if (u.protocol !== 'https:') {
    throw new NightscoutError('The Nightscout address must start with https://. Browsers block '
      + 'plain http requests from this page.');
  }
  return u.origin + u.pathname.replace(/\/+$/, '');
}

const sleep = (ms) => new Promise((res) => setTimeout(res, ms));
const fmtDay = (ms) => new Date(ms).toISOString().slice(0, 16).replace('T', ' ');

async function nsGet(base, path, params, token) {
  const u = new URL(`${base}/api/v1/${path}`);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  if (token) u.searchParams.set('token', token);
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), REQUEST_TIMEOUT_MS);
  let r;
  try {
    r = await fetch(u, { headers: { accept: 'application/json' }, signal: ctl.signal });
  } catch (e) {
    // A CORS block, a proxy timeout without CORS headers, a dropped connection and a DNS
    // failure all arrive here as the same TypeError; the browser does not say which.
    throw new NightscoutError(ctl.signal.aborted ? 'timed out' : 'no response', { retryable: true });
  } finally {
    clearTimeout(timer);
  }
  if (r.status === 401 || r.status === 403) {
    throw new NightscoutError('Nightscout rejected the token (401/403). Use a token with the '
      + 'readable role from Admin Tools.');
  }
  if (r.status === 429 || r.status >= 500) throw new NightscoutError(`HTTP ${r.status}`, { retryable: true });
  if (!r.ok) throw new NightscoutError(`Nightscout ${path} returned HTTP ${r.status}.`);
  try {
    return await r.json();
  } catch {
    throw new NightscoutError(`Nightscout ${path} did not return JSON. Check the address points at `
      + 'the Nightscout site itself.');
  }
}

// Retries a request that got no usable reply, with backoff. Errors that retrying cannot fix
// (a rejected token, a page that is not JSON) go straight through.
async function withRetry(call, label, progress) {
  let last;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
      return await call();
    } catch (e) {
      if (!e.retryable) throw e;
      last = e;
      if (attempt < MAX_ATTEMPTS) {
        progress.note(`no reply for ${label}, retrying`);
        await sleep(2000 * 2 ** (attempt - 1));
      }
    }
  }
  throw last;
}

function tooSlow(what, last) {
  return new NightscoutError(
    `Nightscout stopped responding while sending ${what} (${last.message}, after ${MAX_ATTEMPTS} `
    + 'attempts). The address and CORS were fine for earlier requests, so the server is most '
    + 'likely too slow for its proxy: behind nginx the default limit is 60 s, and raising '
    + 'proxy_read_timeout fixes it. Fewer days also helps.');
}

async function fetchWindow(base, token, spec, lo, hi, progress) {
  const params = {
    [`find[${spec.field}][$gte]`]: spec.iso ? new Date(lo).toISOString() : lo,
    [`find[${spec.field}][$lte]`]: spec.iso ? new Date(hi).toISOString() : hi,
    count: PER_WINDOW_COUNT,
  };
  try {
    const docs = await withRetry(() => nsGet(base, spec.path, params, token),
      `${spec.key} from ${fmtDay(lo)}`, progress);
    return Array.isArray(docs) ? docs : [];
  } catch (e) {
    if (!e.retryable) throw e;
    // A window that keeps failing is usually one the server cannot answer inside its proxy
    // timeout, so ask for half as much at a time.
    if (hi - lo <= MIN_WINDOW_MS) throw tooSlow(`${spec.key} for ${fmtDay(lo)} to ${fmtDay(hi)} UTC`, e);
    const mid = lo + Math.floor((hi - lo) / 2);
    progress.split();
    const first = await fetchWindow(base, token, spec, lo, mid, progress);
    const second = await fetchWindow(base, token, spec, mid, hi, progress);
    progress.tick();             // the half that replaced the original window's count
    return first.concat(second);
  }
}

// Runs jobs with at most `n` in flight, started in order. After a failure no new job starts,
// so a server that has stopped answering is not sent the rest of the queue.
async function pool(jobs, n) {
  let next = 0;
  let failed = false;
  async function lane() {
    while (!failed && next < jobs.length) {
      const job = jobs[next++];
      try {
        await job();
      } catch (e) {
        failed = true;
        throw e;
      }
    }
  }
  await Promise.all(Array.from({ length: Math.min(n, jobs.length) }, lane));
}

// Boundaries are inclusive on both sides, so adjacent windows can return the same document.
function dedupe(docs) {
  const seen = new Set();
  return docs.filter((d) => {
    if (!d || typeof d !== 'object') return false;
    const k = d._id ?? JSON.stringify([d.date, d.created_at, d.sgv, d.eventType]);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

async function fetchNightscout(rawBase, token, days, onProgress) {
  const base = normaliseBase(rawBase);
  const endMs = Date.now();
  const startMs = endMs - days * DAY_MS;

  // One small request first. If it fails, the address, the network or CORS is the problem;
  // if it succeeds, a later failure is the server running out of time.
  try {
    await nsGet(base, 'status.json', {}, token);
  } catch (e) {
    if (!e.retryable) throw e;
    throw new NightscoutError(`Could not reach Nightscout at ${new URL(base).host} (${e.message}). `
      + 'Check the address opens in this browser, and that the site has cors in its ENABLE '
      + 'setting.');
  }

  const progress = {
    total: 0, done: 0,
    tick() { this.done++; this.show(); },
    split() { this.total++; },
    note(t) { onProgress(`Fetching Nightscout… ${this.done}/${this.total} requests (${t})`); },
    show() { onProgress(`Fetching Nightscout… ${this.done}/${this.total} requests. Keep this page open.`); },
  };
  const parts = { entries: [], treatments: [], devicestatus: [] };
  let profiles = [];
  const jobs = [async () => {
    try {
      profiles = await withRetry(() => nsGet(base, 'profile.json', {}, token), 'profile', progress);
    } catch (e) {
      throw e.retryable ? tooSlow('the profile', e) : e;
    }
    progress.tick();
  }];
  for (const spec of STREAMS) {
    for (let lo = startMs; lo < endMs; lo += spec.windowDays * DAY_MS) {
      const hi = Math.min(lo + spec.windowDays * DAY_MS, endMs);
      jobs.push(async () => {
        parts[spec.key].push(...await fetchWindow(base, token, spec, lo, hi, progress));
        progress.tick();
      });
    }
  }
  progress.total = jobs.length;
  progress.show();
  await pool(jobs, CONCURRENCY);

  return { base_url: base, start_ms: startMs, end_ms: endMs,
           entries: dedupe(parts.entries), treatments: dedupe(parts.treatments),
           devicestatus: dedupe(parts.devicestatus),
           profiles: Array.isArray(profiles) ? profiles : [profiles] };
}

// Escape before any interpolation into innerHTML. Settings-file keys and error strings are
// attacker-influenced (a hostile prefs export is a normal thing to be handed in a forum),
// and this page holds a Nightscout token and a master-password field in the DOM.
const esc = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

// --- minimal, safe Markdown -> HTML (headings, bold, list items) ---
function mdToHtml(md) {
  return esc(md).split('\n').map((line) => {
    if (line.startsWith('### ')) return `<h3>${line.slice(4)}</h3>`;
    if (line.startsWith('## ')) return `<h2>${line.slice(3)}</h2>`;
    if (line.startsWith('# ')) return `<h1>${line.slice(2)}</h1>`;
    if (line.startsWith('- ')) return `<li>${inline(line.slice(2))}</li>`;
    if (line.trim() === '---') return '<hr>';
    if (line.trim() === '') return '';
    return `<p>${inline(line)}</p>`;
  }).join('\n');
  function inline(s) { return s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/_(.+?)_/g, '<em>$1</em>'); }
}

// The summary is optional, so no failure here may cost the person their report: a network
// error used to escape this function and replace the finished report with "Failed to fetch".
async function narrate(sourceJson) {
  if (!NARRATOR_URL) return null;
  try {
    const r = await fetch(NARRATOR_URL, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ findings: sourceJson }),
    });
    if (!r.ok) return null;
    const { narrative } = await r.json();
    return narrative || null;
  } catch {
    return null;
  }
}

// Android suspends a backgrounded or screen-locked tab and can drop its requests, and a
// slow Nightscout keeps the fetch going for minutes, so hold the screen on while it runs.
async function holdScreen() {
  try {
    return await navigator.wakeLock?.request('screen') ?? null;
  } catch {
    return null;                 // unsupported or refused; the run goes ahead regardless
  }
}

async function run() {
  $('run').disabled = true;
  const wakeLock = await holdScreen();
  try {
    setStatus('Fetching Nightscout…');
    // clamp to the same bounds as the input's min/max — a typed 3650 would fire several
    // thousand windowed requests at someone's Nightscout.
    const days = Math.min(90, Math.max(1, parseInt($('days').value, 10) || 7));
    const raw = await fetchNightscout($('url').value, $('token').value.trim(), days, setStatus);

    setStatus('Analysing…');
    const B = pyodide.pyimport('report.browser');
    // Run decision-level counterfactuals via real oref0 (web/oref-bundle.js) when available.
    const runner = (typeof globalThis.orefDetermine === 'function') ? B.make_js_oref_runner() : null;
    const kwargs = { oref_runner: runner };

    // Optional settings file (AAPS prefs / Trio JSON) — extracted and validated locally.
    const file = $('prefsfile').files[0];
    let settingsNote = '';
    if (file) {
      setStatus('Reading settings file…');
      const loaded = await loadSettingsFromFile(file, $('prefspw').value);
      if (loaded.needsPassword) throw new Error('That AAPS file is encrypted — enter your master password and try again.');
      const parsed = B.settings_from_raw(pyodide.toPy(loaded.raw)).toJs({ dict_converter: Object.fromEntries });
      const blocked = parsed.blocked || [];
      if (parsed.settings && Object.keys(parsed.settings).length) {
        kwargs.settings = pyodide.toPy(parsed.settings);
        settingsNote = `Settings loaded from ${esc(loaded.format)} `
          + `(${Object.keys(parsed.settings).length} values used`;
        settingsNote += blocked.length
          ? `, ${blocked.length} withheld pending confirmation: ${esc(blocked.join(', '))}).`
          : ').';
        if (parsed.settings.max_iob === undefined && parsed.unmapped_iob_keys.length) {
          settingsNote += ` Max IOB not recognised; IOB-like keys in your file: ${esc(parsed.unmapped_iob_keys.join(', '))}.`;
        }
      } else {
        settingsNote = 'No recognised settings found in that file.'
          + (blocked.length ? ` Withheld pending confirmation: ${esc(blocked.join(', '))}.` : '')
          + (parsed.unmapped_iob_keys.length ? ` IOB-like keys present: ${esc(parsed.unmapped_iob_keys.join(', '))}.` : '');
      }
      if (loaded.collisions && loaded.collisions.length) {
        settingsNote += ` <span class="warn">Duplicate keys in that file (last value used):`
          + ` ${esc(loaded.collisions.join(', '))}.</span>`;
      }
      for (const i of (parsed.issues || [])) {
        if (i.kind === 'out_of_range' || i.kind === 'needs_confirm') {
          settingsNote += ` <span class="warn">${esc(i.message)}</span>`;
        }
      }
    }

    const maxIob = parseFloat($('maxiob').value);
    if (!isNaN(maxIob)) kwargs.max_iob_override = maxIob;
    setStatus('Analysing…');
    // Always pass kwargs: with the ternary, a failed oref bundle silently dropped the
    // uploaded settings and the Max IOB override while still claiming they were loaded.
    const rawPy = pyodide.toPy(raw);
    const resultProxy = B.build_report.callKwargs(rawPy, kwargs);
    const result = resultProxy.toJs({ dict_converter: Object.fromEntries });
    resultProxy.destroy();
    rawPy.destroy();

    let html = mdToHtml(result.report_md);
    if (settingsNote) html = `<p class="muted">${settingsNote}</p>` + html;

    if ($('narrate').checked && NARRATOR_URL) {
      setStatus('Generating written summary…');
      const resultPy = pyodide.toPy(result);
      const sourceProxy = B.abstracted_findings(resultPy);
      const source = sourceProxy.toJs({ dict_converter: Object.fromEntries });
      sourceProxy.destroy();
      resultPy.destroy();
      const narrative = await narrate(source);
      if (narrative) {
        const sourcePy = pyodide.toPy(source);
        const gateProxy = B.gate_narrative(narrative, sourcePy);
        const gate = gateProxy.toJs({ dict_converter: Object.fromEntries });
        gateProxy.destroy();
        sourcePy.destroy();
        if (gate.passed) {
          html = `<h2>Summary</h2>${mdToHtml(narrative)}<hr>` + html;
        } else {
          html = `<p class="warn">The written summary failed verification (${gate.violations.length} issue(s)); showing the verified report instead.</p>` + html;
        }
      } else {
        html = '<p class="muted">The written summary is unavailable just now; this is the verified report.</p>' + html;
      }
    }

    $('report').innerHTML = html;
    setStatus('Done.');
  } catch (e) {
    setStatus('');
    // NightscoutError messages already say what went wrong and what to change.
    $('report').innerHTML = `<p class="warn">${esc(e.message)}</p>`
      + (e instanceof NightscoutError ? ''
        : '<p class="muted">If this is a CORS error, enable CORS on your Nightscout instance rather than proxying your data.</p>');
  } finally {
    wakeLock?.release().catch(() => {});
    $('run').disabled = false;
  }
}

$('run').addEventListener('click', run);
boot().catch((e) => setStatus('Failed to load runtime: ' + e.message));
