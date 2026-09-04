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

### Amendment 3 — 2026-09-04, before any HAI detector run

**P0b is restructured into three independently falsifiable parts. A4 is
removed, A5 is deleted. The original P0b text above is unchanged and stands.**

**The original P0b-1 was run and FAILED.** It registered "0 of 200 structured
detections" and measured 6 of 200 on the S25 Ultra, exit 1. The failure is kept
in the repository as `fdia_control.py`, which is not replaced.

Diagnosis: all six were trials in which the clean, unattacked measurement
already exceeded the chi-square threshold — baseline false positives, 6
observed against 10 expected at the 0.95 level. The attack contributed zero
detections. The theorem held throughout; `max |r' - r|` was within tolerance in
every trial. The registered prediction silently assumed a detector with no
false-positive rate, and no residual-based bad-data detector has that.

**The assumption that broke the prediction appears nowhere in A1–A5.**
Amendment 2 was written to enumerate the conditions under which P0b's verdict
is meaningful, and it missed the one that bit.

Two further defects were found in the original implementation, both before any
HAI detector ran:

- The numerical tolerance was derived once, before the trial loop, from a
  `z_clean` built from a `theta` draw appearing in none of the 200 trials it
  governed. Measured: per-trial `||z_i||` spans 6.61x, from 3.1791 to 21.0098,
  against that single global scale of 12.2907, so 142 of 200 trials deserved a
  tighter bound than they were given.
- `max |r' - r|` is not reproducible across architectures: `3.722391e-15` on
  x86_64 and `5.027120e-15` on aarch64 from an identical seeded run. A specific
  value can therefore never be a registered prediction.

**Restated:**

- **P0b-1 — numerical invariance, per trial.**
  `||r'_i - r_i||_inf <= C * eps * max(1, ||z_i||_2)` for every structured
  trial `i`, with `C = 1000` frozen before execution and the bound computed and
  printed per trial. The registered object is the **predicate**. No
  architecture-specific residual value is itself a prediction; observed values
  are reported with the machine that produced them. *Falsified by any trial
  exceeding its own bound.*
- **P0b-2 — the detection indicator is unchanged.**
  `1[J'_i > tau] == 1[J_i > tau]` for every trial, compared trial by trial,
  with the clean detection count reported alongside. *Falsified by any trial in
  which the indicators differ.*
- **P0b-3 — matched unstructured control.** At the same `tau` and identical
  `||a||`, at least 190 of 200 unstructured injections are detected.
  *Falsified by fewer than 190.*

**A4 is removed from the assumption list.** Exact arithmetic is a fact about
the machine, not a condition that can hold or fail. It is replaced by the
per-trial printed bound in P0b-1.

**A5 is deleted.** Once P0b-2 compares indicators trial by trial instead of a
count against a threshold, threshold proximity is irrelevant. A5 existed only
because the original P0b-1 was ill-posed.

**Surviving assumptions: A1, A2, A3**, each necessary. A1 and A2 are **not
independent**: an iterative largest-normalised-residual loop changes the
measurement set between iterations, which changes `H`, which changes `S`, so
the `H` used to construct `a = Hc` is no longer the estimator's `H`. Relaxing
A2 breaks A1 as a consequence.

**Scope, registered:** the corrected P0b establishes residual invariance for a
single-pass linear WLS estimator on a fixed measurement set, and nothing wider.
Using the IEEE Task Force taxonomy (DOI 10.1109/TPWRS.2019.2894769), this is
static state estimation — the bottom rung. Tracking, forecasting-aided and
dynamic estimators all carry a state-transition model that predicts the state
independently of the measurement, so `a = Hc` may well be **visible** to them.
Not tested. Registered as an unrun door.

The phrase "provably-undetectable FDIA control" is **retracted** as an
overclaim wherever it appears, including the repository description, and
replaced with "residual-invariance control under the registered linear WLS
model". The `a = Hc` construction is prior work: Liu, Ning and Reiter, CCS '09,
pp. 21–32, DOI 10.1145/1653662.1653666.

The corrected implementation is `fdia_control_v2.py`, device-verified on
aarch64: clean detections 8, structured detections 8, indicator mismatches 0,
unstructured 200 of 200, PASS exit 0. Four sabotages verified to produce exit
1, including a never-fires detector that passes P0b-2 and is caught only by
P0b-3.

---

### Amendment 4 — 2026-09-04, before any HAI detector run

**Corrections of published fact, one proposal withdrawn before registration,
two new registered predictions, and the freeze.**

#### (a) Amendment 1 published a wrong number

Amendment 1 states "63 columns". The measured value is **64**. The error came
from splitting a semicolon-delimited header on a comma. The original text
stands; this is the correction.

#### (b) `train2` is not attack-free

Measured across all four HAI 20.07 files at the pinned commit, and
independently corroborated where the dataset authors publish a figure:

| File | Rows | attack | % | episodes | published episodes |
|---|---|---|---|---|---|
| train1 | 309,600 | 0 | 0.000 | 0 | — |
| train2 | 241,200 | **776** | **0.322** | **2** | not in the summary table |
| test1 | 291,600 | 11,538 | 3.957 | 28 | **28** |
| test2 | 153,000 | 5,989 | 3.914 | 10 | **10** |

The 28 and 10 come from `hai_dataset_technical_details.pdf` (v4.0, May 2023,
CC BY-SA 4.0), which records 38 attack scenarios for HAI 20.07. Total measured
test episodes 38 of 38.

`train2`'s 776 attack rows resolve to **two episodes of 387 and 389 seconds** —
deliberate attacks, not stray labels. The summary table gives attack counts for
test files only, so this figure is **not** corroborated by it and is flagged as
such in `verify_hai.py` output.

**P0a's premise — that training data contains no attacks — is false for
`train2`. Fitting and calibration use `train1` only.** `attack` is exactly
`OR(attack_P1, attack_P2, attack_P3)`, zero mismatches across all 995,400 rows,
so `attack == 0` is sufficient to establish a row is clean.

#### (c) A candidate P0c was proposed and withdrawn before registration

The proposal was an iid label-permutation test of discrimination. Tested
against a null detector with zero detection ability and contiguous labels, it
false-passed **30% of the time at phi = 0.9 and 47% at phi = 0.999**, against a
nominal 1%. HAI attacks are contiguous episodes and sliding-window scores are
autocorrelated by construction, so an iid permutation null is the wrong null.
**Withdrawn, not registered. The record of its failure is kept.**

#### (d) P5 is registered — discrimination, outside P0

> **P5.** At the reference configuration frozen in `frozen.py` — not the
> maximum over the P1 sweep — compute the detector's scores on `test1` and the
> average precision `AP_obs` against the `attack` column, using the grouped
> tie-invariant implementation in `ap_grouped.py`.
>
> Draw `B = 999` **distinct** shifts `k_b` without replacement from
> `{1, ..., n-1}` using `numpy.random.default_rng(20260903)`, form
> `y^(k) _t = y_((t+k) mod n)`, and compute `AP_b` for each. Then
>
>     p = (1 + #{ b : AP_b >= AP_obs }) / (B + 1)
>
> **P5 is confirmed iff `p < 0.01`. Otherwise P5 is REFUTED.**
>
> Sampling is **without replacement**, so `p` is the **exact** p-value rather
> than a conservative bound, and has strictly more power than the
> with-replacement scheme (Phipson & Smyth 2010, SAGMB 9(1) Art. 39, sections 5
> and 6). Exactness rests on each draw yielding a distinct statistic;
> `mt = n - 1 = 291,599` against `B = 999`, and the implementation must assert
> `B` distinct `AP_b` values and report any collisions.
>
> **Logical status: P5 is not a member of P0 and gates nothing.** A P5
> refutation does NOT void P1 or P3 — coverage and metric-ranking behaviour
> remain validly measurable on a detector with no discriminative power.
> If P5 is refuted, P1 and P3 are still computed and reported, and every
> reported number carries the annotation "P5 REFUTED: discrimination not
> established". A P5 refutation is the headline result, not a suppressed one.

#### (e) P6 is registered — the temporal null. Left unrun in v1.

A circular shift preserves label structure but cannot prevent a detector from
exploiting temporal phase. HAI attacks are temporally structured, so a detector
could pass P5 on time-of-day alone.

> **P6.** Construct TIME_NULL, a detector whose only inputs are temporal
> variables — hour, minute, day of week, sample index — and run it through the
> **identical** P5 machinery on `test1`.
>
> If TIME_NULL passes P5, then passing P5 establishes nothing on its own, and
> the scientific question becomes whether the detector carries
> attack-discriminative information **beyond temporal structure**.
>
> The control hierarchy is PURE_NOISE → TIME_NULL → the detector under test.
> **P6 is registered and left unrun in v1.** No expectation is registered for
> it. It is stated here so whoever runs it first knows it was the intended next
> step and was not quietly skipped after an unfavourable result.

#### (f) The AP implementation is constrained

AP must be computed over distinct score values, satisfying: *permuting
observations within an equal-score group cannot change AP.* The original
index-order implementation is **WITHDRAWN**: it changed AP on 50 of 50
within-group reshuffles, swung 0.0091 on a constructed case from tie order
alone, and returned 0.611 where prevalence 0.300 was correct.

#### (g) eTaPR — three conflicting published defaults, and a crash

`github.com/saurf4ng/eTaPR` at `af9e7ae` does not have one set of defaults. The
README CLI documentation gives `theta_p 0.5, theta_r 0.1, delta 0.0`; the
README worked example uses `theta_r 0.01`; `evaluate_w_streams`'s signature
declares `theta_p 0.7`; `evaluate_w_ranges` has no defaults at all. "eTaPR at
published defaults" is therefore not a well-defined instruction, and the entry
point our per-tick data requires is the one whose signature contradicts the
documentation. **The documented values are registered and must be passed
explicitly on every call**, so no signature default can silently apply.

Separately, `evaluate_w_streams` **raises AttributeError when a detector
predicts nothing** — `_etar_p()` returns the scalar `0.0` on its no-prediction
guard while `eTaR_p()` calls `.mean()` on it. At threshold quantile 0.99 a
sweep configuration may produce zero positive predictions, so the score such a
configuration receives is registered in advance as `0.0`, keeping the
configuration in the grid rather than dropping it and silently shrinking the
enumerated sweep that P1 depends on.

An independent implementation, `etapr_independent.py`, agrees with the
published one below `5e-13` on all seven comparable fixture cases. The fixture
was generated from the published package and committed **before** the
independent implementation was written.

#### (h) The freeze

All remaining choices are fixed in `frozen.py`, **sealed at**

    6005fb60e473dfdf22b165b7b6375b52a0e5a055c57cc2fea8a013074a7bbbf4

over 48 constants, device-verified identical on aarch64 and x86_64. The module
recomputes the digest at run time and exits 1 on any mismatch, so an
independent observer can confirm that the values registered are the values that
ran. Detectors must import every constant from it.

`CONFORMAL_ALPHA = 0.10`, nominal coverage 0.90 — **registered, not merely
frozen**, because P3's 0.05 shortfall is an absolute threshold whose stringency
depends on the nominal level. Chosen to match the level at which VERA's BATADAL
coverage failure was measured (0.697 against nominal 0.90), so P3 tests a
replication rather than a differently tuned quantity.

The P1 sweep grid is enumerated as 3 x 3 = 9 configurations, windows
{30, 60, 120} seconds against quantiles {0.90, 0.95, 0.99}. Deliberately small:
with enough configurations, two metrics disagreeing somewhere becomes
near-certain and P1 stops being a claim. **Enlarging this grid after seeing
results would be fraud, not amendment.**
