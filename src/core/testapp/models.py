from django.db import models
from wagtail.fields import StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page

from core.breadcrumbs import Breadcrumb
from core.models import (
    ContentPage,
    LLMsTxtListingMixin,
    RelatedPagesMixin,
    TableOfContentsPageMixin,
)
from core.testapp.blocks import RootStreamBlock


class TocPage(TableOfContentsPageMixin, Page):
    body = StreamField(RootStreamBlock(), blank=True)


class LLMsTxtListingPage(LLMsTxtListingMixin, Page):
    def get_llms_txt_pages(self):
        return ContentPage.objects.live().child_of(self).order_by("-first_published_at")


class BreadcrumbPage(Page):
    def get_extra_breadcrumb(self, request) -> Breadcrumb | None:
        return getattr(request, "extra_breadcrumb", None)


class RelatedPagesTestPage(RelatedPagesMixin, Page):
    template = "core_testapp/related_pages_test_page.html"
    related_page_details_template = "core_testapp/related_page_details.html"
    related_type = "test"

    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )


class MissingDetailsTemplatePage(RelatedPagesMixin, Page):
    related_type = "missing-details-template"
