"""Clean-room M1 research implementation.

The package is intentionally independent from the historical project tree.
"""

from .config_loader import load_study, study_status
from .procedure_reference import ReferencePath, LineSegment, CircularArc
from .time_and_vertical import time_map, invert_time, kinematic_state
from .smooth_uncertainty import SEProcess, sample_error_pair
from .scenario_sync import synchronize_aircraft_states
from .aircraft_state import AircraftSpec, AircraftState, state_from_reference_and_error
from .generator import inspect_study, generate_formal_scenario

__all__ = [
    "load_study", "study_status", "ReferencePath", "LineSegment", "CircularArc",
    "time_map", "invert_time", "kinematic_state", "SEProcess",
    "sample_error_pair", "synchronize_aircraft_states", "AircraftSpec",
    "AircraftState", "state_from_reference_and_error", "inspect_study",
    "generate_formal_scenario",
]
