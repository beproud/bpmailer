"""
Email backend that writes messages to console instead of sending them.
"""
import sys
import logging
import threading

from django.conf import settings

from mailer.backends.base import BaseEmailBackend

logger = logging.getLogger(getattr(settings, "EMAIL_LOGGER", ""))

class EmailBackend(BaseEmailBackend):
    def __init__(self, *args, **kwargs):
        self.stream = kwargs.pop('stream', sys.stdout)
        self._lock = threading.RLock()
        super(EmailBackend, self).__init__(*args, **kwargs)

    def send_messages(self, email_messages):
        """Write all messages to the stream in a thread-safe way."""
        if not email_messages:
            return
        self._lock.acquire()
        try:
            # The try-except is nested to allow for
            # Python 2.4 support (Refs #12147)
            stream_created = self.open()
            for message in email_messages:
                self._send_message_wrapper(message)
            if stream_created:
                self.close()
        finally:
            self._lock.release()
        return len(email_messages)

    def _send_message(self, email_message):
        self.stream.write('%s\n' % email_message.message().as_string())
        self.stream.write('-'*79)
        self.stream.write('\n')
        self.stream.flush()  # flush after each message
