import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from m1_research.aip_reference import build_16l_reference, build_16r_reference
from m1_research.config_loader import load_study


class AIPReferenceTests(unittest.TestCase):
    def test_16r_partial_reference_has_rf_rf_tf_events_and_single_sided_curvature(self):
        result = build_16r_reference(load_study())
        self.assertEqual(result["status"], "CONDITIONAL_REFERENCE_GEOMETRY")
        self.assertLess(result["events"]["TJ907"], result["events"]["TJ906"])
        self.assertLess(result["events"]["TJ906"], result["events"]["TJ903"])
        self.assertLess(result["events"]["TJ903"], result["events"]["RW16R"])
        boundary = result["path"].boundary_states()[2]
        self.assertNotEqual(boundary["left"]["curvature_1_m"], boundary["right"]["curvature_1_m"])
        self.assertLess(result["derived"]["rf_tf_position_gap_m"], 1e-5)
        self.assertTrue(result["horizontal_continuity"]["continuous"])

    def test_16l_partial_reference_preserves_faf_as_event_without_gp_capture_guess(self):
        result = build_16l_reference(load_study())
        self.assertEqual(result["status"], "CONDITIONAL_LOC_REFERENCE")
        self.assertIsNone(result["events"]["TJ954_PUBLISHED"]["s_m"])
        self.assertEqual(result["events"]["IF_REFERENCE_STATION"]["s_m"], 0.)
        self.assertLess(result["events"]["FAF_D6P2_ICU"]["s_m"], result["events"]["THR"]["s_m"])
        self.assertIsNone(result["derived"]["published_fap_s_m"])
        self.assertEqual(result["path"].evaluate(result["events"]["FAF_D6P2_ICU"]["s_m"])["segment_id"], "LOC_REFERENCE")
        self.assertFalse(any(x in str(result) for x in ["TJ958", "TJ901", "TJ957"]))

    def test_true_azimuth_enu_axes(self):
        from m1_research.geodesy import ENUFrame
        import numpy as np
        frame = ENUFrame(0, 0, 0)
        np.testing.assert_allclose(frame.to_enu(0, 0, 0), [0, 0, 0], atol=1e-10)
        self.assertGreater(frame.to_enu(0, .001, 0)[0], 0)
        self.assertGreater(frame.to_enu(.001, 0, 0)[1], 0)


if __name__ == "__main__":
    unittest.main()
