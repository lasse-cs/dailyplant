from datetime import timedelta

import factory
from django.utils import timezone
from wagtail.rich_text import RichText
from wagtail_factories import (
    PageFactory,
    StreamBlockFactory,
    StreamFieldFactory,
    StructBlockFactory,
)

from core.factories import RelatedPagesFactoryMixin, TaggedPageFactoryMixin
from facts.blocks import ReferenceStreamBlock, ReferenceStructBlock
from facts.models import FactIndexPage, FactPage


class ReferenceStructBlockFactory(StructBlockFactory):
    label = factory.Transformer(
        factory.Faker("sentence"),
        transform=lambda value: (
            value if isinstance(value, RichText) else RichText(value)
        ),
    )
    url = factory.Faker("url")

    class Meta:
        model = ReferenceStructBlock


class ReferenceStreamBlockFactory(StreamBlockFactory):
    reference = factory.SubFactory(ReferenceStructBlockFactory)

    class Meta:
        model = ReferenceStreamBlock


class FactIndexPageFactory(PageFactory):
    class Meta:
        model = FactIndexPage


class FactPageFactory(RelatedPagesFactoryMixin, TaggedPageFactoryMixin):
    title = factory.Sequence(lambda index: f"Fact {index}")
    date = factory.Sequence(lambda index: timezone.localdate() - timedelta(days=index))
    content = factory.Faker("sentence")
    references = StreamFieldFactory(
        ReferenceStreamBlockFactory,
        **{"0": "reference"},
    )

    class Meta:
        model = FactPage
        skip_postgeneration_save = True
