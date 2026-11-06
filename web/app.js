/*
 * The page for the oref digital twin: the form, the status line, settings-file decryption,
 * optional narration and rendering.
 *
 * The engine (the Nightscout fetch, Pyodide and real oref0) runs in a Web Worker,
 * engine.js, so the page stays responsive during the minutes the settings tests take and can
 * show which step is running. Everything stays client-side: the token and the data go to the
 * worker, never to a server. Optional narration runs a small language model on this device
 * (narrator.js), and its text is re-verified by the grounding gate in the engine before it is
 * shown.
 */

import { loadSettingsFromFile } from './settings.js';

const $ = (id) => document.getElementById(id);
const setStatus = (t) => ($('status').textContent = t);

// --- the engine worker, called like a function ---
const engine = new Worker('./engine.js');
const pending = new Map();
let nextId = 0;

engine.onmessage = ({ data }) => {
  if (data.op === 'progress') {
    setStatus(data.text);
    return;
  }
  const call = pending.get(data.id);
  if (!call) return;
  pending.delete(data.id);
  if (data.ok) {
    call.resolve(data.value);
  } else {
    call.reject(Object.assign(new Error(data.error.message), { nightscout: data.error.nightscout }));
  }
};
engine.onerror = (e) => {
  setStatus('The analysis engine stopped: ' + (e.message || 'unknown error'));
  for (const call of pending.values()) call.reject(new Error('the analysis engine stopped'));
  pending.clear();
};

const ask = (op, args) => new Promise((resolve, reject) => {
  const id = ++nextId;
  pending.set(id, { resolve, reject });
  engine.postMessage({ id, op, args });
});

async function boot() {
  await ask('boot');
  setStatus('Ready.');
  $('run').disabled = false;
}

// Escape before any interpolation into innerHTML. Settings-file keys and error strings are
// attacker-influenced (a hostile prefs export is a normal thing to be handed in a forum),
// and this page holds a Nightscout token and a master-password field in the DOM.
const esc = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

// --- minimal, safe Markdown -> HTML (headings, bold, list items, pipe tables) ---
function mdToHtml(md) {
  const out = [];
  let table = null;                       // rows of cells while inside a pipe table
  const cells = (line) => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => inline(c.trim()));
  const flush = () => {
    if (!table) return;
    const [head, ...body] = table;
    out.push('<div class="scroll"><table><thead><tr>' + head.map((c) => `<th>${c}</th>`).join('')
      + '</tr></thead><tbody>' + body.map((r) => '<tr>' + r.map((c) => `<td>${c}</td>`).join('') + '</tr>').join('')
      + '</tbody></table></div>');
    table = null;
  };
  for (const line of esc(md).split('\n')) {
    if (line.trim().startsWith('|')) {
      if (/^\|?\s*-{3}/.test(line.trim().replace(/^\|/, ''))) continue;   // the |---| rule
      (table ||= []).push(cells(line));
      continue;
    }
    flush();
    if (line.startsWith('### ')) out.push(`<h3>${line.slice(4)}</h3>`);
    else if (line.startsWith('## ')) out.push(`<h2>${line.slice(3)}</h2>`);
    else if (line.startsWith('# ')) out.push(`<h1>${line.slice(2)}</h1>`);
    else if (line.startsWith('- ')) out.push(`<li>${inline(line.slice(2))}</li>`);
    else if (line.trim() === '---') out.push('<hr>');
    else if (line.trim() !== '') out.push(`<p>${inline(line)}</p>`);
  }
  flush();
  return out.join('\n');
  function inline(s) { return s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/_(.+?)_/g, '<em>$1</em>'); }
}

// --- the optional written summary, from a model running on this device ---
// Llama 3.1 8B, the model the earlier Cloudflare narrator ran. On the grounding tests' findings
// it passed the gate 19 times in 20 over two runs; Llama 3.2 3B passed 4 in 10 and called SMBs glucose
// readings (validation/narrator/).
// The f32 build is for GPUs without 16-bit shaders. About 5 GB downloads once and is cached.
const NARRATOR_MODEL = 'Llama-3.1-8B-Instruct-q4f16_1-MLC';
const NARRATOR_MODEL_F32 = 'Llama-3.1-8B-Instruct-q4f32_1-MLC';
const NARRATOR_PROMPT = [
  'You rewrite structured diabetes-loop findings into a clear, calm report for the person.',
  'Hard rules:',
  '- Use ONLY numbers that appear in the provided findings. Never introduce a new number.',
  '- Never give dosing instructions or tell the user to change a setting. This is advisory only.',
  '- Preserve every caveat: association is not causation; a counterfactual is decision-level, not a blood-glucose prediction.',
  '- Whenever you mention SMBs, say that the pattern is an association and does not prove causation.',
  '- Lead with anything critical. Be plain and British-spelled. Do not add a diagnosis.',
  '- Write two or three short paragraphs of plain prose to the person, with no headings or lists.',
  '- Keep each number with the unit it has in the findings: percentages stay percentages and "4 of 10" stays "4 of 10". Do not mention the counts.',
].join('\n');
let narrator = null;

// The summary is optional, so no failure here may cost the person their report.
async function narrate(sourceJson) {
  try {
    if (!narrator) {
      const adapter = await navigator.gpu.requestAdapter();
      if (!adapter) return null;
      const model = adapter.features.has('shader-f16') ? NARRATOR_MODEL : NARRATOR_MODEL_F32;
      const { CreateWebWorkerMLCEngine } = await import('./web-llm.js');
      narrator = await CreateWebWorkerMLCEngine(
        new Worker('./narrator.js', { type: 'module' }), model,
        { initProgressCallback: (p) => setStatus('Loading the summary model: ' + p.text) },
      );
    }
    setStatus('Writing the summary…');
    const res = await narrator.chat.completions.create({
      messages: [
        { role: 'system', content: NARRATOR_PROMPT },
        { role: 'user', content: 'Findings JSON:\n' + JSON.stringify(sourceJson) },
      ],
      max_tokens: 700,
      temperature: 0.2,
    });
    return res.choices[0]?.message?.content?.trim() || null;
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
    // clamp to the same bounds as the input's min/max — a typed 3650 would fire several
    // thousand windowed requests at someone's Nightscout.
    const days = Math.min(90, Math.max(1, parseInt($('days').value, 10) || 7));

    // Optional settings file (AAPS prefs / Trio JSON): decrypted here, validated in the engine.
    const file = $('prefsfile').files[0];
    let settingsNote = '';
    let settings = null;
    if (file) {
      setStatus('Reading settings file…');
      const loaded = await loadSettingsFromFile(file, $('prefspw').value);
      if (loaded.needsPassword) throw new Error('That AAPS file is encrypted — enter your master password and try again.');
      const parsed = await ask('settings_from_raw', { raw: loaded.raw });
      const blocked = parsed.blocked || [];
      if (parsed.settings && Object.keys(parsed.settings).length) {
        settings = parsed.settings;
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

    const maxIobText = parseFloat($('maxiob').value);
    const maxIob = isNaN(maxIobText) ? null : maxIobText;
    setStatus('Fetching Nightscout…');
    const { report_md: reportMd, source } = await ask('analyse', {
      url: $('url').value, token: $('token').value.trim(), days, settings, maxIob,
      jurisdiction: $('jurisdiction').value,
    });

    let html = mdToHtml(reportMd);
    if (settingsNote) html = `<p class="muted">${settingsNote}</p>` + html;
    $('report').innerHTML = html;

    // The settings tests re-run the loop through every 5-minute cycle under about thirty
    // scenarios. The report is already on screen, and the engine reports each stage.
    setStatus('Running settings tests…');
    let section;
    try {
      const aim = document.querySelector('input[name="aim"]:checked')?.value || 'tighter';
      section = await ask('settings_tests', { aim });
    } catch (err) {
      section = `## Settings tests (estimated)\n\n_Settings tests errored: ${err.message.split('\n').slice(-2).join(' ')}_`;
    }
    $('report').insertAdjacentHTML('beforeend', '<hr>' + mdToHtml(section));

    // Last, so a first-time model download delays neither the report nor the settings tests.
    if ($('narrate').checked) {
      setStatus('Preparing the written summary…');
      const narrative = await narrate(source);
      let top;
      if (narrative) {
        const gate = await ask('gate', { narrative, source });
        top = gate.passed
          ? `<h2>Summary</h2>${mdToHtml(narrative)}<hr>`
          : `<p class="warn">The written summary failed verification (${gate.violations.length} issue(s)); showing the verified report instead.</p>`;
      } else {
        top = '<p class="muted">The written summary could not be produced on this device; this is the verified report.</p>';
      }
      $('report').insertAdjacentHTML('afterbegin', top);
    }
    setStatus('Done.');
  } catch (e) {
    setStatus('');
    // Nightscout errors already say what went wrong and what to change.
    $('report').innerHTML = `<p class="warn">${esc(e.message)}</p>`
      + (e.nightscout ? ''
        : '<p class="muted">If this is a CORS error, enable CORS on your Nightscout instance rather than proxying your data.</p>');
  } finally {
    wakeLock?.release().catch(() => {});
    $('run').disabled = false;
  }
}

// A browser without WebGPU cannot run the summary model, so it is not offered there.
if (!navigator.gpu) $('narrate-row').style.display = 'none';

$('run').addEventListener('click', run);
boot().catch((e) => setStatus('Failed to load the analysis engine: ' + e.message));
