from django.forms import BooleanField
from django.shortcuts import redirect
from wagtail import hooks
from wagtail.admin import messages

from images.models import ImagePage
from images.relationships import ImageUsageRelationshipProvider


@hooks.register("register_relationship_provider")
def register_image_usage_relationship_provider():
    return ImageUsageRelationshipProvider()


@hooks.register("before_copy_page")
def prevent_image_page_copy(request, page):
    if page.specific_class is ImagePage:
        messages.error(
            request,
            "Image pages cannot be copied. Create a new page and select a different image.",
        )
        return redirect("wagtailadmin_explore", page.get_parent().pk)

    # Wagtail does not call this hook for descendants in a recursive copy.
    copy_subpages = BooleanField(required=False).clean(
        request.POST.get("copy_subpages")
    )
    if copy_subpages and ImagePage.objects.descendant_of(page).exists():
        messages.error(
            request,
            "This branch contains image pages and cannot be copied with its subpages.",
        )
        return redirect("wagtailadmin_explore", page.get_parent().pk)
