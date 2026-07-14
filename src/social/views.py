from django.middleware.csrf import get_token
from django.urls import path, reverse

from django_filters import DateFromToRangeFilter, FilterSet

from wagtail.admin.filters import DateRangePickerWidget
from wagtail.admin.ui.tables import (
    ButtonsColumnMixin,
    DateColumn,
    StatusTagColumn,
    TitleColumn,
)
from wagtail.admin.views.generic.base import BaseListingView, BaseOperationView
from wagtail.admin.viewsets.base import ViewSet

from social.models import BlueskyPost, BlueskyPostStatus


class StatusWithActionsColumn(ButtonsColumnMixin, StatusTagColumn):
    cell_template_name = (
        "non_patterns/social/admin/tables/status_with_actions_tag_cell.html"
    )

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        if instance.status == BlueskyPostStatus.FAILED:
            context["retry_url"] = reverse("bluesky-posts:retry", args=(instance.pk,))
            context["csrf_token"] = get_token(context["request"])
        else:
            context["retry_url"] = None
        return context


class BlueskyPostRetryView(BaseOperationView):
    model = BlueskyPost

    def get_success_url(self):
        return reverse("bluesky-posts:index")

    def get_success_message(self):
        return f"Retrying bluesky post for '{self.object.page.title}'"

    def get_base_object_queryset(self):
        return BlueskyPost.objects.filter(status=BlueskyPostStatus.FAILED)

    def perform_operation(self):
        self.object.status = BlueskyPostStatus.PENDING
        self.object.save()


class BlueskyPostFilterClass(FilterSet):
    created_at = DateFromToRangeFilter(widget=DateRangePickerWidget)
    updated_at = DateFromToRangeFilter(widget=DateRangePickerWidget)

    class Meta:
        model = BlueskyPost
        fields = ["status"]


class BlueskyPostListingView(BaseListingView):
    model = BlueskyPost
    page_title = "Bluesky Posts"
    header_icon = "bluesky"
    ordering = ["-created_at"]
    index_url_name = "bluesky-posts:index"
    index_results_url_name = "bluesky-posts:index_results"
    filterset_class = BlueskyPostFilterClass

    columns = [
        TitleColumn(
            "page.title",
            label="Title",
            get_url=lambda post: post.get_post_url(),
            link_attrs={"target": "_blank", "rel": "noopener noreferrer"},
        ),
        DateColumn("created_at", label="Created"),
        DateColumn("updated_at", label="Updated"),
        StatusWithActionsColumn(
            "status",
            label="Status",
            primary=lambda post: post.status == BlueskyPostStatus.POSTED,
        ),
    ]


class BlueskyPostViewset(ViewSet):
    icon = "bluesky"
    menu_label = "Bluesky Posts"
    add_to_admin_menu = True

    def get_urlpatterns(self):
        return [
            path("", BlueskyPostListingView.as_view(), name="index"),
            path(
                "results/",
                BlueskyPostListingView.as_view(results_only=True),
                name="index_results",
            ),
            path("<int:pk>/retry/", BlueskyPostRetryView.as_view(), name="retry"),
        ]


bluesky_post_viewset = BlueskyPostViewset("bluesky-posts")
