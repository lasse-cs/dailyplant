from django.db import models
from django.utils.html import strip_tags

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, MultipleChooserPanel
from wagtail.fields import RichTextField, RichTextMaxLengthValidator, StreamField
from wagtail.images import get_image_model
from wagtail.models import Page
from wagtail.rich_text import expand_db_html
from wagtail.search import index

from core.blocks import ContentStreamBlock
from core.models import (
    FeedPageMixin,
    MetadataMixin,
    RelatedPagesMixin,
    TableOfContentsPageMixin,
    TaggedPageMixin,
)
from core.panels import IncomingRelatedPagesPanel
from search.models import SearchablePageMixin


class ArticleIndexPage(MetadataMixin, Page):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["articles.ArticlePage"]
    max_count = 1
    template = "patterns/pages/articles/article_index.html"

    introduction = RichTextField(
        blank=True,
        help_text="Introductory content for the article index page.",
    )

    def get_articles(self):
        return ArticlePage.objects.live().child_of(self).order_by("-first_published_at")

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["articles"] = self.get_articles()
        return context

    content_panels = Page.content_panels + ["introduction"]


class ArticlePage(
    SearchablePageMixin,
    FeedPageMixin,
    MetadataMixin,
    RelatedPagesMixin,
    TaggedPageMixin,
    TableOfContentsPageMixin,
    Page,
):
    search_result_template = "patterns/components/search/results/article.html"

    parent_page_types = ["articles.ArticleIndexPage"]
    subpage_types = []
    template = "patterns/pages/articles/article.html"
    metadata_type = "article"

    introduction = RichTextField(
        validators=[RichTextMaxLengthValidator(500)],
        help_text="A short introduction used in article listings and social posts.",
    )
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="articles",
    )
    image_description = models.TextField(
        max_length=150,
        blank=True,
        help_text="The caption displayed underneath the image.",
    )
    image_alt = models.TextField(
        max_length=300,
        blank=True,
        help_text="Override the alt text for this image.",
    )
    body = StreamField(ContentStreamBlock())

    @property
    def image_alt_text(self):
        if not self.image:
            return None
        return self.image_alt or self.image.default_alt_text

    @property
    def metadata_description(self):
        return " ".join(strip_tags(expand_db_html(self.introduction)).split())

    @property
    def metadata_image(self):
        return self.image

    @property
    def metadata_image_alt(self):
        return self.image_alt_text

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["related_pages"] = self.get_related_pages()
        return context

    content_panels = Page.content_panels + [
        "introduction",
        MultiFieldPanel(
            [
                "image",
                FieldPanel("image_description", heading="Image Caption"),
                "image_alt",
            ],
            heading="Article Image",
        ),
        "body",
        MultipleChooserPanel(
            "tag_assignments",
            label="Tags",
            chooser_field_name="tag",
        ),
        MultipleChooserPanel(
            "outgoing_page_relationships",
            label="Related Pages",
            chooser_field_name="target",
        ),
        IncomingRelatedPagesPanel(),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]
