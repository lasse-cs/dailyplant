import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def test_homepage(page, home_page_and_site):
    home_page, site = home_page_and_site
    page.goto(home_page.full_url)

    expect(page).to_have_title(f"{home_page.title} - {site.site_name}")
