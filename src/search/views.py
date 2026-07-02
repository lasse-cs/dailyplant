from django.shortcuts import render
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

    return render(
        request,
        "patterns/components/search/results.html",
        {
            "query": query,
            "results": results,
        },
    )
