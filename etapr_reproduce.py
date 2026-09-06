#!/usr/bin/env python3
"""Minimal reproducer: eTaPR raises AttributeError on an empty prediction.

    pip install numpy
    git clone https://github.com/saurf4ng/eTaPR.git
    python3 reproduce.py
"""
import sys, traceback
sys.path.insert(0, "eTaPR")          # adjust to your checkout
from eTaPR_pkg import etapr

N = 100
anomalies  = [0]*20 + [1]*20 + [0]*60   # one attack episode
predictions_empty = [0]*N               # detector predicts nothing
predictions_some  = [0]*25 + [1]*10 + [0]*65

print("eTaPR empty-prediction reproducer")
print(f"n={N}, anomaly ticks={sum(anomalies)}, "
      f"prediction ticks (case A)={sum(predictions_some)}, "
      f"(case B)={sum(predictions_empty)}")
print()

for label, pred in [("A non-empty prediction", predictions_some),
                    ("B EMPTY prediction", predictions_empty)]:
    print(f"--- {label} ---")
    try:
        r = etapr.evaluate_w_streams(anomalies, pred,
                                     theta_p=0.5, theta_r=0.1, delta=0.0)
        print(f"    eTaP {r['eTaP']:.6f}  eTaR {r['eTaR']:.6f}  f1 {r['f1']:.6f}")
    except Exception:
        tb = traceback.format_exc().strip().splitlines()
        print("    RAISED:")
        for line in tb[-5:]:
            print("      " + line)
    print()
