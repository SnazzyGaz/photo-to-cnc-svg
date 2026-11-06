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

**Option B: mid-ground engraving.** Two generations, sometimes three:
1. Faithful engraving pass from the photo only: woodcut / engraved-illustration interpretation of the exact subject, same pose and framing, tightly cropped, keeping defining items on the subject (e.g. a bridle, a collar) unless the brief says otherwise. Directional hatching following muscle and hair flow, dense blacks in shadows, open white on lit planes. Name defining features explicitly.
2. Moderate refinement with pass 1 plus the photo as references: keep pose, anatomy, props and most hatching, but turn grey or stippled tones into clean black strokes, make strokes slightly thicker, deepen the darkest shadows into some solid black, add a clear contour on the outer edge. Not a full bold linocut: it should sit between a fine engraving and a bold linocut.
3. Only if pass 2 barely changed pass 1 (common; the model copies the reference closely): run a pass with only the pass-2 image as reference asking to "convert to a bold linocut relief print" with chunky gouge marks, same pose and features: solid black masses with a few thick white cuts, fewer strokes, minimum line width like a 2-3 mm gouge cut, nothing hair-thin, no texture or dots. Use that as option B.

Prompt rules for both: pure black on pure white only, no grey, gradients, speckles, text or background, crisp edges, high resolution. Full prompt templates are in the repo README.

## 3. Trace the chosen one
Follow `skills/image-to-cnc-cut-svg/SKILL.md` sections 2 and 3: its defaults (unless the person gives specs), the "clean B/W art" settings, the trace command and the preview check. Don't ask for specs unless the person wants to choose.

## 4. Deliver
As in `image-to-cnc-cut-svg` section 4: the SVG, the preview and the short note with its CAM import tip.
