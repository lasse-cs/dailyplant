from wagtail.signals import page_published

from social.bluesky import BLUESKY_FORMATTERS
from social.models import BlueskyPost


def auto_bluesky_posting(sender, **kwargs):
    page = kwargs["instance"]
    if not page.live or page.specific_class not in BLUESKY_FORMATTERS:
        return
    BlueskyPost.objects.get_or_create(page=page)


page_published.connect(auto_bluesky_posting)
