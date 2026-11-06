# AGENTS.md

This repo is a skill pack for LLM agents: photo → B/W artwork → CNC-ready SVG.

- **Entry point:** `skills/photo-to-cnc-svg/SKILL.md`. Also load `skills/cnc-graphic-artwork-generator/SKILL.md` and `skills/image-to-cnc-cut-svg/SKILL.md`.
- **Needs:** an image-generation tool that takes a reference image; Python 3.10+; `pip install -r requirements.txt` (no system libraries).
- **Flow:**
  1. Take the photo + short direction; don't over-ask.
  2. Generate option A (bold stencil) and option B (engraving pass, then a moderate firming pass; if pass 2 barely changed, a third "bold linocut relief print" pass with only the pass-2 image as reference). Prompt templates are in `README.md`.
  3. Let the user pick A or B (or a tweak).
  4. Trace and preview the pick: settings, commands and defaults are in `skills/image-to-cnc-cut-svg/SKILL.md` (the single source for those).
- **Return:** SVG + preview PNG + short note, as in `image-to-cnc-cut-svg` section 4 (includes the CAM import tips).
- **Tests:** `pip install pytest && pytest -q` from the repo root.
- Examples of good output: `examples/` (overview: `docs/contact-sheet.png`; `old-fisherman` is the reference look).
