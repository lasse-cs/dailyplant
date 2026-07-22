import factory

from wagtail_factories import (
    ListBlockFactory,
    PageFactory,
    StreamBlockFactory,
    StreamFieldFactory,
    StructBlockFactory,
)

from core.blocks import HeadingBlock, HeadingLevel
from core.testapp.blocks import (
    GroupedContentBlock,
    NestedStreamBlock,
    RootStreamBlock,
)
from core.testapp.models import BreadcrumbPage, TocPage


class HeadingBlockFactory(StructBlockFactory):
    text = factory.Sequence(lambda index: f"Heading {index}")
    level = HeadingLevel.H2

    class Meta:
        model = HeadingBlock


class NestedStreamBlockFactory(StreamBlockFactory):
    heading = factory.SubFactory(HeadingBlockFactory)

    class Meta:
        model = NestedStreamBlock


class GroupedContentBlockFactory(StructBlockFactory):
    introduction = factory.SubFactory(HeadingBlockFactory)
    items = ListBlockFactory(HeadingBlockFactory)
    body = StreamFieldFactory(NestedStreamBlockFactory)

    class Meta:
        model = GroupedContentBlock


class RootStreamBlockFactory(StreamBlockFactory):
    group = factory.SubFactory(GroupedContentBlockFactory)
    paragraph = factory.Faker("sentence")

    class Meta:
        model = RootStreamBlock


class TocPageFactory(PageFactory):
    body = StreamFieldFactory(RootStreamBlockFactory)

    class Meta:
        model = TocPage


class BreadcrumbPageFactory(PageFactory):
    class Meta:
        model = BreadcrumbPage
