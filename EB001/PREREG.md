# EB-001: registration — does edge-bin clipping explain the P0a failure?

**Registered:** 2026-10-31, before the diagnostic was committed to this repository or run inside it.
**Author:** Claude (Anthropic, Opus 5.5), at Chad Holland's direction. Review level: direction only.
**Status at registration:** nothing run in this repository. `sentinel.py`, `frozen.py`, `PREREG.md` and every constant are untouched, and `test1` is not read.

## What could have gone wrong, first (disclosed before the run)

- **Not blind.** On 2026-10-31, while surveying Chad's Google Drive for unpublished work, Claude ran this diagnostic once in a container on HAI 20.07 `train1`. The pinned sha256 matched. Claude has seen the outcome. This file records the question and the decision rule as they were written on **2026-09-08**, in the diagnostic's own docstring, before any run of it. The rule is not reworded or tightened now that the answer is known.
- **The rule is qualitative.** "Broad-based and positive" versus "flat" is not a numeric threshold. The results will report the numbers and apply the rule as written, and they will not invent a threshold afterwards.
- **The recovered script did not run.** `edge_bin_diagnostic.original.py.txt` (sha256 `394cdfa0b7bead915feac34c3c98dc559d2b2065261f70507e480a3e41c84d3f`, from Drive, dated 2026-09-08) contains an f-string split across two lines, which is a `SyntaxError`. It is kept as received, with a `.txt` extension so nothing imports it. The runnable copy, `edge_bin_diagnostic.py` at the repository root, differs in those two lines only. They now compute the same printed message on a separate line, and no measurement changes. The diff will be in the results.

## The question

P0a failed: breach 0.042402 against the registered [0.05, 0.2]. On the held-out slice the score's mean rises (25.2869 vs 25.1206) while its SD falls (1.9876 vs 2.6027).

An external review of `sentinel.py` raised a hypothesis. Bin edges come from the fit split's min/max, and held-out values outside that range are clipped into the edge bins. That would compress window histograms toward the reference and shrink the variance. If true, the P0a failure is a bin-construction defect in the instrument, not a property of the data.

## Procedure (as in the script)

1. Reproduce the published P0a numbers first. If they do not reproduce, the diagnostic is VOID.
2. Compare, per channel, the fraction of ticks that land in bin 0 or bin 63, between the calibration slice and the held-out slice.

## Decision rule (verbatim from the 2026-09-08 docstring)

> If held-out ticks pile into edge bins materially more than calibration ticks, the P0a failure is an instrument defect (bin construction) … If edge mass is flat across the split, the hypothesis is REFUTED and the variance collapse lives elsewhere.

and from its printed interpretation aid:

> If delta is broad-based and positive, clipping is compressing tails on most channels at once … If delta is flat, the hypothesis is REFUTED.

## What a result licenses

- **Supported:** a fix is an amendment-scale decision. New edge construction would be registered before any run, and the split re-scored under both constructions.
- **Refuted:** no change to anything. The variance collapse needs another explanation, and that question stays open.

## Left unrun

The same diagnostic on the S25, and any proposal for what else causes the variance collapse.
