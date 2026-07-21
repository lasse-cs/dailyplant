from django.contrib.syndication.views import Feed
from django.http import Http404
from django.utils.feedgenerator import Atom1Feed

from wagtail.models import Page, Site, get_page_models

from core.models import FeedPageMixin, MetadataSettings


class RSSFeed(Feed):
    def get_object(self, request):
        site = Site.find_for_request(request)
        if not site:
            raise Http404("No site found")
        return site

    def title(self, site):
        return site.site_name

    def description(self, site):
        return MetadataSettings.for_site(site).description

    def link(self, site):
        return site.root_url

    def items(self, site):
        page_types = [
            model for model in get_page_models() if issubclass(model, FeedPageMixin)
        ]
        if not page_types:
            return []
        return (
            Page.objects.live()
            .in_site(site)
            .type(*page_types)
            .filter(first_published_at__isnull=False)
            .order_by("-first_published_at", "-pk")
            .specific()[:20]
        )

    def item_title(self, item):
        return item.feed_title

    def item_link(self, item):
        return item.full_url

    def item_description(self, item):
        return item.feed_description

    def item_pubdate(self, item):
        return item.feed_published_at

    def item_updateddate(self, item):
        return item.feed_updated_at


class AtomFeed(RSSFeed):
    feed_type = Atom1Feed

    def subtitle(self, site=None):
        return self.description(site)
