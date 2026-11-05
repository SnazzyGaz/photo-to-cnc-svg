---
name: image-to-cnc-cut-svg
description: >-
  Use when an image (photo, line art, logo, or a stage-1 B/W artwork PNG) needs
  to become an SVG ready for CNC cutting or carving; asks finished size, style,
  bits and CAM software, then outputs the SVG.
---
# Image to CNC cut SVG

The tracing script is `scripts/cnc_vector.py` in the photo-to-cnc-svg repo (modes: vcarve, pocket, engrave, profile; run `--help` for all flags).

## 1. Ask (one question, only what's missing)
- Finished size: width in mm. Required.
- Style: V-carve (recommended for line art/portraits), pocket, single-line engrave, profile cut-out.
- Bits: V-bit angle (30/60/90°) plus end mill diameter (default 3.175 mm).
- CAM software: Vectric (VCarve/Aspire), Carbide Create, Easel, Fusion 360, other.

Defaults: depth 3 mm V-carve / 6 pocket / 1 engrave / stock thickness profile; feeds 1200/300/3000 mm/min.

## 2. Build
1. `pip install -r requirements.txt` (numpy scipy opencv-python-headless scikit-image potracer cairosvg)
2. Put the image in a working directory.
3. Settings by source:
   - Clean B/W line art or stencil (e.g. stage-1 artwork): `--threshold 128 --smooth 0.8 --min-feature 0.5` (0.8 to 1.0 for a 90° bit).
   - Photo: defaults (`--threshold auto --smooth 2`), add `--crop`/`--isolate` if needed.
4. Run, e.g. `python3 scripts/cnc_vector.py in.png -o out.svg --mode vcarve --width-mm 300 --vbit-angle 60 --depth 3 <settings> > stats.json` (the JSON on stdout holds path count and time estimate)
   Other modes: `--mode pocket --tool-dia 6 [--levels 3]`, `--mode engrave`, `--mode profile --isolate --use-isolation-as-mask --single`.

## 3. Preview correctly
The built-in `--preview` fills each path separately, so holes show solid. Use the even-odd merged preview instead:
```
python3 scripts/preview.py out.svg preview.png --width 1600
```
Look at the preview next to the original. Too speckled: raise `--min-feature`; lost detail: lower it. 1 to 3 iterations.

## 4. Deliver
Name `<subject>_<mode>_<width>mm.svg`; deliver SVG plus preview. Short summary:
- size (mm), mode, path count
- time estimate from the script's JSON with range and assumed feeds (estimate only; CAM simulation is authoritative)
- wide areas needing a clearance end mill (from `notes`)
- CAM notes:
  - Vectric: import 1:1 mm, select all, V-Carve toolpath; flat depth plus clearance tool for wide areas.
  - Carbide Create: import SVG, check size, Advanced V-carve with end mill as pocket tool (free version does this, but only exports G-code for Carbide 3D machines; other machines need Pro).
  - Easel: import SVG, check width (can mis-scale). V-carve needs Easel Pro; on the free plan, fill cut/pocket with an end mill or use other CAM.
  - Fusion 360: insert SVG on a sketch, verify scale, Engrave or 2D pocket toolpath.
Keep the reply short.
