import pytest
from django.core.exceptions import ImproperlyConfigured
from pytest_django.asserts import assertTemplateUsed

from core.factories import RelatedPagesExplorerPageFactory
from core.models import PageRelationship
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
    node = response.context["data"]["nodes"][page.pk]

    assert node["url"] == page.get_url(response.wsgi_request)


@pytest.mark.django_db
def test_explorer_nodes_include_neighbours(client, root_page):
    source = RelatedPagesTestPageFactory(parent=root_page, title="Source")
    target = RelatedPagesTestPageFactory(parent=root_page, title="Target")
    PageRelationship.objects.create(source=source, target=target)
    explorer = RelatedPagesExplorerPageFactory(
        parent=root_page,
        title="Related pages",
    )

    response = client.get(explorer.url)
    nodes = response.context["data"]["nodes"]

    assert nodes[source.pk]["edges"] == [target.pk]
    assert nodes[target.pk]["edges"] == [source.pk]


@pytest.mark.django_db
def test_explorer_uses_markdown_template(client, root_page):
    explorer = RelatedPagesExplorerPageFactory(parent=root_page)

    response = client.get(explorer.url.rstrip("/") + ".md")

    assertTemplateUsed(response, "non_patterns/pages/core/related_pages_explorer.md")


@pytest.mark.django_db
def test_explorer_shows_empty_state_without_pages(client, root_page):
    explorer = RelatedPagesExplorerPageFactory(
        parent=root_page,
        title="Related pages",
    )

    response = client.get(explorer.url)

    assert "There are no pages to explore yet." in response.text
    assert 'data-controller="explorer-chart"' not in response.text
