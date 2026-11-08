"""Conditional 16L horizontal geometry only; no execution or risk experiment."""
import copy
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from m1_research.aip_reference import build_16l_reference
from m1_research.config_loader import load_study
from m1_research.geodesy import ENUFrame, parse_dms
from m1_research.procedure_reference import LineSegment


class LOCHorizontalReferenceTests(unittest.TestCase):
    def setUp(self):
        self.study = load_study()
        self.before = copy.deepcopy(self.study)
        self.model = build_16l_reference(self.study)

    def test_one_line_from_reference_station_to_threshold(self):
        model = self.model
        self.assertEqual(model["status"], "CONDITIONAL_LOC_REFERENCE")
        path = model["path"]
        self.assertEqual(len(path.segments), 1)
        self.assertIsInstance(path.segments[0], LineSegment)
        self.assertTrue(path.require_continuity()["continuous"])
        self.assertAlmostEqual(path.length_m, 16742.69, delta=1.)
        for name, s in (("IF_REFERENCE_STATION", 0.), ("THR", path.length_m)):
            state = path.evaluate(s)
            np.testing.assert_allclose([state["east_m"], state["north_m"]],
                                       model["events"][name]["xy_m"], atol=1e-7)
        for s in np.linspace(0., path.length_m, 5):
            state = path.evaluate(s)
            np.testing.assert_allclose([state["tangent_east"], state["tangent_north"]],
                                       model["derived"]["loc_forward_unit_enu"], atol=1e-12)
            self.assertEqual(state["curvature_1_m"], 0.)

    def test_published_if_and_reference_projection_are_distinct_and_orthogonal(self):
        self.assertEqual(self.study, self.before)
        geometry = self.study["procedures"][0]["reference_geometry"]
        event = self.model["events"]["TJ954_PUBLISHED"]
        self.assertEqual(event["published_point"], geometry["points"]["TJ954"])
        self.assertIsNone(event["s_m"])
        self.assertEqual(event["status"], "SOURCE_VERIFIED")
        station = self.model["events"]["IF_REFERENCE_STATION"]
        self.assertNotEqual(station["status"], "SOURCE_VERIFIED")
        origin = self.study["airport"]["reference_frame"]
        frame = ENUFrame(origin["arp_latitude_deg"], origin["arp_longitude_deg"], origin["arp_elevation_m"])
        published = frame.to_enu(*parse_dms(geometry["points"]["TJ954"]))[:2]
        difference = published-np.array(station["xy_m"])
        u = np.array(self.model["derived"]["loc_forward_unit_enu"])
        self.assertAlmostEqual(float(difference @ u), 0., delta=1e-7)
        self.assertAlmostEqual(np.linalg.norm(difference), 132.04, delta=1.)
        self.assertAlmostEqual(self.model["derived"]["IF_PUBLISHED_TO_LOC_CROSS_TRACK_M"],
                               np.linalg.norm(difference), delta=1e-7)
        self.assertEqual(self.model["derived"]["cross_track_interpretation"],
                         "CONDITIONAL_AXIS_TO_PUBLISHED_FIX_DIAGNOSTIC_NOT_TSE_OR_SIGMA")

    def test_conditional_faf_is_on_axis_and_uses_horizontal_dme_range(self):
        events = self.model["events"]
        faf = events["FAF_D6P2_ICU"]
        self.assertLess(0., faf["s_m"])
        self.assertLess(faf["s_m"], events["THR"]["s_m"])
        self.assertAlmostEqual(faf["s_m"], 5579.72, delta=1.)
        p = self.model["path"].evaluate(faf["s_m"])
        np.testing.assert_allclose([p["east_m"], p["north_m"]], faf["xy_m"], atol=1e-7)
        distance = np.linalg.norm(np.array(faf["xy_m"])-self.model["derived"]["dme_xy_m"])
        self.assertAlmostEqual(distance, 6.2*1852., delta=1e-7)
        self.assertEqual(faf["status"], "CONDITIONAL_DME_HORIZONTAL_EVENT")
        self.assertIn("NOT_SLANT_RANGE", faf["range_interpretation"])
        self.assertIsNone(events["FAP"]["s_m"])
        self.assertIsNone(events["GP_CAPTURE"]["s_m"])
        self.assertEqual(self.model["full_nominal_status"], "UNRESOLVED")

    def test_topology_and_dates_remain_metadata_not_extra_segments(self):
        topology = self.model["program_topology"]
        self.assertEqual(topology["iaf_to_if"], [["TJ919", "TJ954"], ["TJ960", "TJ954"]])
        self.assertEqual(topology["geometry_scope"], "METADATA_ONLY_OUTSIDE_REFERENCE_SUPPORT")
        self.assertEqual(self.model["source_versions"]["H01_5A"], "2024-10-31")
        self.assertEqual(self.model["source_versions"]["H01_AD2025"], "2025-10-02")
        self.assertEqual(self.model["compatibility_status"], "CROSS_DATE_UNVERIFIED")
        self.assertEqual(self.model["entry_event_id"], "IF_REFERENCE_STATION")

    def test_invalid_reference_event_order_is_rejected(self):
        self.study["procedures"][0]["reference_geometry"]["faf_dme_nm"] = 20.
        with self.assertRaisesRegex(ValueError, "SOURCE_GEOMETRY_CONFLICT"):
            build_16l_reference(self.study)


if __name__ == "__main__":
    unittest.main()
