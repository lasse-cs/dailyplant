{% load markdown_tags wagtailcore_tags wagtailimages_tags %}
---
title: "{{ page.title }}"
url: {% markdownpageurl page %}
---

# {{ page.title }}
Date: {{ page.date|date:'Y-m-d' }}

{% include "non_patterns/facts/fact_body.md" with fact=page %}

## References:
{% include "non_patterns/facts/fact_references.md" with fact=page %}

{% if related_facts %}
## Related Facts
{% for related_fact in related_facts %}
- [{{ related_fact.title }}]({% markdownpageurl related_fact %})
{% endfor %}
{% endif %}
