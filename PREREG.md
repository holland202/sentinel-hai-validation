# PREREG — sentinel-hai-validation

**Registered 2026-09-03, before any data was fetched and before any detector code
was written in this repository.**

This file is the first commit. Its position in `git log` is the evidence that
these predictions were registered before the run, not fitted to it. If a later
commit changes a prediction, the change is recorded as an amendment below —
predictions are never edited in place and never deleted.

Motto: *Vincit Omnia Veritas.*

---

## Status

**NOT RUN.** No data has been downloaded. No detector has been executed. No
number in this repository is a result. Every prediction below is unresolved.

---

## 0. Scope and honest limits

- Benchmark: **HAI (HIL-based Augmented ICS)**, `github.com/icsdataset/hai`,
  CC BY 4.0, from the Affiliated Institute of ETRI. The testbed emulates
  steam-turbine power generation and pumped-storage hydropower via a
  hardware-in-the-loop simulator.
- **Version pinned to HAI 22.04.** One version only. Files are pinned by
  sha256 in `fetch_hai.sh` at fetch time; the hashes are recorded in that
  script, not here, because they are measurements and this file predates the
  measurement.
- HAI is **not the power grid**. It is one testbed with a simulated grid model
  in its P4 controller. Nothing here generalises to transmission, distribution,
  or any operating utility, and no such claim will be made.
- Detectors under test are transferred, not new:
  - **SENTINEL** — Jensen–Shannon divergence over a sliding window, from
    `holland202/sentinel-batadal-validation`.
  - **VERA** — ridge linear dynamics `x_{t+1} = A x_t + b` with split conformal
    prediction, from `vera_batadal.py` in that same repository.
- Device of record: Samsung Galaxy S25 Ultra, Termux, aarch64, Python 3.14.
  A number enters this repository only after it reproduces on that device.
  Container runs are staging, not results.
- Every number appearing in prose must be pasted verbatim from script output.
  Paraphrased numbers are a defect.

## What is not claimed

- No novelty for the eTaPR implementation. eTaPR is prior work by the HAI
  authors. This repository reimplements it independently to check its own
  scoring, and confirms against the published implementation. Agreement is the
  goal; disagreement is a finding about one of the two implementations, not a
  new metric.
- No state-of-the-art claim. See P2, which registers a loss.
- No trained model. Nothing in this repository is trained.

---

## 1. Registered predictions

### P0 — anti-vacuity. The instrument must be able to return null.

If P0 fails, **P1–P3 are VOID** and are not reported as results in either
direction. A failed P0 is a finding about the harness and is kept.

**P0a — normal-vs-normal null.**
Run both detectors on a held-out slice of HAI 22.04 *training* data, which
contains no attacks. At a conformal level `q`, the breach rate on that clean
slice is predicted to fall in `[0.5·(1−q), 2·(1−q)]`. A detector that raises
alarms on data containing no attacks cannot be read as detecting attacks
anywhere else.

**P0b — provably-undetectable FDIA control, two-sided.**
Build a DC state-estimation model on the IEEE 14-bus case in pure NumPy, with
classical residual-based bad-data detection (BDD). Construct N = 200 false data
injections of the structured form `a = Hc`, which are invisible to
residual-based BDD by construction, and N = 200 unstructured injections of
matched L2 magnitude.

- Predicted: BDD detects **0 of 200** structured injections.
- Predicted: BDD detects **≥ 190 of 200** unstructured injections at the same
  threshold.

Both halves must hold. The first alone would be satisfied by a detector that
never fires; the second is what proves the harness is alive. A nonzero
structured-detection count means the implementation is wrong, not the theory —
the invisibility of `a = Hc` is a linear-algebra fact about the null space of
the residual operator, not an empirical question.

### P1 — metric disagreement replicates in a second domain

`sentinel-batadal-validation` argues that point-wise F1 is the wrong metric for
BATADAL, and shows F1 and the official S score selecting different best
profiles.

**Predicted:** on HAI 22.04, sweeping window length and threshold, the
configuration ranked best by point-wise F1 is **not** the configuration ranked
best by eTaPR.

Refuted if the same configuration tops both rankings. A refutation is
informative: it would mean the BATADAL metric disagreement was a property of
that dataset rather than of point-wise scoring on ICS time series.

### P2 — SENTINEL loses to the published floor

**Predicted:** untuned SENTINEL JSD scores **below** the best published eTaPR
result from the HAI anomaly-detection contest.

This is registered as a loss on purpose. HAI is a well-worked benchmark and an
untuned transferred detector is not expected to win. If it wins, that is the
surprise and it gets scrutinised harder than a loss would be, starting with a
leakage audit of the split.

### P3 — the BATADAL coverage failure reproduces

On BATADAL, VERA's split-conformal coverage on clean test data came out at
0.697 against a nominal 0.90 — a registered failure, kept, attributed to real
drift between the clean training year and the test period.

**Predicted:** clean-slice conformal coverage on HAI 22.04 also falls below
nominal by more than 0.05.

Refuted if coverage holds within 0.05 of nominal. Either outcome is worth
having: reproduction indicates the drift failure is a property of the method on
ICS data generally, refutation localises it to BATADAL.

### P4 — left unrun. The door.

Do SENTINEL or VERA flag the structured `a = Hc` injections from P0b — the
attacks that residual-based bad-data detection provably cannot see?

Neither detector uses the residual, so there is no theorem forbidding it. This
is not run in v1 and no expectation is registered. It is stated here so that
whoever runs it first, including a stranger, knows it was the intended next
step and was not quietly skipped after an unfavourable result.

---

## 2. Abandonment conditions

Stated in advance so that quitting is a decision and not a drift:

- P0a or P0b fails and cannot be repaired without changing what the detector
  measures → the transfer is reported as failed and the repository stands as a
  negative result.
- HAI 22.04 turns out to have no clean held-out slice large enough to estimate
  P0a → the pin moves to another HAI version, recorded as an amendment with the
  reason, before any scoring run.
- The independent eTaPR implementation disagrees with the published one and the
  disagreement cannot be resolved → scoring halts, and the disagreement is the
  finding.

## 3. Amendments

Amendments are appended here with a date and a reason, and the original
text above is left untouched.

---

## Contributors

Chad Edward Holland — architecture, method, device verification.
Claude (Anthropic) — benchmark selection, prediction drafting, review.

AI contributions are credited by model name and are not stripped.

### Amendment 1 — 2026-09-03, before any data was scored

**The version pin moves from HAI 22.04 to HAI 20.07.**

Reason, measured not assumed: every CSV under `hai-22.04/` in
`github.com/icsdataset/hai` is a Git LFS pointer file of 133-134 bytes, not
data. `hai-22.04/train1.csv` contains only an LFS spec line, an oid, and
`size 53190281`. The same holds for `hai-23.05/` and `haiend-23.05/`. Only
`hai-20.07/` and `hai-21.03/` carry real blobs in git, as `.csv.gz`, and those
fetch with plain curl.

`hai-20.07/train1.csv.gz` was fetched and read: 35,252,451 bytes gzipped,
130,293,220 bytes uncompressed, gzip metadata naming the original `train1.csv`
dated 2020-07-20.

HAI 20.07 is selected over HAI 21.03 on size: four files at roughly 110 MB
gzipped against eight files at roughly 186 MB, on a phone.

This is the abandonment condition already registered in section 2 — "the pin
moves to another HAI version, recorded as an amendment with the reason, before
any scoring run." It fired as intended. No detector has run and no score exists
at the time of this amendment.

**Schema observed in the container, not yet device-verified:** 63 columns,
**semicolon-delimited**, not comma. Label columns are `attack`, `attack_P1`,
`attack_P2`, `attack_P3` — a global flag plus per-process flags. Training files
carry the label columns, which is what P0a requires. Sampling is one second,
beginning 2019-09-11 20:00:00.

**Open item raised by this amendment, not resolved by it.** P2 refers to "the
best published eTaPR result from the HAI anomaly-detection contest" without
naming the contest edition or the HAI version it scored against. If that
contest ran on 21.03 or 22.04, a 20.07 result has no floor to compare with and
P2 is unresolvable as written. P2 is therefore **suspended** until a specific,
citable result on HAI 20.07 is identified. If none exists, P2 will be amended
again — restated against a named published baseline or withdrawn — and the
withdrawal will be recorded here rather than deleted above.

### Amendment 2 — 2026-09-03, before any data was fetched

**P0b is restated. The original text above is unchanged and still stands as
written; this amendment narrows an overreaching claim inside it.**

The original P0b says: "A nonzero structured-detection count means the
implementation is wrong, not the theory." That is too strong, and the error is
Claude's, raised by an external AI review before any run.

The invariance is a theorem, but a conditional one. For the linear DC model
with weighted least squares, an injection `a = Hc` on the measurement vector
induces a state displacement `c`, and

    r' = (z + Hc) - H(x-hat + c) = z - H x-hat = r

**only under all of the following:**

- **A1** The `H` used to construct `a` is bit-identical to the `H` used by the
  estimator. A topology or ordering mismatch breaks invariance.
- **A2** The estimator is linear WLS with no bad-data rejection or measurement
  removal loop active during the test. An iterative largest-normalised-residual
  loop is not invariant.
- **A3** No clipping, saturation, or range limiting is applied to `z` or to the
  state.
- **A4** Exact arithmetic. In floating point `r' = r + O(eps * ||z||)`, not
  exactly `r`.
- **A5** The detection threshold is not being evaluated at a knife edge, where
  an `O(eps)` perturbation could flip the verdict.

**Revised P0b, registered:**

Construct N = 200 structured injections `a = Hc` and N = 200 unstructured
injections of matched L2 magnitude on the IEEE 14-bus DC model.

- Predicted: residual BDD detects **0 of 200** structured injections.
- Predicted: residual BDD detects **>= 190 of 200** unstructured injections at
  the same threshold.
- Predicted: `max |r' - r|` over the 200 structured cases is at or below a
  tolerance stated in the script and derived from machine epsilon and `||z||`,
  not assumed to be zero.
- The script asserts A1, A2, A3 and reports the A5 threshold margin. Each
  assertion prints its own value.

**Interpretation rule, replacing the sentence quoted above:** if the structured
count is nonzero, the run identifies which of A1-A5 failed. Only when all five
hold and `max |r' - r|` is within tolerance is an implementation error the
conclusion. If an assumption failed, the failed assumption is the finding and is
kept.

This also corrects the caption under `figures/fdia_nullspace.png` in README.md,
which carried the same overreaching sentence.

Credit: the defect was identified by an external AI review of the public
repository at commit 6befd98, before any data was fetched.
