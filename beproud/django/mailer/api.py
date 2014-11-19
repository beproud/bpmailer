#:coding=utf-8:

import sys
import traceback
import logging
from StringIO import StringIO

from email import Encoders, charset, generator, message_from_string
from email.Utils import formatdate
from email.MIMEBase import MIMEBase
from email.mime.text import MIMEText
from email.message import Message

import django
from django.core import mail as django_mail
from django.template.loader import render_to_string
from django.conf import settings

from beproud.django.mailer.signals import mail_pre_send, mail_post_send

# NOTE: CHARSETSや、ALIASESを先に登録しておかないといけない
from beproud.django.mailer.models import *  # NOQA

__version__ = '0.35'

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
    'SafeMIMEMessage',
    'SafeMIMEText',
    'SafeMIMEMultipart',
    'BadHeaderError',
)

utf8_charset = charset.Charset('UTF-8')

# ガラケの場合は base64 じゃないとダメなやつが多いので、デフォルトで BASE64を使う。
if not getattr(settings, "EMAIL_USE_BASE64_FOR_UTF8", True):
    # Don't BASE64-encode UTF-8 messages so that we avoid unwanted attention from
    # some spam filters.
    utf8_charset.body_encoding = None

if django.VERSION > (1, 6):
    _old_safemimetext = django_mail.SafeMIMEText

    class SafeMIMEText(_old_safemimetext):
        def __init__(self, text, subtype, charset):
            self.encoding = charset
            # NOTE: utf8 でも utf-8 でも対応する
            if charset.upper().replace("-", "") == 'UTF8':
                # Unfortunately, Python doesn't support setting a Charset instance
                # as MIMEText init parameter (http://bugs.python.org/issue16324).
                # We do it manually and trigger re-encoding of the payload.
                MIMEText.__init__(self, text, subtype, None)
                del self['Content-Transfer-Encoding']
                self.set_payload(text, utf8_charset)
                self.replace_header('Content-Type', 'text/%s; charset="%s"'
                                    % (subtype, utf8_charset.get_output_charset()))
            else:
                MIMEText.__init__(self, text, subtype, charset)
else:
    class SafeMIMEText(MIMEText):

        def __init__(self, text, subtype, charset):
            self.encoding = charset
            if charset.upper().replace("-", "") == 'UTF8':
                # Unfortunately, Python doesn't support setting a Charset instance
                # as MIMEText init parameter (http://bugs.python.org/issue16324).
                # We do it manually and trigger re-encoding of the payload.
                MIMEText.__init__(self, text, subtype, None)
                del self['Content-Transfer-Encoding']
                self.set_payload(text, utf8_charset)
                self.replace_header('Content-Type', 'text/%s; charset="%s"'
                                    % (subtype, utf8_charset.get_output_charset()))
            else:
                MIMEText.__init__(self, text, subtype, charset)

        def __setitem__(self, name, val):
            name, val = forbid_multi_line_headers(name, val, self.encoding)
            MIMEText.__setitem__(self, name, val)

        def as_string(self, unixfrom=False, linesep='\n'):
            """Return the entire formatted message as a string.
            Optional `unixfrom' when True, means include the Unix From_ envelope
            header.

            This overrides the default as_string() implementation to not mangle
            lines that begin with 'From '. See bug #13433 for details.
            """
            fp = StringIO()
            g = generator.Generator(fp, mangle_from_=False)
            g.flatten(self, unixfrom=unixfrom)
            return fp.getvalue()

        as_bytes = as_string

django_mail.SafeMIMEText = SafeMIMEText
try:
    from django.core.mail import message as django_mail_message
    django_mail_message.SafeMIMEText = SafeMIMEText
except ImportError:
    pass

SafeMIMEMultipart = django_mail.SafeMIMEMultipart
BadHeaderError = django_mail.BadHeaderError
get_connection = django_mail.get_connection
forbid_multi_line_headers = django_mail.forbid_multi_line_headers
make_msgid = django_mail.make_msgid

# NOTE: Django 1.4 では、SMTPConnectionはもうないので、
#       なかったらスルーする
if hasattr(django_mail, 'SMTPConnection'):
    SMTPConnection = django_mail.SMTPConnection
    __all__ = __all__ + ('SMTPConnection',)

# NOTE: Django 1.6 以上の SafeMimeMessage
if hasattr(django_mail, 'SafeMIMEMessage'):
    SafeMIMEMessage = django_mail.SafeMIMEMessage
else:
    from email.mime.message import MIMEMessage

    class SafeMIMEMessage(MIMEMessage):
        def __setitem__(self, name, val):
            # message/rfc822 attachments must be ASCII
            name, val = forbid_multi_line_headers(name, val, 'ascii')
            MIMEMessage.__setitem__(self, name, val)


logger = logging.getLogger(getattr(settings, "EMAIL_LOGGER", ""))


class EmailMessage(django_mail.EmailMessage):
    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
                 connection=None, attachments=None, headers=None, cc=None):
        super(EmailMessage, self).__init__(
            subject=subject,
            body=body,
            from_email=from_email,
            to=to,
            bcc=bcc,
            connection=connection,
            attachments=attachments,
            headers=headers,
        )
        # NOTE: Django 1.2 の場合の cc に対応
        if cc:
            assert not isinstance(cc, basestring), '"cc" argument must be a list or tuple'
            self.cc = list(cc)
        else:
            self.cc = []

    def get_connection(self, fail_silently=False):
        if not self.connection:
            self.connection = get_connection(fail_silently=fail_silently)
        return self.connection

    # NOTE: Django 1.2 の場合の cc に対応
    def recipients(self):
        """
        Returns a list of all recipients of the email (includes direct
        addressees as well as Cc and Bcc entries).
        """
        return self.to + self.cc + self.bcc

    def message(self):
        encoding = self.encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
        msg = SafeMIMEText(self.body, self.content_subtype, encoding)
        msg = self._create_message(msg)
        msg['Subject'] = self.subject
        msg['From'] = self.extra_headers.get('From', self.from_email)
        msg['To'] = ', '.join(self.to)
        if self.cc:
            msg['Cc'] = ', '.join(self.cc)

        # Email header names are case-insensitive (RFC 2045), so we have to
        # accommodate that when doing comparisons.
        header_names = [key.lower() for key in self.extra_headers]
        if 'date' not in header_names:
            msg['Date'] = formatdate(localtime=getattr(settings, "EMAIL_USE_LOCALTIME", False))
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

        If the mimetype is message/rfc822, content may be an
        email.Message or EmailMessage object, as well as a str.
        """
        basetype, subtype = mimetype.split('/', 1)
        if basetype == 'text':
            encoding = self.encoding or getattr(settings, "EMAIL_CHARSET",
                                                settings.DEFAULT_CHARSET)
            attachment = SafeMIMEText(content, subtype, encoding)
        elif basetype == 'message' and subtype == 'rfc822':
            # Bug #18967: per RFC2046 s5.2.1, message/rfc822 attachments
            # must not be base64 encoded.
            if isinstance(content, EmailMessage):
                # convert content into an email.Message first
                content = content.message()
            elif not isinstance(content, Message):
                # For compatibility with existing code, parse the message
                # into an email.Message object if it is not one already.
                content = message_from_string(content)

            attachment = SafeMIMEMessage(content, subtype)
        else:
            # Encode non-text attachments with base64.
            attachment = MIMEBase(basetype, subtype)
            attachment.set_payload(content)
            Encoders.encode_base64(attachment)
        return attachment

    def send(self, *args, **kwargs):
        mail_pre_send.send(sender=self, message=self)
        super(EmailMessage, self).send(*args, **kwargs)
        mail_post_send.send(sender=self, message=self)


class EmailMultiAlternatives(EmailMessage):
    """
    A version of EmailMessage that makes it easy to send multipart/alternative
    messages. For example, including text and HTML versions of the text is
    made easier.
    """
    alternative_subtype = 'alternative'

    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
                 connection=None, attachments=None, headers=None, alternatives=None,
                 cc=None):
        """
        Initialize a single email message (which can be sent to multiple
        recipients).

        All strings used to create the message can be unicode strings (or UTF-8
        bytestrings). The SafeMIMEText class will handle any necessary encoding
        conversions.
        """
        super(EmailMultiAlternatives, self).__init__(subject, body, from_email, to, bcc,
                                                     connection, attachments, headers, cc)
        self.alternatives = alternatives or []

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
              fail_silently=False, auth_user=None, auth_password=None, encoding=None,
              connection=None, html_message=None, cc=None, bcc=None, attachments=None):
    """
    Sends an email message.

    Arguments
    --------------

    * subject           -- The email subject
    * message           -- The email message body text
    * from_email        -- The sender. Can be an email address or formatted name and address.
                           Example: Ian Lewis <ian@example.com>
                           Example: ian@example.com
    * recipient_list    -- A list of recipients. This is formatted the same as the from_email.

    Keyword Arguments
    ----------------------
    fail_silently       -- A boolean indicating whether errors when sending emails should be
                           squelched. If True errors are squelched and logged. If False errors
                           are raised as Exceptions as normal. Default is False.
    auth_user           -- The username to use when authenticating with the SMTP server.
                           This argument is ignored if a connection object is provided.
                           Defaults to the EMAIL_HOST_USER in settings.py
    auth_password       -- The password to use when authenticating with the SMTP server.
                           This argument is ignored if a connection object is provided.
                           Defaults to the EMAIL_HOST_PASSWORD in settings.py
    encoding            -- The character encoding to use in the email.
                           Defaults to the EMAIL_CHARSET or DEFAULT_CHARSET in settings.py
    connection          -- The connection object to use when sending the email as returned
                           by get_connection()
    html_message        -- The html body part of the email. If provided the email is encoded
                           as a multi-part email with an html part containing the html body.
                           Useful for sending html emails.
    cc                  -- The cc email recipient list.
    bcc                 -- The bcc recipient list.
    attachments         -- A list of two/three tuples used as attachments for the email.
                           The fields in the tuple are as follows:

                               - A filename
                               - A str object containing the file content.
                               - The mimetype for the file (optional but recommended.)
                                 If the mimetype is not provided it is guessed.
    """

    if settings.DEBUG and hasattr(settings, "EMAIL_ALL_FORWARD"):
        recipient_list = [settings.EMAIL_ALL_FORWARD]
        from_email = settings.EMAIL_ALL_FORWARD

    connection = connection or get_connection(username=auth_user, password=auth_password,
                                              fail_silently=fail_silently)
    if html_message:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
            cc=cc,
            bcc=bcc,
            connection=connection,
        )
        msg.attach_alternative(html_message, "text/html")
    else:
        msg = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
            cc=cc,
            bcc=bcc,
            connection=connection,
        )

    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)

    msg.encoding = encoding
    return_val = msg.send()
    log_message(msg, return_val)
    return return_val


def _render_mail_template(template_name, extra_context=None):
    """
    Renders the template and returns the resulting text.
    """
    context = {}
    context.update(getattr(settings, "EMAIL_DEFAULT_CONTEXT", {}))
    context.update(extra_context or {})
    return render_to_string(template_name, context)


def render_message(template_name, extra_context={}):
    """
    Renders a text email message from a template and returns a two
    tuple containing the subject and body of the message.

    The contents of the EMAIL_DEFAULT_CONTENT setting are
    passed to the template when it is rendered but can be
    overridden.
    """
    mail_text = _render_mail_template(template_name, extra_context)
    rendered_mail = mail_text.replace(u"\r\n", u"\n").replace(u"\r", u"\n").split(u"\n")
    return rendered_mail[0], "\n".join(rendered_mail[1:])


def send_template_mail(template_name, from_email, recipient_list, extra_context={},
                       fail_silently=False, auth_user=None, auth_password=None, encoding=None,
                       connection=None, html_template_name=None, cc=None, bcc=None,
                       attachments=None):
    u"""
    Send an email using a django template. The template should be formatted
    so that the first line of the template is the subject. All subsequent lines
    are used as the body of the email message. The easiest way to create a template is to
    extend the "mail.tpl" template provided with bpmailer and specify the subject and body
    blocks.

    You can also specify the "mail.tpl" template and add the "subject" and "body" to
    the extra_context argument to use bpmailer's default template.

    Arguments
    --------------

    * template_name     -- The name of the Django template to use to render the email.
    * from_email        -- The sender. Can be an email address or formatted name and address.
                           Example: Ian Lewis <ian@example.com>
                           Example: ian@example.com
    * recipient_list    -- A list of recipients. This is formatted the same as the from_email.
    * extra_context     -- An dictionary of extra data that is added to the context when
                           rendering the template.

    Keyword Arguments
    ----------------------
    fail_silently       -- A boolean indicating whether errors when sending emails should be
                           squelched. If True errors are squelched and logged. If False errors
                           are raised as Exceptions as normal. Default is False.
    auth_user           -- The username to use when authenticating with the SMTP server.
                           This argument is ignored if a connection object is provided.
                           Defaults to the EMAIL_HOST_USER in settings.py
    auth_password       -- The password to use when authenticating with the SMTP server.
                           This argument is ignored if a connection object is provided.
                           Defaults to the EMAIL_HOST_PASSWORD in settings.py
    encoding            -- The character encoding to use in the email.
                           Defaults to the EMAIL_CHARSET or DEFAULT_CHARSET in settings.py
    connection          -- The connection object to use when sending the email as returned
                           by get_connection()
    html_template_name  -- The template for the html body part of the email. If provided
                           the email is encoded as a multi-part email with an html part
                           containing the html body.  Useful for sending html emails.
    cc                  -- The cc email recipient list.
    bcc                 -- The bcc recipient list.
    attachments         -- A list of two/three tuples used as attachments for the email.
                           The fields in the tuple are as follows:

                               - A filename
                               - A str object containing the file content.
                               - The mimetype for the file (optional but recommended.)
                                 If the mimetype is not provided it is guessed.
    """
    if not isinstance(recipient_list, list) and not isinstance(recipient_list, tuple):
        recipient_list = [recipient_list]

    html_message = None
    try:
        subject, message = render_message(template_name, extra_context)
        if html_template_name:
            html_message = _render_mail_template(html_template_name, extra_context)
    except Exception:
        log_exception("Mail Error")
        if fail_silently:
            return
        else:
            raise

    return send_mail(
        subject=subject,
        message=message,
        recipient_list=recipient_list,
        cc=cc,
        bcc=bcc,
        from_email=from_email,
        fail_silently=fail_silently,
        auth_user=auth_user,
        auth_password=auth_password,
        encoding=encoding,
        connection=connection,
        html_message=html_message,
        attachments=attachments,
    )


def send_mass_mail(datatuple, fail_silently=False, auth_user=None,
                   auth_password=None, encoding=None, connection=None):
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
    connection = connection or get_connection(username=auth_user, password=auth_password,
                                              fail_silently=fail_silently)

    def _message(args):
        if isinstance(args, EmailMessage):
            return args
        if len(args) > 4:
            subject, body, sender, recipient, charset = args
        else:
            subject, body, sender, recipient = args
            charset = encoding or None
        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=sender,
            to=recipient,
            connection=connection,
        )
        if charset:
            message.encoding = charset
        return message

    messages = [_message(d) for d in datatuple]

    for message in messages:
        mail_pre_send.send(sender=message, message=message)
    return_val = connection.send_messages(messages)
    for message in messages:
        mail_post_send.send(sender=message, message=message)
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


def mail_managers_template(template_name, extra_context={}, fail_silently=False, encoding=None):
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
    tb = ''.join(traceback.format_exception(sys.exc_info()[0],
                 sys.exc_info()[1], sys.exc_info()[2]))
    logger.exception(msg + tb)
