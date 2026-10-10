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
    assert "<figcaption" not in html.text
    assert 'href="https://example.com/leaves"' in html.text

    markdown = client.get(page.url.rstrip("/") + ".md")
    assert markdown.status_code == 200
    assert "A **leaf** in detail." in markdown.text
    assert f"![{page.image_alt}]" in markdown.text
    assert "[Leaf anatomy](https://example.com/leaves)" in markdown.text

    details = client.get(
        page.url,
        headers={"HX-Request": "true", "HX-Target": "explorer-details-content"},
    )
    assertTemplateUsed(details, "non_patterns/images/related_page_details.html")
    assert "View image" in details.text
    assert "HX-Target" in details.headers["Vary"]
    assert "<figcaption" not in details.text


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
        ImagesListingPage,
        "get_paginator",
        lambda self, slug=None: Paginator(self.get_images(slug), 2),
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
    markdown = client.get(listing.url, {"page": 2}, headers={"Accept": "text/markdown"})
    assert markdown.status_code == 200
    assert pages[0].title in markdown.text
    assert f"url: {listing.full_url}?page=2" in markdown.text
    assert "Content-Location" not in markdown.headers
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


def test_image_tags_link_to_filtered_listing(client, root_page, monkeypatch):
    listing = ImagesListingPageFactory(parent=root_page)
    leaves = [ImagePageFactory(parent=listing, tags=["Leaves"]) for _ in range(3)]
    ImagePageFactory(parent=listing, tags=["Flowers"])
    ImagePageFactory(parent=listing, tags=["Draft only"], live=False)
    monkeypatch.setattr(
        ImagesListingPage,
        "get_paginator",
        lambda self, slug=None: Paginator(self.get_images(slug), 2),
    )
    tag_url = listing.url + "tags/leaves/"
    detail = client.get(leaves[0].url)
    assert 'class="tag-list"' in detail.text
    assert f'href="{tag_url}"' in detail.text

    response = client.get(tag_url)
    assert response.status_code == 200
    assert list(response.context["images"]) == [leaves[2], leaves[1]]
    assert 'aria-current="page"' in response.text
    second = client.get(tag_url, {"page": 2})
    assert list(second.context["images"]) == [leaves[0]]
    assert f"{listing.full_url}tags/leaves/?page=2" in second.text
    markdown = client.get(tag_url, headers={"Accept": "text/markdown"})
    assert markdown.status_code == 200
    assert "text/markdown" in markdown.headers["Content-Type"]
    assert f"url: {listing.full_url}tags/leaves/\n" in markdown.text
    assert "Filtered on Tag leaves" in markdown.text
    assert f"[Older images]({listing.full_url}tags/leaves/?page=2)" in markdown.text
    assert "Content-Location" not in markdown.headers
    second_markdown = client.get(
        tag_url, {"page": 2}, headers={"Accept": "text/markdown"}
    )
    assert second_markdown.status_code == 200
    assert f"url: {listing.full_url}tags/leaves/?page=2" in second_markdown.text
    assert (
        f"[Newer images]({listing.full_url}tags/leaves/?page=1)" in second_markdown.text
    )
    assert "Content-Location" not in second_markdown.headers
    assert client.get(listing.url + "tags/missing/").status_code == 404
    assert client.get(listing.url + "tags/draft-only/").status_code == 404
