{% load markdown_tags %}
---
title: "{{ page.title }}"
url: {{ page.get_full_url }}{% if images.number > 1 %}?page={{ images.number }}{% endif %}
---

# {{ page.title }}

{{ page.introduction|richtext_markdown }}

{% for image_page in images %}
## [{{ image_page.title }}]({% markdownpageurl image_page %})

{{ image_page.description|richtext_markdown }}
{% empty %}
No images found.
{% endfor %}

{% if images.has_previous %}[Newer images](?page={{ images.previous_page_number }}){% endif %}
{% if images.has_next %}[Older images](?page={{ images.next_page_number }}){% endif %}
