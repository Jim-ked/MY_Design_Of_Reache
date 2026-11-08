"""Absolute-time state evaluation and activity-aware synchronization."""

from collections.abc import Callable, Sequence
from typing import Any
from dataclasses import dataclass
import math

from .aircraft_state import AircraftState


@dataclass(frozen=True)
class ScheduledAircraft:
    aircraft_id: str
    scenario_id: str
    entry_s: float
    exit_s: float
    evaluate_active: Callable[[float], AircraftState]

    def __post_init__(self):
        if not math.isfinite(self.entry_s) or not math.isfinite(self.exit_s) or self.exit_s <= self.entry_s:
            raise ValueError("invalid scheduled active domain")

    def __call__(self, time_s):
        if not self.entry_s <= time_s <= self.exit_s:
            return None
        return self.evaluate_active(time_s)


def synchronize_aircraft_states(
    evaluators: dict[str, Callable[[float], AircraftState]],
    time_grid_s: Sequence[float],
) -> list[dict[str, Any]]:
    """Evaluate each aircraft at common absolute times without extrapolation."""
    times = [float(value) for value in time_grid_s]
    if not evaluators or not times or not all(map(math.isfinite, times)) or any(not (times[i] < times[i + 1]) for i in range(len(times) - 1)):
        raise ValueError("time grid must be nonempty and strictly increasing")
    rows: list[dict[str, Any]] = []
    for time_s in times:
        states: dict[str, dict[str, Any]] = {}
        active_ids: list[str] = []
        for aircraft_id, evaluator in evaluators.items():
            state = evaluator(time_s)
            if state is None:
                states[aircraft_id] = {"aircraft_id": aircraft_id, "time_abs_s": time_s, "active": False,
                                       "position_m": None, "velocity_mps": None}
                continue
            if state.aircraft_id != aircraft_id or state.time_abs_s != time_s:
                raise ValueError("aircraft identity or evaluation time mismatch")
            states[aircraft_id] = state.as_dict()
            if state.active:
                active_ids.append(aircraft_id)
        relative = None
        if len(evaluators) == 2 and len(active_ids) == 2:
            first, second = (states[key] for key in evaluators)
            if first["scenario_id"] != second["scenario_id"]:
                raise ValueError("pair must belong to the same scenario")
            relative = {"definition": "second minus first in evaluator order",
                        "delta_position_m": [second[key] - first[key] for key in ("east_m", "north_m", "altitude_msl_m")],
                        "delta_velocity_mps": [second[key] - first[key] for key in ("velocity_e_mps", "velocity_n_mps", "velocity_u_mps")]}
        rows.append({"time_abs_s": time_s, "states": states, "relative_state": relative,
                     "pair_active": len(active_ids) == len(evaluators),
                     "active_aircraft_ids": active_ids})
    return rows


def synthetic_pair(study):
    """Explicit synthetic-only kinematics on arbitrary straight test paths."""
    from .aircraft_state import state_from_reference_and_error
    from .procedure_reference import ReferencePath, LineSegment
    demo = study["operations"]["synthetic_demo"]
    assignments = study["scenarios"][0]["assignments"]
    evaluators = {}
    for index, assignment in enumerate(assignments):
        aircraft_id = assignment["aircraft_id"]
        entry = demo["t_entry_s"][aircraft_id]
        duration = demo["duration_s"][aircraft_id]
        speed = demo["horizontal_speed_mps"][aircraft_id]
        height = demo["altitude_msl_m"][aircraft_id]
        path = ReferencePath([LineSegment(duration * speed, (index * 100., 0.), 0., "SYNTHETIC_TF")])
        kind = next(a["aircraft_type"] for a in study["aircraft"] if a["aircraft_id"] == aircraft_id)
        def evaluate(t, aid=aircraft_id, entry=entry, speed=speed, height=height, path=path, kind=kind, assignment=assignment):
            return state_from_reference_and_error(
                path=path, aircraft_id=aid, scenario_id="case_001",
                procedure_id=assignment["procedure_id"], aircraft_type=kind,
                time_abs_s=t, s_m=(t-entry)*speed, altitude_msl_m=height,
                d_height_ds=0., horizontal_speed_mps=speed, e_n_m=0., e_z_m=0.,
                de_n_dt_mps=0., de_z_dt_mps=0., model_status="CONDITIONAL_NOMINAL",
                provenance_id="synthetic-interface-only-not-Tianjin")
        evaluators[aircraft_id] = ScheduledAircraft(aircraft_id, "case_001", entry, entry+duration, evaluate)
    return evaluators
