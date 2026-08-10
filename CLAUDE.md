# Working preferences

## Explain in plain language, and recap the facts

When presenting a judgement call, a trade-off, or anything non-obvious, state
the underlying facts in plain language first — what the thing is, what it does,
what the numbers actually are — before the conclusion. Don't assume the shared
context from earlier in a session is fresh, and don't assume a term used in the
code is self-explanatory.

This is cheap: writing a recap costs far less than reading it does, so err
heavily toward including it. A short table or a worked example ("the line
predicted 162.36, it came in at 162.10") beats a sentence of jargon.

## Prefer the simplest rule; avoid special-casing

Strong preference for one uniform rule applied everywhere over a rule plus
exceptions. Do not add per-model flags, hand-maintained exclusion lists, or
bespoke branches unless the alternative genuinely doesn't work — "it would make
the number slightly nicer" is not a reason.

**The reason is scientific, not convenience.** This is not mainly about tidy
code or readability. Every special case is another researcher degree of
freedom, and with enough of them you can tune this chart's fits to look however
you like. That buys apparent in-sample accuracy and does nothing for
out-of-sample accuracy — it is overfitting, dressed up as judgement. These fits
are used to predict horizons for models METR hasn't tested, so out-of-sample is
the *only* thing that matters. The goal is to do it the right way, not the
convenient way.

Two consequences that invert the usual instinct:

- **An exception that improves the fit is more suspect, not less.** If the
  argument for excluding a point is that the trend looks better without it,
  that is evidence against making the exclusion.
- **The uniform rule is allowed to look worse.** If the simple rule produces an
  uglier number or a slower trend, that is probably the data talking. Report it
  rather than tuning it away.

The honest way to earn predictive accuracy here is out-of-sample scoring —
record what the fits predicted, then check them against METR results when they
publish (see the validation-ledger item in `analysis/NOTES.md`) — not tightening
the fit against data already in hand.

Before adding an exception, measure what it actually buys and say so. If the
answer is a fraction of a percent, it isn't worth the inconsistency. If an
exception really is necessary, add it deliberately, document the reasoning and
its measured effect in `analysis/NOTES.md`, and make it visible in the UI rather
than silent.

Worked example, for calibration: Opus 5 beat the previous AECI record, so the
uniform running-max rule put it in the trend fit. A hold-out flag was added to
keep it out, on the theory that a distilled model isn't an independent frontier
push. It was removed — it moved the trend by 0.3% and would have been the only
per-model exception in the whole chart. The uniform rule won.

# Where things live

- `analysis/NOTES.md` — project context that isn't in the code: data
  provenance, methodology decisions and why they were made, environment quirks.
  Read it before changing anything analytical; update it when a decision changes.
- All chart data is GENERATED. Never hand-edit `M_RAW`, `PRED_RAW`, `IDX_RAW`,
  `FITS`, `FIN_RAW` or `FIN_FITS` in `index.html`.

Verify with:

```
python3 gen_model_data.py --check              # M_RAW matches the METR YAML
python3 analysis/eci_conversions.py --check-html   # PRED_RAW/IDX_RAW/FITS match the fits
python3 analysis/finance_data.py --check-html  # FIN_RAW/FIN_FITS match the Epoch CSVs
cd analysis/render_test && npm test            # headless render of every view/toggle
```
