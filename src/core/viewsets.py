from wagtail.snippets.views.snippets import SnippetViewSet

from core.models import Tag


class TagSnippetViewSet(SnippetViewSet):
    panels = ["name"]
    model = Tag
    icon = "tag"
    add_to_admin_menu = True
    menu_label = "Tags"
    menu_order = 200
    list_display = ["name", "slug"]
    search_fields = ("name",)
