#!/usr/bin/env python3
"""
frozen.py - every constant that must be fixed before a HAI detector runs.

This module replaces the proposed FROZEN.md. A prose file can claim a value is
frozen while the code uses a different one; a module the detector IMPORTS
cannot. Detectors must read every constant from here and never redefine one
locally.

TAMPER DETECTION. FREEZE_DIGEST is the sha256 of the canonical serialisation
of FROZEN. Change any value and the digest stops matching, the selftest exits
1, and CI fails. The digest is what an amendment cites, so an independent
observer can confirm the values that were registered are the values that ran.

INCOMPLETE BY DESIGN. PENDING lists constants that are not yet fixed. While
PENDING is non-empty this module exits 1, so an unfinished freeze is a loud
failure rather than a forgotten TODO.

Run directly to execute the selftest.
"""

import hashlib
import json

# ---------------------------------------------------------------- dataset
DATASET = "HAI 20.07"
UPSTREAM_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
N_COLUMNS = 64
DELIMITER = ";"

# train2 carries 776 attack rows (0.322%) and is excluded. train1 is clean:
# 0 of 309,600. Measured, not assumed. See Amendment 4.
FIT_FILE = "train1"
EVAL_FILE = "test1"          # P1, P3 and P5 all score here
REPLICATION_FILE = "test2"   # reserved, untouched
EXCLUDED_FILE = "train2"

# --------------------------------------------------------------- labelling
# The HAI README states `attack` applies to all processes while the other
# three apply only to their corresponding control process. Measured: `attack`
# is exactly OR(attack_P1, attack_P2, attack_P3), 0 mismatches in 995,400
# rows. Chosen from the specification, not from which label scores better.
PRIMARY_LABEL = "attack"
SECONDARY_LABELS = ("attack_P1", "attack_P2", "attack_P3")  # descriptive only
EXCLUDED_COLUMNS = ("time", "attack", "attack_P1", "attack_P2", "attack_P3")

# ------------------------------------------------------------------ split
# Contiguous temporal blocks. At 1-second sampling adjacent rows are near
# duplicates, so a random split leaks. No shuffling at any point.
SPLIT_STRATEGY = "contiguous_temporal"
FIT_FRACTION = 0.60          # first 60% of train1
CALIBRATION_FRACTION = 0.40  # last 40% of train1, also the P0a clean slice
SHUFFLE = False

# ------------------------------------------------------------- detectors
# alpha = 0.10, nominal coverage 0.90. Chosen to match the level at which
# VERA's BATADAL coverage failure was measured (0.697 against nominal 0.90),
# so P3 tests whether that failure reproduces rather than testing a
# differently tuned quantity. Registered, not merely frozen: P3's 0.05
# shortfall is an absolute threshold whose stringency depends on this value.
CONFORMAL_ALPHA = 0.10
QUANTILE_CONVENTION = "order_statistic_ceil_n_plus_1"
JSD_BINS = 64
RIDGE_LAMBDA = 1.0
WARMUP_POLICY = "exclude_first_max_window_ticks_from_scoring"
SEED = 20260903
RNG = "numpy.random.default_rng"   # PCG64; legacy RandomState differs

# ------------------------------------------------------------ P1 sweep grid
# 3 x 3 = 9 configurations, enumerated. Deliberately small: with enough
# configurations, two metrics disagreeing somewhere becomes near-certain and
# P1 stops being a claim. Enlarging this grid after seeing results would be
# fraud, not amendment.
WINDOW_GRID_SECONDS = (30, 60, 120)
THRESHOLD_QUANTILE_GRID = (0.90, 0.95, 0.99)
RANKING_RULE = "argmax_over_enumerated_grid"
DISAGREEMENT_CRITERION = "argmax_F1 != argmax_eTaPR"

# --------------------------------------------------------------------- P5
# Circular shift, not iid permutation. The permutation null false-passed a
# useless autocorrelated detector 30% (phi=0.9) and 47% (phi=0.999) of the
# time at a nominal 1%; circular shift measured 0% and 1%. See the third and
# fourth pass documents.
P5_NULL = "circular_shift"
P5_B = 999
P5_SEED = 20260903
P5_SHIFT_LOW = 1                      # k = 0 excluded
P5_SHIFT_REPLACEMENT = True           # sampled with replacement
P5_COMPARISON = ">="                  # AP_b >= AP_obs counts toward p
P5_CORRECTION = "plus_one_numerator_and_denominator"
P5_ALPHA = 0.01
P5_TEST_TYPE = "monte_carlo_randomization"   # NOT exact; reference set sampled
P5_AP = "grouped_tie_invariant"       # ap_grouped.average_precision
P5_REFERENCE_CONFIG = (60, 0.95)      # (window seconds, threshold quantile)


# ------------------------------------------------------------------ eTaPR
# github.com/saurf4ng/eTaPR at commit af9e7ae.
#
# DEFECT IN THE PUBLISHED PACKAGE, recorded not smoothed over: eTaPR does not
# have one set of defaults, it has three and they disagree.
#   README CLI documentation      theta_p 0.5   theta_r 0.1    delta 0.0
#   README worked example         theta_p 0.5   theta_r 0.01
#   evaluate_w_streams signature  theta_p 0.7   theta_r 0.1    delta 0.0
#   evaluate_w_ranges signature   no defaults, both required
# "eTaPR at published defaults" is therefore not a well-defined instruction.
# Our data is per-tick, so evaluate_w_streams is the natural entry point - and
# it is the one whose signature (0.7) contradicts the documentation (0.5).
#
# Registered: the DOCUMENTED values, passed EXPLICITLY on every call so that
# no signature default can ever silently apply.
ETAPR_UPSTREAM_COMMIT = "af9e7ae"
ETAPR_ENTRY_POINT = "evaluate_w_streams"
ETAPR_THETA_P = 0.5
ETAPR_THETA_R = 0.1
ETAPR_DELTA = 0.0
ETAPR_PASS_EXPLICITLY = True

# ------------------------------------------------------------------- P0b
P0B_C_TOL = 1000.0
P0B_TRIALS = 200
P0B_UNSTRUCTURED_MIN = 190

FROZEN = {
    "DATASET": DATASET, "UPSTREAM_COMMIT": UPSTREAM_COMMIT,
    "N_COLUMNS": N_COLUMNS, "DELIMITER": DELIMITER,
    "FIT_FILE": FIT_FILE, "EVAL_FILE": EVAL_FILE,
    "REPLICATION_FILE": REPLICATION_FILE, "EXCLUDED_FILE": EXCLUDED_FILE,
    "PRIMARY_LABEL": PRIMARY_LABEL, "SECONDARY_LABELS": SECONDARY_LABELS,
    "EXCLUDED_COLUMNS": EXCLUDED_COLUMNS,
    "SPLIT_STRATEGY": SPLIT_STRATEGY, "FIT_FRACTION": FIT_FRACTION,
    "CALIBRATION_FRACTION": CALIBRATION_FRACTION, "SHUFFLE": SHUFFLE,
    "CONFORMAL_ALPHA": CONFORMAL_ALPHA,
    "QUANTILE_CONVENTION": QUANTILE_CONVENTION,
    "JSD_BINS": JSD_BINS, "RIDGE_LAMBDA": RIDGE_LAMBDA,
    "WARMUP_POLICY": WARMUP_POLICY, "SEED": SEED, "RNG": RNG,
    "WINDOW_GRID_SECONDS": WINDOW_GRID_SECONDS,
    "THRESHOLD_QUANTILE_GRID": THRESHOLD_QUANTILE_GRID,
    "RANKING_RULE": RANKING_RULE,
    "DISAGREEMENT_CRITERION": DISAGREEMENT_CRITERION,
    "P5_NULL": P5_NULL, "P5_B": P5_B, "P5_SEED": P5_SEED,
    "P5_SHIFT_LOW": P5_SHIFT_LOW,
    "P5_SHIFT_REPLACEMENT": P5_SHIFT_REPLACEMENT,
    "P5_COMPARISON": P5_COMPARISON, "P5_CORRECTION": P5_CORRECTION,
    "P5_ALPHA": P5_ALPHA, "P5_TEST_TYPE": P5_TEST_TYPE, "P5_AP": P5_AP,
    "P5_REFERENCE_CONFIG": P5_REFERENCE_CONFIG,
    "ETAPR_UPSTREAM_COMMIT": ETAPR_UPSTREAM_COMMIT,
    "ETAPR_ENTRY_POINT": ETAPR_ENTRY_POINT,
    "ETAPR_THETA_P": ETAPR_THETA_P, "ETAPR_THETA_R": ETAPR_THETA_R,
    "ETAPR_DELTA": ETAPR_DELTA,
    "ETAPR_PASS_EXPLICITLY": ETAPR_PASS_EXPLICITLY,
    "P0B_C_TOL": P0B_C_TOL, "P0B_TRIALS": P0B_TRIALS,
    "P0B_UNSTRUCTURED_MIN": P0B_UNSTRUCTURED_MIN,
}

# Not yet fixed. This module fails while anything remains here.
PENDING = {}


def digest():
    blob = json.dumps(FROZEN, sort_keys=True, default=list).encode()
    return hashlib.sha256(blob).hexdigest()


# Recorded after the first clean run and cited by the amendment. Set to None
# until the freeze is complete; a real value here makes tampering detectable.
FREEZE_DIGEST = "99d6608c762203f7231f04ee3c9464c60320110a185c0ca97f260eae119ff83b"


def selftest():
    print("frozen.py selftest")
    print()
    for k in sorted(FROZEN):
        print(f"  {k:26s} = {FROZEN[k]!r}")
    print()
    d = digest()
    print(f"  digest over {len(FROZEN)} frozen constants: {d}")

    ok = True
    if PENDING:
        print()
        print(f"  FREEZE INCOMPLETE - {len(PENDING)} constant(s) still pending:")
        for k, why in sorted(PENDING.items()):
            print(f"    {k}: {why}")
        ok = False
    if FREEZE_DIGEST is None:
        print()
        print("  FREEZE_DIGEST is None - the freeze has not been sealed.")
        ok = False
    elif FREEZE_DIGEST != d:
        print()
        print(f"  DIGEST MISMATCH - a frozen constant changed after sealing.")
        print(f"    sealed:   {FREEZE_DIGEST}")
        print(f"    computed: {d}")
        ok = False

    print()
    print("FREEZE:", "SEALED" if ok else "NOT SEALED")
    if not ok:
        print("No HAI detector may run while the freeze is not sealed.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
