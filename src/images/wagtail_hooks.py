from wagtail import hooks

from images.relationships import ImageUsageRelationshipProvider


@hooks.register("register_relationship_provider")
def register_image_usage_relationship_provider():
    return ImageUsageRelationshipProvider()
