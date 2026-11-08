"""16R horizontal properties only; no trajectory/vertical/stochastic runs."""
import copy
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from m1_research.aip_reference import build_16r_reference
from m1_research.config_loader import load_study
from m1_research.geodesy import ENUFrame
from m1_research.procedure_reference import ReferencePath, LineSegment
from m1_research.rf_precision import solve_rf_precision


class RFPrecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = load_study()
        cls.before = copy.deepcopy(cls.study)
        cls.reference = build_16r_reference(cls.study)

    def test_raw_aip_fields_are_not_mutated_or_promoted(self):
        self.assertEqual(self.study, self.before)
        self.assertEqual(self.study["procedures"][1]["reference_geometry"]["rf_radius_nm"], 2.7)
        self.assertEqual(self.reference["rounding_solution"]["raw_points"],
                         self.study["procedures"][1]["reference_geometry"]["points"])
        self.assertEqual(self.reference["status"], "CONDITIONAL_REFERENCE_GEOMETRY")
        self.assertEqual(self.reference["full_nominal_status"], "UNRESOLVED")

    def test_all_ten_coordinate_adjustments_are_strictly_inside_half_last_digit(self):
        adjustments = self.reference["rounding_solution"]["adjustments_arcsec"]
        self.assertEqual(len(adjustments), 5)
        for change in adjustments.values():
            self.assertLess(abs(change["latitude"]), .05)
            self.assertLess(abs(change["longitude"]), .05)

    def test_reconstructed_latlon_projection_independently_agrees_with_enu(self):
        from m1_research.geodesy import parse_dms
        origin = self.study["airport"]["reference_frame"]
        frame = ENUFrame(origin["arp_latitude_deg"], origin["arp_longitude_deg"], origin["arp_elevation_m"])
        solution = self.reference["rounding_solution"]
        for name, ll in solution["reconstructed_latlon_deg"].items():
            raw_ll = np.array(parse_dms(solution["raw_points"][name]))
            delta_arcsec = (np.array(ll)-raw_ll)*3600.
            self.assertTrue(np.all(np.abs(delta_arcsec) < .05))
            np.testing.assert_allclose(frame.to_enu(*ll)[:2], solution["reconstructed_xy_m"][name], atol=1e-8)

    def test_analytic_constraint_jacobian_matches_independent_difference(self):
        from m1_research.geodesy import parse_dms
        from m1_research.rf_precision import _project_with_jacobian, _constraints, POINT_ORDER
        origin = self.study["airport"]["reference_frame"]
        frame = ENUFrame(origin["arp_latitude_deg"], origin["arp_longitude_deg"], origin["arp_elevation_m"])
        ll = np.array([parse_dms(self.reference["rounding_solution"]["raw_points"][key]) for key in POINT_ORDER])
        z = np.array(self.reference["rounding_solution"]["normalized_adjustments"])
        def values(x):
            p,j = _project_with_jacobian(frame, ll, x, .05)
            return _constraints(p,j)
        analytic = values(z)[1]
        for i in range(10):
            step = np.zeros(10); step[i] = .001
            difference = (values(z+step)[0]-values(z-step)[0])/.002
            np.testing.assert_allclose(difference, analytic[:,i], atol=3e-6)

    def test_radius_in_display_interval_and_three_points_on_same_circle(self):
        solution = self.reference["rounding_solution"]
        radius = solution["radius_m"]
        self.assertGreaterEqual(radius / 1852., 2.65)
        self.assertLess(radius / 1852., 2.75)
        center = np.asarray(solution["reconstructed_xy_m"]["TJC01"])
        for name in ("TJ907", "TJ906", "TJ903"):
            point = np.asarray(solution["reconstructed_xy_m"][name])
            self.assertAlmostEqual(np.linalg.norm(point-center), radius, delta=1e-5)

    def test_rf_rf_tf_positions_and_forward_tangents_are_continuous(self):
        path = self.reference["path"]
        for boundary in path.boundary_states()[1:-1]:
            a, b = boundary["left"], boundary["right"]
            np.testing.assert_allclose([a["east_m"], a["north_m"]], [b["east_m"], b["north_m"]], atol=1e-5)
            np.testing.assert_allclose([a["tangent_east"], a["tangent_north"]],
                                       [b["tangent_east"], b["tangent_north"]], atol=1e-8)
        self.assertTrue(path.require_continuity()["continuous"])
        self.assertTrue(all(segment.direction == -1 for segment in path.segments[:2]))

    def test_representative_selection_is_deterministic_and_not_a_fixed_witness(self):
        other = build_16r_reference(copy.deepcopy(self.study))
        np.testing.assert_allclose(other["rounding_solution"]["normalized_adjustments"],
                                   self.reference["rounding_solution"]["normalized_adjustments"], atol=1e-9)
        self.assertIn("sum", self.reference["rounding_solution"]["selection_rule"])
        self.assertFalse(self.reference["rounding_solution"]["unique_database_path_claimed"])

    def test_inconsistent_fix_is_rejected_without_patch_or_relaxation(self):
        study = copy.deepcopy(self.study)
        geometry = study["procedures"][1]["reference_geometry"]
        geometry["points"]["TJ906"]["lat_min"] += 1
        result = build_16r_reference(study)
        self.assertEqual(result["status"], "SOURCE_GEOMETRY_CONFLICT")
        self.assertIsNone(result["path"])
        self.assertIn("residuals", result["rounding_solution"])
        self.assertEqual(result["rounding_solution"]["assumptions"],
                         self.reference["rounding_solution"]["assumptions"])

    def test_missing_source_point_is_rejected(self):
        study = copy.deepcopy(self.study)
        del study["procedures"][1]["reference_geometry"]["points"]["TJ903"]
        result = build_16r_reference(study)
        self.assertEqual(result["status"], "SOURCE_GEOMETRY_CONFLICT")
        self.assertIsNone(result["path"])

    def test_gap_or_tangent_corner_cannot_be_used_as_continuous_path(self):
        for second in (LineSegment(2., (8., 0.), np.pi/2, "TF"),
                       LineSegment(2., (2., 0.), 0., "TF")):
            path = ReferencePath([LineSegment(2., (0., 0.), np.pi/2, "RF_TEST"), second])
            with self.assertRaisesRegex(ValueError, "SOURCE_GEOMETRY_CONFLICT"):
                path.require_continuity()
            with self.assertRaises(ValueError):
                path.require_continuity(position_tolerance_m=float("nan"))

    def test_downstream_state_request_rejects_disconnected_horizontal_path(self):
        from m1_research.aircraft_state import state_from_reference_and_error
        path = ReferencePath([LineSegment(2., (0., 0.), 0., "RF_TEST"),
                              LineSegment(2., (0., 8.), 0., "TF_TEST")])
        with self.assertRaisesRegex(ValueError, "SOURCE_GEOMETRY_CONFLICT"):
            state_from_reference_and_error(
                path=path, aircraft_id="synthetic", scenario_id="synthetic", procedure_id="synthetic",
                aircraft_type="synthetic", time_abs_s=0., s_m=1., altitude_msl_m=0.,
                d_height_ds=0., horizontal_speed_mps=1., e_n_m=0., e_z_m=0.,
                de_n_dt_mps=0., de_z_dt_mps=0., model_status="UNRESOLVED", provenance_id="property-test")


if __name__ == "__main__":
    unittest.main()
