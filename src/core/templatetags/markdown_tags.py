from django import template
from django.utils.safestring import mark_safe
from markdownify import markdownify as html_to_markdown


register = template.Library()


@register.filter(name="markdownify")
def markdownify(value):
    if hasattr(value, "__html__"):
        value = value.__html__()
    return mark_safe(html_to_markdown(str(value or "")).strip())
