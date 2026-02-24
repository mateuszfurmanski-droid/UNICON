# UNICON — TASK PACKAGE → SNAG GENERATION RULES (v0.1)

## Purpose
Define how assigned task packages automatically produce an installer-visible snag list.

Installer sees only generated snags from assigned packages.

---

## Input
- TASK_PACKAGE_*.json

## Output
- SNAG_LIST_ASSIGNED_<package_id>.json
- SNAG records per step (optional as separate files)

---

## Generation Rules (LOCK)

### Rule 1 — MEASURE steps always generate a snag
If step.type = MEASURE:
- create a snag
- snag.issue_type = step.issue_type
- snag.tool_id = step.tool_id
- snag.tool_name = step.tool_name
- snag.status = TODO

### Rule 2 — CHECK steps generate a snag only if evidence_required = true
If step.type = CHECK and parent task evidence_required = true:
- create a snag
- snag.issue_type = step.issue_type (or FINAL if compliance)
- snag.tool_id / tool_name from step

### Rule 3 — Linking fields must be present
Each generated snag must include:
- package_id
- task_id
- step_id

### Rule 4 — Location propagation
snag.site.room_name = task.location.room_name
snag.site.location_note = task.location.location_note

### Rule 5 — Standards propagation
If step contains standards (e.g. gaps rules):
- copy into snag.description or snag.measurements tolerances.

### Rule 6 — Visibility
Installer-visible snag list includes ONLY snags generated from assigned packages.
Manager can see full project snag list + all packages.

---

## Status Sync (Optional v0.2)
- snag DONE contributes to step completion
- all must_pass steps GREEN ⇒ task can be DONE
