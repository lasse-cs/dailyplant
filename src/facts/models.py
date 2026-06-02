from datetime import datetime, time

from django.db import models
from django.utils import timezone

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey

from wagtail.fields import RichTextField, RichTextMaxLengthValidator, StreamField
from wagtail.models import Page

from taggit.models import ItemBase, TagBase

from core.models import MetadataMixin

from facts.blocks import ReferenceStreamBlock


class FactTag(TagBase):
    free_tagging = False

    class Meta:
        verbose_name = "fact tag"
        verbose_name_plural = "fact tags"


class TaggedFact(ItemBase):
    tag = models.ForeignKey(
        FactTag, related_name="tagged_facts", on_delete=models.CASCADE
    )
    content_object = ParentalKey(
        to="facts.FactPage", related_name="tagged_items", on_delete=models.CASCADE
    )


class FactIndexPage(Page):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["facts.FactPage"]
    max_count = 1
    template = "patterns/pages/facts/fact_index.html"

    introduction = RichTextField(
        blank=True, help_text="Introductory content for the fact index page."
    )

    def get_facts(self):
        return (
            FactPage.objects.live()
            .child_of(self)
            .prefetch_related("tags")
            .order_by("-date")
            .annotate(heading_level=models.Value("h2"))
        )

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["facts"] = self.get_facts()
        return context

    content_panels = Page.content_panels + [
        "introduction",
    ]


class FactPage(MetadataMixin, Page):
    parent_page_types = ["facts.FactIndexPage"]
    subpage_types = []
    template = "patterns/pages/facts/fact.html"
    metadata_type = "article"

    date = models.DateField(help_text="The date this fact is for.", unique=True)
    content = RichTextField(
        help_text="The content of this fact.",
        validators=[RichTextMaxLengthValidator(500)],
    )
    references = StreamField(
        ReferenceStreamBlock, help_text="The references for this fact"
    )
    tags = ClusterTaggableManager(through="facts.TaggedFact", blank=True)

    def clean(self):
        super().clean()
        # If we're a future date, schedule it for publishing at midnight
        if not self.go_live_at and self.date and self.date > timezone.localdate():
            self.go_live_at = timezone.make_aware(datetime.combine(self.date, time.min))

    content_panels = Page.content_panels + [
        "date",
        "content",
        "references",
        "tags",
    ]
