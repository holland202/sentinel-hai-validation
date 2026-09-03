# PRE-RUN ADVERSARIAL AUDIT

Adversarial review of `sentinel-hai-validation` conducted 2026-09-03, at
commit `a4351cd`, **before the first HAI detector run**. The reviewer's brief
was to attack the experiment, not to help it succeed.

Nothing in this document reports a detector result. No HAI detector has run.

Findings are ordered by severity. Two are rated CRITICAL, meaning the
experiment as currently registered could produce a published result that is
not evidence of anything.

---

## SUMMARY TABLE

| # | Finding | Severity | Claim affected | Fixable without amending prereg? |
|---|---|---|---|---|
| F1 | P0a has no power requirement; a random-score detector passes it | CRITICAL | P0a, and by inheritance P1/P3 | No — needs a new registered P0c |
| F2 | P1 is close to unfalsifiable: the sweep grid is unspecified | CRITICAL | P1 | No — needs the grid registered |
| F3 | Reproducibility gap: `fetch_hai.sh` and `fdia_control.py` are not on origin | HIGH | Whole repo's reproducibility claim | Yes — commit them |
| F4 | Attack-label column is unregistered; four columns give four answers | HIGH | P1, P3, all scoring | No |
| F5 | P0b-1 registered `0 of 200`, ignoring detector false-positive rate | HIGH | P0b-1 | No — measured FAIL, needs amendment |
| F6 | Training files not verified attack-free | MEDIUM | P0a's premise | Yes — measurement |
| F7 | eTaPR parameters unregistered | MEDIUM | P1, P2 | No |
| F8 | A5 is an artifact of F5's bad formulation; A1–A5 incomplete | MEDIUM | Amendment 2 | No |

---

## 1. PROVENANCE — MEASURED, NOT ASSERTED

Cold clone of `https://github.com/holland202/sentinel-hai-validation.git`
performed in an environment with no access to the working tree.

**Verified good:**

- `e48cdac` exists on origin and contains exactly four files: `.gitignore`,
  `LICENSE.md`, `PREREG.md`, `README.md`. No data, no fetch script, no
  detector. The claim that registration preceded acquisition is supported by
  the commit contents, not only by the timestamp.
- Amendments are append-only. The pre-amendment body of `PREREG.md` at
  `e48cdac` appears byte-identical inside `PREREG.md` at HEAD. Original claims
  were not edited to look better.
- Amendment ordering is coherent: `e48cdac` → `38627d5` → `6befd98` →
  `a4351cd`.

**F3, HIGH — the BATADAL-class failure is present right now.**

Tracked files at HEAD: `.gitignore`, `LICENSE.md`, `PREREG.md`, `README.md`,
and four files under `figures/`. That is all.

`fetch_hai.sh` was written on the operator's device, ran successfully, and
verified all four HAI 20.07 sha256 values. **It is not on origin.**
`fdia_control.py` exists only in a container. A cold clone therefore cannot
acquire the dataset, cannot run the P0b control, and cannot reproduce any
claimed pre-run state. The repository currently describes a reproducible
protocol it does not ship.

This is the exact defect class recorded from `sentinel-batadal-validation`,
where a genuine 18-test smoke suite passed locally and never reached origin.
A linter finds nothing wrong, because nothing is wrong with the code that is
there — the failure is an absence.

**Standing test, to be run before any claim of reproducibility:**

Clone to a fresh directory with no access to the working tree. Assert that the
set of files required by the protocol is a subset of `git ls-files`. Run the
fetch script from the clone. Run every gate script from the clone. Any script
named in `README.md` or `PREREG.md` that is absent from `git ls-files` is a
finding, regardless of whether it works on the author's machine.

"Exists locally" and "is published" are separate propositions and must be
tested separately.

---

## 2. ATTACKING THE ANTI-VACUITY DESIGN

P0a as registered: on a clean held-out slice of HAI training data, the breach
rate at conformal level `q` must fall in `[0.5·(1−q), 2·(1−q)]`.

**F1, CRITICAL — P0a is a calibration check wearing the costume of a validity
gate.**

Construct a detector that emits pure noise as its anomaly score, independent
of the input. Its conformal quantile is a quantile of noise; its breach rate
on clean data is exactly nominal by construction. **It passes P0a perfectly.**
It also has zero discriminative power, and P0b is silent about it because P0b
tests the state-estimation harness, not the detector.

So a useless detector passes the entire P0 gate, after which the prereg says
P1 and P3 may be interpreted. The gate does not gate.

Note the internal inconsistency: P0b is explicitly two-sided — it requires
0 of 200 on the invisible set **and** ≥190 of 200 on the visible set,
precisely so a detector that never fires cannot pass. P0a has only the
never-fires half. **P0b learned the lesson P0a did not.**

Required: a registered **P0c** power floor. The detector must exceed a
matched-budget random-score control on the HAI attack set by a stated margin,
with the control's score reported alongside. Without it, P0's PASS licenses
nothing.

**Case-by-case on the attacks named in the brief:**

| Attack | Prevented by current design? |
|---|---|
| Trivial all-negative detector | Partly. A constant score gives breach rate ~0, below the `0.5·(1−q)` floor, so P0a rejects it. **A calibrated-but-uninformative detector is not rejected.** |
| Class imbalance | No. HAI test attack fraction is not yet measured and not registered. Point-wise F1 in P1 is imbalance-sensitive. |
| Window-boundary effects | No. Warm-up handling for the first `W` ticks is unspecified. |
| Timestamp leakage | No. HAI carries a `time` column. No channel list is registered, so nothing forbids feeding it to VERA's ridge, which would let the model exploit time-localised attacks. |
| Duplicate / near-duplicate rows | No. Unaddressed. |
| Training contamination | Untested. See F6. |
| Label leakage | Partly. Training files carry `attack`, `attack_P1..P3`; nothing registered forbids using them as features. |
| Missing values | No. Unaddressed. |
| Constant / near-constant channels | No. JSD over a degenerate histogram is ill-defined or trivially zero; HAI is known to contain low-variance columns. |
| Emits null but cannot emit meaningful positives | **No. This is F1.** |

**F6, MEDIUM.** P0a's premise is that HAI training data contains no attacks.
The training files carry the label columns, so this is directly checkable and
has not been checked. If any training row has `attack == 1`, P0a's clean slice
is not clean and the gate is measuring something else. This should be the
first thing `verify_hai.py` prints.

---

## 3. ATTACKING P0b MATHEMATICALLY

**Derivation.** For the linear DC model with weighted least squares,

    theta_hat = (H' W H)^-1 H' W z  =  K z
    r         = z - H theta_hat     =  (I - H K) z  =  S z

The key identity is `S H = H - H (H'WH)^-1 H'W H = H - H = 0`. Therefore for
any `c`,

    r' = S (z + H c) = S z + (S H) c = S z = r

exactly, and independently of `c`. Invariance is a property of `S` annihilating
the column space of `H`. It is not approximate and not statistical.

**Empirically confirmed:** across 200 structured trials,
`max |r' - r| = 3.464243e-15` against a tolerance of `2.729078e-12`. The
theorem holds to machine precision.

**F5, HIGH — and the registered prediction failed anyway.**

The container run returned `structured detected 6 of 200` against a registered
`0`. Diagnosis: all six were trials where the **clean, unattacked** measurement
already exceeded the chi-square threshold. Baseline false positives — 6
observed against 10 expected at the 0.95 level. The attack contributed exactly
zero detections. Every structured trial that tripped would have tripped
without any attack.

The registered prediction `0 of 200` silently assumed a detector with no
false-positive rate. No residual-based BDD has that. The prediction was
ill-posed; the theory was never in question.

The correct registered quantity is that the **detection indicator is unchanged
trial by trial** — `1[J' > tau] == 1[J > tau]` for all trials — with the clean
count reported alongside. Not that the count is zero.

**F8, MEDIUM — are A1–A5 sufficient? No. Necessary? Only partly.**

- **A1** (identical `H`) — necessary. A different `H` breaks `S H = 0`.
- **A2** (no bad-data rejection loop) — necessary. An iterative
  largest-normalised-residual loop removes measurements and is not invariant.
- **A3** (no clipping) — necessary. Saturation is nonlinear; `S` no longer
  applies.
- **A4** (exact arithmetic) — **not an assumption.** It is a fact about the
  machine, and what it generates is a reporting requirement (a tolerance),
  not a condition that can hold or fail.
- **A5** (no knife edge) — **an artifact of the wrong formulation.** Once
  P0b-1 compares `J'` to `J` rather than to `tau`, threshold proximity becomes
  irrelevant, because the two are equal to machine precision regardless of
  where they sit. A5 exists only because F5 existed.

And the assumption that actually broke the prediction — that the detector has
no false-positive rate under the null — **appears nowhere in A1–A5.**

Amendment 2 was written specifically to enumerate the conditions under which
P0b's verdict is meaningful. It missed the one that bit. This is the same
failure recorded as `arch_map`'s P10b: the instrument built to find a defect
contained that defect.

**Does the current test establish what P0b claims?** No. It establishes the
invariance (P0b-3, `3.46e-15`) and the two-sided liveness (P0b-2, `200/200`).
It does not establish P0b-1 as written, because P0b-1 as written is not the
right question.

---

## 4. HIDDEN DEGREES OF FREEDOM

Every decision still available after seeing HAI data. Classification per the
brief.

| Parameter | Status |
|---|---|
| HAI version | PRE-REGISTERED (Amendment 1: 20.07) |
| Dataset file hashes | PRE-REGISTERED, device-verified |
| Which train file(s) to fit on | **CURRENTLY UNCONTROLLED** |
| Which test file(s) to score | **CURRENTLY UNCONTROLLED** |
| Channel selection from 59 process columns | **CURRENTLY UNCONTROLLED** |
| Inclusion of the `time` column | **CURRENTLY UNCONTROLLED** |
| Normalisation and whose statistics | **CURRENTLY UNCONTROLLED** |
| JSD window length `W` | DATA-DEPENDENT (swept, grid unspecified) |
| JSD histogram bin count | **CURRENTLY UNCONTROLLED** — JSD is strongly binning-sensitive |
| Ridge lambda | **CURRENTLY UNCONTROLLED** |
| Conformal alpha / `q` | **CURRENTLY UNCONTROLLED** — P0a references `q` and never fixes it |
| Calibration split fraction | **CURRENTLY UNCONTROLLED** |
| Warm-up handling, first `W` ticks | **CURRENTLY UNCONTROLLED** |
| Missing-row treatment | **CURRENTLY UNCONTROLLED** |
| Attack-label column: `attack` vs `attack_P1..P3` | **CURRENTLY UNCONTROLLED** — see F4 |
| eTaPR theta parameters | **CURRENTLY UNCONTROLLED** — see F7 |
| Tick-to-episode aggregation | **CURRENTLY UNCONTROLLED** |
| Random seed | **CURRENTLY UNCONTROLLED** |
| P3's "nominal" coverage level | **CURRENTLY UNCONTROLLED** |

Two PRE-REGISTERED, one DATA-DEPENDENT, **sixteen UNCONTROLLED.**

**F2, CRITICAL.** P1 predicts that point-wise F1 and eTaPR select different
best configurations across a sweep of window length and threshold. With
sixteen uncontrolled knobs and an unspecified grid, a configuration pair
exhibiting metric disagreement can almost always be found. **A prediction that
is satisfiable by enlarging the search is not falsifiable.**

P1 requires, registered before scoring: the exact grid (window lengths,
thresholds, bin counts), the exact ranking rule, and a stated criterion for
what counts as disagreement. Otherwise P1 should be marked UNRESOLVABLE rather
than reported.

**F4, HIGH.** HAI 20.07 carries four label columns. `attack` is the global
flag; `attack_P1`, `attack_P2`, `attack_P3` are per-process. Scoring against
different columns yields different precision, recall, F1 and eTaPR. Choosing
after seeing results is a researcher degree of freedom sufficient on its own
to manufacture P1. The column must be registered now, in advance, with the
others reported as secondary if reported at all.

**F7, MEDIUM.** eTaPR is parameterised. Selecting its parameters after seeing
scores would let the "independent reimplementation" be tuned toward a
favourable comparison. Parameters must be registered, and agreement with the
published implementation must be demonstrated on a fixture computed before any
HAI score exists.

---

## 5. THE UNRESOLVED STATE

The correct outcome is **UNRESOLVED** — not PASS, not FAIL, not a convenient
reading — in each of the following. An UNRESOLVED prediction is reported as
UNRESOLVED and kept.

1. **P2, published baseline.** If no citable eTaPR result on HAI **20.07**
   exists, P2 is UNRESOLVED. It may not be silently rescored against a
   different HAI version, nor against a baseline the author computes himself
   and then calls published.
2. **Version mismatch.** If a baseline exists but for another HAI version, the
   comparison is UNRESOLVED. Cross-version comparison is not a result.
3. **Failed data verification.** Any sha256 mismatch halts everything.
   Downstream predictions are UNRESOLVED, never "run anyway on the file we
   got".
4. **Failed P0b assumption.** If A1, A2 or A3 fails, P0b is UNRESOLVED and P1
   and P3 are VOID. Fixing the assumption and rerunning is permitted; quietly
   relaxing the assumption is not.
5. **P0a failure.** VOID for P1 and P3, per the existing prereg. Unchanged.
6. **Insufficient provenance.** If a result cannot be regenerated from a cold
   clone, it is UNRESOLVED regardless of how convincingly it ran on the
   author's device. F3 is currently in this state.
7. **Metric disagreement.** If the independent eTaPR implementation disagrees
   with the published one and the disagreement is not resolved, scoring halts
   and the disagreement is the finding. P1 and P2 are UNRESOLVED. The
   implementation that gives the more favourable number is not selected.
8. **Ill-posed prediction.** If a prediction turns out not to ask a
   well-defined question — as with P0b-1 — it is recorded as failed **and**
   amended, with the original text preserved. It is never retroactively
   reinterpreted into a pass.

**Binding rule:** an ambiguous prediction is not repaired by redefining it.
It is marked, amended in the append-only record, and the original stands.

---

## RECOMMENDED ORDER OF OPERATIONS

1. Commit `fetch_hai.sh` (F3). Nothing else is credible until a cold clone can
   acquire the data.
2. Commit `fdia_control.py` **in its failing state**, with its verbatim output,
   before any correction. The registered prediction failed; the public record
   should show that it failed.
3. Amendment 3: restate P0b-1 as indicator-equality; record that A1–A5 was
   incomplete and that A5 was an artifact.
4. Amendment 4: register P0c (power floor), the P1 sweep grid, the attack-label
   column, eTaPR parameters, and the conformal level.
5. `verify_hai.py`, leading with whether the training files are attack-free.
6. Only then, detectors.

Steps 3 and 4 must land before any HAI detector runs, or the sixteen
uncontrolled parameters become sixteen opportunities to reach a preferred
answer.

---

*Vincit Omnia Veritas.*
