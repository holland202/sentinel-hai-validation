#!/usr/bin/env python3
"""
evaluator_experiments.py - E1, E2, E13, E14.

STATUS: EXPLORATORY. These are NOT registered predictions and are not in
PREREG.md. They characterise the evaluator. They do not test a detector, and
no detector exists in this repository to test.

WHY ONLY FOUR. A proposed matrix of fourteen experiments, each with its own
acceptance and failure criteria, is a second research programme with its own
researcher degrees of freedom - the hazard the whole protocol exists to avoid.
Four are implemented here because each answers a question the evaluator cannot
answer about itself:

  E1  positive control  - can the evaluator recognise a perfect detector?
  E2  negative control  - can it survive a detector that predicts nothing?
  E13 adversarial matrix - how does it respond to pathological inputs?
  E14 metamorphic tests  - which transformations must leave a score unchanged?

WHAT THIS FILE DOES NOT DO. It does not define its own scoring. Every number
comes from the frozen implementations: ap_grouped.average_precision and
etapr_independent.evaluate, with theta passed explicitly from frozen.py. A
harness that computed its own metric would be measuring something other than
what the experiment reports, which is the defect this file was written to
avoid.

Synthetic data only. No HAI file is read.
"""

import sys

import numpy as np

import frozen
from ap_grouped import average_precision
from etapr_independent import evaluate as etapr_evaluate

TP = frozen.ETAPR_THETA_P
TR = frozen.ETAPR_THETA_R
N = 3000
SEED = 20260903


def truth(n=N):
    """Contiguous attack episodes, shaped like HAI: ~4% prevalence in blocks."""
    y = np.zeros(n, int)
    for a, b in [(300, 420), (1100, 1160), (2200, 2320)]:
        y[a:b] = 1
    return y


def score_both(pred, y):
    """Both frozen metrics on a binary prediction. Returns (AP, eTaPR f1)."""
    try:
        ap = average_precision(pred.astype(float), y)
    except ValueError:
        ap = float(frozen.EMPTY_PREDICTION_ETAPR)
    r = etapr_evaluate(y, pred, TP, TR)
    return ap, r["f1"], r


class Suite:
    def __init__(self):
        self.fail = []
        self.n = 0

    def check(self, name, ok, detail=""):
        self.n += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if detail:
            print(f"        {detail}")
        if not ok:
            self.fail.append(name)


def e1_positive(s, y):
    """E1. A perfect prediction must score at the top of both metrics."""
    print("E1 positive control - perfect detector")
    ap, f1, r = score_both(y.copy(), y)
    s.check("E1a perfect prediction gives AP 1.0", abs(ap - 1.0) < 1e-12,
            f"AP {ap:.12f}")
    s.check("E1b perfect prediction gives eTaPR f1 1.0", abs(f1 - 1.0) < 1e-12,
            f"eTaP {r['eTaP']:.6f}  eTaR {r['eTaR']:.6f}  f1 {f1:.12f}")
    print()


def e2_negative(s, y):
    """E2. A detector predicting nothing must produce a deterministic score
    and no exception.

    The two metrics correctly disagree here and E2 asserts both behaviours.
    The published eTaPR RAISES AttributeError on an empty prediction, so the
    registered EMPTY_PREDICTION_ETAPR applies to it. Average precision does
    not raise: an all-zero prediction is a constant score, whose AP is exactly
    the label prevalence. That is the correct AP null baseline and forcing it
    to 0 would be a fabrication - P5's circular-shift null values are
    themselves near prevalence, so a no-prediction configuration correctly
    yields p near 1 and is refuted. Zeroing AP would understate the null.

    An earlier version of this experiment asserted AP == EMPTY_PREDICTION_ETAPR
    and FAILED. The defect was in the assertion, not the evaluator. Kept here
    as the reason the two branches are asserted separately."""
    print("E2 negative control - detector predicts nothing")
    empty = np.zeros_like(y)
    crashed = False
    try:
        ap, f1, r = score_both(empty, y)
    except Exception as exc:
        crashed = True
        ap = f1 = None
        print(f"        raised {type(exc).__name__}: {exc}")
    s.check("E2a scoring an empty prediction does not raise", not crashed)
    if not crashed:
        prev = float(y.mean())
        s.check("E2b eTaPR on an empty prediction returns the registered value",
                f1 == frozen.EMPTY_PREDICTION_ETAPR,
                f"eTaPR f1 {f1}  registered {frozen.EMPTY_PREDICTION_ETAPR}")
        s.check("E2b2 AP on an empty prediction equals prevalence, "
                "NOT the registered eTaPR value",
                abs(ap - prev) < 1e-12,
                f"AP {ap:.12f}  prevalence {prev:.12f} - the correct AP null "
                f"baseline; forcing it to 0 would understate P5's null")
        a2, f2, _ = score_both(np.zeros_like(y), y)
        s.check("E2c the empty-prediction score is deterministic",
                (a2, f2) == (ap, f1))
    print()


def e13_adversarial(s, y):
    """E13. Pathological detectors through both frozen metrics. This does not
    assert a ranking; it RECORDS the response surface. The one assertion is
    that no pathological input outscores the perfect detector."""
    print("E13 adversarial matrix")
    rng = np.random.default_rng(SEED)
    n = len(y)
    cases = {}
    cases["perfect"] = y.copy()
    cases["inverted"] = 1 - y
    cases["constant all 1"] = np.ones(n, int)
    cases["single spike"] = np.zeros(n, int)
    cases["single spike"][350] = 1
    cases["random iid"] = (rng.random(n) < y.mean()).astype(int)
    for k in (1, 10, 100):
        cases[f"shift +{k}s"] = np.roll(y, k)
    frag = np.zeros(n, int)
    for a, b in [(300, 420), (1100, 1160), (2200, 2320)]:
        frag[a:b:4] = 1                      # same region, fragmented
    cases["fragmented"] = frag
    exp = np.zeros(n, int)
    for a, b in [(300, 420), (1100, 1160), (2200, 2320)]:
        exp[max(0, a - 60):min(n, b + 60)] = 1
    cases["expanded 60s"] = exp
    con = np.zeros(n, int)
    for a, b in [(300, 420), (1100, 1160), (2200, 2320)]:
        con[a + 30:b - 30] = 1
    cases["contracted 30s"] = con
    merged = np.zeros(n, int)
    merged[300:2320] = 1                     # spans all three episodes
    cases["merged"] = merged

    print(f"  {'detector':18s} {'AP':>10s} {'eTaP':>10s} {'eTaR':>10s} "
          f"{'eTaPR f1':>10s}")
    results = {}
    for name, p in cases.items():
        ap, f1, r = score_both(p, y)
        results[name] = (ap, f1)
        print(f"  {name:18s} {ap:10.6f} {r['eTaP']:10.6f} "
              f"{r['eTaR']:10.6f} {f1:10.6f}")
    print()
    best_ap = max(results, key=lambda k: results[k][0])
    best_f1 = max(results, key=lambda k: results[k][1])
    s.check("E13a no pathological input beats the perfect detector on AP",
            best_ap == "perfect", f"highest AP: {best_ap}")
    s.check("E13b no pathological input beats the perfect detector on eTaPR",
            best_f1 == "perfect", f"highest eTaPR f1: {best_f1}")
    s.check("E13c the constant-all-1 detector does not score highly",
            results["constant all 1"][1] < results["perfect"][1],
            f"constant eTaPR f1 {results['constant all 1'][1]:.6f}")
    print()
    return results


def e14_metamorphic(s, y):
    """E14. Transformations and whether each MUST leave the score unchanged.
    Generalises the invariant the withdrawn AP violated."""
    print("E14 metamorphic invariance")
    rng = np.random.default_rng(SEED)
    n = len(y)
    # continuous scores with heavy ties, as JSD over finite bins produces
    scores = np.round(rng.normal(size=n) + 1.2 * y, 1)
    base = average_precision(scores, y)

    # T1 MUST hold: permuting within an equal-score group cannot change AP
    moved = 0
    for _ in range(50):
        o = np.lexsort((rng.permutation(n), -scores))
        if abs(average_precision(scores[o], y[o]) - base) > 1e-12:
            moved += 1
    s.check("E14-T1 AP invariant to within-tie-group permutation (MUST)",
            moved == 0, f"{moved} of 50 moved, base AP {base:.12f}")

    # T2 MUST hold: a strictly increasing transform of scores preserves AP
    t2 = average_precision(np.exp(scores / 3.0), y)
    s.check("E14-T2 AP invariant to a strictly increasing transform (MUST)",
            abs(t2 - base) < 1e-9, f"{t2:.12f} vs {base:.12f}")

    # T3 MUST hold: eTaPR is invariant to relabelling time origin by a shift
    # applied to BOTH truth and prediction
    pred = (scores > np.quantile(scores, 0.95)).astype(int)
    r0 = etapr_evaluate(y, pred, TP, TR)["f1"]
    k = 137
    r1 = etapr_evaluate(np.roll(y, k), np.roll(pred, k), TP, TR)["f1"]
    s.check("E14-T3 eTaPR invariant to shifting truth and prediction together "
            "(MUST)", abs(r0 - r1) < 1e-9, f"{r0:.9f} vs {r1:.9f}")

    # T4 MUST NOT hold: shifting the prediction alone should change the score.
    # This is the anti-vacuity half - if it is invariant, the metric is not
    # time-aware and every temporal claim built on it is void.
    r2 = etapr_evaluate(y, np.roll(pred, k), TP, TR)["f1"]
    s.check("E14-T4 eTaPR CHANGES when only the prediction is shifted "
            "(MUST NOT be invariant)", abs(r0 - r2) > 1e-9,
            f"{r0:.9f} vs {r2:.9f} - the suite can detect a non-time-aware metric")
    print()


def main():
    quick = "--quick" in sys.argv
    y = truth()
    s = Suite()
    print("evaluator_experiments.py - E1, E2, E13, E14   EXPLORATORY, NOT REGISTERED")
    print(f"synthetic truth: n={len(y)}, {int(y.sum())} attack ticks "
          f"({100*y.mean():.2f}%), 3 contiguous episodes")
    print(f"metrics: ap_grouped.average_precision and etapr_independent.evaluate")
    print(f"theta_p {TP}  theta_r {TR}  empty-prediction score "
          f"{frozen.EMPTY_PREDICTION_ETAPR}")
    print()
    e1_positive(s, y)
    e2_negative(s, y)
    if not quick:
        e13_adversarial(s, y)
        e14_metamorphic(s, y)
    print(f"{s.n - len(s.fail)}/{s.n} checks passed")
    if s.fail:
        print("FAILED:", s.fail)
        print("An evaluator failure blocks detector work. Do not proceed.")
        return 1
    print("Evaluator characterised. These are EXPLORATORY results and are not")
    print("registered predictions. No detector has been run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
