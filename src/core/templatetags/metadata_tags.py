from django.template import Library
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from wagtail.models import Site

from core.models import MetadataSettings

register = Library()


def build_metadata(page, request, **overrides):
    site = Site.find_for_request(request)
    settings = MetadataSettings.for_site(site)

    title = (
        overrides.get("title")
        or getattr(page, "seo_title", None)
        or getattr(page, "title", None)
        or site.site_name
    )
    description = (
        overrides.get("description")
        or getattr(page, "metadata_description", None)
        or getattr(page, "search_description", None)
        or settings.description
    )
    image = (
        overrides.get("image")
        or getattr(page, "metadata_image", None)
        or settings.image
    )
    url = overrides.get("url")
    if not url:
        if page and hasattr(page, "get_metadata_url"):
            url = page.get_metadata_url(request)
        elif page:
            url = page.get_full_url(request)
        else:
            url = request.build_absolute_uri()

    return {
        "title": title,
        "description": description,
        "site": site,
        "url": url,
        "type": overrides.get("type") or getattr(page, "metadata_type", "website"),
        "image": image,
    }


def get_metadata_template(page):
    return getattr(
        page, "metadata_template", "patterns/components/metadata/default.html"
    )


@register.simple_tag(takes_context=True)
def render_metadata(context, **overrides):
    request = context.get("request")
    page = context.get("page")
    metadata = build_metadata(page, request, **overrides)
    template = get_metadata_template(page)
    return mark_safe(
        render_to_string(
            template,
            {"metadata": metadata},
            request=context.get("request"),
        )
    )
