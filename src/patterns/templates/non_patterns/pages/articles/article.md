{% load markdown_tags wagtailcore_tags wagtailimages_tags %}
---
title: "{{ page.title }}"
url: {% fullpageurl page %}
---

# {{ page.title }}
{% if page.first_published_at %}Published: {{ page.first_published_at|date:'Y-m-d' }}{% endif %}

{{ page.introduction|richtext|markdownify }}

{% if page.image %}![{{ page.image_alt_text }}]({{ page.get_site.root_url }}{% image_url page.image 'fill-1120x630-c90' 'wagtailimages_serve' %}{% if page.image_description %} "{{ page.image_description }}"{% endif %})

{% endif %}{% for block in page.body %}{% if block.block_type == "heading" %}{% if block.value.level == "2" %}##{% else %}###{% endif %} {{ block.value.text }}

{% elif block.block_type == "paragraph" %}{{ block.value|richtext|markdownify }}

{% endif %}{% endfor %}

{% if related_pages %}
## Related Pages
{% for related_page in related_pages %}
- [{{ related_page.title }}]({% markdownpageurl related_page %})
{% endfor %}
{% endif %}

{% render_markdown_json_ld %}
