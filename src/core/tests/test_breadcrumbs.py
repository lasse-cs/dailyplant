import json

import pytest

from django.template.loader import render_to_string

from core.breadcrumbs import Breadcrumb, build_breadcrumbs
from core.templatetags.breadcrumb_tags import render_breadcrumbs
from core.templatetags.metadata_tags import build_json_ld
from core.testapp.factories import BreadcrumbPageFactory


def make_home_page(site, root_page):
    home_page = BreadcrumbPageFactory(parent=root_page, title="Home")
    site.root_page = home_page
    site.save()
    return home_page


@pytest.mark.django_db
def test_home_page_has_no_breadcrumbs(rf, site, root_page):
    home_page = make_home_page(site, root_page)
    request = rf.get(home_page.url)

    breadcrumbs = build_breadcrumbs(request, home_page)
    data = json.loads(build_json_ld(home_page, request))

    assert breadcrumbs == []
    assert data["@type"] == "WebSite"


@pytest.mark.django_db
def test_page_breadcrumbs_follow_wagtail_tree(rf, site, root_page):
    home_page = make_home_page(site, root_page)
    section = BreadcrumbPageFactory(parent=home_page, title="Guides")
    page = BreadcrumbPageFactory(parent=section, title="Growing herbs")
    request = rf.get(page.url)

    breadcrumbs = build_breadcrumbs(request, page)
    html = render_to_string(
        "patterns/components/breadcrumbs/breadcrumbs.html",
        {"breadcrumbs": breadcrumbs},
    )

    assert [item.name for item in breadcrumbs] == [
        "Home",
        "Guides",
        "Growing herbs",
    ]
    assert '<nav class="breadcrumbs" aria-label="Breadcrumb">' in html
    assert '<span aria-current="page">Growing herbs</span>' in html
    assert f'<a href="{section.full_url}"' in html


@pytest.mark.django_db
def test_breadcrumb_json_ld_matches_page_trail(rf, site, root_page):
    home_page = make_home_page(site, root_page)
    section = BreadcrumbPageFactory(parent=home_page, title="Guides")
    page = BreadcrumbPageFactory(parent=section, title="Growing herbs")
    request = rf.get(page.url)

    data = json.loads(build_json_ld(page, request))
    breadcrumb_schema = data[-1]

    assert breadcrumb_schema["@type"] == "BreadcrumbList"
    assert breadcrumb_schema["itemListElement"] == [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": site.root_url,
        },
        {
            "@type": "ListItem",
            "position": 2,
            "name": "Guides",
            "item": section.full_url,
        },
        {
            "@type": "ListItem",
            "position": 3,
            "name": "Growing herbs",
            "item": page.full_url,
        },
    ]


@pytest.mark.django_db
def test_page_can_add_an_extra_breadcrumb(rf, site, root_page):
    home_page = make_home_page(site, root_page)
    page = BreadcrumbPageFactory(parent=home_page, title="Archive")
    request = rf.get(f"{page.url}filtered/")
    request.extra_breadcrumb = Breadcrumb(
        name="Filtered", url=request.build_absolute_uri()
    )

    breadcrumbs = build_breadcrumbs(request, page)

    assert [item.name for item in breadcrumbs] == ["Home", "Archive", "Filtered"]
    assert breadcrumbs[-1] is request.extra_breadcrumb


@pytest.mark.django_db
def test_breadcrumbs_are_cached_for_the_request(rf, site, root_page):
    home_page = make_home_page(site, root_page)
    page = BreadcrumbPageFactory(parent=home_page, title="Guides")
    request = rf.get(page.url)

    first_result = build_breadcrumbs(request, page)
    second_result = build_breadcrumbs(request, page)

    assert second_result is first_result


@pytest.mark.parametrize(
    "breadcrumbs",
    [[], [Breadcrumb(name="Search", url="https://example.com/search/")]],
)
def test_breadcrumb_tag_uses_explicit_override(breadcrumbs):
    result = render_breadcrumbs({}, breadcrumbs)

    assert result["breadcrumbs"] is breadcrumbs


@pytest.mark.django_db
def test_json_ld_accepts_a_breadcrumb_override(rf, site, root_page):
    make_home_page(site, root_page)
    request = rf.get("/search/")
    breadcrumbs = [
        Breadcrumb(name="Home", url=site.root_url),
        Breadcrumb(name="Search", url=request.build_absolute_uri()),
    ]

    data = json.loads(build_json_ld(None, request, breadcrumbs=breadcrumbs))
    breadcrumb_schema = data[-1]

    assert breadcrumb_schema["@type"] == "BreadcrumbList"
    assert [item["name"] for item in breadcrumb_schema["itemListElement"]] == [
        "Home",
        "Search",
    ]


@pytest.mark.django_db
def test_empty_json_ld_breadcrumb_override_suppresses_schema(rf, site, root_page):
    make_home_page(site, root_page)
    request = rf.get("/search/")

    data = json.loads(build_json_ld(None, request, breadcrumbs=[]))

    assert data["@type"] == "WebSite"
