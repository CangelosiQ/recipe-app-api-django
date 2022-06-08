"""
Tests for recipe APIs.
"""
from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status

from core.models import Recipe
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


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


@pytest.mark.django_db
def test_auth_required(api_client):
    """Test auth is required to call API."""
    res = api_client.get(RECIPES_URL)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_retrieve_recipes(api_client, authenticated_user):
    """Test retrieving a list of recipes."""
    create_recipe(user=authenticated_user)
    create_recipe(user=authenticated_user)

    res = api_client.get(RECIPES_URL)

    recipes = Recipe.objects.all().order_by("-id")
    serializer = RecipeSerializer(recipes, many=True)
    assert res.status_code == status.HTTP_200_OK
    assert res.data == serializer.data


@pytest.mark.django_db
def test_recipe_list_limited_to_user(api_client, authenticated_user, create_user):
    """Test list of recipes is limited to authenticated user."""
    other_user = create_user(email="other@example.com", password="password123")
    create_recipe(user=other_user)
    create_recipe(user=authenticated_user)

    res = api_client.get(RECIPES_URL)

    recipes = Recipe.objects.filter(user=authenticated_user)
    serializer = RecipeSerializer(recipes, many=True)
    assert res.status_code == status.HTTP_200_OK
    assert res.data == serializer.data


@pytest.mark.django_db
def test_get_recipe_detail(api_client, authenticated_user):
    """Test get recipe detail."""
    recipe = create_recipe(authenticated_user)

    url = detail_url(recipe.id)
    res = api_client.get(url)

    serializer = RecipeDetailSerializer(recipe)
    assert res.data == serializer.data


@pytest.mark.django_db
def test_create_recipe(api_client, authenticated_user):
    """Test creating a recipe."""
    payload = {
        "title": "Sample recipe",
        "time_minutes": 30,
        "price": Decimal("5.99"),
    }
    res = api_client.post(RECIPES_URL, payload)

    assert res.status_code == status.HTTP_201_CREATED
    recipe = Recipe.objects.get(id=res.data["id"])
    for k, v in payload.items():
        assert getattr(recipe, k) == v
    assert recipe.user == authenticated_user


@pytest.mark.django_db
def test_partial_update(api_client, authenticated_user):
    """Test partial update of a recipe."""
    original_link = "https://example.com/recipe.pdf"
    recipe = create_recipe(
        user=authenticated_user, title="Sample recipe title", link=original_link,
    )

    payload = {"title": "New recipe title"}
    url = detail_url(recipe.id)
    res = api_client.patch(url, payload)

    assert res.status_code == status.HTTP_200_OK
    recipe.refresh_from_db()
    assert recipe.title == payload["title"]
    assert recipe.link == original_link
    assert recipe.user == authenticated_user


@pytest.mark.django_db
def test_full_update(api_client, authenticated_user, create_user):
    """Test full update of recipe."""
    recipe = create_recipe(
        user=authenticated_user,
        title="Sample recipe title",
        link="https://exmaple.com/recipe.pdf",
        description="Sample recipe description.",
    )

    payload = {
        "title": "New recipe title",
        "link": "https://example.com/new-recipe.pdf",
        "description": "New recipe description",
        "time_minutes": 10,
        "price": Decimal("2.50"),
    }
    url = detail_url(recipe.id)
    res = api_client.put(url, payload)

    assert res.status_code == status.HTTP_200_OK
    recipe.refresh_from_db()
    for k, v in payload.items():
        assert getattr(recipe, k) == v
    assert recipe.user == authenticated_user


@pytest.mark.django_db
def test_update_user_returns_error(api_client, authenticated_user, create_user):
    """Test changing the recipe user results in an error."""
    new_user = create_user(email="user2@example.com", password="test123")
    recipe = create_recipe(user=authenticated_user)

    payload = {"user": new_user.id}
    url = detail_url(recipe.id)
    api_client.patch(url, payload)

    recipe.refresh_from_db()
    assert recipe.user == authenticated_user


@pytest.mark.django_db
def test_delete_recipe(api_client, authenticated_user):
    """Test deleting a recipe successful."""
    recipe = create_recipe(user=authenticated_user)

    url = detail_url(recipe.id)
    res = api_client.delete(url)

    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not Recipe.objects.filter(id=recipe.id).exists()


@pytest.mark.django_db
def test_delete_other_users_recipe_error(api_client, authenticated_user, create_user):
    """Test trying to delete another users recipe gives error."""
    new_user = create_user(email="user2@example.com", password="test123")
    recipe = create_recipe(user=new_user)

    url = detail_url(recipe.id)
    res = api_client.delete(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert Recipe.objects.filter(id=recipe.id).exists()
