from django.urls import reverse


def test_rate_limits_email_sending(client, django_user_model, mailoutbox):
    django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com"
    )
    django_user_model.objects.create_superuser(
        username="otheradmin", email="otheradmin@example.com"
    )

    url = reverse("wagtailadmin_login")
    client.post(url, {"email": "admin@example.com"})
    client.post(url, {"email": "admin@example.com"})
    client.post(url, {"email": "admin@example.com"})

    # This one should be rate limited
    client.post(url, {"email": "admin@example.com"})
    assert len(mailoutbox) == 3

    # But a different admin should still be able to
    client.post(url, {"email": "otheradmin@example.com"})
    assert len(mailoutbox) == 4
