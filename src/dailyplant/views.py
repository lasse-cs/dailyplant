from django.contrib.auth.decorators import user_passes_test
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from django.views.decorators.vary import vary_on_headers
from django.views.defaults import page_not_found as django_page_not_found
from django.views.defaults import server_error as django_server_error

from wagtail.coreutils import WAGTAIL_APPEND_SLASH
from wagtail.models import Page
from wagtail.views import serve


def page_not_found(request, exception, template_name="patterns/pages/error/404.html"):
    return django_page_not_found(request, exception, template_name)


def server_error(request, template_name="patterns/pages/error/500.html"):
    return django_server_error(request, template_name)


def markdown_suffix_page(request, path):
    if WAGTAIL_APPEND_SLASH:
        path += "/"
    route_result = Page.route_for_request(request, path)
    if route_result is None:
        raise Http404

    page, _, _ = route_result
    if not getattr(page, "supports_md_suffix", False):
        raise Http404

    request.is_md_suffix = True
    return serve(request, path)


@user_passes_test(lambda u: u.is_superuser)
def error_500_test(request):
    raise Exception("This is a test exception")


@cache_page(60 * 60)
@vary_on_headers("Host")
@require_GET
def robots_txt(request):
    sitemap = request.build_absolute_uri(reverse("sitemap"))
    return render(
        request,
        "non_patterns/robots.txt",
        {"sitemap": sitemap},
        content_type="text/plain",
    )
