import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from m1_research.aircraft_state import state_from_reference_and_error
from m1_research.procedure_reference import LineSegment, ReferencePath
from m1_research.scenario_sync import synchronize_aircraft_states
from m1_research.time_and_vertical import invert_time, kinematic_state, time_map


class TimeAndStateTests(unittest.TestCase):
    def test_time_inverse_and_vertical_units(self):
        s = np.array([0.0, 5.0, 10.0])
        v = np.array([10.0, 10.0, 10.0])
        t = time_map(s, v)
        np.testing.assert_allclose(t, [0.0, 0.5, 1.0])
        np.testing.assert_allclose(invert_time(t, s, [0.25, 0.75]), [2.5, 7.5])
        k = kinematic_state(v, np.zeros(3), np.zeros(3), np.full(3, -0.05), np.zeros(3))
        np.testing.assert_allclose(k["vertical_speed_mps"], -0.5)
        np.testing.assert_allclose(k["path_angle_rate_rad_s"], 0.0)

    def test_piecewise_linear_speed_uses_integral_and_inverse(self):
        s = np.array([0.0, 10.0, 20.0])
        v = np.array([10.0, 20.0, 20.0])
        t = time_map(s, v)
        expected_first = np.log(2.0)
        self.assertAlmostEqual(t[1], expected_first)
        np.testing.assert_allclose(
            invert_time(t, s, t, horizontal_speed_mps=v), s, atol=1e-12,
        )

    def test_random_state_uses_shared_path_and_derivative(self):
        path = ReferencePath([LineSegment(100.0, (0.0, 0.0), 0.0, "TF")])
        state = state_from_reference_and_error(
            path=path, aircraft_id="aircraft_01", scenario_id="case_001",
            procedure_id="synthetic", aircraft_type="synthetic",
            time_abs_s=2.0, s_m=20.0, altitude_msl_m=100.0,
            d_height_ds=-0.01, horizontal_speed_mps=10.0,
            e_n_m=1.0, e_z_m=2.0, de_n_dt_mps=0.3, de_z_dt_mps=-0.2,
            model_status="exploratory", provenance_id="synthetic-test",
        )
        self.assertAlmostEqual(state.east_m, -1.0)
        self.assertAlmostEqual(state.north_m, 20.0)
        self.assertAlmostEqual(state.altitude_msl_m, 102.0)
        self.assertAlmostEqual(state.velocity_u_mps, -0.3)

    def test_sync_does_not_extrapolate_activity(self):
        path = ReferencePath([LineSegment(20.0, (0.0, 0.0), 0.0, "TF")])

        def evaluator_a(t):
            return state_from_reference_and_error(
                path=path, aircraft_id="a", scenario_id="case_001",
                procedure_id="synthetic", aircraft_type="synthetic",
                time_abs_s=t, s_m=5.0, altitude_msl_m=10.0,
                d_height_ds=0.0, horizontal_speed_mps=2.0,
                e_n_m=0.0, e_z_m=0.0, de_n_dt_mps=0.0, de_z_dt_mps=0.0,
                model_status="exploratory", provenance_id="test",
            )

        def evaluator_b(t):
            state = evaluator_a(t)
            return state.__class__(**{**state.as_dict(), "aircraft_id": "b", "active": t <= 1.0})

        rows = synchronize_aircraft_states({"a": evaluator_a, "b": evaluator_b}, [0.0, 2.0])
        self.assertTrue(rows[0]["pair_active"])
        self.assertFalse(rows[1]["pair_active"])

    def test_circle_random_velocity_is_same_position_derivative(self):
        from m1_research.procedure_reference import CircularArc
        path = ReferencePath([CircularArc(100., 1., (0., 0.), 0., -1, "RF")])
        def state(t):
            return state_from_reference_and_error(
                path=path, aircraft_id="a", scenario_id="synthetic", procedure_id="synthetic",
                aircraft_type="synthetic", time_abs_s=t, s_m=10.*t,
                altitude_msl_m=100.-t, d_height_ds=-.1, horizontal_speed_mps=10.,
                e_n_m=2.+.2*t, e_z_m=.3*t, de_n_dt_mps=.2, de_z_dt_mps=.3,
                model_status="CONDITIONAL_NOMINAL", provenance_id="synthetic")
        a,b=state(2.-1e-5),state(2.+1e-5)
        p=lambda x: np.array([x.east_m,x.north_m,x.altitude_msl_m])
        derivative=(p(b)-p(a))/2e-5
        s=state(2.)
        np.testing.assert_allclose(derivative,[s.velocity_e_mps,s.velocity_n_mps,s.velocity_u_mps],atol=1e-7)


if __name__ == "__main__":
    unittest.main()
