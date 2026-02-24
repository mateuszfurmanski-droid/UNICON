from pathlib import Path

# ===== UNICON HUD v1 config (single source of truth) =====
VERSION = "v1.1.0-turbo"
BUILT_UTC = "2025-12-30 20:15Z"

PORT = 8081
CAM_INDEX = 0
W, H = 640, 480

BASE = Path("/home/pi/UNICON/UNICON_CORE")
TOOLS_DIR = BASE / "tools"
PACKS_DIR = TOOLS_DIR / "packs"
ACTIVE_PACK_PATH = TOOLS_DIR / "active_pack.json"   # we will create if missing
ACTIVE_TOOL_PATH = TOOLS_DIR / "active_tool.json"

DEFAULT_PACK_ID = "carpentry"
DEFAULT_TOOL_ID = "DISTANCE_MEASURE"

# THEME
THEME_ENABLE = True
THEME_BG_ENABLE = False
THEME_BG_ALPHA = 0.22
THEME_GRID_ENABLE = True
THEME_VIGNETTE_ENABLE = True

HUD_BG_IMAGE = Path("/home/pi/UNICON/UNICON_DOCS/hud_mockups/mockup1.png")
