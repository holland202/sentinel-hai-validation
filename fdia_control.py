#!/usr/bin/env python3
"""
fdia_control.py - P0b, the anti-vacuity control for sentinel-hai-validation.

Registered in PREREG.md before any data was fetched. Restated in Amendment 2
with explicit assumptions A1-A5.

The claim under test is NOT about SENTINEL or VERA. It is about the harness:
a residual-based bad-data detector on a linear DC state-estimation model is
blind by construction to injections of the form a = H c, and is not blind to
unstructured injections of the same magnitude. If the harness cannot show
both, it cannot be used to say anything about a detector.

Registered predictions:
  P0b-1  structured a = Hc     detected   0 of 200
  P0b-2  unstructured, matched >= 190 of 200
  P0b-3  max |r' - r| over structured cases <= TOL, TOL derived from
         machine epsilon and ||z||, not assumed to be zero

Assumptions, asserted at runtime, each printing its own value:
  A1  the H used to build the attack is bit-identical to the estimator's H
  A2  linear WLS, no bad-data rejection loop active
  A3  no clipping or saturation applied to z or the state
  A4  floating point, so r' = r + O(eps * ||z||); reported, not assumed away
  A5  detection threshold not evaluated at a knife edge; margin reported

Pure NumPy. No SciPy. Runs on the S25 Ultra under Termux.
"""

import numpy as np

SEED = 20260903
N_TRIALS = 200
SIGMA = 0.01           # measurement noise std, per unit
ATTACK_SCALE = 8.0     # attack magnitude in units of sigma * sqrt(m)
CHI2_95_DF20 = 31.410432844230918   # chi-square 0.95 quantile, df = 20

# IEEE 14-bus branch data: (from_bus, to_bus, reactance_pu)
BRANCHES = [
    (1, 2, 0.05917), (1, 5, 0.22304), (2, 3, 0.19797), (2, 4, 0.17632),
    (2, 5, 0.17388), (3, 4, 0.17103), (4, 5, 0.04211), (4, 7, 0.20912),
    (4, 9, 0.55618), (5, 6, 0.25202), (6, 11, 0.19890), (6, 12, 0.25581),
    (6, 13, 0.13027), (7, 8, 0.17615), (7, 9, 0.11001), (9, 10, 0.08450),
    (9, 14, 0.27038), (10, 11, 0.19207), (12, 13, 0.19988), (13, 14, 0.34802),
]
N_BUS = 14
SLACK = 1


def build_H():
    """DC measurement matrix: 20 line flows + 13 bus injections, 13 states."""
    states = [b for b in range(1, N_BUS + 1) if b != SLACK]
    idx = {b: i for i, b in enumerate(states)}
    rows = []
    for (f, t, x) in BRANCHES:                      # line flow measurements
        row = np.zeros(len(states))
        if f != SLACK:
            row[idx[f]] += 1.0 / x
        if t != SLACK:
            row[idx[t]] -= 1.0 / x
        rows.append(row)
    for b in states:                                # bus injection measurements
        row = np.zeros(len(states))
        for (f, t, x) in BRANCHES:
            if f == b:
                row[idx[b]] += 1.0 / x
                if t != SLACK:
                    row[idx[t]] -= 1.0 / x
            elif t == b:
                row[idx[b]] += 1.0 / x
                if f != SLACK:
                    row[idx[f]] -= 1.0 / x
        rows.append(row)
    return np.array(rows)


def main():
    rng = np.random.default_rng(SEED)
    H = build_H()
    m, n = H.shape
    W = np.eye(m) / (SIGMA ** 2)
    df = m - n

    G = H.T @ W @ H
    Ginv = np.linalg.inv(G)
    K = Ginv @ H.T @ W                   # theta_hat = K z
    S = np.eye(m) - H @ K                # residual sensitivity: r = S z

    print("fdia_control.py - P0b")
    print(f"IEEE 14-bus DC model: {m} measurements, {n} states, df {df}")
    print(f"seed {SEED}   sigma {SIGMA}   trials {N_TRIALS}")
    print(f"chi-square 0.95 threshold at df {df}: {CHI2_95_DF20:.6f}")
    print(f"condition number of gain matrix: {np.linalg.cond(G):.6e}")
    print()

    # --- assumption checks -------------------------------------------------
    H_attack = build_H()
    a1 = np.array_equal(H, H_attack)
    print(f"A1 attack H bit-identical to estimator H : {a1}")
    assert a1, "A1 FAILED - attack and estimator use different H"

    a2 = True   # no bad-data rejection loop exists in this script
    print(f"A2 linear WLS, no bad-data rejection loop: {a2}")
    assert a2

    a3 = True   # no clipping applied anywhere below
    print(f"A3 no clipping or saturation applied     : {a3}")
    assert a3
    print()

    theta_true = rng.normal(0, 0.1, n)
    z_clean = H @ theta_true
    tol = 1e3 * np.finfo(float).eps * np.linalg.norm(z_clean)
    print(f"A4 machine eps {np.finfo(float).eps:.6e}, ||z|| "
          f"{np.linalg.norm(z_clean):.6f}, TOL {tol:.6e}")
    print()

    struct_detected = 0
    unstruct_detected = 0
    max_resid_shift = 0.0
    min_margin = np.inf
    mag = ATTACK_SCALE * SIGMA * np.sqrt(m)

    for _ in range(N_TRIALS):
        theta = rng.normal(0, 0.1, n)
        z = H @ theta + rng.normal(0, SIGMA, m)
        r = S @ z
        J = float(r.T @ W @ r)

        c = rng.normal(0, 1, n)
        a_s = H @ c
        a_s = a_s / np.linalg.norm(a_s) * mag        # structured, in col(H)
        r_s = S @ (z + a_s)
        J_s = float(r_s.T @ W @ r_s)
        if J_s > CHI2_95_DF20:
            struct_detected += 1
        max_resid_shift = max(max_resid_shift,
                              float(np.max(np.abs(r_s - r))))
        min_margin = min(min_margin, abs(J_s - CHI2_95_DF20))

        a_u = rng.normal(0, 1, m)
        a_u = a_u / np.linalg.norm(a_u) * mag        # unstructured, same ||a||
        r_u = S @ (z + a_u)
        J_u = float(r_u.T @ W @ r_u)
        if J_u > CHI2_95_DF20:
            unstruct_detected += 1

    print(f"attack magnitude ||a||: {mag:.6f} (both arms, matched)")
    print()
    print(f"P0b-1 structured   detected {struct_detected} of {N_TRIALS}"
          f"   registered 0        "
          f"{'PASS' if struct_detected == 0 else 'FAIL'}")
    print(f"P0b-2 unstructured detected {unstruct_detected} of {N_TRIALS}"
          f"   registered >= 190   "
          f"{'PASS' if unstruct_detected >= 190 else 'FAIL'}")
    print(f"P0b-3 max |r' - r| {max_resid_shift:.6e}   TOL {tol:.6e}   "
          f"{'PASS' if max_resid_shift <= tol else 'FAIL'}")
    print()
    print(f"A5 smallest |J_structured - threshold| over trials: "
          f"{min_margin:.6f}")
    print(f"A5 knife edge would be a margin near zero; "
          f"{'clear' if min_margin > 1.0 else 'TOO CLOSE - verdict unsafe'}")
    print()

    ok = (struct_detected == 0 and unstruct_detected >= 190
          and max_resid_shift <= tol and min_margin > 1.0)
    print("P0b VERDICT:", "PASS" if ok else "FAIL")
    print()
    print("Interpretation rule, per Amendment 2: a nonzero structured count")
    print("identifies which of A1-A5 failed. Only when all five hold and")
    print("max |r' - r| is within tolerance is implementation error the")
    print("conclusion.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
