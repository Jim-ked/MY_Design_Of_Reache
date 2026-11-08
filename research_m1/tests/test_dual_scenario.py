from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from m1_research.config_loader import load_study
from m1_research.scenario_sync import ScheduledAircraft, synthetic_pair, synchronize_aircraft_states


class DualScenarioTests(unittest.TestCase):
    def test_config_has_one_pair_and_no_fabricated_operational_time(self):
        study = load_study()
        self.assertEqual(len(study["scenarios"]), 1)
        assignments = study["scenarios"][0]["assignments"]
        self.assertEqual(len(assignments), 2)
        self.assertEqual({a["aircraft_id"] for a in assignments}, {"aircraft_01", "aircraft_02"})
        self.assertTrue(all(a["t_entry_s"] is None for a in assignments))

    def test_enter_leave_and_relative_velocity_no_outside_evaluation(self):
        study = load_study()
        pair = synthetic_pair(study)
        rows = synchronize_aircraft_states(pair, [-1., 0., 6., 7., 20., 21., 23., 24.])
        self.assertEqual([r["pair_active"] for r in rows], [False, False, False, True, True, False, False, False])
        self.assertIsNone(rows[0]["states"]["aircraft_01"]["position_m"])
        self.assertIsNone(rows[1]["relative_state"])
        relative = rows[3]["relative_state"]
        self.assertEqual(relative["delta_velocity_mps"], [0., -3., 0.])
        self.assertEqual(pair["aircraft_02"].entry_s - pair["aircraft_01"].entry_s, 7.)
        self.assertEqual(rows[3]["states"]["aircraft_01"]["scenario_id"], "case_001")

    def test_schedule_never_calls_outside_its_domain(self):
        def must_not_run(t):
            self.fail("out-of-support evaluator called")
        scheduled = ScheduledAircraft("x", "case_001", 1., 2., must_not_run)
        self.assertIsNone(scheduled(0.))
        self.assertIsNone(scheduled(3.))


if __name__ == "__main__":
    unittest.main()
