# web — the client-side app (GitHub Pages + Pyodide)

Runs the whole read-only pipeline in the browser via Pyodide (CPython in WASM). The
Nightscout token and data stay on the device; the deterministic report renders with no
network. Optional narration goes to the Cloudflare Worker and is re-verified by the
grounding gate before it is shown. See [../DESIGN.md](../DESIGN.md) §7, §10.

## Flow

1. `boot()` loads Pyodide and unpacks `odt-packages.zip` (the pure-Python packages) into it.
2. On **Analyse**, the browser checks `status.json`, then fetches Nightscout directly
   (`entries` in 2-day windows, `treatments` in 7-day, `devicestatus` in 1-day, plus `profile`;
   two requests at a time), hands the raw JSON to `report.browser.build_report`, and renders the
   deterministic Markdown report. A request with no usable reply is retried twice with backoff,
   and a window that still fails is halved, down to three hours.
3. If narration is enabled and `NARRATOR_URL` is set, it sends **only** `abstracted_findings`
   (stats + finding-keys, no data/token) to the Worker, runs the returned text through
   `report.browser.gate_narrative`, and shows it **only if it passes** — otherwise the
   verified deterministic report stands.

## Build & run locally

```bash
bash web/build.sh                     # produces web/odt-packages.zip
python3 -m http.server -d web 8000    # then open http://localhost:8000
```

## Deploy

`.github/workflows/pages.yml` builds the package bundle and deploys `web/` to GitHub Pages
on push to `main`. Set `NARRATOR_URL` in `app.js` to your deployed Worker to enable
narration (leave empty for report-only).

## Notes / caveats

- `odt-packages.zip` is a build artifact (gitignored) — the workflow builds it; `build.sh`
  builds it locally.
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
