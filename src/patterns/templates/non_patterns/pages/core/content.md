{% load markdown_tags wagtailcore_tags %}
---
title: "{{ page.title }}"
url: {% markdownpageurl page %}
---

# {{ page.title }}

{{ page.body|richtext|markdownify }}
