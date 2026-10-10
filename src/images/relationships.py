from django.contrib.contenttypes.models import ContentType
from wagtail.images import get_image_model
from wagtail.models import Page, ReferenceIndex

from core.models import RelatedPagesMixin
from core.relationships import RelationshipEdge
from images.models import ImagePage


class ImageUsageRelationshipProvider:
    """Discover image usage through Wagtail's maintained reference index."""

    def edges_for_pages(self, page_ids):
        image_pages = dict(
            ImagePage.objects.live()
            .filter(pk__in=page_ids)
            .values_list("image_id", "pk")
        )
        if not image_pages:
            return
        references = ReferenceIndex.get_references_to_in_bulk(
            get_image_model().objects.filter(pk__in=image_pages)
        ).filter(
            base_content_type=ContentType.objects.get_for_model(Page),
            object_id__in=[str(pk) for pk in page_ids],
        )
        for source_id, image_id in references.values_list("object_id", "to_object_id"):
            image_page_id = image_pages[int(image_id)]
            source_id = int(source_id)
            if image_page_id != source_id:
                yield RelationshipEdge(image_page_id, source_id)

    def related_page_ids(self, page):
        if not Page.objects.live().filter(pk=page.pk).exists():
            return
        # Read the stored image association, not a possibly unpublished revision.
        image_id = (
            ImagePage.objects.live()
            .filter(pk=page.pk)
            .values_list("image_id", flat=True)
            .first()
        )
        if image_id is not None:
            references = ReferenceIndex.get_references_to(
                get_image_model()(pk=image_id)
            ).filter(base_content_type=ContentType.objects.get_for_model(Page))
            source_ids = [
                int(pk) for pk in references.values_list("object_id", flat=True)
            ]
            yield from (
                Page.objects.live()
                .type(RelatedPagesMixin)
                .filter(pk__in=source_ids)
                .exclude(pk=page.pk)
                .values_list("pk", flat=True)
            )

        # The reverse lookup works for any page type, including Image pages with
        # images embedded in their description. Both paths may contribute edges.
        references = ReferenceIndex.get_references_for_object(page).filter(
            to_content_type=ContentType.objects.get_for_model(get_image_model())
        )
        image_ids = [
            int(pk) for pk in references.values_list("to_object_id", flat=True)
        ]
        yield from (
            ImagePage.objects.live()
            .filter(image_id__in=image_ids)
            .exclude(pk=page.pk)
            .values_list("pk", flat=True)
        )
