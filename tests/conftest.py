"""This file is used to set up the test environment for Home Assistant custom components."""

import sys
from pathlib import Path

# When this file is at <repo>/tests/conftest.py, parents[1] is the repo root
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))