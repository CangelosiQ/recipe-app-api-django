"""
Tests for the Django admin modifications.
"""

from django.urls import reverse
import pytest


@pytest.mark.django_db
def test_users_list(client, default_user):
    url = reverse("admin:core_user_changelist")
    res = client.get(url)
    default_user.name in res
    default_user.email in res


@pytest.mark.django_db
def test_edit_user_page(client, with_admin_user, default_user):
    """Test the edit user page works."""
    url = reverse("admin:core_user_change", args=[default_user.id])
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_create_user_page(client, with_admin_user, default_user):
    """Test create the user page works."""
    url = reverse("admin:core_user_add")
    res = client.get(url)
    assert res.status_code == 200
