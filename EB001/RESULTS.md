# EB-001: results — edge-bin clipping does not explain the P0a failure (2026-10-31)

**Who:** Claude (Anthropic, Opus 5.5), at Chad Holland's direction. Review level: direction only. **SELF-TESTED** in an x86_64 container (Python 3.13.18, NumPy 2.5.3), on HAI 20.07 `train1` (sha256 `376e8288…0844`, matching the pin). **NOT RUN** on the S25. The run is bound to clean commit `63d229a` by [run_manifest.json](run_manifest.json).

## What could have gone wrong, first

- **Not blind.** A container run while surveying Drive came before the registration ([PREREG.md](PREREG.md)). The in-repo run reproduces it line for line; only the data-load time differs, 4.3 s against 4.4 s.
- **The recovered script never ran as written.** It had a `SyntaxError` (an f-string split across two lines). Two print lines were changed and nothing else; see [fix.diff](fix.diff). So this is the first run of this diagnostic anywhere.
- **The decision rule is qualitative**, as registered. It is applied as written below, with no threshold added afterwards.
- **Only `train1` was read.** `test1` stays sealed, and no constant or file the protocol depends on was changed.

## Raw output (from [run.txt](run.txt))

```
step 1 - reproduction of p0a_result.json
  breach 0.042402  (registered [0.05, 0.2], published 0.042402)
  held-out mean 25.2869 sd 1.9876   calibration mean 25.1206 sd 2.6027
  reproduction CONSISTENT with published numbers

step 2 - edge-bin mass (fraction of ticks landing in bin 0 or bin 63, per channel)
  overall  calibration 0.323533   held-out 0.321962   delta -0.001571
  held-out channel-values outside the fit range [lo, hi]: 0.004443 mean over channels, max 0.116053
  ...
  ... 18 of 59 channels gain edge mass across the split boundary, 41 lose it

step 3 - interpretation aid
  SD ratio held-out/calibration: 0.7637 (published 0.764)
```

## Verdict under the registered rule

**Step 1 passed:** the diagnostic reproduces the published P0a numbers exactly, so its step 2 is admissible.

**The clipping hypothesis is REFUTED** by the rule written on 2026-09-08.
- The overall edge-bin mass **falls slightly** across the split (−0.001571).
- **41 of 59 channels lose edge mass.**
- That is neither "materially more" nor "broad-based and positive".

On average, 0.44% of held-out values fall outside the fit range.

**One channel moves a lot, and it is not clipping.** P4_ST_PS goes from 0.5698 to 1.0000 edge mass. A separate check (below) found that in the held-out slice it takes only two values, 0 and 50.4048. Both lie inside the fit range [0, 50.9871] and land in bins 0 and 63 because the channel sits at its extremes. Nothing is clipped.

```
P4_ST_PS distinct values   fit: 0, 49.0655, 49.7998, 50.9871   held-out: 0, 50.4048
```

(That check was run after the main result, with a short inline script over the same `train1` slice. It is not a registered measurement.)

## What this changes

- **Nothing in the protocol.** No fix is licensed, and `sentinel.py` keeps its bin construction.
- The variance collapse behind P0a (SD 2.6027 to 1.9876) **still has no explanation**. The external review's leading hypothesis is now ruled out.

## Open

- What does cause the variance collapse? Not registered yet.
- The same run on the S25.
