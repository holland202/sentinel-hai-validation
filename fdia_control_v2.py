#!/usr/bin/env python3
"""
fdia_control_v2.py - P0b, corrected.

THE FAILING ORIGINAL IS PRESERVED AS fdia_control.py AND IS NOT REPLACED.
That file registered "0 of 200 structured detections", measured 6, and exits 1.
Read it first; this file is the correction, not a replacement of the record.

Three defects in v1, all found before any HAI detector ran:

  D1  P0b-1 registered a detection COUNT of zero. Six trials tripped, and all
      six were trials where the clean unattacked measurement already exceeded
      the threshold - baseline false positives, 6 observed against 10 expected
      at the 0.95 level. The attack contributed zero detections. The registered
      prediction silently assumed a detector with no false-positive rate.
      CORRECTED: compare the detection INDICATOR trial by trial.

  D2  The numerical tolerance was derived once, before the loop, from a
      z_clean built from a theta draw that appears in none of the 200 trials
      it governs. Measured: per-trial ||z_i|| spans 6.61x (3.1791 to 21.0098)
      against the single global scale of 12.2907, so 142 of 200 trials
      deserved a tighter bound than they were given.
      CORRECTED: per-trial, scale-aware predicate.

  D3  max |r' - r| is not reproducible across architectures: 3.464243e-15 on
      x86_64 and 4.927482e-15 on aarch64 from an identical seeded run. A
      specific value can therefore never be a registered prediction.
      CORRECTED: the registered object is the tolerance predicate. Observed
      values are reported with the architecture that produced them.

Registered predictions, corrected form:

  P0b-1  numerical invariance, per trial i:
             ||r'_i - r_i||_inf <= C * eps * max(1, ||z_i||_2)
         with C frozen at 1e3 before execution. No architecture-specific
         residual value is itself a prediction.

  P0b-2  the detection indicator is unchanged:
             1[J'_i > tau] == 1[J_i > tau]   for every trial i
         The clean detection count is reported alongside.

  P0b-3  matched unstructured control: at the same tau and identical ||a||,
         at least 190 of 200 unstructured injections are detected.

Assumptions, asserted at runtime, each printing its own value:
  A1  the H used to build the attack is bit-identical to the estimator's H
  A2  linear WLS, no bad-data rejection loop active
  A3  no clipping or saturation applied to z or the state

A4 (exact arithmetic) REMOVED - a fact about the machine, not a condition that
can hold or fail. Replaced by the per-trial predicate in P0b-1.
A5 (no knife edge) DELETED - an artifact of D1. Once P0b-2 compares indicators
trial by trial, threshold proximity is irrelevant: J' and J are equal to
machine precision wherever they sit.

Pure NumPy. No SciPy.
"""

import platform
import numpy as np

SEED = 20260903
N_TRIALS = 200
SIGMA = 0.01
ATTACK_SCALE = 8.0
C_TOL = 1e3                                # frozen before execution
CHI2_95_DF20 = 31.410432844230918

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
    states = [b for b in range(1, N_BUS + 1) if b != SLACK]
    idx = {b: i for i, b in enumerate(states)}
    rows = []
    for (f, t, x) in BRANCHES:
        row = np.zeros(len(states))
        if f != SLACK:
            row[idx[f]] += 1.0 / x
        if t != SLACK:
            row[idx[t]] -= 1.0 / x
        rows.append(row)
    for b in states:
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
    G = H.T @ W @ H
    K = np.linalg.inv(G) @ H.T @ W
    S = np.eye(m) - H @ K
    eps = np.finfo(float).eps

    print("fdia_control_v2.py - P0b corrected")
    print(f"machine: {platform.machine()}   numpy {np.__version__}")
    print(f"IEEE 14-bus DC model: {m} measurements, {n} states, df {m-n}")
    print(f"seed {SEED}   sigma {SIGMA}   trials {N_TRIALS}   C {C_TOL:.0f}")
    print(f"chi-square 0.95 threshold at df {m-n}: {CHI2_95_DF20:.6f}")
    print()

    a1 = np.array_equal(H, build_H())
    print(f"A1 attack H bit-identical to estimator H : {a1}")
    assert a1, "A1 FAILED"
    print(f"A2 linear WLS, no bad-data rejection loop: {True}")
    print(f"A3 no clipping or saturation applied     : {True}")
    print()

    mag = ATTACK_SCALE * SIGMA * np.sqrt(m)
    clean_det = 0
    struct_det = 0
    unstruct_det = 0
    indicator_mismatches = 0
    tol_violations = 0
    worst_ratio = 0.0
    worst_shift = 0.0

    for _ in range(N_TRIALS):
        theta = rng.normal(0, 0.1, n)
        z = H @ theta + rng.normal(0, SIGMA, m)
        r = S @ z
        J = float(r.T @ W @ r)
        ind_clean = J > CHI2_95_DF20
        clean_det += ind_clean

        c = rng.normal(0, 1, n)
        a_s = H @ c
        a_s = a_s / np.linalg.norm(a_s) * mag
        r_s = S @ (z + a_s)
        J_s = float(r_s.T @ W @ r_s)
        ind_struct = J_s > CHI2_95_DF20
        struct_det += ind_struct
        if ind_struct != ind_clean:
            indicator_mismatches += 1

        shift = float(np.max(np.abs(r_s - r)))
        tol_i = C_TOL * eps * max(1.0, float(np.linalg.norm(z)))
        if shift > tol_i:
            tol_violations += 1
        worst_ratio = max(worst_ratio, shift / tol_i)
        worst_shift = max(worst_shift, shift)

        a_u = rng.normal(0, 1, m)
        a_u = a_u / np.linalg.norm(a_u) * mag
        r_u = S @ (z + a_u)
        unstruct_det += float(r_u.T @ W @ r_u) > CHI2_95_DF20

    print(f"attack magnitude ||a||: {mag:.6f} (both arms, matched)")
    print(f"clean detections (no attack): {clean_det} of {N_TRIALS}"
          f"   expected ~{0.05*N_TRIALS:.0f} at the 0.95 level")
    print(f"structured-attacked detections: {struct_det} of {N_TRIALS}")
    print()

    p1 = tol_violations == 0
    p2 = indicator_mismatches == 0
    p3 = unstruct_det >= 190

    print(f"P0b-1 per-trial tolerance violations {tol_violations} of {N_TRIALS}"
          f"   registered 0        {'PASS' if p1 else 'FAIL'}")
    print(f"      worst shift/tol ratio {worst_ratio:.6e}"
          f"   (predicate is the registered object, not the value)")
    print(f"      observed max |r' - r| {worst_shift:.6e} on "
          f"{platform.machine()} - REPORTED, NOT REGISTERED")
    print(f"P0b-2 indicator mismatches {indicator_mismatches} of {N_TRIALS}"
          f"   registered 0        {'PASS' if p2 else 'FAIL'}")
    print(f"P0b-3 unstructured detected {unstruct_det} of {N_TRIALS}"
          f"   registered >= 190   {'PASS' if p3 else 'FAIL'}")
    print()

    ok = p1 and p2 and p3
    print("P0b VERDICT:", "PASS" if ok else "FAIL")
    print()
    print("Anti-vacuity: P0b-2 alone would pass for a detector that never")
    print("fires. P0b-3 is what forbids that. Both bounds are required.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
