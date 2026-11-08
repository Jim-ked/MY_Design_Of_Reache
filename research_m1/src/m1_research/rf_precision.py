"""Conditional RF reconstruction inside explicit printed rounding cells.

Only standard WGS84 geometry and the user-adjudicated rounding hypothesis
are used. No optimized coordinate is promoted to a published source value.
"""
import copy
import math

import numpy as np
from scipy.optimize import minimize

from .geodesy import WGS84_A_M, WGS84_F, parse_dms


POINT_ORDER = ("TJC01", "TJ907", "TJ906", "TJ903", "RW16R")
SELECTION_RULE = "minimize 0.5 * sum((delta_arcsec / half_unit_arcsec)**2), equal weights; deterministic SLSQP from zero adjustments"
POSITION_TOL_M = 1e-5
TANGENT_TOL = 1e-8


def _project_with_jacobian(frame, latlon_deg, normalized, half_unit_arcsec):
    """ENU projection and analytic Jacobian wrt normalized lat/lon tails."""
    scale = math.radians(half_unit_arcsec / 3600.)
    angles = np.deg2rad(latlon_deg) + normalized.reshape(5, 2) * scale
    lat, lon = angles.T
    sin, cos = np.sin(lat), np.cos(lat)
    slon, clon = np.sin(lon), np.cos(lon)
    e2 = WGS84_F * (2. - WGS84_F)
    denominator = 1. - e2 * sin**2
    n = WGS84_A_M / np.sqrt(denominator)
    dn = n * e2 * sin * cos / denominator
    xyz = np.column_stack((n*cos*clon, n*cos*slon, n*(1.-e2)*sin))
    dlat = np.column_stack(((dn*cos-n*sin)*clon,
                           (dn*cos-n*sin)*slon, (1.-e2)*(dn*sin+n*cos)))
    dlon = np.column_stack((-n*cos*slon, n*cos*clon, np.zeros(5)))
    xy = (xyz-frame.origin_ecef) @ frame.rotation[:2].T
    jac = np.stack((dlat @ frame.rotation[:2].T,
                    dlon @ frame.rotation[:2].T), axis=2) * scale
    return xy, jac


def _constraints(xy, jac):
    center = xy[0]
    radial = xy[1:4]-center
    radii = np.linalg.norm(radial, axis=1)
    if np.any(radii <= 0):
        raise ValueError("zero radius")
    dr = np.zeros((3, 10))
    for j in range(3):
        unit = radial[j]/radii[j]
        dr[j, :2] = -unit @ jac[0]
        dr[j, (j+1)*2:(j+2)*2] = unit @ jac[j+1]
    tf = xy[4]-xy[3]
    length = np.linalg.norm(tf)
    if length <= 0:
        raise ValueError("zero TF length")
    tangent = tf/length
    dot = np.dot(radial[2], tangent)
    endpoint_term = (radial[2]-dot*tangent)/length
    dt = np.zeros(10)
    dt[:2] = -tangent @ jac[0]
    dt[6:8] = (tangent-endpoint_term) @ jac[3]
    dt[8:10] = endpoint_term @ jac[4]
    values = np.array([radii[1]-radii[0], radii[2]-radii[0], dot])
    derivative = np.stack((dr[1]-dr[0], dr[2]-dr[0], dt))
    return values, derivative, radii, dr


def solve_rf_precision(raw_points, frame, *, coordinate_half_unit_arcsec,
                       radius_interval_nm, displayed_radius_nm):
    """Return a checked conditional representative, or an explicit conflict.

    The representative is a deterministic local least-adjustment solution.
    Neither uniqueness of the feasible set nor global optimality is claimed.
    Failed convergence means no verified representative was produced; it is
    not a proof that the mathematical feasible set is empty.
    """
    half = float(coordinate_half_unit_arcsec)
    interval = [float(v) for v in radius_interval_nm]
    assumptions = {"status": "CONDITIONAL", "coordinate_half_unit_arcsec": half,
                   "coordinate_bounds": "strict abs(delta) < half_unit",
                   "radius_interval_nm": interval, "radius_bounds": "lower inclusive; upper exclusive",
                   "basis": "nearest printed 0.1 arcsecond and nearest 0.1 NM are research hypotheses, not navigation database accuracy"}
    result = {"status": "SOURCE_GEOMETRY_CONFLICT", "raw_points": copy.deepcopy(raw_points),
              "displayed_radius_nm": float(displayed_radius_nm), "assumptions": assumptions,
              "selection_rule": SELECTION_RULE, "initialization": "all ten normalized tails = zero",
              "unique_database_path_claimed": False,
              "numerical_checks": {"position_tolerance_m": POSITION_TOL_M, "tangent_vector_tolerance": TANGENT_TOL},
              "residuals": {}}
    try:
        if len(interval) != 2 or not 0 < interval[0] < interval[1] or not half > 0:
            raise ValueError("invalid explicit rounding intervals")
        ll = np.array([parse_dms(raw_points[name]) for name in POINT_ORDER])
        if not np.all(np.isfinite(ll)) or not np.isfinite(half):
            raise ValueError("nonfinite source coordinates")
        lo, hi = np.array(interval)*1852.

        def evaluate(z):
            xy, jac = _project_with_jacobian(frame, ll, z, half)
            values, derivative, radii, dr = _constraints(xy, jac)
            return xy, values, derivative, radii, dr

        optimum = minimize(lambda z: .5*np.dot(z, z), np.zeros(10),
                           jac=lambda z: z, method="SLSQP", bounds=[(-1., 1.)]*10,
                           constraints=[
                               {"type": "eq", "fun": lambda z: evaluate(z)[1],
                                "jac": lambda z: evaluate(z)[2]},
                               {"type": "ineq", "fun": lambda z: np.array([evaluate(z)[3][0]-lo, hi-evaluate(z)[3][0]]),
                                "jac": lambda z: np.stack((evaluate(z)[4][0], -evaluate(z)[4][0]))}],
                           options={"maxiter": 240, "ftol": 1e-9})
        z = optimum.x
        xy, values, derivative, radii, _ = evaluate(z)
        radius = float(radii.mean())
        angles = np.arctan2((xy[1:4]-xy[0])[:, 1], (xy[1:4]-xy[0])[:, 0])
        sweeps = (angles[:-1]-angles[1:]) % (2.*np.pi)
        last_radial = (xy[3]-xy[0])/radii[2]
        rf_tangent = np.array([last_radial[1], -last_radial[0]])
        tf = xy[4]-xy[3]
        tf_tangent = tf/np.linalg.norm(tf)
        tangent_error = float(np.linalg.norm(rf_tangent-tf_tangent))
        signed_angle = float(np.arctan2(np.linalg.det(np.stack((rf_tangent, tf_tangent))), np.dot(rf_tangent, tf_tangent)))
        multipliers = np.linalg.lstsq(derivative.T, -z, rcond=None)[0]
        result.update({
            "normalized_adjustments": z.tolist(), "objective": float(.5*np.dot(z,z)),
            "adjustments_arcsec": {name: {"latitude": float(z[2*i]*half), "longitude": float(z[2*i+1]*half)}
                                    for i, name in enumerate(POINT_ORDER)},
            "reconstructed_latlon_deg": {name: (ll[i]+z[2*i:2*i+2]*half/3600.).tolist() for i, name in enumerate(POINT_ORDER)},
            "reconstructed_xy_m": {name: xy[i].tolist() for i, name in enumerate(POINT_ORDER)},
            "radius_m": radius, "radius_nm": radius/1852., "right_sweeps_rad": sweeps.tolist(),
            "residuals": {"equal_radius_m": float(np.ptp(radii)), "tangent_radial_projection_m": float(values[2]),
                          "tangent_vector_difference": tangent_error, "tangent_signed_angle_rad": signed_angle,
                          "coordinate_max_adjustment_arcsec": float(np.max(np.abs(z))*half),
                          "radius_lower_margin_m": radius-lo, "radius_upper_margin_m": hi-radius,
                          "interior_stationarity_norm": float(np.linalg.norm(z+derivative.T@multipliers))},
            "solver": {"name": "scipy.optimize.minimize/SLSQP", "success": bool(optimum.success),
                       "message": str(optimum.message), "iterations": int(optimum.nit), "ftol": 1e-9, "maxiter": 240},
        })
        inside = np.all(np.abs(z) < 1.) and all(lo <= r < hi for r in radii)
        ordered = np.all(sweeps > 0) and np.sum(sweeps) < 2.*np.pi
        valid = inside and ordered and np.max(np.abs(values)) <= POSITION_TOL_M and tangent_error <= TANGENT_TOL
        if optimum.success and valid:
            result["status"] = "CONDITIONAL_REFERENCE_GEOMETRY"
        else:
            result["reason"] = "prescribed deterministic solve produced no verified feasible representative; no constraints relaxed"
    except (ValueError, KeyError, FloatingPointError) as exc:
        result["reason"] = str(exc)
    return result
