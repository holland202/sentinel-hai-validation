# SECOND ADVERSARIAL PASS — audit of the audit

Conducted 2026-09-03 at commit `6e5ba3f`, before any HAI detector run. The
brief was to attack the first audit's own findings rather than accept them
because they sounded persuasive. Two of the eight were overstated. Two new
defects were found by measurement.

Nothing here reports a detector result.

---

## 0. TWO MEASUREMENTS THAT CHANGE THE DESIGN

Measured on the four HAI 20.07 files, all 995,400 rows, from the pinned
commit `2a814ce`:

| File | Rows | attack | % | P1 | P2 | P3 | rows where attack != OR(P1,P2,P3) |
|---|---|---|---|---|---|---|---|
| train1 | 309,600 | 0 | 0.000 | 0 | 0 | 0 | 0 |
| train2 | 241,200 | **776** | **0.322** | 776 | 0 | 0 | 0 |
| test1 | 291,600 | 11,538 | 3.957 | 9,683 | 2,495 | 1,197 | 0 |
| test2 | 153,000 | 5,989 | 3.914 | 5,207 | 3,510 | 604 | 0 |

**M1 — `train2` is not attack-free.** It contains 776 attack rows, all in
process P1. Any design that fits "on the training data" and assumes it is
clean is wrong for `train2`. `train1` is genuinely clean. This upgrades F6
from MEDIUM/unverified to a confirmed defect that forces a design decision.

**M2 — `attack` is exactly `OR(attack_P1, attack_P2, attack_P3)`,** with zero
mismatches across all 995,400 rows. The process labels are strictly redundant
for global detection.

**M3 — a published number in Amendment 1 is wrong.** Amendment 1 states
"63 columns". The measured value is **64**. The earlier count came from
splitting the header on a comma when the file is semicolon-delimited. Under
the house rule that numbers in prose match code output verbatim, this must be
corrected in the append-only record, not edited in place.

---

## 1. F1 AND THE PROPOSED P0c — DOES IT SURVIVE?

**My original phrasing was sloppy.** I wrote "matched-budget random-score
control". A random-score control has no parameters, so there is no budget to
match. The phrase was borrowed from a different kind of experiment.

**The formal null detector.** Let `s_t ~ U(0,1)` iid, independent of the
input. Its conformal quantile is a quantile of `U(0,1)`; its breach rate on
clean data is exactly `1-q` in expectation. **It passes P0a for every `q`.**
Its average precision on any label vector equals the prevalence of that
vector. It has zero discriminative power. P0a therefore does not exclude it,
and the first audit's F1 stands.

**Can P0c be specified without adding more degrees of freedom than it
removes?** Evaluating each named vulnerability:

| Vulnerability | Does a naive attack-set power floor suffer it? | Fix |
|---|---|---|
| Attack prevalence | Yes. AP's floor is prevalence, which differs by file. | Permutation preserves prevalence exactly |
| Threshold selection | Yes, if the statistic is thresholded. | Use average precision — threshold-free |
| Post-hoc control construction | Yes. | Control fully specified before the run |
| Random-seed selection | Yes, for a single draw. | 200 permutations, seed fixed now |
| Multiple comparisons | **Yes, severely** — a floor evaluated at the sweep max is inflated. | Evaluate at ONE registered reference configuration |
| Test-set overfitting | Yes — P0c consumes labels. | Score P0c on `test2`, P1/P3 on `test1` |
| Detector/control budget mismatch | Not applicable — the control has no budget. | Drop the phrase |

**Verdict: YES, P0c can be specified.** The mechanism is a label-permutation
test, not a power floor. Permutation preserves prevalence and the score
distribution exactly and destroys only the association, which is precisely
the quantity in question.

### Exact proposed P0c

> **P0c — discrimination exists.** At the registered reference configuration
> (not the sweep maximum), compute average precision `AP_true` of the
> detector's scores against the `attack` column of `test2`. Then compute
> `AP_perm` for each of 200 random permutations of that label vector, seed
> `20260903`. Registered prediction: `AP_true` exceeds the 99th percentile of
> the 200 permuted values.
>
> A detector emitting scores independent of the input has
> `AP_true ≈ AP_perm ≈ prevalence` and fails. Scored on `test2` only;
> `test1` is reserved for P1 and P3 and is not touched by P0c.

New constants introduced: statistic (AP), permutation count (200), seed, test
file assignment, reference configuration. **All five are fixable now, without
seeing any result.** Removed: the ability to pass the P0 gate with a detector
that cannot produce meaningful positives.

**Registered limitation, stated rather than hidden.** Simple permutation
destroys temporal structure. A detector that merely tracks time of day could
beat permuted labels and pass P0c while being scientifically uninteresting.
P0c is therefore a **floor, not a proof of validity**. Block permutation would
address this but introduces a block-size parameter, which is a new degree of
freedom for a check whose whole purpose is to remove them. The limitation is
registered instead of engineered away.

---

## 2. F2 AND P1 — A OR B?

**It is B, and my first audit overstated it.** P1 is falsifiable once the
configuration space is frozen. A large frozen space is not a problem; a space
that can grow after seeing results is. My "16 uncontrolled parameters" mixed
genuine threats with implementation constants and was rhetorically inflated.
Conceded.

**Taxonomy of the parameters:**

- **Change the hypothesis being tested** — the label column, the test file,
  the ranking rule, the disagreement criterion, and the sweep grid itself
  (because P1 *is* a claim about the sweep).
- **Implementation constants** — JSD bin count, ridge lambda, calibration
  split fraction, normalisation, warm-up handling, seed. These change the
  numbers but not what is being predicted. They must be frozen; they do not
  need registering as predictions.
- **Nuisance** — none that survive freezing.

### Minimum preregistration to make P1 falsifiable

Three items only:

1. The sweep grid as a **finite enumerated set**, written down before the run.
2. The **ranking rule**: for each metric, the best configuration is the argmax
   over that enumerated set.
3. The **disagreement criterion**: P1 is confirmed only if
   `argmax_F1 != argmax_eTaPR`, and refuted if they coincide.

Nothing else. Registering every implementation constant as a prediction would
be bureaucracy that makes the document harder to read without making the claim
harder to fool.

**Classification: IMPLEMENTATION FREEZE, not AMENDMENT.** P1 already says the
window length and threshold are swept. Enumerating the grid makes an existing
claim operational; it does not change the claim. It must be committed before
the run, and enlarging it afterwards would be fraud rather than amendment.

---

## 3. F4 — SETTLED FROM THE SPECIFICATION

The HAI README states that of the four label columns, `attack` applies to all
processes while the other three apply only to their corresponding control
processes. M2 confirms empirically that `attack` is the exact disjunction of
the three, with zero mismatches in 995,400 rows.

> **PRIMARY LABEL = `attack`**
> **SECONDARY = `attack_P1`, `attack_P2`, `attack_P3`** — reported for
> description only, never used to compute a verdict.

This is determined by the benchmark specification and confirmed by
measurement, not chosen because it produces better numbers.
**Classification: IMPLEMENTATION FREEZE.**

---

## 4. F6 — WHAT "CLEAN" MEANS, AND THE SPLIT

**Is `attack == 0` sufficient?** Yes. M2 establishes it is the exact
disjunction, so a row with `attack == 0` has no process-level attack either.
No separate check of the P-columns is required.

**Is the training set clean?** `train1` yes, 0 of 309,600. **`train2` no,
776 of 241,200.** The design must respond to this rather than assume it away.

> **Fit and calibrate on `train1` only.** It is genuinely attack-free and
> supplies 309,600 rows. Using `train2` would require deleting 776 rows,
> which introduces discontinuities into a dynamics model that assumes
> `x_{t+1} = A x_t + b` on contiguous time.

**What does "clean held-out training slice" mean?** It must be a **contiguous
temporal block**, not random rows. At 1-second sampling, adjacent rows are
near-duplicates; a random split places near-identical observations on both
sides and leaks. This is the same defect that makes the MSU/ORNL power-system
dataset unusable for sliding-window methods.

> Registered split: `train1` in temporal order, first 60% fit, last 40%
> conformal calibration and the P0a clean slice. No shuffling at any point.

**Classification: IMPLEMENTATION FREEZE** for the split;
**AMENDMENT REQUIRED** to record M1, since P0a's premise as written assumed
training data is attack-free and that is false for one of the two files.

---

## 5. P0b — FINAL THREE-PART STRUCTURE

Separating the theorem, the numerical test, and the detector behaviour:

> **P0b-1 — numerical invariance.** Over 200 structured injections `a = Hc`,
> `max |r' - r| <= TOL`, where `TOL = 1e3 * eps * ||z||` is computed and
> printed by the script. *Falsified by exceeding TOL.*
>
> **P0b-2 — the detection indicator is unchanged.** For every trial,
> `1[J' > tau] == 1[J > tau]`, compared trial by trial. The clean detection
> count is reported alongside. *Falsified by any trial where the indicators
> differ.*
>
> **P0b-3 — the matched unstructured control is detected.** At the same `tau`
> and identical `||a||`, at least 190 of 200 unstructured injections are
> detected. *Falsified by fewer than 190.*

**Independence check.** P0b-1 can pass while P0b-2 fails, if the
implementation compares the wrong quantities. P0b-2 passes trivially for a
detector that never fires, which is exactly why P0b-3 exists. P0b-3 can pass
while P0b-1 fails. None subsumes another.

**HAI dependency: none.** All three run on synthetic IEEE 14-bus data. P0b
can be executed and verified before the HAI data is opened.

**A4 — remove entirely.** Exact arithmetic is not an assumption that can hold
or fail; it is a fact about the machine. It is replaced by the explicit
printed `TOL` in P0b-1.

**A5 — delete.** Once P0b-2 compares indicators trial by trial instead of
comparing a count against a threshold, proximity to the threshold is
irrelevant: `J'` and `J` are equal to machine precision wherever they sit.
A5 existed only because the original P0b-1 was ill-posed.

**Surviving assumptions: A1, A2, A3.** All three are necessary — violating any
one breaks `S H = 0`. Together with the corrected P0b-2 formulation they are
now sufficient, because the false-positive rate that broke the original
prediction is handled structurally rather than assumed away.

---

## 6. THE DEGREES OF FREEDOM, REDUCED HONESTLY

Of the sixteen, ten are implementation constants that threaten nothing once
frozen. **Six genuinely threaten inferential validity:**

| # | Parameter | Affects | Fixable from spec or measurement? | Amendment? |
|---|---|---|---|---|
| 1 | Which train file | P0a's premise; `train2` is contaminated | Yes — measured, `train1` only | Record M1 |
| 2 | Test file assignment | P0c would contaminate P1/P3 | Yes — `test2` for P0c, `test1` for P1/P3 | No — freeze |
| 3 | Channel set | Post-hoc exclusion of hard channels | Yes — all 59 process columns; exclude `time` and the 4 label columns | No — freeze |
| 4 | JSD bin count | JSD is strongly binning-sensitive; highly tunable | No spec basis — must be fixed by fiat before the run | No — freeze |
| 5 | Conformal alpha | Appears inside P0a's bounds and P3's "nominal" | No spec basis — fix now | No — freeze |
| 6 | Sweep grid | P1 is a claim *about* the grid | Enumerate before the run | No — freeze |

The other ten — ridge lambda, calibration fraction, normalisation, warm-up,
seed, missing-row handling, aggregation, eTaPR parameters, label column, time
column — are either determined by the specification or are constants whose
only requirement is that they be fixed and published before the run.

---

## 7. AMENDMENT VERSUS IMPLEMENTATION

| Change | Classification |
|---|---|
| Commit `fetch_hai.sh` | NO AMENDMENT REQUIRED |
| Commit `fdia_control.py` in its failing state | NO AMENDMENT REQUIRED |
| P0b restated as three parts; A4 removed, A5 deleted | **AMENDMENT REQUIRED** — changes a registered claim |
| P0c added | **AMENDMENT REQUIRED** — new registered prediction |
| Record M1 (`train2` contaminated) and M3 (63 → 64 columns) | **AMENDMENT REQUIRED** — corrects published facts |
| Primary label = `attack` | IMPLEMENTATION FREEZE |
| `train1` only; 60/40 contiguous temporal split | IMPLEMENTATION FREEZE |
| `test2` for P0c, `test1` for P1/P3 | IMPLEMENTATION FREEZE |
| Channel set, JSD bins, alpha, lambda, seed, warm-up | IMPLEMENTATION FREEZE |
| Sweep grid enumerated | IMPLEMENTATION FREEZE |
| eTaPR parameters at published defaults | IMPLEMENTATION FREEZE |

**Two amendments, not eight.** Better engineering practice is not grounds for
amending a preregistration. Only a changed claim, a new claim, or a corrected
published fact is.

---

# PRE_RUN_VERITAS_GATE

No HAI detector may execute until every row is TRUE and its artifact exists.
Each gate names the file that proves it, so the checklist is machine-auditable
rather than a prose promise.

| # | Gate | Proving artifact | State |
|---|---|---|---|
| G1 | Cold clone from origin contains every script the protocol names | `gate_coldclone.sh` output, run outside the working tree | FALSE — `fetch_hai.sh`, `fdia_control.py` unpublished |
| G2 | Four HAI 20.07 sha256 verified on the S25 | `fetch_hai.sh` transcript in `DATA_NOTES.md` | TRUE — verified on device |
| G3 | Schema verified: 64 columns, semicolon-delimited, 4 label columns | `verify_hai.py` output | FALSE — script not written |
| G4 | Training cleanliness measured per file, not assumed | `verify_hai.py` output showing train1 = 0, train2 = 776 | FALSE — not yet run on device |
| G5 | Primary label frozen to `attack`, with spec citation and OR-identity check | `FROZEN.md` + `verify_hai.py` | FALSE |
| G6 | Split frozen: `train1`, contiguous 60/40, no shuffling | `FROZEN.md` | FALSE |
| G7 | Detector hyperparameters frozen: bins, lambda, alpha, warm-up, seed | `FROZEN.md` | FALSE |
| G8 | Sweep grid enumerated as a finite set | `FROZEN.md` | FALSE |
| G9 | eTaPR implementation agrees with the published one on a fixture computed before any HAI score exists | `etapr_agreement.txt` | FALSE |
| G10 | eTaPR parameters frozen at published defaults | `FROZEN.md` | FALSE |
| G11 | P0b restated and passing in its three-part form | `fdia_control.py` output, exit 0 | FALSE — currently exits 1 |
| G12 | Amendments 3 and 4 committed and pushed | `git log`, `PREREG.md` | FALSE |
| G13 | No result-producing detector execution has occurred before the freeze | `git log` shows no detector script preceding G12 | TRUE — hold it |

G13 is the one that cannot be recovered once lost. Every other gate can be
satisfied late; G13 can only be preserved.

---

## 9. THE TWO QUESTIONS

**If this experiment says PASS, what would have to be true for that PASS to
mean something?**

That the detector was fit on genuinely attack-free data (`train1`, measured,
not assumed); that it was calibrated and evaluated on contiguous temporal
blocks so no near-duplicate second leaked across the split; that it beat its
own permuted labels at a configuration chosen before scoring, not the best of
a sweep; that the grid it was ranked over was enumerated in a commit that
predates the run; that the metric implementation agreed with the published one
on a fixture computed before any HAI score existed; and that every one of
those facts is reproducible from a cold clone by someone with no access to the
author's device.

**What observation would force the conclusion that the experiment failed to
establish its claim?**

`AP_true` inside the permutation null. Any P0b indicator mismatch under A1–A3.
A cold clone that cannot regenerate a published number. An eTaPR
disagreement that is not resolved. A grid that grew between the freeze commit
and the result commit. Or a P0a pass accompanied by a P0c failure — which
would say precisely that the detector is well calibrated and cannot detect
anything.

**Rejected on the "harder to falsify" test:** block permutation for P0c
(introduces a tunable block size into an anti-vacuity check), and registering
implementation constants as predictions (inflates the document without
constraining anything).

---

*Vincit Omnia Veritas.*
