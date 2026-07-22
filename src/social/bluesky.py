from dataclasses import dataclass
from typing import Any

from articles.models import ArticlePage
from core.models import MetadataSettings
from facts.models import FactPage


@dataclass(frozen=True)
class BlueskyPostContent:
    text: Any
    url: str
    title: str
    description: str
    thumbnail_image: Any | None


def format_page(page: ArticlePage | FactPage) -> BlueskyPostContent:
    # Lazily import the Bluesky client dependency.
    from atproto_client.utils.text_builder import TextBuilder

    text = TextBuilder()
    text.text(page.title)
    text.text("\n\n")
    full_url = page.get_full_url()
    text.link(full_url, full_url)
    text.text("\n\n")
    for index, tag in enumerate(page.get_tags()):
        hashtag = "#" + "".join(word.capitalize() for word in tag.slug.split("-"))
        if index:
            text.text(" ")
        text.tag(hashtag, hashtag)

    thumbnail_image = page.metadata_image
    if not thumbnail_image and (site := page.get_site()):
        thumbnail_image = MetadataSettings.for_site(site).image

    return BlueskyPostContent(
        text=text,
        url=full_url,
        title=page.title,
        description=page.metadata_description,
        thumbnail_image=thumbnail_image,
    )


BLUESKY_FORMATTERS = {
    ArticlePage: format_page,
    FactPage: format_page,
}
