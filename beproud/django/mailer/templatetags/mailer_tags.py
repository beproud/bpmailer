#:coding=utf-8:

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.text import normalize_newlines

register = template.Library()


def replace_newlines(text, replacement=' '):
    """
    Replaces all newline characters in a block of text.
    """
    normalized_text = normalize_newlines(text)
    return normalized_text.replace('\n', replacement)
replace_newlines.is_safe = True
replace_newlines = stringfilter(replace_newlines)
register.filter(replace_newlines)
