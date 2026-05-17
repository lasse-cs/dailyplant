from django.template import Library

register = Library()


@register.inclusion_tag("patterns/components/menu/main_menu.html")
def main_menu(site):
    root_page = site.root_page
    menu_items = root_page.get_children().live().in_menu()
    return {
        "menu_items": menu_items,
    }
