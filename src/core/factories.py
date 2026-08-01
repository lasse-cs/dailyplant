import factory
from wagtail_factories import PageFactory

from core.models import PageRelationship, PageTag, Tag


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
