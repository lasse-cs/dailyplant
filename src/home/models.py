from wagtail.models import Page

from facts.models import FactPage


class HomePage(Page):
    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    template = "patterns/pages/home/home_page.html"

    def get_fact(self):
        return FactPage.objects.live().released().order_by("-date").first()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["fact"] = self.get_fact()
        return context
