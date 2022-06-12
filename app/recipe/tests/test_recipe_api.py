"""
Tests for recipe APIs.
"""
from decimal import Decimal
import tempfile
import os

from PIL import Image
import pytest
from django.urls import reverse
from rest_framework import status

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)
from conftest import create_recipe, create_user


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return an image upload URL."""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


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
def test_recipe_list_limited_to_user(api_client, authenticated_user):
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
def test_full_update(api_client, authenticated_user):
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
def test_update_user_returns_error(api_client, authenticated_user, recipe):
    """Test changing the recipe user results in an error."""
    new_user = create_user(email="user2@example.com", password="test123")

    payload = {"user": new_user.id}
    url = detail_url(recipe.id)
    api_client.patch(url, payload)

    recipe.refresh_from_db()
    assert recipe.user == authenticated_user


@pytest.mark.django_db
def test_delete_recipe(api_client, authenticated_user, recipe):
    """Test deleting a recipe successful."""

    url = detail_url(recipe.id)
    res = api_client.delete(url)

    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not Recipe.objects.filter(id=recipe.id).exists()


@pytest.mark.django_db
def test_delete_other_users_recipe_error(api_client, authenticated_user):
    """Test trying to delete another users recipe gives error."""
    new_user = create_user(email="user2@example.com", password="test123")
    recipe = create_recipe(user=new_user)

    url = detail_url(recipe.id)
    res = api_client.delete(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert Recipe.objects.filter(id=recipe.id).exists()


@pytest.mark.django_db
def test_create_recipe_with_new_tags(api_client, authenticated_user):
    """Test creating a recipe with new tags."""
    payload = {
        "title": "Thai Prawn Curry",
        "time_minutes": 30,
        "price": Decimal("2.50"),
        "tags": [{"name": "Thai"}, {"name": "Dinner"}],
    }
    res = api_client.post(RECIPES_URL, payload, format="json")

    assert res.status_code == status.HTTP_201_CREATED
    recipes = Recipe.objects.filter(user=authenticated_user)
    assert recipes.count() == 1
    recipe = recipes[0]
    assert recipe.tags.count() == 2
    for tag in payload["tags"]:
        exists = recipe.tags.filter(name=tag["name"], user=authenticated_user,).exists()
        assert exists


@pytest.mark.django_db
def test_create_recipe_with_existing_tags(api_client, authenticated_user):
    """Test creating a recipe with existing tag."""
    tag_indian = Tag.objects.create(user=authenticated_user, name="Indian")
    payload = {
        "title": "Pongal",
        "time_minutes": 60,
        "price": Decimal("4.50"),
        "tags": [{"name": "Indian"}, {"name": "Breakfast"}],
    }
    res = api_client.post(RECIPES_URL, payload, format="json")

    assert res.status_code == status.HTTP_201_CREATED
    recipes = Recipe.objects.filter(user=authenticated_user)
    assert recipes.count() == 1
    recipe = recipes[0]
    assert recipe.tags.count() == 2
    assert tag_indian in recipe.tags.all()
    for tag in payload["tags"]:
        exists = recipe.tags.filter(name=tag["name"], user=authenticated_user,).exists()
        assert exists


@pytest.mark.django_db
def test_create_tag_on_update(api_client, authenticated_user, recipe):
    """Test create tag when updating a recipe."""

    payload = {"tags": [{"name": "Lunch"}]}
    url = detail_url(recipe.id)
    res = api_client.patch(url, payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    new_tag = Tag.objects.get(user=authenticated_user, name="Lunch")
    assert new_tag in recipe.tags.all()


@pytest.mark.django_db
def test_update_recipe_assign_tag(api_client, authenticated_user, recipe):
    """Test assigning an existing tag when updating a recipe."""
    tag_breakfast = Tag.objects.create(user=authenticated_user, name="Breakfast")
    recipe.tags.add(tag_breakfast)

    tag_lunch = Tag.objects.create(user=authenticated_user, name="Lunch")
    payload = {"tags": [{"name": "Lunch"}]}
    url = detail_url(recipe.id)
    res = api_client.patch(url, payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    assert tag_lunch in recipe.tags.all()
    assert tag_breakfast not in recipe.tags.all()


@pytest.mark.django_db
def test_clear_recipe_tags(api_client, authenticated_user, recipe):
    """Test clearing a recipes tags."""
    tag = Tag.objects.create(user=authenticated_user, name="Dessert")
    recipe.tags.add(tag)

    payload = {"tags": []}
    url = detail_url(recipe.id)
    res = api_client.patch(url, payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    assert recipe.tags.count() == 0


@pytest.mark.django_db
def test_create_recipe_with_new_ingredients(api_client, authenticated_user):
    """Test creating a recipe with new ingredients."""
    payload = {
        "title": "Thai Prawn Curry",
        "time_minutes": 30,
        "price": Decimal("2.50"),
        "ingredients": [{"name": "Cream"}, {"name": "Coffee"}],
    }
    res = api_client.post(RECIPES_URL, payload, format="json")

    assert res.status_code == status.HTTP_201_CREATED
    recipes = Recipe.objects.filter(user=authenticated_user)
    assert recipes.count() == 1
    recipe = recipes[0]
    assert recipe.ingredients.count() == 2
    for ingredient in payload["ingredients"]:
        exists = recipe.ingredients.filter(
            name=ingredient["name"], user=authenticated_user,
        ).exists()
        assert exists


@pytest.mark.django_db
def test_create_recipe_with_existing_ingredients(api_client, authenticated_user):
    """Test creating a recipe with existing ingredient."""
    ingredient_brocoli = Ingredient.objects.create(
        user=authenticated_user, name="Brocoli"
    )
    payload = {
        "title": "Pongal",
        "time_minutes": 60,
        "price": Decimal("4.50"),
        "ingredients": [{"name": "Brocoli"}, {"name": "Salt"}],
    }
    res = api_client.post(RECIPES_URL, payload, format="json")

    assert res.status_code == status.HTTP_201_CREATED
    recipes = Recipe.objects.filter(user=authenticated_user)
    assert recipes.count() == 1
    recipe = recipes[0]
    assert recipe.ingredients.count() == 2
    assert ingredient_brocoli in recipe.ingredients.all()
    for ingredient in payload["ingredients"]:
        exists = recipe.ingredients.filter(
            name=ingredient["name"], user=authenticated_user,
        ).exists()
        assert exists


@pytest.mark.django_db
def test_create_ingredient_on_update(api_client, authenticated_user, recipe):
    """Test create ingredient when updating a recipe."""

    payload = {"ingredients": [{"name": "Carrot"}]}
    url = detail_url(recipe.id)
    res = api_client.patch(url, payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    new_ingredient = Ingredient.objects.get(user=authenticated_user, name="Carrot")
    assert new_ingredient in recipe.ingredients.all()


@pytest.mark.django_db
def test_update_recipe_assign_ingredient(api_client, authenticated_user, recipe):
    """Test assigning an existing ingredient when updating a recipe."""
    ingredient_apple = Ingredient.objects.create(user=authenticated_user, name="Apple")
    recipe.ingredients.add(ingredient_apple)

    ingredient_lemon = Ingredient.objects.create(user=authenticated_user, name="Lemon")
    payload = {"ingredients": [{"name": "Lemon"}]}
    url = detail_url(recipe.id)
    res = api_client.patch(url, payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    assert ingredient_lemon in recipe.ingredients.all()
    assert ingredient_apple not in recipe.ingredients.all()


@pytest.mark.django_db
def test_clear_recipe_ingredients(api_client, authenticated_user, recipe):
    """Test clearing a recipes ingredients."""
    ingredient = Ingredient.objects.create(user=authenticated_user, name="Dessert")
    recipe.ingredients.add(ingredient)

    payload = {"ingredients": []}
    url = detail_url(recipe.id)
    res = api_client.patch(url, payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    assert recipe.ingredients.count() == 0


@pytest.mark.django_db
def test_upload_image(api_client, recipe):
    """Test uploading an image to a recipe."""
    url = image_upload_url(recipe.id)
    with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
        img = Image.new("RGB", (10, 10))
        img.save(image_file, format="JPEG")
        image_file.seek(0)
        payload = {"image": image_file}
        res = api_client.post(url, payload, format="multipart")

    recipe.refresh_from_db()
    assert res.status_code == status.HTTP_200_OK
    assert "image" in res.data
    assert os.path.exists(recipe.image.path)


@pytest.mark.django_db
def test_upload_image_bad_request(api_client, recipe):
    """Test uploading an invalid image."""
    url = image_upload_url(recipe.id)
    payload = {"image": "notanimage"}
    res = api_client.post(url, payload, format="multipart")

    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_filter_by_tags(api_client, authenticated_user):
    """Test filtering recipes by tags."""
    r1 = create_recipe(user=authenticated_user, title="Thai Vegetable Curry")
    r2 = create_recipe(user=authenticated_user, title="Aubergine with Tahini")
    tag1 = Tag.objects.create(user=authenticated_user, name="Vegan")
    tag2 = Tag.objects.create(user=authenticated_user, name="Vegetarian")
    r1.tags.add(tag1)
    r2.tags.add(tag2)
    r3 = create_recipe(user=authenticated_user, title="Fish and chips")

    params = {"tags": f"{tag1.id},{tag2.id}"}
    res = api_client.get(RECIPES_URL, params)

    s1 = RecipeSerializer(r1)
    s2 = RecipeSerializer(r2)
    s3 = RecipeSerializer(r3)
    assert s1.data in res.data
    assert s2.data in res.data
    assert s3.data not in res.data


@pytest.mark.django_db
def test_filter_by_ingredients(api_client, authenticated_user):
    """Test filtering recipes by ingredients."""
    r1 = create_recipe(user=authenticated_user, title="Posh Beans on Toast")
    r2 = create_recipe(user=authenticated_user, title="Chicken Cacciatore")
    in1 = Ingredient.objects.create(user=authenticated_user, name="Feta Cheese")
    in2 = Ingredient.objects.create(user=authenticated_user, name="Chicken")
    r1.ingredients.add(in1)
    r2.ingredients.add(in2)
    r3 = create_recipe(user=authenticated_user, title="Red Lentil Daal")

    params = {"ingredients": f"{in1.id},{in2.id}"}
    res = api_client.get(RECIPES_URL, params)

    s1 = RecipeSerializer(r1)
    s2 = RecipeSerializer(r2)
    s3 = RecipeSerializer(r3)
    assert s1.data in res.data
    assert s2.data in res.data
    assert s3.data not in res.data
