# REFERENCES AND ASSUMPTION SCOPE

Every registered assumption in `PREREG.md` that rests on prior work is
attached to its source here. Written before any HAI detector run.

Citation details marked VERIFIED were checked against the publisher record on
2026-09-03. Details marked UNVERIFIED are from recollection and must be
confirmed before any publication.

**Nothing in this repository claims novelty for any result cited below.**

---

## 1. A2 — WHAT IT ASSUMES, WHY, AND WHAT BREAKS WITHOUT IT

A2, registered in Amendment 2 and carried into `fdia_control_v2.py`:

> *The estimator is linear WLS with no bad-data rejection or measurement
> removal loop active during the test.*

### What A2 excludes

The classical bad-data procedure does not stop at a chi-square test on the
residual. It iterates: compute normalised residuals, identify the largest,
remove the corresponding measurement, re-estimate, repeat. A2 excludes that
loop and evaluates the chi-square test on a single estimation pass.

### Why the exclusion is necessary, not convenient

The invariance being tested is

    r = (I - H (H'WH)^-1 H'W) z = S z,     S H = 0,     so   S(z + Hc) = S z

`S` is fixed by `H` and `W`. An iterative largest-normalised-residual loop
**changes the measurement set between iterations**, which changes `H`, which
changes `S`. The identity `S H = 0` still holds for each new `H`, but the `H`
used to construct `a = Hc` is no longer the `H` the estimator is using — which
is A1, violated as a consequence of A2 being violated. A1 and A2 are therefore
not independent: relaxing A2 breaks A1.

### What remains valid inside the A2 boundary

Exactly this, and no more: **for a single-pass linear WLS estimator on a fixed
measurement set, an injection in the column space of `H` leaves the residual
vector unchanged to within the registered numerical tolerance, and therefore
leaves any residual-based detection verdict unchanged.**

It does **not** establish that such an injection is undetectable in general,
by any estimator, or in an operating utility.

### What would change if A2 were relaxed

Unknown, and deliberately not assumed. Measuring it is a candidate future
experiment: implement the iterative largest-normalised-residual loop, run the
same 200 structured injections, and report whether the indicator equality of
P0b-2 survives. Either outcome is informative. If invariance survives, A2 was
unnecessary and the assumption list is over-specified. **This is registered as
unrun, not claimed.**

### Source

- **UNVERIFIED CITATION DETAILS.** A. Abur and A. G. Expósito, *Power System
  State Estimation: Theory and Application*, Marcel Dekker, Inc., 2004. Cited
  as reference [4] of the IEEE Task Force paper below, which is where the
  title was confirmed. Note: an earlier draft of this repository's notes gave
  the title as "Theory and Implementation". That was wrong. **Not yet
  obtained; A2 above is documented from first principles and from the
  measurement in `fdia_control_v2.py`, not from this book.**

---

## 2. SCOPE LIMITATION — P0b COVERS STATIC ESTIMATION ONLY

Source, VERIFIED: IEEE Task Force on Power System Dynamic State and Parameter
Estimation (J. Zhao, chair; A. Gómez-Expósito, M. Netto, L. Mili, A. Abur,
V. Terzija, I. Kamwa, B. Pal, A. K. Singh, J. Qi, Z. Huang,
A. P. S. Meliopoulos), "Power System Dynamic State Estimation: Motivations,
Definitions, Methodologies and Future Work," *IEEE Transactions on Power
Systems*, 2019. DOI 10.1109/TPWRS.2019.2894769.

That paper places four estimator families in one framework: static state
estimation (SSE), tracking (TSE), forecasting-aided (FASE), and dynamic (DSE).
It characterises SSE as the case in which state-transition information is
fully ignored and only the measurement function is retained, so the estimator
has no memory of previous time steps.

**`fdia_control_v2.py` implements SSE. It is the bottom rung.**

Every family above SSE carries a state-transition model that predicts the
state independently of the current measurement. An injection `a = Hc` moves
the measurement but not the prediction, so the innovation is not obviously
invariant — the attack that is invisible to P0b may well be visible to a
tracking or Kalman-type estimator. The same paper notes that normalised
innovation vector tests are already used against observation outliers, and
cites work on DSE robustness against cyber attacks and unknown inputs.

**Registered as an unrun door, not a claim:** does `a = Hc` remain invisible
under an estimator with a state-transition model? Not tested here.

**Consequence for the repository's own language:** the phrase
"provably-undetectable FDIA control" is an overclaim and is to be replaced
with "residual-invariance control under the registered linear WLS model"
wherever it appears, including the GitHub repository description.

---

## 3. THE `a = Hc` CONSTRUCTION IS NOT OURS

VERIFIED:

- Y. Liu, P. Ning, and M. K. Reiter, "False Data Injection Attacks against
  State Estimation in Electric Power Grids," in *Proceedings of the 16th ACM
  Conference on Computer and Communications Security (CCS '09)*, ACM, New
  York, 2009, pp. 21–32. DOI 10.1145/1653662.1653666.
- Extended journal version: *ACM Transactions on Information and System
  Security (TISSEC)*, vol. 14, no. 1, Article 13, pp. 1–33, June 2011.
  DOI 10.1145/1952982.1952995.

**Correct framing for P0b:** it reimplements and experimentally tests the
established structured-FDIA construction under explicitly stated assumptions.
The mathematics is prior work. What this repository contributes is the
registered two-sided predicate around it — that the harness must show both
`0` detections on the structured set and `>= 190 of 200` on a matched
unstructured set — and the measurement that its first formulation was
ill-posed.

---

## 4. THE +1 CORRECTION IN P5

VERIFIED: B. Phipson and G. K. Smyth, "Permutation P-values Should Never Be
Zero: Calculating Exact P-values When Permutations Are Randomly Drawn,"
*Statistical Applications in Genetics and Molecular Biology*, vol. 9, no. 1,
Article 39, 2010. DOI 10.2202/1544-6115.1585. Preprint arXiv:1603.05766.
Published 31 October 2010; corrected 9 February 2011.

The paper's argument is that resampling should be treated as generating an
exact discrete null distribution rather than as estimating a tail probability,
and that the naive uncorrected p-value is understated by roughly `1/m`.

**Scope note, so the citation is not overstated.** Phipson and Smyth develop a
refined estimator for the case where resamples are randomly drawn. The
registered `P5_CORRECTION` is the simple conservative form

    p = (1 + #{ b : AP_b >= AP_obs }) / (B + 1)

which is the well-known valid-but-conservative special case, **not** their
full method. The registered form stays frozen. It is not to be changed because
a more refined convention exists.

---

## 5. EXCHANGEABILITY, AND WHY IT IS NOT ASSUMED

The condition a resampling test requires is exchangeability under the null,
not merely that labels were shuffled. This repository did not take that on
authority — it measured the consequence of getting it wrong.

Against a null detector with zero detection ability and contiguous attack
labels, `B = 200`, `alpha = 0.01`, 100 trials:

| Null detector | iid permutation | circular shift |
|---|---|---|
| iid noise, phi = 0.000 | 0/100 | 0/100 |
| mild autocorrelation, phi = 0.900 | 30/100 | 0/100 |
| smooth, phi = 0.999 | 47/100 | 1/100 |

A supporting textbook treatment would be **UNVERIFIED**: P. I. Good,
*Permutation, Parametric, and Bootstrap Tests of Hypotheses*, Springer. Not
obtained. The empirical result above stands on its own measurement and does
not depend on it.

**P5 is not described as distribution-free.** It is a Monte Carlo
randomization test whose validity rests on the circular-shift null preserving
the label structure that an iid permutation destroys.

---

## 6. CONFORMAL COVERAGE IN P3

UNVERIFIED CITATION DETAILS: A. N. Angelopoulos and S. Bates, "A Gentle
Introduction to Conformal Prediction and Distribution-Free Uncertainty
Quantification," arXiv:2107.07511. Not obtained; the arXiv identifier is from
recollection and must be confirmed.

Relevant to the registered `QUANTILE_CONVENTION` and to P3's coverage bound

    1 - alpha  <=  Coverage  <=  1 - alpha + 1/(n_cal + 1)

which holds **only under exchangeability of calibration and test scores**.
P3 predicts that this fails under drift, so the guarantee is what P3 stresses,
not what it assumes. The reference must not be cited as evidence that
conformal prediction remains valid under arbitrary distribution shift.

---

## 7. OT SECURITY VOCABULARY

VERIFIED: NIST Special Publication 800-82 Revision 3, *Guide to Operational
Technology (OT) Security*, September 2023. Supersedes Rev. 2 (2015). NIST has
issued a pre-draft call for a Revision 4; Rev. 3 remains current.
`csrc.nist.gov/pubs/sp/800/82/r3/final`

Cited for terminology and operational context only. It establishes nothing
about the statistics or the state-estimation mathematics in this repository,
and is not to be presented as if it did.

---

## 8. WHAT IS AND IS NOT THIS REPOSITORY'S CONTRIBUTION

**Not ours.** The `a = Hc` construction and residual invariance; WLS state
estimation and residual-based bad-data detection; conformal prediction;
permutation and randomization testing; the HAI benchmark; eTaPR; average
precision.

**Possibly ours, and unproven until the experiment runs.** The registered
verification protocol around those components: preregistered gates, frozen and
digest-sealed constants, two-sided anti-vacuity controls, sabotage testing of
the gates themselves, an independent metric implementation checked against a
fixture committed before it was written, and explicit statements of the
conditions under which a PASS means anything.

**Nothing is validated yet.** No HAI detector has run. The correct present
description is that a protocol has been registered and its instruments are
being tested — not that SENTINEL has been validated on HAI.

---

*Vincit Omnia Veritas.*
