import json

from django.core.serializers.json import DjangoJSONEncoder
from django.template import Library
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from wagtail.models import Site

from core.models import MetadataSettings, SocialMediaChoices, SocialMediaSettings

register = Library()


JSON_LD_ESCAPE = {
    ord(">"): "\\u003E",
    ord("<"): "\\u003C",
    ord("&"): "\\u0026",
}


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
    image_alt = overrides.get("image_alt") or getattr(page, "metadata_image_alt", None)
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
        "settings": settings,
        "url": url,
        "type": overrides.get("type") or getattr(page, "metadata_type", "website"),
        "image": image,
        "image_alt": image_alt,
    }


def build_base_schema(request, metadata):
    site = metadata["site"]
    site_url = site.root_url
    settings = metadata["settings"]
    graph = []

    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "url": site_url,
        "name": site.site_name,
        "description": settings.description,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{site_url.rstrip('/')}{reverse('search')}?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }

    social_settings = SocialMediaSettings.for_site(site)
    same_as = [
        link.url
        for link in social_settings.social_links.all()
        if link.type != SocialMediaChoices.FEED
    ]
    if same_as:
        website["sameAs"] = same_as
    graph.append(website)
    return graph


def build_structured_data(page, request, metadata):
    schemas = build_base_schema(request, metadata)
    if page and hasattr(page, "get_schema_graph"):
        schemas.extend(page.get_schema_graph(request, metadata))
    if len(schemas) == 1:
        return schemas[0]
    return schemas


def build_json_ld(page, request, indent=None, **overrides):
    metadata = build_metadata(page, request, **overrides)
    json_ld = json.dumps(
        build_structured_data(page, request, metadata),
        cls=DjangoJSONEncoder,
        indent=indent,
    )
    return json_ld


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


@register.simple_tag(takes_context=True)
def render_json_ld(context, **overrides):
    request = context.get("request")
    page = context.get("page")
    json_ld = build_json_ld(page, request, **overrides).translate(JSON_LD_ESCAPE)
    return format_html(
        '<script type="application/ld+json">{}</script>',
        mark_safe(json_ld),
    )
