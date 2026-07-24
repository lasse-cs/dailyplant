import pytest

from articles.models import ArticleIndexPage, ArticlePage
from core.blocks import LLMsTxtListingPageChooserBlock
from core.models import ContentPage, LLMsTxtSettings, MetadataSettings
from facts.models import FactIndexPage
from home.factories import HomePageFactory


def make_content_page(parent, title):
    return parent.add_child(instance=ContentPage(title=title, body="Content"))


@pytest.mark.django_db
def test_llms_txt_renders_site_metadata_and_curated_markdown_links(client, site):
    home_page = HomePageFactory(parent=site.root_page)
    guide = make_content_page(home_page, "Growing guide")
    MetadataSettings.objects.create(site=site, description="Practical plant advice.")
    llms_settings = LLMsTxtSettings.for_site(site)
    llms_settings.sections = [
        ("curated", {"title": "Guides", "pages": [guide]}),
    ]
    llms_settings.save()

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
    home_page = HomePageFactory(parent=site.root_page)
    article_index = home_page.add_child(instance=ArticleIndexPage(title="Articles"))
    article = article_index.add_child(
        instance=ArticlePage(
            title="Choosing a pot",
            introduction="<p>Start with drainage.</p>",
            body=[],
        )
    )
    llms_settings = LLMsTxtSettings.for_site(site)
    llms_settings.sections = [
        ("automatic", {"listing_page": article_index}),
    ]
    llms_settings.save()

    response = client.get("/llms.txt")

    assert "## Articles" in response.text
    assert (
        f"- [Choosing a pot]({article.get_full_url(response.wsgi_request).rstrip('/')}.md)"
        in response.text
    )


@pytest.mark.django_db
def test_llms_txt_omits_unpublished_curated_pages(client, site):
    home_page = HomePageFactory(parent=site.root_page)
    hidden_page = make_content_page(home_page, "Hidden guide")
    hidden_page.unpublish()
    llms_settings = LLMsTxtSettings.for_site(site)
    llms_settings.sections = [
        ("curated", {"title": "Guides", "pages": [hidden_page]}),
    ]
    llms_settings.save()

    response = client.get("/llms.txt")

    assert "## Guides" in response.text
    assert "Hidden guide" not in response.text


@pytest.mark.django_db
def test_llms_txt_setting_preview_renders_markdown(site):
    home_page = HomePageFactory(parent=site.root_page)
    guide = make_content_page(home_page, "Preview guide")
    llms_settings = LLMsTxtSettings.for_site(site)
    llms_settings.sections = [
        ("curated", {"title": "Preview", "pages": [guide]}),
    ]

    response = llms_settings.make_preview_request()

    assert response.headers["Content-Type"].startswith("text/markdown")
    assert "## Preview" in response.text
    assert "Preview guide" in response.text


def test_llms_txt_listing_chooser_only_targets_implementing_page_types():
    target_models = LLMsTxtListingPageChooserBlock().target_models

    assert set(target_models) == {ArticleIndexPage, FactIndexPage}
