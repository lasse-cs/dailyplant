import pytest
from playwright.sync_api import expect

from core.factories import SocialMediaLinkFactory, SocialMediaSettingsFactory
from facts.factories import FactPageFactory

pytestmark = pytest.mark.e2e


def test_homepage(page, home_page_and_site, fact_index_page):
    home_page, site = home_page_and_site
    fact = FactPageFactory(parent=fact_index_page)
    fact.save_revision().publish()
    social_settings = SocialMediaSettingsFactory(site=site)
    social_link = SocialMediaLinkFactory(
        social_settings=social_settings,
        display="Follow us",
        url="https://example.com/dailyplant",
    )

    page.goto(home_page.full_url)

    expect(page).to_have_title(f"{home_page.title} - {site.site_name}")

    # There should be a brand link - this should link back to the home page
    brand_link = page.get_by_role("link", name=site.site_name)
    expect(brand_link).to_have_attribute("href", site.root_url)

    # The fact index page should be displayed in the top navigation
    navigation = page.get_by_role("navigation", name="Main Navigation")
    fact_index_nav_link = navigation.get_by_role("link", name=fact_index_page.title)
    expect(fact_index_nav_link).to_have_attribute("href", fact_index_page.url)

    fact_link = page.get_by_role("link", name=fact.title)
    expect(fact_link).to_be_visible()
    expect(fact_link).to_have_attribute("href", fact.url)

    social_link_element = page.get_by_role("link", name=social_link.display)
    expect(social_link_element).to_be_visible()
    expect(social_link_element).to_have_attribute("href", social_link.url)
    expect(social_link_element).to_have_attribute("target", "_blank")
    expect(social_link_element).to_have_attribute("rel", "noopener noreferrer")
