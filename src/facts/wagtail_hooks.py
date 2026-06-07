from wagtail import hooks
from wagtail.admin.auth import user_has_any_page_permission
from wagtail.admin.site_summary import SummaryItem
from wagtail.snippets.models import register_snippet

from facts.models import FactPage
from facts.viewsets import fact_page_viewset, FactTagSnippetViewSet, FactCalendarViewSet


@hooks.register("register_admin_viewset")
def register_fact_page_viewset():
    return fact_page_viewset


register_snippet(FactTagSnippetViewSet)


@hooks.register("register_admin_viewset")
def register_fact_calendar_viewset():
    return FactCalendarViewSet()


class UpcomingFactsSummaryItem(SummaryItem):
    order = 100
    template_name = "non_patterns/facts/admin/upcoming_facts.html"

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["upcoming"] = (
            FactPage.objects.filter(_revisions__approved_go_live_at__isnull=False)
            .distinct()
            .count()
        )
        return context

    def is_shown(self):
        return user_has_any_page_permission(self.request.user)


@hooks.register("construct_homepage_summary_items")
def construct_homepage_summary_items(request, items):
    items.append(UpcomingFactsSummaryItem(request))
