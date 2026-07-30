from wagtail_factories import PageFactory

from facts.models import FactIndexPage


class FactIndexPageFactory(PageFactory):
    class Meta:
        model = FactIndexPage
