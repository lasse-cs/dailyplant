from django import template
from django.utils.safestring import mark_safe
from markdownify import markdownify as html_to_markdown


register = template.Library()


@register.filter(name="markdownify")
def markdownify(value):
    if hasattr(value, "__html__"):
        value = value.__html__()
    return mark_safe(html_to_markdown(str(value or "")).strip())


@register.simple_tag(takes_context=True)
def markdownpageurl(context, page):
    url = page.get_full_url(request=context.get("request"))
    if not getattr(page, "supports_md_suffix", False):
        return url
    return url.rstrip("/") + ".md"
