# vim:fileencoding=utf8

import re
from datetime import datetime,date,timedelta
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Header import Header
from email.Utils import formatdate, parseaddr, formataddr

from django.core import mail
from django.utils.encoding import smart_str
from django import template
from django.template.loader import render_to_string
from django.conf import settings

__all__ = (
    'send_mail',
    'send_basic_mail',
    'send_template_mail',
    'mail_managers',
    'mail_managers_template',
    'mail_admins',
    'render_message',
    'EncodedEmailMessage',
)

# Python charset => mail header charset mapping
# TODO: Add more encodings
CHARSET_MAP = getattr(settings, "EMAIL_HEADER_CHARSET_MAP", {
    # UTF-8
    "utf8": "UTF-8",
    "utf_8": "UTF-8",
    "U8": "UTF-8",
    "UTF": "UTF-8",
    "utf8": "UTF-8",

    # Shift-JIS
    "cp932": "SHIFT-JIS",
    "932": "SHIFT-JIS",
    "ms932": "SHIFT-JIS",
    "mskanji": "SHIFT-JIS",
    "ms-kanji": "SHIFT-JIS",

    "shift_jis": "SHIFT-JIS",
    "csshiftjis": "SHIFT-JIS",
    "shiftjis": "SHIFT-JIS",
    "sjis": "SHIFT-JIS",
    "s_jis": "SHIFT-JIS",
    
    "shift_jis_2004": "SHIFT-JIS",
    "shiftjis2004": "SHIFT-JIS",
    "sjis_2004": "SHIFT-JIS",
    "sjis2004": "SHIFT-JIS",
    
    "shift_jisx0213": "SHIFT-JIS",
    "shiftjisx0213": "SHIFT-JIS",
    "sjisx0213": "SHIFT-JIS",
    "s_jisx0213": "SHIFT-JIS",

    # ISO-2022-JP
    "iso2022_jp": "ISO-2022-JP",
    "scsiso2022jp": "ISO-2022-JP",
    "iso2022jp": "ISO-2022-JP",
    "iso-2022-jp": "ISO-2022-JP",
    "iso-2022-jp": "ISO-2022-JP",
    "iso-2022-jp-1": "ISO-2022-JP",
    "iso2022_jp_2": "ISO-2022-JP",
    "iso2022jp-2": "ISO-2022-JP",
    "iso-2022-jp-2": "ISO-2022-JP",
    "iso-2022-jp-2": "ISO-2022-JP",
    "iso2022_jp_2004": "ISO-2022-JP",
    "iso2022jp-2004": "ISO-2022-JP",
    "iso-2022-jp-2004": "ISO-2022-JP",
    "iso2022_jp_3": "ISO-2022-JP",
    "iso2022jp-3": "ISO-2022-JP",
    "iso-2022-jp-3": "ISO-2022-JP",
    "iso2022_jp_ext": "ISO-2022-JP",
    "iso2022jp-ext": "ISO-2022-JP",
    "iso-2022-jp-ext": "ISO-2022-JP",
})

def format_header(name, val, encoding=None):
    encoding = encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
    if '\n' in val or '\r' in val:
        raise mail.BadHeaderError("Header values can't contain newlines (got %r for header %r)" % (val, name)) 
    if name.lower() in ('to', 'from', 'cc'):
        result = []
        for item in val.split(', '):
            nm, addr = parseaddr(item)
            nm = str(Header(nm.encode(encoding,'replace'), CHARSET_MAP.get(encoding, encoding)))
            result.append(formataddr((nm, str(addr))))
        val = ', '.join(result)
    elif name.lower() == 'subject':
        val = Header(val.encode(encoding,'replace'), CHARSET_MAP.get(encoding, encoding))
    else:
        val = Header(val, CHARSET_MAP.get(encoding, encoding))
    
    return name,val

class EncodedMIMEText(MIMEText):
    def __setitem__(self, name, val):
        if name.lower() in ('subject', 'to', 'from', 'cc'):
            name,val = format_header(name, val, smart_str(self._charset))
        MIMEText.__setitem__(self, name, val)

class EncodedMIMEMultipart(MIMEMultipart):
    def __setitem__(self, name, val):
        if name.lower() in ('subject', 'to', 'from', 'cc'):
            name,val = format_header(name, val, smart_str(self._charset))
        MIMEText.__setitem__(self, name, val)

class EncodedEmailMessage(mail.EmailMessage):
    def message(self):
        encoding = self.encoding or getattr(settings, "EMAIL_CHARSET", settings.DEFAULT_CHARSET)
        msg = EncodedMIMEText(smart_str(self.body, encoding, 'replace'),
                           self.content_subtype, CHARSET_MAP.get(encoding, encoding))
        if self.attachments:
            body_msg = msg
            msg = EncodedMIMEMultipart(_subtype=self.multipart_subtype)
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
            msg['Message-ID'] = mail.make_msgid()
        for name, value in self.extra_headers.items():
            msg[name] = value
        return msg

def send_basic_mail(subject, body, recipient_list, from_email=settings.SERVER_EMAIL, fail_silently=True,
              fail_silently=False, auth_user=None, auth_password=None, encoding=None):

    from django.core.mail import SMTPConnection

    if settings.DEBUG and hasattr(settings, "EMAIL_ALL_FORWARD"):
        recipient_list = [settings.EMAIL_ALL_FORWARD]
        from_email = settings.EMAIL_ALL_FORWARD

    connection = SMTPConnection(username=auth_user, password=auth_password,
                                fail_silently=fail_silently)
    msg = EncodedEmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to_list,
    )
    if encoding is not None:
        msg.encoding = encoding 
    return msg.send(fail_silently)

def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None):
    send_basic_mail(
        subject=subject,
        body=body,
        to_list=recipient_list,
        from_email=from_email,
        fail_silently=fail_silently,
        auth_user=auth_user,
        auth_password=auth_password,
    )

def render_message(template_name, extra_context={}):
    """
    メールメッセージをテンプレートからレンダーする
    subject,bodyを返す 
    """
    from django.template.loader import render_to_string
    context = getattr(settings, "EMAIL_DEFAULT_CONTEXT", {})
    context.update(extra_context)

    rendered_mail = render_to_string(template_name, context).replace(u"\r\n",u"\n").replace(u"\r",u"\n").split(u"\n")
    return rendered_mail[0], "\n".join(rendered_mail[1:])
    
def send_template_mail(template_name, recipient_list, extra_context={},
                       from_email=settings.SERVER_EMAIL, fail_silently=True, encoding=None):
    u"""
    メールを送信する
    """
    try:
        #TODO: logging 
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
    except:
        if not fail_silently:
            raise

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
