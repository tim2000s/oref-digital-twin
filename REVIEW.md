# Review checklist

Concerns that recur in this repository, each a check a diff can be tested against. Findings are
labelled important (fix before commit), nit (optional) or pre-existing (record, do not block).

- Public repository: no names, tokens, Nightscout addresses, site URLs or locations in code,
  docs, fixtures or commit messages. Documentation addresses copies as
  `https://{your-github-id}.github.io/oref-digital-twin/`, never a real one.
- Nothing leaves the browser except requests to the user's own Nightscout and the fetches of
  pinned code and model weights. A new `fetch` or third-party origin needs a reason in the diff.
- The page's CSP keeps `script-src 'self'`. Third-party script is served from the site after a
  pinned SHA-384 check (`build.sh` for WebLLM, `engine.js` for Pyodide); a version bump changes
  the digest in the same commit.
- Text from settings files, Nightscout or errors is escaped before it reaches `innerHTML`
  (`esc` in `app.js`).
- Model-written text is shown only after `report.browser.gate_narrative` passes. A change to
  the summary prompt, the model or `report/grounding.py` is re-scored with
  `validation/narrator/` and `pytest report/tests`, and the figures in README.md updated.
- Advisory only: no text, generated or templated, tells the user to change a dose or setting.
  A more-insulin value is considered only under the time-below-range floors in README.md, and
  floors only tighten.
- The optional parts (the summary, a settings file) can fail without costing the person their
  report.
