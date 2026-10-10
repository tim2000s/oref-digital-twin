# Official guidance

The report quotes official guidance beside the findings it bears on: driving rules for the
country the person picks, passages on hypoglycaemia when the report finds lows, and glucose
targets. `report/guidance.py` chooses and renders them.

| File | Holds |
|---|---|
| `report/guidance/sources.json` | Each source: body, jurisdiction, title, URL |
| `report/guidance/references.json` | Each quoted passage: source, topics, jurisdiction, exact wording, date retrieved, SHA-256 of the snapshot it was taken from |
| `guidance/fetch_sources.py` | Fetches every source to a plain-text snapshot under `guidance/sources/` |
| `report/tests/test_guidance.py` | Checks every quote appears word for word in its snapshot, and that the snapshot is the one the quote was taken from |

## Rules

Nothing is paraphrased. A driving rule restated from memory is the error this must not make, so
every passage is a quotation and the test fails when it is not found in its source. Whitespace is
normalised before the comparison, because the PDF sources break sentences across lines; nothing
else is.

The snapshots are not committed. Several sources are copyright (NICE, Diabetes Care, ISPAD)
and the repository is public. Run `python3 guidance/fetch_sources.py` to fetch them; until then
the word-for-word test skips. When a source changes, its SHA-256 no longer matches and the test
fails, which is the prompt to re-read the source and update or retire the quotes taken from it.

## Adding a source or a passage

1. Add the source to `report/guidance/sources.json` and fetch it.
2. Read the passage in the snapshot, not the web page, and copy it exactly.
3. Add it to `references.json` with its topics (`driving`, `hypoglycaemia`, `targets`), its
   jurisdiction and the snapshot's SHA-256 (`fetch_sources.py` prints it).
4. Run `pytest report/tests/test_guidance.py`.

## Retrieved 10 October 2026, and what is missing

| Source | Status |
|---|---|
| DVLA: public page, INF294 leaflet, guidance for medical professionals | quoted |
| NICE NG17 (adults) and NG18 (children and young people) | quoted |
| International consensus on time in range (Battelino 2019) | quoted from its prose; the 70% / <4% / <1% targets are in a table that does not survive conversion to text, so the in-range figure is quoted from ISPAD |
| ISPAD 2024 glycaemic targets | quoted |
| EU Directive 2006/126/EC, Annex III, consolidated 1 November 2020 | quoted; a later consolidation was not found at the URL tried |
| American Diabetes Association, "Diabetes and driving" (2013) | quoted; US rules are set by each state |
| Austroads, Assessing Fitness to Drive (Australia) | not retrieved: the site refuses automated requests (HTTP 403) |
| ADA Standards of Care, glycaemic goals | not retrieved: the search for an open copy failed |
