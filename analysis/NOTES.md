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
  (Jul 24 2026, CC-BY 4.0, cite epoch.ai/benchmarks). METR Time Horizons is
  NOT among the ~52 benchmarks feeding the ECI, so TH-on-ECI fits aren't
  circular. Reasoning-effort/context variants (`_high`, `_32K`, ...) share
  their base model's score. Refresh it from
  `https://epoch.ai/data/benchmark_data.zip` (the "LLM Benchmark Data" link on
  epoch.ai/benchmarks/use-this-data); the ECI CSV is one member of that zip.
  Epoch refit the index globally on each refresh, so every score drifts a
  little (Jul 15 -> Jul 24 moved tracked models by at most 0.3 pts).
- `data/aeci_systemcards.csv` — AECI point estimates with CIs, one row per
  model, `source` naming the system card each row came from:
  - `fable5_card` — Barry's extraction of the "Anthropic ECI over time" chart
    in the Fable/Mythos 5 system card, from the Datawrapper dataset behind his
    Jun 20 post (datawrapper.dwcdn.net/qBQks/1/dataset.csv).
  - `opus5_card` — the Claude Opus 5 point quoted in prose in the Opus 5
    system card (Jul 24 2026), §2.3.3.
  Anthropic "rerun the ECI fit globally" at each release, so vintages are only
  mixable when they agree on the models they share. These two do: Mythos 5 is
  161.3 [157.3, 165.4] in both cards, unchanged to the precision either
  reports, so no benchmark was added or dropped in a way that moved the scale
  and Opus 5's 162.1 is directly comparable to the older rows. Re-check that
  overlap before appending the next card's rows; if it fails, replace the
  whole file with the new vintage instead of appending.

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
- **Opus 5 vs the card's frontier set**: the Opus 5 card overlays Opus 5 as a
  *non-frontier* point ("as with Claude Opus 4.7 and Claude Opus 4.8") and
  keeps its slope ratios unchanged — "frontier" there means Anthropic's own
  Mythos-class line. The chart instead applies its uniform cross-lab
  running-max rule, under which Opus 5's 162.1 does beat Mythos 5's 161.29 and
  joins the score frontier. Deliberate: hand-excluding a point on one lab's
  model-line taxonomy would be inconsistent with how every other lab's models
  are treated, and the cost is nil — including Opus 5 moves the fast AECI
  trend from 14.17 to 14.21 pts/yr (ECI: 14.95 -> 14.98). The two are within
  each other's CIs anyway (Opus 5 [158.0, 167.3] vs Mythos 5 [157.3, 165.4]),
  and "pin new trend to 13.5/yr" reproduces the card's rate exactly.
- **Kimi K3 counts as open weights, ahead of the data**: Epoch lists K3 as
  *API access* — Moonshot shipped K2.x as open weights but had not released
  K3's at the Jul 24 2026 snapshot. It is grouped with the open-weights markers
  anyway (owner's call, on the expectation that the weights are imminent), so
  the gold color is a deliberate divergence from `Model accessibility` in the
  CSV rather than a read of it. Revisit if the release doesn't happen. Its fit
  routing is unrelated to this and unaffected: no METR-tested Moonshot model,
  hence no ANCOVA intercept, hence the pooled ECI fit.
- **Open-weights reference models** (DeepSeek-R1, GLM-5.2): plotted for the
  open-vs-closed gap. Public ECI only — no METR run, no AECI — so they enter
  no fit anywhere (and sit below the running-max score frontier, so they can't
  join the score trends either). Their labs have no METR-tested model, hence
  no ANCOVA intercept: predictions route through the pooled ECI fit (flagged
  in `basis`; the chart's "ECI lab-adj" button falls back to pooled for them).
  Both share one gold "open-weights" color in the chart.
- **Slowdown scenario defaults**: it is a hypothetical, so it starts switched
  OFF, and its start date defaults to one year from whenever the page is
  opened (`DECAY_START_DEFAULT`) rather than a fixed date that would silently
  age into the past. The toggle label and legend both derive their year from
  that date, so nothing has to be hand-edited as time passes.
- **The slowdown does apply to ECI/AECI, and always did.** `scoreDecel` decays
  the score growth rate by the same fraction per *TH-doubling-equivalent* of
  score gained (K = ln2 / TH-fit slope), which is algebraically the same
  scenario as the TH-space decay: with ln(TH) = a + b·score, the substitution
  (y−y0)/ln2 = (s−s0)/K makes the two laws identical. It only looked absent
  because the score y-axis was fitted to the datapoints alone, so both trend
  lines left the top of the frame right where the decay begins. `scoreDomain`
  now grows to frame the curves while the scenario is displayed.
  One residual inconsistency worth knowing: the two views fit their baselines
  independently, so they don't describe quite the same world. The ECI trend
  (15.0 pts/yr) implies a 3.51-month TH doubling, matching the TH view's fixed
  3.5 months almost exactly — there, the two slowdowns agree to within 0.1
  points at 2029. The AECI trend (14.2 pts/yr) implies 3.10 months, i.e.
  faster horizon growth than the TH view assumes, so it accrues more decay:
  7.2 points of shortfall by 2029 against 5.9 if the TH curve's shortfall were
  imported directly. Both are defensible; the gap is a statement about the
  AECI-vs-TH baseline disagreement, not about the slowdown model.
- **Responsive sizing**: the shell grows into the viewport (`SHELL_W`) instead
  of the old fixed 900px, and the chart grows taller (`CHART_HEIGHT`) where
  there is vertical room. Two constraints are deliberate: height only exceeds
  the 540px baseline once the viewport clears ~1140px, because the non-chart
  chrome is ~560px tall and a 1080p screen is already full; and width is capped
  by height at ~2.6:1, because past that the plot letterboxes and visually
  flattens the exponential the chart exists to show. Prose blocks keep a
  separate `PROSE_W` so line length stays readable when the chart goes wide.
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
lesswrong.com (+ wildcards). anthropic.com itself remains blocked at the
gateway regardless of allowlist entries (platform special-casing), but the
CDN host that actually serves the system-card PDFs, www-cdn.anthropic.com, is
reachable — the Opus 5 card was pulled straight from it with curl, no manual
upload needed. The PDFs are big (Opus 5 is 16 MB / 193 pages), which is over
WebFetch's limit, so curl + pypdf rather than WebFetch. Substack bot-blocks
plain fetchers on
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
  Mythos/Fable 5 vs the 61.3h/8.2h AECI-fit prediction, then Opus 5 vs
  71.4h/9.5h).
- Opus 5 has no Epoch ECI row yet (its public ECI is imputed from the AECI
  fit, 164.2). Worth re-pulling the ECI zip in a week or two and letting the
  measured value replace the imputed one.
