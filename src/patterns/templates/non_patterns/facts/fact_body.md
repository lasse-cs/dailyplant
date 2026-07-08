{% load markdown_tags wagtailcore_tags wagtailimages_tags %}{{ fact.content|richtext|markdownify }}
{% if fact.image %}![{{ fact.image_alt_text }}]({{ fact.get_site.root_url }}{% image_url fact.image 'fill-1200x630' 'wagtailimages_serve' %}{% if fact.image_description %} "{{ fact.image_description }}"{% endif %}){% endif %}
