from django.templatetags.static import static

from wagtail import hooks
from wagtail.admin.rich_text.editors.draftail.features import ControlFeature
from wagtail.contrib.settings.models import register_setting

from wagtail_umami_analytics.models import UmamiAnalyticsSetting
from wagtail_umami_analytics.views import UmamiAnalyticsViewSet


register_setting(UmamiAnalyticsSetting)


@hooks.register("register_admin_viewset")
def umami_dashboard():
    return UmamiAnalyticsViewSet()


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
