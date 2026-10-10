import pytest
from wagtail.models import Page
from wagtail_factories import ImageFactory

from core.factories import RelatedPagesExplorerPageFactory
from core.models import PageRelationship, RelatedPagesMixin
from core.relationships import RelationshipEdge, graph_for_pages
from core.testapp.factories import RelatedPagesTestPageFactory
from images.factories import ImagePageFactory, ImagesListingPageFactory
from images.relationships import ImageUsageRelationshipProvider

pytestmark = pytest.mark.django_db


def related_ids(page):
    return set(page.get_related_pages().values_list("pk", flat=True))


def test_provider_excludes_self_edges_before_service_filtering(root_page):
    image_page = ImagePageFactory(parent=root_page)
    content = RelatedPagesTestPageFactory(parent=root_page, image=image_page.image)
    edges = list(
        ImageUsageRelationshipProvider().edges_for_pages({image_page.pk, content.pk})
    )
    assert edges == [RelationshipEdge(image_page.pk, content.pk)]


def test_same_asset_connects_both_ways_and_deduplicates_manual_edges(client, root_page):
    image = ImageFactory()
    content = RelatedPagesTestPageFactory(parent=root_page, image=image)
    # Creating the Image page after the content requires no backfill.
    listing = ImagesListingPageFactory(parent=root_page)
    image_page = ImagePageFactory(parent=listing, image=image)
    unrelated = RelatedPagesTestPageFactory(parent=root_page, image=ImageFactory())
    without_image = RelatedPagesTestPageFactory(parent=root_page)
    assert related_ids(image_page) == {content.pk}
    assert related_ids(content) == {image_page.pk}
    assert not related_ids(unrelated)
    assert not related_ids(without_image)
    assert not PageRelationship.objects.exists()

    PageRelationship.objects.create(source=content, target=image_page)
    PageRelationship.objects.create(source=image_page, target=content)
    explorer = RelatedPagesExplorerPageFactory(parent=root_page, title="Explorer")
    nodes = client.get(explorer.url).context["data"]["nodes"]
    assert nodes[image_page.pk]["type"] == "image"
    assert nodes[image_page.pk]["edges"] == [content.pk]
    assert nodes[content.pk]["edges"] == [image_page.pk]
    assert nodes[image_page.pk]["degree"] == 1
    assert nodes[content.pk]["degree"] == 1


def test_image_changes_take_effect_on_publication_and_manual_links_survive(
    root_page,
):
    first = ImagePageFactory(parent=root_page)
    second = ImagePageFactory(parent=root_page)
    content = RelatedPagesTestPageFactory(parent=root_page, image=first.image)
    content.save_revision().publish()
    content.image = second.image
    revision = content.save_revision()
    assert related_ids(content) == {first.pk}
    assert related_ids(first) == {content.pk}
    assert not related_ids(second)

    revision.publish()
    content.refresh_from_db()
    assert related_ids(content) == {second.pk}
    assert not related_ids(first)
    assert related_ids(second) == {content.pk}

    PageRelationship.objects.create(source=second, target=content)
    content.image = None
    content.save_revision().publish()
    content.refresh_from_db()
    assert related_ids(content) == {second.pk}
    PageRelationship.objects.all().delete()
    assert not related_ids(content)
    assert not related_ids(second)


def test_draft_unpublish_republish_and_delete(root_page):
    image_page = ImagePageFactory(parent=root_page, live=False)
    published = RelatedPagesTestPageFactory(parent=root_page, image=image_page.image)
    draft = RelatedPagesTestPageFactory(
        parent=root_page, image=image_page.image, live=False
    )
    assert not related_ids(published)
    image_page.save_revision().publish()
    image_page.refresh_from_db()
    assert related_ids(image_page) == {published.pk}
    draft.save_revision().publish()
    draft.refresh_from_db()
    assert related_ids(image_page) == {published.pk, draft.pk}
    published.unpublish()
    assert related_ids(image_page) == {draft.pk}
    graph = graph_for_pages(Page.objects.type(RelatedPagesMixin).live())
    assert graph.neighbors(image_page.pk) == [draft.pk]
    draft.delete()
    assert not related_ids(image_page)
    image_page.unpublish()
    assert not related_ids(published)


def test_image_page_draft_change_does_not_change_public_edges(root_page):
    image_page = ImagePageFactory(parent=root_page)
    content = RelatedPagesTestPageFactory(parent=root_page, image=image_page.image)
    image_page.save_revision().publish()
    image_page.image = ImageFactory()
    revision = image_page.save_revision()
    assert related_ids(image_page) == {content.pk}
    assert related_ids(content) == {image_page.pk}
    revision.publish()
    assert not related_ids(content)
    assert not related_ids(image_page)


def test_graph_uses_bulk_queries(root_page, django_assert_num_queries):
    images = [ImagePageFactory(parent=root_page) for _ in range(3)]
    content_pages = [
        RelatedPagesTestPageFactory(parent=root_page, image=page.image)
        for page in images
    ]
    with django_assert_num_queries(3):
        graph = graph_for_pages([*images, *content_pages])
    for image, content in zip(images, content_pages, strict=True):
        assert graph.neighbors(image.pk) == [content.pk]
        assert graph.neighbors(content.pk) == [image.pk]
