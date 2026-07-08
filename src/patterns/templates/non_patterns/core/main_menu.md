{% load wagtailcore_tags %}
{% for menu_item in menu_items %}
1. [{{ menu_item.title }}]({% pageurl menu_item %})
{% endfor %}