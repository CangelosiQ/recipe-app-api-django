"""
Config Tests Pytest
"""

from pathlib import Path
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

root_tests = str(Path(__file__).parent)


@pytest.fixture()
def client():
    yield Client()


@pytest.fixture()
def api_client():
    yield APIClient()


@pytest.fixture()
def with_admin_user(client):
    user = get_user_model().objects.create_superuser(
        email="admin@example.com", password="testpass123"
    )
    client.force_login(user)
    return user


@pytest.fixture()
def default_user(client):
    user = get_user_model().objects.create_user(
        email="test@example.com", password="test123", name="Test User"
    )
    return user


@pytest.fixture
def authenticated_user(api_client):
    user = get_user_model().objects.create_user(
        email="test@example.com", password="test123", name="Test User"
    )
    api_client.force_authenticate(user=user)
    return user


@pytest.fixture
def create_user():
    """Create and return a new user"""
    return lambda **params: get_user_model().objects.create_user(**params)
