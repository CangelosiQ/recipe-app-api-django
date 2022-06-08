"""Tests for the User API"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


@pytest.mark.django_db
def test_create_user_success(api_client):
    """Test creating a user is successful."""
    payload = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test Name",
    }
    res = api_client.post(CREATE_USER_URL, payload)

    assert res.status_code == status.HTTP_201_CREATED
    user = get_user_model().objects.get(email=payload["email"])
    assert user.check_password(payload["password"])
    assert "password" not in res.data


@pytest.mark.django_db
def test_user_with_email_exists_error(api_client):
    """Test error returned if user with email exists."""
    payload = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test Name",
    }
    create_user(**payload)
    res = api_client.post(CREATE_USER_URL, payload)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_password_too_short_error(api_client):
    """Test an error is returned if password less than 5 chars."""
    payload = {
        "email": "test@example.com",
        "password": "pw",
        "name": "Test Name",
    }
    res = api_client.post(CREATE_USER_URL, payload)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert not get_user_model().objects.filter(email=payload["email"]).exists()


@pytest.mark.django_db
def test_create_token_for_user(api_client):
    """Test generates token for valid credentials."""
    user_details = {
        "email": "newtest@example.com",
        "password": "test2password1",
        "name": "Test Name",
    }
    create_user(**user_details)
    payload = {
        "email": user_details["email"],
        "password": user_details["password"],
    }
    res = api_client.post(TOKEN_URL, payload)
    assert res.status_code == status.HTTP_200_OK
    assert "token" in res.json()


@pytest.mark.django_db
def test_create_token_bad_credentials(api_client, default_user):
    """Test returns error if credentials invalid."""
    payload = {
        "email": default_user.email,
        "password": "incorrect-password",
    }
    res = api_client.post(TOKEN_URL, payload)
    assert "token" not in res.json()
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_token_blank_password(api_client, default_user):
    """Test posting a blank password returns an error."""
    payload = {
        "email": default_user.email,
        "password": "",
    }
    res = api_client.post(TOKEN_URL, payload)
    assert "token" not in res.json()
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_retrieve_user_unauthorized(api_client):
    """Test authentication is required for users."""
    res = api_client.get(ME_URL)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_retrieve_profile_success(api_client, authenticated_user):
    """Test retrieving profile for logged in user."""
    res = api_client.get(ME_URL)
    assert res.status_code == status.HTTP_200_OK
    assert res.data == {
        "name": authenticated_user.name,
        "email": authenticated_user.email,
    }


@pytest.mark.django_db
def test_post_me_not_allowed(api_client, authenticated_user):
    """Test POST is not allowed for the me endpoint."""
    res = api_client.post(ME_URL, {})

    assert res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_update_user_profile(api_client, authenticated_user):
    """Test updating the user profile for the authenticated user."""
    payload = {"name": "Updated name", "password": "newpassword123"}

    res = api_client.patch(ME_URL, payload)

    authenticated_user.refresh_from_db()
    assert res.status_code == status.HTTP_200_OK
    authenticated_user.name == payload["name"]
    assert authenticated_user.check_password(payload["password"])
