import calendar
import datetime

from django.http import Http404
from django.urls import path, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView

from django_filters.filters import DateFromToRangeFilter

from wagtail.admin.filters import DateRangePickerWidget
from wagtail.admin.views.pages.create import CreateView
from wagtail.admin.views.generic import WagtailAdminTemplateMixin
from wagtail.admin.ui.tables import Column
from wagtail.admin.viewsets.base import ViewSet
from wagtail.admin.viewsets.pages import PageViewSet
from facts.models import FactIndexPage, FactPage


class FactPageFilterSet(PageViewSet.filterset_class):
    date = DateFromToRangeFilter(
        label="Date",
        widget=DateRangePickerWidget,
    )

    class Meta:
        model = FactPage
        fields = []


def replace_type_with_date():
    cols = PageViewSet.columns[:]
    date_column = Column("date", label="Date", sort_key="date")
    type_column_index = next(
        (i for i, col in enumerate(cols) if col.name == "type"), None
    )
    if type_column_index is not None:
        cols[type_column_index] = date_column
    else:
        cols.append(date_column)
    return cols


class FactPageViewSet(PageViewSet):
    filterset_class = FactPageFilterSet
    model = FactPage
    parent_models = [FactIndexPage]
    ordering = "-date"
    columns = replace_type_with_date()


fact_page_viewset = FactPageViewSet()


class FactCalendarIndexView(WagtailAdminTemplateMixin, TemplateView):
    page_title = "Fact Calendar"
    template_name = "non_patterns/facts/admin/calendar/index.html"
    header_icon = "calendar-alt"

    breadcrumbs_items = [
        *WagtailAdminTemplateMixin.breadcrumbs_items,
        {"url": reverse_lazy("fact_calendar:index"), "label": "Fact Calendar"},
    ]

    def _get_date(self, year, month):
        if not year or not month:
            return timezone.now().date()

        try:
            return datetime.date(year, month, 1)
        except (ValueError, TypeError) as exc:
            raise Http404("Invalid Year and Month combination") from exc

    def _get_dates_with_facts(self, month_dates):
        first_date = month_dates[0][0]
        last_date = month_dates[-1][-1]
        facts = (
            FactPage.objects.filter(date__gte=first_date)
            .filter(date__lte=last_date)
            .all()
        )
        facts_by_date = {fact.date: fact for fact in facts}

        return [[(day, facts_by_date.get(day)) for day in week] for week in month_dates]

    def _can_add_fact(self):
        parent_page = FactIndexPage.objects.first()
        if not parent_page:
            return False
        return parent_page.permissions_for_user(self.request.user).can_add_subpage()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        date = self._get_date(self.kwargs.get("year"), self.kwargs.get("month"))
        month_dates = calendar.Calendar().monthdatescalendar(date.year, date.month)

        context["dates_with_facts"] = self._get_dates_with_facts(month_dates)
        context["current_date"] = date
        context["next_date"] = month_dates[-1][-1] + datetime.timedelta(days=1)
        context["previous_date"] = month_dates[0][0] - datetime.timedelta(days=1)
        context["can_add_fact"] = self._can_add_fact()

        return context


class FactPageCreateView(CreateView):
    def dispatch(self, request, year, month, day):
        try:
            self.prefilled_date = datetime.date(year, month, day)
        except ValueError as exc:
            raise Http404("Invalid date") from exc

        parent_page = FactIndexPage.objects.first()
        if not parent_page:
            raise Http404("Fact index page not found")

        return super().dispatch(
            request,
            FactPage._meta.app_label,
            FactPage._meta.model_name,
            parent_page.id,
        )

    def get(self, request):
        self.page.date = self.prefilled_date
        return super().get(request)


class FactCalendarViewSet(ViewSet):
    add_to_admin_menu = True
    menu_label = "Calendar"
    icon = "calendar-alt"
    name = "fact_calendar"
    menu_order = 201

    def get_urlpatterns(self):
        return [
            path("", FactCalendarIndexView.as_view(), name="index"),
            path(
                "add/<int:year>/<int:month>/<int:day>/",
                FactPageCreateView.as_view(),
                name="add",
            ),
            path(
                "<int:year>/<int:month>/",
                FactCalendarIndexView.as_view(),
                name="index_by_month",
            ),
        ]
