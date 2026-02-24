# UNICON CORE PACK (v0.1)

## What this is
Universal, platform-agnostic specification pack for UNICON.
Contains:
- style tokens
- tool registry
- tool selection rules
- snag schema + examples

## How to use
Any client (Android/iOS/Web/Desktop) can:
1) load SNAG_LIST
2) select snag
3) choose tool via tool_selector_rules (issue_type → tool_id)
4) render overlays according to tool docs + style_tokens
5) store results back into snag record

## No code here
This pack intentionally has no platform code to avoid lock-in.
