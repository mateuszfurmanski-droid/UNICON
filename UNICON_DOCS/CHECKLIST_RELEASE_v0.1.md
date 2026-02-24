# UNICON — RELEASE CHECKLIST (v0.1)

Status meanings:
- [x] Done / locked
- [ ] Missing / to do
- [!] Exists but needs review

---

## 1) Project structure
- [x] Root folder: UNICON_PROJECT
- [x] UNICON_CORE exists
- [x] UNICON_DOCS exists
- [x] Main README.md exists and describes system

---

## 2) Core pack (platform-agnostic)
- [x] core_manifest.json present
- [x] style_tokens.json present (TXT_HUD_90S_THIN_GREEN)
- [x] tool_registry.json present (tools 31–36)
- [x] tool_selector_rules.json present (issue_type → tool_id)
- [x] No platform code in UNICON_CORE (LOCK)

LOCK:
- Core pack files should not be changed without bumping core_version.

---

## 3) Roles & workflow (site-realistic)
- [x] ROLE_AND_TASK_FLOW.md present (LOCK: installer sees assigned tasks only)
- [x] README.md includes Roles and Task Assignment section

LOCK:
- Installer does NOT see full project snag list
- Manager assigns task packages
- Tools and tolerances are not chosen by installer

---

## 4) Data model
- [x] SNAG_DATA_SCHEMA.json present
- [x] SNAG schema includes assignment: package_id / task_id / step_id
- [x] SNAG_LIST_EXAMPLE.json present
- [x] SNAG_LIST_ASSIGNED_pkg-joinery-doors-001.json present
- [x] TASK_PACKAGE_EXAMPLE_DOORS_HANDLES_FIRE.json present
- [x] TASK_TO_SNAG_RULES.md present

---

## 5) Tool documentation
- [!] Tool docs 31–36 exist in UNICON_DOCS (check filenames match registry)
- [ ] Preview PNGs exist for each tool (optional for release, required for demo deck)

Recommended:
- Tool docs should include:
  - required inputs
  - outputs / tolerances
  - minimal HUD overlays behavior
  - evidence requirements

---

## 6) Demo readiness
- [x] Demo scenario defined (tasks → snags → tools → evidence → status)
- [ ] DEMO_SCRIPT_3MIN.md (read-out script) created
- [ ] Demo assets folder (photos placeholders) created:
  - photos/worktop_ref_001.jpg
  - photos/frame_ref_001.jpg
  - photos/gaps_ref_001.jpg
  - photos/door1_frame_ref.jpg, etc.

---

## 7) Release packaging
- [ ] Zip export created (UNICON_PROJECT_v0.1.zip)
- [ ] Release note created (RELEASE_NOTES_v0.1.md)

---

## 8) Next upgrade targets (v0.2)
- [ ] Add “must_pass” propagation into generated snags
- [ ] Add evidence requirements per step into snag schema (optional)
- [ ] Add simple “HANDLE HEIGHT CHECK” tool (new tool_id)
- [ ] Add auto photo relocalization (future, not MVP)

---

## FINAL CHECK (manual)
- [ ] Open README.md and verify it explains system in 60 seconds
- [ ] Open SNAG_LIST_ASSIGNED and verify every snag has:
  - tool_id
  - issue_type
  - package_id/task_id/step_id
- [ ] Open tool_registry and confirm doc filenames match actual docs

If all above pass:
✅ Release v0.1 can be frozen.
