/*
 * oref-twin narrator — Cloudflare Worker.
 *
 * Turns the abstracted findings into readable prose using a small LLM (Cloudflare
 * Workers AI, free daily allocation). It is a NARRATOR, not an analyst: it is told never
 * to invent numbers and never to give dosing instructions.
 *
 * Trust model: this Worker is UNTRUSTED from the client's safety point of view. The
 * browser runs the deterministic grounding gate on whatever this returns and only shows
 * it if it passes; otherwise it falls back to the deterministic template. So the Worker
 * cannot, by construction, put an ungrounded number or a prescription in front of a user.
 *
 * Privacy: the client sends ONLY abstracted findings (stats + finding-keys). Reject any
 * payload that carries raw data or connection info.
 */

const ALLOWED_KEYS = new Set(['counts', 'glycemia', 'findings', 'variant', 'counterfactuals']);
const MAX_BODY_BYTES = 64 * 1024;
const MODEL = '@cf/meta/llama-3.1-8b-instruct';

const SYSTEM_PROMPT = [
  'You rewrite structured diabetes-loop findings into a clear, calm report for the person.',
  'Hard rules:',
  '- Use ONLY numbers that appear in the provided findings. Never introduce a new number.',
  '- Never give dosing instructions or tell the user to change a setting. This is advisory only.',
  '- Preserve every caveat: association is not causation; a counterfactual is decision-level, not a blood-glucose prediction.',
  '- Lead with anything critical. Be plain and British-spelled. Do not add a diagnosis.',
].join('\n');

function cors(origin) {
  return {
    'Access-Control-Allow-Origin': origin || '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

function json(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...cors(origin) },
  });
}

function sanitiseFindings(payload) {
  // keep only allow-listed top-level keys; reject anything that smells like raw data
  const out = {};
  for (const [k, v] of Object.entries(payload || {})) {
    if (ALLOWED_KEYS.has(k)) out[k] = v;
  }
  return out;
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const allowOrigin = env.ALLOWED_ORIGIN || origin;

    if (request.method === 'OPTIONS') return new Response(null, { headers: cors(allowOrigin) });
    if (request.method !== 'POST') return json({ error: 'POST only' }, 405, allowOrigin);

    // optional rate limit (bind a Ratelimit as env.RL to enable)
    if (env.RL) {
      const ip = request.headers.get('CF-Connecting-IP') || 'anon';
      const { success } = await env.RL.limit({ key: ip });
      if (!success) return json({ error: 'rate limited' }, 429, allowOrigin);
    }

    const raw = await request.text();
    if (raw.length > MAX_BODY_BYTES) return json({ error: 'payload too large' }, 413, allowOrigin);

    let body;
    try {
      body = JSON.parse(raw);
    } catch {
      return json({ error: 'invalid JSON' }, 400, allowOrigin);
    }

    const findings = sanitiseFindings(body.findings || body);
    if (!findings.findings) return json({ error: 'no findings provided' }, 400, allowOrigin);

    if (!env.AI) return json({ error: 'no AI binding configured' }, 501, allowOrigin);

    let narrative = '';
    try {
      const res = await env.AI.run(MODEL, {
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: 'Findings JSON:\n' + JSON.stringify(findings) },
        ],
        max_tokens: 700,
        temperature: 0.2,
      });
      narrative = (res && (res.response || res.result || '')).trim();
    } catch (e) {
      return json({ error: 'model error: ' + String(e && e.message ? e.message : e) }, 502, allowOrigin);
    }

    // The client re-verifies this with the grounding gate before showing it.
    return json({ narrative }, 200, allowOrigin);
  },
};
