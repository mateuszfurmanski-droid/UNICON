# UNICON — RELEASE NOTES v0.1

Release date: 2025-12-20  
Status: LOCKED (logic & structure)

---

## Overview

UNICON v0.1 is a **platform-agnostic workflow specification** for construction quality control.

This release defines:
- roles
- task assignment
- automatic tool selection
- tolerance-based validation
- evidence-driven acceptance

No platform UI or sensor integration is included by design.

---

## What Is Included (v0.1)

### 1) Core Architecture
- Universal project structure (`UNICON_PROJECT`)
- Platform-independent core pack (`UNICON_CORE`)
- Documentation-first approach (`UNICON_DOCS`)

### 2) Role Model (LOCKED)
- Manager assigns task packages
- Installer sees ONLY assigned tasks
- Installer does NOT choose tools or tolerances

Defined in:
- `ROLE_AND_TASK_FLOW.md`
- reinforced in `README.md`

### 3) Task Packages
- Structured task packages with:
  - tasks
  - required steps
  - must_pass logic
- Example package:
  - 2 doors
  - 4 handles
  - fire door signage

File:
- `TASK_PACKAGE_EXAMPLE_DOORS_HANDLES_FIRE.json`

### 4) Automatic Snag Generation
- Task steps generate installer-visible snags
- Snags inherit:
  - package_id
  - task_id
  - step_id

Rules defined in:
- `TASK_TO_SNAG_RULES.md`

Output example:
- `SNAG_LIST_ASSIGNED_pkg-joinery-doors-001.json`

### 5) Snag Data Model
- Unified snag schema
- Assignment block added:
  - package_id
  - task_id
  - step_id

File:
- `SNAG_DATA_SCHEMA.json`

### 6) Tools (IDs 31–36)
Defined tools:
- 31 — Worktop level + measure
- 32 — Frame plumb 3D
- 33 — Cut / generic measure placeholder
- 34 — Door gap tolerance
- 35 — Hinge load check
- 36 — Final client check

Tools are:
- auto-selected
- sequential
- non-skippable if must_pass

### 7) Visual System
- 90s thin TXT HUD style
- No icons
- No gradients
- Color-based status logic

File:
- `style_tokens.json`

### 8) Demo Assets
- Silent demo flow (no narration)
- Demo checklist
- Example snags and task packages

Files:
- `DEMO_SCRIPT_SILENT_3MIN.md`
- `DEMO_CHECKLIST.md`

---

## What Is Explicitly NOT Included (v0.1)

- No Android / iOS / Web app
- No AR SDK integration
- No IMU / LiDAR / camera processing
- No cloud backend
- No user authentication
- No permissions system
- No AI claims

This is intentional.

---

## Stability Guarantees

LOCKED in v0.1:
- Role hierarchy
- Task → tool auto-selection
- Assignment-based visibility
- Tolerance enforcement logic
- Silent demo philosophy

Changes to these require a new major version.

---

## Known Limitations

- Tool 33 used as generic placeholder
- Evidence handling is structural only (no storage)
- Photo relocalization is manual
- Demo assets are placeholders

---

## Upgrade Path (v0.2 candidates)

- Platform client (one minimal target)
- Sensor abstraction layer
- Evidence metadata expansion
- Additional tools (handle height, fixings)
- Auto status propagation

---

## Release Statement

UNICON v0.1 is complete as a **system definition**.

It is suitable for:
- demos
- pitches
- grants
- implementation planning

It is not a prototype application.

---

End of release notes.
