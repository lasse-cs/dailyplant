from wagtail.fields import StreamField
from wagtail.models import Page

from core.breadcrumbs import Breadcrumb
from core.models import ContentPage, LLMsTxtListingMixin, TableOfContentsPageMixin
from core.testapp.blocks import RootStreamBlock


class TocPage(TableOfContentsPageMixin, Page):
    body = StreamField(RootStreamBlock(), blank=True)


class LLMsTxtListingPage(LLMsTxtListingMixin, Page):
    def get_llms_txt_pages(self):
        return ContentPage.objects.live().child_of(self).order_by("-first_published_at")


class BreadcrumbPage(Page):
    def get_extra_breadcrumb(self, request) -> Breadcrumb | None:
        return getattr(request, "extra_breadcrumb", None)
