# UNICON — ANDROID APP FLOW (MVP v0.1)

## GOAL
Deliver a working MVP on Android that demonstrates:
- Snag list workflow
- Location matching (manual first, auto later)
- Tool auto-selection
- Simple pass/fail statuses
- Snapshot evidence per snag

No hardware integration beyond the phone at this stage.

---

## APP START
1. App opens
2. Show: SNAG LIST (TO DO / DOING / DONE)
3. Button: + NEW SNAG

---

## NEW SNAG (CREATE)
1. User taps: + NEW SNAG
2. App requests: take PHOTO
3. User enters:
   - title (short)
   - issue type (dropdown)
   - notes (optional)
4. App saves snag as: TO DO

Snag record contains:
- photo (path)
- issue_type
- created_time
- status

---

## SNAG LIST (MAIN)
Each snag row shows:
- small photo thumbnail
- title
- issue type
- status color (G/Y/R or none)

Actions:
- OPEN
- DONE

---

## OPEN SNAG (WORK MODE)
1. Show snag photo full-screen + issue text
2. Button: START CAMERA

---

## LOCATION MATCH (MVP v0.1)
MVP uses manual matching:
1. Camera opens
2. User aligns view visually with snag photo
3. User presses: PIN (anchor lock)

System shows:
- MATCH: MANUAL
- ANCHOR: LOCKED

Later versions will add auto image matching.

---

## TOOL AUTO-SELECTION
Tool is selected based on snag.issue_type:

- WORKTOP → 31_TOOL_WORKTOP_LEVEL_MEASURE
- FRAME  → 32_TOOL_FRAME_PLUMB_3D
- CUT    → 33_TOOL_CUT_MITRE_SAW
- GAPS   → 34_TOOL_DOOR_GAP_TOLERANCE
- HINGE  → 35_TOOL_HINGE_LOAD_CHECK
- FINAL  → 36_TOOL_FINAL_CLIENT_CHECK (aggregated view)

---

## TOOL RUN (GENERAL)
While tool is running:
- overlays are world-anchored to PIN point
- minimal HUD only
- numbers hidden by default
- color indicates tolerance (G/Y/R)

Buttons:
- DETAILS (hold)
- SNAP (save evidence)
- STATUS: OK / ATTENTION / ISSUE
- BACK

---

## SNAP / SAVE
When user taps SNAP:
- take screenshot / photo evidence
- save timestamp
- attach to snag record

---

## COMPLETE SNAG
User sets status:
- DONE if OK
- DOING if ATTENTION
- TO DO if ISSUE

Optional: add short note.

---

## RETURN
After save:
- return to snag list
- snag row updated with status color
