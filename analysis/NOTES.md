# Project notes (context that isn't in the code)

## What this is

Recreation and extension of Alexander Barry's AECI -> METR time-horizon
conversions (abstatisticalconsulting.substack.com), plus a public-ECI leg,
wired into the interactive chart in `index.html`. Both of his posts
("Predicting Opus 4.8's Time Horizon from its AECI", May 29 2026, and
"Predicting Mythos/Fable 5's Time Horizon from its AECI", Jun 20 2026) are
reproduced exactly by `eci_conversions.py` / `aeci_metr_conversion.py`.

## Data provenance

- `../benchmark_results_1_1 (5).yaml` — METR-Horizon-v1.1 ground truth.
- `data/epoch_capabilities_index.csv` — Epoch AI Benchmarking Hub download
  (Jul 15 2026, CC-BY 4.0, cite epoch.ai/benchmarks). METR Time Horizons is
  NOT among the ~52 benchmarks feeding the ECI, so TH-on-ECI fits aren't
  circular. Reasoning-effort/context variants (`_high`, `_32K`, ...) share
  their base model's score.
- `data/aeci_fable5_systemcard.csv` — Barry's extraction (with CIs) of the
  "Anthropic ECI over time" chart in the Fable/Mythos 5 system card; pulled
  from the Datawrapper dataset behind his Jun 20 post
  (datawrapper.dwcdn.net/qBQks/1/dataset.csv). AECI values shift at every
  system-card release; replace this file wholesale at the next release.

## Methodology decisions worth remembering

- **Mythos 5 vs Fable 5**: the system card's AECI point is Mythos 5; Epoch's
  public ECI measures the GA Fable 5. Same underlying model, different
  deployment variants — kept as separate rows, and the cross-variant pair is
  excluded from the ECI<->AECI fit basis (n=10 within-variant Claude pairs).
- **Provenance tiers**: measured > imputed (one index derived from the other
  via the ECI<->AECI line) > estimated (both indices derived from a measured
  METR horizon). Imputed points join the score-frontier trend fits (toggle
  "show tested models only" to refit measured-only); estimated points never
  join any fit — a TH-derived ECI steering the ECI trend would be circular.
- **Estimation/prediction routes are lab-consistent**: Anthropic models go
  through the Claude-only AECI fit; other labs through the lab-adjusted
  (per-lab-intercept) ECI fit. The pooled fit misprices Claude models, which
  earn ~1.5x the horizon per capability point (see the ANCOVA intercepts).
- **Dates**: Mythos Preview (Early) plots at 2026-02-24 (system-card
  internal-availability date), overriding the YAML's 2026-04-07; the
  override lives in `gen_model_data.DATE_OVERRIDES` and is mirrored in
  `eci_conversions.IDX_DATE_OVERRIDES`.

## Verification

- `python3 gen_model_data.py --check` — M_RAW in index.html matches the YAML.
- `python3 analysis/eci_conversions.py --check-html` — PRED_RAW, IDX_RAW and
  FITS in index.html match the regressions.
- `cd analysis/render_test && npm install && npm test` — headless-Chromium
  smoke test of every chart view/toggle.
- All chart data is GENERATED (`gen_model_data.py`, `eci_conversions.py
  --emit-js`) — never hand-edit M_RAW/PRED_RAW/IDX_RAW/FITS.

## Environment notes (Claude Code on the web sessions)

The session's network egress allowlist was extended with: substack.com,
abstatisticalconsulting.substack.com, epoch.ai, datawrapper.dwcdn.net,
lesswrong.com (+ wildcards). anthropic.com remains blocked at the gateway
regardless of allowlist entries (platform special-casing), so system-card
PDFs must be uploaded by hand. Substack bot-blocks plain fetchers on
/home/post/ URLs but its JSON API works: 
`<publication>.substack.com/api/v1/posts/<slug>`.

## Open items / ideas

- Prediction intervals (the fits are unweighted OLS on point estimates;
  METR CIs are huge and unused, AECI CIs only drawn as whiskers).
- Epoch publishes no ECI CIs in the main CSV — ECI mode has no whiskers.
- CLI sensitivity switches (`--drop-reward-hacked`, `--with-gpt35`) affect
  the report only, not the generated chart arrays (which always use the
  default fits).
- A validation ledger: record predictions per data vintage, score them as
  METR publishes actuals (first real test: a METR run of launch-version
  Mythos/Fable 5 vs the 61.3h/8.2h AECI-fit prediction).
