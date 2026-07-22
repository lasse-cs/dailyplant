from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import FormView

from wagtail.models import Site

from sesame.utils import get_query_string

from core.breadcrumbs import Breadcrumb
from users.forms import EmailLoginForm


class EmailLoginView(FormView):
    template_name = "patterns/pages/users/email_login.html"
    form_class = EmailLoginForm

    def get_breadcrumbs(self):
        site = Site.find_for_request(self.request)
        return [
            Breadcrumb(name=site.root_page.title, url=site.root_url),
            Breadcrumb(
                name="Log In",
                url=self.request.build_absolute_uri(reverse("wagtailadmin_login")),
            ),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = self.get_breadcrumbs()
        return context

    def get_user(self, email):
        """Find the user with this email address."""
        User = get_user_model()
        return User.objects.filter(email=email).first()

    def create_link(self, user):
        """Create a login link for this user."""
        link = reverse("sesame-login")
        link = self.request.build_absolute_uri(link)
        link += get_query_string(user)
        return link

    def send_email(self, user, link, sitename):
        """Send an email with this login link to this user."""
        subject = f"Log in to '{sitename}'"
        message = render_to_string(
            "non_patterns/users/login_email.txt", {"link": link, "sitename": sitename}
        )
        user.email_user(subject=subject, message=message)

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = self.get_user(email)
        site = Site.find_for_request(self.request)
        sitename = site.site_name or str(site)
        if user:
            link = self.create_link(user)
            self.send_email(user, link, sitename)
        return render(
            self.request,
            "patterns/pages/users/email_login_success.html",
            {"breadcrumbs": self.get_breadcrumbs()},
        )
