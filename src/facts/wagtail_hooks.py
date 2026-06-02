from wagtail import hooks
from wagtail.snippets.models import register_snippet

from facts.viewsets import fact_page_viewset, FactTagSnippetViewSet


@hooks.register("register_admin_viewset")
def register_fact_page_viewset():
    return fact_page_viewset


register_snippet(FactTagSnippetViewSet)
