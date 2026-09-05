#!/usr/bin/env python3
"""
run_manifest.py - the provenance record for a measurement, GENERATED.

Nothing here is typed by hand. Every field is read from the environment, the
repository, or the files on disk at the moment a run happens. A manifest a
human wrote is a claim; this one is an observation.

Emitted as JSON so a result can be bound to exactly the conditions that
produced it: dataset hashes, freeze digest, prereg commit, git HEAD and
cleanliness, interpreter and NumPy versions, machine architecture, seed.

Usage:
    python3 run_manifest.py                 # print the manifest
    python3 run_manifest.py > manifest.json # or capture it

Import `manifest()` to embed the same record inside a result file.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys

import numpy as np

import frozen

DATA = "data"
DATA_FILES = ["train1.csv.gz", "train2.csv.gz", "test1.csv.gz", "test2.csv.gz",
              "hai_dataset_technical_details.pdf"]
CODE_FILES = ["frozen.py", "ap_grouped.py", "etapr_independent.py",
              "verify_hai.py", "fetch_hai.sh", "sentinel.py"]
PREREG_COMMIT = "e48cdacfcc62eec3ad2681f8308015918be95092"


def _git(*a):
    r = subprocess.run(["git"] + list(a), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _sha(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest():
    dirty = _git("status", "--porcelain")
    return {
        "generated_by": "run_manifest.py",
        "repository": {
            "head": _git("rev-parse", "HEAD"),
            "head_short": _git("rev-parse", "--short", "HEAD"),
            "describe": _git("describe", "--tags", "--always"),
            "prereg_commit": PREREG_COMMIT,
            "prereg_is_ancestor": subprocess.run(
                ["git", "merge-base", "--is-ancestor", PREREG_COMMIT, "HEAD"]
            ).returncode == 0,
            "working_tree_clean": dirty == "",
            "uncommitted": [l for l in (dirty or "").splitlines()],
        },
        "freeze": {
            "digest_sealed": frozen.FREEZE_DIGEST,
            "digest_computed": frozen.digest(),
            "sealed_matches_computed":
                frozen.FREEZE_DIGEST == frozen.digest(),
            "n_constants": len(frozen.FROZEN),
            "pending": list(frozen.PENDING),
        },
        "dataset": {
            "name": frozen.DATASET,
            "upstream_commit": frozen.UPSTREAM_COMMIT,
            "sha256": {f: _sha(os.path.join(DATA, f)) for f in DATA_FILES},
        },
        "code_sha256": {f: _sha(f) for f in CODE_FILES},
        "environment": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "configuration": dict(sorted(frozen.FROZEN.items(), key=lambda kv: kv[0])),
    }


def main():
    m = manifest()
    print(json.dumps(m, indent=2, sort_keys=True, default=list))
    r = m["repository"]
    f = m["freeze"]
    problems = []
    if not r["prereg_is_ancestor"]:
        problems.append("prereg commit is not an ancestor of HEAD")
    if not f["sealed_matches_computed"]:
        problems.append("freeze digest does not match the sealed value")
    if f["pending"]:
        problems.append(f"freeze incomplete: {f['pending']}")
    if not r["working_tree_clean"]:
        problems.append("working tree is dirty - the result cannot be bound "
                        "to a commit")
    if problems:
        print("\nMANIFEST REFUSED:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
