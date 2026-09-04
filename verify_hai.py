#!/usr/bin/env python3
"""
verify_hai.py - gates G3 (schema) and G4 (training cleanliness).

Reads all four HAI 20.07 files and checks them against expectations registered
here BEFORE any detector runs. Every number printed is measured on the file,
not recalled.

Why G4 exists: P0a's premise is that training data contains no attacks. That
premise is FALSE for train2, which carries 776 attack rows. It was assumed
clean until it was measured. This script exists so nobody assumes again.

The expected counts below were measured in Claude's container on 2026-09-03 at
upstream commit 2a814ce. If the device disagrees, that is a finding and must be
reported, not edited away.

Anti-vacuity: the script must be able to return a failure. Run with
--sabotage to corrupt an expectation in memory and confirm a non-zero exit.

Reads gzip directly; nothing is decompressed to disk. train1 alone is
130,293,220 bytes uncompressed.
"""

import gzip
import sys
import os

import frozen

LABELS = ("attack", "attack_P1", "attack_P2", "attack_P3")

# Registered expectations. Measured, not assumed.
EXPECTED = {
    "train1": {"rows": 309600, "attack": 0,     "P1": 0,    "P2": 0,    "P3": 0},
    "train2": {"rows": 241200, "attack": 776,   "P1": 776,  "P2": 0,    "P3": 0},
    "test1":  {"rows": 291600, "attack": 11538, "P1": 9683, "P2": 2495, "P3": 1197},
    "test2":  {"rows": 153000, "attack": 5989,  "P1": 5207, "P2": 3510, "P3": 604},
}
CLEAN_FILES = ("train1",)          # the only files P0a may use
CONTAMINATED_FILES = ("train2",)


def scan(path):
    """Return (n_rows, n_cols, counts, or_mismatches). Parses only the
    trailing label fields; the other 60 columns are never split."""
    counts = {k: 0 for k in LABELS}
    or_mismatch = 0
    n = 0
    with gzip.open(path, "rt") as f:
        header = f.readline().rstrip("\n").split(frozen.DELIMITER)
        ncols = len(header)
        tail = [h.strip() for h in header[-4:]]
        if tuple(tail) != LABELS:
            raise ValueError(f"last four columns are {tail}, expected {list(LABELS)}")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.rsplit(frozen.DELIMITER, 4)
            if len(parts) != 5:
                continue
            n += 1
            v = [int(float(x)) for x in parts[1:]]
            for k, val in zip(LABELS, v):
                counts[k] += val
            if v[0] != (1 if (v[1] or v[2] or v[3]) else 0):
                or_mismatch += 1
    return n, ncols, counts, or_mismatch


def main():
    sabotage = "--sabotage" in sys.argv
    exp = {k: dict(v) for k, v in EXPECTED.items()}
    if sabotage:
        exp["train2"]["attack"] = 0     # the assumption that was false
        print("SABOTAGE: train2 attack expectation forced to 0\n")

    print("verify_hai.py - gates G3 schema and G4 training cleanliness")
    print(f"dataset {frozen.DATASET} at upstream {frozen.UPSTREAM_COMMIT[:12]}")
    print(f"expected columns {frozen.N_COLUMNS}, delimiter {frozen.DELIMITER!r}")
    print()

    failures = []
    for name in ("train1", "train2", "test1", "test2"):
        path = os.path.join("data", f"{name}.csv.gz")
        if not os.path.exists(path):
            print(f"{name}: MISSING - run fetch_hai.sh first")
            failures.append(f"{name} missing")
            continue
        n, ncols, c, orm = scan(path)
        e = exp[name]
        pct = 100.0 * c["attack"] / n if n else 0.0
        print(f"{name}: rows {n} cols {ncols}")
        print(f"   attack {c['attack']} ({pct:.3f}%)  P1 {c['attack_P1']}"
              f"  P2 {c['attack_P2']}  P3 {c['attack_P3']}")
        print(f"   rows where attack != OR(P1,P2,P3): {orm}")

        if ncols != frozen.N_COLUMNS:
            failures.append(f"{name} columns {ncols} != {frozen.N_COLUMNS}")
        if n != e["rows"]:
            failures.append(f"{name} rows {n} != {e['rows']}")
        if c["attack"] != e["attack"]:
            failures.append(f"{name} attack {c['attack']} != {e['attack']}")
        for k, lbl in zip(("P1", "P2", "P3"), LABELS[1:]):
            if c[lbl] != e[k]:
                failures.append(f"{name} {lbl} {c[lbl]} != {e[k]}")
        if orm != 0:
            failures.append(f"{name} OR identity broken in {orm} rows")
        if name in CLEAN_FILES and c["attack"] != 0:
            failures.append(f"{name} is used for fitting but is NOT clean")
        if name in CONTAMINATED_FILES and c["attack"] == 0:
            failures.append(f"{name} was recorded contaminated but measured clean")
        print()

    print(f"G3 schema: {frozen.N_COLUMNS} columns, {frozen.DELIMITER!r} delimited,"
          f" label columns last four")
    print(f"G4 cleanliness: fit file {frozen.FIT_FILE} must be attack-free;"
          f" {frozen.EXCLUDED_FILE} is excluded as contaminated")
    print()
    if failures:
        print(f"FAIL - {len(failures)} discrepancy(ies):")
        for f_ in failures:
            print(f"   {f_}")
        print()
        print("A discrepancy is a FINDING. Report it; do not edit EXPECTED.")
        return 1
    print("PASS - all four files match their registered expectations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
