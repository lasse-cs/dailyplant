from wagtail.models import Page

from core.models import ListingSitemapMixin, MarkdownPageMixin
from facts.models import FactPage


class HomePage(ListingSitemapMixin, MarkdownPageMixin, Page):
    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    template = "patterns/pages/home/home_page.html"
    markdown_template = "non_patterns/pages/home/home_page.md"
    supports_md_suffix = False

    def get_fact(self):
        return FactPage.objects.live().order_by("-date").first()

    def get_sitemap_pages(self):
        return FactPage.objects.live().order_by("-date")[:1]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["fact"] = self.get_fact()
        return context
