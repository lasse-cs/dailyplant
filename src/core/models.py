from wagtail.fields import RichTextField
from wagtail.models import Page


class ContentPage(Page):
    template = "patterns/pages/core/content.html"

    body = RichTextField(help_text="The content for this page.")

    content_panels = Page.content_panels + [
        "body",
    ]
