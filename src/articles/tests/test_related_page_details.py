import pytest
from pytest_django.asserts import assertTemplateUsed

from articles.factories import ArticlePageFactory


@pytest.mark.django_db
def test_article_page_returns_details_for_explorer_htmx_target(client, root_page):
    article = ArticlePageFactory(
        parent=root_page,
        title="Growing herbs",
        introduction="<p>A practical introduction.</p>",
        body=[],
    )

    response = client.get(
        article.url,
        headers={
            "HX-Request": "true",
            "HX-Target": "explorer-details-content",
        },
    )

    assert response.status_code == 200
    assertTemplateUsed(
        response, "non_patterns/articles/partials/related_page_details.html"
    )
