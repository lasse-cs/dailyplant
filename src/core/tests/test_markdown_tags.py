import pytest
from django.utils.functional import lazy
from wagtail.rich_text import RichText
from wagtail_factories import DocumentFactory

from core.factories import ContentPageFactory
from core.templatetags.markdown_tags import richtext_markdown


def test_richtext_markdown_string():
    value = "<p><b>Bold</b> and <i>italic</i></p>"
    assert richtext_markdown(value) == "**Bold** and *italic*"


def test_richtext_markdown_richtext():
    value = RichText("<p><b>Bold</b> and <i>italic</i></p>")
    assert richtext_markdown(value) == "**Bold** and *italic*"


def test_richtext_markdown_lazy_string():
    value = lazy(lambda: "<p><b>Bold</b> and <i>italic</i></p>", str)()
    assert richtext_markdown(value) == "**Bold** and *italic*"


def test_richtext_markdown_none():
    assert richtext_markdown(None) == ""


def test_richtext_markdown_empty_string():
    assert richtext_markdown("") == ""


def test_richtext_markdown_empty_richtext():
    assert richtext_markdown(RichText("")) == ""


@pytest.mark.django_db
def test_richtext_markdown_resolves_wagtail_links(root_page):
    page = ContentPageFactory(parent=root_page)
    document = DocumentFactory()
    source = (
        f'<p><a linktype="page" id="{page.pk}">Page</a> and '
        f'<a linktype="document" id="{document.pk}">Document</a></p>'
    )

    assert richtext_markdown(RichText(source)) == (
        f"[Page]({page.url}) and [Document]({document.url})"
    )


@pytest.mark.django_db
def test_richtext_markdown_preserves_broken_link_text():
    source = (
        '<p><a linktype="page" id="999999">Missing page</a> and '
        '<a linktype="document" id="999999">Missing document</a></p>'
    )

    assert richtext_markdown(source) == "Missing page and Missing document"
