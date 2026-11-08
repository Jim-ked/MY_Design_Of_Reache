"""Small deterministic checks of the user-adjudicated conditional example."""
import copy
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from m1_research.config_loader import load_study
from m1_research.conditional_nominal import build_conditional_flights, common_time_grid
from m1_research.generator import generate_conditional_nominal, generate_formal_scenario


class ConditionalNominalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flights = build_conditional_flights(load_study(), delta_entry_s=0.)

    def test_heights_slopes_and_one_sided_continuity(self):
        left, right = self.flights.values()
        self.assertAlmostEqual(left.profile.evaluate(0.)["height_m"], 600.)
        self.assertAlmostEqual(left.profile.fap_s_m, 5623.99, delta=1.)
        self.assertAlmostEqual(left.profile.evaluate(left.profile.join_s_m)["dh_ds"], -np.tan(np.deg2rad(3.)), delta=1e-12)
        self.assertAlmostEqual(left.profile.transition_length_m, left.speed_mps**2*np.tan(np.deg2rad(3.))/0.5, delta=1e-9)
        self.assertAlmostEqual(left.profile.evaluate(left.path.length_m)["height_m"], 17.3)
        self.assertAlmostEqual(right.profile.evaluate(right.profile.join_s_m)["height_m"], 599.69996, delta=1e-5)
        self.assertAlmostEqual(right.profile.evaluate(right.path.length_m)["height_m"], 17.4496)
        for flight in self.flights.values():
            for s in flight.profile.boundaries_m:
                a, b = (flight.profile.evaluate(s, side) for side in ("left", "right"))
                self.assertAlmostEqual(a["height_m"], b["height_m"], delta=1e-8)
                self.assertAlmostEqual(a["dh_ds"], b["dh_ds"], delta=1e-12)
            self.assertTrue(all(row["c1_consistent"] for row in flight.connection_checks()))

    def test_constant_groundspeed_time_inverse_and_exact_endpoints(self):
        for flight, kt, duration in zip(self.flights.values(), (145., 115.), (224.45, 318.58)):
            self.assertAlmostEqual(flight.speed_mps, kt*1852./3600.)
            self.assertAlmostEqual(flight.exit_s-flight.entry_s, duration, delta=.01)
            for s in (0., flight.path.length_m*.37, flight.path.length_m):
                t = flight.time_at_s(s)
                self.assertAlmostEqual(flight.s_at_time(t), s, delta=1e-8)
            self.assertEqual(flight.s_at_time(flight.exit_s), flight.path.length_m)
            with self.assertRaises(ValueError):
                flight.s_at_time(flight.exit_s+1.)
        grid = common_time_grid(self.flights)
        self.assertTrue(np.all(np.diff(grid)>0))
        for f in self.flights.values():
            self.assertIn(f.entry_s, grid)
            self.assertIn(f.exit_s, grid)

    def test_velocity_is_derivative_of_same_position_and_profile(self):
        for f in self.flights.values():
            for fraction in (.1, .31, .7):
                t = f.entry_s+(f.exit_s-f.entry_s)*fraction
                a, b, state = f.evaluate(t-1e-4), f.evaluate(t+1e-4), f.evaluate(t)
                p = lambda x: np.array([x.east_m, x.north_m, x.altitude_msl_m])
                np.testing.assert_allclose((p(b)-p(a))/2e-4,
                    [state.velocity_e_mps,state.velocity_n_mps,state.velocity_u_mps],atol=1e-6)
                s = f.s_at_time(t)
                hm, hp, h = f.profile.evaluate(s-.01), f.profile.evaluate(s+.01), f.profile.evaluate(s)
                self.assertAlmostEqual((hp["height_m"]-hm["height_m"])/.02, h["dh_ds"], delta=1e-10)
                self.assertAlmostEqual((hp["dh_ds"]-hm["dh_ds"])/.02, h["d2h_ds2_per_m"], delta=1e-12)
            self.assertAlmostEqual(f.evaluate(f.exit_s).velocity_u_mps,
                                   -f.speed_mps*np.tan(np.deg2rad(3.)))
            with self.assertRaisesRegex(ValueError, "CONDITIONAL_MODEL_CONFLICT"):
                f.state_at_s(0., time_abs_s=f.entry_s+1.)

    def test_faf_is_preserved_and_fap_is_a_distinct_geometry_event(self):
        left = self.flights["aircraft_01"]
        events = left.reference["events"]
        self.assertEqual(events["FAF_D6P2_ICU"]["status"], "CONDITIONAL_DME_HORIZONTAL_EVENT")
        self.assertEqual(events["FAP"]["status"], "CONDITIONAL_GEOMETRY_CANDIDATE")
        self.assertAlmostEqual(events["FAP"]["s_m"], left.profile.fap_s_m, delta=1e-9)
        self.assertLess(left.profile.start_s_m, left.profile.fap_s_m)
        self.assertLess(left.profile.fap_s_m, left.profile.join_s_m)
        self.assertIsNone(events["GP_CAPTURE"]["s_m"])

    def test_entry_sign_activity_identity_and_formal_block(self):
        for delta in (-20., 20.):
            output = generate_conditional_nominal(delta_entry_s=delta)
            self.assertEqual(output["status"], "CONDITIONAL_NOMINAL")
            self.assertEqual(output["qualification_status"], "FORMAL_NOT_QUALIFIED")
            self.assertEqual(output["delta_t_entry_s"], delta)
            for row in output["rows"]:
                self.assertEqual(row["relative_state"] is not None, row["pair_active"])
                for aid, state in row["states"].items():
                    self.assertEqual(state["aircraft_id"], aid)
                    if state["active"]:
                        self.assertEqual(state["scenario_id"], "case_001")
                        self.assertEqual(state["model_status"], "CONDITIONAL_NOMINAL")
                    else:
                        self.assertIsNone(state["position_m"])
        self.assertIsNone(generate_formal_scenario("case_001")["trajectory"])
        self.assertEqual(generate_formal_scenario("case_001")["qualification_status"], "FORMAL_NOT_QUALIFIED")
        for value in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                build_conditional_flights(load_study(), delta_entry_s=value)

    def test_synthetic_demo_is_not_a_parameter_source(self):
        study = copy.deepcopy(load_study())
        del study["operations"]["synthetic_demo"]
        other = build_conditional_flights(study, delta_entry_s=0.)
        for aid, f in other.items():
            self.assertEqual(f.path.length_m, self.flights[aid].path.length_m)
            self.assertEqual(f.speed_mps, self.flights[aid].speed_mps)
        study["operations"]["conditional_nominal"]["runways"]["16L"]["vertical_accel_reference"]["value"] = -0.1
        with self.assertRaisesRegex(ValueError, "CONDITIONAL_MODEL_CONFLICT"):
            build_conditional_flights(study, delta_entry_s=0.)

    def test_cli_requires_explicit_entry_delta(self):
        run = subprocess.run([sys.executable,"-m","m1_research","nominal-conditional"],
                             capture_output=True,text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("--delta-entry-s", run.stderr)


if __name__ == "__main__":
    unittest.main()
