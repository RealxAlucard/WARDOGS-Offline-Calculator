#!/usr/bin/env python3
"""
Offline-port patches for the WARDOGS Artillery Calculator build output.

Usage:  python3 offline_patch.py <path-to-upstream-dist>

Run after the upstream build (node scripts/build-pages.mjs && node scripts/sync-locales.mjs
&& node scripts/version-assets.mjs). Idempotent. It
  1. points every map at LOCAL tile folders (maps/tiles/<id>, maps/tiles-color/<id>),
  2. removes every network dependency (asset gateway, live lobbies, terrain-correction data,
     CDN preconnect hints),
  3. deletes the standalone mobile site and the desktop->mobile redirect.
"""
import json, re, sys
from pathlib import Path

dist = Path(sys.argv[1]).resolve()
rw = lambda p: json.loads(p.read_text(encoding="utf-8"))
def wj(p, d): p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# 1. local tiles for every map -------------------------------------------------------------
for m in ("bakurani", "ozeti", "zestafona"):
    p = dist / "maps" / f"{m}.json"; d = rw(p); t = d["tiles"]
    t["path"] = f"maps/tiles/{m}"
    t["styles"]["grayscale"]["path"] = f"maps/tiles/{m}"
    t["styles"]["color"]["path"] = f"maps/tiles-color/{m}"
    wj(p, d)

# 2. no network ------------------------------------------------------------------------------
p = dist / "data/ballistics/terrain-context.json"; d = rw(p)
local = lambda m: f"data/terrain/{m}/manifest.json"
d["terrainManifest"] = local(d.get("mapId", "bakurani"))
for m, v in d.get("terrainMaps", {}).items():
    v["terrainManifest"] = local(m)
d["experimentalCorrection"]["available"] = False
wj(p, d)

p = dist / "config/app.json"; d = rw(p)
d["assetGateway"]["enabled"] = False
d["assetGateway"]["origin"] = d["assetGateway"]["directOrigin"] = "http://localhost"
d["collab"]["enabled"] = False
d["feedback"]["enabled"] = False
wj(p, d)

html = list(dist.rglob("*.html"))
for f in html:
    s = f.read_text(encoding="utf-8")
    s2 = re.sub(r'<link[^>]*assets\.wardogs-artillery\.com[^>]*>\r?\n?', "", s)
    # analytics script (third-party) - drop any line that loads it
    s2 = "\n".join(l for l in s2.split("\n") if "cloud.umami.is" not in l)
    # 3. mobile site + redirect --------------------------------------------------------------
    s2 = re.sub(r'<script[^>]*mobile-redirect\.js[^>]*></script>\r?\n?', "", s2)
    s2 = re.sub(r'<link[^>]*max-width: 900px[^>]*rel="alternate"[^>]*/?>\r?\n?', "", s2)
    s2 = re.sub(r'<link[^>]*rel="alternate"[^>]*max-width: 900px[^>]*/?>\r?\n?', "", s2)
    if s2 != s:
        f.write_text(s2, encoding="utf-8")

import shutil
shutil.rmtree(dist / "mobile", ignore_errors=True)
for rel in ("js/mobile.bundle.js", "mobile.css", "js/core/mobile-redirect.js"):
    (dist / rel).unlink(missing_ok=True)
for rel in ("sitemap.xml", "robots.txt", "CNAME"):   # website-only files
    (dist / rel).unlink(missing_ok=True)

# sanity: nothing may still reference what was removed ---------------------------------------
bad = []
for f in list(dist.rglob("*.html")) + list(dist.rglob("*.css")):   # (js only keeps a harmless CSS selector that mentions the old file name)
    s = f.read_text(encoding="utf-8", errors="ignore")
    for needle in ("mobile.bundle.js", "mobile-redirect.js", "mobile.css"):
        if needle in s:
            bad.append((str(f.relative_to(dist)), needle))
print("leftover references to removed mobile files:", bad if bad else "none")
