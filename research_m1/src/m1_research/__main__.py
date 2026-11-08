"""Read-only exports from the single study configuration."""
import argparse
import json

from .aip_reference import build_16r_reference, build_16l_reference
from .config_loader import load_study
from .generator import inspect_study
from .scenario_sync import synthetic_pair, synchronize_aircraft_states


def reference_export():
    study = load_study()
    output = {"status": "PARTIAL_REFERENCE", "units": {"length": "m", "angle": "rad"}}
    for runway, build in (("16R", build_16r_reference), ("16L", build_16l_reference)):
        model = build(study)
        output[runway] = {key: value for key, value in model.items() if key != "path"}
        output[runway]["one_sided_boundaries"] = model["path"].boundary_states()
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "reference", "synthetic-pair"])
    command = parser.parse_args().command
    if command == "reference":
        result = reference_export()
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
