# MeetNote · A Wearable AI Meeting Assistant

[中文](README.md) · English · [Live site](https://anweat.github.io/meetnote/)

> From a desktop meeting recorder to a rounded, wearable AI assistant: four rounds of product definition, hardware architecture, mechanical/thermal design, and cost research.

**Status: engineering concept research · `BLOCKED / NOT FOR FAB`.**
This repository contains editable, reviewable design research — **not a manufacturable product, not a purchasing basis, and not a performance commitment**. Every power, runtime, temperature, and cost figure is an estimate; there are zero physical (E2) tests.

[![Docs license](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)](LICENSE-CC-BY-4.0)
[![Code license](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Live pages](https://img.shields.io/badge/pages-online-196b61.svg)](https://anweat.github.io/meetnote/)

![MeetNote R2 metal-enclosure research prototype](iterations/MeetNote-R2-metal/visuals/01_front.png)

## What this is

MeetNote is a wearable AI assistant built around one loop: **capture on purpose → save locally → understand on a server → review with evidence**. It is worn on the chest, detached for framing a shot, and placed on the table for meetings. The goal is to remove three steps — reaching for a phone, opening an app, searching afterwards — not to build another voice recorder.

Instead of drawing a finished product once, the project advances through **R0 → R1 → R2 → R3**. Each round ships editable engineering files, explicit calculation assumptions, verification results, and **open risks** — then decides whether the next round is worth doing.

**Core design principles**

1. **Consent before capture** — no recording by default at power-on; a physical switch cuts microphone/camera permission, and status LEDs are driven by the real capture rails, not by software alone.
2. **Local-first reliability** — losing the network never stops recording; "Saved" is shown only after an atomic local commit.
3. **Evidence, not automation** — summaries, action items, and decisions are candidates that link back to the original audio interval or photo and require user confirmation.
4. **Prove before promising** — FPGA retention, 43 °C touch temperature, 2-hour runtime, and the ¥300 cost target all have explicit test gates; failing one keeps the status `BLOCKED`.
5. **Transparent evidence levels** — every conclusion is tagged E0 (estimate), E1 (local tool verification), or E2 (physical test). E2 is currently zero.

## Four iterations

| Round | Positioning | Key output | Conclusion |
|---|---|---|---|
| [R0](iterations/MeetNote-R0/) | Desktop meeting recorder for 4–8 people | KiCad 4-layer carrier draft (root + 7 sheets), FreeCAD enclosure, BOM, OpenAPI draft, 12 local software tests, 8-page schematic PDF | Editable baseline established; ERC 3 errors + 7 warnings, DRC 4 violations + 93 unconnected — **not for fabrication** |
| [R1](iterations/MeetNote-R1-design/) | Wearable AI assistant (positioning shift) | Product/engineering baseline, offline interactive prototype, thermal/runtime/cost sensitivity | Form and interaction improved; 68×90×26 mm thermal screen FAIL (~62.8 °C estimated shell temperature) |
| [R2](iterations/MeetNote-R2-metal/) | Metal enclosure, bonding, motion/location | 60-object FreeCAD assembly, STEP/STL, Blender scene and 5 renders, single-unit cost model | Envelope feasible but heavy: 155–190 g; ¥1,985–4,530 per research unit, **not suitable as a lightweight pendant** |
| [R3 Lite](iterations/MeetNote-Lite-R3/) | ¥200–300 low-cost route | Component selection, budget, architecture trade-offs, validation order | A ~¥300 self-assembled test unit is conditionally feasible; **a complete ¥200 build has no credible sourcing closure** |

## Design snapshot

| Dimension | Current research value |
|---|---|
| Form factor | Chest-worn / handheld framing / desktop meeting |
| Dimensions | 82×118×29 mm (R0 bench) → 68×90×26 mm (R1 target) → 76×104×34 mm (R2 metal prototype, ~108 mm with strap lugs) |
| Mass | 120–160 g (R0) → 65–95 g (R1 target) → 155–190 g (R2) |
| Runtime | 2.39 h (R0) / 2.25 h (R1 meeting + occasional screen) / 2.09 h (R2 with GNSS + IMU) @ 2500 mAh — estimates |
| Main platform | Raspberry Pi Zero 2 W + iCE40UP5K + 4× IM69D130 PDM mics + Camera Module 3 AF |
| Low-cost platform | Luckfox Pico Mini A (RV1103) + Tang Nano 1K + SC3336 + dual mics + USB Wi-Fi |
| Cost | ¥500/unit allocation at 100 units; ¥1,985–4,530 per metal prototype; Lite target ¥296 (range ¥245–403) |
| Software | Encrypted chunking, resumable upload, idempotent retry, human-confirmation reference implementation; OpenAPI draft — **not deployed, no firmware** |
| Verification | Mostly E1 local verification (KiCad/FreeCAD/Blender/Python); zero E2 physical tests |

## Repository layout

```text
.
├── README.md                     # Chinese overview
├── README.en.md                  # This file
├── docs/                         # Cross-round product design synthesis
│   ├── 00-产品设计总览.md          # Positioning, form, decisions, maturity
│   ├── 01-需求与交互.md            # R01–R11, MVP, states and feedback
│   ├── 02-系统架构与软件协议.md     # Data path, budgets, power, crypto, API
│   ├── 03-机械结构与热设计.md       # Dimensions, assembly, metal shell, thermal
│   ├── 04-成本与供应链.md          # Three cost models and sourcing rules
│   ├── 05-风险与验证计划.md        # Risk register, gates, next tests
│   └── 06-迭代记录.md             # R0–R3 inputs, outputs, leftovers
├── iterations/                   # Original four delivery packages (byte-preserved)
│   ├── MeetNote-R0/
│   ├── MeetNote-R1-design/
│   ├── MeetNote-R2-metal/
│   └── MeetNote-Lite-R3/
├── site/                         # GitHub Pages static site + interactive reviews
├── .github/workflows/pages.yml   # Pages deployment
├── LICENSE                       # MIT (scripts and software)
└── LICENSE-CC-BY-4.0             # CC BY 4.0 (docs, images, mechanical/engineering material)
```

Each iteration folder keeps its own `README.md`, `FILE_MANIFEST.csv` (SHA-256), and `verification/` results unchanged — they are the evidence behind this synthesis.

## Where to start

- **Product only:** [Product design overview](docs/00-产品设计总览.md) → [Iteration history](docs/06-迭代记录.md)
- **Verification:** [Risks and validation plan](docs/05-风险与验证计划.md) → R0 [acceptance record](iterations/MeetNote-R0/verification/验收记录.md)
- **Hardware:** [Architecture and software protocol](docs/02-系统架构与软件协议.md) → [R0 ECAD constraints](iterations/MeetNote-R0/docs/03_ECAD_constraints.md)
- **Mechanical/thermal:** [Mechanical and thermal design](docs/03-机械结构与热设计.md) → R2 [design and validation boundary](iterations/MeetNote-R2-metal/docs/设计说明与验证边界.md)
- **Cost:** [Cost and supply chain](docs/04-成本与供应链.md)

## Live site and interactive reviews

**Project home:** [anweat.github.io/meetnote](https://anweat.github.io/meetnote/)

Three static, offline-capable research pages (no network calls, no recording, no AI):

- **R1 interactive prototype:** [live](https://anweat.github.io/meetnote/reviews/r1.html) · [source](iterations/MeetNote-R1-design/design-review.html) — switch between remember / look / review / meeting / offline modes, compare 68×90×26 and 54×72×22 mm envelopes, and recompute runtime and thermal screening.
- **R2 structure review:** [live](https://anweat.github.io/meetnote/reviews/r2.html) · [source](iterations/MeetNote-R2-metal/review.html) — metal enclosure, bonding, exploded view, and single-unit cost basis.
- **R3 Lite budget review:** [live](https://anweat.github.io/meetnote/reviews/r3.html) · [source](iterations/MeetNote-Lite-R3/review.html) — budget, architecture, add-on cost calculator, and validation order.

The site is built from `site/` and deployed through GitHub Actions; the original HTML and source files remain under `iterations/`.

## Reproduce the local calculations

Python 3 standard library only (R0 software tests additionally need `requirements.txt`):

```bash
# R0: budget / bandwidth / storage, plus 12 reference software tests
python3 iterations/MeetNote-R0/scripts/budget_check.py
cd iterations/MeetNote-R0/software && python3 -m unittest -v test_pipeline

# R1: budget, runtime, thermal screening
python3 iterations/MeetNote-R1-design/scripts/check_design.py

# R2: single-unit cost and power model
python3 iterations/MeetNote-R2-metal/scripts/cost_model.py

# R3: budget and bandwidth calculations + review page build
python3 iterations/MeetNote-Lite-R3/scripts/build_review.py
```

KiCad / FreeCAD / Blender rebuild steps are documented in each round's README. **This repository does not contain a usable fabrication package.** The manufacturing exports under `iterations/MeetNote-R0/electronics/NOT_FOR_FAB/` exist only to verify the export chain; the folder name, readme, and silkscreen all say do not fabricate.

## Boundaries and disclaimer

- This is not a manufacturable product and not an investment or purchasing basis. `POWER_ASSEMBLY`, `12M288_XO`, and `HARD_INTERLOCK` are interface placeholders; the PCB is unrouted; there is no FPGA bitstream, firmware, or server implementation.
- The thermal target (≤43 °C touch surface at 35 °C ambient) **fails estimation**; the battery's 6 W peak pulse capability is unproven; two RF keep-out conflicts remain unresolved.
- All costs are RMB research budgets with **no formal supplier quotes** and no guarantee of achievability.
- Encryption, key protection, anti-theft, and secure update are design drafts only; the Zero 2 W has no verified secure key storage.
- Every "done" means done at the local tool/script level, not physical function, certification, or production readiness.

See the [R0 acceptance record](iterations/MeetNote-R0/verification/验收记录.md) for evidence levels and open items, and the [risk plan](docs/05-风险与验证计划.md) for the validation order.

## License

- Documentation, images, mechanical/structural design, and engineering research: [CC BY 4.0](LICENSE-CC-BY-4.0)
- Scripts and software code: [MIT](LICENSE)

When citing or redistributing, keep the attribution and the "research estimate, not production" boundary.
