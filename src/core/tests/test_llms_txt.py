from datetime import timedelta

import pytest
from django.utils import timezone

from core.factories import ContentPageFactory
from core.models import LLMsTxtSettings, MetadataSettings
from core.testapp.factories import LLMsTxtListingPageFactory


def make_llms_txt_settings(site, sections, information=""):
    llms_settings = LLMsTxtSettings.for_site(site)
    llms_settings.sections = sections
    llms_settings.information = information
    llms_settings.save()
    return llms_settings


@pytest.mark.django_db
def test_llms_txt_renders_site_metadata_and_curated_markdown_links(client, site):
    guide = ContentPageFactory(parent=site.root_page, title="Growing guide")
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
    listing = LLMsTxtListingPageFactory(parent=site.root_page, title="Listing")
    page = ContentPageFactory(parent=listing, title="Choosing a pot")
    make_llms_txt_settings(site, [("automatic", {"listing_page": listing})])

    response = client.get("/llms.txt")

    assert "## Listing" in response.text
    assert (
        f"- [Choosing a pot]({page.get_full_url(response.wsgi_request).rstrip('/')}.md)"
        in response.text
    )


@pytest.mark.django_db
def test_llms_txt_automatic_section_limits_links(client, site):
    listing = LLMsTxtListingPageFactory(parent=site.root_page)
    for i in range(7):
        ContentPageFactory(
            parent=listing,
            title=f"Page {i}",
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
    hidden_page = ContentPageFactory(parent=site.root_page, title="Hidden guide")
    hidden_page.unpublish()
    make_llms_txt_settings(
        site, [("curated", {"title": "Guides", "pages": [hidden_page]})]
    )

    response = client.get("/llms.txt")

    assert "## Guides" in response.text
    assert "Hidden guide" not in response.text


@pytest.mark.django_db
def test_llms_txt_setting_preview_renders_markdown(site):
    guide = ContentPageFactory(parent=site.root_page, title="Preview guide")
    llms_settings = LLMsTxtSettings.for_site(site)
    llms_settings.sections = [("curated", {"title": "Preview", "pages": [guide]})]

    response = llms_settings.make_preview_request()

    assert response.headers["Content-Type"].startswith("text/markdown")
    assert "## Preview" in response.text
    assert "Preview guide" in response.text


@pytest.mark.django_db
def test_llms_txt_includes_search_description(client, site):
    guide = ContentPageFactory(
        parent=site.root_page,
        title="Guide",
        search_description="First line\n\nSecond\tline",
    )
    make_llms_txt_settings(site, [("curated", {"title": "Preview", "pages": [guide]})])

    response = client.get("/llms.txt")
    assert "): First line Second line" in response.text


@pytest.mark.django_db
def test_llms_txt_includes_information(client, site):
    make_llms_txt_settings(site, [], "SomeInformation")

    response = client.get("/llms.txt")
    assert "SomeInformation" in response.text
