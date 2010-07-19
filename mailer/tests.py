# vim:fileencoding=utf-8
from django.test import TestCase as DjangoTestCase
from django.core import mail as django_mail
from django.conf import settings

from mailer import *

AVAILABLE_SETTINGS = [
    "EMAIL_CHARSET", "EMAIL_CHARSETS",
    "EMAIL_CHARSET_ALIASES", "EMAIL_CHARSET_CODECS",
    "EMAIL_ALL_FORWARD",
]

class MailTestCase(object):
    DEFAULT_CHARSET = None
    DEBUG = None
    EMAIL_CHARSET = None
    EMAIL_CHARSETS = None
    EMAIL_CHARSET_ALIASES = None
    EMAIL_CHARSET_CODECS = None
    EMAIL_ALL_FORWARD = None

    def assertEllipsisMatch(self, first, second, msg=None):
        from doctest import _ellipsis_match
        if not _ellipsis_match(first, second):
            raise self.failureException, \
                (msg or '%r != %r' % (first, second))
    
    def setUp(self):
        from mailer.models import init_mailer
        from email import charset

        self._old_email_CHARSETS = charset.CHARSETS
        self._old_email_ALIASES = charset.ALIASES
        self._old_email_CODEC_MAP = charset.ALIASES

        if self.DEFAULT_CHARSET is not None:
            self._old_DEFAULT_CHARSET = settings.DEFAULT_CHARSET
            settings.DEFAULT_CHARSET = self.DEFAULT_CHARSET
        if self.DEBUG is not None:
            self._old_DEBUG = settings.DEBUG
            settings.DEBUG = self.DEBUG

        for setting_name in AVAILABLE_SETTINGS:
            setting_value = getattr(self, setting_name, None)
            if setting_value:
                setattr(self, "_old_"+setting_name, getattr(settings, setting_name, None))
                setattr(settings, setting_name, setting_value)
        init_mailer()

    def tearDown(self):
        from email import charset

        charset.CHARSETS = self._old_email_CHARSETS
        charset.ALIASES = self._old_email_ALIASES
        charset.ALIASES = self._old_email_CODEC_MAP

        if self.DEFAULT_CHARSET is not None:
            settings.DEFAULT_CHARSET = self._old_DEFAULT_CHARSET
        if self.DEBUG is not None:
            settings.DEBUG = self._old_DEBUG

        for setting_name in AVAILABLE_SETTINGS:
            old_setting_value = getattr(self, "_old_"+setting_name, None)
            if old_setting_value is None:
                if hasattr(settings, setting_name):
                    delattr(settings._wrapped, setting_name)
            else:
                setattr(settings, setting_name, old_setting_value)

class EncodingTestCaseUTF8(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'utf-8'

    def test_send_mail(self):
        send_mail(
           u'件名',
           u'本文',
           'example-from@example.net',
           ['example@example.net'],
       )
        self.assertEquals(len(django_mail.outbox), 1)
        self.assertEquals(django_mail.outbox[0].body, u'本文')

        message = django_mail.outbox[0].message() 
        self.assertEquals(str(message['Subject']), '=?UTF-8?b?5Lu25ZCN?=')
        self.assertEquals(str(message['To']), 'example@example.net')
        self.assertEquals(str(message['From']), 'example-from@example.net')

class EncodingTestCaseISO2022JP(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'utf-8'
    EMAIL_CHARSET = 'iso-2022-jp'
    # TODO: Set ALIASES and CODECS

    def test_send_mail_encoding(self):
        send_mail(
           u'件名',
           u'本文',
           'example-from@example.net',
           ['example@example.net'],
           encoding="utf-8",
        )
        self.assertEquals(len(django_mail.outbox), 1)
        self.assertEquals(django_mail.outbox[0].body, u'本文')

        message = django_mail.outbox[0].message()
        self.assertEquals(str(message['Subject']), '=?UTF-8?b?5Lu25ZCN?=')
        self.assertEquals(str(message['To']), 'example@example.net')
        self.assertEquals(str(message['From']), 'example-from@example.net')
    
    def test_email_charset(self):
        send_mail(
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example@example.net>'],
        )
        
        self.assertEquals(len(django_mail.outbox), 1)
        self.assertEquals(django_mail.outbox[0].body, u'本文')

        message = django_mail.outbox[0].message()
        self.assertEquals(str(message['Subject']), '=?ISO-2022-JP?b?GyRCN29MPhsoQg==?=')
        self.assertEquals(str(message['To']), '=?ISO-2022-JP?b?GyRCMDhAaBsoQg==?= <example@example.net>')
        self.assertEquals(str(message['From']), '=?ISO-2022-JP?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>')

    def test_email_charset_strict(self):
        send_mail(
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example@example.net>'],
        )
        
        message = django_mail.outbox[0].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="ISO-2022-JP"\n'''
            '''Content-Transfer-Encoding: 7bit\n'''
            '''Subject: =?ISO-2022-JP?b?GyRCN29MPhsoQg==?=\n'''
            '''From: =?ISO-2022-JP?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>\n'''
            '''To: =?ISO-2022-JP?b?GyRCMDhAaBsoQg==?= <example@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''\x1b$BK\\J8\x1b(B''',
            message.as_string())

class EmailAllForwardTestCase(MailTestCase, DjangoTestCase):
    DEBUG = True
    EMAIL_ALL_FORWARD="all-forward@example.net"

    def test_email_all_forward(self):
        send_mail(
           u'件名',
           u'本文',
           'example-from@example.net',
           ['example@example.net'],
       )
        self.assertEquals(len(django_mail.outbox), 1)
        self.assertEquals(django_mail.outbox[0].body, u'本文')

        message = django_mail.outbox[0].message() 
        self.assertEquals(str(message['Subject']), '=?UTF-8?b?5Lu25ZCN?=')
        self.assertEquals(str(message['To']), 'all-forward@example.net')
        self.assertEquals(str(message['From']), 'all-forward@example.net')

class EmailAllForwardTestCase2(MailTestCase, DjangoTestCase):
    DEBUG = False
    EMAIL_ALL_FORWARD="all-forward@example.net"

    def test_email_all_forward(self):
        send_mail(
           u'件名',
           u'本文',
           'example-from@example.net',
           ['example@example.net'],
       )
        self.assertEquals(len(django_mail.outbox), 1)
        self.assertEquals(django_mail.outbox[0].body, u'本文')

        message = django_mail.outbox[0].message() 
        self.assertEquals(str(message['Subject']), '=?UTF-8?b?5Lu25ZCN?=')
        self.assertEquals(str(message['To']), 'example@example.net')
        self.assertEquals(str(message['From']), 'example-from@example.net')

class TemplateTestCase(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'utf-8'
    # TODO: Set ALIASES and CODECS

    def test_template_mail(self):
        send_template_mail(
            u'mailer/mail.tpl',
            u'差出人 <example-from@example.net>',
            [u'宛先 <example@example.net>'],
            extra_context={
                'subject': u'件名',
                'body': u'本文',
            },
            fail_silently=False,
        )

        self.assertEquals(len(django_mail.outbox), 1)
        self.assertEquals(django_mail.outbox[0].body, u'本文\n')

        message = django_mail.outbox[0].message()
        self.assertEquals(str(message['Subject']), '=?UTF-8?b?5Lu25ZCN?=')
        self.assertEquals(str(message['To']), '=?UTF-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEquals(str(message['From']), '=?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>')

    def test_multi_line_subject(self):
        send_template_mail(
            u'mailer/mail.tpl',
            u'差出人 <example-from@example.net>',
            [u'宛先 <example@example.net>'],
            extra_context={
                'subject': u'これは\r改行\nの\nある\r\n件名',
                'body': u'本文',
            },
            fail_silently=False,
        )

        self.assertEquals(len(django_mail.outbox), 1)

        mail_message = django_mail.outbox[0]
        self.assertEquals(mail_message.subject, u'これは改行のある件名')
        self.assertEquals(mail_message.body, u'本文\n')

        message = mail_message.message()
        self.assertEquals(str(message['Subject']), '=?UTF-8?b?44GT44KM44Gv5pS56KGM44Gu44GC44KL5Lu25ZCN?=')
        self.assertEquals(str(message['To']), '=?UTF-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEquals(str(message['From']), '=?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>')
