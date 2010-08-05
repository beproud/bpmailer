#:coding=utf-8:

import re
from datetime import datetime,date,timedelta
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Header import Header
from email.Utils import formatdate, getaddresses, formataddr

from django import VERSION as DJANGO_VERSION
from django.core import mail as django_mail
from django.utils.encoding import smart_str
from django import template
from django.template.loader import render_to_string
from django.conf import settings

from django.core.mail import (
    EmailMessage, SMTPConnection,
    BadHeaderError, make_msgid,
)

import logging

from signals import mail_pre_send, mail_post_send

__version__ = '0.2'

__all__ = (
    'get_connection',
    'forbid_multi_line_headers',
    'make_msgid',
    'send_mail',
    'send_template_mail',
    'send_mass_mail',
    'mail_managers',
    'mail_managers_template',
    'mail_admins',
    'render_message',
    'EmailMessage',
    'EmailMultiAlternatives',
    'SafeMIMEText',
    'SafeMIMEMultipart',
    'SMTPConnection',
    'BadHeaderError',
)

logger = logging.getLogger(getattr(settings, "EMAIL_LOGGER", ""))

if DJANGO_VERSION > (1,2):
    from django.core.mail import (
        SafeMIMEText, SafeMIMEMultipart,
        get_connection, forbid_multi_line_headers,
    )
else:
    from django.utils.encoding import force_unicode

    def get_connection(backend=None, fail_silently=False, **kwds):
        return SMTPConnection(fail_silently=fail_silently, **kwds)
 
    def forbid_multi_line_headers(name, val, encoding):
        """Forbids multi-line headers, to prevent header injection."""
        encoding = encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
        val = force_unicode(val)
        if '\n' in val or '\r' in val:
            raise BadHeaderError("Header values can't contain newlines (got %r for header %r)" % (val, name))
        try:
            val = val.encode('ascii')
        except UnicodeEncodeError:
            if name.lower() in ('to', 'from', 'cc'):
                result = []
                for nm, addr in getaddresses((val,)):
                    nm = str(Header(nm.encode(encoding), encoding))
                    result.append(formataddr((nm, str(addr))))
                val = ', '.join(result)
            else:
                val = Header(val.encode(encoding), encoding)
        else:
            if name.lower() == 'subject':
                val = Header(val)
        return name, val

    class SafeMIMEText(MIMEText):
        
        def __init__(self, text, subtype, charset):
            self.encoding = charset
            MIMEText.__init__(self, text, subtype, charset)
        
        def __setitem__(self, name, val):    
            name, val = forbid_multi_line_headers(name, val, self.encoding)
            MIMEText.__setitem__(self, name, val)

    class SafeMIMEMultipart(MIMEMultipart):
        
        def __init__(self, _subtype='mixed', boundary=None, _subparts=None, encoding=None, **_params):
            self.encoding = encoding
            MIMEMultipart.__init__(self, _subtype, boundary, _subparts, **_params)
            
        def __setitem__(self, name, val):
            name, val = forbid_multi_line_headers(name, val, self.encoding)
            MIMEMultipart.__setitem__(self, name, val)


class EmailMessage(django_mail.EmailMessage):
    def message(self):
        encoding = self.encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
        msg = SafeMIMEText(smart_str(self.body, encoding),
                           self.content_subtype, encoding)
        msg = self._create_message(msg)
        msg['Subject'] = self.subject
        msg['From'] = self.extra_headers.get('From', self.from_email)
        msg['To'] = ', '.join(self.to)

        # Email header names are case-insensitive (RFC 2045), so we have to
        # accommodate that when doing comparisons.
        header_names = [key.lower() for key in self.extra_headers]
        if 'date' not in header_names:
            msg['Date'] = formatdate()
        if 'message-id' not in header_names:
            msg['Message-ID'] = make_msgid()
        for name, value in self.extra_headers.items():
            if name.lower() == 'from':  # From is already handled
                continue
            msg[name] = value
        return msg

    def _create_mime_attachment(self, content, mimetype):
        """
        Converts the content, mimetype pair into a MIME attachment object.
        """
        basetype, subtype = mimetype.split('/', 1)
        if basetype == 'text':
            encoding = self.encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
            attachment = SafeMIMEText(smart_str(content, encoding), subtype, encoding)
        else:
            # Encode non-text attachments with base64.
            attachment = MIMEBase(basetype, subtype)
            attachment.set_payload(content)
            Encoders.encode_base64(attachment)
        return attachment

class EmailMultiAlternatives(EmailMessage):
    """
    A version of EmailMessage that makes it easy to send multipart/alternative
    messages. For example, including text and HTML versions of the text is
    made easier.
    """
    alternative_subtype = 'alternative'

    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
            connection=None, attachments=None, headers=None, alternatives=None):
        """
        Initialize a single email message (which can be sent to multiple
        recipients).

        All strings used to create the message can be unicode strings (or UTF-8
        bytestrings). The SafeMIMEText class will handle any necessary encoding
        conversions.
        """
        super(EmailMultiAlternatives, self).__init__(subject, body, from_email, to, bcc, connection, attachments, headers)
        self.alternatives=alternatives or []

    def attach_alternative(self, content, mimetype):
        """Attach an alternative content representation."""
        assert content is not None
        assert mimetype is not None
        self.alternatives.append((content, mimetype))

    def _create_message(self, msg):
        return self._create_attachments(self._create_alternatives(msg))

    def _create_alternatives(self, msg):
        encoding = self.encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
        if self.alternatives:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.alternative_subtype, encoding=encoding)
            if self.body:
                msg.attach(body_msg)
            for alternative in self.alternatives:
                msg.attach(self._create_mime_attachment(*alternative))
        return msg

def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None, encoding=None):

    try:
        if settings.DEBUG and hasattr(settings, "EMAIL_ALL_FORWARD"):
            recipient_list = [settings.EMAIL_ALL_FORWARD]
            from_email = settings.EMAIL_ALL_FORWARD

        connection = get_connection(username=auth_user, password=auth_password,
                                    fail_silently=False)
        msg = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
        )
        msg.encoding = encoding
        mail_pre_send.send(sender=msg, message=msg)
        return_val = msg.send()
        mail_post_send.send(sender=msg, message=msg)
        log_message(msg, return_val) 
        return return_val
    except Exception, e:
        log_exception("Mail Error")
        if not fail_silently:
            raise

def render_message(template_name, extra_context={}):
    """
    Renders an email message from a template and returns a two
    tuple containing the subject and body of the message.

    The contents of the EMAIL_DEFAULT_CONTENT setting are
    passed to the template when it is rendered but can be
    overridden.
    """
    from django.template.loader import render_to_string
    context = getattr(settings, "EMAIL_DEFAULT_CONTEXT", {})
    context.update(extra_context)

    rendered_mail = render_to_string(template_name, context).replace(u"\r\n",u"\n").replace(u"\r",u"\n").split(u"\n")
    return rendered_mail[0], "\n".join(rendered_mail[1:])
    
def send_template_mail(template_name, from_email, recipient_list, extra_context={},
                       fail_silently=True, auth_user=None, auth_password=None, encoding=None):
    u"""
    Send an email using a django template. The template should be formatted
    so that the first line of the template is the subject. All subsequent lines
    are used as the body of the email message.
    """
    try:
        if not isinstance(recipient_list, list) and not isinstance(recipient_list, tuple):
            recipient_list = [recipient_list]
        
        subject,message = render_message(template_name, extra_context)
        return send_mail(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            from_email=from_email,
            fail_silently=fail_silently,
            auth_user=auth_user,
            auth_password=auth_password,
            encoding=encoding,
        )
    except Exception, e:
        log_exception("Mail Error")
        if not fail_silently:
            raise

def send_mass_mail(datatuple, fail_silently=False, auth_user=None,
                   auth_password=None, encoding=None):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.
    Also supports an optional encoding parameter to the datatuple. Individual
    items in the datatuple may have a fifth item which specifies the encoding
    of the particular email. Encodings in the datatuple have priority over
    the encoding passed to send_mass_mail.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    connection = get_connection(username=auth_user, password=auth_password,
                                fail_silently=fail_silently)
    def _message(args):
        if len(args) > 4:
            subject, message, sender, recipient, charset = args
        else:
            subject, message, sender, recipient = args
            charset = encoding or None
        message = EmailMessage(subject, message, sender, recipient)
        if charset:
            message.encoding = charset
        mail_pre_send.send(sender=message, message=message)
        return message
    
    messages = map(_message, datatuple)
    return_val = connection.send_messages(messages)
    messages = map(lambda msg: mail_post_send.send(sender=msg, message=msg), messages)
    return return_val

def mail_managers(subject, message, fail_silently=False, encoding=None):
    if not settings.MANAGERS:
        return
    send_mail(
        subject=settings.EMAIL_SUBJECT_PREFIX + subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        recipient_list=[a[1] for a in settings.MANAGERS],
        fail_silently=fail_silently,
        encoding=encoding,
    )

def mail_managers_template(template_name, extra_context={}, fail_silently=True, encoding=None):
    if not settings.MANAGERS:
        return
    return send_template_mail(
        template_name=template_name,
        recipient_list=[a[1] for a in settings.MANAGERS],
        extra_context=extra_context,
        from_email=settings.SERVER_EMAIL,
        fail_silently=fail_silently,
        encoding=encoding,
    )

def mail_admins(subject, message, fail_silently=False, encoding=None):
    if not settings.ADMINS:
        return
    send_mail(
        subject=settings.EMAIL_SUBJECT_PREFIX + subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        recipient_list=[a[1] for a in settings.ADMINS],
        fail_silently=fail_silently,
        encoding=encoding,
    )

def log_message(msg, sent):
    message = "%s messages sent.\n" % sent 
    message += "From: %s\n" % msg.from_email 
    message += "To: %s\n" % ", ".join(msg.to)
    message += "Subject: %s\n" % msg.subject
    message += "Body\n"
    message += "-"*30 + "\n"
    message += msg.body

    logger.info(message)

def log_exception(msg=""):
    msg = msg+"\n" if msg else ""
    import traceback,sys
    tb = ''.join(traceback.format_exception(sys.exc_info()[0],
                    sys.exc_info()[1], sys.exc_info()[2]))
    logger.exception(msg + tb)
