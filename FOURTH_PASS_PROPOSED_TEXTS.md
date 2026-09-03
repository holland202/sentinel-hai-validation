# FOURTH PASS — PROPOSED TEXTS, NOT YET APPLIED

Prepared 2026-09-03. **`PREREG.md` is not modified by this document.** These
are proposed texts for review. No HAI detector has run.

New finding this pass, and a second one carried from the device run:

- **AP tie handling is broken in the reference implementation.** Measured:
  50 of 50 within-group reshuffles change AP under index tie-breaking; 0 of 50
  under grouped scoring.
- **`fdia_control.py` is not bit-reproducible across architectures.**
  `max |r' - r|` = `3.464243e-15` (x86_64 container) vs `4.927482e-15`
  (aarch64, S25 Ultra). All other outputs matched exactly.

---

## 1. CIRCULAR-SHIFT NULL — EXACT DEFINITION

For a label vector `y` of length `n` and shift `k`:

    y^(k)_t = y_((t + k) mod n),   t = 0 .. n-1

- **Admissible shift set:** `k ∈ {1, ..., n-1}`. `k = 0` is excluded — it is
  the identity and enters the p-value only through the `+1` correction.
- **Enumerated or sampled: sampled.** Full enumeration on `test2`
  (`n = 153,000`) measured 0.86 hours on x86_64 and would be several hours on
  the S25. **`B = 999` Monte Carlo draws**, `k_b ~ Uniform{1..n-1}`, drawn
  with `numpy.random.default_rng(20260903)` (PCG64). Draws are with
  replacement; no de-duplication.
- **Wraparound:** the shift is cyclic, `numpy.roll`. Labels crossing the array
  end reappear at the start. No truncation, no padding, no guard band. An
  attack episode split by the wrap remains two contiguous runs whose total
  length and prevalence are unchanged, which is what the null requires.

**What is preserved:** the exact label prevalence, the exact number of attack
episodes, and the exact length of every episode. The temporal structure of the
label vector is carried through untouched.

**What is destroyed:** the alignment between label episodes and score
excursions. That alignment is precisely the quantity under test.

**Why this matters for HAI specifically.** HAI attacks are contiguous
episodes — `test1` carries 11,538 attack ticks (3.957%) and `test2` 5,989
(3.914%), in runs, not scattered. A sliding-window JSD score is autocorrelated
by construction, because consecutive windows share `W-1` samples. An iid
permutation null therefore compares an autocorrelated score series against
scattered labels while the observed statistic uses contiguous ones. The null
is the wrong null, and the test is anti-conservative for exactly the detector
this repository intends to run.

---

## 2. FALSE-PASS REPRODUCTION

Identical scores and labels supplied to both arms. Corrected grouped AP.
`N = 20,000`, `B = 200`, 100 trials, `alpha = 0.01`, seed `20260903`.
The detector is noise with zero detection ability by construction.

| Null detector | iid permutation | circular shift |
|---|---|---|
| iid noise, phi = 0.000 | 0/100 = 0.000 | 0/100 = 0.000 |
| mild autocorrelation, phi = 0.900 | **30/100 = 0.300** | 0/100 = 0.000 |
| smooth, phi = 0.999 | **47/100 = 0.470** | 1/100 = 0.010 |

The circular-shift arm sits at the nominal level. The permutation arm reaches
47% at a nominal 1%. `phi = 0.9` is ordinary smoothing, not a pathological
case, and it already produces a 30% false-pass rate.

---

## 3. AP TIE HANDLING — REQUIRED IMPLEMENTATION

Constructed case: `n = 4,000`, 420 positives in three contiguous blocks, 74
distinct score values.

| AP implementation | value |
|---|---|
| ties broken by index ascending | 0.4613625489 |
| ties broken by index descending | 0.4522478316 |
| grouped, tie-invariant | 0.4474675419 |

Index-order swing: **0.0091147173**, roughly 1% of AP, produced by nothing but
tie-breaking order.

Invariance test — 50 random reshuffles within equal-score groups:

- index tie-breaking: **50 of 50 changed AP**
- grouped scoring: **0 of 50 changed AP**

> **Required invariant:** permuting observations within an equal-score group
> must not change AP.

> **Required implementation:** AP is computed over **distinct score values**.
> Observations sharing a score form one threshold group; precision and recall
> are evaluated at group boundaries only, and
> `AP = sum over groups of (R_i - R_{i-1}) * P_i`.

This matters concretely because JSD over a finite histogram produces many
exact ties, and because HAI attack labels are contiguous in index — so
index-order tie-breaking correlates with the labels and biases AP. This is the
note054 defect class: a published `+0.117` that was sort-path dependent and
whose tie-corrected value was `+0.1480`.

---

## 4. PROPOSED P5 — FINAL WORDING

> **P5 — discrimination exists.** Registered before any HAI score is computed.
>
> At the frozen reference configuration in `frozen.py` — not the maximum over
> the P1 sweep — compute the detector's scores on `test1` of HAI 20.07 and
> evaluate average precision against the `attack` column using the grouped,
> tie-invariant implementation specified in Section 3.
>
> Let `AP_obs` be that value. For `b = 1..B` with `B = 999`, draw
> `k_b ~ Uniform{1..n-1}` using `numpy.random.default_rng(20260903)` and
> compute `AP_b` = average precision of the same scores against `roll(y, k_b)`.
>
>     p = (1 + #{ b : AP_b >= AP_obs }) / (B + 1)
>
> **P5 is confirmed iff `p < 0.01`. Otherwise P5 is REFUTED.**
>
> This is a **Monte Carlo randomization test, not an exact test.** The `+1`
> correction in numerator and denominator makes the p-value valid — it
> guarantees `P(p <= alpha) <= alpha` under the null — but the reference set
> is sampled, not enumerated. The smallest attainable p-value is `1/1000`.
>
> **Logical status: P5 is not a member of P0 and does not gate anything.** A
> P5 refutation does NOT void P1 or P3. Coverage and metric-ranking behaviour
> remain validly measurable on a detector with no discriminative power, and
> discarding them would throw away valid measurements of different quantities.
> If P5 is refuted, P1 and P3 are still computed and reported, and every
> reported number carries the annotation "P5 REFUTED: discrimination not
> established." A P5 refutation is the headline result, not a suppressed one.
>
> **Registered limitation.** A circular shift preserves label structure but not
> score structure. A detector whose scores happen to align with the labels'
> particular phase for a non-causal reason could still pass. P5 is a floor, not
> a proof of validity.

Note the change from the third pass: P5 is scored on **`test1`**, the same
file as P1 and P3. This is deliberate. P5 is no longer a gate, so it cannot
contaminate a gate, and asking whether *this* detector discriminates on *the*
evaluation set is the scientifically meaningful question. `test2` is
reserved as an untouched replication set.

---

## 5. PROPOSED AMENDMENT 3 — FINAL WORDING

> ### Amendment 3 — 2026-09-03, before any HAI detector run
>
> **P0b is restructured into three independently falsifiable parts. A4 is
> removed and A5 is deleted. The original P0b text above is unchanged.**
>
> The original P0b-1 registered "0 of 200 structured detections". It was run
> and **FAILED, measured 6 of 200**. Diagnosis: all six were trials in which
> the clean, unattacked measurement already exceeded the chi-square threshold —
> baseline false positives, 6 observed against 10 expected at the 0.95 level.
> The attack contributed zero detections. The theorem held throughout:
> `max |r' - r|` was within tolerance in every trial.
>
> The registered prediction silently assumed a detector with no false-positive
> rate. No residual-based bad-data detector has that. **The failure is kept and
> is not reinterpreted as a pass.**
>
> The assumption that broke the prediction appears nowhere in A1–A5. Amendment
> 2 was written to enumerate the conditions under which P0b's verdict is
> meaningful, and it missed the one that bit.
>
> **Restated:**
>
> - **P0b-1 — numerical invariance.** Over 200 structured injections `a = Hc`,
>   `max |r' - r| <= TOL`, with `TOL = 1e3 * eps * ||z||` computed and printed
>   by the script. Registered as a **tolerance test only**. The value of
>   `max |r' - r|` is architecture-dependent and is never registered as a
>   constant: measured `3.464243e-15` on x86_64 and `4.927482e-15` on aarch64
>   from an identical seeded run, both far within `TOL = 2.729078e-12`.
>   Falsified by exceeding TOL.
> - **P0b-2 — the detection indicator is unchanged.** For every trial,
>   `1[J' > tau] == 1[J > tau]`, compared trial by trial, with the clean
>   detection count reported alongside. Falsified by any trial in which the
>   indicators differ.
> - **P0b-3 — matched unstructured control.** At the same `tau` and identical
>   `||a||`, at least 190 of 200 unstructured injections are detected.
>   Falsified by fewer than 190.
>
> **A4 is removed from the assumption list.** Exact arithmetic is a fact about
> the machine, not a condition that can hold or fail. It is replaced by the
> printed `TOL` in P0b-1.
>
> **A5 is deleted.** Once P0b-2 compares indicators trial by trial instead of
> a count against a threshold, threshold proximity is irrelevant. A5 existed
> only because the original P0b-1 was ill-posed.
>
> **Surviving assumptions: A1, A2, A3**, each necessary. With P0b-2's
> corrected form they are sufficient, because the false-positive rate is now
> handled structurally rather than assumed away.

---

## 6. PROPOSED AMENDMENT 4 — FINAL WORDING

> ### Amendment 4 — 2026-09-03, before any HAI detector run
>
> **Three corrections of published fact, one withdrawn proposal, one new
> registered prediction.**
>
> **(a) Amendment 1 published a wrong number.** It states "63 columns". The
> measured value is **64**. The error came from splitting a semicolon-delimited
> header on a comma. The original text stands; this is the correction.
>
> **(b) `train2` is not attack-free.** Measured across all four HAI 20.07
> files at the pinned commit:
>
> | File | Rows | attack | % |
> |---|---|---|---|
> | train1 | 309,600 | 0 | 0.000 |
> | train2 | 241,200 | **776** | **0.322** |
> | test1 | 291,600 | 11,538 | 3.957 |
> | test2 | 153,000 | 5,989 | 3.914 |
>
> P0a's premise — that training data contains no attacks — is false for
> `train2`. **Fitting and calibration use `train1` only.** `attack` is exactly
> `OR(attack_P1, attack_P2, attack_P3)`, with zero mismatches across all
> 995,400 rows, so `attack == 0` is sufficient to establish a row is clean.
>
> **(c) A candidate P0c was proposed and withdrawn before registration.** The
> proposal was an iid label-permutation test of discrimination. It was tested
> against a null detector with zero detection ability and **falsely passed 30%
> of the time at phi = 0.9 and 47% at phi = 0.999, against a nominal 1%**. HAI
> attack labels are contiguous episodes and sliding-window scores are
> autocorrelated, so an iid permutation null is the wrong null. **The proposal
> is withdrawn, not registered, and this record of its failure is kept.**
>
> **(d) P5 is registered** in the form given in the fourth-pass document, using
> a circular-shift null which measured 0/100 and 1/100 false passes on the same
> two null detectors. **P5 is not a member of P0 and voids nothing.**
>
> **(e) The AP implementation is constrained.** AP must be computed over
> distinct score values, satisfying the invariant that permuting observations
> within an equal-score group cannot change AP. Index-order tie-breaking
> measured a 0.0091 swing on a constructed case and changed AP on 50 of 50
> within-group reshuffles.
>
> The following are **implementation freezes, not amendments**, and are
> published in `frozen.py` before any detector runs: primary label `attack`;
> fit and calibrate on `train1` with a contiguous 60/40 temporal split and no
> shuffling; channel set as all process columns excluding `time` and the four
> label columns; JSD bin count; ridge lambda; conformal alpha; warm-up
> handling; seed; the enumerated P1 sweep grid; eTaPR parameters at published
> defaults.

---

## 7. CI GATE DESIGN

**The distinction that matters:** *the repository contains the verifier* is
not *the repository's verifier passes*. A workflow that only checks files
exist proves the former and is worthless for the latter. Every gate below
executes something and asserts on its exit status.

`.github/workflows/veritas_gate.yml`, on push and pull request, from a clean
checkout with `fetch-depth: 0`:

| Step | Action | Fails when |
|---|---|---|
| 1 | Echo `github.sha` into the log | never — this records which commit was tested |
| 2 | `git merge-base --is-ancestor <PREREG_SHA> HEAD` | the prereg is not an ancestor of the tested commit |
| 3 | Assert amendment order: each amendment commit is an ancestor of the next | amendments were reordered or rewritten |
| 4 | Assert the pre-amendment body of `PREREG.md` at `e48cdac` appears verbatim in `PREREG.md` at HEAD | a registered claim was edited rather than amended |
| 5 | `git ls-files` contains every script named in `README.md` and `PREREG.md` | a script exists locally but not on origin — the BATADAL-class failure |
| 6 | Run `fetch_hai.sh` | any download fails or any sha256 mismatches |
| 7 | Run `verify_hai.py`, assert 64 columns and the four per-file attack counts | the dataset changed under the pin |
| 8 | Run `fdia_control.py`, assert exit 0 | P0b fails |
| 9 | Run `test_ap.py`, assert AP invariance under within-group reshuffles | the tie-invariance requirement is violated |
| 10 | Run `test_frozen.py`, asserting every constant in `frozen.py` equals its registered value | a frozen constant was changed |
| 11 | `git merge-base --is-ancestor <FREEZE_SHA> HEAD` and assert no detector script exists in any commit before `<FREEZE_SHA>` | a detector ran before the freeze |

Step 11 is the one that cannot be recovered once violated. Steps 2 through 5
and 11 are pure git operations, so an independent observer can re-run them
from a clone with no trust in the author. Steps 6 through 10 are executions
whose pass or fail an observer reads from GitHub's own run record rather than
from a file in the repository.

**`FROZEN.md` is not used.** Constants live in `frozen.py`, which the detector
imports, so a value cannot be frozen in prose and different in code.

---

## 8. WHAT IS PRESERVED

This sequence stays in the git history exactly as it happened and is not
tidied:

    iid-permutation P0c proposed
      -> adversarial null constructed
      -> 30% and 47% false-pass rates measured
      -> P0c withdrawn BEFORE registration

together with the original `fdia_control.py` failing at 6 of 200, and the
architecture-dependent `max |r' - r|`. A repository in which the final code
mysteriously always worked is weaker evidence than one that records what
broke.

---

*Vincit Omnia Veritas.*
