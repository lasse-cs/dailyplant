from django.db import models


class BlueskyPostStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    POSTED = "posted", "Posted"
    FAILED = "failed", "Failed"


class BlueskyPost(models.Model):
    page = models.OneToOneField(
        "wagtailcore.Page", on_delete=models.CASCADE, related_name="bluesky_post"
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

    def get_post_url(self):
        if not self.bluesky_uri:
            return None
        _, _, repo, _, rkey = self.bluesky_uri.split("/")
        return f"https://bsky.app/profile/{repo}/post/{rkey}"

    def __str__(self):
        return f"Bluesky Post - {self.status} - {self.page.title}"
