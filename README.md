# photo-to-cnc-svg

**A skill pack for LLM agents** (Grok Bot, Claude, ChatGPT-style and other tool-using agents) that turns a photo into carve-ready CNC art: bold black-and-white artwork first, then a clean, mm-scaled SVG with a true-to-cut preview, a machining-time estimate and import notes for your CAM program.

> **For humans:** you don't run this yourself. Point your AI agent at this repo (e.g. *"install the skill from github.com/SnazzyGaz/photo-to-cnc-svg"*), then send it a photo and a line of direction, like *"head and shoulders, keep the cap and beard, lose the background"*. It shows you two artwork options, you pick one, and it hands back the SVG.

<table>
<tr><th width="25%">Source</th><th width="25%">B/W art</th><th width="25%">Traced SVG (cut map)</th><th width="25%">Carved, in Carve Sim</th></tr>
<tr>
<td><img src="docs/pipeline/samurai-1-source.jpg" alt="Generated source: samurai helmet on a skull"></td>
<td><img src="docs/pipeline/samurai-2-art.jpg" alt="White-on-black woodcut art"></td>
<td><img src="docs/pipeline/samurai-3-cutmap.jpg" alt="Cut map, black is carved"></td>
<td><img src="docs/pipeline/samurai-4-carvesim.jpg" alt="Walnut board with white epoxy fill"></td>
</tr>
<tr><td colspan="4"><sub><b>Samurai skull, inverted.</b> Drawn white on black and traced with <code>--invert</code>, so the light parts are cut. Filled with white epoxy in walnut it reads as a pale image on a dark board. 380 paths, about 16 min.</sub></td></tr>
<tr>
<td><img src="docs/pipeline/stag-1-source.jpg" alt="Generated source: red deer stag"></td>
<td><img src="docs/pipeline/stag-2-art.jpg" alt="Black-on-white woodcut art"></td>
<td><img src="docs/pipeline/stag-3-cutmap.jpg" alt="Cut map, black is carved"></td>
<td><img src="docs/pipeline/stag-4-carvesim.jpg" alt="Ash board with walnut inlay"></td>
</tr>
<tr><td colspan="4"><sub><b>Regal stag, standard.</b> Black lines are cut. Shown in ash with a walnut inlay. 326 paths, about 11 min.</sub></td></tr>
</table>

<sub>V-carve, 300 mm, 60° V-bit, 3 mm deep. The source images are generated stand-ins.</sub>

## How it works

<table>
<tr><th width="16%"></th><th width="28%">Source photo</th><th width="28%">Option A: bold stencil</th><th width="28%">Option B: mid-ground engraving</th></tr>
<tr>
<td><b>1–2. Photo in, two options out</b><br><sub>Example direction: <i>"head and shoulders, keep the cap and beard, lose the background"</i></sub></td>
<td><img src="examples/old-fisherman/source.jpg" alt="Generated source photo: old fisherman in a knitted cap and jumper"></td>
<td><img src="examples/old-fisherman/option-a.jpg" alt="Option A: bold stencil of the fisherman"></td>
<td><img src="examples/old-fisherman/option-b.jpg" alt="Option B: bold linocut-style engraving of the fisherman"></td>
</tr>
<tr>
<td colspan="2" align="right"><b>3–5. Pick, trace, deliver</b><br><sub>True-to-cut previews: black is carved.<br>Click one to open its SVG.</sub></td>
<td><a href="examples/old-fisherman/old-fisherman-stencil_vcarve_300mm.svg"><img src="examples/old-fisherman/preview-option-a.png" alt="Traced option A, true-to-cut preview"></a><br><sub>112 paths · ~33 min (23–42)</sub></td>
<td><a href="examples/old-fisherman/old-fisherman_vcarve_300mm.svg"><img src="examples/old-fisherman/preview.png" alt="Traced option B, true-to-cut preview"></a><br><sub>292 paths · ~39 min (27–51)</sub></td>
</tr>
</table>

1. **Photo + short direction:** which subject or region, and what to keep or drop. If the subject is obvious, the agent doesn't ask questions.
2. **Two artwork options**, generated with the photo as the reference image:
   - **A, simplified bold stencil** (one generation): big solid black shapes, white negative space, smooth contours, few internal lines. Quick to carve, reads from across a room.
   - **B, mid-ground engraving** (two or three generations): a faithful **engraving pass** (woodcut-style hatching that follows the form), then a **moderate firming pass** that thickens strokes, removes grey and stipple and deepens the darkest shadows into solid black. Image models often copy pass 1 too closely; if pass 2 barely changes it, a **third pass** with only the pass-2 image as reference ("convert to a bold linocut relief print") does the firming. The fisherman above needed that third pass. B sits between a fine engraving and a bold linocut: lots of character, still traceable.
3. **Pick one**, or ask for a tweak.
4. **Trace to SVG** with `cnc_vector.py` at the [defaults](#defaults-used-by-the-skills) unless you give specs, then check the even-odd preview and re-trace with a higher or lower `--min-feature` if it's speckled or has lost detail (1 to 3 tries).
5. **Deliver:** the SVG, the preview PNG of exactly what gets carved, and a short note: size, path count, time estimate, whether wide areas need a clearance end mill, and how to import it into your CAM program.

## For agents: start here

**Entry point:** [`skills/photo-to-cnc-svg/SKILL.md`](skills/photo-to-cnc-svg/SKILL.md). Load it, plus the two stage skills it references:
[`skills/cnc-graphic-artwork-generator/SKILL.md`](skills/cnc-graphic-artwork-generator/SKILL.md) (photo → B/W artwork) and
[`skills/image-to-cnc-cut-svg/SKILL.md`](skills/image-to-cnc-cut-svg/SKILL.md) (artwork → SVG). [`AGENTS.md`](AGENTS.md) has the same flow in short form.

**You need:** an image-generation tool that accepts a reference image, and a shell with Python 3.9+, this repo checked out and `pip install -r requirements.txt`.

**Flow:** the five steps [above](#how-it-works). Prompts are in the [templates](#image-generation-prompt-templates). Trace and preview the pick with:

```bash
python3 scripts/cnc_vector.py art.png -o <subject>_vcarve_300mm.svg --mode vcarve --width-mm 300 \
  --vbit-angle 60 --depth 3 --threshold 128 --smooth 0.8 --min-feature 0.5 > stats.json   # 0.8 for option A
python3 scripts/preview.py <subject>_vcarve_300mm.svg preview.png
```

**Return to the user:** the SVG, the preview PNG, and a short note: size (mm), mode, path count, the time range from `stats.json` (rough; CAM simulation is authoritative), whether wide areas need a clearance end mill (`notes` in `stats.json`), and the one-line [CAM import tip](#importing-into-cam) for their program.

## Example gallery

Every "photo" is a generated stand-in, run through the flow at the default settings. Both options are traced for every subject except the lighthouse; B is the house style. Click a traced preview to open its SVG.

| Subject | Source | Option A | Option B | Traced A | Traced B | Paths | Est. min* |
|---|---|---|---|---|---|---|---|
| **Old fisherman** | <img src="examples/old-fisherman/source.jpg" width="110" alt="Old fisherman: source"> | <img src="examples/old-fisherman/option-a.jpg" width="110" alt="Old fisherman: option A"> | <img src="examples/old-fisherman/option-b.jpg" width="110" alt="Old fisherman: option B"> | <a href="examples/old-fisherman/old-fisherman-stencil_vcarve_300mm.svg"><img src="examples/old-fisherman/preview-option-a.png" width="110" alt="Old fisherman: traced A"></a> | <a href="examples/old-fisherman/old-fisherman_vcarve_300mm.svg"><img src="examples/old-fisherman/preview.png" width="110" alt="Old fisherman: traced B"></a> | A&nbsp;112<br>B&nbsp;292 | A&nbsp;~33&nbsp;(23–42)<br>B&nbsp;~39&nbsp;(27–51) |
| **Howling wolf** | <img src="examples/howling-wolf/source.jpg" width="110" alt="Howling wolf: source"> | <img src="examples/howling-wolf/option-a.jpg" width="110" alt="Howling wolf: option A"> | <img src="examples/howling-wolf/option-b.jpg" width="110" alt="Howling wolf: option B"> | <a href="examples/howling-wolf/howling-wolf-stencil_vcarve_300mm.svg"><img src="examples/howling-wolf/preview-option-a.png" width="110" alt="Howling wolf: traced A"></a> | <a href="examples/howling-wolf/howling-wolf_vcarve_300mm.svg"><img src="examples/howling-wolf/preview.png" width="110" alt="Howling wolf: traced B"></a> | A&nbsp;12<br>B&nbsp;101 | A&nbsp;~13&nbsp;(9–16)<br>B&nbsp;~19&nbsp;(14–25) |
| **Red deer stag** | <img src="examples/red-deer-stag/source.jpg" width="110" alt="Red deer stag: source"> | <img src="examples/red-deer-stag/option-a.jpg" width="110" alt="Red deer stag: option A"> | <img src="examples/red-deer-stag/option-b.jpg" width="110" alt="Red deer stag: option B"> | <a href="examples/red-deer-stag/red-deer-stag-stencil_vcarve_300mm.svg"><img src="examples/red-deer-stag/preview-option-a.png" width="110" alt="Red deer stag: traced A"></a> | <a href="examples/red-deer-stag/red-deer-stag_vcarve_300mm.svg"><img src="examples/red-deer-stag/preview.png" width="110" alt="Red deer stag: traced B"></a> | A&nbsp;7<br>B&nbsp;265 | A&nbsp;~13&nbsp;(9–16)<br>B&nbsp;~11&nbsp;(7–14) |
| **Tall ship** | <img src="examples/tall-ship/source.jpg" width="110" alt="Tall ship: source"> | <img src="examples/tall-ship/option-a.jpg" width="110" alt="Tall ship: option A"> | <img src="examples/tall-ship/option-b.jpg" width="110" alt="Tall ship: option B"> | <a href="examples/tall-ship/tall-ship-stencil_vcarve_300mm.svg"><img src="examples/tall-ship/preview-option-a.png" width="110" alt="Tall ship: traced A"></a> | <a href="examples/tall-ship/tall-ship_vcarve_300mm.svg"><img src="examples/tall-ship/preview.png" width="110" alt="Tall ship: traced B"></a> | A&nbsp;144<br>B&nbsp;408 | A&nbsp;~25&nbsp;(17–32)<br>B&nbsp;~17&nbsp;(12–22) |
| **Bald eagle** | <img src="examples/bald-eagle/source.jpg" width="110" alt="Bald eagle: source"> | <img src="examples/bald-eagle/option-a.jpg" width="110" alt="Bald eagle: option A"> | <img src="examples/bald-eagle/option-b.jpg" width="110" alt="Bald eagle: option B"> | <a href="examples/bald-eagle/bald-eagle-stencil_vcarve_300mm.svg"><img src="examples/bald-eagle/preview-option-a.png" width="110" alt="Bald eagle: traced A"></a> | <a href="examples/bald-eagle/bald-eagle_vcarve_300mm.svg"><img src="examples/bald-eagle/preview.png" width="110" alt="Bald eagle: traced B"></a> | A&nbsp;18<br>B&nbsp;253 | A&nbsp;~25&nbsp;(17–32)<br>B&nbsp;~26&nbsp;(18–34) |
| **Vintage motorcycle**<br><sub>300×225 mm</sub> | <img src="examples/vintage-motorcycle/source.jpg" width="110" alt="Vintage motorcycle: source"> | <img src="examples/vintage-motorcycle/option-a.jpg" width="110" alt="Vintage motorcycle: option A"> | <img src="examples/vintage-motorcycle/option-b.jpg" width="110" alt="Vintage motorcycle: option B"> | <a href="examples/vintage-motorcycle/vintage-motorcycle-stencil_vcarve_300mm.svg"><img src="examples/vintage-motorcycle/preview-option-a.png" width="110" alt="Vintage motorcycle: traced A"></a> | <a href="examples/vintage-motorcycle/vintage-motorcycle_vcarve_300mm.svg"><img src="examples/vintage-motorcycle/preview.png" width="110" alt="Vintage motorcycle: traced B"></a> | A&nbsp;105<br>B&nbsp;354 | A&nbsp;~19&nbsp;(13–24)<br>B&nbsp;~7&nbsp;(5–10) |
| **Red fox** | <img src="examples/red-fox/source.jpg" width="110" alt="Red fox: source"> | <img src="examples/red-fox/option-a.jpg" width="110" alt="Red fox: option A"> | <img src="examples/red-fox/option-b.jpg" width="110" alt="Red fox: option B"> | <a href="examples/red-fox/red-fox-stencil_vcarve_300mm.svg"><img src="examples/red-fox/preview-option-a.png" width="110" alt="Red fox: traced A"></a> | <a href="examples/red-fox/red-fox_vcarve_300mm.svg"><img src="examples/red-fox/preview.png" width="110" alt="Red fox: traced B"></a> | A&nbsp;20<br>B&nbsp;1099 | A&nbsp;~18&nbsp;(13–24)<br>B&nbsp;~35&nbsp;(25–45) |
| **Lighthouse**<br><sub>300×400 mm</sub> | <img src="examples/lighthouse/source.jpg" width="110" alt="Lighthouse: source"> | <img src="examples/lighthouse/option-a.jpg" width="110" alt="Lighthouse: option A"> | <img src="examples/lighthouse/option-b.jpg" width="110" alt="Lighthouse: option B"> | <a href="examples/lighthouse/lighthouse_vcarve_300mm.svg"><img src="examples/lighthouse/preview.png" width="110" alt="Lighthouse: traced A"></a> | <sub>not traced</sub> | A&nbsp;87 | A&nbsp;~32&nbsp;(22–41) |

\* Minutes: estimate (range). V-carve, 300 mm wide (except where noted), 60° V-bit, 3 mm max depth, feeds 1200/300/3000 mm/min. Rough estimate from the script; your CAM simulation is authoritative. Each folder has the script's `stats.json` (B) and `stats-option-a.json` (A).

Notes:

- **Which pass B came from:** the old fisherman, tall ship, bald eagle and vintage motorcycle needed the third (bold linocut) pass; the wolf and stag firmed up at pass 2.
- **Time follows area, not path count.** Thin strokes are cut in one sweep along their centreline; shapes wider than the bit can span at 3 mm (about 3.5 mm with a 60° bit) are cleared at full depth. That's why A, with its big solid blacks, is sometimes the slower carve (stag, tall ship, motorcycle).
- **Tall ship:** the thin rigging lines carve shallow at 300 mm; it suits 450 mm+ or a 30° bit.
- **Red fox:** from the first batch, made before the third pass existed. Its B traces cleanly but at 1,099 paths it is by far the busiest file here.
- **Lighthouse:** traced as A only (stored under the B filenames, `lighthouse_vcarve_300mm.svg` and `preview.png`). Its B kept fine stipple and sky hatching: fine on paper, slow and fragile in wood.

The six subjects made with the current flow on one page: [`docs/contact-sheet.png`](docs/contact-sheet.png).

## Works with Carve Sim

The SVGs can be previewed in [Carve Sim](https://github.com/SnazzyGaz/carve-sim), a free browser app that shows the carve in 3D in different woods and fills (epoxy, metallic or wood inlay), sanded flush or as poured. Drop the SVG in and it reads the size and carve type from the file. **[Open Carve Sim →](https://snazzygaz.github.io/carve-sim/)**

<p align="center"><img src="docs/pipeline/samurai-carvesim-walnut-elm.jpg" width="640" alt="The samurai skull SVG in Carve Sim: black walnut with an elm inlay"></p>
<p align="center"><sub>The samurai skull SVG in Carve Sim · black walnut · elm inlay, sanded flush</sub></p>

## Installing the skills in your agent

The `skills/` folder holds three plain-Markdown skills with YAML front matter (`name`, `description`):

| Skill | Does |
|---|---|
| `skills/photo-to-cnc-svg/SKILL.md` | The end-to-end flow (start here) |
| `skills/cnc-graphic-artwork-generator/SKILL.md` | Stage 1: photo → B/W artwork, prompt rules and QC |
| `skills/image-to-cnc-cut-svg/SKILL.md` | Stage 2: artwork → SVG, settings, preview, CAM notes |

- **Grok Bot and similar agents with a skills folder:** drop the three folders into the agent's skills directory and keep this repo checked out on the machine the agent runs code on. The skills call `scripts/cnc_vector.py` relative to the repo root and point to this README for the full prompt templates.
- **Claude (Agent Skills / Claude Code):** copy each folder into `.claude/skills/` (project) or `~/.claude/skills/` (personal), and keep the repo checked out alongside.
- **ChatGPT / custom GPTs and other chat assistants:** paste `skills/photo-to-cnc-svg/SKILL.md` and the stage 1 skill into the instructions, plus the prompt templates below, and attach `cnc_vector.py` + `preview.py` as files for the code tool.

## Image-generation prompt templates

Replace the `[...]` parts and attach the source photo as a reference image. Naming the subject's defining features is what keeps it from drifting into generic clip art.

- If pass 2 barely changes pass 1 (common: the model copies the first reference closely), don't keep re-running it; go to pass 3.
- For scenes (buildings, landscapes), ask for "a few bold horizontal engraved cloud lines with plenty of white" instead of a fully hatched sky.

### Option A: simplified bold stencil (one generation, photo as reference)

```
Simplified bold stencil of THIS exact [subject] from the reference photo: same
[pose / view] and framing, tightly cropped to [region, e.g. head and shoulders],
no background. Bold clean graphic made of large solid black shapes and pure
white negative space, smooth contours, few internal lines. Keep what makes it
this [subject]: [defining features, e.g. ear shape, eye, nose, markings, props],
[fur / hair / feathers] shown as a handful of bold locks. Pure black on pure
white only, no grey, no gradients, no speckles, no text, crisp edges, high
resolution, looks like finished vector stencil artwork.
```

### Option B, pass 1: faithful engraving (photo as reference)

```
Faithful black-and-white woodcut / engraved-illustration interpretation of THIS
exact [subject] from the reference photo, same [pose / view] and framing,
tightly cropped to [region], background removed to plain white. Name and keep:
[defining features and anything physically on the subject, e.g. collar, bridle].
Render form with directional hatching that follows the [fur / muscle / feather]
flow, dense blacks in shadows, open white on lit planes. Pure black on pure
white only, no grey, no gradients, no text, crisp edges, high resolution.
```

### Option B, pass 2: moderate firming (pass 1 + photo as references)

```
Moderate refinement of the engraved [subject] (first reference) using the photo
(second reference) for fidelity. Keep the exact same pose, framing, anatomy and
most of the hatching, but turn all grey or stippled tones into clean black
strokes, make every stroke slightly thicker, deepen the darkest shadows
([where, e.g. under the jaw, inner ear]) into some solid black, and add a clear
contour line on the outer edge. Not a full bold linocut: it should sit between a
fine engraving and a bold linocut. Pure black on pure white only, no grey, no
gradients, no speckles, no text, plain white background, crisp edges, high
resolution.
```

### Option B, pass 3 (only if pass 2 barely changed): bold linocut (pass 2 as the ONLY reference)

```
Convert this engraving of [subject] into a bold black-and-white linocut relief
print with chunky gouge marks, keeping the exact same [pose / face / features].
[Dark areas, e.g. cap, sweater, body feathers, tyres] become solid black masses
with only a few thick white carved cuts. Lit planes stay clean white with a few
decisive strokes. [Hair / fur / beard / feathers] as fewer, long thick locks
separated by black gouge strokes, no fine wiry hairs. Minimum line width like a
2-3 mm gouge cut; nothing hair-thin, no texture, no dots. Pure black and pure
white, no grey, white background, crisp edges, high resolution.
```

## Importing into CAM

- **Vectric (VCarve / Aspire):** import the SVG at 1:1 in mm, select all, V-Carve toolpath with your V-bit; tick flat depth and add the end mill as clearance tool for wide areas.
- **Carbide Create:** import the SVG, check the size, then Advanced V-carve with the end mill as the pocket tool. Advanced V-carve is in the free version, but free (Core) only exports G-code for Carbide 3D machines; other machines need Pro.
- **Easel:** import the SVG and check the width (it can mis-scale). V-carving needs Easel Pro; on the free plan, fill-cut/pocket with an end mill or use other CAM for the V-carve.
- **Fusion 360:** insert the SVG onto a sketch, verify scale, then use an Engrave (V-bit) or 2D Pocket toolpath.

If `stats.json` notes say *"flat areas wider than 3.5 mm hit max depth"*, that's the 60° bit bottoming out at 3 mm: use flat-depth V-carving with a clearance end mill.

## Reference: the tracing script

The agent runs these; they're documented here for agents and for anyone running them by hand.

### Install

Python 3.9+.

```bash
git clone https://github.com/SnazzyGaz/photo-to-cnc-svg.git
cd photo-to-cnc-svg
pip install -r requirements.txt
```

Dependencies: numpy, scipy, opencv-python-headless, scikit-image, potracer (pure-Python potrace) and cairosvg (previews). cairosvg needs the Cairo library: `brew install cairo` on macOS, `apt install libcairo2` on Debian/Ubuntu; on Windows, install a GTK3 runtime or MSYS2's Cairo package and make sure its DLLs are on `PATH`.

### Usage

This reproduces the old fisherman's option B exactly (292 paths, ~39 min), so it doubles as a check that the install works. `work/` is git-ignored.

```bash
mkdir -p work

# B/W artwork (option A or B) -> V-carve SVG, 300 mm wide, with job estimate
python3 scripts/cnc_vector.py examples/old-fisherman/option-b.jpg -o work/old-fisherman_vcarve_300mm.svg \
  --mode vcarve --width-mm 300 --vbit-angle 60 --depth 3 \
  --threshold 128 --smooth 0.8 --min-feature 0.5 > work/stats.json

# True-to-cut preview (all paths merged, even-odd, so holes read correctly)
python3 scripts/preview.py work/old-fisherman_vcarve_300mm.svg work/preview.png --width 1600
```

The SVG is in millimetres (`width="300mm"` with a matching viewBox), so it imports at 1:1. The JSON on stdout has size, path/node counts and, when `--depth` is given, a time estimate with range and notes.

### Modes

| Mode | What you get | Typical use |
|---|---|---|
| `vcarve` | Closed filled regions, cleaned to what the V-bit can resolve | Portraits, line art, engravings (recommended) |
| `pocket` | Closed regions constrained to the end-mill diameter; `--levels N` for stepped depths | Signs, relief-style layering |
| `engrave` | Single-line centrelines (open paths, smoothed) | Fine line engraving, drag/pen tools |
| `profile` | Outer silhouette only | Cutting the shape free |

### Flags

| Flag | Default | Meaning |
|---|---|---|
| `--mode` | (required) | `vcarve`, `pocket`, `engrave`, `profile` |
| `--width-mm` / `--height-mm` | | Finished size (give one; aspect is kept) |
| `--threshold` | `auto` | `auto`, `adaptive`, or 0–255. Use `128` for clean B/W art |
| `--smooth` | `2.0` | Denoise strength 0–5. Use `0.8` for clean art, higher for photos |
| `--min-feature` | vcarve 0.6, engrave 0.8, pocket/profile = tool Ø | Smallest kept detail in mm. Raise if speckled, lower if detail is lost |
| `--tool-dia` | `3.175` | End mill / profile tool diameter (mm) |
| `--vbit-angle` | `60` | V-bit included angle |
| `--depth` | | Total cut depth (V-carve: max/flat depth). Enables the estimate |
| `--pass-depth` | tool Ø / 2 | Depth per pass (V-carve: = depth) |
| `--feed` / `--plunge` / `--rapid` | 1200 / 300 / 3000 | mm/min, for the estimate |
| `--safe-z` / `--stepover` | 5 / 0.4 | Estimate inputs (mm / fraction of tool or V width) |
| `--crop x0,y0,x1,y1` | | Crop in px or 0–1 fractions |
| `--isolate` | | GrabCut the subject inside `--crop` (photos) |
| `--use-isolation-as-mask` | | Profile: silhouette = isolated subject |
| `--invert` | | Cut the light areas instead of the dark |
| `--levels` | `1` | Pocket depth levels |
| `--lines dark\|edges` | `dark` | Engrave source |
| `--single` | | Profile: keep the largest outline only |
| `--border` | `0` | Add a rectangular profile border, margin in mm |
| `--alphamax` / `--opttol` | 1.1 / 0.4 | Potrace corner smoothness / curve simplification |
| `--preview` | | Quick built-in PNG (fills paths separately, so holes look solid; use `preview.py`) |

`python3 scripts/cnc_vector.py --help` prints the same list.

### Defaults used by the skills

| Setting | Default |
|---|---|
| Style | V-carve |
| Width | 300 mm |
| V-bit | 60° |
| Depth | 3 mm (pocket 6, engrave 1, profile = stock thickness) |
| End mill (clearance / pocket) | 3.175 mm (1/8") |
| Feeds | 1200 feed / 300 plunge / 3000 rapid mm/min |
| Trace settings, generated art | `--threshold 128 --smooth 0.8 --min-feature 0.5` (0.8 for option A or a 90° bit) |
| Trace settings, photo | `--threshold auto --smooth 2`, plus `--crop`/`--isolate` as needed |

## Repo layout

```
AGENTS.md                 short agent entry point
scripts/cnc_vector.py     tracer (vcarve / pocket / engrave / profile) + job estimate
scripts/preview.py        even-odd merged preview PNG
skills/                   the three agent skills
examples/<subject>/       source.jpg, option-a.jpg, option-b.jpg
                          B: <subject>_vcarve_300mm.svg, preview.png, stats.json
                          A: <subject>-stencil_vcarve_300mm.svg, preview-option-a.png, stats-option-a.json
                          (lighthouse: A only, under the B filenames)
docs/contact-sheet.png    the six current-flow subjects on one page
docs/pipeline/            images for the samurai and stag strips and the Carve Sim shot
```

## Licence

MIT © 2026 Garyck Arntzen ([@_mintydoge](https://x.com/_mintydoge)). See [LICENSE](LICENSE).
