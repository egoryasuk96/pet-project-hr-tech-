"""Stage 5.3 Pre-E2 auth tests — superseded by E3.1 Target API tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(
    reason="Pre-E2 UUID/snapshot API; superseded by tests/test_e31_target_api.py"
)
