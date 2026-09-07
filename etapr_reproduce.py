#!/usr/bin/env python3
"""Reproducer and REGRESSION GATE for the defects in ETAPR_DEFECT_REPORT.md.

    pip install numpy
    git clone https://github.com/saurf4ng/eTaPR.git
    python3 etapr_reproduce.py

Exit codes:
    0  every documented defect reproduced exactly as the report describes
    1  at least one did NOT reproduce -- upstream changed, or the report is
       now wrong. Either way the report needs revisiting.
    2  the instrument could not run (eTaPR not importable). Distinguishes
       "could not look" from "looked and agreed".

WHY THE EXIT CODE EXISTS. The previous version printed a traceback and exited
0 whether or not anything was reproduced. It could not report that a defect
had been FIXED, so ETAPR_DEFECT_REPORT.md could silently become false while
this script kept passing. A reproducer that cannot fail is the same defect
class this repository was built to find.

Run with --sabotage to invert the expectations and prove the gate can fail.

VERIFICATION STATUS, stated rather than implied. The exit-2 path is verified
on aarch64/Termux/Python 3.14 for two distinct causes (eTaPR absent; eTaPR
present but a dependency of its own missing). The five reproductions and the
--sabotage inversion are verified in a container (x86_64, Python 3.12) only.
eTaPR imports pandas and cv2, and OpenCV was not installed on the device, so
cases A-E have NOT been reproduced there. Do not read the five MATCH lines as
device-verified.
"""
import sys, traceback

SABOTAGE = "--sabotage" in sys.argv

try:
    sys.path.insert(0, "eTaPR")
    from eTaPR_pkg import etapr
except ModuleNotFoundError as e:
    missing = e.name or "?"
    print(f"instrument unavailable: missing module {missing!r}", file=sys.stderr)
    if missing.startswith("eTaPR"):
        print("  clone https://github.com/saurf4ng/eTaPR.git beside this script",
              file=sys.stderr)
    else:
        print(f"  eTaPR imports {missing}; it is not installed here.",
              file=sys.stderr)
        print("  Install it however your platform provides it. No package name",
              file=sys.stderr)
        print("  is suggested: module names and package names differ, and a",
              file=sys.stderr)
        print("  guessed one would be a fabricated value.", file=sys.stderr)
    sys.exit(2)
except Exception as e:
    print(f"instrument unavailable: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(2)

N = 100
attack   = [0]*20 + [1]*20 + [0]*60      # one attack episode
no_attack = [0]*N                        # ground truth with no anomaly
pred_some  = [0]*25 + [1]*10 + [0]*65
pred_empty = [0]*N

# Each case: label, truth, prediction, expected exception type or None.
# Expectations are transcribed from ETAPR_DEFECT_REPORT.md, not from a run.
CASES = [
    ("A  non-empty prediction, attack present", attack, pred_some,  None),
    ("B  detector predicts nothing",            attack, pred_empty, AttributeError),
    ("C  segment contains no attack",           no_attack, pred_some, ZeroDivisionError),
    ("D  both empty",                           no_attack, pred_empty, ZeroDivisionError),
]

print("eTaPR defect reproducer / regression gate")
print(f"n={N}" + ("   [SABOTAGE: expectations inverted]" if SABOTAGE else ""))
print()

results = []
for label, truth, pred, expected in CASES:
    if SABOTAGE:                       # flip what we expect, nothing else
        expected = None if expected else AttributeError
    print(f"--- {label} ---")
    got = None
    try:
        r = etapr.evaluate_w_streams(truth, pred,
                                     theta_p=0.5, theta_r=0.1, delta=0.0)
        print(f"    returned  eTaP {r['eTaP']:.6f}  eTaR {r['eTaR']:.6f}"
              f"  f1 {r['f1']:.6f}")
    except Exception as exc:
        got = type(exc)
        tb = traceback.format_exc().strip().splitlines()
        print(f"    RAISED {got.__name__}: {tb[-1].strip()}")
        for line in tb[-4:-1]:
            if "eTaPR_pkg" in line:
                print(f"      {line.strip()}")
    ok = (got is expected) if expected else (got is None)
    exp_name = expected.__name__ if expected else "no exception"
    print(f"    expected {exp_name:<18} -> {'MATCH' if ok else 'MISMATCH'}")
    results.append((label, ok))
    print()

# The three conflicting defaults, checked rather than asserted in prose.
import inspect
sig = inspect.signature(etapr.evaluate_w_streams)
tp, tr = sig.parameters["theta_p"].default, sig.parameters["theta_r"].default
print(f"evaluate_w_streams signature defaults: theta_p={tp}  theta_r={tr}")
print("  ETAPR_DEFECT_REPORT.md finding 2 records theta_p=0.7, theta_r=0.1,")
print("  contradicting the documented theta_p=0.5")
sig_ok = (tp == 0.7 and tr == 0.1)
if SABOTAGE:
    sig_ok = not sig_ok
print(f"  -> {'MATCH' if sig_ok else 'MISMATCH'}")
results.append(("E  signature defaults contradict the docs", sig_ok))

n_ok = sum(1 for _, ok in results if ok)
print(f"\n{n_ok} of {len(results)} documented behaviours reproduced")
for label, ok in results:
    if not ok:
        print(f"  MISMATCH: {label}")
if n_ok != len(results):
    print("\nETAPR_DEFECT_REPORT.md no longer matches upstream. Revisit it.")
    sys.exit(1)
print("\nreport agrees with upstream at this checkout")
sys.exit(0)
