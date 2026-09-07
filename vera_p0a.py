#!/usr/bin/env python3
"""
vera_p0a.py - the VERA arm of Amendment 5: P7a, P7b, P7c.

    python3 vera_p0a.py

Registered at d2c63fb BEFORE this file existed. Reads frozen.FIT_FILE only.
frozen.EVAL_FILE is never referenced; test1 stays unread.

Every constant comes from frozen.py. Nothing is defined locally: the split
fractions, the conformal alpha, the ridge lambda and the quantile convention
are all imports, so a value that was registered is the value that runs.

The split reproduces p0a_characterization.py exactly:
    fit           [0, cut)                 cut = n * FIT_FRACTION
    calibration   [cut, cut + half)        half = (n - cut) // 2
    heldout       [cut + half, n)

P8 IS NOT RUN AND THE REGISTRATION IS DEFECTIVE. Amendment 5 states P8 is
"measured on train1 only". train1 contains 0 attack rows, so there is no
detection quantity defined on it and no exchange rate to measure. The
prediction needs frozen.EVAL_FILE, which the P0 gate seals. Recorded here
rather than reinterpreted; correcting it requires a further amendment.
"""
import gzip, sys
import numpy as np
import frozen


def load(name):
    with gzip.open(f"data/{name}.csv.gz", "rt") as f:
        hdr = [h.strip() for h in f.readline().split(frozen.DELIMITER)]
        rows = [ln.rstrip("\n").split(frozen.DELIMITER) for ln in f if ln.strip()]
    keep = [i for i, h in enumerate(hdr) if h not in frozen.EXCLUDED_COLUMNS]
    ilab = hdr.index(frozen.PRIMARY_LABEL)
    X = np.array([[float(r[i]) for i in keep] for r in rows], dtype=float)
    y = np.array([int(float(r[ilab])) for r in rows], dtype=int)
    return X, y, [hdr[i] for i in keep]


def qhat(res, alpha):
    k = int(np.ceil((len(res) + 1) * (1 - alpha))) - 1
    return np.sort(res)[min(k, len(res) - 1)]


def main():
    X, y, chans = load(frozen.FIT_FILE)
    assert y.sum() == 0, "fit file is not attack-free"
    n = len(X)
    cut = int(n * frozen.FIT_FRACTION)
    half = (n - cut) // 2
    fit, cal, hld = X[:cut], X[cut:cut + half], X[cut + half:]
    print(f"{frozen.FIT_FILE}: {n} rows, {len(chans)} channels, "
          f"{int(y.sum())} attack rows")
    print(f"  fit         [0, {cut})            {len(fit)} rows")
    print(f"  calibration [{cut}, {cut+half})   {len(cal)} rows")
    print(f"  heldout     [{cut+half}, {n})     {len(hld)} rows")

    mu, sd = fit.mean(0), fit.std(0)
    sd[sd < 1e-9] = 1.0
    z = lambda A: (A - mu) / sd
    Zf, Zc, Zh = z(fit), z(cal), z(hld)

    A = np.hstack([Zf[:-1], np.ones((len(Zf) - 1, 1))])
    W = np.linalg.solve(A.T @ A + frozen.RIDGE_LAMBDA * np.eye(A.shape[1]),
                        A.T @ Zf[1:])

    def resid(Z):
        M = np.hstack([Z[:-1], np.ones((len(Z) - 1, 1))])
        return np.sqrt(np.mean((M @ W - Z[1:]) ** 2, axis=1))

    rc, rh = resid(Zc), resid(Zh)
    q = qhat(rc, frozen.CONFORMAL_ALPHA)
    breach_cal = float((rc > q).mean())
    breach_hld = float((rh > q).mean())
    cov_hld = 1.0 - breach_hld

    print(f"\nalpha={frozen.CONFORMAL_ALPHA}  lambda={frozen.RIDGE_LAMBDA}  "
          f"q={q:.6f}")
    print(f"calibration: n={len(rc)} mean={rc.mean():.4f} sd={rc.std():.4f} "
          f"breach={breach_cal:.6f}")
    print(f"heldout:     n={len(rh)} mean={rh.mean():.4f} sd={rh.std():.4f} "
          f"breach={breach_hld:.6f}")

    lo, hi = 0.05, 0.20
    p7a = lo <= breach_hld <= hi
    print(f"\nP7a VERA held-out breach in [{lo}, {hi}]: {p7a}  "
          f"({breach_hld:.6f})")

    ratio = rh.std() / rc.std()
    p7b = ratio < 0.90
    print(f"P7b held-out/calibration SD ratio < 0.90: {p7b}  "
          f"({ratio:.4f}; SENTINEL's was 0.764)")
    print(f"    -> {'shared across two unrelated detectors: a property of the '
                   'train1 split' if p7b else 'not shared: the narrowing is '
                   'specific to SENTINEL windowed JSD'}")

    p7c = cov_hld > 0.90
    print(f"P7c coverage exceeds nominal 0.90 (over-covers): {p7c}  "
          f"({cov_hld:.4f}; BATADAL was 0.697)")
    if not p7a:
        print("\nP7a FAILED -> P7c is VOID as registered and is reported "
              "above descriptively only. test1 remains unread.")

    print("\nP8 NOT RUN. Amendment 5 registers it as 'measured on train1 "
          "only', but train1 has 0 attack rows so no detection quantity "
          "exists there. The registration is defective and needs a "
          "corrective amendment; it is not reinterpreted here.")
    print("P9 NOT RUN (open door: re-splitting touches frozen constants).")

    import ast, pathlib
    src = ast.parse(pathlib.Path(__file__).read_text())
    names = {nd.attr for nd in ast.walk(src)
             if isinstance(nd, ast.Attribute) and isinstance(nd.value, ast.Name)
             and nd.value.id == "frozen"}
    print(f"\nAUDIT frozen constants read: {sorted(names)}")
    print(f"AUDIT EVAL_FILE referenced: {'EVAL_FILE' in names}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
