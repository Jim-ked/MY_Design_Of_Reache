"""SI time mapping, vertical kinematics and explicit constraint blocking."""

import numpy as np
from dataclasses import dataclass


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


@dataclass
class ConditionalHeightProfile:
    """Only the user-adjudicated quadratic example; not a constraint solver."""
    runway_id: str
    length_m: float
    join_s_m: float
    initial_height_m: float
    threshold_height_m: float
    final_angle_rad: float

    def __post_init__(self):
        values = [self.length_m, self.join_s_m, self.initial_height_m,
                  self.threshold_height_m, self.final_angle_rad]
        if (not np.all(np.isfinite(values)) or not 0 < self.join_s_m < self.length_m
                or not 0 < self.final_angle_rad < np.pi/2):
            raise ValueError("CONDITIONAL_MODEL_CONFLICT: invalid profile parameters")
        self.m = float(np.tan(self.final_angle_rad))
        self.join_height_m = self.threshold_height_m+(self.length_m-self.join_s_m)*self.m
        if self.runway_id == "16R":
            self.b = 2*(self.join_height_m-self.initial_height_m)/self.join_s_m+self.m
            self.a = (-self.m-self.b)/(2*self.join_s_m)
            if self.b > 0 or self.join_height_m >= self.initial_height_m:
                raise ValueError("CONDITIONAL_MODEL_CONFLICT: specified RF1 descent not feasible")
            self.boundaries_m = [self.join_s_m]
        elif self.runway_id == "16L":
            self.transition_length_m = 2*(self.initial_height_m-self.join_height_m)/self.m
            self.start_s_m = self.join_s_m-self.transition_length_m
            if not 0 < self.start_s_m < self.join_s_m:
                raise ValueError("CONDITIONAL_MODEL_CONFLICT: specified level/quadratic/GP closure not feasible")
            self.boundaries_m = [self.start_s_m, self.join_s_m]
        else:
            raise ValueError("CONDITIONAL_MODEL_CONFLICT: unknown runway")

    def evaluate(self, s_m: float, side: str = "right") -> dict[str, float]:
        s = float(s_m)
        if not np.isfinite(s) or not 0 <= s <= self.length_m or side not in ("left", "right"):
            raise ValueError("profile query outside support or invalid side")
        before_join = s < self.join_s_m or (s == self.join_s_m and side == "left")
        if self.runway_id == "16R" and before_join:
            h = self.initial_height_m+self.b*s+self.a*s*s
            slope, second = self.b+2*self.a*s, 2*self.a
        elif self.runway_id == "16L" and before_join:
            x = max(0., s-self.start_s_m)
            h = self.initial_height_m-self.m*x*x/(2*self.transition_length_m)
            slope = -self.m*x/self.transition_length_m
            second = (-self.m/self.transition_length_m
                      if s > self.start_s_m or (s == self.start_s_m and side == "right") else 0.)
        else:
            h = self.threshold_height_m+(self.length_m-s)*self.m
            slope, second = -self.m, 0.
        return {"height_m": float(h), "dh_ds": float(slope), "d2h_ds2_per_m": float(second)}
