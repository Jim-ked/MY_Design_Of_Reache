import math
import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from m1_research.procedure_reference import CircularArc, LineSegment, ReferencePath


class ReferenceGeometryTests(unittest.TestCase):
    def test_circle_and_line_have_expected_boundary_states(self):
        arc = CircularArc(10.0, math.pi / 2.0, (0.0, 0.0), 0.0, 1, "RF")
        line = LineSegment(5.0, (0.0, 10.0), -math.pi / 2.0, "TF")
        path = ReferencePath([arc, line])
        mid = path.evaluate(arc.length_m / 2.0)
        self.assertAlmostEqual(mid["curvature_1_m"], 0.1)
        self.assertAlmostEqual(np.hypot(mid["tangent_east"], mid["tangent_north"]), 1.0)
        boundary = path.boundary_states()[1]
        self.assertAlmostEqual(boundary["left"]["east_m"], boundary["right"]["east_m"])
        self.assertAlmostEqual(boundary["left"]["north_m"], boundary["right"]["north_m"])
        self.assertAlmostEqual(boundary["left"]["curvature_1_m"], 0.1)
        self.assertAlmostEqual(boundary["right"]["curvature_1_m"], 0.0)


if __name__ == "__main__":
    unittest.main()
