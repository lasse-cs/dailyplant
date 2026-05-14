import pytest
from pytest_django.asserts import assertTemplateUsed

from django.urls import reverse
from django.test import Client


@pytest.mark.django_db
def test_404_view(client):
    response = client.get("/this-view-should-not-be-found/")
    assert response.status_code == 404
    assertTemplateUsed("patterns/pages/error/404.html")


def test_500_view(admin_user, settings):
    settings.DEBUG = False
    settings.DEBUG_PROPAGATE_EXCEPTIONS = False
    client = Client(raise_request_exception=False)
    client.force_login(admin_user)
    response = client.get(reverse("server_error"))
    assert response.status_code == 500
    assertTemplateUsed(response, "patterns/pages/error/500.html")
