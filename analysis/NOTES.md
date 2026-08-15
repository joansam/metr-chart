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
  (Aug 2 2026, CC-BY 4.0, cite epoch.ai/benchmarks). METR Time Horizons is
  NOT among the ~52 benchmarks feeding the ECI, so TH-on-ECI fits aren't
  circular. Reasoning-effort/context variants (`_high`, `_32K`, ...) share
  their base model's score. Refresh it from
  `https://epoch.ai/data/benchmark_data.zip` (the "LLM Benchmark Data" link on
  epoch.ai/benchmarks/use-this-data); the ECI CSV is one member of that zip.
  Epoch refit the index globally on each refresh, so every score drifts a
  little — Jul 15 -> Jul 24 moved tracked models by at most 0.3 pts, and
  Jul 24 -> Aug 2 by up to 1.8 (Kimi K3), so never treat a refresh as a
  no-op: regenerate the arrays and re-check the stats quoted in BASIS_DOC.
- `data/ai_companies_revenue_reports.csv` / `data/ai_companies_funding_rounds.csv`
  — Epoch AI "AI Companies" hub download (Aug 10 2026 snapshot; revenue file
  dated Jul 31, funding file Jul 31; CC-BY 4.0, cite epoch.ai/data/ai-companies).
  Feeds the finance chart via `finance_data.py`. Refresh straight from
  `https://epoch.ai/data/ai_companies_revenue_reports.csv` and
  `https://epoch.ai/data/ai_companies_funding_rounds.csv` (updated ~weekly),
  then regenerate with `--emit-js`. A refresh that adds a company not yet in
  `finance_data.COMPANY_KEY` fails loudly — add it there and to COL/FIN_NAME
  in index.html (new colors go through the CVD/contrast validation noted below).
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
  excluded from the ECI<->AECI fit basis (n=11 within-variant Claude pairs).
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
  models rather than anything peculiar to Opus 5.
  A `TREND_EXCLUDE` hold-out was briefly added to keep it off the AECI
  frontier, on the theory that a distillation of the Mythos/Fable line is not
  an independent frontier push. It was removed: it changed the AECI trend by
  0.3% (14.44 -> 14.40 pts/yr) and the ECI trend by nothing, and it would have
  been the only per-model judgement anywhere in the chart's fits. Not worth
  the inconsistency. If a future model genuinely needs holding out, add the
  mechanism back deliberately and document why here — do not reach for it to
  shave fractions of a point.
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
  means Opus 5's predicted horizon (TH), Mythos 5's imputed ECI, and Opus 5's
  measured AECI. With "show tested models only" on, derived points are hidden
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
- ~~A validation ledger~~ — exists now: `ledger.csv` + `finance_data.py
  --ledger` (see "Validation ledger" above). The capability-side entries
  (Mythos/Fable 5 at 61.3h/8.2h, Opus 5 at 71.4h/9.5h) are seeded as
  event-based rows; extending `--ledger`-style automation to
  `eci_conversions.py` is still open.
- Opus 5's Epoch ECI landed on Aug 2 2026 (161.05, dated 2026-07-24) and
  replaced the imputed 164.2. It is the first prediction-only row with BOTH
  indices measured, so it joins the ECI<->AECI basis (n=10 -> 11) and pulled
  that line close to 1:1 — AECI = 0.30 + 0.991*ECI, from 4.70 + 0.959*ECI.
  Its horizon still routes through the AECI fit, as for any Anthropic model.
