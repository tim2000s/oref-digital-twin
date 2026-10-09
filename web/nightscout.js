/*
 * Nightscout fetch, loaded into the engine worker (engine.js) with importScripts.
 *
 * A classic script rather than a module, so its declarations are globals of the worker that
 * loads it. Moved here unchanged from app.js when the engine left the page.
 */

const DAY_MS = 86_400_000;

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
// Only a guard against a hung connection. One site took 199 s to answer a one-day
// devicestatus query and still returned 200, so a tighter limit discards real answers.
const REQUEST_TIMEOUT_MS = 300_000;
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
