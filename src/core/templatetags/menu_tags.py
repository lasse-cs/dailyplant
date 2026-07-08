from django.template import Library

register = Library()


@register.inclusion_tag("patterns/components/menu/main_menu.html")
def main_menu(site):
    root_page = site.root_page
    menu_items = root_page.get_children().live().in_menu()
    return {
        "menu_items": menu_items,
    }


@register.inclusion_tag("non_patterns/core/main_menu.md")
def markdown_main_menu(site):
    return main_menu(site)
