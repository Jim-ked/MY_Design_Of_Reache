from pathlib import Path
import unittest


class CleanroomIndependenceTests(unittest.TestCase):
    def test_new_source_has_no_historical_import_or_alias(self):
        source_root = Path(__file__).resolve().parents[1] / "src"
        forbidden = (
            "from src", "import src", "../config", "human_baseline",
            "rpas_baseline", "U90", "HL_REF", "HH", "legacy",
        )
        for path in source_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"forbidden token {token!r} in {path}")


if __name__ == "__main__":
    unittest.main()
