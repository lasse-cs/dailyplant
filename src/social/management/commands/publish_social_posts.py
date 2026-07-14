from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from wagtail.images.models import SourceImageIOError

from social.bluesky import BLUESKY_FORMATTERS
from social.models import BlueskyPost, BlueskyPostStatus


BLUESKY_EXTERNAL_THUMB_MAX_BYTES = 1_000_000


class Command(BaseCommand):
    help = "Publish the pending social posts"

    def _get_client(self, username, password):
        # Lazily import this
        from atproto import Client

        client = Client()
        client.login(username, password)
        return client

    def handle(self, *args, **options):
        # Lazily import these
        from atproto import models
        from atproto.exceptions import AtProtocolError

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
            page = post.page.specific
            if not page.live:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Deleted entry for {page.title} because no longer live."
                    )
                )
                post.delete()
                continue

            try:
                formatter = BLUESKY_FORMATTERS.get(page.specific_class)
                if not formatter:
                    raise ValueError(
                        f"No Bluesky formatter is registered for {page._meta.label}."
                    )
                content = formatter(page)

                thumb_blob = None
                if thumbnail_image := content.thumbnail_image:
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
                        uri=content.url,
                        title=content.title,
                        description=content.description,
                        thumb=thumb_blob,
                    )
                )

                response = client.send_post(content.text, embed=embed)
                post.bluesky_uri = response.uri
                post.bluesky_cid = response.cid
                error = ""
                status = BlueskyPostStatus.POSTED
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully posted {page.title}")
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
                self.stdout.write(self.style.ERROR(f"Failed to post {page.title}: {e}"))
            post.status = status
            post.error = error
            post.save()
