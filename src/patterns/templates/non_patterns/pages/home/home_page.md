{% load markdown_tags menu_tags wagtailcore_tags wagtailimages_tags %}
---
title: "{{ page.title }}"
url: {% fullpageurl page %}
---

# {{ page.title }}

## Menu
{% wagtail_site as current_site %}{% markdown_main_menu current_site %}


{% with social_links=settings.core.SocialMediaSettings.social_links.all %}{% if social_links %}
## Links
{% for social_link in social_links %}
- [{{ social_link.display }}]({{ social_link.url }})
{% endfor %}{% endif %}{% endwith %}

{% if fact %}
## {{ fact.title }}
Link: {% markdownpageurl fact %}
Date: {{ fact.date|date:'Y-m-d' }}

{% include "non_patterns/facts/fact_body.md" with fact=fact %}

### References
{% include "non_patterns/facts/fact_references.md" with fact=fact %}
{% endif %}

{% render_markdown_json_ld %}
