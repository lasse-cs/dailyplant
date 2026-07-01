from django.middleware.csrf import get_token
from django.urls import path, reverse

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


class BlueskyPostListingView(BaseListingView):
    model = BlueskyPost
    page_title = "Bluesky Posts"
    header_icon = "comment"
    ordering = ["-created_at"]

    columns = [
        TitleColumn(
            "page.title", label="Title", get_url=lambda post: post.get_post_url()
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
    icon = "comment"
    menu_label = "Social Posts"
    add_to_admin_menu = True

    def get_urlpatterns(self):
        return [
            path("", BlueskyPostListingView.as_view(), name="index"),
            path("<int:pk>/retry/", BlueskyPostRetryView.as_view(), name="retry"),
        ]


bluesky_post_viewset = BlueskyPostViewset("bluesky-posts")
