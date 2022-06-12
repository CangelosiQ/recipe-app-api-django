"""
Tests for the ingredients API.
"""
from decimal import Decimal
from django.urls import reverse
import pytest
from rest_framework import status

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer
from conftest import create_user

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Create and return a ingredient detail url."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


@pytest.mark.django_db
def test_auth_required(api_client):
    """Test auth is required for retrieving ingredients."""
    res = api_client.get(INGREDIENTS_URL)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_retrieve_ingredients(api_client, authenticated_user):
    """Test retrieving a list of ingredients."""
    Ingredient.objects.create(user=authenticated_user, name="Chocolate")
    Ingredient.objects.create(user=authenticated_user, name="Vanilla")

    res = api_client.get(INGREDIENTS_URL)

    ingredients = Ingredient.objects.all().order_by("-name")
    serializer = IngredientSerializer(ingredients, many=True)
    assert res.status_code == status.HTTP_200_OK
    assert res.data == serializer.data


@pytest.mark.django_db
def test_ingredients_limited_to_user(api_client, authenticated_user):
    """Test list of ingredients is limited to authenticated user."""
    user2 = create_user(email="user2@example.com", password="pass132")
    Ingredient.objects.create(user=user2, name="Fruity")
    ingredient = Ingredient.objects.create(user=authenticated_user, name="Comfort Food")

    res = api_client.get(INGREDIENTS_URL)

    assert res.status_code == status.HTTP_200_OK
    assert len(res.data) == 1
    assert res.data[0]["name"] == ingredient.name
    assert res.data[0]["id"] == ingredient.id


@pytest.mark.django_db
def test_update_ingredient(api_client, authenticated_user):
    """Test updating a ingredient."""
    ingredient = Ingredient.objects.create(user=authenticated_user, name="Cilantro")

    payload = {"name": "Coriander"}
    url = detail_url(ingredient.id)
    res = api_client.patch(url, payload)

    assert res.status_code == status.HTTP_200_OK
    ingredient.refresh_from_db()
    assert ingredient.name == payload["name"]


@pytest.mark.django_db
def test_delete_ingredient(api_client, authenticated_user):
    """Test deleting a ingredient."""
    ingredient = Ingredient.objects.create(user=authenticated_user, name="Salad")

    url = detail_url(ingredient.id)
    res = api_client.delete(url)

    assert res.status_code == status.HTTP_204_NO_CONTENT
    ingredients = Ingredient.objects.filter(user=authenticated_user)
    assert not ingredients.exists()


@pytest.mark.django_db
def test_filter_ingredients_assigned_to_recipes(api_client, authenticated_user):
    """Test listing ingedients to those assigned to recipes."""
    in1 = Ingredient.objects.create(user=authenticated_user, name="Apples")
    in2 = Ingredient.objects.create(user=authenticated_user, name="Turkey")
    recipe = Recipe.objects.create(
        title="Apple Crumble",
        time_minutes=5,
        price=Decimal("4.50"),
        user=authenticated_user,
    )
    recipe.ingredients.add(in1)

    res = api_client.get(INGREDIENTS_URL, {"assigned_only": 1})

    s1 = IngredientSerializer(in1)
    s2 = IngredientSerializer(in2)
    assert s1.data in res.data
    assert s2.data not in res.data


@pytest.mark.django_db
def test_filtered_ingredients_unique(api_client, authenticated_user):
    """Test filtered ingredients returns a unique list."""
    ing = Ingredient.objects.create(user=authenticated_user, name="Eggs")
    Ingredient.objects.create(user=authenticated_user, name="Lentils")
    recipe1 = Recipe.objects.create(
        title="Eggs Benedict",
        time_minutes=60,
        price=Decimal("7.00"),
        user=authenticated_user,
    )
    recipe2 = Recipe.objects.create(
        title="Herb Eggs",
        time_minutes=20,
        price=Decimal("4.00"),
        user=authenticated_user,
    )
    recipe1.ingredients.add(ing)
    recipe2.ingredients.add(ing)

    res = api_client.get(INGREDIENTS_URL, {"assigned_only": 1})

    assert len(res.data) == 1
