"""
"""
import pytest
from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError


@pytest.fixture()
def mocked_check_for_db(mocker):
    return mocker.patch("core.management.commands.wait_for_db.Command.check")


def test_wait_for_db_ready(mocked_check_for_db):
    """Test waiting for database if database ready."""
    mocked_check_for_db.return_value = True
    print(mocked_check_for_db)
    print(dir(mocked_check_for_db))
    print("hello")
    call_command("wait_for_db")
    mocked_check_for_db.assert_called_once_with(databases=["default"])


def test_wait_for_db_delay(mocker, mocked_check_for_db):
    """Test waiting for database when getting OperationalError."""
    mocker.patch("time.sleep")
    mocked_check_for_db.side_effect = (
        [Psycopg2Error] * 2 + [OperationalError] * 3 + [True]
    )
    print(dir(mocked_check_for_db))
    call_command("wait_for_db")
    assert mocked_check_for_db.call_count == 6
    mocked_check_for_db.assert_called_with(databases=["default"])
