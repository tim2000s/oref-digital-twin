/*
 * Generate summaries from an in-browser WebLLM model, with the page's own prompt, for the
 * grounding tests' findings. Writes <out>.json with the source and the texts; gate.py scores it.
 *
 *   bash web/build.sh && python3 -m http.server -d web 8765 &
 *   npm i --no-save puppeteer-core@23.11.1
 *   node validation/narrator/generate.mjs Llama-3.1-8B-Instruct-q4f16_1-MLC validation/narrator/llama-3.1-8b.json
 *
 * Needs desktop Chrome with WebGPU (CHROME= overrides the path); it runs headed, because
 * headless Chrome has no GPU.
 */
import puppeteer from 'puppeteer-core';
import fs from 'fs';
import { execFileSync } from 'child_process';

const [model, out, n = '10'] = process.argv.slice(2);
const app = fs.readFileSync(new URL('../../web/app.js', import.meta.url), 'utf8');
const prompt = eval(app.match(/const NARRATOR_PROMPT = (\[[\s\S]*?\]\.join\('\\n'\));/)[1]);
const source = JSON.parse(execFileSync('python3', ['-c',
  'import json; from report.tests.test_grounding import SOURCE; print(json.dumps(SOURCE))'],
  { cwd: new URL('../..', import.meta.url) }).toString());

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: false, protocolTimeout: 1_800_000,
});
const page = await browser.newPage();
await page.goto('http://localhost:8765/');
const texts = await page.evaluate(async (model, prompt, source, n) => {
  const { CreateWebWorkerMLCEngine } = await import('./web-llm.js');
  const e = await CreateWebWorkerMLCEngine(new Worker('./narrator.js', { type: 'module' }), model);
  const texts = [];
  for (let i = 0; i < n; i++) {
    const r = await e.chat.completions.create({
      messages: [{ role: 'system', content: prompt }, { role: 'user', content: 'Findings JSON:\n' + JSON.stringify(source) }],
      max_tokens: 700, temperature: 0.2,
    });
    texts.push(r.choices[0].message.content.trim());
  }
  return texts;
}, model, prompt, source, Number(n));
fs.writeFileSync(out, JSON.stringify({ model, prompt, source, texts }, null, 1));
await browser.close();
