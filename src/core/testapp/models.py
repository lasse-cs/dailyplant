from wagtail.fields import StreamField
from wagtail.models import Page

from core.models import TableOfContentsPageMixin
from core.testapp.blocks import RootStreamBlock


class TocPage(TableOfContentsPageMixin, Page):
    body = StreamField(RootStreamBlock(), blank=True)
