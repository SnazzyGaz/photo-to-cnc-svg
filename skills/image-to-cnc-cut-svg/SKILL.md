---
name: image-to-cnc-cut-svg
description: >-
  Use when an image (photo, line art, logo, or a stage-1 B/W artwork PNG) needs
  to become an SVG ready for CNC cutting or carving; asks finished size, style,
  bits and CAM software, then outputs the SVG.
---
# Image to CNC cut SVG

This file is the single source for trace settings, commands, defaults and CAM notes; the other skills, `AGENTS.md` and the README point here. The tracing script is `scripts/cnc_vector.py` in the photo-to-cnc-svg repo (modes: vcarve, pocket, engrave, profile; run `--help` for all flags). Paths are relative to the repo root.

## Defaults
Use these unless the person gives specs:

| Setting | Default |
|---|---|
| Style | V-carve |
| Width | 300 mm |
| V-bit | 60° |
| Depth | 3 mm V-carve / 6 pocket / 1 engrave / stock thickness profile |
| End mill (clearance / pocket) | 3.175 mm (1/8") |
| Feeds | 1200 feed / 300 plunge / 3000 rapid mm/min |

## 1. Ask (one question, only what's missing)
If the person wants to choose rather than take the defaults:
- Finished size: width in mm.
- Style: V-carve (recommended for line art/portraits), pocket, single-line engrave, profile cut-out.
- Bits: V-bit angle (30/60/90°) plus end mill diameter.
- CAM software: Vectric (VCarve/Aspire), Carbide Create, Easel, Fusion 360, other.

## 2. Build
1. `pip install -r requirements.txt` (numpy, scipy, opencv-python-headless, scikit-image, potracer; no system libraries needed). For output identical to the examples use `requirements-lock.txt`.
2. Put the image in a working directory, e.g. `work/<subject>/` (git-ignored).
3. Settings by source:
   - Clean B/W art (e.g. stage-1 artwork): `--threshold 128 --smooth 0.8 --min-feature 0.5`. Use `--min-feature 0.8` for a bold stencil (option A) or a 90° bit (0.8 to 1.0).
   - Art drawn white on black (light parts are the carve): add `--invert`.
   - Photo: defaults (`--threshold auto --smooth 2`), plus `--crop x0,y0,x1,y1` and `--isolate` to cut the subject out.
4. Run (V-carve, generated art, defaults):
   ```
   python3 scripts/cnc_vector.py art.png -o <subject>_vcarve_300mm.svg --mode vcarve --width-mm 300 \
     --vbit-angle 60 --depth 3 --threshold 128 --smooth 0.8 --min-feature 0.5 > stats.json
   ```
   The JSON on stdout holds size, path count and the time estimate. Other modes: `--mode pocket --tool-dia 6 [--levels 3]`, `--mode engrave`, `--mode profile --crop ... --isolate --use-isolation-as-mask --single`. `--border <mm>` adds a rectangular profile frame.

## 3. Preview
```
python3 scripts/preview.py <subject>_vcarve_300mm.svg preview.png
```
(or add `--preview preview.png` to the trace; same renderer). Black is carved, white stays; a `--border` frame shows as a grey outline. Look at it next to the artwork: speckled, raise `--min-feature`; detail lost, lower it. 1 to 3 tries.

## 4. Deliver
Name `<subject>_<mode>_<width>mm.svg` (`<subject>-stencil_...` for option A); deliver SVG plus preview. Short summary:
- size (mm), mode, path count
- time estimate from `stats.json` with range and assumed feeds (estimate only; CAM simulation is authoritative)
- if `notes` says flat areas hit max depth: those are wider than the V-bit spans at full depth (3.5 mm for 60° at 3 mm), so use flat-depth V-carving with a clearance end mill
- the CAM import tip for their program:
  - **Vectric (VCarve / Aspire):** import 1:1 in mm, select all, V-Carve toolpath with the V-bit; tick flat depth and add the end mill as clearance tool for wide areas.
  - **Carbide Create:** import the SVG, check the size, Advanced V-carve with the end mill as the pocket tool. Advanced V-carve is in the free version, but free (Core) only exports G-code for Carbide 3D machines; other machines need Pro.
  - **Easel:** import the SVG and check the width (it can mis-scale). V-carving needs Easel Pro; on the free plan, fill-cut/pocket with an end mill or use other CAM for the V-carve.
  - **Fusion 360:** insert the SVG onto a sketch, verify scale, then an Engrave (V-bit) or 2D Pocket toolpath.
Keep the reply short.
