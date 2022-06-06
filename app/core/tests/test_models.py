"""
Test for models.
"""
from django.contrib.auth import get_user_model
import pytest


@pytest.mark.django_db
def test_create_user_with_email_successfull():
    """Test creating a user with an email is successfull"""
    email = "test@example.com"
    password = "testpass123"
    print(get_user_model())
    print(get_user_model().objects)
    print(type(get_user_model().objects))
    print(dir(get_user_model()))

    user = get_user_model().objects.create_user(email=email, password=password)
    assert user.email == email
    user.check_password(password)


@pytest.mark.django_db
def test_new_user_email_is_normalized():
    """Test email is normalized for new users."""
    sample_emails = [
        ["test1@EXAMPLE.com", "test1@example.com"],
        ["Test2@Example.com", "Test2@example.com"],
        ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
        ["test4@example.COM", "test4@example.com"],
    ]
    for email, expected in sample_emails:
        user = get_user_model().objects.create_user(email, "sample123")
        assert user.email == expected


@pytest.mark.django_db
def test_new_user_without_email_raises_error():
    """Test that creating a user without email raises a ValueError."""
    with pytest.raises(ValueError):
        get_user_model().objects.create_user("", "sample123")


@pytest.mark.django_db
def test_create_superuser():
    """Test creating a superuser."""
    user = get_user_model().objects.create_superuser("test", "sample123")
    assert user.is_superuser
    assert user.is_staff
