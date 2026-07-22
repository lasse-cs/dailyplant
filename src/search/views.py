from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_GET

from wagtail.models import Page, Site

from core.breadcrumbs import Breadcrumb
from search.models import SearchablePageMixin


MAX_SEARCH_RESULTS = 5


@require_GET
def search(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        results = (
            Page.objects.live()
            .public()
            .type(SearchablePageMixin)
            .specific()
            .search(query)[:MAX_SEARCH_RESULTS]
        )

    context = {"query": query, "results": results}
    if "HX-Request" in request.headers:
        template = "patterns/components/search/results.html"
    else:
        template = "patterns/pages/search/search.html"
        site = Site.find_for_request(request)
        context["breadcrumbs"] = [
            Breadcrumb(name=site.root_page.title, url=site.root_url),
            Breadcrumb(
                name="Search", url=request.build_absolute_uri(reverse("search"))
            ),
        ]

    response = render(request, template, context)
    patch_vary_headers(response, ["HX-Request"])
    return response
