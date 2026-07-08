{% load markdown_tags wagtailcore_tags %}
---
title: "{{ page.title }}"
url: {{ metadata_url }}
---

# {{ page.title }}

{{ page.introduction|richtext|markdownify }}

{% if active_slug %}Filtered on Tag {{ active_slug }}{% endif %}

{% for fact in facts %}
1. [{{ fact.title }}]({% fullpageurl fact %})
{% empty %}
No facts found.
{% endfor %}

Page {{ facts.number }}
{% if facts.has_next %}
[Next Page]({{ index_url }}{% querystring page=facts.next_page_number %})
{% endif %}
{% if facts.has_previous %}
[Previous Page]({{ index_url }}{% querystring page=facts.previous_page_number %})
{% endif %}
