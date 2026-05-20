from django.db import models

from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Page
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


class MetadataMixin:
    metadata_template_name = "patterns/components/metadata/default.html"
    metadata_type = "website"

    @property
    def metadata_image(self):
        return None


@register_setting
class MetadataSettings(BaseSiteSetting):
    description = models.TextField(
        blank=True,
        help_text="Base site description.",
    )

    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Base image to use for site metadata",
    )

    panels = [
        "description",
        "image",
    ]


class ContentPage(Page):
    template = "patterns/pages/core/content.html"

    body = RichTextField(help_text="The content for this page.")

    content_panels = Page.content_panels + [
        "body",
    ]
