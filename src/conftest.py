import pytest

from wagtail.models import Site

from wagtail_factories import SiteFactory


@pytest.fixture
def site():
    # Ensure that all site objects are deleted.
    # Wagtail will initially create one, but we don't
    # want that one
    Site.objects.all().delete()
    site = SiteFactory(is_default_site=True)
    yield site


@pytest.fixture
def root_page(site):
    yield site.root_page
