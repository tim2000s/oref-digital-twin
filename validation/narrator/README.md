# In-browser summary model

The page's summary is written by a WebLLM model on the user's device and shown only if the
grounding gate (`report/grounding.py`) passes it. Two models were compared on 6 November 2026, each
given the findings from `report/tests/test_grounding.py` ten times with the prompt in `web/app.js`,
at temperature 0.2.

| Model | Download | Passed the gate | Notes |
|---|---|---|---|
| Llama 3.1 8B Instruct, q4f16_1 | about 5 GB | 10 of 10, then 9 of 10 on a re-run | The failure called a mean of 120 mg/dL "a bit higher than the target" and was blocked |
| Llama 3.2 3B Instruct, q4f16_1 | about 2 GB | 4 of 10 | Called SMBs glucose readings, in texts that passed as well as failed |

The page uses the 8B model. Passing the gate is necessary but not sufficient: the gate checks
numbers, dosing directives, omitted critical findings and caveats, and a text can pass it while
misdescribing a term, as the 3B texts show. This is one synthetic set of findings, not a measure
across real reports. `llama-3.1-8b.json` holds the re-run; the first run was not kept.

To regenerate (needs desktop Chrome with WebGPU):

    bash web/build.sh && python3 -m http.server -d web 8765 &
    npm i --no-save puppeteer-core@23.11.1
    node validation/narrator/generate.mjs Llama-3.1-8B-Instruct-q4f16_1-MLC validation/narrator/llama-3.1-8b.json
    PYTHONPATH=. python3 validation/narrator/gate.py validation/narrator/llama-3.1-8b.json
