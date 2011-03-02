{% load mailer_tags %}{% autoescape off %}{% filter replace_newlines:"" %}{% block subject %}{{ subject }}{% endblock %}{% endfilter %}
{% block body %}{{ body }}{% endblock %}{% endautoescape %}
