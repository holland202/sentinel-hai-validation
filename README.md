# sentinel-hai-validation

**A preregistered evaluation of anomaly detection on the HAI industrial
control system benchmark.**

**Two detectors, two outcomes. No detector has scored `test1`.**

SENTINEL's P0a **FAILED** — it did not satisfy the registered precondition
required to interpret any attack-detection measurement, so P1 and P3 are VOID.
VERA's P7a **PASSED** on the same held-out slice under amendment 5, which is
the first anti-vacuity gate this repository has cleared.

**No attack-detection result is claimed by either.** A passing gate licenses
scoring `test1`; no detector has scored it. Its label columns have been read
once, by `verify_hai.py`, to cross-check the dataset authors' published
episode counts.

The useful result here is not a better score. It is knowing when a score is
not justified.

---

## Defects found in the benchmark's recommended metric

While validating the scoring path, three reproducible failures were found in
[eTaPR](https://github.com/saurf4ng/eTaPR), the metric the HAI dataset authors
recommend:

| Input | Exception | Location |
|---|---|---|
| Detector predicts nothing | `AttributeError: 'float' object has no attribute 'mean'` | `etapr.py:113` |
| Segment contains no attack | `ZeroDivisionError` | `etapr.py:101` |
| Both empty | `ZeroDivisionError` | `etapr.py:101` |

Separately, **"eTaPR at published defaults" has three different answers.** The
README documents `theta_p = 0.5`; the worked example uses a different
`theta_r`; the signature of `evaluate_w_streams` declares `0.7`. That
threshold decides whether a prediction block is *deleted entirely* by the
pruning loop rather than down-weighted, so the settings are not close.

**No patch is proposed, and the report says why** — two attempts each moved
the failure somewhere new.

→ **[Read the report](ETAPR_DEFECT_REPORT.md)** ·
**[Run the reproducer](etapr_reproduce.py)** (needs only numpy and a clone of
the package)

---

## The results

### SENTINEL — P0a FAILED

`sentinel.py`, JSD over a sliding window, every constant imported from a
sealed freeze. Fit on `train1[:60%]`, calibrate on the next 20%, measure P0a
on the final 20% — held out from the quantile, not merely from the fit.

```
P0a breach rate   0.042402   on 61,861 clean held-out ticks
registered interval          [0.05, 0.2]  at alpha = 0.10
                             FAIL
```

P0a is the anti-vacuity gate: a detector that alarms on data containing no
attacks cannot be read as detecting attacks anywhere else. `sentinel.py` will
not open `test1` until P0a passes, so the evaluation set was not touched
before the gate that licenses touching it.

**Then the explanation turned out to be wrong.** The commit recording the
failure claimed held-out scores were systematically *lower*. Measurement
refuted that — the held-out mean is **higher** (25.2869 vs 25.1206) while the
standard deviation **falls** (1.9876 vs 2.6027). A tail threshold on a
narrower distribution catches fewer points even as the centre rises. It is a
variance change, not the drift story. The original claim stays in the history.

→ [`p0a_result.json`](p0a_result.json) ·
[`p0a_score_characterization.json`](p0a_score_characterization.json) ·
[`p0a_characterization.py`](p0a_characterization.py)

### VERA — P7a PASSED, P7b and P7c refuted

Ridge dynamics plus split conformal, transferred unchanged from the BATADAL
predecessor and registered in amendment 5 *before* the code existed. Same
file, same frozen split, same alpha.

```
P7a  held-out breach 0.115845   in [0.05, 0.2]        PASS
P7b  SD ratio       0.9351      predicted < 0.90      REFUTED
P7c  coverage       0.8842      predicted > 0.90      REFUTED
```

**P7b is the informative one.** SENTINEL and VERA share no mathematics but
read the same file across the same split boundary. If the variance collapse
that failed P0a were a property of the data, both should show it. VERA
narrows in the same direction but far more weakly — 0.9351 against SENTINEL's
0.764 — so the collapse is largely an artefact of the windowed JSD score
itself, not of `train1`.

P7c was registered as **not blind**: it was informed by SENTINEL's already
published 0.042402 on the same slice, that dependence was stated in the
amendment rather than hidden, and it was refuted anyway.

A defect of ours travelled with this. Amendment 5 registered P8 as measured
on `train1`, which has zero attack rows — so it could not have been refuted
by any measurement. The run meant to test it printed the problem instead of
reinterpreting it. P8 is void; amendment 6 replaces it with P10, correctly
scoped to `EVAL_FILE`.

→ [`vera_p0a.py`](vera_p0a.py) · amendments 5 and 6 in
[`PREREG.md`](PREREG.md)

## What passed

**P0b PASSES.** A residual-invariance control on IEEE 14-bus DC state
estimation: 200 structured injections `a = Hc` produce zero change in the
detection indicator, and 200 matched unstructured injections are detected
200/200. Both bounds are required — a detector that never fires passes the
first and is caught only by the second.

The construction is prior work (Liu, Ning & Reiter, CCS '09). What is
registered here is the two-sided predicate around it.

## Reproduce

```bash
git clone https://github.com/holland202/sentinel-hai-validation
cd sentinel-hai-validation
python3 gate_provenance.py       # 11 provenance checks, no data needed
python3 frozen.py                # freeze digest, exits 1 if a constant moved
python3 fdia_control_v2.py       # P0b
python3 etapr_independent.py     # metric agreement against a pre-committed fixture
bash fetch_hai.sh                # ~113 MB, five sha256-pinned files
python3 verify_hai.py            # schema, cleanliness, published-episode check
python3 sentinel.py --p0a        # the result. exits 1.
```

A cold clone is the reproducibility boundary. CI runs the no-data steps on
every push.

## Method

Predictions registered before any data was fetched —
[`PREREG.md`](PREREG.md) is the first commit, and it contains four files with
no data and no scripts. Amendments are append-only; `gate_provenance.py`
fails the build if a single character of the original registration is edited.
Every constant lives in [`frozen.py`](frozen.py), sealed at digest
`6005fb60`, which recomputes its own hash and refuses to run if a value
changed.

Refutations are kept. The failing first implementation of P0b is still
published beside its correction. So is the withdrawn average-precision
implementation, retained specifically so its own test can prove it fails.

Defects found and kept during this work, several of them in our own code: a
P0a gate that could not fail; a proposed discrimination test that false-passed
30–47% against a null detector and was withdrawn before registration; an
order-dependent AP implementation; a training file that is not attack-free; a
provenance tool that dirtied the tree it was checking.

## Registered but not run

- **P2** — suspended. No citable eTaPR baseline on HAI 20.07 has been
  identified.
- **P4** — do the detectors flag injections that residual detection provably
  cannot see?
- **P6** — TIME_NULL, a detector whose only inputs are temporal, through
  identical P5 machinery. If it passes, passing P5 establishes nothing alone.
- **P10** — the coverage/detection exchange rate, replacing the void P8.
  Gated behind P7a, which passed. Measured on `EVAL_FILE`, which is not yet
  opened.
- **P11** — VERA's coverage shortfall is 0.0158. Real drift at small scale, or
  sampling noise at n = 61,919? Needs a null not yet specified.

## Prior work and scope

- HAI dataset: [icsdataset/hai](https://github.com/icsdataset/hai), CC BY 4.0,
  Affiliated Institute of ETRI. Not redistributed; `fetch_hai.sh` pulls it at
  a pinned commit.
- eTaPR is prior work by the HAI authors. No novelty is claimed for the
  independent reimplementation, which exists to check our own scoring.
- BATADAL predecessor:
  [sentinel-batadal-validation](https://github.com/holland202/sentinel-batadal-validation)

HAI is one testbed containing a simulated grid model. **It is not the power
grid**, and nothing here generalises to an operating utility. The P0b control
covers static state estimation only; the same injection may well be visible to
a tracking or Kalman-type estimator, which is untested.

## Figures

Both describe the registered method, not results.

![Prereg gate structure](figures/prereg_gates.png)

P0a and P0b gate everything downstream. P2 is suspended under amendment 1. P4
is registered and deliberately left unrun.

![FDIA null space](figures/fdia_nullspace.png)

Residual-based detection measures distance to the column space of H, so an
injection `a = Hc` moves the measurement along that space and leaves the
residual identical. Structured injections are invisible under the registered
assumptions; unstructured ones are not. If the structured count is nonzero,
the run identifies which of A1–A3 failed. See amendment 2.

SVG sources sit beside each PNG.

*Vincit Omnia Veritas.*
