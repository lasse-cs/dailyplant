from datetime import UTC, date, datetime, timedelta
from xml.etree import ElementTree

import pytest

from articles.factories import ArticleIndexPageFactory, ArticlePageFactory
from facts.factories import FactIndexPageFactory, FactPageFactory
from home.factories import HomePageFactory

EARLIER = datetime(2026, 1, 1, tzinfo=UTC)
LATER = datetime(2026, 1, 2, tzinfo=UTC)
LATEST = datetime(2026, 1, 3, tzinfo=UTC)

pytestmark = pytest.mark.django_db


def sitemap_lastmods(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return {
        entry.findtext("s:loc", namespaces=namespace): entry.findtext(
            "s:lastmod", namespaces=namespace
        )
        for entry in ElementTree.fromstring(response.content)
    }


def test_listing_sitemap_uses_first_page_with_orphans(root_page, client):
    home = HomePageFactory(parent=root_page, last_published_at=EARLIER)
    articles = ArticleIndexPageFactory(
        parent=home, slug="articles", last_published_at=EARLIER
    )
    facts = FactIndexPageFactory(parent=home, slug="facts", last_published_at=EARLIER)
    for position in range(20):
        published = EARLIER - timedelta(days=position)
        # Item 20 is an orphan included on page one until item 21 is added.
        lastmod = LATEST if position == 19 else LATER
        ArticlePageFactory(
            parent=articles, first_published_at=published, last_published_at=lastmod
        )
        FactPageFactory(parent=facts, date=published.date(), last_published_at=lastmod)

    entries = sitemap_lastmods(client)
    assert entries[articles.full_url] == "2026-01-03"
    assert entries[facts.full_url] == "2026-01-03"

    ArticlePageFactory(
        parent=articles,
        first_published_at=EARLIER - timedelta(days=20),
        last_published_at=LATEST,
    )
    FactPageFactory(
        parent=facts,
        date=date(2025, 12, 12),
        last_published_at=LATEST,
    )
    ArticlePageFactory(parent=articles, live=False, last_published_at=LATEST)
    FactPageFactory(parent=facts, live=False, last_published_at=LATEST)

    # More recently updated items on page two must not date the base listing.
    entries = sitemap_lastmods(client)
    assert entries[articles.full_url] == "2026-01-02"
    assert entries[facts.full_url] == "2026-01-02"


def test_home_sitemap_uses_displayed_fact(root_page, client):
    home = HomePageFactory(parent=root_page, last_published_at=EARLIER)
    index = FactIndexPageFactory(parent=home)
    FactPageFactory(parent=index, date=date(2026, 1, 1), last_published_at=LATEST)
    displayed = FactPageFactory(
        parent=index, date=date(2026, 1, 2), last_published_at=LATER
    )
    FactPageFactory(
        parent=index, date=date(2026, 1, 3), live=False, last_published_at=LATEST
    )
    articles = ArticleIndexPageFactory(parent=home, slug="articles")
    ArticlePageFactory(parent=articles, last_published_at=LATEST)

    displayed.title = "Draft title"
    displayed.save_revision()
    assert sitemap_lastmods(client)[home.full_url] == "2026-01-02"

    home.last_published_at = LATEST
    home.save(update_fields=["last_published_at"])
    assert sitemap_lastmods(client)[home.full_url] == "2026-01-03"
