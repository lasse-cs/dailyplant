from wagtail.fields import StreamField
from wagtail.models import Page

from core.breadcrumbs import Breadcrumb
from core.models import TableOfContentsPageMixin
from core.testapp.blocks import RootStreamBlock


class TocPage(TableOfContentsPageMixin, Page):
    body = StreamField(RootStreamBlock(), blank=True)


class BreadcrumbPage(Page):
    def get_extra_breadcrumb(self, request) -> Breadcrumb | None:
        return getattr(request, "extra_breadcrumb", None)
