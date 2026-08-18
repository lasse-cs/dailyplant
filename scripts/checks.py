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
import ssl
from datetime import UTC, datetime, timedelta
from functools import cache
from html.parser import HTMLParser

import httpx
from rich.console import Console

console = Console()
error_console = Console(stderr=True)

CERTIFICATE_MIN_VALIDITY = timedelta(days=14)


class CheckError(Exception):
    pass


@cache
def fetch(client: httpx.Client, url: httpx.URL) -> httpx.Response:
    """Fetch a URL, at most once per run."""
    return client.get(url)


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
    response = fetch(client, base_url)

    if response.status_code != 200:
        raise CheckError(
            f"{base_url}: expected HTTP 200, received {response.status_code}"
        )

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("text/html"):
        raise CheckError(f"{base_url}: expected text/html, received {content_type!r}")

    console.print(f"PASS {base_url} returns HTML", style="green")


def check_homepage_markdown(client, base_url):
    """Check that the homepage is available as Markdown."""
    response = client.get(base_url, headers={"Accept": "text/markdown"})

    if response.status_code != 200:
        raise CheckError(
            f"{base_url}: expected HTTP 200 for Markdown, "
            f"received {response.status_code}"
        )

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("text/markdown"):
        raise CheckError(
            f"{base_url}: expected text/markdown, received {content_type!r}"
        )

    if not response.text.strip():
        raise CheckError(f"{base_url}: received an empty Markdown response")

    console.print(f"PASS {base_url} returns Markdown if requested", style="green")


def check_certificate(client, base_url):
    """Check that the TLS certificate is not approaching expiry."""
    response = fetch(client, base_url)
    stream = response.extensions.get("network_stream")
    ssl_object = stream.get_extra_info("ssl_object") if stream else None

    if ssl_object is None:
        raise CheckError(f"{base_url}: could not inspect TLS certificate")

    certificate = ssl_object.getpeercert()
    expires_at = datetime.fromtimestamp(
        ssl.cert_time_to_seconds(certificate["notAfter"]),
        tz=UTC,
    )
    remaining = expires_at - datetime.now(UTC)

    if remaining < CERTIFICATE_MIN_VALIDITY:
        raise CheckError(
            f"{base_url}: certificate expires {expires_at:%Y-%m-%d} "
            f"({remaining.days} days remaining)"
        )

    console.print(
        f"PASS {base_url.host} certificate valid until "
        f"{expires_at:%Y-%m-%d} ({remaining.days} days remaining)",
        style="green",
    )


def check_not_found(client, base_url):
    """Check that a missing page returns HTTP 404."""
    url = base_url.join("page-should-not-be-found/")
    response = client.get(url)

    if response.status_code != 404:
        raise CheckError(f"{url}: expected HTTP 404, received {response.status_code}")

    console.print(f"PASS {url} returns HTTP 404", style="green")


def check_link_headers(client, base_url):
    """Check that the homepage advertises its discovery resources."""
    response = fetch(client, base_url)
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


class HeadHTMLParser(HTMLParser):
    def __init__(self, *, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.links = []
        self.meta = []
        self.in_head = False

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
        elif tag == "body":
            self.in_head = False
        elif tag == "link" and self.in_head:
            self.links.append(dict(attrs))
        elif tag == "meta" and self.in_head:
            self.meta.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False


def parse_head_links(html):
    parser = HeadHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.links


def parse_head_meta(html):
    parser = HeadHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.meta


def has_rel(link, expected_rel):
    return expected_rel.lower() in (link.get("rel") or "").lower().split()


def check_link_in_head(client, base_url):
    """Check that the homepage advertises its discovery resources in the <head>."""
    response = fetch(client, base_url)
    links = parse_head_links(response.text)

    expected_links = {
        "/llms.txt": "describedby",
        "/sitemap.xml": "sitemap",
        "/rss.xml": "alternate",
        "/atom.xml": "alternate",
    }
    missing_links = [
        href
        for href, rel in expected_links.items()
        if not any(link.get("href") == href and has_rel(link, rel) for link in links)
    ]

    if missing_links:
        raise CheckError(
            f"{base_url}: missing Link in <head> for {', '.join(missing_links)}"
        )

    console.print(
        f"PASS {base_url} advertises discovery links in <head>", style="green"
    )


def check_color_scheme(client, base_url):
    """Check that the homepage declares its supported colour scheme."""
    response = fetch(client, base_url)
    meta = parse_head_meta(response.text)
    color_scheme = next(
        (
            item.get("content", "")
            for item in meta
            if item.get("name", "").lower() == "color-scheme"
        ),
        None,
    )

    if color_scheme is None or color_scheme.strip().lower() != "only light":
        raise CheckError(
            f"{base_url}: expected color-scheme 'only light', received {color_scheme!r}"
        )

    console.print(f"PASS {base_url} declares color-scheme 'only light'", style="green")


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


def check_static_file(client, base_url):
    """Check that static fiels can be loaded - by loading a css file."""
    response = fetch(client, base_url)
    links = parse_head_links(response.text)
    href = next(
        (
            link["href"]
            for link in links
            if link.get("href") and has_rel(link, "stylesheet")
        ),
        None,
    )

    if href is None:
        raise CheckError("Found no CSS File to fetch")

    check_endpoint(client, base_url, href, "text/css")


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
            check_homepage_markdown,
            check_certificate,
            check_not_found,
            check_link_headers,
            check_link_in_head,
            check_color_scheme,
            check_static_file,
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
