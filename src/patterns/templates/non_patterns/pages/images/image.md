{% load markdown_tags wagtailcore_tags wagtailimages_tags %}
---
title: "{{ page.title }}"
url: {% fullpageurl page %}
---

# {{ page.title }}

![{{ page.image_alt_text }}]({{ page.get_site.root_url }}{% image_url page.image 'width-1120' 'wagtailimages_serve' %})

{{ page.description|richtext_markdown }}

{% if page.references %}
## References
{% for reference in page.references %}
- [{{ reference.value.label|richtext_markdown }}]({{ reference.value.url }})
{% endfor %}
{% endif %}

{% if related_pages %}
## Related Pages
{% for related_page in related_pages %}
- [{{ related_page.title }}]({% markdownpageurl related_page %})
{% endfor %}
{% endif %}

{% render_markdown_json_ld %}
