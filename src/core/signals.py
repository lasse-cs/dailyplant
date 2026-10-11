from django.core.cache import cache
from django.db.models.signals import post_delete
from wagtail.models import Page
from wagtail.signals import page_published, page_unpublished, post_page_move

from core.models import EXPLORER_DATA_CACHE_KEY


def invalidate_explorer_data(sender, **kwargs):
    cache.delete(EXPLORER_DATA_CACHE_KEY)


page_published.connect(invalidate_explorer_data)
page_unpublished.connect(invalidate_explorer_data)
post_page_move.connect(invalidate_explorer_data)
post_delete.connect(invalidate_explorer_data, sender=Page)
