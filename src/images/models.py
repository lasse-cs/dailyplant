from django.core.paginator import InvalidPage, Paginator
from django.db import models
from django.http import Http404
from django.utils.html import strip_tags
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, MultipleChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page
from wagtail.rich_text import expand_db_html
from wagtail.search import index

from core.blocks import ReferenceStructBlock
from core.models import (
    ListingSitemapMixin,
    LLMsTxtListingMixin,
    MarkdownPageMixin,
    MetadataMixin,
    RelatedPagesMixin,
    TaggedPageMixin,
)
from core.panels import IncomingRelatedPagesPanel
from search.models import SearchablePageMixin


class ImagesListingPage(
    ListingSitemapMixin, LLMsTxtListingMixin, MetadataMixin, MarkdownPageMixin, Page
):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["images.ImagePage"]
    max_count = 1
    template = "patterns/pages/images/listing.html"
    markdown_template = "non_patterns/pages/images/listing.md"

    introduction = RichTextField(blank=True)

    content_panels = Page.content_panels + ["introduction"]

    def get_images(self):
        return (
            ImagePage.objects.live()
            .child_of(self)
            .select_related("image")
            .prefetch_related("image__renditions")
            .order_by("-first_published_at", "-pk")
        )

    def get_paginator(self):
        return Paginator(self.get_images(), 18, orphans=2)

    def get_llms_txt_pages(self):
        return self.get_images()

    def get_sitemap_pages(self):
        return self.get_paginator().page(1).object_list

    def get_metadata_url(self, request):
        url = super().get_metadata_url(request)
        try:
            number = int(request.GET.get("page", 1))
        except ValueError:
            return url
        return f"{url}?page={number}" if number > 1 else url

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        try:
            context["images"] = self.get_paginator().page(request.GET.get("page", 1))
        except InvalidPage:
            raise Http404
        return context


class ImagePage(
    SearchablePageMixin,
    MetadataMixin,
    RelatedPagesMixin,
    TaggedPageMixin,
    MarkdownPageMixin,
    Page,
):
    parent_page_types = ["images.ImagesListingPage"]
    subpage_types = []
    template = "patterns/pages/images/image.html"
    markdown_template = "non_patterns/pages/images/image.md"
    search_result_template = "patterns/components/search/results/image.html"
    related_page_details_template = "non_patterns/images/related_page_details.html"
    related_type = "image"

    image = models.OneToOneField(
        get_image_model_string(),
        on_delete=models.PROTECT,
        related_name="image_page",
        help_text="The image this page describes.",
    )
    description = RichTextField()
    image_description = models.TextField(
        max_length=150,
        blank=True,
        help_text="The caption displayed underneath the image.",
    )
    image_alt = models.TextField(
        max_length=300,
        blank=True,
        help_text="Override the image's default alt text for this page.",
    )
    references = StreamField(
        [("reference", ReferenceStructBlock())],
        blank=True,
        help_text="Optional sources or further reading for this image.",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("image"),
                FieldPanel("image_description", heading="Image Caption"),
                FieldPanel("image_alt"),
            ],
            heading="Image",
        ),
        FieldPanel("description"),
        FieldPanel("references"),
        MultipleChooserPanel("tag_assignments", label="Tags", chooser_field_name="tag"),
        MultipleChooserPanel(
            "outgoing_page_relationships",
            label="Related Pages",
            chooser_field_name="target",
        ),
        IncomingRelatedPagesPanel(),
    ]
    search_fields = Page.search_fields + [index.SearchField("description")]

    class Meta:
        verbose_name = "image"
        verbose_name_plural = "images"

    @property
    def image_alt_text(self):
        return self.image_alt or self.image.default_alt_text

    @property
    def metadata_description(self):
        return " ".join(strip_tags(expand_db_html(self.description)).split())

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
