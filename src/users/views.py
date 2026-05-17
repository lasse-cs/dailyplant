from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView

from sesame.utils import get_query_string

from users.forms import EmailLoginForm


class EmailLoginView(FormView):
    template_name = "patterns/pages/users/email_login.html"
    form_class = EmailLoginForm

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

    def send_email(self, user, link):
        """Send an email with this login link to this user."""
        user.email_user(
            subject="[django-sesame] Log in to our app",
            message=f"""\
Hello,

You requested that we send you a link to log in to our app:

{link}

Thank you for using django-sesame!""",
        )

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = self.get_user(email)
        if user:
            link = self.create_link(user)
            self.send_email(user, link)
        return render(self.request, "patterns/pages/users/email_login_success.html")
