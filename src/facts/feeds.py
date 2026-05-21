from datetime import datetime, time

from django.contrib.syndication.views import Feed
from django.http import Http404
from django.utils.html import strip_tags
from django.utils import timezone
from django.utils.feedgenerator import Atom1Feed

from wagtail.models import Site
from wagtail.rich_text import expand_db_html

from facts.models import FactIndexPage, FactPage


class FactsRssFeed(Feed):
    def get_object(self, request):
        site = Site.find_for_request(request)
        if not site:
            raise Http404(("No site found"))
        try:
            return FactIndexPage.objects.live().in_site(site).get()
        except FactIndexPage.DoesNotExist:
            raise Http404("No fact archive found for this site.")

    def site_name(self, object):
        site = object.get_site()
        return site.site_name if site else ""

    def title(self, object):
        return object.title

    def description(self, object):
        return object.search_description

    def link(self, object):
        return object.full_url

    def items(self, object):
        return (
            FactPage.objects.live()
            .child_of(object)
            .filter(date__lte=timezone.localdate())
            .order_by("-date")
        )

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return item.full_url

    def item_description(self, item):
        return strip_tags(expand_db_html(item.content))

    def item_pubdate(self, item):
        return timezone.make_aware(datetime.combine(item.date, time.min))

    def item_updateddate(self, item):
        return self.item_pubdate(item)


class FactsAtomFeed(FactsRssFeed):
    feed_type = Atom1Feed

    def subtitle(self, object=None):
        return self.description(object)
