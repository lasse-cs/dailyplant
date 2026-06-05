from django.apps import AppConfig


class SocialConfig(AppConfig):
    name = "social"

    def ready(self):
        from social import signals  # noqa: F401
