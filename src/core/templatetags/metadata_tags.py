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
        or getattr(page, "seo_title")
        or getattr(page, "title")
        or site.site_name
    )
    description = (
        overrides.get("description")
        or getattr(page, "search_description")
        or settings.description
    )
    image = getattr(page, "metadata_image", settings.image)

    return {
        "title": title,
        "description": description,
        "site": site,
        "url": page.get_full_url(request) if page else request.build_absolute_uri(),
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
