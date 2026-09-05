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

import argparse
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

# This tool writes its output into the tree it inspects, so its own output
# path is excluded from the cleanliness check. Without the exclusion the tool
# creates the dirty state that causes its own refusal - found on first use.
# The exclusion is RECORDED in the manifest, so a reader who later sees
# working_tree_clean true alongside an uncommitted file knows why.
# Nothing else is exempt. Any other uncommitted change still refuses.
SELF_OUTPUT = "run_manifest.json"


def _git(*a):
    r = subprocess.run(["git"] + list(a), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _resolve(rev):
    """Full SHA of rev, or None if git cannot resolve it. An argument that
    cannot be verified is a typed assertion, which is what this tool exists
    to eliminate."""
    r = subprocess.run(["git", "rev-parse", "--verify", f"{rev}^{{commit}}"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _sha_at(rev, path):
    """sha256 of a file AS COMMITTED at rev, not as it sits on disk."""
    r = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


def _sha(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(experiment_rev=None):
    """experiment_rev: the commit at which the experiment RAN.

    "This manifest was generated from this repository state" and "this
    experiment was executed at this repository state" are different claims.
    Recorded separately, never collapsed. HEAD is never substituted for a
    supplied experiment commit."""
    head_full = _resolve("HEAD")
    exp_full = _resolve(experiment_rev) if experiment_rev else None
    raw = (_git("status", "--porcelain") or "").splitlines()
    excluded = [l for l in raw if l.split(maxsplit=1)[-1:] == [SELF_OUTPUT]]
    dirty = [l for l in raw if l not in excluded]
    return {
        "generated_by": "run_manifest.py",
        "provenance": {
            "experiment_commit": exp_full,
            "experiment_commit_supplied": experiment_rev,
            "manifest_generation_commit": head_full,
            "experiment_is_ancestor_of_manifest":
                (subprocess.run(["git", "merge-base", "--is-ancestor",
                                 exp_full, head_full]).returncode == 0)
                if exp_full else None,
            "experiment_equals_manifest_commit":
                (exp_full == head_full) if exp_full else None,
            "infrastructure_baseline": _resolve("infrastructure-baseline"),
            "freeze_digest": frozen.FREEZE_DIGEST,
            "experiment_artefact": "p0a_result.json",
            "experiment_artefact_sha256_at_experiment_commit":
                _sha_at(exp_full, "p0a_result.json") if exp_full else None,
            "note": "manifest generation and experiment execution are "
                    "different events, recorded separately and never merged",
        },
        "repository": {
            "head": _git("rev-parse", "HEAD"),
            "head_short": _git("rev-parse", "--short", "HEAD"),
            "describe": _git("describe", "--tags", "--always"),
            "prereg_commit": PREREG_COMMIT,
            "prereg_is_ancestor": subprocess.run(
                ["git", "merge-base", "--is-ancestor", PREREG_COMMIT, "HEAD"]
            ).returncode == 0,
            "working_tree_clean": dirty == [],
            "uncommitted": dirty,
            "manifest_output": SELF_OUTPUT,
            "manifest_output_excluded": excluded != [],
            "excluded_entries": excluded,
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-commit", default=None,
                    help="commit at which the experiment RAN; must resolve")
    a = ap.parse_args()
    if a.experiment_commit and _resolve(a.experiment_commit) is None:
        print(f"MANIFEST REFUSED:\n  --experiment-commit "
              f"{a.experiment_commit!r} does not resolve in this repository",
              file=sys.stderr)
        return 1
    m = manifest(a.experiment_commit)
    print(json.dumps(m, indent=2, sort_keys=True, default=list))
    r = m["repository"]
    f = m["freeze"]
    pv = m["provenance"]
    problems = []
    if pv["experiment_commit"]:
        if pv["experiment_is_ancestor_of_manifest"] is False:
            problems.append(
                f"experiment commit {pv['experiment_commit'][:8]} is NOT an "
                f"ancestor of the manifest commit - the chronology is not "
                f"what this manifest would otherwise imply")
        if pv["experiment_artefact_sha256_at_experiment_commit"] is None:
            problems.append(
                f"p0a_result.json absent at {pv['experiment_commit'][:8]}")
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
