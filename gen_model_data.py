#!/usr/bin/env python3
"""Generate the M_RAW JS array for index.html directly from the METR YAML.

This is the foolproof data path: model horizon values are never hand-typed into
index.html. Edit SELECTION below (which models to show, their display name,
lab colour, and whether they feed the trend fit), then run:

    python gen_model_data.py            # prints the M_RAW array
    python gen_model_data.py --check    # verify index.html matches the YAML

Values in the YAML p50/p80 estimates are in MINUTES; index.html divides by 60.
"""
import re, sys

YAML = "benchmark_results_1_1 (5).yaml"
HTML = "index.html"

# yaml_key -> (display name, lab). This is purely the DISPLAY list — which models
# get plotted. SOTA/in-fit status is NOT set here: index.html computes the p50 and
# p80 frontiers (running max over time) at runtime, separately per horizon.
# Order here is irrelevant; output is sorted by release date.
SELECTION = {
    # --- slow segment (pre Jun 2024) ---
    "gpt2":                               ("GPT-2",             "openai"),
    "davinci_002":                        ("davinci-002",      "openai"),
    "gpt_3_5_turbo_instruct":             ("GPT-3.5 Instruct", "openai"),
    "gpt_4":                              ("GPT-4",            "openai"),
    "gpt_4_1106_inspect":                 ("GPT-4 1106",       "openai"),
    "gpt_4o_inspect":                     ("GPT-4o",           "openai"),
    # --- fast segment (Jun 2024+) ---
    "claude_3_5_sonnet_20240620_inspect": ("Claude 3.5 Sonnet","anthropic"),
    "o1_preview":                         ("o1-preview",       "openai"),
    "claude_3_5_sonnet_20241022_inspect": ("Claude 3.5S v2",   "anthropic"),
    "o1_inspect":                         ("o1",               "openai"),
    "claude_3_7_sonnet_inspect":          ("Claude 3.7",       "anthropic"),
    "o3_inspect":                         ("o3",               "openai"),
    "gpt_5_2025_08_07_inspect":           ("GPT-5",            "openai"),
    "gemini_3_pro":                       ("Gemini 3 Pro",     "google"),
    "gpt_5_1_codex_max_inspect":          ("GPT-5.1 Codex Max","openai"),
    "claude_opus_4_5_inspect":            ("Opus 4.5",         "anthropic"),
    "gpt_5_2":                            ("GPT-5.2",          "openai"),
    "claude_opus_4_6_inspect":            ("Opus 4.6",         "anthropic"),
    "gpt_5_3_codex":                      ("GPT-5.3 Codex",    "openai"),
    "gemini_3_1_pro":                     ("Gemini 3.1 Pro",   "google"),
    "gpt_5_4":                            ("GPT-5.4",          "openai"),
    "claude_mythos_preview_early_inspect":("Mythos Preview (Early)",    "anthropic"),
}

# Plot-date overrides where the YAML's release_date isn't the right date.
# Mythos Preview (Early): the system card reports Feb 24 2026 as when Mythos
# Preview became available for internal use; the YAML carries the April 7
# public-launch date.
DATE_OVERRIDES = {"claude_mythos_preview_early_inspect": "2026-02-24"}


def parse_yaml(path):
    text = open(path, encoding="utf-8").read()
    out = {}
    res = text.split("\nresults:\n", 1)[1]
    for b in re.split(r"\n  (?=\S)", "\n" + res):
        mk = re.match(r"\s*([a-z0-9_]+):", b)
        if not mk:
            continue
        def grab(sec):
            m = re.search(sec + r":\s*\n\s*ci_high:\s*([\d.]+)\s*\n\s*ci_low:\s*"
                          r"([\d.]+)\s*\n\s*estimate:\s*([\d.]+)", b)
            return (float(m.group(3)), float(m.group(2)), float(m.group(1))) if m else None
        rd = re.search(r"release_date:\s*([\d-]+)", b)
        out[mk.group(1)] = {
            "date": rd.group(1) if rd else None,
            "p50": grab("p50_horizon_length"),
            "p80": grab("p80_horizon_length"),
        }
    return out


def build_rows(Y):
    rows = []
    for key, (name, lab) in SELECTION.items():
        if key not in Y:
            raise SystemExit(f"ERROR: '{key}' not found in {YAML}")
        y = Y[key]
        rows.append({"n": name, "d": DATE_OVERRIDES.get(key, y["date"]), "l": lab,
                     "p50": y["p50"], "p80": y["p80"]})
    rows.sort(key=lambda r: r["d"])
    return rows


def fmt(v):
    return f"{v:.6f}".rstrip("0").rstrip(".")


def emit(rows):
    lines = ["const M_RAW = ["]
    for r in rows:
        p, lo, hi = r["p50"]
        p80, lo80, hi80 = r["p80"]
        name = f'"{r["n"]}",'
        lines.append(
            f'  {{ n: {name:24} d: "{r["d"]}", '
            f"p: {fmt(p)}, lo: {fmt(lo)}, hi: {fmt(hi)}, "
            f"p80: {fmt(p80)}, lo80: {fmt(lo80)}, hi80: {fmt(hi80)}, "
            f'l: "{r["l"]}" }},')
    lines.append("];")
    return "\n".join(lines)


def check(rows):
    html = open(HTML, encoding="utf-8").read()
    ok = True
    for r in rows:
        m = re.search(r'n:\s*"' + re.escape(r["n"]) + r'",\s*d:\s*"([\d-]+)",\s*'
                      r'p:\s*([\d.]+),\s*lo:\s*([\d.]+),\s*hi:\s*([\d.]+),\s*'
                      r'p80:\s*([\d.]+),\s*lo80:\s*([\d.]+),\s*hi80:\s*([\d.]+)', html)
        if not m:
            print(f"[MISSING] {r['n']}"); ok = False; continue
        want = [r["d"], *r["p50"], *r["p80"]]
        got = [m.group(1), *map(float, m.groups()[1:7])]
        for w, g in zip(want, got):
            if isinstance(w, float):
                if abs(w - g) > 1e-4 * max(1, abs(w)):
                    print(f"[DIFF] {r['n']}: {w} != {g}"); ok = False
            elif w != g:
                print(f"[DIFF] {r['n']}: {w} != {g}"); ok = False
    print("OK: index.html matches YAML" if ok else "*** MISMATCH ***")
    return ok


if __name__ == "__main__":
    Y = parse_yaml(YAML)
    rows = build_rows(Y)
    if "--check" in sys.argv:
        sys.exit(0 if check(rows) else 1)
    print(emit(rows))
    print(f"\n// {len(rows)} models displayed (SOTA/in-fit computed at runtime)",
          file=sys.stderr)
