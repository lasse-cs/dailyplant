from dataclasses import dataclass

from django.http import HttpRequest

from wagtail.models import Page
from wagtail.models import Site


@dataclass(frozen=True, slots=True)
class Breadcrumb:
    name: str
    url: str


def _page_url(page: Page, request: HttpRequest) -> str:
    if hasattr(page, "get_metadata_url"):
        return page.get_metadata_url(request)
    return page.get_full_url(request)


def _build_breadcrumbs(
    request: HttpRequest, page: Page | None = None
) -> list[Breadcrumb]:
    if page is None:
        return []

    site = Site.find_for_request(request)
    if not site:
        return []

    root_page = site.root_page
    page = page.specific
    if page.pk == root_page.pk:
        return []

    root_item = Breadcrumb(name=root_page.title, url=site.root_url)

    ancestors = page.get_ancestors(inclusive=True).filter(depth__gte=root_page.depth)
    items = [
        Breadcrumb(name=ancestor.title, url=ancestor.get_full_url(request))
        for ancestor in ancestors
    ]
    items[0] = root_item

    get_extra_breadcrumb = getattr(page, "get_extra_breadcrumb", None)
    if get_extra_breadcrumb:
        extra_item = get_extra_breadcrumb(request)
        if extra_item:
            items.append(extra_item)
            return items

    items[-1] = Breadcrumb(name=page.title, url=_page_url(page, request))
    return items


def build_breadcrumbs(
    request: HttpRequest, page: Page | None = None
) -> list[Breadcrumb]:
    cache = getattr(request, "_breadcrumb_cache", None)
    if cache is None:
        cache = request._breadcrumb_cache = {}

    cache_key = getattr(page, "pk", None)
    if cache_key not in cache:
        cache[cache_key] = _build_breadcrumbs(request, page)
    return cache[cache_key]
