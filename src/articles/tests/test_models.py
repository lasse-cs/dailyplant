import pytest

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
