from django.contrib.auth.decorators import user_passes_test

from django.views.defaults import page_not_found as django_page_not_found
from django.views.defaults import server_error as django_server_error


def page_not_found(request, exception, template_name="patterns/pages/error/404.html"):
    return django_page_not_found(request, exception, template_name)


def server_error(request, template_name="patterns/pages/error/500.html"):
    return django_server_error(request, template_name)


@user_passes_test(lambda u: u.is_superuser)
def error_500_test(request):
    raise Exception("This is a test exception")
