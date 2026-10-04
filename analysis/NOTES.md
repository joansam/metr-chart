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
- `data/eci_scores.csv` — Epoch AI Benchmarking Hub download (Oct 4 2026,
  CC-BY 4.0, cite epoch.ai/benchmarks), copied verbatim from the
  `epoch_capabilities_index/eci_scores.csv` member of
  `https://epoch.ai/data/benchmark_data.zip` (the "LLM Benchmark Data" link on
  epoch.ai/benchmarks/use-this-data). **METR Time Horizons IS one of the
  ECI's inputs** (`in_eci=True` in the zip's `benchmark_metadata.csv`; the
  earlier claim here that it wasn't was wrong, or became wrong) — see
  "METR inside the ECI" below for what that does to the fits.
  **Format change (by Oct 2026):** the zip used to carry a flat
  `epoch_capabilities_index.csv` with one row per model *version*
  (`claude-opus-4-6`, `gpt-5.4-2026-03-05`, effort variants like `_high`);
  it now has one row per *model*, keyed by display name (`Claude Opus 4.6`,
  `GPT-4o (May 2024)`), with the effort variants folded in and — new —
  90% CIs (`eci_ci_low`/`eci_ci_high`). `MODELS` in `eci_conversions.py`
  keys on that name now. The old flat URL 404s.
  Epoch refit the index globally on each refresh, so every score drifts a
  little — Jul 15 -> Jul 24 moved tracked models by at most 0.3 pts, and
  Jul 24 -> Aug 2 by up to 1.8 (Kimi K3), and Aug 2 -> Oct 4 by up to 1.9
  (Opus 5 161.05 -> 162.94; GPT-5.3 Codex +1.2, Fable 5 +0.7, most others
  within ±0.5), so never treat a refresh as a no-op: regenerate the arrays
  and re-check the stats quoted in BASIS_DOC.
- `data/ai_companies_revenue_reports.csv` / `data/ai_companies_funding_rounds.csv`
  — Epoch AI "AI Companies" hub download (Aug 17 2026 snapshot; CC-BY 4.0,
  cite epoch.ai/data/ai-companies).
  Feeds the finance chart via `finance_data.py`. Refresh straight from
  `https://epoch.ai/data/ai_companies_revenue_reports.csv` and
  `https://epoch.ai/data/ai_companies_funding_rounds.csv` (updated ~weekly),
  then regenerate with `--emit-js`. A refresh that adds a company not yet in
  `finance_data.COMPANY_KEY` fails loudly — add it there and to COL/FIN_NAME
  in index.html (new colors go through the CVD/contrast validation noted below).
- `data/aeci_systemcards.csv` — AECI point estimates with CIs, one row per
  model, `source` naming the system card the vintage came from. **One vintage
  at a time.** Anthropic "rerun the ECI fit globally" at each release, so
  each card's chart is a different scale; vintages are only mixable when they
  agree on the models they share, and the Sep 1 2026 card broke that (Mythos 5
  161.29 -> 159.46, Opus 5 162.1 -> 160.73, both well inside their CIs but a
  full ~1.5 points), so the whole file was replaced rather than appended to.
  - `opus55_card` (current) — the Claude Opus 5.5 system card (Sep 22 2026,
    www-cdn.anthropic.com/fc1b44717c85dc068bc6ba5024219938094694bd/), §2.3.5.
    Anthropic changed the AECI benchmark basket (338 -> 374 benchmarks,
    525 -> 732 models) and refit; the card says outright that values are not
    comparable with earlier cards. Recent frontier models rose 4.1–6.1 points
    (Mythos 5.1 161.98 -> 168.12, Opus 5 160.73 -> 165.18), older ones moved
    ~±1.5, so the file was replaced whole again. Five rows are verbatim from
    Table 2.3.5.3.A (Mythos Preview, Mythos 5, Opus 5, Mythos 5.1, Opus 5.5 —
    169.36 [165.23, 177.05]); the other eight are digitized from Figure
    2.3.5.3.B, a 2000x1300 raster in the same style as the Fable 5.1 card's
    (14.84 px per AECI point from the six gridlines, fit residual 0.03 px).
    Against the five tabulated points the digitizer read dot centres within
    0.06 (Mythos 5: 0.21, its dot overlaps a trend line) and every whisker
    end within 0.06, so the digitized rows are good to ~±0.1 and recorded to
    one decimal. Sonnet 3.5 again anchors at 130 with no CI.
    The card now reports two CIs: *global* (bootstrap refits, the same
    quantity as earlier cards' whiskers) and a new, narrower *local* one
    (gap to the three preceding Claude releases). The CSV keeps the global
    CI, for continuity. Like the Fable 5.1 chart, this one has no Opus 4.1,
    4.7 or 4.8; it does include Sonnet 4.5 and Mythos Preview.
  - Superseded: `fable51_card` — the "Anthropic ECI over time" chart in the
    Claude Fable 5.1 & Claude Mythos 5.1 system card (Sep 1 2026), Figure
    2.3.5.A, §2.3.5. The figure is a 2000x1300 raster, not a Datawrapper
    embed, so nine of the twelve points were digitized from it: dot centroids
    and whisker-cap rows calibrated against the y-axis tick marks (17.24 px
    per AECI point, so ~0.06 pt/px; whiskers read to ±1 px). The three points
    the card also quotes in prose — Mythos 5.1 161.98 [158.20, 169.00],
    Mythos 5 159.46 [156.30, 165.46], Opus 5 160.73 [157.35, 167.11] — are
    entered verbatim and double as the accuracy check: the digitizer read
    them as 161.96, 160.69 and 159.64 (CI ends all within 0.1), so the
    digitized rows are good to about ±0.2 and are recorded to one decimal.
    Sonnet 3.5 (Jun 2024) anchors the scale at 130 with no CI.
    This chart does NOT include Opus 4.7 or Opus 4.8 (the Fable 5 card's
    did), so they now have no AECI here — see the methodology note below.
    It is what the Sep 1 ledger rows were computed on.
  - Also superseded: `fable5_card` (Barry's Datawrapper extraction of the Fable 5
    card chart, datawrapper.dwcdn.net/qBQks/1/dataset.csv) and `opus5_card`
    (the Opus 5 point quoted in that card's §2.3.3). Both live in git history
    and are what Barry's two posts and the Jun/Jul ledger rows were computed
    on.
  Before appending the next card's rows, check the shared models agree; if
  not, replace the whole file again with the new vintage.

## Methodology decisions worth remembering

- **Mythos 5 vs Fable 5**: the system card's AECI point is Mythos 5; Epoch's
  public ECI measures the GA Fable 5. Same underlying model, different
  deployment variants — kept as separate rows, and the cross-variant pair is
  excluded from the ECI<->AECI fit basis (n=10 within-variant Claude pairs on
  the Opus 5.5 vintage; n=9 on Fable 5.1; n=11 before Opus 4.7/4.8 lost their
  AECI). Mythos 5.1 / Fable 5.1 are split the same way.
- **Provenance tiers**: measured > imputed (one index derived from the other
  via the ECI<->AECI line) > estimated (both indices derived from a measured
  METR horizon). **Only measured values set a score frontier.** Imputed and
  estimated points are still plotted, but a derived score carries no
  information the fit that produced it didn't already have, so letting one set
  the trend is the model steering its own input.
  This was not always so — imputed points used to join, and it went wrong in a
  visible way: Mythos 5's ECI is imputed from its AECI (162.43) while Fable 5's
  is measured by Epoch (161.55). They are the same underlying model on the same
  day, so the estimate outranked the real measurement, took the frontier, and
  knocked Fable 5, GPT-5.5 and GPT-5.6 Sol — all measured — off it.
  Effects of the fix: the ECI trend goes 14.79 -> 14.27 pts/yr with n=11 -> 12,
  every member now measured. The AECI trend goes 14.40 -> 15.84 with n=12 -> 10
  and becomes Anthropic-only, because AECI is published only for Anthropic
  models and every other lab's AECI here is just its ECI mapped through the
  fitted line. That is the honest reading of what the AECI view measures.
  Two consequences to know: the AECI view no longer draws a pre-mid-2024
  "previous trend" at all (one measured point, no line to fit — `lin` returns
  null and the legend entry drops rather than showing NaN); and "show tested
  models only" no longer changes a score trend, since the frontier is already
  measured-only. It now only controls which dots are drawn.
- **Estimation/prediction routes are lab-consistent**: Anthropic models go
  through the Claude-only AECI fit; other labs through the lab-adjusted
  (per-lab-intercept) ECI fit. The pooled fit misprices Claude models, which
  earn ~1.5x the horizon per capability point (see the ANCOVA intercepts).
- **Why the fits carry no per-model exceptions.** The bar for special-casing is
  high here for a scientific reason, not a stylistic one: every hand-added
  exception is a researcher degree of freedom, and enough of them would let
  these fits be tuned to any conclusion. That improves in-sample appearance and
  not out-of-sample accuracy — which is the only accuracy that matters, since
  the whole point is predicting horizons for models METR has not tested. So an
  exception that makes a trend look better is evidence against itself, and a
  uniform rule producing an uglier number is usually the data talking. Earn
  accuracy through the validation ledger below (score predictions against METR
  results as they publish), not by adjusting what the fits are allowed to see.
- **Opus 5 gets no special treatment.** Every mechanism applies to it by the
  same rule as everything else, and the outcomes fall out of the data:
  no METR run, so it is absent from the TH frontier and the TH regressions,
  exactly like the other prediction-only rows; both indices measured, so it
  joins the ECI<->AECI fit; Anthropic, so its horizon is predicted through the
  AECI fit. On the score frontiers the running max puts it on AECI (162.1 >
  Mythos 5's 161.29) and off ECI (161.05 < Fable 5's 161.55). Since the AECI
  frontier is Anthropic-only, that split is now the normal case for Claude
  models rather than anything peculiar to Opus 5. (On the Fable 5.1 vintage
  the AECI frontier order is Mythos 5 159.46 < Opus 5 160.73 < Mythos 5.1
  161.98, so the same running max still puts Opus 5 on it.)
  A `TREND_EXCLUDE` hold-out was briefly added to keep it off the AECI
  frontier, on the theory that a distillation of the Mythos/Fable line is not
  an independent frontier push. It was removed: it changed the AECI trend by
  0.3% (14.44 -> 14.40 pts/yr) and the ECI trend by nothing, and it would have
  been the only per-model judgement anywhere in the chart's fits. Not worth
  the inconsistency. If a future model genuinely needs holding out, add the
  mechanism back deliberately and document why here — do not reach for it to
  shave fractions of a point.
- **AECI vintage swap, Sep 1 2026 (Fable 5.1 / Mythos 5.1 card).** The
  uniform rule is "the AECI file is the latest card's chart, whole"; two
  consequences fell out of it and were kept rather than patched:
  - *Opus 4.7 and 4.8 lost their AECI.* The new chart omits them, so they are
    now ECI-only rows and take the same route as Fable 5: Epoch ECI -> implied
    AECI through the fitted line -> horizon. Their predicted p50s move from
    18.7 h / 24.3 h to 17.3 h / 24.0 h, i.e. the implied-AECI route lands
    within ~8% of what their old measured AECIs gave. Carrying their old
    values forward on a rescaled axis was rejected: it would need a
    vintage-to-vintage correction fit, which is one more derived quantity
    dressed up as a measurement. If a later card re-plots them, they come back
    automatically.
  - *Every Claude prediction moved.* The rescale pulled the recent points
    down ~1.5 pts, and the AECI->TH fit barely changed (n=7 measured pairs;
    slope 0.1890 -> 0.1887, R² 0.997 -> 0.998, still ~3.7 pts per doubling),
    so predictions fell with the inputs: Mythos 5 61.3 h -> 43.4 h, Opus 5
    71.4 h -> 55.2 h, Mythos Preview 39.1 h -> 31.1 h. Mythos 5.1 at 161.98
    predicts 69.8 h p50 / 9.3 h p80. The ECI<->AECI line went from
    0.30 + 0.991*ECI (n=11) to 2.71 + 0.973*ECI (n=9). The ECI-side fits are
    untouched (no ECI changed). The AECI view's frontier trend (measured,
    Anthropic-only running max) goes 15.8 -> 15.1 pts/yr, n=10 -> 11, with
    Mythos 5.1 joining the frontier; the ECI trend is unchanged at 14.3.
  - The earlier ledger rows (61.3 h / 71.4 h) stand as written; the
    re-predictions are appended as 2026-09-01 rows so both vintages get
    scored when METR publishes.
  - Mythos 5.1 is dated 2026-09-01 (system card / GA date, the same
    convention as Opus 5). The card's chart plots its dot at ~Aug 7 2026,
    presumably the evaluated snapshot; Mythos Preview likewise plots ~Mar 23
    there against the Apr 7 launch date used here.
  - Fable 5.1's Epoch ECI (164.82) landed by Oct 4 and was added exactly as
    planned: an ECI-only row next to Mythos 5.1, routed through the implied
    AECI like Fable 5.
- **AECI vintage swap, Oct 4 2026 (Opus 5.5 card), and two new models.**
  Same uniform rule as the Sep 1 swap: the AECI file is the latest card,
  whole. This one is a much bigger rescale, and it moves the chart a lot:
  - *What changed in the fits.* The AECI->TH fit is calibrated on the seven
    Claude models with a METR run (3 Opus .. Opus 4.6), which moved only
    ~±1.5 points, but unevenly (Opus 4.6 152.7 -> 154.3, 3 Opus 125.9 ->
    125.1), so the line flattened: slope 0.1887 -> 0.1726, i.e. ~3.7 -> 4.0
    AECI points per horizon doubling (R² 0.998 either way). The ECI<->AECI
    line went from 2.71 + 0.973*ECI (n=9) to -9.29 + 1.0645*ECI (n=10; Opus
    5.5 joins): the new scale is stretched at the top, ~1.06 AECI per ECI.
  - *What changed in the predictions.* The frontier rose ~4–6 AECI points
    against a fit that barely moved, i.e. roughly 1–1.5 extra doublings:
    Mythos 5.1 69.8 h -> 123.6 h, Opus 5 55.2 h -> 74.4 h, Mythos 5
    43.4 h -> 66.1 h, Mythos Preview 31.1 h -> 42.1 h (p50). That is
    Anthropic's rescale, not new horizon evidence. It was kept, not patched:
    the card's stated reason for the refit is better coverage at the top of
    the scale, and anything else would mean a hand-built cross-vintage
    correction. The re-predictions are in the ledger as Oct 4 rows beside
    the Sep 1 ones, so METR results (if any arrive) will score both vintages.
  - *Claude Opus 5.5* (Sep 22 2026; system-card date, the same as Epoch's):
    AECI 169.36 measured, ECI 167.35 measured, so it is routed like Opus 5 —
    joins the ECI<->AECI basis, horizon via the AECI fit: **153 h p50 /
    20 h p80**. For scale, the ECI routes give 69 h (Anthropic lab-adjusted)
    and 48 h (pooled). That ~2.2x gap between AECI and lab-adjusted-ECI
    routes is not new — it was ~2.1x for Opus 5 on the Sep 1 vintage.
  - *GPT-6 Astra* (OpenAI's GPT-6 flagship; announced and Epoch-dated
    Sep 3 2026, API Sep 4): ECI 166.51 only. OpenAI has METR-tested models,
    so it takes the openai lab-adjusted ECI fit like GPT-5.5 / 5.6 Sol:
    **38.8 h p50 / 6.5 h p80**. Its AECI (167.96) is imputed through the
    Claude-only ECI<->AECI line and so, like every non-Anthropic AECI, never
    sets the AECI frontier. The only published horizon-like number for it is
    UK AISI's *no-chain-of-thought* math horizon (~31 min, in OpenAI's system
    card) and a LessWrong estimate of the same no-CoT quantity (~15–40 min);
    neither measures METR's agentic horizon, so neither is used.
  - Neither model has a METR horizon: METR's Opus 5.5 pre-deployment summary
    (quoted in the card, §2.3.6) is qualitative AI-R&D evidence only, and
    METR's public results YAML has not been updated since Mythos Preview.
  - *Frontier trends.* AECI 15.1 -> 18.0 pts/yr (n=11 -> 12, Opus 5.5
    joins); ECI 14.3 -> 15.1 pts/yr (n=12 -> 15: Epoch's refit lifted Fable 5
    to 162.22, above GPT-5.6 Sol's 161.80, so Sol drops off; Opus 5 at
    162.94 now beats Fable 5 and joins; Fable 5.1, GPT-6 Astra and Opus 5.5
    all join — Astra is a measured ECI record on its Sep 3 date). The card's own historical fit is 14.7/yr plus a one-time
    +5.9 jump at Mythos Preview — the chart's uniform running-max OLS reads
    that jump as slope.
- **METR inside the ECI (checked Oct 4 2026): measured, small, left alone.**
  Epoch's index takes METR Time Horizons' average task score as one of its
  60 benchmarks, so every METR-tested model's public ECI partly encodes the
  very result the ECI->TH fits regress on. How much it matters, measured
  from the zip's own files: re-solving each model's ECI from
  `processed_data_for_eci.csv` with Epoch's published benchmark difficulties
  and slopes (`edi_scores.csv`) reproduces the published scores to a mean
  0.03 points; dropping the METR row moves the METR-tested models by
  -0.24 to +0.34 points (GPT-5.3 Codex, which has only 4 benchmarks; most
  move <0.1). Refitting the conversion on those METR-free ECIs changes no
  prediction by more than 2% (GPT-6 Astra 38.8 h -> 38.1 h; Claude AECI
  routes 0%) and the pooled R² 0.967 -> 0.965. Replacing Epoch's published
  scores with our own re-derivation would be a new derived quantity for a
  ~1% effect, so the published ECI stays. Re-check on refreshes: if METR's
  weight in the index grows (it is 1 of 4–30 benchmarks per model today),
  this can stop being negligible.
- **METR-tested models still without an ECI.** GPT-4 1106 and GPT-5.1 Codex
  Max stay "estimated from TH". Codex Max has no row in the Oct 4 file
  (the Aug 2 one had 149.96). Epoch's "GPT-4 Turbo (Nov 2023)" (126.47)
  pools three API versions — 1106-preview, 0125-preview and gpt-4-turbo —
  so equating it with METR's 1106 run is a judgement call; measured effect
  of making it anyway: n 20 -> 21, at most 1.4% on any prediction. Not done.
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
  DeepSeek keeps the shared open-weights gold; Z.ai/GLM-5.2 has its own pink —
  with the finance chart drawing whole trend lines, three-plus gold series
  became indistinguishable, so Zhipu was pulled out of the group color and
  Mistral (open-adjacent, behind the frontier — owner's call) took the gold
  slot. Same entity keeps the same color across both charts.
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
  (14.8 pts/yr) implies a 3.59-month TH doubling, close to the TH view's fixed
  3.5 months — there, the two slowdowns agree to within ~0.3 points at 2029.
  The AECI trend (14.4 pts/yr) implies 3.06 months, i.e. faster horizon growth
  than the TH view assumes, so it accrues more decay: 7.3 points of shortfall
  by 2029 against 5.9 if the TH curve's shortfall were imported directly. Both are defensible; the gap is a statement about the
  AECI-vs-TH baseline disagreement, not about the slowdown model.
- **Horizon unit ladder**: `fmtH` shows a value in the largest unit it reaches
  at least TWO of — 90 min stays minutes, 8 hours stays hours, 24 months reads
  "2 years". Day/week/month are the 8h/40h/160h working units the right-hand
  axis labels use; a year is 12 such months (1920h). The threshold tests the
  ROUNDED figure, so the larger unit never prints "1.x" and the smaller never
  prints a boundary value — that is what keeps "24 months" from appearing.
  Before this the ladder stepped at 1x every rung except months->years.
- **Permanent labels are placed by one rule, not per-model offsets.** The
  hand-tuned `{dx, dy}` per model went stale every time a model landed
  nearby (by the Opus 5.5 update, 1–6 label pairs overlapped per view, 6 at
  phone width). `placeLabels` now tries, for each label in order: a ring of
  spots touching the dot (only if no other dot is nearer the label than its
  own, so it can't be misread as a neighbour's); then a wider ring drawn
  with a thin leader line (which may not cross another dot or label); else
  the label is hover-only. Order: frontier points first, then newest, then
  the higher point on a same-day tie. `LBL` is just the set of names
  eligible for a permanent label. Which names survive depends on width —
  e.g. at 1100px Fable 5.1 and Opus 5 are hover-only in the TH view. The
  render test asserts zero overlapping permanent labels in all three views.
- **Responsive sizing**: the shell grows into the viewport (`SHELL_W`) instead
  of the old fixed 900px, and `CHART_HEIGHT` is 5/8 of viewport height (floor
  540, ceiling 950). Height is deliberately NOT "whatever is left after the
  chrome" — that fits 1080p scroll-free but leaves the plot squat, so the page
  now scrolls ~130px at 1080p in exchange for a properly proportioned chart.
  Width is then capped by height at 2:1, which is what stops the shell running
  to its 1600 ceiling and cancelling out the height; past that ratio the plot
  letterboxes and visually flattens the exponential the chart exists to show.
  Resulting plot aspect is ~2.1:1 at 1080p and ~1.8:1 at 1440p. Prose blocks
  keep a separate `PROSE_W` so line length stays readable when the chart is
  wider than text should be.
- **Trend lines can't drive the y-ceiling past the top labelled tick.** The
  chart runs to 2030, where the 3.5-month doubling reaches ~65 years. Letting
  that set the ceiling added a decade of unlabelled axis and pushed every
  measured point into the lower half, so `yhiDyn` caps the trend contribution
  at the highest tick (6 yr) and the fast line simply clips there. Real data
  and predictions are uncapped and still raise it. The alternative — extending
  YTICKS to ~72 yr — was rejected: it costs ~15% vertical compression of the
  whole chart to show one extrapolated line nobody should read literally.
- **Prediction-basis hover copy** lives in `BASIS_DOC` in index.html and quotes
  fit statistics (R², n, points-per-doubling, the ~1.5x Anthropic/OpenAI
  intercept ratio) straight from this script's report. Regenerating the fits
  can move those numbers, so re-read the report and update the copy whenever
  `--emit-js` changes FITS. Predicted dots also carry a "via ..." line naming
  the route actually used, which tracks the selected basis rather than the
  baked-in `PRED_RAW.basis` string.
- **Dates**: Mythos Preview (Early) plots at 2026-02-24 (system-card
  internal-availability date), overriding the YAML's 2026-04-07; the
  override lives in `gen_model_data.DATE_OVERRIDES` and is mirrored in
  `eci_conversions.IDX_DATE_OVERRIDES`.

- **Finance chart (revenue/valuations) rules are uniform by construction.**
  Revenue: every dated full-company annualized figure counts — all confidence
  tiers and all flavors (ARR / run rate / interpolation), because the flavor
  mix is the labs' reporting inconsistency, not ours to adjudicate; it is
  surfaced in tooltips instead of filtered on. Valuations: every closed round
  with a dated post-money valuation, primary and secondary alike (both are
  market-priced events); "late discussions"/cancelled rounds are out. Trends:
  unweighted OLS of ln(USD) on time wherever a company has ≥4 qualifying
  points in a series, dots-only below that — no per-company exceptions. All
  trend lines extrapolate exactly six months past the day the page is opened
  (uniform horizon that never silently ages, like DECAY_START_DEFAULT).
  Two readings to keep honest about: these are *reported* figures at irregular
  intervals, so the fits measure growth in what gets reported; and Anthropic's
  10.6x/yr revenue slope is real in the data but leans on a tiny 2023 base.
  The legend chips toggle companies in/out of the display (useful because the
  giants compress everyone else on the log axis) — display only: hiding a
  company rescales the axes but never refits any trend.
- **"Trend from last report / <model>" tooltip line**: hovering the
  current-era trend (fast TH/score line, or a finance company line) at a date
  past its most recent frontier point also shows the fitted slope re-anchored
  through that point, styled like the trend line it belongs to. Pure display
  arithmetic, not a second fit and never fed back into anything — it exists
  because an OLS line can sit well under a hot streak's latest report
  (Anthropic's May 2026 $47B is ~2x its fitted line). One DELIBERATE special
  case, owner's call: for TH/ECI/AECI the anchor is the newest
  frontier-setting point on screen even when predicted, imputed or estimated —
  unlike the frontier and trend fits, which stay measured-only. Today that
  means Mythos 5.1 in all three views: its predicted horizon (TH), its imputed
  ECI (163.64, above Fable 5's measured 161.55) and its measured AECI. Since
  Oct 4 it is Opus 5.5 in all three views (predicted TH, measured ECI and
  AECI). With "show tested models only" on, derived points are hidden
  and the anchor reverts to the newest measured point.
- **Finance-chart colors**: labs shared with the capability chart keep their
  color (same entity, same hue, both charts; the open-weights gold covers
  DeepSeek, Moonshot, MiniMax and Mistral). The non-gold hues — xAI #2fbcd3,
  Z.ai #e069a8, Cohere #8f7bf0 —
  were checked with the dataviz palette validator against the #12121f surface:
  chroma, adjacent-pair CVD separation, normal-vision separation and contrast
  all pass. (The validator's lightness-band check fails for the *pre-existing*
  palette on this very dark surface; the new hues match that established
  brightness rather than repainting the page.)

## Validation ledger

`ledger.csv` is the out-of-sample scorecard: what the fits predicted, written
down *before* the outcome existed, then checked against reality. In-sample R²
says nothing about the predictions this project exists to make; special-casing
inflates it. The ledger is the counterweight — predicted values are append-only
and never edited, only their `actual`/`actual_date` fields get filled.

- Finance rows are automated: `python3 finance_data.py --ledger` (run it after
  a data refresh) appends the current fits' six-month-out revenue/valuation
  predictions for every fitted company, and scores any past prediction that
  has come due against the nearest report within ±60 days. Re-running on the
  same day is a no-op.
- `th_*` rows are event-based (empty `target_date`): fill `actual` by hand
  when METR publishes a run of that model. Seeded with the two AECI-fit
  predictions from the open-items list.

First observation for calibration (Aug 14 2026): the pre-refresh OpenAI
revenue fit (4.00x/yr, data through Feb 2026) implied ~$53B for Aug 13 2026;
Bloomberg reported "more than $40B" that day, so the trend overshot by ~30%
over a six-month horizon (or less, if 40B is a real underestimate). The
refreshed fit softened to 3.88x/yr.

Second observation (Aug 15 2026, owner-supplied figure not yet in Epoch's
dataset): Anthropic reportedly hit $63B annualized on Jun 30 2026. The OLS
fit (10.6x/yr, data through May 15) put Jun 30 at $40.3B — 56% under, because
the line averages back through the tiny 2023 base. The "trend from last
report" reading (May 15's $47B extended at the fitted slope) put it at
$63.3B — a ratio of 1.00, i.e. implied May->Jun growth of 10.2x/yr against
the fitted 10.6x/yr. Early but consistent lesson from both observations: the
plain OLS lines lag the current level for hot companies (exactly the bias the
anchored tooltip line displays), while the anchored reading was excellent at
a ~6-week horizon. Score the Feb 2027 ledger rows with this in mind.

Third observation (Aug 17 2026 refresh): Epoch ingested Anthropic's $65B run
rate dated Jul 31 (Bloomberg). Against the pre-refresh fit (data through
May 15): OLS said $49.2B (actual 1.32x above), anchored-from-May said $77.3B
(actual 0.84x). With the Jun 30 $63B figure this brackets a sharp July
deceleration — 63 -> 65 in a month is ~1.4x/yr annualized, versus 10x/yr
May -> June. One month proves little, but the pattern so far: OLS too low,
anchored-at-full-slope too high past ~6 weeks. The refreshed fit is
10.94x/yr (n=15) — the new point pulled it UP, since $65B sits above even
the steep line.

## Refreshing the finance data

Epoch updates the AI-companies CSVs roughly weekly. To refresh:

```
cd analysis
curl -sSL -o data/ai_companies_revenue_reports.csv https://epoch.ai/data/ai_companies_revenue_reports.csv
curl -sSL -o data/ai_companies_funding_rounds.csv  https://epoch.ai/data/ai_companies_funding_rounds.csv
python3 finance_data.py                # eyeball the new fits (growth, n, R^2)
python3 finance_data.py --emit-js      # paste over the FIN_RAW/FIN_FITS block in index.html
python3 finance_data.py --check-html   # must pass
python3 finance_data.py --ledger       # score due predictions, log this vintage's
cd render_test && npm test             # both finance views still render
```

Things a refresh can surface, and what to do:

- **A new company** → the script exits with an error naming it. Add it to
  `COMPANY_KEY` in `finance_data.py` and to `COL`/`FIN_NAME`/`FIN_ORDER` in
  `index.html`; validate any new color (see the finance-chart colors note).
- **A company crosses n=4** → it gains a trend line automatically. That is the
  uniform rule working, not something to review away.
- **Revised history** — Epoch edits old rows, not just appends. The diff of the
  committed CSVs shows exactly what moved; quote any notable revision in the
  commit message. Fits can drift on a refresh even with no new reports.

## Verification

- `python3 gen_model_data.py --check` — M_RAW in index.html matches the YAML.
- `python3 analysis/eci_conversions.py --check-html` — PRED_RAW, IDX_RAW and
  FITS in index.html match the regressions.
- `python3 analysis/finance_data.py --check-html` — FIN_RAW and FIN_FITS in
  index.html match the Epoch AI-companies CSVs.
- `cd analysis/render_test && npm install && npm test` — headless-Chromium
  smoke test of every chart view/toggle.
- All chart data is GENERATED (`gen_model_data.py`, `eci_conversions.py
  --emit-js`, `finance_data.py --emit-js`) — never hand-edit
  M_RAW/PRED_RAW/IDX_RAW/FITS or FIN_RAW/FIN_FITS.

## Environment notes (Claude Code on the web sessions)

The session's network egress allowlist was extended with: substack.com,
abstatisticalconsulting.substack.com, epoch.ai, datawrapper.dwcdn.net,
lesswrong.com (+ wildcards). anthropic.com itself remains blocked at the
gateway regardless of allowlist entries (platform special-casing), but the
CDN host that actually serves the system-card PDFs, www-cdn.anthropic.com, is
reachable — the Opus 5 card was pulled straight from it with curl, no manual
upload needed, and so was the Fable 5.1 card (Sep 1 2026). The PDFs are big
(Opus 5 is 16 MB / 193 pages, Fable 5.1 is 16 MB / 212 pages), which is over
WebFetch's limit, so curl + pypdf rather than WebFetch. The system python's
`cryptography` module is broken (pypdf/pdfplumber import fails); a throwaway
venv with pypdf + pymupdf works. The AECI figure is a raster image: pull it
out with pymupdf and digitize (dot centroids + whisker caps against the tick
marks) rather than expecting a dataset behind it. Substack bot-blocks
plain fetchers on
/home/post/ URLs but its JSON API works: 
`<publication>.substack.com/api/v1/posts/<slug>`.

## Open items / ideas

- Prediction intervals (the fits are unweighted OLS on point estimates;
  METR CIs are huge and unused, AECI CIs only drawn as whiskers).
- Epoch's ECI file now carries 90% CIs (`eci_ci_low`/`eci_ci_high`, since
  the Oct 2026 format change); ECI mode could draw whiskers from them. Not
  wired in yet.
- The "Pin trend to 13.5/yr (system card)" toggle quotes an older card's
  rate. The current (Opus 5.5) card fits 14.7/yr with a one-time +5.9 jump,
  or 14.4 -> 22.2/yr with a Sep 2025 break; which (if any) the pin should
  track is an open call.
- CLI sensitivity switches (`--drop-reward-hacked`, `--with-gpt35`) affect
  the report only, not the generated chart arrays (which always use the
  default fits).
- ~~A validation ledger~~ — exists now: `ledger.csv` + `finance_data.py
  --ledger` (see "Validation ledger" above). The capability-side entries
  (Mythos/Fable 5 at 61.3h/8.2h, Opus 5 at 71.4h/9.5h, plus the Sep 1 2026
  re-predictions and Mythos 5.1 at 69.8h/9.3h) are seeded as event-based
  rows; extending `--ledger`-style automation to
  `eci_conversions.py` is still open.
- Opus 5's Epoch ECI landed on Aug 2 2026 (161.05, dated 2026-07-24) and
  replaced the imputed 164.2. It is the first prediction-only row with BOTH
  indices measured, so it joins the ECI<->AECI basis (n=10 -> 11) and pulled
  that line close to 1:1 — AECI = 0.30 + 0.991*ECI, from 4.70 + 0.959*ECI.
  Its horizon still routes through the AECI fit, as for any Anthropic model.
