from django.templatetags.static import static

from wagtail import hooks
from wagtail.admin.rich_text.editors.draftail.features import ControlFeature
from wagtail.contrib.settings.models import register_setting
from wagtail.snippets.models import register_snippet

from wagtail_umami_analytics.models import UmamiAnalyticsSetting
from wagtail_umami_analytics.views import (
    register_umami_page_analytics_urls,
    UmamiAnalyticsViewSet,
)

from core.viewsets import TagSnippetViewSet


register_setting(UmamiAnalyticsSetting)
register_snippet(TagSnippetViewSet)


@hooks.register("register_admin_viewset")
def umami_dashboard():
    return UmamiAnalyticsViewSet()


hooks.register("register_admin_urls", register_umami_page_analytics_urls)


@hooks.register("register_rich_text_features")
def register_characters_counter(features):
    feature_name = "characters"

    features.register_editor_plugin(
        "draftail",
        feature_name,
        ControlFeature(
            {
                "type": feature_name,
            },
            js=[static("core/js/character_counter.js")],
        ),
    )
