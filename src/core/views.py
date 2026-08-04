from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_safe
from django.views.decorators.vary import vary_on_headers

from core.models import LLMsTxtSettings


@cache_page(60 * 60)
@vary_on_headers("Host")
@require_safe
def llms_txt(request):
    return LLMsTxtSettings.for_request(request).render(request)
