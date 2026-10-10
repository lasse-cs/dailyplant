import pytest
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from pytest_django.asserts import assertTemplateUsed
from wagtail_factories import ImageFactory

from images.factories import ImagePageFactory, ImagesListingPageFactory
from images.models import ImagesListingPage

pytestmark = pytest.mark.django_db


def test_image_page_renders_html_markdown_and_explorer_details(client, root_page):
    listing = ImagesListingPageFactory(parent=root_page)
    page = ImagePageFactory(
        parent=listing,
        description="<p>A <strong>leaf</strong> in detail.</p>",
        image_alt="Veins running through a leaf",
        image_description="A leaf photographed in summer.",
        references=[
            (
                "reference",
                {"label": "<p>Leaf anatomy</p>", "url": "https://example.com/leaves"},
            )
        ],
        tags=["Leaves"],
    )
    html = client.get(page.url)
    assert html.status_code == 200
    assert page.image_alt in html.text
    assert "Leaves" in html.text
    assert "A <strong>leaf</strong> in detail." in html.text
    assert page.metadata_description == "A leaf in detail."
    assert page.metadata_image == page.image
    assert 'class="content-media__caption"' in html.text
    assert page.image_description in html.text
    assert 'href="https://example.com/leaves"' in html.text

    markdown = client.get(page.url.rstrip("/") + ".md")
    assert markdown.status_code == 200
    assert "A **leaf** in detail." in markdown.text
    assert f"![{page.image_alt}]" in markdown.text
    assert page.image_description in markdown.text
    assert "[Leaf anatomy](https://example.com/leaves)" in markdown.text

    details = client.get(
        page.url,
        headers={"HX-Request": "true", "HX-Target": "explorer-details-content"},
    )
    assertTemplateUsed(details, "non_patterns/images/related_page_details.html")
    assert "View image" in details.text
    assert "HX-Target" in details.headers["Vary"]
    assert page.image_description in details.text


def test_revision_cannot_select_an_image_claimed_by_another_page(root_page):
    listing = ImagesListingPageFactory(parent=root_page)
    page = ImagePageFactory(parent=listing)
    available_image = ImageFactory()
    page.image = available_image
    revision = page.save_revision()
    ImagePageFactory(parent=listing, image=available_image)
    with pytest.raises(ValidationError) as error:
        revision.as_object().full_clean()
    assert "image" in error.value.message_dict


def test_listing_limits_to_live_children_and_paginates(client, root_page, monkeypatch):
    listing = ImagesListingPageFactory(parent=root_page)
    pages = [ImagePageFactory(parent=listing) for _ in range(3)]
    draft = ImagePageFactory(parent=listing, live=False)
    outside = ImagePageFactory(parent=root_page)
    monkeypatch.setattr(
        ImagesListingPage, "get_paginator", lambda self: Paginator(self.get_images(), 2)
    )
    response = client.get(listing.url)
    assert response.status_code == 200
    assert list(response.context["images"]) == [pages[2], pages[1]]
    assert draft.title not in response.text
    assert outside.title not in response.text
    assert "Older images" in response.text
    second = client.get(listing.url, {"page": 2})
    assert list(second.context["images"]) == [pages[0]]
    assert f"{listing.full_url}?page=2" in second.text
    markdown = client.get(listing.url.rstrip("/") + ".md", {"page": 2})
    assert markdown.status_code == 200
    assert pages[0].title in markdown.text
    assert set(listing.get_llms_txt_pages()) == set(pages)
    assert list(listing.get_sitemap_pages()) == [pages[2], pages[1]]


@pytest.mark.parametrize("number", ["bad", "0", "-1", "999"])
def test_listing_rejects_invalid_page_numbers(client, root_page, number):
    listing = ImagesListingPageFactory(parent=root_page)
    assert client.get(listing.url, {"page": number}).status_code == 404


def test_empty_listing(client, root_page):
    listing = ImagesListingPageFactory(parent=root_page)
    response = client.get(listing.url)
    assert response.status_code == 200
    assert "No images found." in response.text
