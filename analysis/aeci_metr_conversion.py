#!/usr/bin/env python3
"""Recreate Alexander Barry's AECI -> METR time-horizon conversion.

Source article: "Predicting Opus 4.8's Time Horizon from its AECI"
(abstatisticalconsulting.substack.com, May 29 2026). The author regresses
ln(METR time horizon) on Anthropic's internal ECI ("AECI") for the models
that have both values, then predicts time horizons for models that only
have an AECI.

AECI values below are the author's extraction from the "Anthropic ECI over
time" chart in the Opus 4.8 system card. METR p50/p80 horizons (minutes)
come from benchmark_results_1_1 (5).yaml in this repo (METR-Horizon-v1.1).

Published fits to reproduce:
    p50: TH_min = 2.9e-10 * 1.2053^AECI  (R^2 = 0.993)
    p80: TH_min = 1e-10   * 1.1984^AECI  (R^2 = 0.981)
Published predictions: Opus 4.7 15.4h/2.2h, Opus 4.8 20.0h/2.8h,
Mythos Preview 33.8h (p50).
"""
import numpy as np
from scipy import stats

# model: (AECI point estimate, METR p50 minutes, METR p80 minutes)
# METR values of None => model has an AECI but no METR result (prediction target).
MODELS = {
    "Claude 3 Opus":          (126.0, 3.952262,   0.638973),
    "Claude 3.5 Sonnet":      (130.0, 11.395377,  1.671757),
    "Claude 3.5 Sonnet (new)":(132.9, 20.522872,  2.595677),
    "Claude 3.7 Sonnet":      (139.4, 60.388937,  12.09179),
    "Claude Opus 4":          (141.8, 100.366123, 20.429752),
    "Claude Sonnet 4.5":      (145.5, None,       None),
    "Claude Opus 4.5":        (149.1, 292.994594, 49.430584),
    "Claude Opus 4.6":        (152.3, 718.80683,  69.874587),
    "Claude Opus 4.7":        (154.1, None,       None),
    "Claude Opus 4.8":        (155.5, None,       None),
    "Claude Mythos Preview":  (158.3, None,       None),
}

PUBLISHED = {  # from the article, for verification
    "p50": {"a": 2.9e-10, "b": 1.2053, "r2": 0.993},
    "p80": {"a": 1e-10,   "b": 1.1984, "r2": 0.981},
}
PUBLISHED_PREDICTIONS_HOURS = {
    "Claude Opus 4.7":       {"p50": 15.4, "p80": 2.2},
    "Claude Opus 4.8":       {"p50": 20.0, "p80": 2.8},
    "Claude Mythos Preview": {"p50": 33.8, "p80": None},  # p80 cropped in PDF
}


def fit(metric_idx):
    """OLS of ln(TH_minutes) on AECI over models with both values."""
    pts = [(v[0], v[metric_idx]) for v in MODELS.values() if v[metric_idx]]
    x = np.array([p[0] for p in pts])
    y = np.log([p[1] for p in pts])
    res = stats.linregress(x, y)
    return {"a": np.exp(res.intercept), "b": np.exp(res.slope),
            "r2": res.rvalue**2, "n": len(pts), "res": res}


def hours(minutes):
    return minutes / 60


def main():
    for name, idx in [("p50", 1), ("p80", 2)]:
        f = fit(idx)
        pub = PUBLISHED[name]
        print(f"--- {name}: TH_min = a * b^AECI  (n={f['n']}) ---")
        print(f"  fitted:    a = {f['a']:.3g}   b = {f['b']:.4f}   R^2 = {f['r2']:.3f}")
        print(f"  published: a = {pub['a']:.3g}   b = {pub['b']:.4f}   R^2 = {pub['r2']:.3f}")
        for model, target in PUBLISHED_PREDICTIONS_HOURS.items():
            aeci = MODELS[model][0]
            pred_h = hours(f["a"] * f["b"] ** aeci)
            pub_h = target[name]
            pub_s = f"(published {pub_h} h)" if pub_h else "(published value cropped)"
            print(f"  {model:24s} AECI {aeci}: predicted {pred_h:.1f} h {pub_s}")
        print()

    # Sanity check the article's note on Mythos Preview (early): METR measured
    # its p80 horizon at 3h06m on the early (Feb/Mar) checkpoint.
    early_p80_min = 185.911829  # claude_mythos_preview_early_inspect in the YAML
    print(f"Mythos Preview (early) measured p80: {early_p80_min:.0f} min "
          f"= {hours(early_p80_min):.2f} h (article says 3 h 6 min = 186 min)")


if __name__ == "__main__":
    main()
