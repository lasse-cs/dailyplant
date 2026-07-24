from datetime import date

import pytest

from core.blocks import LLMsTxtListingPageChooserBlock
from facts.models import FactIndexPage, FactPage
from home.factories import HomePageFactory


@pytest.mark.django_db
def test_fact_index_prefetches_tag_assignments(root_page):
    home_page = HomePageFactory(parent=root_page)
    fact_index = home_page.add_child(
        instance=FactIndexPage(title="Facts", introduction="")
    )

    prefetch = fact_index.get_facts()._prefetch_related_lookups[0]
    assert prefetch.prefetch_to == "tag_assignments"


@pytest.mark.django_db
def test_fact_index_provides_llms_txt_listing(root_page):
    home_page = HomePageFactory(parent=root_page)
    fact_index = home_page.add_child(
        instance=FactIndexPage(title="Facts", introduction="")
    )
    fact = fact_index.add_child(
        instance=FactPage(
            title="Tomato",
            date=date(2026, 1, 1),
            content="<p>Tomatoes are berries.</p>",
            references=[],
        )
    )

    assert FactIndexPage in LLMsTxtListingPageChooserBlock().target_models
    assert list(fact_index.get_llms_txt_pages()) == [fact]
