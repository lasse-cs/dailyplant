from datetime import datetime, time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.cache import patch_vary_headers
from django.utils.html import strip_tags
from django.utils.text import Truncator

from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    MultipleChooserPanel,
)
from wagtail.contrib.routable_page.models import RoutablePage, path
from wagtail.contrib.routable_page.templatetags.wagtailroutablepage_tags import (
    routablefullpageurl,
)
from wagtail.fields import RichTextField, RichTextMaxLengthValidator, StreamField
from wagtail.models import Page
from wagtail.images import get_image_model
from wagtail.rich_text import expand_db_html
from wagtail.search import index

from wagtail_umami_analytics.panels import UmamiAnalyticsPanel

from core.breadcrumbs import Breadcrumb
from core.models import (
    FeedPageMixin,
    MarkdownPageMixin,
    MarkdownRoutablePageMixin,
    MetadataMixin,
    PageTag,
    RelatedPagesMixin,
    Tag,
    TaggedPageMixin,
)
from core.panels import IncomingRelatedPagesPanel

from facts.blocks import ReferenceStreamBlock
from search.models import SearchablePageMixin


class FactIndexPage(MetadataMixin, MarkdownRoutablePageMixin, RoutablePage):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["facts.FactPage"]
    max_count = 1
    template = "patterns/pages/facts/fact_index.html"
    markdown_template = "non_patterns/pages/facts/fact_index.md"
    supports_md_suffix = False

    introduction = RichTextField(
        blank=True, help_text="Introductory content for the fact index page."
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
            return "non_patterns/facts/partials/fact_index.html"
        return super().get_template(request)

    def get_facts(self, slug=None):
        facts = (
            FactPage.objects.live()
            .child_of(self)
            .prefetch_related(
                Prefetch(
                    "tag_assignments",
                    queryset=PageTag.objects.select_related("tag"),
                )
            )
            .order_by("-date")
            .annotate(heading_level=models.Value("h2"))
        )
        if slug:
            facts = facts.filter(tag_assignments__tag__slug=slug)
        return facts

    def get_tags(self):
        return Tag.objects.filter(
            page_assignments__page__in=self.get_facts()
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
        paginator = Paginator(self.get_facts(slug), 18, orphans=2)
        try:
            facts = paginator.page(page_number)
        except PageNotAnInteger, EmptyPage:
            facts = Paginator([], 1, allow_empty_first_page=True).page(1)
        context["facts"] = facts
        context["tags"] = self.get_tags()
        context["active_slug"] = slug
        context["index_url"] = self.get_index_url(request)
        context["metadata_url"] = self.get_metadata_url(request)
        return context

    content_panels = Page.content_panels + [
        "introduction",
    ]


class FactPage(
    SearchablePageMixin,
    FeedPageMixin,
    MetadataMixin,
    RelatedPagesMixin,
    TaggedPageMixin,
    MarkdownPageMixin,
    Page,
):
    search_result_template = "patterns/components/search/results/fact.html"

    parent_page_types = ["facts.FactIndexPage"]
    subpage_types = []
    template = "patterns/pages/facts/fact.html"
    markdown_template = "non_patterns/pages/facts/fact.md"
    metadata_type = "article"

    date = models.DateField(help_text="The date this fact is for.", unique=True)
    content = RichTextField(
        help_text="The content of this fact.",
        validators=[RichTextMaxLengthValidator(500)],
    )
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="facts",
    )
    image_description = models.TextField(
        max_length=150, help_text="The caption for this image", blank=True
    )
    image_alt = models.TextField(
        max_length=300, help_text="Override the alt text for this image", blank=True
    )
    references = StreamField(
        ReferenceStreamBlock, help_text="The references for this fact"
    )

    @property
    def image_alt_text(self):
        if not self.image:
            return
        return self.image_alt or self.image.default_alt_text

    @property
    def metadata_description(self):
        content = strip_tags(expand_db_html(self.content))
        return Truncator(" ".join(content.split())).chars(240, truncate="...")

    @property
    def metadata_image(self):
        if not self.image:
            return None
        return self.image

    @property
    def metadata_image_alt(self):
        return self.image_alt_text

    @property
    def feed_published_at(self):
        return timezone.make_aware(datetime.combine(self.date, time.min))

    @property
    def feed_updated_at(self):
        return self.feed_published_at()

    def clean(self):
        super().clean()
        # If we're a future date, schedule it for publishing at midnight
        if self.date and self.date > timezone.localdate():
            self.go_live_at = timezone.make_aware(datetime.combine(self.date, time.min))

    def get_older_fact(self):
        """
        Returns the fact which is the "next older", or None
        if this is the oldest fact.
        """
        if not self.date:
            return None
        return (
            FactPage.objects.live().order_by("-date").filter(date__lt=self.date).first()
        )

    def get_newer_fact(self):
        """
        Returns the fact with the "next newer", or None
        if this is the newest fact.
        """
        if not self.date:
            return None
        return (
            FactPage.objects.live().order_by("date").filter(date__gt=self.date).first()
        )

    def get_schema_graph(self, request, metadata):
        article = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": metadata["title"],
            "description": metadata["description"],
            "url": metadata["url"],
            "datePublished": self.date,
        }

        if metadata["site"].site_name:
            article["author"] = {
                "@type": "Organization",
                "name": metadata["site"].site_name,
            }

        keywords = [tag.name for tag in self.get_tags()]
        if keywords:
            article["keywords"] = keywords

        citations = [
            {
                "@type": "CreativeWork",
                "name": strip_tags(block.value["label"]),
                "url": block.value["url"],
            }
            for block in self.references
        ]
        if citations:
            article["citation"] = citations

        return [article]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["share"] = self.get_full_url(request)
        context["related_pages"] = self.get_related_pages()
        return context

    @classmethod
    def get_indexed_objects(cls):
        return (
            super()
            .get_indexed_objects()
            .prefetch_related(
                Prefetch(
                    "tag_assignments",
                    queryset=PageTag.objects.select_related("tag"),
                )
            )
        )

    content_panels = Page.content_panels + [
        "date",
        "content",
        MultiFieldPanel(
            [
                "image",
                FieldPanel(
                    "image_description",
                    heading="Image Caption",
                    help_text="The caption displayed underneath the image.",
                ),
                FieldPanel(
                    "image_alt",
                    help_text="Override the alt text for this image. If not provided, falls back to the description of the image.",
                ),
            ],
            heading="Fact Image",
        ),
        "references",
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

    promote_panels = [
        UmamiAnalyticsPanel(),
    ] + Page.promote_panels

    search_fields = Page.search_fields + [
        index.SearchField("content"),
        index.FilterField("date"),
    ]
