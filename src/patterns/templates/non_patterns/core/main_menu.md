{% load markdown_tags %}
{% for menu_item in menu_items %}
1. [{{ menu_item.title }}]({% markdownpageurl menu_item %})
{% endfor %}