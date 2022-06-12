"""
Tests for the health check API.
"""
from django.urls import reverse

from rest_framework import status


def test_health_check(api_client):
    """Test health check API."""

    url = reverse("health-check")
    res = api_client.get(url)

    assert res.status_code == status.HTTP_200_OK
