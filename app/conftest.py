"""
Config Tests Pytest
"""

from decimal import Decimal
from pathlib import Path
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Recipe

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


def create_user(**params):
    """Return function to create a new user"""
    return get_user_model().objects.create_user(**params)


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        "title": "Sample recipe title",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


@pytest.fixture
def recipe(authenticated_user):
    """Create and return a recipe for the authenticated user."""
    _recipe = create_recipe(user=authenticated_user)
    yield _recipe
    _recipe.image.delete()
