import pytest

from facts.models import FactIndexPage
from home.factories import HomePageFactory


@pytest.mark.django_db
def test_fact_index_prefetches_tag_assignments(root_page):
    home_page = HomePageFactory(parent=root_page)
    fact_index = home_page.add_child(
        instance=FactIndexPage(title="Facts", introduction="")
    )

    prefetch = fact_index.get_facts()._prefetch_related_lookups[0]
    assert prefetch.prefetch_to == "tag_assignments"
