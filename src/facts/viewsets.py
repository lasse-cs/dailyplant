from django_filters.filters import DateFromToRangeFilter

from wagtail.admin.filters import DateRangePickerWidget
from wagtail.admin.ui.tables import Column
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
