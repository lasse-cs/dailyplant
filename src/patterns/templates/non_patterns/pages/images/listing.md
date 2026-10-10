{% load markdown_tags wagtailcore_tags %}
---
title: "{{ page.title }}"
url: {{ metadata_url }}
---

# {{ page.title }}

{{ page.introduction|richtext_markdown }}

{% if active_slug %}Filtered on Tag {{ active_slug }}{% endif %}

{% for image_page in images %}
## [{{ image_page.title }}]({% markdownpageurl image_page %})

{{ image_page.description|richtext_markdown }}
{% empty %}
No images found.
{% endfor %}

Page {{ images.number }}
{% if images.has_previous %}[Newer images]({{ index_url }}{% querystring page=images.previous_page_number %}){% endif %}
{% if images.has_next %}[Older images]({{ index_url }}{% querystring page=images.next_page_number %}){% endif %}

{% render_markdown_json_ld %}
