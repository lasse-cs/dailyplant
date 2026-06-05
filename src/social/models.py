from django.db import models

from atproto_client.utils.text_builder import TextBuilder


class BlueskyPostStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    POSTED = "posted", "Posted"
    FAILED = "failed", "Failed"


class BlueskyPost(models.Model):
    page = models.OneToOneField(
        "facts.FactPage", on_delete=models.CASCADE, related_name="bluesky_post"
    )
    status = models.CharField(
        choices=BlueskyPostStatus,
        default=BlueskyPostStatus.PENDING,
        db_index=True,
        max_length=20,
    )
    bluesky_uri = models.CharField(max_length=512, blank=True)
    bluesky_cid = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    error = models.TextField(blank=True)

    def format_post(self):
        text_builder = TextBuilder()
        text_builder.text(self.page.title)
        text_builder.text("\n\n")
        full_url = self.page.get_full_url()
        text_builder.link(full_url, full_url)
        text_builder.text("\n\n")
        for index, tag in enumerate(self.page.tags.all()):
            hashtag = "#" + "".join(word.capitalize() for word in tag.slug.split("-"))
            if index:
                text_builder.text(" ")
            text_builder.tag(hashtag, hashtag)
        return text_builder
