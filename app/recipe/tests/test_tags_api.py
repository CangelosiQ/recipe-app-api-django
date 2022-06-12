"""
Tests for the tags API.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer
from conftest import create_user

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse("recipe:tag-detail", args=[tag_id])


@pytest.mark.django_db
def test_auth_required(api_client):
    """Test auth is required for retrieving tags."""
    res = api_client.get(TAGS_URL)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_retrieve_tags(api_client, authenticated_user):
    """Test retrieving a list of tags."""
    Tag.objects.create(user=authenticated_user, name="Vegan")
    Tag.objects.create(user=authenticated_user, name="Dessert")

    res = api_client.get(TAGS_URL)

    tags = Tag.objects.all().order_by("-name")
    serializer = TagSerializer(tags, many=True)
    assert res.status_code == status.HTTP_200_OK
    assert res.data == serializer.data


@pytest.mark.django_db
def test_tags_limited_to_user(api_client, authenticated_user):
    """Test list of tags is limited to authenticated user."""
    user2 = create_user(email="user2@example.com", password="pass132")
    Tag.objects.create(user=user2, name="Fruity")
    tag = Tag.objects.create(user=authenticated_user, name="Comfort Food")

    res = api_client.get(TAGS_URL)

    assert res.status_code == status.HTTP_200_OK
    assert len(res.data) == 1
    assert res.data[0]["name"] == tag.name
    assert res.data[0]["id"] == tag.id


@pytest.mark.django_db
def test_update_tag(api_client, authenticated_user):
    """Test updating a tag."""
    tag = Tag.objects.create(user=authenticated_user, name="After Dinner")

    payload = {"name": "Dessert"}
    url = detail_url(tag.id)
    res = api_client.patch(url, payload)

    assert res.status_code == status.HTTP_200_OK
    tag.refresh_from_db()
    assert tag.name == payload["name"]


@pytest.mark.django_db
def test_delete_tag(api_client, authenticated_user):
    """Test deleting a tag."""
    tag = Tag.objects.create(user=authenticated_user, name="Breakfast")

    url = detail_url(tag.id)
    res = api_client.delete(url)

    assert res.status_code == status.HTTP_204_NO_CONTENT
    tags = Tag.objects.filter(user=authenticated_user)
    assert not tags.exists()


@pytest.mark.django_db
def test_filter_tags_assigned_to_recipes(authenticated_user, api_client):
    """Test listing tags to those assigned to recipes."""
    tag1 = Tag.objects.create(user=authenticated_user, name="Breakfast")
    tag2 = Tag.objects.create(user=authenticated_user, name="Lunch")
    recipe = Recipe.objects.create(
        title="Green Eggs on Toast",
        time_minutes=10,
        price=Decimal("2.50"),
        user=authenticated_user,
    )
    recipe.tags.add(tag1)

    res = api_client.get(TAGS_URL, {"assigned_only": 1})

    s1 = TagSerializer(tag1)
    s2 = TagSerializer(tag2)
    assert s1.data in res.data
    assert s2.data not in res.data


@pytest.mark.django_db
def test_filtered_tags_unique(authenticated_user, api_client):
    """Test filtered tags returns a unique list."""
    tag = Tag.objects.create(user=authenticated_user, name="Breakfast")
    Tag.objects.create(user=authenticated_user, name="Dinner")
    recipe1 = Recipe.objects.create(
        title="Pancakes",
        time_minutes=5,
        price=Decimal("5.00"),
        user=authenticated_user,
    )
    recipe2 = Recipe.objects.create(
        title="Porridge",
        time_minutes=3,
        price=Decimal("2.00"),
        user=authenticated_user,
    )
    recipe1.tags.add(tag)
    recipe2.tags.add(tag)

    res = api_client.get(TAGS_URL, {"assigned_only": 1})

    assert len(res.data) == 1
