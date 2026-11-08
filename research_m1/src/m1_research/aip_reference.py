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


def _right_sweep(start: float, end: float) -> float:
    # ENU angles increase counterclockwise. The coding page explicitly says R.
    return (start - end) % (2.0 * math.pi)


def _aip_frame(study: dict[str, Any]) -> ENUFrame:
    reference = study["airport"]["reference_frame"]
    if any(reference[key] is None for key in ("arp_latitude_deg", "arp_longitude_deg", "arp_elevation_m")):
        raise ValueError("ARP evidence is required to construct the ENU frame")
    return ENUFrame(reference["arp_latitude_deg"], reference["arp_longitude_deg"],
                    reference["arp_elevation_m"])


def build_16r_reference(study: dict[str, Any] | None = None) -> dict[str, Any]:
    study = load_study() if study is None else study
    frame = _aip_frame(study)
    raw = study["procedures"][1]["reference_geometry"]["points"]
    if study["procedures"][1]["reference_geometry"]["rf_direction"] != "right":
        raise ValueError("source-defined right RF direction required")
    center = _point(frame, raw["TJC01"])
    points = {name: _point(frame, value) for name, value in raw.items() if name != "TJC01"}
    radius_m = float(study["procedures"][1]["reference_geometry"]["rf_radius_nm"]) * 1852.0
    def angle(name: str) -> float:
        delta = points[name] - center
        return float(math.atan2(delta[1], delta[0]))
    sweep_1 = _right_sweep(angle("TJ907"), angle("TJ906"))
    sweep_2 = _right_sweep(angle("TJ906"), angle("TJ903"))
    arc_1 = CircularArc(radius_m, sweep_1, tuple(center), angle("TJ907"), -1, "RF1")
    arc_2 = CircularArc(radius_m, sweep_2, tuple(center), angle("TJ906"), -1, "RF2")
    end_arc_2 = arc_2.evaluate(arc_2.length_m)[0]
    # Preserve the encoded TF endpoints. A gap from the exact coded RF circle
    # is an unresolved source inconsistency, not permission to move TJ903.
    tf_vector = points["RW16R"] - points["TJ903"]
    tf_length = float(np.linalg.norm(tf_vector))
    tf_heading = float(math.atan2(tf_vector[0], tf_vector[1]))
    tf = LineSegment(tf_length, tuple(points["TJ903"]), tf_heading, "TF")
    path = ReferencePath([arc_1, arc_2, tf])
    return {
        "status": "PARTIAL_REFERENCE",
        "reference_frame": "ZBTJ_ENU_ARP",
        "path": path,
        "events": {
            "TJ907": 0.0,
            "TJ906": arc_1.length_m,
            "TJ903": arc_1.length_m + arc_2.length_m,
            "RW16R": path.length_m,
        },
        "derived": {
            "rf_radius_m": radius_m,
            "rf1_length_m": arc_1.length_m,
            "rf2_length_m": arc_2.length_m,
            "tf_length_m": tf_length,
            "tj903_endpoint_residual_m": float(np.linalg.norm(end_arc_2 - points["TJ903"])),
            "radial_residuals_m": {name: float(np.linalg.norm(points[name] - center) - radius_m)
                                   for name in ("TJ907", "TJ906", "TJ903")},
            "rf_tf_position_gap_m": float(np.linalg.norm(end_arc_2 - points["TJ903"])),
            "tf_endpoint_residual_m": float(np.linalg.norm(tf.evaluate(tf.length_m)[0] - points["RW16R"])),
        },
        "segment_sources": {"RF1": ["H01_4Y01", "H01_4Z18"],
                            "RF2": ["H01_4Y01", "H01_4Z18"], "TF": ["H01_4Y01", "H01_4Z18"]},
        "path_source": ["H01_4Y01", "H01_4Z18", "H01_2A_2025"],
        "formal_status": "PARTIAL_REFERENCE",
        "executable_continuous_path": False,
        "limitations": ["coded radius and fix coordinates do not close; no radius fitting performed",
                        "ARP page date compatibility unverified; no vertical execution model"],
    }


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
