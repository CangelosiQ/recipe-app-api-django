"""
Tests for the Django admin modifications.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
import pytest


@pytest.fixture()
def client():
    yield Client()


@pytest.fixture()
def with_admin_user(client):
    user = get_user_model().objects.create_superuser(
        email="admin@example.com", password="testpass123"
    )
    client.force_login(user)
    return user


@pytest.fixture()
def user(client):
    user = get_user_model().objects.create_user(
        email="test@example.com", password="test123", name="Test User"
    )
    return user


@pytest.mark.django_db
def test_users_list(client, user):
    url = reverse("admin:core_user_changelist")
    res = client.get(url)
    user.name in res
    user.email in res


@pytest.mark.django_db
def test_edit_user_page(client, with_admin_user, user):
    """Test the edit user page works."""
    url = reverse("admin:core_user_change", args=[user.id])
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_create_user_page(client, with_admin_user, user):
    """Test create the user page works."""
    url = reverse("admin:core_user_add")
    res = client.get(url)
    assert res.status_code == 200
