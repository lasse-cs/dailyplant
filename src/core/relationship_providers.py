from django.db.models import Q

from core.models import PageRelationship
from core.relationships import RelationshipEdge


class ManualRelationshipProvider:
    def edges_for_pages(self, page_ids):
        relationships = PageRelationship.objects.filter(
            source_id__in=page_ids, target_id__in=page_ids
        ).values_list("source_id", "target_id")
        return (RelationshipEdge(source, target) for source, target in relationships)

    def related_page_ids(self, page):
        relationships = PageRelationship.objects.filter(
            Q(source_id=page.pk) | Q(target_id=page.pk)
        ).values_list("source_id", "target_id")
        return (
            target if source == page.pk else source for source, target in relationships
        )
