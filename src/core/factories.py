import factory
from wagtail_factories import PageFactory, SiteFactory

from core.models import (
    ContentPage,
    PageRelationship,
    PageTag,
    RelatedPagesExplorerPage,
    SocialMediaChoices,
    SocialMediaLink,
    SocialMediaSettings,
    Tag,
)


class RelatedPagesExplorerPageFactory(PageFactory):
    intro = "<p>Explore related pages.</p>"

    class Meta:
        model = RelatedPagesExplorerPage


class SocialMediaSettingsFactory(factory.django.DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SocialMediaSettings


class SocialMediaLinkFactory(factory.django.DjangoModelFactory):
    social_settings = factory.SubFactory(SocialMediaSettingsFactory)
    display = factory.Sequence(lambda index: f"Social link {index}")
    url = factory.Sequence(lambda index: f"https://example.com/social/{index}")
    type = factory.Faker(
        "random_element",
        elements=[choice.value for choice in SocialMediaChoices],
    )

    class Meta:
        model = SocialMediaLink


class RelatedPagesFactoryMixin(PageFactory):
    @factory.post_generation
    def related_pages(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        PageRelationship.objects.bulk_create(
            [PageRelationship(source=self, target=page) for page in extracted]
        )

    class Meta:
        abstract = True


class TaggedPageFactoryMixin(PageFactory):
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        tags = [
            Tag.objects.get_or_create(name=tag)[0] if isinstance(tag, str) else tag
            for tag in extracted
        ]
        PageTag.objects.bulk_create([PageTag(page=self, tag=tag) for tag in tags])

    class Meta:
        abstract = True


class ContentPageFactory(PageFactory):
    body = factory.Faker("paragraph")

    class Meta:
        model = ContentPage
