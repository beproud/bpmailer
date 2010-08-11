"""
Dummy email backend that does nothing.
"""

from mailer.backends.base import BaseEmailBackend

class EmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        from mailer.signals import mail_pre_send, mail_post_send
        map(lambda msg: mail_pre_send.send(sender=msg, message=msg), email_messages)
        map(lambda msg: mail_post_send.send(sender=msg, message=msg), email_messages)
        return len(email_messages)
