# UNICON: Measurement state model (anchors/lines/angles) - placeholder for V0 modularization
# Keep this as the single "source of truth" for measurement objects.

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Vec2 = Tuple[float, float]

@dataclass
class Anchor:
    id: str
    x: float
    y: float
    # later: depth/z, confidence, timestamp, etc.

@dataclass
class MeasureLine:
    id: str
    a_id: str
    b_id: str
    value_mm: Optional[float] = None
    color_state: str = "green"  # green/yellow/red

@dataclass
class HudState:
    anchors: Dict[str, Anchor] = field(default_factory=dict)
    lines: Dict[str, MeasureLine] = field(default_factory=dict)
