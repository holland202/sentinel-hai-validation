#!/usr/bin/env python3
"""
etapr_independent.py - independent eTaPR, gate G9.

NO NOVELTY IS CLAIMED. eTaPR is prior work by the HAI authors
(github.com/saurf4ng/eTaPR, ACM SAC '22). This module exists only so the
repository can check its own scoring against the published implementation
rather than trusting it blindly, and so scoring works when the published one
crashes.

WHY IT EXISTS AT ALL. The published evaluate_w_streams raises AttributeError
when a detector predicts nothing: _etar_p() returns the scalar 0.0 on its
no-prediction guard while eTaR_p() calls .mean() on it. At threshold quantile
0.99 a sweep configuration may produce zero positive predictions, so the sweep
would die mid-run. This module returns the registered
frozen.EMPTY_PREDICTION_ETAPR instead.

ORDER OF WORK, which matters. etapr_fixture.json was generated from the
PUBLISHED package and committed at 98ffb09, BEFORE this file was written. The
fixture therefore cannot have been influenced by this implementation. Run this
file directly to check agreement against it.

DEFINITIONS at delta = 0, read from the published source, not from memory:

  M[i,j]   = overlap in ticks between anomaly i and prediction j
  maxA[i]  = length of anomaly i          (uniform func summed over the range)
  maxP[j]  = length of prediction j
  w[j]     = sqrt(length of prediction j)

  pruning  = iterative fixed point. Any anomaly row whose ratio is nonzero and
             below theta_r is zeroed; any prediction column whose ratio is
             nonzero and below theta_p is zeroed; repeat until stable.

  eTaR side is an UNWEIGHTED mean over anomalies, portion scores CLIPPED at 1.
  eTaP side is a sqrt-length-WEIGHTED mean over predictions, NOT clipped.
  That asymmetry is in the published implementation and is reproduced here.
"""

import json
import sys

import numpy as np

import frozen


def to_ranges(stream):
    """Contiguous blocks of 1s as (first, last) inclusive index pairs."""
    s = np.asarray(stream).astype(int)
    out, start = [], None
    for i, v in enumerate(s):
        if v == 1 and start is None:
            start = i
        elif v == 0 and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(s) - 1))
    return out


def evaluate(anomaly_stream, prediction_stream, theta_p, theta_r):
    A = to_ranges(anomaly_stream)
    P = to_ranges(prediction_stream)
    z = float(frozen.EMPTY_PREDICTION_ETAPR)
    if not A or not P:
        return {"eTaP": z, "eTaPd": z, "eTaPp": z,
                "eTaR": z, "eTaRd": z, "eTaRp": z, "f1": z,
                "empty": True}

    nA, nP = len(A), len(P)
    maxA = np.array([b - a + 1 for a, b in A], dtype=float)
    maxP = np.array([b - a + 1 for a, b in P], dtype=float)
    w = np.sqrt(maxP)
    W = w.sum()

    M = np.zeros((nA, nP))
    for i, (a0, a1) in enumerate(A):
        for j, (p0, p1) in enumerate(P):
            M[i, j] = max(0, min(a1, p1) - max(a0, p0) + 1)

    while True:                                   # pruning fixed point
        tars = M.sum(axis=1) / maxA
        kill_a = [i for i in range(nA) if 0.0 < tars[i] < theta_r]
        for i in kill_a:
            M[i, :] = 0.0
        taps = M.sum(axis=0) / maxP
        kill_p = [j for j in range(nP) if 0.0 < taps[j] < theta_p]
        for j in kill_p:
            M[:, j] = 0.0
        if not kill_a and not kill_p:
            break

    tars = M.sum(axis=1) / maxA
    taps = M.sum(axis=0) / maxP

    d_r = (tars >= theta_r).astype(float)
    p_r = np.clip(tars, None, 1.0)                # eTaR portion IS clipped
    eTaRd = float(d_r.sum() / nA)
    eTaRp = float(p_r.mean())
    eTaR = float(((d_r + d_r * p_r) / 2).mean())

    d_p = (taps >= theta_p).astype(float)
    p_p = taps                                    # eTaP portion is NOT clipped
    eTaPd = float((w * d_p).sum() / W)
    eTaPp = float((w * p_p).sum() / W)
    eTaP = float((w * ((d_p + d_p * p_p) / 2)).sum() / W)

    f1 = 0.0 if (eTaR + eTaP) == 0 else 2 * eTaR * eTaP / (eTaR + eTaP)
    return {"eTaP": eTaP, "eTaPd": eTaPd, "eTaPp": eTaPp,
            "eTaR": eTaR, "eTaRd": eTaRd, "eTaRp": eTaRp,
            "f1": float(f1), "empty": False}


def _rebuild_case(name, n):
    """Regenerate the fixture inputs deterministically. Must match gen."""
    def blocks(spans):
        v = [0] * n
        for a, b in spans:
            v[a:b] = [1] * (b - a)
        return v
    gt = blocks([(50, 110), (250, 300), (430, 520)])
    if name == "perfect":
        return gt, list(gt)
    if name == "none":
        return gt, blocks([])
    if name == "partial_overlap":
        return gt, blocks([(60, 100), (260, 270), (500, 560)])
    if name == "late_short":
        return gt, blocks([(105, 115), (295, 305), (515, 525)])
    if name == "many_false":
        return gt, blocks([(60, 100), (150, 160), (180, 190),
                           (330, 340), (360, 370), (n - 20, n)])
    if name == "one_long":
        return gt, blocks([(0, n)])
    if name == "random":
        rng = np.random.default_rng(20260903)
        return gt, [int(x) for x in (rng.random(n) < 0.12).astype(int)]
    if name == "cascade_prune":
        fx = json.load(open("etapr_fixture.json"))
        rr = fx["cascade_ranges"]
        n2 = fx["n_cascade"]
        def sp(spans):
            v = [0] * n2
            for a, b in spans:
                v[a:b + 1] = [1] * (b - a + 1)
            return v
        return sp(rr["anomalies"]), sp(rr["predictions"])
    raise KeyError(name)


def check(path="etapr_fixture.json", tol=1e-9):
    fx = json.load(open(path))
    tp, tr, n = fx["theta_p"], fx["theta_r"], fx["n"]
    print("etapr_independent.py - G9 agreement check")
    print(f"fixture from published eTaPR at {fx['etapr_commit']}, "
          f"theta_p {tp} theta_r {tr} delta {fx['delta']}")
    print(f"registered empty-prediction score: {frozen.EMPTY_PREDICTION_ETAPR}")
    print()
    keys = ("eTaP", "eTaPd", "eTaPp", "eTaR", "eTaRd", "eTaRp", "f1")
    failures = 0
    for name in sorted(fx["cases"]):
        ref = fx["cases"][name]
        a, p = _rebuild_case(name, n)
        got = evaluate(a, p, tp, tr)
        if "error" in ref:
            print(f"{name}: published implementation CRASHED "
                  f"({ref['error'].split(':')[0]})")
            print(f"   independent returns {got['eTaP']:.6f} for every field "
                  f"- registered value, no crash")
            continue
        worst = max(abs(got[k] - ref[k]) for k in keys)
        ok = worst <= tol
        if not ok:
            failures += 1
        print(f"{name}: {'AGREE' if ok else 'DISAGREE'}   max abs diff {worst:.3e}")
        if not ok:
            for k in keys:
                if abs(got[k] - ref[k]) > tol:
                    print(f"     {k}: independent {got[k]:.12f}  "
                          f"published {ref[k]:.12f}")
    print()
    if failures:
        print(f"G9 FAIL - {failures} case(s) disagree beyond {tol:g}")
        print("A disagreement halts scoring. It is the finding; the")
        print("implementation giving the nicer number is NOT selected.")
        return 1
    print(f"G9 PASS - all comparable cases agree within {tol:g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(check())
