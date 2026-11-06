# web — the client-side app (GitHub Pages + Pyodide)

Runs the whole read-only pipeline in the browser via Pyodide (CPython in WASM). The
Nightscout token and data stay on the device; the deterministic report renders with no
network. The optional summary is written by a language model running on the device
(`narrator.js`) and is re-verified by the grounding gate before it is shown. See [../DESIGN.md](../DESIGN.md) §7, §10.

## Flow

The page (`app.js`) holds the form, the status line, settings-file decryption, narration and
rendering. Everything else runs in a Web Worker, `engine.js`, so the page stays responsive and
shows each step as it starts: the Nightscout fetch (`nightscout.js`), Pyodide with the Python
packages, and real oref0 (`oref-bundle.js`). On the main thread the settings tests held the page
for about two minutes on a week of data in Chrome, longer in Safari, with no way to show
progress. The worker checks `pyodide.js` against a pinned SHA-384 before running it, since a
worker cannot use a script tag's integrity attribute.

1. The worker loads Pyodide and unpacks `odt-packages.zip` (the pure-Python packages) into it.
2. On **Analyse**, the browser checks `status.json`, then fetches Nightscout directly
   (`entries` in 2-day windows, `treatments` in 7-day, `devicestatus` in 1-day, plus `profile`;
   two requests at a time), hands the raw JSON to `report.browser.build_report`, and renders the
   deterministic Markdown report. A request with no usable reply is retried twice with backoff,
   and a window that still fails is halved, down to three hours.
3. The settings tests run and their section is appended to the report.
4. If the summary box is ticked, the page starts `narrator.js`, a module worker running WebLLM,
   loads Llama 3.1 8B into it (about 5 GB the first time, then from the browser's cache), and
   gives it only `abstracted_findings` (stats and finding keys, no data or token). The text goes
   through `report.browser.gate_narrative` and is shown above the report only if it passes;
   otherwise the verified deterministic report stands. It runs last so that a first download
   delays nothing else. The model needs WebGPU, and the box is hidden without it. It runs in a
   worker because the page's CSP does not allow compiling WebAssembly.

## Build & run locally

```bash
bash web/build.sh                     # produces web/odt-packages.zip and fetches web/web-llm.js
python3 -m http.server -d web 8000    # then open http://localhost:8000
```

## Deploy

`.github/workflows/pages.yml` builds the package bundle and deploys `web/` to GitHub Pages
on push to `main`. INSTALL.md at the repository root covers setting up a copy.

## Notes / caveats

- `odt-packages.zip` and `web-llm.js` are build artifacts (gitignored); `build.sh` makes both.
  `web-llm.js` is WebLLM 0.2.85 from jsDelivr, checked against a SHA-384 pinned in `build.sh`,
  and served from the site because the CSP allows script only from the page's own origin. The
  model weights and their WebAssembly come from Hugging Face and GitHub at run time.
- `replay/` (oref0 counterfactuals) is not in the browser bundle yet — running oref0 in the
  browser is a documented follow-up; the diagnostic report does not need it.
- CORS: cgm-remote-monitor sends CORS headers only when `cors` is in its `ENABLE` setting
  (`lib/server/app.js`), so the site owner has to add it. Do not proxy health data through a
  server instead.
- Proxy timeouts look like CORS failures. A self-hosted Nightscout behind nginx answers a query
  that runs past `proxy_read_timeout` (60 s by default) with nginx's own 504 page, which has no
  CORS header, so the browser reports only "Failed to fetch". On one site a two-day
  `devicestatus` query took 10 s on one try and 57 s on another, and the old 7-day windows
  failed intermittently for that reason. The small windows and retries above are the client's
  answer; raising `proxy_read_timeout` is the server's. The page tells the two cases apart by
  whether the initial `status.json` request succeeded.
- The page asks for a screen wake lock while it runs, because Android suspends a backgrounded
  tab and can drop its requests.
