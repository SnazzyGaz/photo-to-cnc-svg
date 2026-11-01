---
name: cnc-graphic-artwork-generator
description: >-
  Use when an uploaded photo needs turning into a crisp black-and-white graphic
  PNG (stencil/linocut style) for later SVG tracing and CNC carving. Stage 1 of
  the image-to-CNC pipeline; stage 2 is image-to-cnc-cut-svg.
---
# CNC Graphic Artwork Generator

## Role
Turn uploaded photographs into crisp, high-contrast black-and-white graphic artwork suitable for later SVG tracing and CNC carving. Use an image-generation model that accepts a reference image (with the source photo as reference) to produce the artwork. The deliverable at this stage is a clean PNG, not an SVG.

## Proven approach (two passes)
A single "simple stencil" prompt drifts into a generic clip-art logo and loses the subject's identity. What works:
1. **Faithful engraving pass.** Reference the photo only. Ask for a black-and-white woodcut / engraved-illustration interpretation of *this exact* subject, same pose and framing as the photo, tightly cropped to the subject. Keep things physically on the subject that define the shot (e.g. a bridle, collar, glasses or hat) unless told to remove them. Name the defining features explicitly (ear shape, forelock, eye, nostril, mouth, markings). Render form with directional hatching that follows muscle and hair flow, dense blacks in shadows, open white on lit planes.
2. **Bolden pass.** Feed pass 1 (plus the photo) back as reference and ask for a bolder linocut / scratchboard print: same pose, anatomy and props, but replace fine pencil-like hatching and grey stippling with fewer, thicker carved strokes; merge shadows into large solid black masses; keep lit planes mostly clean white; no strokes thinner than a bold pen line, no dots, no grey.
Pass 2 is usually the one to trace. Show the user both if pass 1 has detail they might prefer.

## Workflow
1. Inspect the uploaded image and identify the intended subject or region.
2. Isolate the subject, removing the surrounding background.
3. Enlarge or reframe the requested feature when necessary, such as only a person's face or an animal's head.
4. Generate using the two passes above.
5. Check for visual artefacts and unnecessary detail before returning the result.
If the instructions are clear, generate immediately without unnecessary questions.

## Visual style
Bold, professional, monochrome artwork: engraved illustration / woodcut / linocut / scratchboard, with clean vector-graphic edges. Solid black shapes, pure white negative space, crisp edges, deliberate internal detail. No grey shading, gradients, photographic backgrounds, simulated lighting, text or decorative extras unless requested.

## Source fidelity
Use the uploaded image as the primary reference, but don't trace it mechanically. Simplification and interpretation are welcome. Preserve defining characteristics, proportions, pose, expression, silhouette and distinctive markings. It should look like a polished graphic version of the actual subject, not a generic replacement or redesign. Don't invent anatomy, change facial structure, exaggerate features or add decorative elements that weren't there.

## CNC-aware detail
Think about how it will be traced into SVG paths and machined. Avoid: random speckles and isolated fragments; excessive tiny feather, fur or hair marks; noisy photographic texture; jagged, broken or ambiguous contours; unnecessary outlines and redundant internal details; tiny decorative shapes that add little to recognition. Prefer clean, intentional shapes, controlled texture, clear negative spaces and smooth contours. Keep enough detail to stay distinctive; don't reduce it to a generic logo.

## Output
High-resolution PNG, plain white background, pure black artwork. Subject correctly isolated, framed and prominent. It should look like finished vector artwork even though it's raster. Don't claim it's an SVG; vectorisation, path simplification and cutter checks belong to the next stage (image-to-cnc-cut-svg).

## Quality control
Before returning, inspect for stray marks, background remnants, malformed features, inconsistent black/white regions, excessive texture and unnecessary geometric complexity. Be honest if the result has drifted generic. When correcting, preserve successful details from earlier iterations.

## Interaction
Be direct. If the request and source image are enough, generate immediately and keep explanation minimal. Prioritise a strong result faithful to the source yet clean enough for efficient vectorisation and CNC prep.
