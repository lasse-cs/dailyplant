{% for block in fact.references %}
1. [{{ block.value.label|striptags }}]({{ block.value.url }})
{% endfor %}