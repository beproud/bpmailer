# vim:fileencoding=utf8

import re
from datetime import datetime,date,timedelta
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Header import Header
from email.Utils import formatdate, parseaddr, formataddr

from django.core import mail as django_mail
from django.utils.encoding import smart_str
from django import template
from django.template.loader import render_to_string
from django.conf import settings

from django.core.mail import SMTPConnection, BadHeaderError

import logging

__version__ = '0.0.1'

# TODO: Support EmailMultiAlternatives
__all__ = (
    'send_mail',
    'send_basic_mail',
    'send_template_mail',
    'send_mass_mail',
    'mail_managers',
    'mail_managers_template',
    'mail_admins',
    'render_message',
    'EmailMessage',
    'SafeMIMEText',
    'SafeMIMEMultipart',
    'SMTPConnection',
    'BadHeaderError',
)

logger = logging.getLogger(getattr(settings, "EMAIL_LOGGER", ""))

def format_header(name, val, encoding=None):
    encoding = encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
    if '\n' in val or '\r' in val:
        raise django_mail.BadHeaderError("Header values can't contain newlines (got %r for header %r)" % (val, name)) 
    if name.lower() in ('to', 'from', 'cc'):
        result = []
        for item in val.split(', '):
            nm, addr = parseaddr(item)
            nm = str(Header(nm.encode(encoding,'replace'), encoding))
            result.append(formataddr((nm, str(addr))))
        val = ', '.join(result)
    elif name.lower() == 'subject':
        val = Header(val.encode(encoding,'replace'), encoding)
    else:
        val = Header(val, encoding)
    
    return name,val

class SafeMIMEText(MIMEText):
    def __setitem__(self, name, val):
        if name.lower() in ('subject', 'to', 'from', 'cc'):
            name,val = format_header(name, val, smart_str(self._charset))
        MIMEText.__setitem__(self, name, val)

class SafeMIMEMultipart(MIMEMultipart):
    def __setitem__(self, name, val):
        if name.lower() in ('subject', 'to', 'from', 'cc'):
            name,val = format_header(name, val, smart_str(self._charset))
        MIMEText.__setitem__(self, name, val)

class EmailMessage(django_mail.EmailMessage):
    def message(self):
        encoding = self.encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
        msg = SafeMIMEText(smart_str(self.body, encoding, 'replace'),
                           self.content_subtype, encoding)
        if self.attachments:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.multipart_subtype)
            if self.body:
                msg.attach(body_msg)
            for attachment in self.attachments:
                if isinstance(attachment, MIMEBase):
                    msg.attach(attachment)
                else:
                    msg.attach(self._create_attachment(*attachment))
        msg['Subject'] = self.subject 
        msg['From'] = self.extra_headers.pop('From', self.from_email)
        msg['To'] = ', '.join(self.to)

        # Email header names are case-insensitive (RFC 2045), so we have to
        # accommodate that when doing comparisons.
        header_names = [key.lower() for key in self.extra_headers]
        if 'date' not in header_names:
            msg['Date'] = formatdate(localtime=True)
        if 'message-id' not in header_names:
            msg['Message-ID'] = django_mail.make_msgid()
        for name, value in self.extra_headers.items():
            msg[name] = value
        return msg

def send_basic_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None, encoding=None):

    try:
        from django.core.mail import SMTPConnection

        if settings.DEBUG and hasattr(settings, "EMAIL_ALL_FORWARD"):
            recipient_list = [settings.EMAIL_ALL_FORWARD]
            from_email = settings.EMAIL_ALL_FORWARD

        connection = SMTPConnection(username=auth_user, password=auth_password,
                                    fail_silently=False)
        msg = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
        )
        if encoding is not None:
            msg.encoding = encoding 
        return_val = msg.send()
        log_message(msg, return_val) 
        return return_val
    except Exception, e:
        log_exception("Mail Error")
        if not fail_silently:
            raise

def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None):
    send_basic_mail(
        subject=subject,
        message=message,
        recipient_list=recipient_list,
        from_email=from_email,
        fail_silently=fail_silently,
        auth_user=auth_user,
        auth_password=auth_password,
    )

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
    
def send_template_mail(template_name, recipient_list, extra_context={},
                       from_email=settings.SERVER_EMAIL, fail_silently=True, encoding=None):
    u"""
    Send an email using a django template. The template should be formatted
    so that the first line of the template is the subject. All subsequent lines
    are used as the body of the email message.
    """
    try:
        if not isinstance(recipient_list, list) and not isinstance(recipient_list, tuple):
            recipient_list = [recipient_list]
        
        subject,message = render_message(template_name, extra_context, fail_silently)
        return send_basic_mail(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            from_email=from_email,
            fail_silently=fail_silently,
            encoding=encoding,
        )
    except Exception, e:
        log_exception("Mail Error")
        if not fail_silently:
            raise

def send_mass_mail(datatuple, fail_silently=False, auth_user=None,
                   auth_password=None):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    connection = SMTPConnection(username=auth_user, password=auth_password,
                                fail_silently=fail_silently)
    messages = [EmailMessage(subject, message, sender, recipient)
                for subject, message, sender, recipient in datatuple]
    return connection.send_messages(messages)

def mail_managers(subject, message, fail_silently=False):
    if not settings.MANAGERS:
        return
    send_mail(
        subject=settings.EMAIL_SUBJECT_PREFIX + subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        recipient_list=[a[1] for a in settings.MANAGERS],
        fail_silently=fail_silently,
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

def mail_admins(subject, message, fail_silently=False):
    if not settings.ADMINS:
        return
    send_mail(
        subject=settings.EMAIL_SUBJECT_PREFIX + subject,
        message=message,
        from_email=settings.SERVER_EMAIL,
        recipient_list=[a[1] for a in settings.ADMINS],
        fail_silently=fail_silently,
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
