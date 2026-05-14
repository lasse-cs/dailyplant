from wagtail.models import Page


class HomePage(Page):
    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    template = "patterns/pages/home/home_page.html"
