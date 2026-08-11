import pytest
from django.core.exceptions import ImproperlyConfigured
from pytest_django.asserts import assertTemplateUsed

from core.factories import RelatedPagesExplorerPageFactory
from core.testapp.factories import (
    MissingDetailsTemplatePageFactory,
    RelatedPagesTestPageFactory,
)


@pytest.mark.django_db
def test_related_page_implementer_must_declare_details_template(client, root_page):
    page = MissingDetailsTemplatePageFactory(parent=root_page, title="Missing")

    with pytest.raises(ImproperlyConfigured):
        client.get(
            page.url,
            headers={
                "HX-Request": "true",
                "HX-Target": "explorer-details-content",
            },
        )


@pytest.mark.django_db
def test_related_page_returns_details_for_explorer_htmx_target(client, root_page):
    page = RelatedPagesTestPageFactory(parent=root_page, title="Related page")

    response = client.get(
        page.url,
        headers={
            "HX-Request": "true",
            "HX-Target": "explorer-details-content",
        },
    )

    assert response.status_code == 200
    assertTemplateUsed(response, "core_testapp/related_page_details.html")
    assert "HX-Request" in response.headers["Vary"]
    assert "HX-Target" in response.headers["Vary"]


@pytest.mark.django_db
def test_related_page_uses_full_template_for_other_requests(client, root_page):
    page = RelatedPagesTestPageFactory(parent=root_page)

    normal_response = client.get(page.url)
    other_htmx_response = client.get(
        page.url,
        headers={"HX-Request": "true", "HX-Target": "another-target"},
    )

    assertTemplateUsed(normal_response, "core_testapp/related_pages_test_page.html")
    assertTemplateUsed(other_htmx_response, "core_testapp/related_pages_test_page.html")


@pytest.mark.django_db
def test_explorer_nodes_include_page_urls(client, root_page):
    page = RelatedPagesTestPageFactory(parent=root_page, title="Related page")
    explorer = RelatedPagesExplorerPageFactory(
        parent=root_page,
        title="Related pages",
    )

    response = client.get(explorer.url)
    node = next(
        node for node in response.context["data"]["nodes"] if node["id"] == page.pk
    )

    assert node["url"] == page.get_url(response.wsgi_request)
