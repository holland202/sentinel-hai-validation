#!/usr/bin/env python3
"""
sentinel.py - JSD sliding-window anomaly detector on HAI 20.07.

THE DETECTOR HAS NO PARAMETERS OF ITS OWN. Every constant is imported from
frozen.py, which is sealed at digest 6005fb60 and refuses to run if a value
changed. If you find a tunable number in this file that is not imported, that
is a defect.

Method, transferred from sentinel-batadal-validation without modification:
for each process channel, build a reference histogram over the fit split and a
running histogram over a sliding window of the evaluation stream, then score
each tick by the Jensen-Shannon divergence between them, summed over channels.
JSD is bounded in [0, ln 2] per channel with natural log.

ORDER OF OPERATIONS IS A GATE, NOT A CONVENIENCE.

    fit on train1[:60%]  ->  calibrate on train1[60%:]  ->  P0a
                                                             |
                                        P0a FAIL -> STOP. test1 is not read.
                                                             |
                                        P0a PASS -> score test1

P0a is the registered anti-vacuity check: the breach rate on the clean
calibration slice, which contains no attacks, must fall in
[0.5*alpha, 2*alpha]. A detector that alarms on data with no attacks cannot be
read as detecting attacks anywhere else. This script will not open test1 until
P0a passes, so the evaluation set is not touched before the gate that licenses
touching it.

train2 is never read: it contains 776 attack rows in two episodes, so it is
not clean training data. See Amendment 4.

Usage:
    python3 sentinel.py --p0a          # fit, calibrate, P0a only
    python3 sentinel.py --score        # the above, then score test1 if P0a passes
    python3 sentinel.py --quick        # 20000-row subsample, DEVELOPMENT ONLY

--quick is not a result and says so in its output.
"""

import argparse
import gzip
import json
import os
import sys
import time

import numpy as np

import frozen

DATA = "data"
LN2 = np.log(2.0)


def load(name, limit=None):
    """Read a HAI file. Returns (X, labels, channel_names)."""
    path = os.path.join(DATA, f"{name}.csv.gz")
    rows, labels = [], []
    with gzip.open(path, "rt") as f:
        header = [h.strip() for h in f.readline().rstrip("\n").split(frozen.DELIMITER)]
        keep = [i for i, h in enumerate(header)
                if h not in frozen.EXCLUDED_COLUMNS]
        li = header.index(frozen.PRIMARY_LABEL)
        for line in f:
            p = line.rstrip("\n").split(frozen.DELIMITER)
            if len(p) != len(header):
                continue
            rows.append([float(p[i]) for i in keep])
            labels.append(int(float(p[li])))
            if limit and len(rows) >= limit:
                break
    return (np.asarray(rows, dtype=float),
            np.asarray(labels, dtype=int),
            [header[i] for i in keep])


def reference_histograms(X):
    """Per-channel bin edges and reference densities from the fit split."""
    edges, ref = [], []
    for j in range(X.shape[1]):
        col = X[:, j]
        lo, hi = float(col.min()), float(col.max())
        if hi <= lo:
            hi = lo + 1e-12          # constant channel: one degenerate bin
        e = np.linspace(lo, hi, frozen.JSD_BINS + 1)
        h, _ = np.histogram(col, bins=e)
        edges.append(e)
        ref.append(h.astype(float) / max(1, h.sum()))
    return edges, np.asarray(ref)


def jsd_scores(X, edges, ref, window):
    """Summed per-channel Jensen-Shannon divergence over a sliding window.

    Bin indices are computed once per channel, then the window histogram is
    maintained incrementally, so cost is O(n * channels) rather than
    O(n * window * channels)."""
    n, m = X.shape
    idx = np.empty((n, m), dtype=np.int32)
    for j in range(m):
        idx[:, j] = np.clip(
            np.digitize(X[:, j], edges[j][1:-1]), 0, frozen.JSD_BINS - 1)

    counts = np.zeros((m, frozen.JSD_BINS), dtype=np.float64)
    scores = np.full(n, np.nan)
    eps = 1e-12
    for t in range(n):
        counts[np.arange(m), idx[t]] += 1.0
        if t >= window:
            counts[np.arange(m), idx[t - window]] -= 1.0
        if t + 1 < window:
            continue
        p = counts / window
        mix = 0.5 * (p + ref)
        kl_p = np.sum(p * np.log((p + eps) / (mix + eps)), axis=1)
        kl_q = np.sum(ref * np.log((ref + eps) / (mix + eps)), axis=1)
        scores[t] = float(np.sum(0.5 * (kl_p + kl_q)) / LN2)
    return scores


def conformal_quantile(cal_scores, alpha):
    """Split-conformal threshold, order-statistic convention as frozen."""
    s = np.sort(cal_scores[~np.isnan(cal_scores)])
    n = len(s)
    k = int(np.ceil((n + 1) * (1.0 - alpha)))
    k = min(max(k, 1), n)
    return float(s[k - 1]), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0a", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if not (a.p0a or a.score):
        a.p0a = True

    limit = 20000 if a.quick else None
    window = frozen.P5_REFERENCE_CONFIG[0]
    alpha = frozen.CONFORMAL_ALPHA

    print("sentinel.py - JSD sliding window on HAI 20.07")
    if a.quick:
        print("*** --quick: 20000-row subsample. NOT A RESULT. ***")
    print(f"freeze digest {frozen.FREEZE_DIGEST[:16]}  window {window}s  "
          f"bins {frozen.JSD_BINS}  alpha {alpha}")
    print()

    t0 = time.time()
    X, y, chans = load(frozen.FIT_FILE, limit)
    print(f"{frozen.FIT_FILE}: {X.shape[0]} rows, {X.shape[1]} channels, "
          f"{int(y.sum())} attack ticks  [{time.time()-t0:.1f}s]")
    assert y.sum() == 0, "fit file is not attack-free - see Amendment 4"

    cut = int(len(X) * frozen.FIT_FRACTION)
    Xf, rest = X[:cut], X[cut:]
    # The calibration remainder is split AGAIN, in temporal order. The
    # conformal quantile comes from the first half; P0a's breach rate is
    # measured on the second, which the quantile has never seen.
    #
    # WHY. The breach rate of a conformal quantile measured on the SAME scores
    # that produced it is (n-k)/n ~ alpha by construction, for any detector
    # whatsoever - noise, a constant, anything. Measured on the first run:
    # 0.099861 against alpha 0.1. That is arithmetic, not evidence, and P0a
    # would have been unable to fail. The registration says "a held-out
    # slice"; this makes it held out from the quantile as well as the fit.
    half = len(rest) // 2
    Xc, Xh = rest[:half], rest[half:]
    print(f"contiguous temporal split, no shuffling: fit {len(Xf)}  "
          f"calibrate {len(Xc)}  P0a held-out {len(Xh)}")

    edges, ref = reference_histograms(Xf)
    t1 = time.time()
    cal = jsd_scores(Xc, edges, ref, window)
    hld = jsd_scores(Xh, edges, ref, window)
    print(f"calibration and held-out scored [{time.time()-t1:.1f}s]")

    q, ncal = conformal_quantile(cal, alpha)
    self_breach = float(np.mean(cal[~np.isnan(cal)] > q))
    valid = hld[~np.isnan(hld)]
    breach = float(np.mean(valid > q))
    print(f"     in-sample breach on the calibration slice itself: "
          f"{self_breach:.6f} - this is ~alpha BY CONSTRUCTION and is "
          f"reported, never tested")
    lo, hi = 0.5 * alpha, 2.0 * alpha
    p0a = lo <= breach <= hi

    print()
    print(f"P0a  breach rate {breach:.6f} on {len(valid)} clean HELD-OUT "
          f"ticks (quantile from {ncal} separate ticks)")
    print(f"     registered interval [{lo}, {hi}]   threshold q {q:.6f}")
    print(f"     P0a {'PASS' if p0a else 'FAIL'}")
    print()

    out = {
        "quick": a.quick, "window": window, "alpha": alpha,
        "n_calibration": ncal, "n_heldout": int(len(valid)),
        "threshold": q, "breach_rate_heldout": breach,
        "breach_rate_in_sample": self_breach,
        "p0a_interval": [lo, hi], "p0a_pass": bool(p0a),
        "channels": len(chans), "fit_rows": int(len(Xf)),
    }

    if not p0a:
        print("P0a FAILED. test1 is NOT read. P1 and P3 are VOID.")
        print("The instrument cannot be read as detecting attacks anywhere.")
        json.dump(out, open("p0a_result.json", "w"), indent=2)
        return 1

    if not a.score:
        json.dump(out, open("p0a_result.json", "w"), indent=2)
        print("P0a passed. Re-run with --score to read test1.")
        return 0

    t2 = time.time()
    Xt, yt, _ = load(frozen.EVAL_FILE, limit)
    st = jsd_scores(Xt, edges, ref, window)
    print(f"{frozen.EVAL_FILE}: {Xt.shape[0]} rows, {int(yt.sum())} attack "
          f"ticks, scored [{time.time()-t2:.1f}s]")
    keep = ~np.isnan(st)
    np.save("sentinel_scores_test1.npy", st)
    out.update({
        "eval_rows": int(Xt.shape[0]),
        "eval_attack_ticks": int(yt.sum()),
        "scored_ticks": int(keep.sum()),
        "warmup_excluded": int((~keep).sum()),
        "scores_file": "sentinel_scores_test1.npy",
    })
    json.dump(out, open("p0a_result.json", "w"), indent=2)
    print("raw scores written to sentinel_scores_test1.npy")
    print("No metric has been computed. Scoring is a separate step.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
