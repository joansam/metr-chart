#!/usr/bin/env python3
"""AI-lab finance trends (annualized revenue + post-money valuations).

Source: Epoch AI "AI Companies" data hub (CC-BY 4.0, cite epoch.ai/data/ai-companies).
Snapshots live in data/ai_companies_revenue_reports.csv and
data/ai_companies_funding_rounds.csv; refresh them from
  https://epoch.ai/data/ai_companies_revenue_reports.csv
  https://epoch.ai/data/ai_companies_funding_rounds.csv

One uniform inclusion rule per series, no per-company exceptions:
  revenue:   Scope == "Full company" AND a date AND an annualized USD figure.
             All confidence tiers and all annualized-revenue types count; the
             ARR / run-rate / interpolation distinction is the labs' reporting
             inconsistency, surfaced in tooltips rather than filtered on.
  valuation: Status == "Closed" AND a close date AND a post-money valuation.
             Primary and secondary rounds alike — both are market-priced events.
One uniform trend rule: unweighted OLS of ln(USD) on time, fitted only when a
company has >= MIN_FIT_N included points in that series (dots always plot).

Usage:
    python3 finance_data.py            # fit report
    python3 finance_data.py --emit-js  # print the FIN_RAW/FIN_FITS block for index.html
    python3 finance_data.py --check-html   # verify index.html matches this script
    python3 finance_data.py --ledger   # score due ledger rows, append this vintage's predictions
"""
import argparse
import csv
import math
import re
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent
REV_CSV = HERE / "data" / "ai_companies_revenue_reports.csv"
FUND_CSV = HERE / "data" / "ai_companies_funding_rounds.csv"
HTML = HERE.parent / "index.html"

# Epoch company name -> the chart's lab key (COL / FIN_NAME in index.html).
# A refresh that introduces a company missing here fails loudly instead of
# silently dropping rows.
COMPANY_KEY = {
    "OpenAI": "openai",
    "Anthropic": "anthropic",
    "xAI": "xai",
    "Mistral AI": "mistral",
    "Cohere": "cohere",
    "Z.ai (Zhipu)": "zai",
    "Moonshot AI": "moonshot",
    "DeepSeek": "deepseek",
    "MiniMax": "minimax",
}

REV_TYPE_SHORT = {
    "Annual recurring revenue (ARR)": "ARR",
    "Annualized run rate": "run rate",
    "Period interpolation": "interpolated",
    "": "",
}

MIN_FIT_N = 4
T0 = date(2024, 1, 1)  # fit epoch: a = ln-slope per year, b = ln(USD) at T0


def _host(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)", url or "")
    return m.group(1) if m else ""


def _key(name):
    if name not in COMPANY_KEY:
        sys.exit(f"unknown company {name!r} in the Epoch CSVs — add it to "
                 f"COMPANY_KEY (and COL/FIN_NAME in index.html)")
    return COMPANY_KEY[name]


def load_rows():
    rows = []
    with open(REV_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not (r["Date"] and r["Annualized revenue (USD)"]
                    and r["Scope"] == "Full company"):
                continue
            rows.append({
                "c": _key(r["Company"]), "s": "rev", "d": r["Date"],
                "v": float(r["Annualized revenue (USD)"]),
                "t": REV_TYPE_SHORT.get(r["Annualized revenue type"],
                                        r["Annualized revenue type"]),
                "cf": r["Confidence"], "src": _host(r["Source 1"]),
            })
    with open(FUND_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not (r["Close date"] and r["Valuation (post-money)"]
                    and r["Status"] == "Closed"):
                continue
            rows.append({
                "c": _key(r["Company"]), "s": "val", "d": r["Close date"],
                "v": float(r["Valuation (post-money)"]),
                "t": (r["Type"].lower() + " round").strip(),
                "cf": r["Confidence"], "src": _host(r["Source 1"]),
            })
    rows.sort(key=lambda r: (r["s"], r["c"], r["d"]))
    return rows


def _yr(dstr):
    return (date.fromisoformat(dstr) - T0).days / 365.25


def fit_series(rows):
    """{series: {company: {a, b, n, r2}}} — OLS ln(USD) on years since T0."""
    fits = {"rev": {}, "val": {}}
    groups = {}
    for r in rows:
        groups.setdefault((r["s"], r["c"]), []).append(r)
    for (s, c), pts in groups.items():
        n = len(pts)
        if n < MIN_FIT_N:
            continue
        xs = [_yr(p["d"]) for p in pts]
        ys = [math.log(p["v"]) for p in pts]
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        a = sxy / sxx
        b = my - a * mx
        ss_res = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys))
        ss_tot = sum((y - my) ** 2 for y in ys)
        fits[s][c] = {"a": a, "b": b, "n": n, "r2": 1 - ss_res / ss_tot}
    return fits


def emit_js(rows, fits):
    out = []
    out.append("const FIN_RAW = [")
    for r in rows:
        v = f"{r['v']:.0f}"
        out.append(f'  {{ c: "{r["c"]}", s: "{r["s"]}", d: "{r["d"]}", v: {v}, '
                   f't: "{r["t"]}", cf: "{r["cf"]}", src: "{r["src"]}" }},')
    out.append("];")
    out.append("// ln(USD) = b + a*(years since 2024-01-01); OLS per company, n >= "
               f"{MIN_FIT_N} points.")
    out.append("const FIN_FITS = {")
    for s in ("rev", "val"):
        parts = ", ".join(
            f'{c}: {{ a: {f["a"]:.6f}, b: {f["b"]:.4f}, n: {f["n"]}, r2: {f["r2"]:.3f} }}'
            for c, f in sorted(fits[s].items()))
        out.append(f"  {s}: {{ {parts} }},")
    out.append("};")
    return "\n".join(out)


def check_html(rows, fits):
    html = HTML.read_text()
    ok = True

    def compare(what, want, got):
        nonlocal ok
        if want != got:
            print(f"[MISMATCH] {what}: script={want!r} html={got!r}")
            ok = False

    raw = re.findall(r'\{ c: "(\w+)", s: "(\w+)", d: "([\d-]+)", v: (\d+), '
                     r't: "([^"]*)", cf: "([^"]*)", src: "([^"]*)" \}', html)
    want_raw = [(r["c"], r["s"], r["d"], f"{r['v']:.0f}", r["t"], r["cf"], r["src"])
                for r in rows]
    if len(raw) != len(want_raw):
        print(f"[MISMATCH] FIN_RAW row count: script={len(want_raw)} html={len(raw)}")
        ok = False
    for w, g in zip(want_raw, raw):
        compare(f"FIN_RAW {w[0]}/{w[1]}/{w[2]}", w, g)

    for s in ("rev", "val"):
        for c, f in sorted(fits[s].items()):
            m = re.search(rf'{s}: \{{.*?{c}: \{{ a: (-?[\d.]+), b: (-?[\d.]+), '
                          rf'n: (\d+), r2: (-?[\d.]+) \}}', html)
            if not m:
                print(f"[MISSING fit] {s}/{c}")
                ok = False
                continue
            compare(f"FIN_FITS {s}/{c}",
                    [round(f["a"], 6), round(f["b"], 4), f["n"], round(f["r2"], 3)],
                    [float(m.group(1)), float(m.group(2)), int(m.group(3)),
                     float(m.group(4))])
    print("OK: index.html FIN_RAW+FIN_FITS match the CSVs" if ok else "*** MISMATCH ***")
    return ok


def fmt_usd(v):
    for div, unit in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if v >= div:
            return f"${v / div:.1f}{unit}"
    return f"${v:.0f}"


def report(rows, fits):
    for s, label in (("rev", "Annualized revenue (full company)"),
                     ("val", "Post-money valuation (closed rounds)")):
        print(f"=== {label} ===")
        by_c = {}
        for r in rows:
            if r["s"] == s:
                by_c.setdefault(r["c"], []).append(r)
        for c, pts in sorted(by_c.items(), key=lambda kv: -len(kv[1])):
            f = fits[s].get(c)
            last = pts[-1]
            span = f"{pts[0]['d']} .. {last['d']}"
            if f:
                growth = math.exp(f["a"])
                dbl = 12 * math.log(2) / f["a"]
                print(f"{c:10s} n={f['n']:2d}  {growth:5.2f}x/yr "
                      f"(doubles every {dbl:4.1f} mo)  R^2={f['r2']:.3f}  "
                      f"latest {fmt_usd(last['v']):>7s} ({last['d']})  [{span}]")
            else:
                print(f"{c:10s} n={len(pts):2d}  (< {MIN_FIT_N} points — dots only)  "
                      f"latest {fmt_usd(last['v']):>7s} ({last['d']})  [{span}]")
        print()


# ── Validation ledger ────────────────────────────────────────────────────────
# Out-of-sample scoring (see NOTES.md): each --ledger run appends what the
# CURRENT fits predict six months out, and scores any past prediction that has
# come due against the refreshed data. Predicted values are never edited after
# they are written — only the actual/actual_date fields get filled in.
LEDGER = HERE / "ledger.csv"
LEDGER_FIELDS = ["vintage", "series", "entity", "target_date", "predicted",
                 "unit", "actual", "actual_date", "note"]
HORIZON_DAYS = 183   # same six-month horizon the chart's trend lines draw
MATCH_DAYS = 60      # a due prediction scores against the nearest report this close


def run_ledger(rows, fits):
    today = date.today()
    entries = []
    if LEDGER.exists():
        with open(LEDGER, newline="", encoding="utf-8") as f:
            entries = list(csv.DictReader(f))

    # 1. Score due finance rows: nearest qualifying report within MATCH_DAYS
    # of the target date. th_* rows are event-based (empty target_date) and
    # are filled by hand when METR publishes a run.
    for e in entries:
        if e["actual"] or not e["target_date"] or e["series"] not in ("rev", "val"):
            continue
        target = date.fromisoformat(e["target_date"])
        if target > today:
            continue
        cands = [r for r in rows if r["s"] == e["series"] and r["c"] == e["entity"]
                 and abs((date.fromisoformat(r["d"]) - target).days) <= MATCH_DAYS]
        if not cands:
            print(f"[due, unscored] {e['series']}/{e['entity']} @ {e['target_date']}: "
                  f"no report within {MATCH_DAYS} days yet")
            continue
        hit = min(cands, key=lambda r: abs((date.fromisoformat(r["d"]) - target).days))
        e["actual"] = f"{hit['v']:.0f}"
        e["actual_date"] = hit["d"]
        ratio = hit["v"] / float(e["predicted"])
        print(f"[scored] {e['series']}/{e['entity']} @ {e['target_date']}: "
              f"predicted {fmt_usd(float(e['predicted']))}, actual {fmt_usd(hit['v'])} "
              f"({hit['d']}) — actual/predicted = {ratio:.2f}")

    # 2. Append this vintage's six-month-out predictions (skip duplicates so
    # re-running on the same day is a no-op).
    have = {(e["vintage"], e["series"], e["entity"]) for e in entries}
    target = today + timedelta(days=HORIZON_DAYS)
    added = 0
    for s in ("rev", "val"):
        for c, f in sorted(fits[s].items()):
            if (today.isoformat(), s, c) in have:
                continue
            pred = math.exp(f["b"] + f["a"] * _yr(target.isoformat()))
            entries.append({
                "vintage": today.isoformat(), "series": s, "entity": c,
                "target_date": target.isoformat(), "predicted": f"{pred:.0f}",
                "unit": "USD", "actual": "", "actual_date": "",
                "note": f"{math.exp(f['a']):.2f}x/yr fit, n={f['n']}, R2={f['r2']:.3f}",
            })
            added += 1
    with open(LEDGER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        w.writeheader()
        w.writerows(entries)
    print(f"ledger: {added} prediction(s) appended for vintage {today}, "
          f"{len(entries)} row(s) total")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-js", action="store_true",
                    help="print the FIN_RAW/FIN_FITS block for index.html")
    ap.add_argument("--check-html", action="store_true",
                    help="verify index.html FIN_RAW/FIN_FITS match the CSVs")
    ap.add_argument("--ledger", action="store_true",
                    help="score due ledger rows, append this vintage's predictions")
    args = ap.parse_args()
    rows = load_rows()
    fits = fit_series(rows)
    if args.emit_js:
        print(emit_js(rows, fits))
    elif args.check_html:
        sys.exit(0 if check_html(rows, fits) else 1)
    elif args.ledger:
        run_ledger(rows, fits)
    else:
        report(rows, fits)


if __name__ == "__main__":
    main()
