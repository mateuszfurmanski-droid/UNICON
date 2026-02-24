# UNICON: Layout control ONLY placement (where elements render) - placeholder
# This enables themes that also reposition HUD blocks without touching logic.

from dataclasses import dataclass

@dataclass
class Layout:
    name: str = "PHONE_V0"
    # later: margins, bottom panels positions, etc.
