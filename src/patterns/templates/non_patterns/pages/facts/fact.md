{% load markdown_tags wagtailcore_tags wagtailimages_tags %}
---
title: "{{ page.title }}"
url: {% fullpageurl page %}
---

# {{ page.title }}
Date: {{ page.date|date:'Y-m-d' }}

{% include "non_patterns/facts/fact_body.md" with fact=page %}

## References:
{% include "non_patterns/facts/fact_references.md" with fact=page %}

{% if related_pages %}
## Related Pages
{% for related_page in related_pages %}
- [{{ related_page.title }}]({% markdownpageurl related_page %})
{% endfor %}
{% endif %}

{% render_markdown_json_ld %}
