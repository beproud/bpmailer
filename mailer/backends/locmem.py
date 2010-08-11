"""
Backend for test environment.
"""

from django.core import mail

from mailer.backends.base import BaseEmailBackend

class EmailBackend(BaseEmailBackend):
    """A email backend for use during test sessions.

    The test connection stores email messages in a dummy outbox,
    rather than sending them out on the wire.

    The dummy outbox is accessible through the outbox instance attribute.
    """
    def __init__(self, *args, **kwargs):
        super(EmailBackend, self).__init__(*args, **kwargs)
        if not hasattr(mail, 'outbox'):
            mail.outbox = []

    def send_messages(self, messages):
        """Redirect messages to the dummy outbox"""
        from mailer.signals import mail_pre_send, mail_post_send
        for msg in messages:
            mail_pre_send.send(sender=msg, message=msg)
            mail.outbox.append(msg)
            mail_post_send.send(sender=msg, message=msg)
        return len(messages)
