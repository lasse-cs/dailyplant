{% load markdown_tags wagtailcore_tags %}
---
title: "{{ page.title }}"
url: {% fullpageurl page %}
---

# {{ page.title }}

{{ page.body|richtext|markdownify }}
