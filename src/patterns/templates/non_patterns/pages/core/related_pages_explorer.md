{% load core_tags markdown_tags wagtailcore_tags %}
---
title: "{{ page.title }}"
url: {% fullpageurl page %}
---

# {{ page.title }}

{{ page.intro|richtext|markdownify }}

{% if data.nodes %}
| Title | Type | Connections | Connected pages |
| --- | --- | ---: | --- |
{% for id, node in data.nodes.items %}| [{{ node.title }}]({{ node.markdown_url }}) | {{ data.types|get_item:node.type }} | {{ node.degree }} | {% for neighbour in node.edges %}{% with neighbour_node=data.nodes|get_item:neighbour %}"{{ neighbour_node.title }}"{% if not forloop.last %}, {% endif %}{% endwith %}{% empty %}None{% endfor %} |
{% endfor %}
{% else %}
There are no pages to explore yet.
{% endif %}

{% render_markdown_json_ld %}
