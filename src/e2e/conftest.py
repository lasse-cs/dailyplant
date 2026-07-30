import os

import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from wagtail.coreutils import get_supported_content_language_variant
from wagtail.models import Locale, Page, Site
from wagtail_factories.factories import SiteFactory

from home.factories import HomePageFactory


@pytest.fixture(scope="session", autouse=True)
def set_env():
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "1"


@pytest.fixture
def live_site_server(live_server):
    # Ensure that all site and page objects are deleted.
    # Wagtail will initially create ones in migrations
    # but we want to start with a clean slate
    # for consistency
    Site.objects.all().delete()
    Page.objects.all().delete()

    # We also need a Locale
    language_code = get_supported_content_language_variant(settings.LANGUAGE_CODE)
    Locale.objects.get_or_create(language_code=language_code)

    page_content_type, _ = ContentType.objects.get_or_create(
        model="page", app_label="wagtailcore"
    )

    # Create root page
    Page.objects.create(
        title="Root",
        slug="root",
        content_type=page_content_type,
        path="0001",
        depth=1,
        numchild=0,
        url_path="/",
    )
    yield live_server


@pytest.fixture
def home_page_and_site(live_site_server):
    root = Page.get_first_root_node()
    home_page = HomePageFactory(
        title="Home",
        parent=root,
    )
    home_page.save_revision().publish()

    site = SiteFactory(
        hostname=live_site_server.thread.host,
        port=live_site_server.thread.port,
        is_default_site=True,
        site_name="dailyplant",
        root_page=home_page,
    )
    yield home_page, site
