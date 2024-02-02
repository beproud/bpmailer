#:coding=utf-8:
from django.dispatch import Signal

mail_pre_send = Signal()
mail_post_send = Signal()
