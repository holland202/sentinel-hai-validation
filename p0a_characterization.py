#!/usr/bin/env python3
"""
p0a_characterization.py - descriptive analysis of the failed P0a gate.

THIS IS NOT CONFIRMATORY EVIDENCE. It is a post-result descriptive
characterisation of the score distributions behind the P0a failure recorded
at commit c96bc30. It registers nothing, tests nothing, and concludes nothing.

WHY IT EXISTS. P0a failed with a held-out breach rate of 0.042402 against a
registered interval of [0.05, 0.2]. It failed LOW: the detector alarms less
often on held-out clean data than nominal. The reference histograms come from
the EARLIEST slice, calibration from the MIDDLE, held-out from the LATEST, so
drift should push later scores AWAY from the reference and RAISE the breach
rate. It fell. That is unexplained and this file measures it rather than
explaining it.

Candidate patterns, stated as diagnostics and NOT as conclusions:

    mu(H1) > mu(H2) > mu(H3)          consistent with monotone movement
    mu(H1) ~ mu(H2) ~ mu(H3) < mu(C)  consistent with a level shift
    similar means, different SDs       consistent with a variance change
    no coherent pattern                weakens the simple temporal story

Distinguishing among these requires an experiment this file does not perform.

INVARIANTS ENFORCED
  I1  frozen.FIT_FILE is the only dataset input.
  I2  frozen.EVAL_FILE is never referenced. There is no code path to test1.
  I3  every detector constant comes from frozen.py.
  I4  no threshold, split, window or bin value is defined locally.
  I5  the recomputed held-out breach rate must match the committed
      p0a_result.json value within REPRO_TOL.
  I6  reproduction failure prints the discrepancy and exits nonzero with
      NO characterisation reported.
  I7  no pass/fail judgement is made on any distribution.
  I8  no hypothesis test and no p-value.
  I9  no test1 artefact is created.
  I10 output is labelled descriptive throughout.

The reproduction uses the SAME computational path as sentinel.py, including
its STRICT inequality: the breach indicator is (score > q), not (score >= q).
Using >= here would silently change the number being reproduced.

Writes p0a_score_characterization.json. Does NOT modify p0a_result.json,
which remains the immutable committed result.
"""

import json
import os
import sys

import numpy as np

import frozen
from sentinel import load, reference_histograms, jsd_scores, conformal_quantile

REPRO_TOL = 1e-12
QUANTILES = [1, 5, 10, 25, 50, 75, 90, 95, 99]


def describe(x, q_thresh):
    v = x[~np.isnan(x)]
    breaches = int(np.sum(v > q_thresh))          # strict, as in sentinel.py
    return {
        "n_scored": int(len(v)),
        "n_nan_warmup": int(len(x) - len(v)),
        "mean": float(np.mean(v)),
        "median": float(np.median(v)),
        "sd": float(np.std(v, ddof=1)),
        "min": float(np.min(v)),
        "max": float(np.max(v)),
        "quantiles": {f"q{p}": float(np.percentile(v, p)) for p in QUANTILES},
        "breach_count": breaches,
        "breach_rate": float(breaches / len(v)),
    }


def ks_statistic(a, b):
    """sup_x |F_a(x) - F_b(x)|. Descriptive only. No p-value (I8)."""
    a = np.sort(a[~np.isnan(a)])
    b = np.sort(b[~np.isnan(b)])
    grid = np.concatenate([a, b])
    fa = np.searchsorted(a, grid, side="right") / len(a)
    fb = np.searchsorted(b, grid, side="right") / len(b)
    return float(np.max(np.abs(fa - fb)))


def prob_superiority(a, b):
    """P(a random draw from a exceeds a random draw from b), ties at 0.5.
    A rank effect size, reported as a descriptive magnitude. Not a test."""
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    both = np.concatenate([a, b])
    order = np.argsort(both, kind="stable")
    ranks = np.empty(len(both), dtype=float)
    ranks[order] = np.arange(1, len(both) + 1)
    # average ranks within ties
    s = both[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = np.mean(ranks[order[i:j + 1]])
        i = j + 1
    ra = ranks[:len(a)].sum()
    u = ra - len(a) * (len(a) + 1) / 2.0
    return float(u / (len(a) * len(b)))


def main():
    print("p0a_characterization.py - DESCRIPTIVE, NOT CONFIRMATORY")
    print("Post-result characterisation of the P0a failure at c96bc30.")
    print("Registers nothing. Tests nothing. Concludes nothing.")
    print()

    if not os.path.exists("p0a_result.json"):
        print("p0a_result.json absent - nothing to reproduce", file=sys.stderr)
        return 1
    committed = json.load(open("p0a_result.json"))
    if committed.get("quick"):
        print("p0a_result.json is from a --quick subsample, not the full run",
              file=sys.stderr)
        return 1
    expected = committed["breach_rate_heldout"]

    window = frozen.P5_REFERENCE_CONFIG[0]        # I3, I4
    alpha = frozen.CONFORMAL_ALPHA

    X, y, chans = load(frozen.FIT_FILE)           # I1, I2 - FIT_FILE only
    assert y.sum() == 0, "fit file is not attack-free"
    n = len(X)
    cut = int(n * frozen.FIT_FRACTION)
    rest_lo, rest_hi = cut, n
    half = (rest_hi - rest_lo) // 2
    cal_lo, cal_hi = rest_lo, rest_lo + half
    hld_lo, hld_hi = rest_lo + half, rest_hi

    bounds = {
        "fit": [0, cut],
        "calibration_quantile": [cal_lo, cal_hi],
        "heldout": [hld_lo, hld_hi],
    }
    print("slice boundaries as row ranges [start, end), from the same "
          "constants the P0a run used:")
    for k, (a, b) in bounds.items():
        print(f"  {k:22s} [{a}, {b})   {b-a} rows")

    edges, ref = reference_histograms(X[:cut])
    s_fit = jsd_scores(X[:cut], edges, ref, window)
    s_cal = jsd_scores(X[cal_lo:cal_hi], edges, ref, window)
    s_hld = jsd_scores(X[hld_lo:hld_hi], edges, ref, window)

    q, ncal = conformal_quantile(s_cal, alpha)
    v_hld = s_hld[~np.isnan(s_hld)]
    observed = float(np.mean(v_hld > q))           # strict, as in sentinel.py

    print()
    print(f"reproduction: threshold q {q:.6f}   held-out breach rate "
          f"{observed:.6f}")
    print(f"              committed value          {expected:.6f}")
    if abs(observed - expected) > REPRO_TOL:       # I5, I6
        print()
        print("REPRODUCTION FAILURE", file=sys.stderr)
        print(f"  expected: {expected!r}", file=sys.stderr)
        print(f"  observed: {observed!r}", file=sys.stderr)
        print(f"  |diff|:   {abs(observed-expected):.3e} > tol {REPRO_TOL:g}",
              file=sys.stderr)
        print("NO CHARACTERIZATION REPORTED", file=sys.stderr)
        return 1
    print("              reproduced exactly")
    print()

    out = {
        "artefact_type": "descriptive characterization",
        "not_confirmatory": True,
        "experiment_commit_characterised": "c96bc30",
        "registers_nothing": True,
        "threshold_q": q,
        "alpha": alpha,
        "window_seconds": window,
        "slice_boundaries_rows": bounds,
        "reproduction": {"expected": expected, "observed": observed,
                         "tolerance": REPRO_TOL, "reproduced": True},
        "slices": {},
        "heldout_thirds": {},
        "comparisons": {},
    }

    print("SLICE SUMMARIES (descriptive)")
    hdr = f"  {'slice':22s} {'n':>7s} {'mean':>10s} {'sd':>9s} {'median':>10s} {'breach':>9s}"
    print(hdr)
    for name, arr in [("fit", s_fit), ("calibration_quantile", s_cal),
                      ("heldout", s_hld)]:
        d = describe(arr, q)
        out["slices"][name] = d
        print(f"  {name:22s} {d['n_scored']:7d} {d['mean']:10.4f} "
              f"{d['sd']:9.4f} {d['median']:10.4f} {d['breach_rate']:9.6f}")
    print()

    print("HELD-OUT TEMPORAL THIRDS (descriptive)")
    print(hdr)
    third = len(v_hld) // 3
    for i, lab in enumerate(["H1", "H2", "H3"]):
        seg = v_hld[i * third:(i + 1) * third] if i < 2 else v_hld[2 * third:]
        d = describe(seg, q)
        lo = hld_lo + i * third
        d["approx_row_range"] = [int(lo), int(lo + len(seg))]
        out["heldout_thirds"][lab] = d
        print(f"  {lab:22s} {d['n_scored']:7d} {d['mean']:10.4f} "
              f"{d['sd']:9.4f} {d['median']:10.4f} {d['breach_rate']:9.6f}")
    print()

    ks = ks_statistic(s_cal, s_hld)
    ps = prob_superiority(v_hld, s_cal[~np.isnan(s_cal)])
    out["comparisons"] = {
        "ks_statistic_calibration_vs_heldout": ks,
        "prob_heldout_exceeds_calibration": ps,
        "no_p_values": "I8: no hypothesis test is performed",
    }
    print(f"KS statistic, calibration vs held-out: {ks:.6f}  "
          f"(descriptive, no p-value)")
    print(f"P(held-out score > calibration score): {ps:.6f}  "
          f"(rank effect size; 0.5 means no separation)")
    print()

    m = {k: out["heldout_thirds"][k]["mean"] for k in ("H1", "H2", "H3")}
    mc = out["slices"]["calibration_quantile"]["mean"]
    print("DIAGNOSTIC PATTERNS - which pattern the numbers resemble. These "
          "are NOT conclusions and NOT causal claims.")
    print(f"  calibration mean {mc:.4f}   H1 {m['H1']:.4f}  "
          f"H2 {m['H2']:.4f}  H3 {m['H3']:.4f}")
    print("  monotone movement would show H1 > H2 > H3")
    print("  a level shift would show H1 ~ H2 ~ H3, all below calibration")
    print("  a variance change would show similar means, different SDs")
    print("  Distinguishing among these requires an experiment this file "
          "does not perform.")
    print()

    json.dump(out, open("p0a_score_characterization.json", "w"), indent=2)
    print("written: p0a_score_characterization.json")
    print("p0a_result.json is NOT modified; it remains the committed result.")
    print("No test1 artefact was created and no test1 code path exists here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
