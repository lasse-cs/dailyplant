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
from wagtail.contrib.routable_page.models import RoutablePage, path
from wagtail.contrib.routable_page.templatetags.wagtailroutablepage_tags import (
    routablefullpageurl,
)
from wagtail.fields import RichTextField, RichTextMaxLengthValidator, StreamField
from wagtail.models import Page, PageManager
from wagtail.query import PageQuerySet
from wagtail.rich_text import expand_db_html

from taggit.models import ItemBase, TagBase

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
            return routablefullpageurl(
                {"request": request},
                self,
                resolver_match.url_name,
                *resolver_match.args,
                **resolver_match.kwargs,
            )
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
        if not self.go_live_at and self.date and self.date > timezone.localdate():
            self.go_live_at = timezone.make_aware(datetime.combine(self.date, time.min))

    content_panels = Page.content_panels + [
        "date",
        "content",
        "references",
        "tags",
    ]
