import pytest
from pytest_django.asserts import assertTemplateUsed

from facts.factories import FactPageFactory


@pytest.mark.django_db
def test_fact_page_returns_details_for_explorer_htmx_target(client, root_page):
    fact = FactPageFactory(
        parent=root_page,
        title="First fact",
        content="<p>Details about the first fact.</p>",
    )

    response = client.get(
        fact.url,
        headers={
            "HX-Request": "true",
            "HX-Target": "explorer-details-content",
        },
    )

    assert response.status_code == 200
    assertTemplateUsed(
        response, "non_patterns/facts/partials/related_page_details.html"
    )
