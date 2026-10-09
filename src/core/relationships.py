"""Discover public relationships without coupling consumers to their sources.

Apps register provider factories with the project-defined
``register_relationship_provider`` Wagtail hook. Providers must implement both
the bulk and individual-page paths for the same bidirectional relationship rule.
Discovery is read-only; providers should query in bulk rather than per graph node.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from wagtail import hooks
from wagtail.models import Page


@dataclass(frozen=True)
class RelationshipEdge:
    source_id: int
    target_id: int


class RelationshipProvider(Protocol):
    def edges_for_pages(self, page_ids: set[int]) -> Iterable[RelationshipEdge]:
        """Return edges with both endpoints in the supplied set."""
        ...

    def related_page_ids(self, page: Page) -> Iterable[int]:
        """Return neighbors in either direction; consumers filter visibility."""
        ...


def get_providers() -> Iterable[RelationshipProvider]:
    for register in hooks.get_hooks("register_relationship_provider"):
        yield register()


def related_page_ids(page: Page) -> set[int]:
    """Merge provider results; the caller must filter for live pages."""
    if not page.pk:
        return set()
    return {
        page_id
        for provider in get_providers()
        for page_id in provider.related_page_ids(page)
        if page_id != page.pk
    }


@dataclass
class RelationshipGraph:
    adjacency: dict[int, list[int]]

    def neighbors(self, page_id: int) -> list[int]:
        return self.adjacency[page_id]

    def degree(self, page_id: int) -> int:
        return len(self.neighbors(page_id))


def graph_for_pages(pages: Iterable[Page]) -> RelationshipGraph:
    """Build a unique undirected graph within the caller's eligible page set."""
    page_ids = {page.pk for page in pages if page.pk is not None}
    edges = set()
    if page_ids:
        for provider in get_providers():
            for edge in provider.edges_for_pages(page_ids):
                source, target = edge.source_id, edge.target_id
                if source != target and source in page_ids and target in page_ids:
                    edges.add((min(source, target), max(source, target)))

    adjacency = {page_id: [] for page_id in page_ids}
    for source, target in sorted(edges):
        adjacency[source].append(target)
        adjacency[target].append(source)
    return RelationshipGraph(adjacency)
