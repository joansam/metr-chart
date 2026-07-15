#!/usr/bin/env python3
"""ECI <-> AECI <-> METR time-horizon conversions.

Extends analysis/aeci_metr_conversion.py (which recreates Alexander Barry's
AECI -> time-horizon fit) with Epoch's public Capabilities Index, giving three
fitted relationships:

    1. AECI -> ln(TH)   Claude models with an AECI and a METR result (n=7)
    2. ECI  -> ln(TH)   all models with a public ECI and a METR result (~19,
                        cross-lab: Claude / GPT / o-series / Gemini)
    3. ECI  -> AECI     Claude models with both indices (n=10)

Data sources:
    - METR-Horizon-v1.1 p50/p80 estimates: benchmark_results_1_1 (5).yaml
    - Public ECI: analysis/data/epoch_capabilities_index.csv, downloaded from
      Epoch AI's Benchmarking Hub (https://epoch.ai/benchmarks, CC-BY 4.0).
      METR Time Horizons is NOT among the benchmarks that feed the ECI, so
      fit 2 is not circular.
    - AECI: analysis/data/aeci_fable5_systemcard.csv - Barry's extraction
      from the Fable/Mythos 5 system card chart (Datawrapper dataset behind
      his Jun 20 2026 post). Anthropic recalculate AECI values at each
      release; this is the current vintage.

Usage:
    python analysis/eci_conversions.py               # print fits + tables
    python analysis/eci_conversions.py --eci 160.4   # convert a new model
    python analysis/eci_conversions.py --aeci 158.3

Sensitivity switches (affect the ECI fits, mirroring Barry's Apr 30 post):
    --drop-reward-hacked   exclude GPT-5.3 Codex / GPT-5.4, whose METR
                           horizons were depressed by reward-hacking attempts
    --with-gpt35           add GPT-3.5 Instruct at ECI 119 (Epoch's
                           back-extension of the index to earlier LLMs)

Chart integration (same pattern as gen_model_data.py):
    --emit-js              print the PRED_RAW array for index.html
    --check-html           verify index.html's PRED_RAW matches the fits
"""
import argparse
import csv
import os
import re
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
METR_YAML = os.path.join(HERE, "..", "benchmark_results_1_1 (5).yaml")
ECI_CSV = os.path.join(HERE, "data", "epoch_capabilities_index.csv")
AECI_CSV = os.path.join(HERE, "data", "aeci_fable5_systemcard.csv")

# display name (must match the AECI csv) -> (metr_yaml_key, eci_model_version, lab)
# None means the model lacks that value.
MODELS = {
    "Claude 3 Opus":           ("claude_3_opus_inspect",              "claude-3-opus-20240229",     "anthropic"),
    "Claude 3.5 Sonnet":       ("claude_3_5_sonnet_20240620_inspect", "claude-3-5-sonnet-20240620", "anthropic"),
    "Claude 3.5 Sonnet (new)": ("claude_3_5_sonnet_20241022_inspect", "claude-3-5-sonnet-20241022", "anthropic"),
    "Claude 3.7 Sonnet":       ("claude_3_7_sonnet_inspect",          "claude-3-7-sonnet-20250219", "anthropic"),
    "Claude Opus 4":           ("claude_4_opus_inspect",              "claude-opus-4-20250514",     "anthropic"),
    "Claude Opus 4.1":         ("claude_4_1_opus_inspect",            "claude-opus-4-1-20250805",   "anthropic"),
    "Claude Sonnet 4.5":       (None,                                 "claude-sonnet-4-5-20250929", "anthropic"),
    "Claude Opus 4.5":         ("claude_opus_4_5_inspect",            "claude-opus-4-5-20251101",   "anthropic"),
    "Claude Opus 4.6":         ("claude_opus_4_6_inspect",            "claude-opus-4-6",            "anthropic"),
    "Claude Opus 4.7":         (None,                                 "claude-opus-4-7",            "anthropic"),
    "Claude Opus 4.8":         (None,                                 "claude-opus-4-8",            "anthropic"),
    # April 7 early checkpoint has a METR result; the AECI/ECI rows describe
    # the April 7 launch and June 9 release respectively, so no METR key here.
    "Claude Mythos Preview":   (None,                                 None,                         "anthropic"),
    "Claude Mythos/Fable 5":   (None,                                 "claude-fable-5",             "anthropic"),
    "GPT-4":                   ("gpt_4",                              "gpt-4-0314",                 "openai"),
    "GPT-4 Turbo":             ("gpt_4_turbo_inspect",                "gpt-4-turbo-2024-04-09",     "openai"),
    "GPT-4o":                  ("gpt_4o_inspect",                     "gpt-4o-2024-05-13",          "openai"),
    "o1-preview":              ("o1_preview",                         "o1-preview-2024-09-12",      "openai"),
    "o1":                      ("o1_inspect",                         "o1-2024-12-17",              "openai"),
    "o3":                      ("o3_inspect",                         "o3-2025-04-16",              "openai"),
    "GPT-5":                   ("gpt_5_2025_08_07_inspect",           "gpt-5-2025-08-07",           "openai"),
    "GPT-5.2":                 ("gpt_5_2",                            "gpt-5.2-2025-12-11",         "openai"),
    "GPT-5.3 Codex":           ("gpt_5_3_codex",                      "gpt-5.3-codex",              "openai"),
    "GPT-5.4":                 ("gpt_5_4",                            "gpt-5.4-2026-03-05",         "openai"),
    "Gemini 3 Pro":            ("gemini_3_pro",                       "gemini-3-pro-preview",       "google"),
    "Gemini 3.1 Pro":          ("gemini_3_1_pro",                     "gemini-3.1-pro-preview",     "google"),
}

# Sensitivity-analysis inputs (see Barry's Apr 30 post). GPT-3.5's ECI comes
# from Epoch's back-extension of the index; it is blank in the main CSV.
REWARD_HACKED = ("GPT-5.3 Codex", "GPT-5.4")
GPT35 = {"name": "GPT-3.5 Instruct", "metr_key": "gpt_3_5_turbo_instruct",
         "eci": 119.0, "lab": "openai"}

# Models with an AECI but no METR run: these get plotted in index.html as
# predictions from the AECI fit. Release dates from Epoch's CSV / system cards
# (Mythos Preview = the April 7 launch version, not METR's early checkpoint).
PREDICTED_DATES = {
    "Claude Sonnet 4.5":     "2025-09-29",
    "Claude Opus 4.7":       "2026-04-16",
    "Claude Opus 4.8":       "2026-05-28",
    "Claude Mythos Preview": "2026-04-07",
    "Claude Mythos/Fable 5": "2026-06-09",
}
HTML = os.path.join(HERE, "..", "index.html")


def load_metr(path=METR_YAML):
    """yaml_key -> (p50_minutes, p80_minutes) point estimates."""
    text = open(path, encoding="utf-8").read()
    out = {}
    for block in re.split(r"\n  (?=[a-z0-9_]+:)", text.split("\nresults:\n", 1)[1]):
        key = re.match(r"([a-z0-9_]+):", block.strip())
        if not key:
            continue
        vals = []
        for sec in ("p50_horizon_length", "p80_horizon_length"):
            m = re.search(sec + r":.*?estimate:\s*([\d.]+)", block, re.S)
            vals.append(float(m.group(1)) if m else None)
        out[key.group(1)] = tuple(vals)
    return out


VARIANT_SUFFIX = re.compile(r"_(low|medium|high|xhigh|max|none|minimal|unknown|\d+K)$")


def load_eci(path=ECI_CSV):
    """eci model version -> score. Reasoning-effort/context variants (_high,
    _32K, ...) share their base model's score; some models appear ONLY as
    variants, so also index the suffix-stripped base name."""
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if not r["ECI Score"]:
            continue
        score = float(r["ECI Score"])
        out[r["Model version"]] = score
        out.setdefault(VARIANT_SUFFIX.sub("", r["Model version"]), score)
    return out


def loglin_fit(x, y_minutes):
    """OLS ln(TH) = a + b*x. Returns predict(x)->minutes plus fit stats."""
    res = stats.linregress(np.asarray(x), np.log(y_minutes))
    return {"predict": lambda v: np.exp(res.intercept + res.slope * v),
            "slope": res.slope, "intercept": res.intercept,
            "r2": res.rvalue ** 2, "n": len(x),
            "doubling": np.log(2) / res.slope}


def ancova_fit(x, y_minutes, labs):
    """ln(TH) = a_lab + b*x: common slope, one intercept per lab."""
    labs_u = sorted(set(labs))
    y = np.log(y_minutes)
    X = np.column_stack([np.asarray(x, float)] +
                        [[1.0 if l == lu else 0.0 for l in labs] for lu in labs_u])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    slope, intercepts = beta[0], dict(zip(labs_u, beta[1:]))
    resid = y - X @ beta
    r2 = 1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
    return {"predict": lambda v, lab: np.exp(intercepts[lab] + slope * v),
            "slope": slope, "intercepts": intercepts, "r2": r2, "n": len(y),
            "doubling": np.log(2) / slope}


def lin_fit(x, y):
    res = stats.linregress(np.asarray(x), np.asarray(y))
    return {"predict": lambda v: res.intercept + res.slope * v,
            "invert": lambda v: (v - res.intercept) / res.slope,
            "slope": res.slope, "intercept": res.intercept,
            "r2": res.rvalue ** 2, "n": len(x)}


def load_aeci(path=AECI_CSV):
    """display name -> AECI point estimate."""
    return {r["model"]: float(r["aeci"])
            for r in csv.DictReader(open(path, encoding="utf-8"))}


def assemble(with_gpt35=False):
    metr, eci, aeci = load_metr(), load_eci(), load_aeci()
    rows = []
    for name, (mkey, ekey, lab) in MODELS.items():
        p50, p80 = metr.get(mkey, (None, None)) if mkey else (None, None)
        rows.append({"name": name, "p50": p50, "p80": p80, "lab": lab,
                     "eci": eci.get(ekey) if ekey else None,
                     "aeci": aeci.get(name)})
    if with_gpt35:
        p50, p80 = metr[GPT35["metr_key"]]
        rows.insert(0, {"name": GPT35["name"], "p50": p50, "p80": p80,
                        "lab": GPT35["lab"], "eci": GPT35["eci"], "aeci": None})
    return rows, eci


def build_fits(rows, drop=()):
    """drop: model names excluded from the ECI fits (the AECI fit is Barry's
    Claude-only regression and is never affected by the switches)."""
    fits = {}
    for m in ("p50", "p80"):
        a = [(r["aeci"], r[m]) for r in rows if r["aeci"] and r[m]]
        e = [(r["eci"], r[m], r["lab"]) for r in rows
             if r["eci"] and r[m] and r["name"] not in drop]
        fits[f"aeci_{m}"] = loglin_fit(*zip(*a))
        fits[f"eci_{m}"] = loglin_fit(*[[t[i] for t in e] for i in (0, 1)])
        fits[f"eci_{m}_lab"] = ancova_fit(*zip(*e))
    pairs = [(r["eci"], r["aeci"]) for r in rows if r["eci"] and r["aeci"]]
    fits["eci_aeci"] = lin_fit(*zip(*pairs))
    return fits


def predicted_rows(rows, fits):
    """Chart rows for models with an AECI but no METR result, predicted from
    the AECI fit. Values in minutes, matching M_RAW in index.html."""
    out = []
    for r in rows:
        if r["aeci"] is None or r["p50"] is not None:
            continue
        out.append({"n": r["name"].replace("Claude ", ""),
                    "d": PREDICTED_DATES[r["name"]], "aeci": r["aeci"],
                    "p": fits["aeci_p50"]["predict"](r["aeci"]),
                    "p80": fits["aeci_p80"]["predict"](r["aeci"]),
                    "l": r["lab"]})
    out.sort(key=lambda r: r["d"])
    return out


def emit_js(preds):
    lines = ["const PRED_RAW = ["]
    for r in preds:
        lines.append(f'  {{ n: {chr(34) + r["n"] + chr(34) + ",":18} d: "{r["d"]}", '
                     f'aeci: {r["aeci"]}, p: {r["p"]:.6f}, p80: {r["p80"]:.6f}, '
                     f'l: "{r["l"]}" }},')
    lines.append("];")
    return "\n".join(lines)


def check_html(preds):
    html = open(HTML, encoding="utf-8").read()
    ok = True
    for r in preds:
        m = re.search(r'n:\s*"' + re.escape(r["n"]) + r'",\s*d:\s*"([\d-]+)",\s*'
                      r'aeci:\s*([\d.]+),\s*p:\s*([\d.]+),\s*p80:\s*([\d.]+)', html)
        if not m:
            print(f"[MISSING] {r['n']}")
            ok = False
            continue
        want = [r["d"], r["aeci"], r["p"], r["p80"]]
        got = [m.group(1), *map(float, m.groups()[1:])]
        for w, g in zip(want, got):
            if (w != g) if isinstance(w, str) else abs(w - g) > 1e-4 * max(1, abs(w)):
                print(f"[DIFF] {r['n']}: {w} != {g}")
                ok = False
    print("OK: index.html PRED_RAW matches fits" if ok else "*** MISMATCH ***")
    return ok


def hours(minutes):
    return minutes / 60


def fmt_th(minutes):
    return f"{minutes:8.1f} min = {hours(minutes):7.2f} h"


def report(rows, fits, eci_all):
    print("=== Fitted relationships ===")
    for k, label in [("aeci_p50", "AECI -> p50 TH"), ("aeci_p80", "AECI -> p80 TH"),
                     ("eci_p50", "ECI  -> p50 TH"), ("eci_p80", "ECI  -> p80 TH")]:
        f = fits[k]
        print(f"{label}: ln(TH_min) = {f['intercept']:+.3f} {f['slope']:+.4f}*x   "
              f"R^2={f['r2']:.3f}  n={f['n']}  (TH doubles per {f['doubling']:.2f} pts)")
    for m in ("p50", "p80"):
        f = fits[f"eci_{m}_lab"]
        ints = "  ".join(f"{lab}={v:+.3f}" for lab, v in f["intercepts"].items())
        print(f"ECI  -> {m} TH, lab-adjusted: slope {f['slope']:+.4f}, intercepts {ints}   "
              f"R^2={f['r2']:.3f}  n={f['n']}")
    f = fits["eci_aeci"]
    print(f"ECI  -> AECI:  AECI = {f['intercept']:+.2f} {f['slope']:+.4f}*ECI   "
          f"R^2={f['r2']:.3f}  n={f['n']}")

    print("\n=== Per-model table (measured vs fitted, hours) ===")
    hdr = f"{'model':24s} {'ECI':>7s} {'AECI':>6s} | {'p50 meas':>9s} {'viaECI':>7s} {'viaAECI':>8s} | {'p80 meas':>9s} {'viaECI':>7s} {'viaAECI':>8s}"
    print(hdr)
    for r in rows:
        def cell(v, f=None, x=None):
            if f and x:
                return f"{hours(f['predict'](x)):7.1f}"
            return f"{hours(v):9.1f}" if v else " " * (9 if f is None else 7)
        p50e = cell(None, fits["eci_p50"], r["eci"]) if r["eci"] else "       "
        p50a = cell(None, fits["aeci_p50"], r["aeci"]) if r["aeci"] else "        "
        p80e = cell(None, fits["eci_p80"], r["eci"]) if r["eci"] else "       "
        p80a = cell(None, fits["aeci_p80"], r["aeci"]) if r["aeci"] else "        "
        if p50a.strip():
            p50a = f"{p50a:>8s}"
        if p80a.strip():
            p80a = f"{p80a:>8s}"
        eci_s = f"{r['eci']:7.2f}" if r["eci"] else " " * 7
        aeci_s = f"{r['aeci']:6.1f}" if r["aeci"] else " " * 6
        print(f"{r['name']:24s} {eci_s} {aeci_s} | "
              f"{cell(r['p50'])} {p50e} {p50a:>8s} | {cell(r['p80'])} {p80e} {p80a:>8s}")

    print("\nBarry's Jun 20 post predictions to reproduce: "
          "Mythos/Fable 5 p50 61.3 h, p80 8.2 h")


def convert(fits, eci=None, aeci=None, lab=None):
    if eci is not None and aeci is None:
        aeci = fits["eci_aeci"]["predict"](eci)
        print(f"ECI {eci:.2f} -> implied AECI {aeci:.1f}")
    elif aeci is not None and eci is None:
        eci = fits["eci_aeci"]["invert"](aeci)
        print(f"AECI {aeci:.1f} -> implied ECI {eci:.2f}")
    for m in ("p50", "p80"):
        via_e = fits[f"eci_{m}"]["predict"](eci)
        via_a = fits[f"aeci_{m}"]["predict"](aeci)
        print(f"  {m} horizon: via ECI fit {fmt_th(via_e)}   |   via AECI fit {fmt_th(via_a)}")
        if lab:
            via_l = fits[f"eci_{m}_lab"]["predict"](eci, lab)
            print(f"  {m} horizon, lab-adjusted ({lab}): {fmt_th(via_l)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eci", type=float, help="public Epoch ECI of a model")
    ap.add_argument("--aeci", type=float, help="Anthropic internal ECI of a model")
    ap.add_argument("--lab", choices=["anthropic", "openai", "google"],
                    help="also show the lab-adjusted ECI fit for this lab")
    ap.add_argument("--drop-reward-hacked", action="store_true",
                    help="exclude GPT-5.3 Codex / GPT-5.4 from the ECI fits")
    ap.add_argument("--with-gpt35", action="store_true",
                    help="add GPT-3.5 Instruct at ECI 119 to the ECI fits")
    ap.add_argument("--emit-js", action="store_true",
                    help="print PRED_RAW array for index.html")
    ap.add_argument("--check-html", action="store_true",
                    help="verify index.html PRED_RAW matches the fits")
    args = ap.parse_args()

    rows, eci_all = assemble(with_gpt35=args.with_gpt35)
    drop = REWARD_HACKED if args.drop_reward_hacked else ()
    fits = build_fits(rows, drop=drop)
    if args.emit_js or args.check_html:
        preds = predicted_rows(rows, fits)
        if args.emit_js:
            print(emit_js(preds))
        if args.check_html:
            sys.exit(0 if check_html(preds) else 1)
    elif args.eci is not None or args.aeci is not None:
        convert(fits, args.eci, args.aeci, args.lab)
    else:
        if drop:
            print(f"[sensitivity] ECI fits exclude: {', '.join(drop)}")
        if args.with_gpt35:
            print(f"[sensitivity] ECI fits include {GPT35['name']} at ECI {GPT35['eci']}")
        report(rows, fits, eci_all)


if __name__ == "__main__":
    main()
