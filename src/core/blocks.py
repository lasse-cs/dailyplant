from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify

from wagtail import blocks
from wagtail.models import get_page_models


class HeadingLevel(models.TextChoices):
    H2 = "2", "Heading 2"
    H3 = "3", "Heading 3"


class HeadingValue(blocks.StructValue):
    @property
    def anchor(self):
        return slugify(self["text"])


class HeadingBlock(blocks.StructBlock):
    text = blocks.CharBlock(label="Heading")
    level = blocks.ChoiceBlock(
        choices=HeadingLevel.choices,
        default=HeadingLevel.H2,
    )

    class Meta:
        icon = "title"
        label = "Heading"
        label_format = "{text}"
        template = "patterns/components/core/heading.html"
        value_class = HeadingValue


class ContentStreamBlock(blocks.StreamBlock):
    heading = HeadingBlock()
    paragraph = blocks.RichTextBlock()


class LLMsTxtListingPageChooserBlock(blocks.PageChooserBlock):
    @cached_property
    def target_models(self):
        from core.models import LLMsTxtListingMixin

        return [
            model
            for model in get_page_models()
            if issubclass(model, LLMsTxtListingMixin)
        ]

    def clean(self, value):
        from core.models import LLMsTxtListingMixin

        page = super().clean(value)
        if page and not isinstance(page.specific, LLMsTxtListingMixin):
            raise ValidationError("Choose a page that provides an LLMs.txt listing.")
        return page


class LLMsTxtCuratedSectionValue(blocks.StructValue):
    def get_llms_txt_section(self):
        return self["title"], self["pages"]


class LLMsTxtCuratedSectionBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    pages = blocks.ListBlock(blocks.PageChooserBlock())

    class Meta:
        icon = "list-ul"
        label = "Curated section"
        value_class = LLMsTxtCuratedSectionValue


class LLMsTxtAutomaticSectionValue(blocks.StructValue):
    max_links = 5

    def get_llms_txt_section(self):
        listing_page = self["listing_page"]
        if not listing_page:
            return None

        listing_page = listing_page.specific
        pages = listing_page.get_llms_txt_pages()[: self.max_links]
        return listing_page.title, pages


class LLMsTxtAutomaticSectionBlock(blocks.StructBlock):
    listing_page = LLMsTxtListingPageChooserBlock()

    class Meta:
        icon = "list-ul"
        label = "Automatic section"
        value_class = LLMsTxtAutomaticSectionValue


class LLMsTxtSectionsBlock(blocks.StreamBlock):
    curated = LLMsTxtCuratedSectionBlock()
    automatic = LLMsTxtAutomaticSectionBlock()
