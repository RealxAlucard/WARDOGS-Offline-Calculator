"""
Zestafona tile builder v3  (adds a correction step)

HOW THE CORRECTION WORKS
  1. Your 3+ CALIB_POINTS (same ones as before) place the scan on the map.
  2. CORRECTIONS then nudges the result. Each entry is a pair:
        ((X the app currently shows, Y the app currently shows),
         (X it SHOULD be,            Y it SHOULD be))
     1 pair  -> shifts the whole map
     2 pairs -> shifts + rotates + scales evenly
     3+ pairs-> full stretch/skew/rotate fit (best; use points far apart)
  Every time you rebuild, measure a landmark in your NEW build vs. the game
  and add the pair. Keep CALIB_POINTS as your ORIGINAL points and keep the
  ORIGINAL pairs too (only add new ones measured against the ORIGINAL build
  -- see notes at the bottom).
"""
import os, sys, math
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

# ============ EDIT THIS SECTION ============
SOURCE_IMAGE = r"C:\path\to\your_scan.png"
OUTPUT_DIR   = r"C:\path\to\output_tiles"

# Your ORIGINAL calibration points, copied from your old script:
# ((pixel_x, pixel_y), (game_x, game_y))
CALIB_POINTS = [
    ((0, 0), (0.0, 0.0)),      # <-- replace with your real point 1
    ((0, 0), (0.0, 0.0)),      # <-- replace with your real point 2
    ((0, 0), (0.0, 0.0)),      # <-- replace with your real point 3
]

# ((shown_x, shown_y), (true_x, true_y))
CORRECTIONS = [
    ((97.34, 77.87), (96.44, 78.69)),
]

MAX_ZOOM = 7
# ===========================================

BOUNDS = dict(minX=-0.03, maxX=163.81, minY=-0.01, maxY=163.83)  # tileBounds (square)
TS = 256
FILL = (0, 0, 0)

def fit_affine(pairs):
    """pairs of (src, dst) -> A (2x2), t (2,) with dst = A@src + t"""
    n = len(pairs)
    S = np.array([p[0] for p in pairs], float)
    D = np.array([p[1] for p in pairs], float)
    M = np.hstack([S, np.ones((n, 1))])
    sol, *_ = np.linalg.lstsq(M, D, rcond=None)   # 3x2
    A = sol[:2].T; t = sol[2]
    res = D - (S @ A.T + t)
    return A, t, res

def fit_correction(pairs):
    n = len(pairs)
    if n == 0:
        return np.eye(2), np.zeros(2)
    if n == 1:
        (m, r) = pairs[0]
        return np.eye(2), np.array(r, float) - np.array(m, float)
    if n == 2:
        m1, r1 = complex(*pairs[0][0]), complex(*pairs[0][1])
        m2, r2 = complex(*pairs[1][0]), complex(*pairs[1][1])
        a = (r1 - r2) / (m1 - m2); b = r1 - a * m1
        return np.array([[a.real, -a.imag], [a.imag, a.real]]), np.array([b.real, b.imag])
    A, t, res = fit_affine(pairs)
    print("Correction fit residuals (game units):"); print(np.round(res, 3))
    return A, t

def main():
    if len(CALIB_POINTS) < 3:
        sys.exit("Need at least 3 calibration points")
    A0, t0, res = fit_affine(CALIB_POINTS)      # pixel -> game (as your old build)
    print("Calibration residuals (game units, should be tiny):"); print(np.round(res, 3))
    Ac, tc = fit_correction(CORRECTIONS)
    A = Ac @ A0; t = Ac @ t0 + tc               # pixel -> corrected game
    Ainv = np.linalg.inv(A)

    W = BOUNDS["maxX"] - BOUNDS["minX"]; H = BOUNDS["maxY"] - BOUNDS["minY"]
    src = Image.open(SOURCE_IMAGE).convert("RGB")
    sw, sh = src.size
    print("Source:", sw, "x", sh)

    Z = MAX_ZOOM; N = 2 ** Z
    zdir = os.path.join(OUTPUT_DIR, f"zoom_{Z}"); os.makedirs(zdir, exist_ok=True)
    G = np.array([[W / (N * TS), 0], [0, -H / (N * TS)]])
    L = Ainv @ G                                   # tile px -> source px (linear part)
    scale = float(np.hypot(*L[:, 0]))              # source px per tile px
    k = max(1, int(scale))                         # integer pre-reduce factor
    print(f"Source px per tile px: {scale:.2f}  (pre-reduce x{k})")
    reduced_cache = None
    if k > 1:
        print("Pre-reducing source (one time)...")
        src = src.reduce(k); sw, sh = src.size
    for ty in range(N):
        for tx in range(N):
            g0 = np.array([BOUNDS["minX"] + tx / N * W, BOUNDS["maxY"] - ty / N * H])
            c = (Ainv @ (g0 - t)) / k
            Lk = L / k
            corners = [c + Lk @ np.array(uv) for uv in [(0, 0), (TS, 0), (0, TS), (TS, TS)]]
            xs = [p[0] for p in corners]; ys = [p[1] for p in corners]
            x0, x1 = int(math.floor(min(xs))) - 3, int(math.ceil(max(xs))) + 3
            y0, y1 = int(math.floor(min(ys))) - 3, int(math.ceil(max(ys))) + 3
            if x1 < 0 or y1 < 0 or x0 > sw or y0 > sh:
                tile = Image.new("RGB", (TS, TS), FILL)
            else:
                region = src.crop((x0, y0, x1, y1))
                data = (Lk[0, 0], Lk[0, 1], c[0] - x0, Lk[1, 0], Lk[1, 1], c[1] - y0)
                tile = region.transform((TS, TS), Image.AFFINE, data, resample=Image.BICUBIC, fillcolor=FILL)
            tile.save(os.path.join(zdir, f"{tx}_{ty}.webp"), "WEBP", quality=92)
        print(f"zoom {Z}: row {ty + 1}/{N}", end="\r")
    print()
    for z in range(Z - 1, -1, -1):
        n = 2 ** z; d = os.path.join(OUTPUT_DIR, f"zoom_{z}"); os.makedirs(d, exist_ok=True)
        cd = os.path.join(OUTPUT_DIR, f"zoom_{z + 1}")
        for ty in range(n):
            for tx in range(n):
                big = Image.new("RGB", (TS * 2, TS * 2), FILL)
                for dx in (0, 1):
                    for dy in (0, 1):
                        big.paste(Image.open(os.path.join(cd, f"{tx * 2 + dx}_{ty * 2 + dy}.webp")), (dx * TS, dy * TS))
                big.resize((TS, TS), Image.LANCZOS).save(os.path.join(d, f"{tx}_{ty}.webp"), "WEBP", quality=92)
        print("built zoom", z)
    print("DONE ->", OUTPUT_DIR)

if __name__ == "__main__":
    main()
