from wagtail_factories import PageFactory

from home.models import HomePage


class HomePageFactory(PageFactory):
    class Meta:
        model = HomePage
