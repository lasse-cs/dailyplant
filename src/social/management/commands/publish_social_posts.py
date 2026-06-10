from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from atproto import Client, models
from atproto.exceptions import AtProtocolError
from wagtail.images.models import SourceImageIOError

from social.models import BlueskyPost, BlueskyPostStatus


BLUESKY_EXTERNAL_THUMB_MAX_BYTES = 1_000_000


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
                thumb_blob = None
                if thumbnail_image := post.get_thumbnail_image():
                    rendition = thumbnail_image.get_rendition("fill-1200x630")
                    with rendition.file.open("rb") as f:
                        thumb_data = f.read()

                    if len(thumb_data) > BLUESKY_EXTERNAL_THUMB_MAX_BYTES:
                        raise ValueError(
                            "Bluesky external thumbnail exceeds 1MB limit."
                        )

                    thumb_blob = client.upload_blob(thumb_data).blob

                embed = models.AppBskyEmbedExternal.Main(
                    external=models.AppBskyEmbedExternal.External(
                        uri=post.get_url(),
                        title=post.get_title(),
                        description=post.get_description(),
                        thumb=thumb_blob,
                    )
                )

                response = client.send_post(post.format_post(), embed=embed)
                post.bluesky_uri = response.uri
                post.bluesky_cid = response.cid
                error = ""
                status = BlueskyPostStatus.POSTED
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully posted {post.page.title}")
                )
            except (
                AtProtocolError,
                FileNotFoundError,
                OSError,
                SourceImageIOError,
                ValueError,
            ) as e:
                status = BlueskyPostStatus.FAILED
                error = str(e)
                self.stdout.write(
                    self.style.ERROR(f"Failed to post {post.page.title}: {e}")
                )
            post.status = status
            post.error = error
            post.save()
