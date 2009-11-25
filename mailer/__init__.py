# vim:fileencoding=utf8

# TODO: Move to mailer app
# Mail and notice rendering should be separate

import re
from datetime import datetime,date,timedelta
import smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Header import Header
from email.Utils import formatdate, parseaddr, formataddr

from django.core import mail
from django.utils.encoding import smart_str
from django import template
from django.template.loader import render_to_string
from django.conf import settings

# Python charset => mail header charset mapping
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
    encoding = encoding or settings.EMAIL_CHARSET_ENCODING
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

class JPMIMEText(MIMEText):
    def __setitem__(self, name, val):
        if name.lower() in ('subject', 'to', 'from', 'cc'):
            name,val = format_header(name, val, smart_str(self._charset))
        MIMEText.__setitem__(self, name, val)

class JPMIMEMultipart(MIMEMultipart):
    def __setitem__(self, name, val):
        if name.lower() in ('subject', 'to', 'from', 'cc'):
            name,val = format_header(name, val, smart_str(self._charset))
        MIMEText.__setitem__(self, name, val)

class JPEmailMessage(mail.EmailMessage):
    def message(self):
        encoding = self.encoding or settings.EMAIL_CHARSET_ENCODING
        msg = JPMIMEText(smart_str(self.body, encoding, 'replace'),
                           self.content_subtype, CHARSET_MAP.get(encoding, encoding))
        if self.attachments:
            body_msg = msg
            msg = JPMIMEMultipart(_subtype=self.multipart_subtype)
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

def send_mail_basic(subject,body,to_list,from_mail=settings.MAIL_FROM, fail_silently=True, encoding=None):
    if settings.DEBUG and hasattr(settings, "ALL_MAIL_FORWARD"):
        for index in xrange(len(to_list)):
            to_list[index] = settings.ALL_MAIL_FORWARD
        from_mail = settings.ALL_MAIL_FORWARD

    msg = JPEmailMessage(
        subject=subject,
        body=body,
        from_email=from_mail,
        to=to_list,
    )
    if encoding is not None:
        msg.encoding = encoding 
    return msg.send(fail_silently)

def send_mail(template_name, to, extra_context={}, from_mail=settings.MAIL_FROM, fail_silently=True, encoding=None):
    u"""
    メールを送信する
    
    to は User OR メアド(str)
    """
    from django.template.loader import render_to_string
    from account.models import User

    #TODO: MailLog
    context = {
        'domain': settings.DOMAIN, 
        'service_name' : u"日経ウーマンオンライン女子部",
        'symbol' : u"[日経WOL女子部]",
    }
    if isinstance(to, User):
        to_list = [to.email]
        extra_context.update({
            'user': to,
        })
    elif isinstance(to, list) or isinstance(to, tuple):
        to_list = to
    else:
        to_list = [to]
    
    context.update(extra_context)

    rendered_mail = render_to_string(template_name, context).replace(u"\r\n",u"\n").replace(u"\r",u"\n").split(u"\n")
    subject,body = rendered_mail[0], "\n".join(rendered_mail[1:])
    return send_mail_basic(subject, body, to_list, from_mail=from_mail, fail_silently=fail_silently, encoding=encoding)

def mail_managers(template_name, extra_context={}, from_mail=settings.MAIL_FROM, fail_silently=True, encoding=None):
    return send_mail(
        template_name=template_name,
        to=dict(settings.MANAGERS).values(),
        extra_context=extra_context,
        from_mail=from_mail,
        fail_silently=fail_silently,
        encoding=encoding,
    )

def mail_admins(subject, message, fail_silently=False):
    return mail.mail_admins(subject=subject, message=message, fail_silently=fail_silently)
