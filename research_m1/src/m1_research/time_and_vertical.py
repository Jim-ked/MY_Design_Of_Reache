"""SI time mapping, vertical kinematics and explicit constraint blocking."""

import numpy as np


def _validate_grid(s_m: np.ndarray, values: np.ndarray, name: str) -> None:
    if s_m.ndim != 1 or values.shape != s_m.shape or len(s_m) < 2:
        raise ValueError(f"{name} arrays must have matching one-dimensional shape")
    if not np.all(np.isfinite(np.r_[s_m, values])) or np.any(np.diff(s_m) <= 0):
        raise ValueError(f"{name} arrays must be finite and strictly increasing in s")


def time_map(s_m: np.ndarray, horizontal_speed_mps: np.ndarray,
             entry_time_s: float = 0.0) -> np.ndarray:
    s = np.asarray(s_m, dtype=float)
    v = np.asarray(horizontal_speed_mps, dtype=float)
    _validate_grid(s, v, "time map")
    if not np.isfinite(entry_time_s) or np.any(v <= 0.0):
        raise ValueError("entry time must be finite and horizontal speed positive")
    ds = np.diff(s)
    slope = np.diff(v) / ds
    dt = np.empty_like(ds)
    flat = np.abs(slope) <= np.finfo(float).eps
    dt[flat] = ds[flat] / v[:-1][flat]
    dt[~flat] = np.log(v[1:][~flat] / v[:-1][~flat]) / slope[~flat]
    return np.r_[float(entry_time_s), float(entry_time_s) + np.cumsum(dt)]


def invert_time(time_s: np.ndarray, s_m: np.ndarray, query_time_s: np.ndarray,
                horizontal_speed_mps: np.ndarray | None = None) -> np.ndarray:
    t = np.asarray(time_s, dtype=float)
    s = np.asarray(s_m, dtype=float)
    q = np.asarray(query_time_s, dtype=float)
    if t.ndim != 1 or s.shape != t.shape or len(t) < 2:
        raise ValueError("time and s arrays must have matching one-dimensional shape")
    if np.any(~np.isfinite(np.r_[t, s, q])) or np.any(np.diff(t) <= 0) or np.any(np.diff(s) <= 0):
        raise ValueError("time and s must be finite and strictly increasing")
    if np.any(q < t[0]) or np.any(q > t[-1]):
        raise ValueError("time query outside active support")
    if horizontal_speed_mps is None:
        return np.interp(q, t, s)
    v = np.asarray(horizontal_speed_mps, dtype=float)
    if v.shape != s.shape or np.any(~np.isfinite(v)) or np.any(v <= 0):
        raise ValueError("horizontal speed must match s and remain positive")
    index = np.clip(np.searchsorted(t, q, side="right") - 1, 0, len(t) - 2)
    dt = q - t[index]
    ds = s[index + 1] - s[index]
    slope = (v[index + 1] - v[index]) / ds
    flat = np.abs(slope) <= np.finfo(float).eps
    distance = np.empty_like(q)
    distance[flat] = v[index[flat]] * dt[flat]
    distance[~flat] = v[index[~flat]] * np.expm1(slope[~flat] * dt[~flat]) / slope[~flat]
    return s[index] + distance


def kinematic_state(horizontal_speed_mps: np.ndarray, d_speed_ds_mps_per_m: np.ndarray,
                    height_m: np.ndarray, d_height_ds: np.ndarray,
                    d2_height_ds2: np.ndarray) -> dict[str, np.ndarray]:
    v = np.asarray(horizontal_speed_mps, dtype=float)
    dv = np.asarray(d_speed_ds_mps_per_m, dtype=float)
    h = np.asarray(height_m, dtype=float)
    slope = np.asarray(d_height_ds, dtype=float)
    curvature = np.asarray(d2_height_ds2, dtype=float)
    if not (v.shape == dv.shape == h.shape == slope.shape == curvature.shape):
        raise ValueError("kinematic arrays must have equal shape")
    if np.any(~np.isfinite(np.r_[v, dv, h, slope, curvature])) or np.any(v <= 0):
        raise ValueError("kinematic arrays must be finite and speed positive")
    gamma = np.arctan(slope)
    return {
        "horizontal_speed_mps": v,
        "vertical_speed_mps": v * slope,
        "path_angle_rad": gamma,
        "path_angle_rate_rad_s": v * curvature / (1.0 + slope * slope),
        "vertical_accel_mps2": v * v * curvature + v * dv * slope,
    }


def resolve_height_constraints(constraints: list[dict]) -> dict[str, object]:
    """Return a blocker instead of inventing a height profile."""
    if not constraints:
        return {"status": "CONSTRAINT_CONFLICT", "reason": "no sourced constraints supplied"}
    unresolved = [item for item in constraints if item.get("height_m") is None
                  or item.get("status") in {"UNRESOLVED", "SOURCE_RECONCILIATION_REQUIRED"}]
    if unresolved:
        return {"status": "CONSTRAINT_CONFLICT", "reason": "height constraint evidence is incomplete"}
    return {"status": "CONDITIONAL", "reason": "constraints are numerically available; aircraft feasibility remains separate"}
