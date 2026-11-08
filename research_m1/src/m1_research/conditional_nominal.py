"""Explicit conditional nominal example; no formal, stochastic or risk output."""
from dataclasses import dataclass
import copy
import math

import numpy as np

from .aip_reference import build_16l_reference, build_16r_reference
from .aircraft_state import state_from_components
from .time_and_vertical import ConditionalHeightProfile, time_map, invert_time


PROVENANCE_ID = "USER_CONDITIONAL_NOMINAL_20261108"


@dataclass
class ConditionalFlight:
    aircraft_id: str
    aircraft_type: str
    procedure_id: str
    entry_s: float
    speed_mps: float
    reference: dict
    profile: ConditionalHeightProfile
    parameters: dict

    def __post_init__(self):
        self.path = self.reference["path"]
        self.path.require_continuity()
        self._s_nodes = np.array([0., self.path.length_m])
        self._speeds = np.full(2, self.speed_mps)
        self._t_nodes = time_map(self._s_nodes, self._speeds, self.entry_s)
        self.exit_s = float(self._t_nodes[-1])
        if not all(row["c1_consistent"] for row in self.connection_checks()):
            raise ValueError("CONDITIONAL_MODEL_CONFLICT: position/velocity boundary mismatch")

    def time_at_s(self, s):
        if not np.isfinite(s) or not 0 <= s <= self.path.length_m:
            raise ValueError("s outside conditional support")
        return float(self.entry_s+s/self.speed_mps)

    def s_at_time(self, t):
        if not np.isfinite(t) or not self.entry_s <= t <= self.exit_s:
            raise ValueError("time outside conditional active support")
        if t == self.exit_s:
            return self.path.length_m
        return float(invert_time(self._t_nodes, self._s_nodes, np.array([t]), self._speeds)[0])

    def state_at_s(self, s, side="right", time_abs_s=None):
        if time_abs_s is not None and not math.isclose(time_abs_s,self.time_at_s(s),rel_tol=0.,abs_tol=1e-9):
            raise ValueError("CONDITIONAL_MODEL_CONFLICT: inconsistent time and along-path state")
        ref, height = self.path.evaluate(s, side), self.profile.evaluate(s, side)
        return state_from_components(
            aircraft_id=self.aircraft_id, scenario_id="case_001", procedure_id=self.procedure_id,
            aircraft_type=self.aircraft_type, time_abs_s=self.time_at_s(s) if time_abs_s is None else time_abs_s,
            s_m=s, position_m=np.array([ref["east_m"],ref["north_m"],height["height_m"]]),
            velocity_mps=self.speed_mps*np.array([ref["tangent_east"],ref["tangent_north"],height["dh_ds"]]),
            active=True, model_status="CONDITIONAL_NOMINAL", provenance_id=PROVENANCE_ID)

    def evaluate(self, t):
        return self.state_at_s(self.s_at_time(t), time_abs_s=t)

    def __call__(self, t):
        return self.evaluate(t) if self.entry_s <= t <= self.exit_s else None

    def connection_checks(self):
        cuts = set(self.profile.boundaries_m)
        cuts.update(row["s_m"] for row in self.path.boundary_states()[1:-1])
        rows = []
        for s in sorted(cuts):
            left, right = (self.state_at_s(s, side).as_dict() for side in ("left", "right"))
            pgap = float(np.linalg.norm([right[k]-left[k] for k in ("east_m","north_m","altitude_msl_m")]))
            vgap = float(np.linalg.norm([right[k]-left[k] for k in ("velocity_e_mps","velocity_n_mps","velocity_u_mps")]))
            rows.append({"s_m":s,"time_abs_s":self.time_at_s(s),"left":left,"right":right,
                         "left_height_derivatives":self.profile.evaluate(s,"left"),
                         "right_height_derivatives":self.profile.evaluate(s,"right"),
                         "position_gap_m":pgap,"velocity_gap_mps":vgap,
                         "c1_consistent":pgap<=1e-5 and vgap<=1e-6})
        return rows

    def diagnostics(self):
        cuts = {0.,self.path.length_m,*self.profile.boundaries_m}
        cuts.update(row["s_m"] for row in self.path.boundary_states()[1:-1])
        rows = []
        for s in sorted(cuts):
            for side in ("left","right"):
                h = self.profile.evaluate(s,side)
                curvature = self.path.evaluate(s,side)["curvature_1_m"]
                rows.append({"s_m":s,"side":side,**h,"path_angle_rad":math.atan(h["dh_ds"]),
                    "vertical_speed_mps":self.speed_mps*h["dh_ds"],
                    "path_angle_rate_rad_s":self.speed_mps*h["d2h_ds2_per_m"]/(1+h["dh_ds"]**2),
                    "vertical_accel_mps2":self.speed_mps**2*h["d2h_ds2_per_m"],
                    "horizontal_curvature_per_m":curvature,
                    "zero_wind_gs_bank_proxy_rad":math.atan(self.speed_mps**2*abs(curvature)/9.80665)})
        profile_parameters = {"initial_height_m":self.profile.initial_height_m,
            "threshold_height_m":self.profile.threshold_height_m,"join_s_m":self.profile.join_s_m,
            "join_height_m":self.profile.join_height_m,"final_slope":-self.profile.m}
        if self.profile.runway_id == "16L":
            profile_parameters.update(transition_length_m=self.profile.transition_length_m,
                transition_start_s_m=self.profile.start_s_m,
                transition_duration_s=self.profile.transition_length_m/self.speed_mps,
                fap_s_m=self.profile.fap_s_m,
                vertical_accel_reference_mps2=self.profile.vertical_accel_reference_mps2,
                height_constraint_status="600 m horizontal-line FAP candidate; transition scale from 0.5 m/s^2 research reference")
        else:
            profile_parameters.update(rf1_linear_coefficient=self.profile.b,
                rf1_quadratic_coefficient_per_m=self.profile.a,
                tj906_height_ft=self.profile.join_height_m/.3048,
                tj906_minus_2000_ft=self.profile.join_height_m/.3048-2000.,
                height_constraint_status="2000 ft restriction type/rounding unresolved; no compliance claim")
        peaks = {key:max(rows,key=lambda row:abs(row[key])) for key in
                 ("path_angle_rate_rad_s","vertical_accel_mps2","zero_wind_gs_bank_proxy_rad")}
        return {"duration_s":self.exit_s-self.entry_s,"constant_horizontal_gs_mps":self.speed_mps,
                "entry_s":self.entry_s,"exit_s":self.exit_s,"reference_status":self.reference["status"],
                "reference_events":self.reference["events"],"profile_boundaries_m":self.profile.boundaries_m,
                "profile_parameters":profile_parameters,"extrema_at_analytic_one_sided_cuts":peaks,
                "one_sided_kinematics":rows,"connection_checks":self.connection_checks(),
                "bank_interpretation":"zero-wind groundspeed-based requirement proxy, not aircraft performance qualification",
                "parameters_and_sources":self.parameters}


def _metres(field):
    factors = {"m":1.,"ft":.3048}
    if field["unit"] not in factors:
        raise ValueError("unsupported conditional height unit")
    return float(field["value"])*factors[field["unit"]]


def build_conditional_flights(study, *, delta_entry_s):
    if not math.isfinite(delta_entry_s):
        raise ValueError("explicit finite delta_entry_s required")
    example = study["operations"]["conditional_nominal"]
    if example["status"] != "CONDITIONAL_NOMINAL":
        raise ValueError("conditional example status required")
    scenario = next(s for s in study["scenarios"] if s["scenario_id"]=="case_001")
    if [(a["aircraft_id"],a["procedure_id"]) for a in scenario["assignments"]] != [
        ("aircraft_01","ZBTJ_RWY16L_RNAV_ILS_DME"),("aircraft_02","ZBTJ_RWY16R_RNP_Y_AR")]:
        raise ValueError("CONDITIONAL_MODEL_CONFLICT: case_001 assignment mismatch")
    flights = {}
    for assignment, runway, aircraft_type, builder, entry in zip(scenario["assignments"],
            ("16L","16R"),("A320","MQ9A"),(build_16l_reference,build_16r_reference),(0.,float(delta_entry_s))):
        aid = assignment["aircraft_id"]
        if next(a["aircraft_type"] for a in study["aircraft"] if a["aircraft_id"]==aid) != aircraft_type:
            raise ValueError("CONDITIONAL_MODEL_CONFLICT: aircraft type mismatch")
        reference = copy.deepcopy(builder(study))
        if reference["status"] != {"16L":"CONDITIONAL_LOC_REFERENCE","16R":"CONDITIONAL_REFERENCE_GEOMETRY"}[runway]:
            raise ValueError("CONDITIONAL_MODEL_CONFLICT: accepted horizontal reference unavailable")
        params = example["runways"][runway]
        gs = params["groundspeed"]
        if gs["unit"] != "kt" or gs["speed_type"] != "horizontal_GS":
            raise ValueError("conditional speed must be explicitly horizontal GS in kt")
        if runway == "16L":
            threshold_height = _metres(params["threshold_elevation"])+_metres(params["threshold_clearance"])
            final_m = math.tan(math.radians(float(example["final_descent_angle"]["value"])))
            fap_s = reference["path"].length_m - (_metres(params["initial_height"])-threshold_height)/final_m
            fap_state = reference["path"].evaluate(fap_s)
            reference["events"]["FAP"] = {
                "s_m": fap_s, "xy_m": [fap_state["east_m"], fap_state["north_m"]],
                "status": "CONDITIONAL_GEOMETRY_CANDIDATE",
                "definition": "600 m horizontal line and 3 deg GP line intersection; not formal FAP or GP capture",
                "source_ref": "USER_CONDITIONAL_NOMINAL_20261108",
            }
            join = fap_s
        else:
            join = reference["events"]["TJ906"]
        angle = example["final_descent_angle"]
        if angle["unit"] != "deg":
            raise ValueError("conditional final angle must be in deg")
        profile = ConditionalHeightProfile(runway,reference["path"].length_m,join,
            _metres(params["initial_height"]),_metres(params["threshold_elevation"])+_metres(params["threshold_clearance"]),
            math.radians(float(angle["value"])),
            fap_s_m=(fap_s if runway == "16L" else None),
            vertical_accel_reference_mps2=(float(params["vertical_accel_reference"]["value"]) if runway == "16L" else None),
            horizontal_speed_mps=(float(gs["value"])*1852./3600. if runway == "16L" else None))
        flights[aid] = ConditionalFlight(aid,aircraft_type,assignment["procedure_id"],entry,
            float(gs["value"])*1852./3600.,reference,profile,{**params,"final_descent_angle":angle})
    return flights


def common_time_grid(flights):
    """One-second common absolute grid plus both exact entry/exit endpoints."""
    endpoints = [t for f in flights.values() for t in (f.entry_s,f.exit_s)]
    return np.unique(np.r_[np.arange(min(endpoints),max(endpoints),1.),endpoints]).tolist()
