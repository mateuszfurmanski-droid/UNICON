# UNICON: Themes control ONLY visuals (colors/fonts/line widths/opacities) - placeholder
# Logic must not depend on theme.

from dataclasses import dataclass

@dataclass
class Theme:
    name: str = "DEWALT_INDUSTRIAL_LASER"
    line_width: int = 2
    font_px: int = 14
    opacity: float = 0.90
    # colors defined later (green/yellow/red + UI neutrals)
