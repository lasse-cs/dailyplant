from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from social.models import BlueskyPost, BlueskyPostStatus

from atproto import Client
from atproto.exceptions import AtProtocolError


class Command(BaseCommand):
    help = "Publish the pending social posts"

    def _get_client(self, username, password):
        client = Client()
        client.login(username, password)
        return client

    def handle(self, *args, **options):
        if not getattr(settings, "BLUESKY_USERNAME", None) or not getattr(
            settings, "BLUESKY_PASSWORD", None
        ):
            raise CommandError("Bluesky is not configured.")

        try:
            client = self._get_client(
                settings.BLUESKY_USERNAME, settings.BLUESKY_PASSWORD
            )
        except Exception as e:
            raise CommandError("Unable to login") from e
        posts = BlueskyPost.objects.filter(status=BlueskyPostStatus.PENDING)

        for post in posts:
            if not post.page.live:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Deleted entry for {post.page.title} because no longer live."
                    )
                )
                post.delete()
                continue

            try:
                response = client.send_post(post.format_post())
                post.bluesky_uri = response.uri
                post.bluesky_cid = response.cid
                error = ""
                status = BlueskyPostStatus.POSTED
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully posted {post.page.title}")
                )
            except AtProtocolError as e:
                status = BlueskyPostStatus.FAILED
                error = str(e)
                self.stdout.write(
                    self.style.ERROR(f"Failed to post {post.page.title}: {e}")
                )
            post.status = status
            post.error = error
            post.save()
