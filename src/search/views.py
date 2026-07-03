from django.shortcuts import render
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_GET

from facts.models import FactPage


MAX_SEARCH_RESULTS = 5


@require_GET
def search(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        results = (
            FactPage.objects.live()
            .public()
            .released()
            .search(query)[:MAX_SEARCH_RESULTS]
        )

    if "HX-Request" in request.headers:
        template = "patterns/components/search/results.html"
    else:
        template = "patterns/pages/search/search.html"

    response = render(request, template, {"query": query, "results": results})
    patch_vary_headers(response, ["HX-Request"])
    return response
