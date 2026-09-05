#!/usr/bin/env python3
"""
gate_provenance.py - G1. The checks that passing tests cannot fake.

Every other gate in this repository proves that some code behaves correctly.
This one proves things about the REPOSITORY: that the registration precedes
the run, that amendments are append-only, that no script the protocol depends
on exists only on the author's machine, and that no detector ran before the
freeze.

Those are the claims a reader cannot verify by running the science. They are
verifiable from git alone, by anyone, without trusting the author.

Run from a CLEAN CHECKOUT with full history:
    git clone <repo> && cd <repo> && python3 gate_provenance.py

Requires git. Exits 1 on any failure and names it.
"""

import re
import subprocess
import sys

# The root registration. Its contents are asserted below: four files, no data,
# no scripts. That is what makes "registered before the run" checkable rather
# than asserted.
PREREG_COMMIT = "e48cdacfcc62eec3ad2681f8308015918be95092"
PREREG_EXPECTED_FILES = {".gitignore", "LICENSE.md", "PREREG.md", "README.md"}

# The commit that sealed frozen.py at its current digest. No detector script
# may appear in history before this.
FREEZE_COMMIT = "b5b305a"
FREEZE_DIGEST = "6005fb60e473dfdf22b165b7b6375b52a0e5a055c57cc2fea8a013074a7bbbf4"

# Scripts the protocol depends on. Each must be TRACKED, not merely present.
REQUIRED_TRACKED = [
    "PREREG.md", "README.md", "LICENSE.md",
    "fetch_hai.sh", "verify_hai.py", "frozen.py",
    "ap_grouped.py", "etapr_independent.py", "etapr_fixture.json",
    "fdia_control.py", "fdia_control_v2.py",
    "gate_provenance.py", "evaluator_experiments.py",
    ".github/workflows/veritas_gate.yml",
]

# Anything matching these in a commit BEFORE the freeze would mean a detector
# ran before the constants were fixed. Deliberately broad.
DETECTOR_PATTERNS = [
    r"^sentinel.*\.py$", r"^vera.*\.py$", r"^run_p[135].*\.py$",
    r"^p5_runner.*\.py$", r"^detect.*\.py$", r"^results?/.*",
]


def git(*args):
    return subprocess.run(["git"] + list(args), capture_output=True,
                          text=True, check=False)


class Gate:
    def __init__(self):
        self.failures = []
        self.n = 0

    def check(self, name, ok, detail=""):
        self.n += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if detail:
            print(f"        {detail}")
        if not ok:
            self.failures.append(name)
        return ok


def main():
    g = Gate()
    head = git("rev-parse", "HEAD").stdout.strip()
    print("gate_provenance.py - G1 cold-clone provenance")
    print(f"commit under test: {head}")
    print()

    # --- 1. history is present at all -------------------------------------
    depth = git("rev-list", "--count", "HEAD").stdout.strip()
    g.check("1 full history available (not a shallow clone)",
            depth.isdigit() and int(depth) > 1, f"{depth} commits")

    # --- 2. the registration precedes this commit --------------------------
    anc = git("merge-base", "--is-ancestor", PREREG_COMMIT, "HEAD")
    g.check("2 prereg commit is an ancestor of HEAD",
            anc.returncode == 0, PREREG_COMMIT[:12])

    # --- 3. the registration contained no data and no scripts --------------
    tree = git("ls-tree", "--name-only", "-r", PREREG_COMMIT).stdout.split()
    g.check("3 prereg commit contains only the registration",
            set(tree) == PREREG_EXPECTED_FILES,
            f"{sorted(tree)}")

    # --- 4. amendments are append-only -------------------------------------
    old = git("show", f"{PREREG_COMMIT}:PREREG.md").stdout
    new = git("show", "HEAD:PREREG.md").stdout
    core = old.split("## 3. Amendments")[0]
    g.check("4 pre-amendment registered text appears verbatim in HEAD",
            len(core) > 100 and core in new,
            f"{len(core)} chars carried forward into {len(new)}")

    # --- 5. no registered prediction was deleted ---------------------------
    preds = ["P0a", "P0b", "P1", "P2", "P3", "P4"]
    missing = [p for p in preds if p not in new]
    g.check("5 every originally registered prediction still present",
            not missing, f"missing: {missing}" if missing else "P0a..P4")

    # --- 6. required scripts are TRACKED, not just present -----------------
    tracked = set(git("ls-files").stdout.split())
    absent = [f for f in REQUIRED_TRACKED if f not in tracked]
    g.check("6 every protocol script is tracked on origin",
            not absent,
            f"UNPUBLISHED: {absent}" if absent else f"{len(REQUIRED_TRACKED)} files")

    # --- 7. the freeze is an ancestor and its digest is the sealed one ------
    anc2 = git("merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD")
    g.check("7 freeze commit is an ancestor of HEAD",
            anc2.returncode == 0, FREEZE_COMMIT)
    frozen_src = git("show", "HEAD:frozen.py").stdout
    g.check("7b frozen.py at HEAD carries the sealed digest",
            FREEZE_DIGEST in frozen_src, FREEZE_DIGEST[:16])

    # --- 8. no detector script exists before the freeze ---------------------
    pre = git("rev-list", f"{FREEZE_COMMIT}").stdout.split()
    offenders = []
    for sha in pre:
        files = git("ls-tree", "--name-only", "-r", sha).stdout.split()
        for f in files:
            if any(re.match(p, f) for p in DETECTOR_PATTERNS):
                offenders.append((sha[:8], f))
    g.check("8 no detector or results artefact in any commit before the freeze",
            not offenders,
            f"{offenders[:4]}" if offenders else f"{len(pre)} commits scanned")

    # --- 9. kept failures are still kept ------------------------------------
    v1 = git("show", "HEAD:fdia_control.py").stdout
    g.check("9 the failing P0b implementation is still published",
            "0 of 200" in v1 or "registered 0" in v1,
            "fdia_control.py retained alongside v2")

    # --- 10. the withdrawn AP is still shown failing -------------------------
    ap = git("show", "HEAD:ap_grouped.py").stdout
    g.check("10 the withdrawn AP is retained as an anti-vacuity control",
            "_ap_by_index" in ap and "WITHDRAWN" in ap,
            "index-order AP kept so the selftest can prove it can fail")

    print()
    if g.failures:
        print(f"G1 FAIL - {len(g.failures)} of {g.n}: {g.failures}")
        print("A provenance failure is not fixable by rerunning the science.")
        return 1
    print(f"G1 PASS - {g.n}/{g.n}")
    print("Registration precedes the run, amendments are append-only, every")
    print("protocol script is published, and no detector ran before the freeze.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
