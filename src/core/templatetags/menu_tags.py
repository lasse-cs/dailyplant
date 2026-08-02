from django.template import Library

register = Library()


@register.inclusion_tag("patterns/components/menu/main_menu.html", takes_context=True)
def main_menu(context, site):
    root_page = site.root_page
    menu_items = root_page.get_children().live().in_menu()
    return {
        "menu_items": menu_items,
        "request": context.get("request"),
    }


@register.inclusion_tag("non_patterns/core/main_menu.md", takes_context=True)
def markdown_main_menu(context, site):
    items = main_menu(context, site)
    # Might want to think about this... need specific information to
    # check if the page supports markdown or not...
    items["menu_items"] = items["menu_items"].specific()
    return items
