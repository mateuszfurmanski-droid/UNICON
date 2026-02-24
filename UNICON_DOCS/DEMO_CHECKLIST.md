# UNICON — DEMO CHECKLIST (v0.1)

Purpose:
Ensure a clean, silent demo with no explanations required.

---

## 1) Files & Structure (MUST)

- [ ] UNICON_PROJECT folder present
- [ ] UNICON_CORE present and unchanged
- [ ] UNICON_DOCS present
- [ ] README.md opens without scrolling confusion

Critical files to verify:
- [ ] UNICON_CORE/core_manifest.json
- [ ] UNICON_CORE/style_tokens.json
- [ ] UNICON_CORE/tool_registry.json
- [ ] UNICON_CORE/tool_selector_rules.json

---

## 2) Demo Data (MUST)

Assigned task package:
- [ ] TASK_PACKAGE_EXAMPLE_DOORS_HANDLES_FIRE.json

Generated snag list:
- [ ] SNAG_LIST_ASSIGNED_pkg-joinery-doors-001.json

Snag schema:
- [ ] SNAG_DATA_SCHEMA.json includes assignment block
  - package_id
  - task_id
  - step_id

---

## 3) Snag Examples (MUST)

- [ ] SNAG_EXAMPLE_WORKTOP.json
- [ ] SNAG_EXAMPLE_FRAME.json
- [ ] SNAG_EXAMPLE_GAPS.json

Each snag must include:
- [ ] issue_type
- [ ] tool_id
- [ ] assignment block
- [ ] status + status_color

---

## 4) Tool Documentation (RECOMMENDED)

Verify presence (names must match tool_registry):
- [ ] 31_TOOL_WORKTOP_LEVEL_MEASURE.md
- [ ] 32_TOOL_FRAME_PLUMB_3D.md
- [ ] 33_TOOL_CUT_MITRE_SAW.md
- [ ] 34_TOOL_DOOR_GAP_TOLERANCE.md
- [ ] 35_TOOL_HINGE_LOAD_CHECK.md
- [ ] 36_TOOL_FINAL_CLIENT_CHECK.md

Each tool doc should clearly show:
- purpose
- required checks
- pass/fail logic
- evidence required

---

## 5) Visual Assets (OPTIONAL BUT STRONG)

Create demo placeholders:
- [ ] photos/worktop_ref_001.jpg
- [ ] photos/frame_ref_001.jpg
- [ ] photos/gaps_ref_001.jpg
- [ ] photos/door1_frame_ref.jpg
- [ ] photos/door1_gaps_ref.jpg
- [ ] photos/handles_ref.jpg
- [ ] photos/fire_sign_ref.jpg

Images can be:
- real site photos
- neutral stock
- placeholders with labels

---

## 6) Demo Flow Validation (CRITICAL)

Open DEMO_SCRIPT_SILENT_3MIN.md and confirm:
- [ ] No narration required
- [ ] No user tool selection
- [ ] Steps unlock sequentially
- [ ] Colors communicate result
- [ ] Final state is "IN REVIEW"

---

## 7) What NOT to Do During Demo

- [ ] Do NOT explain tolerances verbally
- [ ] Do NOT show raw numbers unless asked
- [ ] Do NOT open JSON files unless needed
- [ ] Do NOT mention future features

Let the system speak.

---

## 8) Demo Success Criteria

Demo is successful if viewer understands:
- Tasks are assigned by manager
- Tools are auto-selected
- Steps cannot be skipped
- Standards are enforced
- Evidence is attached
- Acceptance is external (manager)

No questions required.

---

## 9) After Demo (Optional)

- [ ] Zip project folder
- [ ] Save demo version as v0.1
- [ ] Collect feedback questions only
- [ ] Do not change system logic on the spot

---

## FINAL NOTE

If this checklist passes:
UNICON demo is ready.

Do not add features.
Do not explain more.
Silence is part of the design.
