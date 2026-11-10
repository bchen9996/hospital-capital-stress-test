"""Load config.yaml."""

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Return the parsed config.yaml (project root by default)."""
    with open(path or PROJECT_ROOT / "config.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
