import pytest

from articles.models import ArticleIndexPage, ArticlePage
from home.factories import HomePageFactory
from social.models import BlueskyPost, BlueskyPostStatus


@pytest.mark.django_db
def test_publishing_article_queues_one_bluesky_post(root_page):
    home_page = HomePageFactory(parent=root_page)
    article_index = home_page.add_child(
        instance=ArticleIndexPage(title="Articles", introduction="")
    )
    article = article_index.add_child(
        instance=ArticlePage(
            title="Growing herbs",
            introduction="A short introduction.",
            body=[],
            live=False,
        )
    )

    article.save_revision().publish()

    post = BlueskyPost.objects.get(page=article)
    assert post.status == BlueskyPostStatus.PENDING

    article.save_revision().publish()

    assert BlueskyPost.objects.filter(page=article).count() == 1
