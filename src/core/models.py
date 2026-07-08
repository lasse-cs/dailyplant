from django.db import models
from django.shortcuts import render
from django.utils.cache import patch_vary_headers

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import InlinePanel
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page
from wagtail.contrib.routable_page.models import path
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


class MetadataMixin:
    metadata_template = "patterns/components/metadata/default.html"
    metadata_type = "website"

    def get_metadata_url(self, request):
        return self.get_full_url(request)

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


def _is_markdown(request):
    content_type = request.get_preferred_type(["text/html", "text/markdown"])
    return content_type == "text/markdown"


class MarkdownRoutablePageMixin:
    markdown_template = None

    @path("")
    def index_route(self, request, *args, **kwargs):
        request.is_preview = getattr(request, "is_preview", False)
        return self.render(request, *args, **kwargs)

    def render(self, request, *args, template=None, context_overrides=None, **kwargs):
        if _is_markdown(request):
            response = self.render_markdown(
                request,
                *args,
                template=template,
                context_overrides=context_overrides,
                **kwargs,
            )
        else:
            response = super().render(
                request,
                *args,
                template=template,
                context_overrides=context_overrides,
                **kwargs,
            )
        patch_vary_headers(response, ["Accept"])
        return response

    def render_markdown(
        self, request, *args, template=None, context_overrides=None, **kwargs
    ):
        if template is None:
            template = self.get_markdown_template(request, *args, **kwargs)
        context = self.get_context(request, *args, **kwargs)
        context.update(context_overrides or {})
        return render(
            request, template, context, content_type="text/markdown; charset=utf-8"
        )

    def get_markdown_template(self, request, *args, **kwargs):
        return self.markdown_template


class MarkdownPageMixin:
    markdown_template = None

    def serve(self, request, *args, **kwargs):
        if _is_markdown(request):
            response = self.serve_markdown(request, *args, **kwargs)
        else:
            response = super().serve(request, *args, **kwargs)
        patch_vary_headers(response, ["Accept"])
        return response

    def serve_markdown(self, request, *args, **kwargs):
        context = self.get_context(request, *args, **kwargs)
        template = self.get_markdown_template(request, *args, **kwargs)
        return render(
            request, template, context, content_type="text/markdown; charset=utf-8"
        )

    def get_markdown_template(self, request, *args, **kwargs):
        return self.markdown_template


class ContentPage(MarkdownPageMixin, Page):
    template = "patterns/pages/core/content.html"
    markdown_template = "non_patterns/pages/core/content.md"

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
