from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def resources_dir() -> Path:
    return ROOT / "resources"
