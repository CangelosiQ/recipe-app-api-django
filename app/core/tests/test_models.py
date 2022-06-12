"""
Test for models.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
import pytest

from core import models
from conftest import create_user


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


@pytest.mark.django_db
def test_create_recipe():
    """Test creating a recipe is successful."""
    user = get_user_model().objects.create_user("test@example.com", "testpass123",)
    recipe = models.Recipe.objects.create(
        user=user,
        title="Sample recipe name",
        time_minutes=5,
        price=Decimal("5.50"),
        description="Sample recipe description.",
    )

    assert str(recipe) == recipe.title


@pytest.mark.django_db
def test_create_tag():
    """Test creating a tag is successful."""
    user = create_user(email="user@example.com", password="pass123")
    tag = models.Tag.objects.create(user=user, name="Tag1")

    assert str(tag) == tag.name


@pytest.mark.django_db
def test_create_ingredient():
    """Test creating a ingredient is successful."""
    user = create_user(email="user@example.com", password="pass123")
    ingredient = models.Ingredient.objects.create(user=user, name="ingredient1")

    assert str(ingredient) == ingredient.name


def test_recipe_file_name_uuid(mocker):
    """Test generating image path."""
    uuid = "test-uuid"
    mocker.patch("core.models.uuid.uuid4", return_value=uuid)
    file_path = models.recipe_image_file_path(None, "example.jpg")

    assert file_path == f"uploads/recipe/{uuid}.jpg"
