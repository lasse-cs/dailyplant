from datetime import timedelta

import pytest
from django.utils import timezone
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


def test_user_can_browse_latest_and_older_facts(
    page, home_page_and_site, fact_index_page
):
    home_page, _ = home_page_and_site
    today = timezone.localdate()
    older_fact = FactPageFactory(
        parent=fact_index_page,
        title="An older published fact",
        date=today - timedelta(days=2),
    )
    older_fact.save_revision().publish()
    latest_fact = FactPageFactory(
        parent=fact_index_page,
        title="The latest published fact",
        date=today - timedelta(days=1),
    )
    latest_fact.save_revision().publish()
    future_fact = FactPageFactory(
        parent=fact_index_page,
        title="An unpublished future fact",
        date=today + timedelta(days=1),
        live=False,
    )

    page.goto(home_page.full_url)

    latest_fact_link = page.get_by_role("link", name=latest_fact.title, exact=True)
    expect(latest_fact_link).to_be_visible()
    expect(
        page.get_by_role("heading", name=future_fact.title, exact=True)
    ).to_have_count(0)

    latest_fact_link.click()
    expect(page).to_have_url(latest_fact.full_url)
    expect(
        page.get_by_role("heading", name=latest_fact.title, exact=True)
    ).to_be_visible()

    page.get_by_role("link", name="Older Fact").click()
    expect(page).to_have_url(older_fact.full_url)
    expect(
        page.get_by_role("heading", name=older_fact.title, exact=True)
    ).to_be_visible()

    page.get_by_role("link", name="Newer Fact").click()
    expect(page).to_have_url(latest_fact.full_url)
    expect(
        page.get_by_role("heading", name=latest_fact.title, exact=True)
    ).to_be_visible()
