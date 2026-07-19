from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.shortcuts import render
from django.utils.cache import patch_vary_headers
from django.utils.text import slugify

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import InlinePanel
from wagtail.blocks import ListBlock, StreamBlock, StructBlock
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page
from wagtail.contrib.routable_page.models import path
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from core.blocks import HeadingBlock
from core.panels import RelatedPageChooserPanel


@dataclass
class TocItem:
    label: str
    anchor: str
    level: int
    children: list["TocItem"] = field(default_factory=list)


def collect_toc_items(block, value):
    """Return heading items in document order without nesting."""
    if isinstance(block, HeadingBlock):
        return [
            TocItem(
                label=value["text"],
                anchor=value.anchor,
                level=int(value["level"]),
            )
        ]

    if isinstance(block, StreamBlock):
        items = []
        for child in value:
            items.extend(collect_toc_items(child.block, child.value))
        return items

    if isinstance(block, StructBlock):
        items = []
        for name, child_block in block.child_blocks.items():
            items.extend(collect_toc_items(child_block, value[name]))
        return items

    if isinstance(block, ListBlock):
        items = []
        for child_value in value:
            items.extend(collect_toc_items(block.child_block, child_value))
        return items

    return []


def build_toc_tree(items):
    """Return copies of flat items nested according to their heading levels."""
    roots = []
    stack = []

    for item in items:
        node = TocItem(
            label=item.label,
            anchor=item.anchor,
            level=item.level,
        )

        while stack and stack[-1].level >= node.level:
            stack.pop()

        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)

        stack.append(node)

    return roots


class MetadataMixin:
    metadata_template = "patterns/components/metadata/default.html"
    metadata_type = "website"

    def get_metadata_url(self, request):
        return self.get_full_url(request)

    @property
    def metadata_image(self):
        return None


class RelatedPagesMixin:
    def get_incoming_related_pages(self):
        if not self.pk:
            return Page.objects.none()
        return (
            Page.objects.live()
            .filter(outgoing_page_relationships__target=self)
            .distinct()
            .specific()
        )

    def get_outgoing_related_pages(self):
        if not self.pk:
            return Page.objects.none()
        return (
            Page.objects.live()
            .filter(incoming_page_relationships__source=self)
            .distinct()
            .specific()
        )

    def get_related_pages(self):
        if not self.pk:
            return Page.objects.none()
        return (
            Page.objects.live()
            .filter(
                Q(outgoing_page_relationships__target=self)
                | Q(incoming_page_relationships__source=self)
            )
            .exclude(pk=self.pk)
            .distinct()
            .specific()
        )


class TableOfContentsPageMixin:
    table_of_contents_field = "body"

    def get_toc_items(self):
        body = getattr(self, self.table_of_contents_field)
        return collect_toc_items(body.stream_block, body)

    def get_table_of_contents(self):
        return build_toc_tree(self.get_toc_items())


class PageRelationship(models.Model):
    source = ParentalKey(
        Page,
        related_name="outgoing_page_relationships",
        on_delete=models.CASCADE,
    )
    target = models.ForeignKey(
        Page,
        related_name="incoming_page_relationships",
        on_delete=models.CASCADE,
    )

    panels = [RelatedPageChooserPanel("target")]


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        editable=False,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def _slug_from_name(self):
        slug = slugify(self.name)[:100]
        if not slug:
            raise ValidationError(
                {"name": "The name must contain characters that can form a URL slug."}
            )
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = self._slug_from_name()
            slug = base_slug
            index = 1
            while Tag.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                index += 1
                suffix = f"-{index}"
                slug = f"{base_slug[: 100 - len(suffix)]}{suffix}"
            self.slug = slug
        return super().save(*args, **kwargs)

    def get_pages(self):
        return (
            Page.objects.live().filter(tag_assignments__tag=self).distinct().specific()
        )


class TaggedPageMixin:
    def get_tags(self):
        return [assignment.tag for assignment in self.tag_assignments.all()]


class PageTag(models.Model):
    page = ParentalKey(
        Page,
        related_name="tag_assignments",
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey(
        Tag,
        related_name="page_assignments",
        on_delete=models.CASCADE,
    )

    panels = ["tag"]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["page", "tag"],
                name="unique_page_tag",
            )
        ]


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
    is_markdown = content_type == "text/markdown"
    is_markdown |= getattr(request, "preview_mode", "") == "markdown"
    is_markdown |= getattr(request, "is_md_suffix", False)
    return is_markdown


def markdown_page_url(page, request=None):
    url = page.get_full_url(request)
    if not getattr(page, "supports_md_suffix", False):
        return url
    return url.rstrip("/") + ".md"


class MarkdownRoutablePageMixin:
    markdown_template = None
    supports_md_suffix = True

    @property
    def preview_modes(self):
        return [*super().preview_modes, ("markdown", "Markdown")]

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
        response = render(
            request, template, context, content_type="text/markdown; charset=utf-8"
        )
        markdown_url = markdown_page_url(self, request)
        if markdown_url.endswith(".md"):
            response.headers["Content-Location"] = markdown_url

        return response

    def get_markdown_template(self, request, *args, **kwargs):
        return self.markdown_template


class MarkdownPageMixin:
    markdown_template = None
    supports_md_suffix = True

    @property
    def preview_modes(self):
        return [*super().preview_modes, ("markdown", "Markdown")]

    def serve_preview(self, request, mode_name):
        if mode_name == "markdown":
            request.is_markdown_preview = True
            return self.serve_markdown(request)
        return super().serve_preview(request, mode_name)

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
        response = render(
            request, template, context, content_type="text/markdown; charset=utf-8"
        )
        markdown_url = markdown_page_url(self, request)
        if markdown_url.endswith(".md"):
            response.headers["Content-Location"] = markdown_url
        return response

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
