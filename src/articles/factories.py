import factory
from wagtail_factories import PageFactory, StreamFieldFactory

from articles.models import ArticleIndexPage, ArticlePage
from core.factories import (
    ContentStreamBlockFactory,
    RelatedPagesFactoryMixin,
    TaggedPageFactoryMixin,
)


class ArticleIndexPageFactory(PageFactory):
    class Meta:
        model = ArticleIndexPage


class ArticlePageFactory(RelatedPagesFactoryMixin, TaggedPageFactoryMixin):
    title = factory.Sequence(lambda index: f"Article {index}")
    introduction = factory.LazyAttribute(lambda article: f"<p>{article.title}</p>")
    body = StreamFieldFactory(ContentStreamBlockFactory)

    class Meta:
        model = ArticlePage
        skip_postgeneration_save = True
