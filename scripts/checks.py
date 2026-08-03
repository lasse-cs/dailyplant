#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "httpx[http2]",
#   "rich>=15.0.0",
# ]
# [tool.uv]
# exclude-newer = "2026-07-30T00:00:00Z"
# ///

import argparse

import httpx
from rich.console import Console

console = Console()
error_console = Console(stderr=True)


class CheckError(Exception):
    pass


def check_redirect(client, base_url):
    """Check that HTTP redirects permanently to the canonical HTTPS URL."""
    http_url = base_url.copy_with(scheme="http")
    response = client.get(http_url)

    if response.status_code != 301:
        raise CheckError(
            f"{http_url}: expected HTTP 301, received {response.status_code}"
        )

    location = response.headers.get("Location")
    if location != str(base_url):
        raise CheckError(
            f"{http_url}: expected redirect to {base_url}, received {location!r}"
        )

    console.print(f"PASS {http_url} redirects to {base_url}", style="green")


def check_homepage(client, base_url):
    """Check that the homepage loads successfully as HTML."""
    response = client.get(base_url)

    if response.status_code != 200:
        raise CheckError(
            f"{base_url}: expected HTTP 200, received {response.status_code}"
        )

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("text/html"):
        raise CheckError(f"{base_url}: expected text/html, received {content_type!r}")

    console.print(f"PASS {base_url} returns HTML", style="green")


def check_link_headers(client, base_url):
    """Check that the homepage advertises its discovery resources."""
    response = client.get(base_url)
    links = response.headers.get_list("Link")
    expected_links = {
        "/llms.txt": 'rel="describedby"',
        "/sitemap.xml": 'rel="sitemap"',
        "/rss.xml": 'rel="alternate"',
        "/atom.xml": 'rel="alternate"',
    }
    missing_links = [
        path
        for path, relation in expected_links.items()
        if not any(f"<{path}>" in link and relation in link for link in links)
    ]

    if missing_links:
        raise CheckError(
            f"{base_url}: missing Link headers for {', '.join(missing_links)}"
        )

    console.print(f"PASS {base_url} advertises discovery links", style="green")


def check_endpoint(client, base_url, path, expected_content_type):
    """Check that an endpoint loads with its expected content type."""
    url = base_url.join(path)
    response = client.get(url)

    if response.status_code != 200:
        raise CheckError(f"{url}: expected HTTP 200, received {response.status_code}")

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith(expected_content_type):
        raise CheckError(
            f"{url}: expected {expected_content_type}, received {content_type!r}"
        )

    console.print(f"PASS {url} returns {expected_content_type}", style="green")


def check_robots(client, base_url):
    """Check that robots.txt loads as plain text."""
    check_endpoint(client, base_url, "robots.txt", "text/plain")


def check_sitemap(client, base_url):
    """Check that the XML sitemap loads successfully."""
    check_endpoint(client, base_url, "sitemap.xml", "application/xml")


def check_llms(client, base_url):
    """Check that llms.txt loads as Markdown."""
    check_endpoint(client, base_url, "llms.txt", "text/markdown")


def main():
    parser = argparse.ArgumentParser(description="Check a website")
    parser.add_argument("url", help="HTTPS base URL to check")
    args = parser.parse_args()

    base_url = httpx.URL(args.url)
    if base_url.scheme != "https":
        parser.error("url must use HTTPS")
    base_url = base_url.copy_with(path="/", query=None, fragment=None)

    failures = []
    with httpx.Client(http2=True, follow_redirects=False, timeout=15) as client:
        for check in (
            check_redirect,
            check_homepage,
            check_link_headers,
            check_robots,
            check_sitemap,
            check_llms,
        ):
            try:
                check(client, base_url)
            except (CheckError, httpx.HTTPError) as error:
                failures.append(str(error))

    if failures:
        error_console.print(f"{len(failures)} site check(s) failed:", style="bold red")
        for failure in failures:
            error_console.print(f"FAIL {failure}", style="red")
        raise SystemExit(1)

    console.print("All site checks passed", style="bold green")


if __name__ == "__main__":
    main()
