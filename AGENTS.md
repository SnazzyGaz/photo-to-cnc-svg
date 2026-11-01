# AGENTS.md

This repo is a skill pack for LLM agents: photo → B/W artwork → CNC-ready SVG.

- **Entry point:** `skills/photo-to-cnc-svg/SKILL.md`. Also load `skills/cnc-graphic-artwork-generator/SKILL.md` and `skills/image-to-cnc-cut-svg/SKILL.md`.
- **Needs:** an image-generation tool that takes a reference image; Python 3; `pip install -r requirements.txt`.
- **Flow:**
  1. Take the photo + short direction; don't over-ask.
  2. Generate option A (bold stencil) and option B (engraving pass, then a moderate firming pass). Prompt templates are in `README.md`.
  3. Let the user pick A or B (or a tweak).
  4. Trace: `python3 scripts/cnc_vector.py art.png -o <subject>_vcarve_300mm.svg --mode vcarve --width-mm 300 --vbit-angle 60 --depth 3 --threshold 128 --smooth 0.8 --min-feature 0.5 > stats.json` (0.8 for option A).
  5. Preview: `python3 scripts/preview.py <svg> preview.png`; check it, adjust `--min-feature` 1 to 3 times if needed.
- **Return:** SVG + preview PNG + short note (size, mode, path count, time range from `stats.json`, clearance end mill if noted, CAM import tip from `README.md`).
- Examples of good output: `examples/`.
