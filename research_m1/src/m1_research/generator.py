"""Conservative entry points for the unified generator."""

from typing import Any

from .config_loader import load_study, study_status
from .time_and_vertical import resolve_height_constraints


def inspect_study() -> dict[str, Any]:
    """Return a status report without manufacturing a formal trajectory."""
    study = load_study()
    procedure_status = {
        item["procedure_id"]: {
            "reference_geometry": item.get("review_status", "UNRESOLVED"),
            "height_constraints": resolve_height_constraints(item.get("constraints") or []),
        }
        for item in study["procedures"]
    }
    aircraft_status = {
        item["aircraft_id"]: "PERFORMANCE_UNQUALIFIED"
        if item.get("status") != "SUPPORTED" else "CONDITIONAL"
        for item in study["aircraft"]
    }
    uncertainty_status = study["uncertainty"]["axes"]
    return {
        "status": study_status(study),
        "procedures": procedure_status,
        "aircraft": aircraft_status,
        "uncertainty": {
            "N": uncertainty_status["N"]["status"],
            "Z": uncertainty_status["Z"]["status"],
        },
        "formal_generation_allowed": False,
        "reason": "required source, performance and statistical parameters remain unresolved",
    }


def generate_formal_scenario(scenario_id: str) -> dict[str, Any]:
    """Return an explicit blocker instead of fabricating a formal trajectory."""
    study = load_study()
    scenario = next((item for item in study["scenarios"]
                     if item["scenario_id"] == scenario_id), None)
    if scenario is None:
        return {"status": "CONSTRAINT_CONFLICT", "scenario_id": scenario_id,
                "trajectory": None, "reason": "unknown scenario_id"}
    report = inspect_study()
    return {
        "status": "PARTIAL_REFERENCE",
        "scenario_id": scenario_id,
        "trajectory": None,
        "reason": report["reason"],
        "blockers": [
            "G1_PROGRAM unresolved",
            "G2_AIRCRAFT unresolved",
            "G4_STOCHASTIC unresolved",
        ],
    }
