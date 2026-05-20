from django.apps import apps
from django.conf import settings
from django.urls import include, path, re_path

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.images.views.serve import ServeView

from sesame.views import LoginView

from dailyplant.views import error_500_test
from users.views import EmailLoginView


urlpatterns = [
    path("sesame/login/", LoginView.as_view(), name="sesame-login"),
    path("admin/login/", EmailLoginView.as_view(), name="wagtailadmin_login"),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("error-500-test/", error_500_test, name="server_error"),
    path("sitemap.xml", sitemap),
    re_path(
        r"^images/([^/]*)/(\d*)/([^/]*)/[^/]*$",
        ServeView.as_view(),
        name="wagtailimages_serve",
    ),
]


handler404 = "dailyplant.views.page_not_found"
handler500 = "dailyplant.views.server_error"


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Browser Reload
    if apps.is_installed("django_browser_reload"):
        urlpatterns += [
            path("__reload__/", include("django_browser_reload.urls")),
        ]

    # Django Debug Toolbar
    if apps.is_installed("debug_toolbar"):
        from debug_toolbar.toolbar import debug_toolbar_urls

        urlpatterns += debug_toolbar_urls()

    if apps.is_installed("pattern_library"):
        urlpatterns += [
            path("patterns/", include("pattern_library.urls")),
        ]

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
]
