import json
from datetime import UTC, datetime

import pytest
from pytest_django.asserts import assertTemplateUsed

from articles.models import ArticleIndexPage, ArticlePage
from core.models import PageRelationship, PageTag, Tag
from home.factories import HomePageFactory


def test_article_introduction_is_used_for_metadata_description():
    article = ArticlePage(
        title="Growing herbs",
        introduction="<p>A <strong>short</strong> introduction.</p>",
        body=[],
    )

    assert article.metadata_description == "A short introduction."
    assert (
        article.search_result_template
        == "patterns/components/search/results/article.html"
    )


def test_article_reading_time_uses_rendered_introduction_and_body(rf):
    article = ArticlePage(
        title="Growing herbs",
        introduction="<p>Short introduction.</p>",
        body=[
            ("heading", {"text": "Choose a pot", "level": "2"}),
            ("paragraph", f"<p>{'plant ' * 352}</p>"),
        ],
    )

    assert article.get_reading_time(rf.get("/")) == 2


@pytest.mark.django_db
def test_article_supports_tags_and_related_pages(root_page):
    home_page = HomePageFactory(parent=root_page)
    article_index = home_page.add_child(
        instance=ArticleIndexPage(title="Articles", introduction="")
    )
    article = article_index.add_child(
        instance=ArticlePage(title="Growing herbs", introduction="Herbs", body=[])
    )
    related = article_index.add_child(
        instance=ArticlePage(title="Choosing pots", introduction="Pots", body=[])
    )
    tag = Tag.objects.create(name="Herbs")
    PageTag.objects.create(page=article, tag=tag)
    PageRelationship.objects.create(source=article, target=related)

    assert article.get_tags() == [tag]
    assert list(article.get_related_pages()) == [related]


@pytest.mark.django_db
def test_article_pages_render_markdown(client, root_page):
    published_at = datetime(2026, 1, 2, 10, tzinfo=UTC)
    modified_at = datetime(2026, 1, 3, 11, tzinfo=UTC)
    home_page = HomePageFactory(parent=root_page)
    article_index = home_page.add_child(
        instance=ArticleIndexPage(
            title="Articles", introduction="<p>Practical growing guides.</p>"
        )
    )
    article = article_index.add_child(
        instance=ArticlePage(
            title="Growing herbs",
            introduction="<p>A <strong>short</strong> introduction.</p>",
            first_published_at=published_at,
            last_published_at=modified_at,
            body=[
                ("heading", {"text": "Choose a pot", "level": "2"}),
                ("paragraph", "<p>Give the roots enough room.</p>"),
            ],
        )
    )
    tag = Tag.objects.create(name="Herbs")
    PageTag.objects.create(page=article, tag=tag)

    index_response = client.get(article_index.url, headers={"accept": "text/markdown"})
    article_response = client.get(article.url.rstrip("/") + ".md")

    assert index_response.status_code == 200
    assert index_response.headers["Content-Type"].startswith("text/markdown")
    assertTemplateUsed(index_response, "non_patterns/pages/articles/article_index.md")
    assert "Practical growing guides." in index_response.text
    assert f"[Growing herbs]({article.full_url.rstrip('/')}.md)" in index_response.text

    assert article_response.status_code == 200
    assert article_response.headers["Content-Type"].startswith("text/markdown")
    assertTemplateUsed(article_response, "non_patterns/pages/articles/article.md")
    assert "A **short** introduction." in article_response.text
    assert "## Choose a pot" in article_response.text
    assert "Give the roots enough room." in article_response.text

    json_ld = article_response.text.split("```json\n", 1)[1].split("\n```", 1)[0]
    article_schema = json.loads(json_ld)[1]
    assert article_schema == {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Growing herbs",
        "description": "A short introduction.",
        "url": article.full_url,
        "datePublished": "2026-01-02T10:00:00Z",
        "dateModified": "2026-01-03T11:00:00Z",
        "author": {"@type": "Organization", "name": article.get_site().site_name},
        "keywords": ["Herbs"],
    }

    html_response = client.get(article.url)
    assert "1 min read" in html_response.text
