from datetime import UTC, datetime, timedelta

import pytest
from pytest_django.asserts import assertTemplateUsed

from articles.models import ArticleIndexPage, ArticlePage
from core.models import PageTag, Tag
from home.factories import HomePageFactory


def make_index(root_page, title="Articles", introduction=""):
    home_page = HomePageFactory(parent=root_page)
    return home_page.add_child(
        instance=ArticleIndexPage(title=title, introduction=introduction)
    )


def make_article(index, title, *, first_published_at=None, body=None):
    return index.add_child(
        instance=ArticlePage(
            title=title,
            introduction=f"<p>{title}</p>",
            first_published_at=first_published_at,
            body=body or [],
        )
    )


@pytest.mark.django_db
def test_article_index_prefetches_tag_assignments(root_page):
    article_index = make_index(root_page)

    prefetch = article_index.get_articles()._prefetch_related_lookups[0]
    assert prefetch.prefetch_to == "tag_assignments"


@pytest.mark.django_db
def test_article_index_only_exposes_tags_used_by_live_articles(root_page):
    article_index = make_index(root_page)
    article = make_article(article_index, "Growing herbs")
    used = Tag.objects.create(name="Herbs")
    PageTag.objects.create(page=article, tag=used)
    Tag.objects.create(name="Unused")

    tags = list(article_index.get_tags())

    assert [t.name for t in tags] == ["Herbs"]


@pytest.mark.django_db
def test_article_index_tag_route_filters_articles(client, root_page):
    article_index = make_index(root_page)
    herbs = make_article(article_index, "Growing herbs")
    make_article(article_index, "Choosing pots")
    tag = Tag.objects.create(name="Herbs")
    PageTag.objects.create(page=herbs, tag=tag)

    tag_url = f"{article_index.url}tags/{tag.slug}/"
    response = client.get(tag_url)

    assert response.status_code == 200
    assert "Growing herbs" in response.text
    assert "Choosing pots" not in response.text
    assertTemplateUsed(response, "patterns/pages/articles/article_index.html")


@pytest.mark.django_db
def test_article_index_tag_route_returns_404_for_unknown_tag(client, root_page):
    article_index = make_index(root_page)

    response = client.get(f"{article_index.url}tags/unknown/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_article_index_paginates_eighteen_per_page(client, root_page):
    article_index = make_index(root_page)
    base = datetime(2026, 1, 1, 10, tzinfo=UTC)
    for i in range(22):
        make_article(
            article_index,
            f"Article {i:02d}",
            first_published_at=base + timedelta(days=i),
        )

    first = client.get(article_index.url)
    second = client.get(f"{article_index.url}?page=2")

    assert "Article 21" in first.text
    assert "Article 04" in first.text
    assert "Article 03" not in first.text
    assert "Older Articles" in first.text
    assert "Newer Articles" not in first.text

    assert "Article 00" in second.text
    assert "Article 03" in second.text
    assert "Article 04" not in second.text
    assert "Article 21" not in second.text
    assert "Newer Articles" in second.text


@pytest.mark.django_db
def test_article_index_metadata_url_includes_tag_route_and_page(client, root_page):
    article_index = make_index(root_page)
    article = make_article(article_index, "Growing herbs")
    tag = Tag.objects.create(name="Herbs")
    PageTag.objects.create(page=article, tag=tag)

    tag_url = f"{article_index.url}tags/{tag.slug}/"
    response = client.get(f"{tag_url}?page=2")
    metadata_url = article_index.get_metadata_url(response.wsgi_request)

    assert f"tags/{tag.slug}/" in metadata_url
    assert "page=2" in metadata_url


@pytest.mark.django_db
def test_article_index_htmx_returns_partial(client, root_page):
    article_index = make_index(root_page)
    make_article(article_index, "Growing herbs")

    response = client.get(article_index.url, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assertTemplateUsed(response, "non_patterns/articles/partials/article_index.html")
    assertTemplateUsed(response, "patterns/components/articles/article_navigation.html")
    assert "<html" not in response.text


@pytest.mark.django_db
def test_article_index_markdown_renders_filter_and_pagination(client, root_page):
    article_index = make_index(root_page, introduction="<p>Practical guides.</p>")
    base = datetime(2026, 1, 1, 10, tzinfo=UTC)
    for i in range(20):
        make_article(
            article_index,
            f"Article {i:02d}",
            first_published_at=base + timedelta(days=i),
        )
    article = make_article(
        article_index, "Growing herbs", first_published_at=base + timedelta(days=30)
    )
    tag = Tag.objects.create(name="Herbs")
    PageTag.objects.create(page=article, tag=tag)

    index_response = client.get(article_index.url, headers={"accept": "text/markdown"})
    tag_response = client.get(
        f"{article_index.url}tags/{tag.slug}/", headers={"accept": "text/markdown"}
    )

    assert index_response.headers["Content-Type"].startswith("text/markdown")
    assert "Practical guides." in index_response.text
    assert "Page 1" in index_response.text
    assert "Next Page" in index_response.text

    assert "Filtered on Tag herbs" in tag_response.text
    assert "Growing herbs" in tag_response.text
    assert f"tags/{tag.slug}/" in tag_response.text


@pytest.mark.django_db
def test_article_index_tag_route_adds_breadcrumb(client, root_page):
    article_index = make_index(root_page)
    article = make_article(article_index, "Growing herbs")
    tag = Tag.objects.create(name="Herbs")
    PageTag.objects.create(page=article, tag=tag)

    response = client.get(f"{article_index.url}tags/{tag.slug}/")

    assert '<span aria-current="page">Herbs</span>' in response.text
