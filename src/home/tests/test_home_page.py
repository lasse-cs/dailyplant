import pytest
from pytest_django.asserts import assertTemplateUsed

from home.factories import HomePageFactory


@pytest.mark.django_db
def test_home_page_renders(client, root_page):
    home_page = HomePageFactory(parent=root_page)
    response = client.get(home_page.url)
    assert response.status_code == 200
    assertTemplateUsed(response, "patterns/pages/home/home_page.html")
