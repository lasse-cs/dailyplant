import pytest

from core.blocks import HeadingLevel
from core.models import TocItem
from core.testapp.factories import TocPageFactory


@pytest.mark.django_db
def test_page_mixin_builds_table_of_contents():
    page = TocPageFactory.build(
        body__0__group__introduction__text="Introduction",
        body__0__group__items__0__text="First item",
        body__0__group__items__0__level=HeadingLevel.H3,
        body__0__group__items__1__text="Second item",
        body__0__group__items__1__level=HeadingLevel.H3,
        body__0__group__body__0__heading__text="Conclusion",
        body__1__paragraph="Ignored",
    )

    assert page.get_table_of_contents() == [
        TocItem(
            "Introduction",
            "introduction",
            2,
            children=[
                TocItem("First item", "first-item", 3),
                TocItem("Second item", "second-item", 3),
            ],
        ),
        TocItem("Conclusion", "conclusion", 2),
    ]
