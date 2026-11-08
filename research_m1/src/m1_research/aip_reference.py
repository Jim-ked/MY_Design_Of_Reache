"""Build partial reference geometry directly from the clean-room AIP fields."""

import math
from typing import Any

import numpy as np

from .config_loader import load_study
from .geodesy import ENUFrame, parse_dms
from .procedure_reference import CircularArc, LineSegment, ReferencePath


def _point(frame: ENUFrame, value: dict[str, Any]) -> np.ndarray:
    lat, lon = parse_dms(value)
    return frame.to_enu(lat, lon)[:2]


def _aip_frame(study: dict[str, Any]) -> ENUFrame:
    reference = study["airport"]["reference_frame"]
    if any(reference[key] is None for key in ("arp_latitude_deg", "arp_longitude_deg", "arp_elevation_m")):
        raise ValueError("ARP evidence is required to construct the ENU frame")
    return ENUFrame(reference["arp_latitude_deg"], reference["arp_longitude_deg"],
                    reference["arp_elevation_m"])


def build_16r_reference(study: dict[str, Any] | None = None) -> dict[str, Any]:
    """A conditional printed-precision representative, never database truth."""
    from .rf_precision import solve_rf_precision
    study = load_study() if study is None else study
    frame = _aip_frame(study)
    geometry = next(item["reference_geometry"] for item in study["procedures"]
                    if item["procedure_id"] == "ZBTJ_RWY16R_RNP_Y_AR")
    raw = geometry["points"]
    hypothesis = geometry["rounding_hypothesis"]
    if geometry["rf_direction"] != "right":
        return {"status": "SOURCE_GEOMETRY_CONFLICT", "path": None,
                "reason": "source-defined right RF direction required"}
    solution = solve_rf_precision(raw, frame,
        coordinate_half_unit_arcsec=hypothesis["coordinate_half_unit_arcsec"],
        radius_interval_nm=hypothesis["radius_interval_nm"],
        displayed_radius_nm=geometry["rf_radius_nm"],
        radius_display_resolution_nm=hypothesis.get("radius_display_resolution_nm"),
        radius_rounding_rule=hypothesis.get("radius_rounding_rule"),
        radius_interval_closure=hypothesis.get("radius_interval_closure"))
    output = {"status": solution["status"], "rounding_solution": solution,
              "full_nominal_status": "UNRESOLVED", "reference_frame": "ZBTJ_ENU_ARP",
              "path": None, "formal_status": solution["status"],
              "segment_sources": {"RF1": ["H01_4Y01", "H01_4Z18"],
                                  "RF2": ["H01_4Y01", "H01_4Z18"], "TF": ["H01_4Y01", "H01_4Z18"]},
              "path_source": ["H01_4Y01", "H01_4Z18", "USER_RF_PRECISION_ADJUDICATION_20261108"],
              "limitations": ["rounding hypothesis is conditional; representative not a unique database path",
                              "LTP, vertical execution and cross-date frame compatibility remain unresolved"]}
    if solution["status"] != "CONDITIONAL_REFERENCE_GEOMETRY":
        return output
    xy = {key: np.asarray(value) for key, value in solution["reconstructed_xy_m"].items()}
    center, radius = xy["TJC01"], solution["radius_m"]
    def angle(name):
        delta = xy[name]-center
        return float(math.atan2(delta[1], delta[0]))
    arc_1 = CircularArc(radius, solution["right_sweeps_rad"][0], tuple(center), angle("TJ907"), -1, "RF1")
    arc_2 = CircularArc(radius, solution["right_sweeps_rad"][1], tuple(center), angle("TJ906"), -1, "RF2")
    delta = xy["RW16R"]-xy["TJ903"]
    tf = LineSegment(float(np.linalg.norm(delta)), tuple(xy["TJ903"]), math.atan2(delta[0], delta[1]), "TF")
    path = ReferencePath([arc_1, arc_2, tf])
    try:
        continuity = path.require_continuity()
    except ValueError as exc:
        output.update(status="SOURCE_GEOMETRY_CONFLICT", reason=str(exc))
        return output
    raw_center = _point(frame, raw["TJC01"])
    raw_radii = {name: float(np.linalg.norm(_point(frame, raw[name])-raw_center))
                 for name in ("TJ907", "TJ906", "TJ903")}
    naive_gap = abs(geometry["rf_radius_nm"]*1852.-raw_radii["TJ903"])
    output.update({"path": path, "horizontal_continuity": continuity,
                   "continuous_reference_available": True,
                   "events": {"TJ907": 0., "TJ906": arc_1.length_m,
                              "TJ903": arc_1.length_m+arc_2.length_m, "RW16R": path.length_m},
                   "derived": {"rf_radius_m": radius, "rf1_length_m": arc_1.length_m,
                               "rf2_length_m": arc_2.length_m, "tf_length_m": tf.length_m,
                               "rf_tf_position_gap_m": continuity["boundaries"][1]["position_gap_m"]},
                   "printed_value_diagnostic": {"printed_center_distances_m": raw_radii,
                       "exact_2p7_algorithm_gap_m": naive_gap,
                       "interpretation": "an exact-display-value algorithm artifact, not an unavoidable AIP geometry conflict"}})
    return output


def build_16l_reference(study: dict[str, Any] | None = None) -> dict[str, Any]:
    study = load_study() if study is None else study
    frame = _aip_frame(study)
    geometry = study["procedures"][0]["reference_geometry"]
    raw = geometry["points"]
    loc = _point(frame, raw["LOC16L"])
    dme = _point(frame, raw["DME16L"])
    im = _point(frame, raw["IM16L"])
    # True azimuth is defined locally at LOC, then projected into the ARP ENU.
    loc_lat, loc_lon = parse_dms(raw["LOC16L"])
    local_frame = ENUFrame(loc_lat, loc_lon, frame.height_m)
    azimuth = math.radians(geometry["true_course_deg"])
    u = (frame.rotation @ local_frame.rotation.T @ np.array([math.sin(azimuth), math.cos(azimuth), 0.0]))[:2]
    u /= np.linalg.norm(u)
    threshold = loc - u * (geometry["runway_length_m"] + geometry["loc_beyond_runway_end_m"])
    # Conditional DME *horizontal* range intersection. Slant range cannot be
    # fixed without resolved altitude/antenna datum and is not silently assumed.
    radius = geometry["faf_dme_nm"] * 1852.0
    delta = threshold - dme
    b = float(np.dot(delta, u))
    discriminant = b * b - float(np.dot(delta, delta)) + radius * radius
    if discriminant <= 0:
        raise ValueError("DME circle does not intersect the LOC axis")
    final_length = b + math.sqrt(discriminant)
    faf = threshold - u * final_length
    path = ReferencePath([LineSegment(final_length, tuple(faf), math.atan2(u[0], u[1]), "LOC_FINAL")])
    return {
        "status": "PARTIAL_REFERENCE",
        "reference_frame": "ZBTJ_ENU_ARP",
        "path": path,
        "station_origin": "conditional FAF on LOC final only; global s from TJ954 unresolved",
        "events": {"IF": None, "FAF": 0.0, "THR": final_length},
        "derived": {
            "final_length_m": final_length,
            "IF_to_LOC_gap_length_m": None,
            "threshold_from_loc_xy_m": threshold.tolist(),
            "threshold_from_im_residual_m": float(np.linalg.norm(threshold - (im + u * geometry["im_before_threshold_m"]))),
            "published_fap_s_m": None,
            "published_gp_capture_s_m": None,
        },
        "segment_sources": {"LOC_FINAL": ["H01_AD2025:p12,p17,p18", "H01_5A"]},
        "path_source": ["H01_AD2025", "H01_5A", "H01_2A_2025"],
        "formal_status": "PARTIAL_REFERENCE",
        "limitations": ["RNAV access geometry unknown; no constructed connector",
                        "2024/2025 page compatibility unresolved", "DME horizontal approximation is conditional, not slant range"],
    }
