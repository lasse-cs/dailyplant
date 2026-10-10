import pytest
from wagtail import hooks

from core.factories import RelatedPagesExplorerPageFactory
from core.models import PageRelationship
from core.relationships import RelationshipEdge, graph_for_pages
from core.testapp.factories import RelatedPagesTestPageFactory
from core.testapp.models import RelatedPagesTestPage

pytestmark = pytest.mark.django_db


def test_manual_relationships_are_unique_bidirectional_and_live(client, root_page):
    source, target, draft, isolated = [
        RelatedPagesTestPageFactory(parent=root_page, title=f"Page {i}", live=live)
        for i, live in enumerate([True, True, False, True])
    ]
    for first, second in [
        (source, target),
        (source, target),
        (target, source),
        (source, source),
        (source, draft),
    ]:
        PageRelationship.objects.create(source=first, target=second)

    assert list(source.get_related_pages()) == [target]
    assert list(target.get_related_pages()) == [source]
    assert not isolated.get_related_pages().exists()

    explorer = RelatedPagesExplorerPageFactory(parent=root_page)
    nodes = client.get(explorer.url).context["data"]["nodes"]
    assert draft.pk not in nodes
    assert nodes[source.pk]["edges"] == [target.pk]
    assert nodes[target.pk]["edges"] == [source.pk]
    assert nodes[source.pk]["degree"] == nodes[target.pk]["degree"] == 1
    assert nodes[isolated.pk]["edges"] == []
    assert nodes[isolated.pk]["degree"] == 0


def test_additional_provider_contributes_to_listings_and_explorer(client, root_page):
    source, manual, automatic, draft = [
        RelatedPagesTestPageFactory(parent=root_page, title=f"Page {i}", live=live)
        for i, live in enumerate([True, True, True, False])
    ]
    PageRelationship.objects.create(source=source, target=manual)
    edges = [
        RelationshipEdge(source.pk, manual.pk),
        RelationshipEdge(source.pk, automatic.pk),
        RelationshipEdge(automatic.pk, source.pk),
        RelationshipEdge(source.pk, source.pk),
        RelationshipEdge(source.pk, draft.pk),
    ]

    class AdditionalProvider:
        def edges_for_pages(self, page_ids):
            # Also exercise the service's boundary filtering.
            return edges

        def related_page_ids(self, page):
            return [
                edge.target_id if edge.source_id == page.pk else edge.source_id
                for edge in edges
                if page.pk in (edge.source_id, edge.target_id)
            ]

    explorer = RelatedPagesExplorerPageFactory(parent=root_page)
    with hooks.register_temporarily(
        "register_relationship_provider", AdditionalProvider
    ):
        nodes = client.get(explorer.url).context["data"]["nodes"]
        for page, expected in [
            (source, {manual.pk, automatic.pk}),
            (manual, {source.pk}),
            (automatic, {source.pk}),
        ]:
            assert (
                set(page.get_related_pages().values_list("pk", flat=True)) == expected
            )
            assert set(nodes[page.pk]["edges"]) == expected
            assert nodes[page.pk]["degree"] == len(expected)
        assert draft.pk not in nodes

    assert list(source.get_related_pages()) == [manual]
    assert PageRelationship.objects.count() == 1


def test_unsaved_page_and_empty_graph_do_not_query(django_assert_num_queries):
    with django_assert_num_queries(0):
        assert list(RelatedPagesTestPage().get_related_pages()) == []
        assert graph_for_pages([]).adjacency == {}


def test_graph_without_image_pages_uses_bulk_queries(
    root_page, django_assert_num_queries
):
    pages = [
        RelatedPagesTestPageFactory(parent=root_page, title=f"Page {i}")
        for i in range(4)
    ]
    for target in pages[1:]:
        PageRelationship.objects.create(source=pages[0], target=target)

    # One manual-edge query and one check for Image pages in the graph.
    with django_assert_num_queries(2):
        graph = graph_for_pages(pages)

    assert graph.neighbors(pages[0].pk) == sorted(page.pk for page in pages[1:])
    assert graph.degree(pages[0].pk) == 3
