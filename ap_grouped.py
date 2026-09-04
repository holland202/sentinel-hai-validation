#!/usr/bin/env python3
"""
ap_grouped.py - tie-invariant average precision, required for P5.

WHY THIS EXISTS. The first AP implementation written for this repository
broke ties by array index, which is what a stable argsort does. Measured on a
constructed case with 74 distinct score values:

    ties broken by index ascending  : 0.4613625489
    ties broken by index descending : 0.4522478316
    grouped, tie-invariant          : 0.4474675419

a swing of 0.0091147173 produced by nothing but tie order, and 50 of 50
within-group reshuffles changed the value. That implementation is WITHDRAWN
and must not be used for P5.

The interaction that makes it dangerous here is specific and not generic:

    equal detector score -> index-based tie order -> HAI attack labels are
    contiguous IN INDEX -> tie order correlates with the labels -> AP biased

JSD over a finite histogram produces many exact ties, so this is the expected
case for SENTINEL, not an edge case. This is the note054 defect class: a
published +0.117 that was sort-path dependent and whose tie-corrected value
was +0.1480.

REQUIRED INVARIANT
    Permuting observations within an equal-score group cannot change AP.

DEFINITION. AP is computed over DISTINCT SCORE VALUES. Observations sharing a
score form one threshold group; precision and recall are evaluated at group
boundaries only.

    AP = sum over groups i of (R_i - R_{i-1}) * P_i

Run this file directly to execute the selftest.
"""

import numpy as np


def average_precision(scores, y):
    """Tie-invariant average precision. scores, y are 1-D arrays; y in {0,1}."""
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y).astype(int)
    if scores.shape != y.shape:
        raise ValueError("scores and y must have the same shape")
    n_pos = int(y.sum())
    if n_pos == 0:
        raise ValueError("no positive labels: AP undefined")
    order = np.argsort(-scores, kind="stable")
    s, yy = scores[order], y[order]
    # index of the LAST element of each distinct-score group
    last = np.r_[np.nonzero(np.diff(s))[0], len(s) - 1]
    tp = np.cumsum(yy)[last]
    cnt = last + 1
    P = tp / cnt
    R = tp / n_pos
    R_prev = np.r_[0.0, R[:-1]]
    return float(((R - R_prev) * P).sum())


def _ap_by_index(scores, y):
    """The WITHDRAWN implementation. Kept only so the selftest can show it
    fails the invariant. Never use this for a registered result."""
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y).astype(int)
    o = np.argsort(-scores, kind="stable")
    yy = y[o]
    tp = np.cumsum(yy)
    prec = tp / np.arange(1, len(yy) + 1)
    return float((prec * yy).sum() / yy.sum())


def selftest():
    rng = np.random.default_rng(20260903)
    checks, failures = 0, 0

    def check(name, cond):
        nonlocal checks, failures
        checks += 1
        if not cond:
            failures += 1
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    print("ap_grouped.py selftest")
    print()

    # T1 perfect ranking
    check("T1 perfect ranking gives AP 1.0",
          abs(average_precision(np.array([9., 8., 7., 1., 0.]),
                                np.array([1, 1, 0, 0, 0])) - 1.0) < 1e-12)

    # T2 all scores tied -> AP must equal prevalence exactly
    y = np.array([1, 0, 0, 1, 0, 0, 0, 0, 1, 0])
    ap_tied = average_precision(np.zeros(10), y)
    check(f"T2 all-tied scores give AP == prevalence ({ap_tied:.6f} vs 0.300000)",
          abs(ap_tied - 0.3) < 1e-12)

    # T3 THE INVARIANT: within-group reshuffles must not move AP
    n = 4000
    y3 = np.zeros(n, int)
    for s0 in (300, 1500, 2900):
        y3[s0:s0 + 140] = 1
    sc3 = np.round(rng.normal(size=n) + 1.4 * y3, 1)
    base = average_precision(sc3, y3)
    moved_grouped = moved_index = 0
    base_idx = _ap_by_index(sc3, y3)
    for _ in range(50):
        o = np.lexsort((rng.permutation(n), -sc3))
        if abs(average_precision(sc3[o], y3[o]) - base) > 1e-12:
            moved_grouped += 1
        if abs(_ap_by_index(sc3[o], y3[o]) - base_idx) > 1e-12:
            moved_index += 1
    check(f"T3 grouped AP invariant under 50 within-group reshuffles "
          f"({moved_grouped} moved)", moved_grouped == 0)

    # T4 ANTI-VACUITY: the selftest must be able to detect a bad implementation
    check(f"T4 withdrawn index-order AP FAILS the same invariant "
          f"({moved_index} of 50 moved) - the test can return non-null",
          moved_index > 0)

    # T5 order of the input array must not matter at all
    perm = rng.permutation(n)
    check("T5 AP unchanged under a full input reordering",
          abs(average_precision(sc3[perm], y3[perm]) - base) < 1e-12)

    # T6 AP undefined with no positives, and says so
    try:
        average_precision(np.array([1., 2.]), np.array([0, 0]))
        raised = False
    except ValueError:
        raised = True
    check("T6 raises on zero positives rather than returning a number", raised)

    print()
    print(f"{checks - failures}/{checks} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
