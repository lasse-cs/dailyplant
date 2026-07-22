from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils.cache import patch_vary_headers
from django.utils.html import strip_tags

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, MultipleChooserPanel
from wagtail.contrib.routable_page.models import RoutablePage, path
from wagtail.contrib.routable_page.templatetags.wagtailroutablepage_tags import (
    routablefullpageurl,
)
from wagtail.fields import RichTextField, RichTextMaxLengthValidator, StreamField
from wagtail.images import get_image_model
from wagtail.models import Page
from wagtail.rich_text import expand_db_html
from wagtail.search import index

from core.blocks import ContentStreamBlock
from core.breadcrumbs import Breadcrumb
from core.models import (
    FeedPageMixin,
    MarkdownPageMixin,
    MarkdownRoutablePageMixin,
    MetadataMixin,
    PageTag,
    RelatedPagesMixin,
    TableOfContentsPageMixin,
    Tag,
    TaggedPageMixin,
)
from core.panels import IncomingRelatedPagesPanel
from search.models import SearchablePageMixin


class ArticleIndexPage(MetadataMixin, MarkdownRoutablePageMixin, RoutablePage):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["articles.ArticlePage"]
    max_count = 1
    template = "patterns/pages/articles/article_index.html"
    markdown_template = "non_patterns/pages/articles/article_index.md"
    supports_md_suffix = False

    introduction = RichTextField(
        blank=True,
        help_text="Introductory content for the article index page.",
    )

    def serve(self, request, view=None, args=None, kwargs=None):
        response = super().serve(request, view=view, args=args, kwargs=kwargs)
        patch_vary_headers(response, ["HX-Request"])
        return response

    @path("tags/<slug:slug>/", name="tag")
    def tag(self, request, slug):
        get_object_or_404(self.get_tags(), slug=slug)
        return self.render(request, slug=slug)

    def get_template(self, request, *args, **kwargs):
        if "HX-Request" in request.headers:
            return "non_patterns/articles/partials/article_index.html"
        return super().get_template(request)

    def get_articles(self, slug=None):
        articles = (
            ArticlePage.objects.live()
            .child_of(self)
            .prefetch_related(
                Prefetch(
                    "tag_assignments",
                    queryset=PageTag.objects.select_related("tag"),
                )
            )
            .order_by("-first_published_at")
        )
        if slug:
            articles = articles.filter(tag_assignments__tag__slug=slug)
        return articles

    def get_tags(self):
        return Tag.objects.filter(
            page_assignments__page__in=self.get_articles()
        ).distinct()

    def get_index_url(self, request):
        resolver_match = getattr(request, "routable_resolver_match", None)
        if resolver_match and resolver_match.url_name == "tag":
            return routablefullpageurl(
                {"request": request},
                self,
                resolver_match.url_name,
                *resolver_match.args,
                **resolver_match.kwargs,
            )
        return super().get_metadata_url(request)

    def get_metadata_url(self, request):
        metadata_url = self.get_index_url(request)
        if "page" in request.GET:
            try:
                page_number = int(request.GET["page"])
                if page_number > 1:
                    parsed = urlparse(metadata_url)
                    params = parse_qs(parsed.query)
                    params["page"] = [str(page_number)]
                    metadata_url = urlunparse(
                        parsed._replace(query=urlencode(params, doseq=True))
                    )
            except ValueError:
                pass
        return metadata_url

    def get_extra_breadcrumb(self, request) -> Breadcrumb | None:
        # Wagtail does not set routable_resolver_match when serving previews.
        resolver_match = getattr(request, "routable_resolver_match", None)
        if not resolver_match or resolver_match.url_name != "tag":
            return None

        tag = self.get_tags().filter(slug=resolver_match.kwargs["slug"]).first()
        if not tag:
            return None
        return Breadcrumb(name=tag.name, url=self.get_metadata_url(request))

    def get_context(self, request, slug=None):
        context = super().get_context(request)
        page_number = request.GET.get("page", 1)
        paginator = Paginator(self.get_articles(slug), 18, orphans=2)
        try:
            articles = paginator.page(page_number)
        except PageNotAnInteger, EmptyPage:
            articles = Paginator([], 1, allow_empty_first_page=True).page(1)
        context["articles"] = articles
        context["tags"] = self.get_tags()
        context["active_slug"] = slug
        context["index_url"] = self.get_index_url(request)
        context["metadata_url"] = self.get_metadata_url(request)
        return context

    content_panels = Page.content_panels + ["introduction"]


class ArticlePage(
    SearchablePageMixin,
    FeedPageMixin,
    MetadataMixin,
    RelatedPagesMixin,
    TaggedPageMixin,
    TableOfContentsPageMixin,
    MarkdownPageMixin,
    Page,
):
    search_result_template = "patterns/components/search/results/article.html"

    parent_page_types = ["articles.ArticleIndexPage"]
    subpage_types = []
    template = "patterns/pages/articles/article.html"
    markdown_template = "non_patterns/pages/articles/article.md"
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

    def get_schema_graph(self, request, metadata):
        article = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": metadata["title"],
            "description": metadata["description"],
            "url": metadata["url"],
        }

        if self.first_published_at:
            article["datePublished"] = self.first_published_at
        if self.last_published_at:
            article["dateModified"] = self.last_published_at

        if metadata["site"].site_name:
            article["author"] = {
                "@type": "Organization",
                "name": metadata["site"].site_name,
            }

        keywords = [tag.name for tag in self.get_tags()]
        if keywords:
            article["keywords"] = keywords

        return [article]

    def get_reading_time(self, request):
        introduction = expand_db_html(self.introduction)
        body = self.body.render_as_block(context={"request": request})
        word_count = len(strip_tags(f"{introduction} {body}").split())

        # Match Wagtail's English reading speed and JavaScript rounding.
        return max(1, int(word_count / 238 + 0.5))

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["reading_time"] = self.get_reading_time(request)
        context["share"] = self.get_full_url(request)
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
