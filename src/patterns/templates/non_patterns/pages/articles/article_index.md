{% load markdown_tags wagtailcore_tags %}
---
title: "{{ page.title }}"
url: {% fullpageurl page %}
---

# {{ page.title }}

{{ page.introduction|richtext|markdownify }}

{% for article in articles %}
1. [{{ article.title }}]({% markdownpageurl article %})
{% empty %}
No articles found.
{% endfor %}

{% render_markdown_json_ld %}
