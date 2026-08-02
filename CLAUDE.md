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
- All chart data is GENERATED. Never hand-edit `M_RAW`, `PRED_RAW`, `IDX_RAW`
  or `FITS` in `index.html`.

Verify with:

```
python3 gen_model_data.py --check              # M_RAW matches the METR YAML
python3 analysis/eci_conversions.py --check-html   # PRED_RAW/IDX_RAW/FITS match the fits
cd analysis/render_test && npm test            # headless render of every view/toggle
```
