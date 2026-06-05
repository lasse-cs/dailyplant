from wagtail.signals import page_published
from facts.models import FactPage
from social.models import BlueskyPost


def auto_bluesky_posting(sender, **kwargs):
    instance = kwargs["instance"]
    if not issubclass(instance.specific_class, FactPage):
        return
    if not instance.live:
        return
    BlueskyPost.objects.get_or_create(page=instance)


page_published.connect(auto_bluesky_posting)
