# Provenance

## Identity

- **Repository**: holland202/sentinel-hai-validation
- **Canonical URL**: https://github.com/holland202/sentinel-hai-validation
- **Purpose**: Preregistered evaluation of anomaly detection methods on the HAI industrial control system benchmark, with emphasis on anti-vacuity gates, provenance, and explicit failure recording.
- **License**: MIT (see LICENSE.md)

## Origin

Initiated by Chad Holland. The first commit contains the preregistration document and establishes the append-only amendment discipline.

## Contributions

See `AUTHORS.md` for category-level attribution. All primary categories currently map to Chad Holland on the basis of repository history.

## Research Status Distinction

| Status | Meaning in this repository |
|--------|----------------------------|
| IMPLEMENTED | Code, freezes, and evaluation scripts exist |
| EXPERIMENTAL | Results obtained under preregistered conditions |
| VERIFIED | Not claimed for external independent verification |
| REPRODUCED | No independent third-party reproductions recorded |
| REFUTED | Explicitly recorded failures retained |
| UNRESOLVED / VOID | Claims that cannot be interpreted or were voided by design |
| NOT TESTED | Registered but not yet executed items |

**Implemented does not mean scientifically validated.**  
A passing gate licenses access to the next evaluation stage; it does not automatically prove a final claim.

## Experimental Lineage (selected)

### SENTINEL — P0a

- **Experiment ID**: P0a (SENTINEL)
- **Status**: REFUTED / FAILED
- **Result**: Breach rate 0.042402 on held-out clean ticks; outside registered interval [0.05, 0.2] at alpha = 0.10 → FAIL
- **Consequence**: P1 and P3 VOID (cannot interpret attack-detection measurements)
- **Notes**: Subsequent characterization showed the original explanatory story (systematically lower scores) was itself incorrect; variance change is the observed pattern. Original failure claim retained.

### VERA — P7a / P7b / P7c

- **P7a**: PASS (held-out breach in registered interval)
- **P7b**: REFUTED
- **P7c**: REFUTED (noted as not fully blind; dependence stated in amendment)
- **Status**: Mixed; first anti-vacuity gate cleared for VERA under amendment 5

### P0b (residual-invariance control)

- **Status**: PASS under registered two-sided predicate
- **Notes**: Construction draws on prior literature (Liu, Ning & Reiter). What is registered here is the two-sided predicate.

### Other registered items

- P2: suspended
- P4, P6, P10, P11: registered, not all executed; see README and PREREG.md

## Independent Reproduction

No independent third-party reproduction records are present in this repository.

Cold-clone reproducibility boundary is defined; CI runs no-data provenance and freeze checks.

## Refutation / Failure Record

Failures and voids are first-class and retained:

- SENTINEL P0a FAIL → downstream VOID
- VERA P7b, P7c REFUTED
- Multiple self-discovered defects (order-dependent AP, non-failing gate designs, etc.) retained or withdrawn with record
- eTaPR metric defects documented with reproducible cases; no silent patch claimed

## Corrections

Amendments are append-only. Original preregistration text is protected by `gate_provenance.py`. Methodological corrections appear as numbered amendments rather than history rewriting.

## Scope of Evidence

This repository documents a preregistered evaluation methodology and specific experimental outcomes on the HAI benchmark (and related controls).

It does **not** establish:

- that any detector is ready for operational deployment
- generalization to real utility power grids
- recursive self-improvement or autonomous discovery
- that a passing gate equals a final scientific claim

HAI is one simulated testbed. Successful gate passage licenses further measurement; it does not by itself prove detection performance on attack data that has not been scored under the protocol.
