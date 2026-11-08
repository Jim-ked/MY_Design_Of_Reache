"""Named aircraft and state records for the clean-room interface."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from .procedure_reference import ReferencePath


@dataclass(frozen=True)
class AircraftSpec:
    aircraft_id: str
    aircraft_class: str
    aircraft_type: str
    mass_kg: float | None
    configuration: str | None
    navigation_qualification: str | None
    performance_evidence: Any

    def performance_status(self) -> str:
        if self.mass_kg is None or self.configuration is None or self.performance_evidence is None:
            return "PERFORMANCE_UNQUALIFIED"
        if self.aircraft_class == "rpas" and self.navigation_qualification != "qualified":
            return "PERFORMANCE_UNQUALIFIED"
        return "CONDITIONAL"


@dataclass(frozen=True)
class AircraftState:
    aircraft_id: str
    scenario_id: str
    procedure_id: str
    aircraft_type: str
    time_abs_s: float
    s_m: float
    east_m: float
    north_m: float
    altitude_msl_m: float
    velocity_e_mps: float
    velocity_n_mps: float
    velocity_u_mps: float
    active: bool
    model_status: str
    provenance_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "aircraft_id": self.aircraft_id,
            "scenario_id": self.scenario_id,
            "procedure_id": self.procedure_id,
            "aircraft_type": self.aircraft_type,
            "time_abs_s": float(self.time_abs_s),
            "s_m": float(self.s_m),
            "east_m": float(self.east_m),
            "north_m": float(self.north_m),
            "altitude_msl_m": float(self.altitude_msl_m),
            "velocity_e_mps": float(self.velocity_e_mps),
            "velocity_n_mps": float(self.velocity_n_mps),
            "velocity_u_mps": float(self.velocity_u_mps),
            "active": bool(self.active),
            "model_status": self.model_status,
            "provenance_id": self.provenance_id,
        }


def state_from_components(*, aircraft_id: str, scenario_id: str,
                          procedure_id: str, aircraft_type: str,
                          time_abs_s: float, s_m: float, position_m: np.ndarray,
                          velocity_mps: np.ndarray, active: bool,
                          model_status: str, provenance_id: str) -> AircraftState:
    position = np.asarray(position_m, dtype=float)
    velocity = np.asarray(velocity_mps, dtype=float)
    if position.shape != (3,) or velocity.shape != (3,):
        raise ValueError("position and velocity must be three-vectors")
    if not np.all(np.isfinite(np.r_[position, velocity, time_abs_s, s_m])):
        raise ValueError("state components must be finite")
    return AircraftState(
        aircraft_id=aircraft_id, scenario_id=scenario_id,
        procedure_id=procedure_id, aircraft_type=aircraft_type,
        time_abs_s=float(time_abs_s), s_m=float(s_m),
        east_m=float(position[0]), north_m=float(position[1]),
        altitude_msl_m=float(position[2]), velocity_e_mps=float(velocity[0]),
        velocity_n_mps=float(velocity[1]), velocity_u_mps=float(velocity[2]),
        active=bool(active), model_status=model_status,
        provenance_id=provenance_id,
    )


def state_from_reference_and_error(*, path: ReferencePath,
                                   aircraft_id: str, scenario_id: str,
                                   procedure_id: str, aircraft_type: str,
                                   time_abs_s: float, s_m: float,
                                   altitude_msl_m: float, d_height_ds: float,
                                   horizontal_speed_mps: float,
                                   e_n_m: float, e_z_m: float,
                                   de_n_dt_mps: float, de_z_dt_mps: float,
                                   model_status: str,
                                   provenance_id: str) -> AircraftState:
    """Construct nominal-plus-error state from one shared spatial/time model."""
    if horizontal_speed_mps <= 0 or not np.isfinite(horizontal_speed_mps):
        raise ValueError("horizontal speed must be positive and finite")
    path.require_continuity()
    ref = path.evaluate(float(s_m))
    tangent = np.array([ref["tangent_east"], ref["tangent_north"]], dtype=float)
    normal = np.array([ref["normal_east"], ref["normal_north"]], dtype=float)
    curvature = float(ref["curvature_1_m"])
    position = np.array([
        ref["east_m"] + e_n_m * normal[0],
        ref["north_m"] + e_n_m * normal[1],
        altitude_msl_m + e_z_m,
    ])
    horizontal_velocity = horizontal_speed_mps * (1.0 - curvature * e_n_m) * tangent
    horizontal_velocity += de_n_dt_mps * normal
    velocity = np.array([
        horizontal_velocity[0], horizontal_velocity[1],
        horizontal_speed_mps * d_height_ds + de_z_dt_mps,
    ])
    return state_from_components(
        aircraft_id=aircraft_id, scenario_id=scenario_id,
        procedure_id=procedure_id, aircraft_type=aircraft_type,
        time_abs_s=time_abs_s, s_m=s_m, position_m=position,
        velocity_mps=velocity, active=True,
        model_status=model_status, provenance_id=provenance_id,
    )
