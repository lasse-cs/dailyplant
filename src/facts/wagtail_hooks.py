from wagtail import hooks

from facts.viewsets import fact_page_viewset


@hooks.register("register_admin_viewset")
def register_fact_page_viewset():
    return fact_page_viewset
