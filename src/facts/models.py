from datetime import datetime, time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django import forms
from django.db import models
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.cache import patch_vary_headers
from django.utils.html import strip_tags
from django.utils.text import Truncator

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import MultipleChooserPanel, Panel
from wagtail.contrib.routable_page.models import RoutablePage, path
from wagtail.contrib.routable_page.templatetags.wagtailroutablepage_tags import (
    routablefullpageurl,
)
from wagtail.fields import RichTextField, RichTextMaxLengthValidator, StreamField
from wagtail.models import Page, PageManager
from wagtail.query import PageQuerySet
from wagtail.rich_text import expand_db_html
from wagtail.search import index

from taggit.models import ItemBase, TagBase

from wagtail_umami_analytics.panels import UmamiAnalyticsPanel

from core.models import MetadataMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

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


class FactIndexPage(MetadataMixin, RoutablePage):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["facts.FactPage"]
    max_count = 1
    template = "patterns/pages/facts/fact_index.html"

    introduction = RichTextField(
        blank=True, help_text="Introductory content for the fact index page."
    )

    def serve(self, request, view=None, args=None, kwargs=None):
        response = super().serve(request, view=view, args=args, kwargs=kwargs)
        patch_vary_headers(response, ["HX-Request"])
        return response

    @path("tags/<slug:slug>/", name="tag")
    def tag(self, request, slug):
        get_object_or_404(FactTag, slug=slug)
        context = self.get_context(request, slug=slug)
        template = self.get_template(request)
        return render(request, template, context)

    def get_template(self, request):
        if "HX-Request" in request.headers:
            return "non_patterns/facts/partials/fact_index.html"
        return super().get_template(request)

    def get_facts(self, slug=None):
        facts = (
            FactPage.objects.live()
            .child_of(self)
            .released()
            .prefetch_related("tags")
            .order_by("-date")
            .annotate(heading_level=models.Value("h2"))
        )
        if slug:
            facts = facts.filter(tags__slug=slug)
        return facts

    def get_tags(self):
        return FactTag.objects.all()

    def get_metadata_url(self, request):
        resolver_match = getattr(request, "routable_resolver_match", None)
        if resolver_match and resolver_match.url_name == "tag":
            metadata_url = routablefullpageurl(
                {"request": request},
                self,
                resolver_match.url_name,
                *resolver_match.args,
                **resolver_match.kwargs,
            )
        else:
            metadata_url = super().get_metadata_url(request)

        if "page" in request.GET:
            try:
                page_number = int(request.GET["page"])
                if page_number > 1:
                    parsed = urlparse(metadata_url)
                    params = parse_qs(parsed.query)
                    params["page"] = [str(page_number)]
                    metadata_url = urlunparse(
                        parsed._replace(query=urlencode(params, doseq=True))
                    )
            except ValueError:
                pass
        return metadata_url

    def get_context(self, request, slug=None):
        context = super().get_context(request)
        page_number = request.GET.get("page", 1)
        paginator = Paginator(self.get_facts(slug), 20, orphans=2)
        try:
            facts = paginator.page(page_number)
        except PageNotAnInteger, EmptyPage:
            facts = Paginator([], 1, allow_empty_first_page=True).page(1)
        context["facts"] = facts
        context["tags"] = self.get_tags()
        context["active_slug"] = slug
        return context

    content_panels = Page.content_panels + [
        "introduction",
    ]


class FactPageQuerySet(PageQuerySet):
    def released(self):
        return self.filter(date__lte=timezone.localdate())


class FactPageForm(WagtailAdminPageForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=FactTag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )


class IncomingRelatedFactsPanel(Panel):
    class BoundPanel(Panel.BoundPanel):
        template_name = "non_patterns/facts/admin/incoming_related_facts.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["incoming"] = self.instance.get_incoming_related_facts()
            return context


class FactPage(MetadataMixin, Page):
    objects = PageManager.from_queryset(FactPageQuerySet)()

    parent_page_types = ["facts.FactIndexPage"]
    subpage_types = []
    template = "patterns/pages/facts/fact.html"
    metadata_type = "article"
    base_form_class = FactPageForm

    date = models.DateField(help_text="The date this fact is for.", unique=True)
    content = RichTextField(
        help_text="The content of this fact.",
        validators=[RichTextMaxLengthValidator(500)],
    )
    references = StreamField(
        ReferenceStreamBlock, help_text="The references for this fact"
    )
    tags = ClusterTaggableManager(through="facts.TaggedFact", blank=True)

    @property
    def metadata_description(self):
        content = strip_tags(expand_db_html(self.content))
        return Truncator(" ".join(content.split())).chars(240, truncate="...")

    def clean(self):
        super().clean()
        # If we're a future date, schedule it for publishing at midnight
        if self.date and self.date > timezone.localdate():
            self.go_live_at = timezone.make_aware(datetime.combine(self.date, time.min))

    def get_older_fact(self):
        """
        Returns the released fact which is the "next older", or None
        if this is the oldest fact.
        """
        if not self.date:
            return None
        return (
            FactPage.objects.live()
            .released()
            .order_by("-date")
            .filter(date__lt=self.date)
            .first()
        )

    def get_newer_fact(self):
        """
        Returns the released fact with the "next newer", or None
        if this is the newest fact.
        """
        if not self.date:
            return None
        return (
            FactPage.objects.live()
            .released()
            .order_by("date")
            .filter(date__gt=self.date)
            .first()
        )

    def get_incoming_related_facts(self):
        # If the fact is not saved, it can not have incoming facts
        # and can not be used in a filter
        if not self.id:
            return FactPage.objects.none()
        return FactPage.objects.live().released().filter(related_facts__fact=self)

    def get_outgoing_related_facts(self):
        return (
            FactPage.objects.live()
            .released()
            .filter(id__in=self.related_facts.values_list("fact_id", flat=True))
        )

    def get_related_facts(self):
        return (
            (self.get_outgoing_related_facts() | self.get_incoming_related_facts())
            .exclude(id=self.id)
            .distinct()
        )

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["share"] = self.get_full_url(request)
        context["related_facts"] = self.get_related_facts()
        return context

    content_panels = Page.content_panels + [
        "date",
        "content",
        "references",
        "tags",
        MultipleChooserPanel(
            "related_facts", label="Related Facts", chooser_field_name="fact"
        ),
        IncomingRelatedFactsPanel(),
    ]

    promote_panels = [
        UmamiAnalyticsPanel(),
    ] + Page.promote_panels

    search_fields = Page.search_fields + [
        index.SearchField("content"),
        index.FilterField("date"),
        index.RelatedFields(
            "tags",
            [
                index.SearchField("name"),
            ],
        ),
    ]


class FactPageRelatedFact(models.Model):
    owner = ParentalKey(
        FactPage, on_delete=models.CASCADE, related_name="related_facts"
    )
    fact = models.ForeignKey(FactPage, on_delete=models.CASCADE, related_name="+")

    panels = [
        "fact",
    ]
