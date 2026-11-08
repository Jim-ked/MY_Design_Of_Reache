"""Read-only exports from the single study configuration."""
import argparse
import json

from .aip_reference import build_16r_reference, build_16l_reference
from .config_loader import load_study
from .generator import inspect_study, generate_conditional_nominal
from .scenario_sync import synthetic_pair, synchronize_aircraft_states


def reference_export(runway_only=None):
    study = load_study()
    output = {"status": "PARTIAL_REFERENCE", "units": {"length": "m", "angle": "rad"}}
    for runway, build in (("16R", build_16r_reference), ("16L", build_16l_reference)):
        if runway_only is not None and runway != runway_only:
            continue
        model = build(study)
        output[runway] = {key: value for key, value in model.items() if key != "path"}
        output[runway]["one_sided_boundaries"] = model["path"].boundary_states() if model["path"] is not None else None
    if runway_only is not None:
        output["status"] = output[runway_only]["status"]
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "reference", "reference-16r", "synthetic-pair", "nominal-conditional"])
    parser.add_argument("--delta-entry-s", type=float, help="explicit t_R_entry minus t_L_entry, scenario-relative seconds")
    args = parser.parse_args()
    command = args.command
    if command == "nominal-conditional" and args.delta_entry_s is None:
        parser.error("nominal-conditional requires --delta-entry-s")
    if command != "nominal-conditional" and args.delta_entry_s is not None:
        parser.error("--delta-entry-s applies only to nominal-conditional")
    if command == "reference":
        result = reference_export()
    elif command == "reference-16r":
        result = reference_export("16R")
    elif command == "nominal-conditional":
        try:
            result = generate_conditional_nominal(delta_entry_s=args.delta_entry_s)
        except ValueError as exc:
            parser.error(str(exc))
    elif command == "synthetic-pair":
        study = load_study()
        schedule = synthetic_pair(study)
        cuts = sorted({time for a in schedule.values() for time in (a.entry_s, a.exit_s)})
        result = {"status": "CONDITIONAL_NOMINAL", "scope": "SYNTHETIC_ONLY_NOT_TIANJIN",
                  "delta_t_entry_s": schedule["aircraft_02"].entry_s - schedule["aircraft_01"].entry_s,
                  "rows": synchronize_aircraft_states(schedule, cuts)}
    else:
        result = inspect_study()
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    main()
