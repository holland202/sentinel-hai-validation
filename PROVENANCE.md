# Provenance

## Identity

- **Repository**: holland202/sentinel-hai-validation
- **Canonical URL**: https://github.com/holland202/sentinel-hai-validation
- **Purpose**: Preregistered evaluation of anomaly detection on the HAI industrial control system benchmark. Emphasis on anti-vacuity gates, provenance checks, and retention of failures.
- **License**: MIT (see LICENSE.md). The HAI dataset itself is not redistributed and remains under its own CC BY 4.0 terms.

## Origin

Chad Holland initiated the work. The LICENSE.md copyright notice and repository history support this attribution.

## Contributions

See AUTHORS.md. All primary categories currently map to Chad Holland on the basis of repository history.

## Research Status Distinction

| Status        | Meaning in this repository                                      |
|---------------|-----------------------------------------------------------------|
| IMPLEMENTED   | Code, gates, and provenance tools exist and can be executed     |
| EXPERIMENTAL  | Experiments have been run under the registered conditions       |
| VERIFIED      | Not claimed; requires independent verification                  |
| REPRODUCED    | No independent external reproduction is recorded here           |
| REFUTED       | Specific registered predictions that failed are retained        |
| UNRESOLVED    | Several registered items remain unrun or suspended              |
| NOT TESTED    | Explicitly gated or out of scope                                |

“Implemented” or a passing gate must not be read as “scientifically validated attack detection.”

## Experimental Lineage

Key recorded outcomes (see README.md, PREREG.md, and associated JSON artifacts for details):

- SENTINEL P0a: FAILED (breach rate outside registered interval). Downstream attack-detection scoring remains VOID.
- VERA P7a: PASSED under amendment 5 (anti-vacuity gate cleared).
- VERA P7b, P7c: REFUTED.
- P0b (residual-invariance control): PASSES under the registered two-sided predicate.
- Multiple defects in the recommended eTaPR metric were characterized and retained.
- Several internal defects (order-dependent AP, non-failing gates, etc.) were discovered, corrected where appropriate, and left visible.

Detailed experiment fields appear in PREREG.md, frozen.py, gate_provenance.py, and the various result JSON files. A centralized machine-readable experiment registry is not yet present.

## Independent Reproduction

None recorded in this repository. The design intentionally makes cold-clone reproduction of the no-data provenance checks and the registered gates feasible.

## Refutation / Failure Record

Failures are first-class and retained:

- P0a failure and the subsequent correction of its explanatory story.
- Refuted predictions (P7b, P7c).
- Withdrawn or defective internal components kept for audit.
- eTaPR defects documented rather than silently worked around.

Original registrations, observed failures, and later amendments remain visible. Amendments are append-only by design (gate_provenance.py enforces this for the original registration).

## Corrections

Methodological corrections and amendments are recorded in PREREG.md and the commit history. Prior failing states are not erased.

## Scope of Evidence

This repository documents a preregistered evaluation methodology and the outcomes obtained under those registrations on the HAI benchmark (and related controls).

It does **not** establish:

- that any detector has successfully detected attacks on the held-out evaluation set (no detector has scored test1 under a cleared gate)
- general industrial-control or power-grid security claims
- performance on live SCADA/ICS telemetry
- independent scientific validation
- recursive self-improvement or any capability beyond the recorded experiments

A passing anti-vacuity gate licenses further evaluation; it does not itself constitute a detection result.

## Relationship to Other Repositories

This repository is an instrument focused on evaluation discipline. Cross-repository research-record functions belong in a separate operating layer.
