from django import template

from core.breadcrumbs import Breadcrumb, build_breadcrumbs


register = template.Library()


@register.inclusion_tag(
    "patterns/components/breadcrumbs/breadcrumbs.html", takes_context=True
)
def render_breadcrumbs(context, breadcrumbs: list[Breadcrumb] | None = None):
    if breadcrumbs is None:
        breadcrumbs = build_breadcrumbs(
            request=context.get("request"),
            page=context.get("page"),
        )
    return {"breadcrumbs": breadcrumbs}
