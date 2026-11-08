import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from m1_research.aircraft_state import AircraftSpec
from m1_research.config_loader import ConfigurationError, STUDY_PATH, load_study, study_status
from m1_research.generator import generate_formal_scenario, inspect_study
from m1_research.procedure_reference import constraint_status
from m1_research.smooth_uncertainty import SEProcess, StatisticsUncalibrated, se_joint_covariance, se_kernel
from m1_research.time_and_vertical import resolve_height_constraints


class UncertaintyAndStatusTests(unittest.TestCase):
    def test_study_is_self_contained_and_reference_only(self):
        study = load_study()
        self.assertEqual(study_status(study), "PARTIAL_REFERENCE")
        self.assertEqual(len(study["scenarios"][0]["assignments"]), 2)
        self.assertIsNone(study["scenarios"][0]["delta_t_entry_s"])
        report = inspect_study()
        self.assertFalse(report["formal_generation_allowed"])
        self.assertIsNone(generate_formal_scenario("case_001")["trajectory"])
        with self.assertRaises(ConfigurationError):
            load_study(Path(__file__).resolve().parents[2] / "config" / "study.yaml")

    def test_se_joint_derivative_is_reproducible(self):
        t = np.linspace(0.0, 4.0, 9)
        process = SEProcess(2.0, 1.5, "SUPPORTED")
        a = process.sample(t, 17)
        b = process.sample(t, 17)
        np.testing.assert_array_equal(a["error_m"], b["error_m"])
        np.testing.assert_array_equal(a["derivative_mps"], b["derivative_mps"])
        cov = se_joint_covariance(t, 2.0, 1.5)
        np.testing.assert_allclose(cov, cov.T, atol=1e-12)
        self.assertTrue(a["joint_derivative"])

    def test_missing_science_inputs_return_explicit_blockers(self):
        with self.assertRaises(StatisticsUncalibrated):
            SEProcess(None, None).sample(np.array([0.0, 1.0]), 1)
        spec = AircraftSpec("aircraft_01", "manned", "A320", None, None, None, None)
        self.assertEqual(spec.performance_status(), "PERFORMANCE_UNQUALIFIED")
        self.assertEqual(resolve_height_constraints([])["status"], "CONSTRAINT_CONFLICT")
        self.assertEqual(constraint_status([]), "CONSTRAINT_CONFLICT")

    def test_se_covariance_derivative_blocks_match_kernel_differentiation(self):
        t = np.array([0., .7, 1.5])
        h = 1e-5
        sigma, tau = 2., 1.5
        joint = se_joint_covariance(t, sigma, tau)
        derivative_second = (se_kernel(t, t+h, sigma, tau) - se_kernel(t, t-h, sigma, tau))/(2*h)
        np.testing.assert_allclose(joint[:3, 3:], derivative_second, atol=1e-9)
        np.testing.assert_allclose(np.diag(joint)[3:], sigma*sigma/(tau*tau))
        self.assertGreaterEqual(np.linalg.eigvalsh(joint).min(), -1e-10)


if __name__ == "__main__":
    unittest.main()
