from wagtail.signals import page_published


def add_post_to_bluesky_task(sender, **kwargs):
    pass


page_published.connect(add_post_to_bluesky_task)
