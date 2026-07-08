from wagtail.models import Page

from core.models import MarkdownPageMixin
from facts.models import FactPage


class HomePage(MarkdownPageMixin, Page):
    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    template = "patterns/pages/home/home_page.html"
    markdown_template = "non_patterns/pages/home/home_page.md"

    def get_fact(self):
        return FactPage.objects.live().released().order_by("-date").first()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["fact"] = self.get_fact()
        return context
