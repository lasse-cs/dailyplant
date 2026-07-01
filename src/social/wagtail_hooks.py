from wagtail import hooks

from social.views import bluesky_post_viewset


@hooks.register("register_icons")
def register_icons(icons):
    return icons + ["svgs/admin/bluesky.svg"]


@hooks.register("register_admin_viewset")
def register_bluesky_post_viewset():
    return bluesky_post_viewset
