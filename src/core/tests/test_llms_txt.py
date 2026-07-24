from datetime import timedelta

import pytest

from django.utils import timezone

from core.blocks import LLMsTxtListingPageChooserBlock
from core.models import ContentPage, LLMsTxtSettings, MetadataSettings
from core.testapp.models import LLMsTxtListingPage


def make_content_page(parent, title, **kwargs):
    return parent.add_child(instance=ContentPage(title=title, body="Content", **kwargs))


def make_listing_page(parent, title="Listing"):
    return parent.add_child(instance=LLMsTxtListingPage(title=title))


def make_llms_txt_settings(site, sections):
    llms_settings = LLMsTxtSettings.for_site(site)
    llms_settings.sections = sections
    llms_settings.save()
    return llms_settings


@pytest.mark.django_db
def test_llms_txt_renders_site_metadata_and_curated_markdown_links(client, site):
    guide = make_content_page(site.root_page, "Growing guide")
    MetadataSettings.objects.create(site=site, description="Practical plant advice.")
    make_llms_txt_settings(site, [("curated", {"title": "Guides", "pages": [guide]})])

    response = client.get("/llms.txt")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/markdown")
    assert f"# {site.site_name}" in response.text
    assert "> Practical plant advice." in response.text
    assert "## Guides" in response.text
    assert (
        f"- [Growing guide]({guide.get_full_url(response.wsgi_request).rstrip('/')}.md)"
        in response.text
    )


@pytest.mark.django_db
def test_llms_txt_automatic_section_uses_listing_page_entries(client, site):
    listing = make_listing_page(site.root_page)
    page = make_content_page(listing, "Choosing a pot")
    make_llms_txt_settings(site, [("automatic", {"listing_page": listing})])

    response = client.get("/llms.txt")

    assert "## Listing" in response.text
    assert (
        f"- [Choosing a pot]({page.get_full_url(response.wsgi_request).rstrip('/')}.md)"
        in response.text
    )


@pytest.mark.django_db
def test_llms_txt_automatic_section_limits_links(client, site):
    listing = make_listing_page(site.root_page)
    for i in range(7):
        make_content_page(
            listing,
            f"Page {i}",
            first_published_at=timezone.now() - timedelta(days=i),
        )
    make_llms_txt_settings(site, [("automatic", {"listing_page": listing})])

    response = client.get("/llms.txt")

    for i in range(5):
        assert f"Page {i}]" in response.text
    assert "Page 5]" not in response.text
    assert "Page 6]" not in response.text


@pytest.mark.django_db
def test_llms_txt_omits_unpublished_curated_pages(client, site):
    hidden_page = make_content_page(site.root_page, "Hidden guide")
    hidden_page.unpublish()
    make_llms_txt_settings(
        site, [("curated", {"title": "Guides", "pages": [hidden_page]})]
    )

    response = client.get("/llms.txt")

    assert "## Guides" in response.text
    assert "Hidden guide" not in response.text


@pytest.mark.django_db
def test_llms_txt_setting_preview_renders_markdown(site):
    guide = make_content_page(site.root_page, "Preview guide")
    llms_settings = LLMsTxtSettings.for_site(site)
    llms_settings.sections = [("curated", {"title": "Preview", "pages": [guide]})]

    response = llms_settings.make_preview_request()

    assert response.headers["Content-Type"].startswith("text/markdown")
    assert "## Preview" in response.text
    assert "Preview guide" in response.text


def test_llms_txt_listing_chooser_only_targets_implementing_page_types():
    target_models = LLMsTxtListingPageChooserBlock().target_models

    assert LLMsTxtListingPage in target_models
    assert ContentPage not in target_models
