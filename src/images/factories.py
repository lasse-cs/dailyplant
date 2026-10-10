import factory
from wagtail_factories import ImageFactory, PageFactory

from core.factories import RelatedPagesFactoryMixin, TaggedPageFactoryMixin
from images.models import ImagePage, ImagesListingPage


class ImagesListingPageFactory(PageFactory):
    title = "Images"

    class Meta:
        model = ImagesListingPage


class ImagePageFactory(RelatedPagesFactoryMixin, TaggedPageFactoryMixin):
    title = factory.Sequence(lambda i: f"Image {i}")
    image = factory.SubFactory(ImageFactory)
    description = "<p>A closer look at the natural world.</p>"

    class Meta:
        model = ImagePage
        skip_postgeneration_save = True
