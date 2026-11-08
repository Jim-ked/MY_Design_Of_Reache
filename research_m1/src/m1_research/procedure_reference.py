"""Independent reference geometry primitives and one-sided boundary states."""

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class LineSegment:
    length_m: float
    start_xy_m: tuple[float, float]
    heading_rad: float
    segment_id: str

    def evaluate(self, local_s_m: float) -> tuple[np.ndarray, np.ndarray, float]:
        u = np.array([math.sin(self.heading_rad), math.cos(self.heading_rad)])
        p = np.asarray(self.start_xy_m, dtype=float) + local_s_m * u
        return p, u, 0.0


@dataclass(frozen=True)
class CircularArc:
    radius_m: float
    sweep_rad: float
    center_xy_m: tuple[float, float]
    start_angle_rad: float
    direction: int
    segment_id: str

    @property
    def length_m(self) -> float:
        return abs(self.radius_m * self.sweep_rad)

    def evaluate(self, local_s_m: float) -> tuple[np.ndarray, np.ndarray, float]:
        direction = 1 if self.direction >= 0 else -1
        angle = self.start_angle_rad + direction * local_s_m / self.radius_m
        radial = np.array([math.cos(angle), math.sin(angle)])
        tangent = direction * np.array([-math.sin(angle), math.cos(angle)])
        point = np.asarray(self.center_xy_m, dtype=float) + self.radius_m * radial
        return point, tangent, direction / self.radius_m


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    kind: str
    interval_s_m: tuple[float, float] | None
    height_m: float | None
    source_ref: str | None
    status: str


class ReferencePath:
    """Piecewise reference path with analytic tangent and curvature."""

    def __init__(self, segments: list[LineSegment | CircularArc],
                 constraints: list[Constraint] | None = None):
        if not segments:
            raise ValueError("at least one reference segment is required")
        self.segments = tuple(segments)
        self.constraints = tuple(constraints or ())
        self._starts = np.r_[0.0, np.cumsum([segment.length_m for segment in segments])]
        if np.any(~np.isfinite(self._starts)) or np.any(np.diff(self._starts) <= 0):
            raise ValueError("segment lengths must be finite and positive")
        self.length_m = float(self._starts[-1])

    def _segment_index(self, s_m: float, side: str) -> int:
        if not np.isfinite(s_m) or not 0.0 <= s_m <= self.length_m:
            raise ValueError("s must lie inside reference support")
        if side not in ("left", "right"):
            raise ValueError("side must be left or right")
        if s_m == self.length_m:
            return len(self.segments) - 1
        if s_m == 0.0:
            return 0
        index = int(np.searchsorted(self._starts, s_m, side="right") - 1)
        if s_m in self._starts[1:-1] and side == "left":
            index -= 1
        return max(0, min(index, len(self.segments) - 1))

    def evaluate(self, s_m: float, side: str = "right") -> dict[str, object]:
        index = self._segment_index(float(s_m), side)
        local = float(s_m) - float(self._starts[index])
        point, tangent, curvature = self.segments[index].evaluate(local)
        tangent = np.asarray(tangent, dtype=float)
        tangent /= np.linalg.norm(tangent)
        normal = np.array([-tangent[1], tangent[0]])
        return {
            "s_m": float(s_m),
            "east_m": float(point[0]),
            "north_m": float(point[1]),
            "tangent_east": float(tangent[0]),
            "tangent_north": float(tangent[1]),
            "normal_east": float(normal[0]),
            "normal_north": float(normal[1]),
            "curvature_1_m": float(curvature),
            "segment_id": self.segments[index].segment_id,
            "segment_index": index,
        }

    def boundary_states(self) -> list[dict[str, object]]:
        states = []
        for index, s_m in enumerate(self._starts):
            if index == 0:
                states.append(self.evaluate(float(s_m), "right"))
            elif index == len(self._starts) - 1:
                states.append(self.evaluate(float(s_m), "left"))
            else:
                states.append({
                    "s_m": float(s_m),
                    "left": self.evaluate(float(s_m), "left"),
                    "right": self.evaluate(float(s_m), "right"),
                })
        return states

    def require_continuity(self, position_tolerance_m=1e-5, tangent_tolerance=1e-8):
        """Check every boundary before a caller constructs a continuous state.

        Curvature may step. A position gap, reversed tangent or corner cannot
        be interpreted as a single position-time execution path.
        """
        if not np.all(np.isfinite([position_tolerance_m, tangent_tolerance])) or min(position_tolerance_m, tangent_tolerance) <= 0:
            raise ValueError("continuity check tolerances must be finite and positive")
        boundaries = []
        for first, second in zip(self.segments[:-1], self.segments[1:]):
            pa, ta, _ = first.evaluate(first.length_m)
            pb, tb, _ = second.evaluate(0.)
            position_gap = float(np.linalg.norm(np.asarray(pb)-pa))
            ta, tb = np.asarray(ta), np.asarray(tb)
            tangent_gap = float(np.linalg.norm(ta/np.linalg.norm(ta)-tb/np.linalg.norm(tb)))
            boundaries.append({"left": first.segment_id, "right": second.segment_id,
                               "position_gap_m": position_gap, "tangent_vector_difference": tangent_gap})
            if not np.isfinite(position_gap+tangent_gap) or position_gap > position_tolerance_m or tangent_gap > tangent_tolerance:
                raise ValueError("SOURCE_GEOMETRY_CONFLICT: discontinuous boundary " + str(boundaries[-1]))
        return {"continuous": True, "boundaries": boundaries,
                "position_tolerance_m": position_tolerance_m, "tangent_vector_tolerance": tangent_tolerance}


def constraint_status(constraints: list[Constraint]) -> str:
    """Return the conservative status for unresolved or conflicting limits."""
    if not constraints:
        return "CONSTRAINT_CONFLICT"
    if any(item.status in {"UNRESOLVED", "SOURCE_RECONCILIATION_REQUIRED"}
           or item.height_m is None for item in constraints):
        return "CONSTRAINT_CONFLICT"
    return "CONDITIONAL"
