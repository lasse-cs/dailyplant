from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import InlinePanel
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page
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


@register_setting
class SocialMediaSettings(BaseSiteSetting, ClusterableModel):
    panels = [InlinePanel("social_links")]


class SocialMediaChoices(models.TextChoices):
    BLUESKY = "bluesky", "BlueSky"
    FEED = "feed", "Feed"


class SocialMediaLink(Orderable):
    social_settings = ParentalKey(
        SocialMediaSettings, on_delete=models.CASCADE, related_name="social_links"
    )
    display = models.CharField(
        help_text="The display text of this social media link",
        max_length=60,
    )
    url = models.URLField(help_text="The URL of this social media link")
    type = models.CharField(
        choices=SocialMediaChoices.choices,
        default=SocialMediaChoices.BLUESKY,
        help_text="The type of social media link",
        max_length=32,
    )
