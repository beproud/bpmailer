"""
Dummy email backend that does nothing.
"""

from beproud.django.mailer.backends.base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    def _send_message(self, email_message):
        pass
