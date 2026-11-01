---
name: photo-to-cnc-svg
description: >-
  Use when someone sends a photo (plus an optional short brief) and wants it
  turned into CNC-carvable art: offers two black-and-white style options, then
  traces the chosen one into a CNC-ready SVG.
---
# Photo to CNC SVG (end-to-end)

Combines `cnc-graphic-artwork-generator` (stage 1, artwork) and `image-to-cnc-cut-svg` (stage 2, tracing). Load both for full detail; this is the flow. Paths are relative to the root of the photo-to-cnc-svg repo.

## 1. Intake
- Take the photo and the brief (what subject or region, anything to keep or remove such as tack, collars, background people). Don't interrogate: if the subject is obvious, go.
- Copy the photo into a working folder, e.g. `work/<subject>/`.

## 2. Make two options (image generation, photo as reference)
Generate both, then show them side by side and ask which to trace (A, B, or tweak).

**Option A: simplified stencil.** Bold, clean graphic: large solid black shapes and white negative space, smooth contours, few internal lines, hair/fur/feathers as a handful of bold locks. Fast to carve. Watch that it stays recognisably *this* subject (markings, ear shape, muzzle) and doesn't drift into generic clip art; name those features in the prompt.

**Option B: mid-ground engraving.** Two generations:
1. Faithful engraving pass from the photo only: woodcut / engraved-illustration interpretation of the exact subject, same pose and framing, tightly cropped, keeping defining items on the subject (e.g. a bridle, a collar) unless the brief says otherwise. Directional hatching following muscle and hair flow, dense blacks in shadows, open white on lit planes. Name defining features explicitly.
2. Moderate refinement with pass 1 plus the photo as references: keep pose, anatomy, props and most hatching, but turn grey or stippled tones into clean black strokes, make strokes slightly thicker, deepen the darkest shadows into some solid black, add a clear contour on the outer edge. Not a full bold linocut: it should sit between a fine engraving and a bold linocut.

Prompt rules for both: pure black on pure white only, no grey, gradients, speckles, text or background, crisp edges, high resolution. Full prompt templates are in the repo README.

## 3. Trace the chosen one
- Unless the person gives specs, use defaults: V-carve, 300 mm wide, 60° V-bit, 3 mm depth, end mill 3.175 mm, feeds 1200/300/3000 mm/min. If they want to choose, ask width, style, bit and CAM program in one question.
- `pip install -r requirements.txt`
- Run, for generated B/W art:
  `python3 scripts/cnc_vector.py art.png -o <subject>_vcarve_300mm.svg --mode vcarve --width-mm 300 --vbit-angle 60 --depth 3 --threshold 128 --smooth 0.8 --min-feature 0.5 > stats.json`
  (Option A can take `--min-feature 0.8`; a 90° bit wants 0.8 to 1.0.)
- Render the true-to-cut preview: `python3 scripts/preview.py <subject>_vcarve_300mm.svg preview.png`. Look at it next to the artwork; adjust `--min-feature` if speckled (raise) or detail is lost (lower). 1 to 3 tries.

## 4. Deliver
Send the SVG plus the preview image, with a short note: size, mode, path count, the time estimate range from `stats.json` (rough; CAM simulation is authoritative), whether wide areas need a clearance end mill, and the one-line import tip for their CAM program (from `image-to-cnc-cut-svg`).
