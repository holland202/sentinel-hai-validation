# eTaPR: degenerate inputs crash, and the published defaults disagree

Two independent findings in `github.com/saurf4ng/eTaPR`, commit
`af9e7aed35cfd160cbe0d04c8ec4c102502cb677` (2023-05-16), the implementation
the HAI dataset authors recommend for evaluating ICS anomaly detectors.

Reported by Chad Edward Holland. Reproducers below are complete and standalone;
they need only `numpy` and a clone of the package.

---

## Finding 1 — three degenerate inputs raise, at three different lines

`evaluate_w_streams` raises rather than returning a score for three input
combinations that arise in ordinary use.

| Input | Exception | Location |
|---|---|---|
| Anomalies present, **prediction empty** | `AttributeError: 'float' object has no attribute 'mean'` | `etapr.py:113` in `eTaR_p` |
| Predictions present, **no anomalies** | `ZeroDivisionError: division by zero` | `etapr.py:101` in `eTaR_d` |
| **Both empty** | `ZeroDivisionError: division by zero` | `etapr.py:101` in `eTaR_d` |

An all-ones prediction returns `f1 = 0.000000` without error, so the failure is
specific to empty sets rather than to pathological input generally.

### Why this matters in practice

The empty-prediction case is not exotic. Any threshold sweep that includes a
high quantile will produce configurations where the detector predicts nothing.
In our own use, scoring a 3x3 grid at threshold quantiles up to 0.99, this is
an expected cell of the sweep, not an edge case. The sweep terminates with a
traceback instead of recording a score, and whatever the experimenter decides
to do next is a post-hoc choice made while the run is broken.

The no-anomaly case arises whenever a segment of a stream is scored
independently and happens to contain no labelled attack.

### Root cause

`etapr.py` has three sibling guards for the same degenerate condition, and they
do not agree on a return type.

```
line  90   _etar_d:  return np.zeros(self.get_n_anomalies()), []     # array
line 105   _etar_p:  return 0.0                                      # scalar
line 145   _etap_p:  return 0.0                                      # scalar
```

The callers assume the array form:

```
line 111-113   def eTaR_p(self) -> float:
                   scores = self._etar_p()
                   return scores.mean()          # float has no .mean()
```

`_etar_d` returns an ndarray on its guard; `_etar_p` and `_etap_p` return a
scalar `0.0` on the identical condition. `eTaR_p` and `eTaP_p` then call
`.mean()` on the result.

The two `ZeroDivisionError` cases are separate arithmetic, not the same bug:

```
line 101   eTaR_d:  return len(detected_id_list)/self.get_n_anomalies(), ...
line 138   eTaP_d:  tapd /= float(self._predictions_total_weight)
```

### Reproducer

```python
import sys
sys.path.insert(0, "eTaPR")          # path to your clone
from eTaPR_pkg import etapr

anomalies = [0]*20 + [1]*20 + [0]*60

# works
print(etapr.evaluate_w_streams(anomalies, [0]*25 + [1]*10 + [0]*65,
                               theta_p=0.5, theta_r=0.1, delta=0.0)["f1"])
# -> 0.8571428571428571

# raises AttributeError
etapr.evaluate_w_streams(anomalies, [0]*100,
                         theta_p=0.5, theta_r=0.1, delta=0.0)

# raises ZeroDivisionError
etapr.evaluate_w_streams([0]*100, [0]*40 + [1]*10 + [0]*50,
                         theta_p=0.5, theta_r=0.1, delta=0.0)
```

### Expected behaviour

A defined score, or an explicit exception documented as intended. Which of
those is correct is the maintainers' call: it is arguable that eTaR is
genuinely undefined with zero anomalies, and that raising is the right
response — but then it should raise deliberately with a clear message rather
than through an internal division.

For the empty-prediction case we take the view that a score is well defined
and should be returned, since a detector that predicts nothing has a
determinable time-aware precision and recall.

### No patch is proposed, and here is why

We attempted one and it did not hold. Making the two scalar guards return
arrays moves the failure to `eTaP_d:138` (`ZeroDivisionError` on a zero total
prediction weight). Guarding that as well moves it again, and a further round
produced `eTaR = nan` for the no-anomaly case rather than an error. The guards
interact, and at least four call sites are involved.

We are reporting what we can evidence — three reproducible failures, each
located — rather than publishing a patch we have not got working. Someone who
knows the intended semantics of eTaR under zero anomalies will fix this in
less time than we would spend guessing at it.

### Suggested regression tests

```
empty prediction, anomalies present   -> defined score or documented raise
predictions present, zero anomalies   -> defined score or documented raise
both empty                            -> defined score or documented raise
all-ones prediction                   -> 0.0        (currently passes)
normal case                           -> unchanged  (currently passes)
```

---

## Finding 2 — three conflicting sets of published defaults

"eTaPR at published defaults" is not a well-defined instruction. The package
supplies three different answers.

| Source | `theta_p` | `theta_r` | `delta` |
|---|---|---|---|
| README, CLI documentation | 0.5 | 0.1 | 0.0 |
| README, worked example | 0.5 | **0.01** | — |
| `evaluate_w_streams` signature | **0.7** | 0.1 | 0.0 |
| `evaluate_w_ranges` signature | *required, no default* | *required* | — |

The documented default for `theta_p` is 0.5. The signature of
`evaluate_w_streams` declares 0.7. For per-tick stream data,
`evaluate_w_streams` is the natural entry point — so the function most users
will call is the one whose default contradicts the documentation.

### Why this matters

`theta_p` is not a minor knob. It is the threshold below which a prediction
block is **deleted entirely** by the iterative pruning in `_pruning()`, not
merely down-weighted. At 0.5, an alarm overlapping a real attack by less than
half is discarded and takes its recall contribution with it. At 0.7 the cut is
considerably more severe.

Any published result stating only "eTaPR with default parameters" is therefore
ambiguous between at least two materially different scoring regimes, and the
difference is not small.

### Suggested resolution

Make the signature defaults match the documented ones, or remove the signature
defaults so the parameters must be passed explicitly. Either removes the
ambiguity. We pass ours explicitly on every call for this reason.

---

## Environment

```
eTaPR    af9e7aed35cfd160cbe0d04c8ec4c102502cb677
python   3.12.3
numpy    2.4.4
platform Linux x86_64
```

Both findings also reproduce on aarch64 under Python 3.14.6.

## Context

Found while building a preregistered evaluation of an anomaly detector on the
HAI 20.07 benchmark, where eTaPR is the metric the dataset authors recommend.
The findings are independent of that detector and of its results.
