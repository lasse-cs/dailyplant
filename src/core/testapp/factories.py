import factory
from wagtail_factories import (
    ListBlockFactory,
    PageFactory,
    StreamBlockFactory,
    StreamFieldFactory,
    StructBlockFactory,
)

from core.factories import HeadingBlockFactory
from core.testapp.blocks import (
    GroupedContentBlock,
    NestedStreamBlock,
    RootStreamBlock,
)
from core.testapp.models import (
    BreadcrumbPage,
    LLMsTxtListingPage,
    MissingDetailsTemplatePage,
    RelatedPagesTestPage,
    TocPage,
)


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


class RelatedPagesTestPageFactory(PageFactory):
    class Meta:
        model = RelatedPagesTestPage


class MissingDetailsTemplatePageFactory(PageFactory):
    class Meta:
        model = MissingDetailsTemplatePage


class LLMsTxtListingPageFactory(PageFactory):
    class Meta:
        model = LLMsTxtListingPage
