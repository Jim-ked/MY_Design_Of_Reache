"""Load the single clean-room study configuration."""

from pathlib import Path
from typing import Any

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
STUDY_PATH = PACKAGE_ROOT / "config" / "study.yaml"
REQUIRED_SECTIONS = {
    "schema", "airport", "procedures", "aircraft", "operations",
    "uncertainty", "scenarios", "provenance",
}


class ConfigurationError(ValueError):
    """Raised when the clean-room configuration is not self-contained."""


def load_study(path: str | Path | None = None) -> dict[str, Any]:
    """Load only ``research_m1/config/study.yaml``.

    A caller may pass the exact package path, but external files and fallback
    configuration names are rejected deliberately.
    """
    requested = STUDY_PATH if path is None else Path(path).resolve()
    if requested != STUDY_PATH.resolve():
        raise ConfigurationError("only research_m1/config/study.yaml is accepted")
    if not requested.is_file():
        raise ConfigurationError(f"missing study configuration: {requested}")
    data = yaml.safe_load(requested.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != REQUIRED_SECTIONS:
        raise ConfigurationError(
            f"study.yaml must contain exactly {sorted(REQUIRED_SECTIONS)}"
        )
    return data


def study_status(study: dict[str, Any]) -> str:
    """Return the conservative status implied by unresolved required inputs."""
    if not isinstance(study, dict):
        raise ConfigurationError("study must be a mapping")
    if any((item.get("reference_geometry") or {}).get("source_status") == "SOURCE_VERIFIED"
           for item in study.get("procedures", [])):
        return "PARTIAL_REFERENCE"
    return "REFERENCE_ONLY"
