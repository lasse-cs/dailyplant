from django import template
from django.utils.functional import Promise
from django.utils.safestring import mark_safe
from wagtail.admin.rich_text.converters.markdown_db import MarkdownConverter
from wagtail.rich_text import RichText

from core.models import markdown_page_url
from core.templatetags.metadata_tags import build_json_ld

register = template.Library()


@register.filter
def richtext_markdown(value):
    """Render Wagtail database rich text as Markdown with public URLs."""
    if value is None:
        return ""
    if isinstance(value, RichText):
        value = value.source
    elif isinstance(value, Promise):
        value = str(value)
    return mark_safe(
        MarkdownConverter().from_database_format(value, resolved=True).strip()
    )


@register.simple_tag(takes_context=True)
def markdownpageurl(context, page):
    return markdown_page_url(page, request=context.get("request"))


@register.simple_tag(takes_context=True)
def render_markdown_json_ld(context, **overrides):
    request = context.get("request")
    page = context.get("page")
    json_ld = build_json_ld(page, request, indent=2, **overrides)
    return mark_safe(f"```json\n{json_ld}\n```")
