{% load markdown_tags wagtailcore_tags %}
---
title: "{{ page.title }}"
url: {{ metadata_url }}
---

# {{ page.title }}

{{ page.introduction|richtext|markdownify }}

{% if active_slug %}Filtered on Tag {{ active_slug }}{% endif %}

{% for article in articles %}
1. [{{ article.title }}]({% markdownpageurl article %})
{% empty %}
No articles found.
{% endfor %}

Page {{ articles.number }}
{% if articles.has_next %}
[Next Page]({{ index_url }}{% querystring page=articles.next_page_number %})
{% endif %}
{% if articles.has_previous %}
[Previous Page]({{ index_url }}{% querystring page=articles.previous_page_number %})
{% endif %}

{% render_markdown_json_ld %}