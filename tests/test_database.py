"""
tests/test_database.py
=======================
PURPOSE:
    Unit test for the database connection check function.

TESTS:
    - check_db_connection() calls sys.exit(1) when Supabase is unreachable.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("GROQ_API_KEY", "test_key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test_anon_key")
os.environ.setdefault("FRAUD_THRESHOLD", "0.70")
os.environ.setdefault("MODEL_PATH", "models/fraud_model.joblib")


def test_unit_db_connection_failure_exits_nonzero():
    """
    If Supabase raises an exception during check_db_connection(),
    the function must call sys.exit(1).

    Validates Requirement 8.6
    """
    from database import check_db_connection

    with patch("database.supabase_client") as mock_client:
        # Simulate a connection failure
        mock_table = MagicMock()
        mock_table.select.return_value.limit.return_value.execute.side_effect = Exception(
            "Connection refused: Supabase unreachable"
        )
        mock_client.table.return_value = mock_table

        # check_db_connection() must call sys.exit(1)
        with pytest.raises(SystemExit) as exc_info:
            check_db_connection()

        assert exc_info.value.code == 1, (
            f"Expected exit code 1, got {exc_info.value.code}"
        )
