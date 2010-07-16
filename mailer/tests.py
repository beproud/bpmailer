# vim:fileencoding=utf-8
from django.test import TestCase as DjangoTestCase
from django.core import mail as django_mail
from django.conf import settings

from mailer import *

class MailTestCase(object):
    DEFAULT_CHARSET = None
    EMAIL_CHARSET = None
    EMAIL_CHARSETS = None
    EMAIL_CHARSET_ALIASES = None
    EMAIL_CHARSET_CODECS = None

    def assertEllipsisMatch(self, first, second, msg=None):
        from doctest import _ellipsis_match
        if not _ellipsis_match(first, second):
            raise self.failureException, \
                (msg or '%r != %r' % (first, second))
    
    def setUp(self):
        self._old_DEFAULT_CHARSET = settings.DEFAULT_CHARSET
        settings.DEFAULT_CHARSET = self.DEFAULT_CHARSET

        for setting_name in ["EMAIL_CHARSET", "EMAIL_CHARSETS", "EMAIL_CHARSET_ALIASES", "EMAIL_CHARSET_CODECS"]:
            setting_value = getattr(self, setting_name, None)
            if setting_value:
                setattr(self, "_old_"+setting_name, getattr(settings, setting_name, None))
                setattr(settings, setting_name, setting_value)

    def tearDown(self):
        settings.DEFAULT_CHARSET = self._old_DEFAULT_CHARSET
        for setting_name in ["EMAIL_CHARSET", "EMAIL_CHARSETS", "EMAIL_CHARSET_ALIASES", "EMAIL_CHARSET_CODECS"]:
            old_setting_value = getattr(self, "_old_"+setting_name, None)
            if old_setting_value is None:
                if hasattr(settings, setting_name):
                    delattr(settings, setting_name)
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

    def test_send_basic_mail_encoding(self):
        send_basic_mail(
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
        settings.DEFAULT_CHARSET = 'utf-8'
         
        send_basic_mail(
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
        send_basic_mail(
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

        message = django_mail.outbox[0].message()
        self.assertEquals(str(message['Subject']), '=?UTF-8?b?5Lu25ZCN?=')
        self.assertEquals(str(message['To']), '=?UTF-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEquals(str(message['From']), '=?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>')
