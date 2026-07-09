from django import template
from django.utils.safestring import mark_safe
from markdownify import markdownify as html_to_markdown

from core.models import markdown_page_url
from core.templatetags.metadata_tags import build_json_ld


register = template.Library()


@register.filter(name="markdownify")
def markdownify(value):
    if hasattr(value, "__html__"):
        value = value.__html__()
    return mark_safe(html_to_markdown(str(value or "")).strip())


@register.simple_tag(takes_context=True)
def markdownpageurl(context, page):
    return markdown_page_url(page, request=context.get("request"))


@register.simple_tag(takes_context=True)
def render_markdown_json_ld(context, **overrides):
    request = context.get("request")
    page = context.get("page")
    json_ld = build_json_ld(page, request, indent=2, **overrides)
    return mark_safe(f"```json\n{json_ld}\n```")
