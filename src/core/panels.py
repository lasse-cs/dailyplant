from wagtail.admin.panels import PageChooserPanel, Panel
from wagtail.admin.widgets import AdminPageChooser
from wagtail.models import get_page_models


class RelatedPageChooserPanel(PageChooserPanel):
    def get_form_options(self):
        from core.models import RelatedPagesMixin

        options = super().get_form_options()
        target_models = [
            model for model in get_page_models() if issubclass(model, RelatedPagesMixin)
        ]
        widgets = options.setdefault("widgets", {})
        widgets[self.field_name] = AdminPageChooser(target_models=target_models)
        return options


class IncomingRelatedPagesPanel(Panel):
    class BoundPanel(Panel.BoundPanel):
        template_name = "non_patterns/core/admin/incoming_related_pages.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["incoming"] = self.instance.get_incoming_related_pages()
            return context
