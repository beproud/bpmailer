#:coding=utf-8:
from django.dispatch import Signal

mail_pre_send = Signal(providing_args=["message"])
mail_post_send = Signal(providing_args=["message"])
