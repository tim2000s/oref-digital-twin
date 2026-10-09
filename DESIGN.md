# oref-digital-twin — design

Advisory decision-support for **AAPS** and **Trio** insulin-dosing settings. A user
supplies their current settings and read-only access to their Nightscout data; the
service returns a report that explains what their loop is doing, flags what is risky,
and proposes settings changes only as trials to be tested — never as instructions to
apply blind.

The name is aspirational, not literal: there is no glucodynamic "twin" that predicts
blood glucose. What *can* be twinned is the **controller** — oref `determine-basal` is
open, deterministic and re-runnable — so the honest core of the tool is replaying the
controller, not simulating the body. See §2. Since October 2026 the settings tests (§2.1)
add a deliberately simple glucose estimate on top of that replay, labelled as a model
everywhere it appears.

---

## 1. Scope and non-goals

**In scope**
- Read Nightscout telemetry (oref `devicestatus`), CGM, treatments and the profile.
- Ingest the operative settings (SMB/oref preferences + profile).
- Detect which algorithm variant is running.
- Produce a diagnostic report: what the loop did, where it sat relative to safety
  floors, which settings are outliers or internally inconsistent.
- Where a setting change would flip a *decision*, price that difference by replaying
  the controller (§2).

**Explicitly not in scope**
- No writes to Nightscout, the pump, or the loop. Ever. Read-only, advisory-only.
- No claim that a counterfactual **blood-glucose** trajectory is an outcome (no
  glucodynamic simulator exists; this is the identification constraint, §3). The settings
  tests in §2.1 estimate glucose with a stated model and report it as an estimate.
- No autonomous "set X to Y" application. Every prescriptive output is a hypothesis to
  trial, gated as in §7.
- No handling of algorithm variants the tool does not model — it downgrades to
  diagnosis-only rather than guess (§4).

---

## 2. The core principle: replay the controller, not the body

oref `determine-basal` is a pure function of its inputs (BG, IOB, COB, profile,
settings, clock). The reference source is open (oref0 for AAPS; the Swift/JS port for
Trio). This gives the tool something a bespoke black-box loop could not offer: a
**decision-level counterfactual**.

Given the logged inputs for a cycle, we can re-run the *actual* controller under altered
settings and observe how the **recommendation** changes:

> "With `maxSMBBasalMinutes` = 60 instead of 30, `determine-basal` would have enacted a
> 1.2 U SMB instead of 0.6 U at these 14 cycles overnight."

This is honest and clean. What it is **not**: a claim about the resulting glucose. The
BG that would have followed the altered dose is unknowable without a glucodynamic model.
So the replay prices the *dosing* difference and the tool states the BG counterfactual
caveat every time.

**Implementation stance:** run the real oref code as an oracle. Do not reimplement
`determine-basal`. Vendor/pin the exact oref version the user runs, feed it the logged
inputs, diff the output. Reimplementation would drift from the reference and quietly
invalidate every counterfactual.

### 2.1 Settings tests: a modelled glucose estimate on the replay

Added October 2026, at the user's request, to aim settings at time in range above 70% and
time below range under 2%. This departs from the decision-only stance above, and the
departure is confined to `replay/scenarios.py` and the `simulate` function in
`replay/oracle/request.js`.

The tests run in the order of a manual basal test, then an ISF test, then a carb-ratio test,
then target, SMB limit and max IOB. Each steps one setting from −30% to +30% and re-runs the real
determine-basal through every 5-minute cycle of the period, closed-loop: the insulin
difference from each earlier cycle is added to the insulin-on-board projection with oref0's
own insulin curve, and shifts glucose by units × profile ISF (adjusted by autosens) × the
fraction of that insulin's action completed, so the loop sees and reacts to the shifted
glucose at the next cycle. Basal is judged on fasting stretches, carb ratio on meal stretches, and ISF and the last three
on the whole period (ISF only once there are 6 h of correction stretches to judge it from), each
stage keeping the earlier choices. A value giving more insulin than the current setting is only
considered when the whole period's estimate keeps time below 70 under 2% and below 54 under
0.6%. Both rules followed the mis-set profile test on TimSim (validation/BAD_PROFILES.md). They replaced the report's earlier decision-level section,
which replayed two fixed changes open-loop over the last 400 cycles and summed each cycle's
30-minute delivery forecast across every cycle, counting the same insulin many times on a
loop that runs every minute.

What the estimate assumes, each a modelling choice rather than a finding: the profile ISF
is the body's real sensitivity; meals, activity and the person's own treatments, hypo
treatments included, would have been the same; logged meal boluses scale with 1 / carb
ratio. It is a model of the loop's response, not of the body's. On one week of an
AndroidAPS user's data a −30% basal left daily insulin almost unchanged (−0.07 U over seven
days) because the loop made up the difference with temps and SMBs, and the estimate's
effect was where glucose settled (+15 mg/dL on average). That pattern is the expected
behaviour of a proportional controller.

Not yet done: a backtest of the estimate against periods where a person actually changed a
setting. Until that exists the estimates rank settings; they do not predict outcomes.

---

## 3. The identification constraint (shapes everything)

There is no simulator that maps a dosing decision to a BG trajectory for this
population. Consequences the whole design must respect:

- **Prediction / detection** questions are validated out-of-sample and are clean — no
  counterfactual required. Most of the diagnostic value lives here.
- **Decision** questions (does a setting change flip what the controller enacts?) are
  answered exactly by the replay oracle (§2).
- **Outcome** questions (does the change improve BG?) are only ever *priced against
  observed outcomes* with the counterfactual caveat stated, and are strongest
  within-subject. Between-user results are hypothesis-generating.
- An observational effect size is associational unless a within-user or randomised
  design backs it. The tool cannot run RCTs, so prescriptive advice stays conservative.

The bottleneck is identification, not modelling. Keep models modest.

---

## 4. Algorithm-variant detection (a gate, runs first)

"Generic AAPS/Trio" is not one algorithm. The levers and their meanings differ by
variant, so detection precedes any advice:

| Variant | Notes |
|---|---|
| AAPS — stock SMB | Baseline oref SMB semantics. |
| AAPS — Dynamic ISF | ISF scaled dynamically; ISF-related advice must account for it. |
| AAPS — AutoISF | Further ISF adjustment layer; different tuning surface. |
| Trio — oref + Dynamic ISF/CR | Trio's dynamic sensitivity/ratio. |
| Trio — **middleware** | Arbitrary JS rewrites the profile *before* `determine-basal`. Stock-oref assumptions are void. |

Detection draws on the `devicestatus` payload (reason string, enacted values, version
fields) and the profile. **If middleware is present, or the variant is one the tool does
not model, the replay oracle cannot assume stock behaviour** — the tool either loads the
user's middleware into the oracle or downgrades to diagnosis-only for the affected
outputs. Never advise on a controller you are not actually replaying.

---

## 5. Data sources

### 5.1 Nightscout (the primary signal)
Both AAPS and Trio upload the oref/OpenAPS `devicestatus` payload — this is the
algorithm narrating itself and is an oref standard shared across AAPS, Trio and oref0
(Loop uses a different schema and is out of scope for the replay oracle).

Pull:
- `devicestatus` — `reason`, IOB, COB, eventualBG, insulinReq, sensitivityRatio, the
  IOB/ZT/COB/UAM prediction arrays, the enacted SMB/tempBasal. The richest source.
- `entries` — CGM.
- `treatments` — boluses, SMBs, carbs, temp targets, temp basals.
- `profile` — basal, ISF, CR, targets, DIA. A large, safety-critical slice of the
  operative settings lives here and is readable directly, no screenshot.

**Fetching discipline:** chunk to ~7-day windows and retry with backoff — long windows
502 on many self-hosted sites. Read-only tokens only; scoped; never stored in plaintext;
revocable.

### 5.2 Settings not in the profile
The SMB/oref preference set (maxIOB, maxSMB, SMB minutes, UAM, autosens min/max,
dynamic-ISF toggles) is not in the NS profile. Options, in order of robustness:

1. **Infer/cross-check from `devicestatus`** — several operative values (effective
   `max_iob`, current target, `sens`) echo in the reason each cycle, so much of the
   config can be reconstructed and verified from NS alone.
2. **AAPS encrypted-prefs export, decrypted client-side.** The export is AES-256-GCM,
   key via PBKDF2-HMAC-SHA1 (50k iterations, 256-bit), salt+IV in the file, keyed on the
   user's **master password**. It cannot and must not be decrypted server-side. But every
   primitive is in the browser's WebCrypto: the user selects the file and types the
   master password *in the page*, decryption happens locally, and only the minimised
   Boost/oref-relevant key set is sent to the backend. Password and full config never
   leave the device.
3. **Screenshots.** Lowest friction. Tractable because the target is a *bounded, known*
   typed key set: vision-extract → validate against the schema (types + ranges) →
   flag low-confidence or out-of-range reads → user confirms before anything runs. Never
   trust an extracted insulin-relevant number without confirmation.

Trio has no AAPS-style encrypted file; its profile-side is covered by NS (5.1), the rest
via screenshots.

---

## 6. Analysis layers (in order)

1. **Deterministic sanity checks.** Values out of range, contradictory combinations,
   caps mis-set relative to TDD (computable from NS), proximity to safety floors. Cheap,
   safe, high-value, no statistics.
2. **Diagnostic pattern detection.** Out-of-sample and honest: SMB stacking into
   high-IOB tails, predictions vs realised, flat-CGM behaviour, time-below-range exposure
   vs the absolute floors, false-positive triggers. Most user value sits here.
3. **Decision-level replay (§2).** For a proposed change, diff the controller's enacted
   output across the logged cycles.
4. **Cohort / within-user comparison.** Within-subject first; between-user is
   hypothesis-generating only. Enforce matched baselines before believing an effect size
   — un-baselined, un-leakage-checked sizes are provisional. Stratify by variant and pump
   before comparing; the population is self-selected and now heterogeneous across
   variants.

---

## 7. Recommendation generation and gating

- The **numbers come from the deterministic / replay / statistical layers**, not from a
  language model. If an LLM is used, it *narrates* findings; it does not invent dosing
  values.
- Every prescriptive suggestion is framed as a **trial**, priced against observed
  outcomes with the counterfactual caveat, and gated behind a two-test bar: absolute
  time-below-range gates **plus** the decision-level replay showing the change is
  material. A real dosing change warrants a pre-registered within-user trial.
- **Safety floors are one-directional.** Advice may only ever tighten a
  time-below-range kill-switch, never loosen one. Statistics rank options; they never
  override a floor.

---

## 8. Don't rebuild what oref ships

- **Autotune** already tunes basal / ISF / CR from history. Run it, interpret its
  output, and cover what it ignores (SMB settings, targets, safety limits, dynamic-ISF
  parameters). Do not reimplement the tuner.
- The oref **objectives** and existing docs are the reference for what "sensible" looks
  like; cite them rather than inventing thresholds.

---

## 9. Safety, privacy, regulatory

- **Read-only, advisory-only.** No path writes to NS, the pump, or the loop.
- **Regulatory.** Advising on insulin-dosing settings is very likely a medical-device /
  clinical-decision-support function under MHRA/FDA. A private tool for an informed DIY
  cohort leans on strong disclaimers and "discuss with your clinician"; a public product
  must take the classification question seriously *before* launch. This choice (private
  cohort vs public) is the decisive scope fork and changes the robustness, privacy and
  regulatory bar sharply.
- **Data.** NS health data and tokens are GDPR / UK-GDPR special-category. Data
  minimisation, encryption at rest, explicit consent, retention limits, scoped/revocable
  read-only tokens, no plaintext token storage.
- **No identifiers in this repo.** Public repository: no names, tokens, site URLs or
  locations in code, docs, fixtures or commit messages. Test data is synthetic or
  anonymised.

---

## 10. Architecture and stack

Polyglot, by necessity:
- **Ingestion + analysis** — Python (mirrors the existing backtesting toolchain; async
  jobs, not a live chat).
- **Replay oracle** — Node, running the real oref0 JS (and Trio's port); pinned per
  user-variant.
- **Client-side decrypt** — browser WebCrypto (PBKDF2 + AES-GCM), for the optional
  encrypted-prefs path.
- **Front door** — thin web UI: upload/connect → async analysis job → structured report.
  The heavy lifting is analysis, not UI.

The report is a structured document, not an interactive advisor.

---

## 11. Open questions (decide before building far)

1. **Scope fork:** private tool for an informed cohort, or public product? (Drives §9.)
2. **First input path:** screenshots (lowest friction) or client-side file decrypt
   (more robust)? Can ship screenshots first and add decrypt later.
3. **Variant coverage at launch:** which of the §4 variants are supported day one, and
   what is the middleware policy (load it, or diagnosis-only)?
4. **Oracle hosting:** how oref versions are pinned and matched to each user's build.

---

## 12. Phasing (indicative)

1. **NS ingestion** — pull + chunk + backoff for `devicestatus` / `entries` /
   `treatments` / `profile`; normalise to a common schema. Everything depends on this.
2. **Variant detection** — classify the running algorithm from NS + settings.
3. **Diagnostics** — deterministic sanity checks and out-of-sample pattern detection
   (the honest, safe core).
4. **Replay oracle** — decision-level counterfactuals against logged inputs.
5. **Settings ingestion** — screenshots first, client-side decrypt second.
6. **Report + front door.**

Diagnostics (1–3) deliver value before the oracle exists; build in this order.
