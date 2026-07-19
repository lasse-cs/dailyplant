from django.db import models
from django.utils.text import slugify

from wagtail import blocks


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
