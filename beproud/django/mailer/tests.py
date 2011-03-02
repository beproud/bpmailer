# vim:fileencoding=utf-8
import os
import time
import logging
from logging.handlers import BufferingHandler

from django.test import TestCase as DjangoTestCase
from django.core import mail as django_mail
from django.conf import settings

from beproud.django.mailer.backends.base import BaseEmailBackend
from beproud.django.mailer import *

# Suppress logging
logging.getLogger("").handlers = [BufferingHandler(0)]

class EmailError(Exception):
    pass

class ErrorEmailBackend(BaseEmailBackend):
    def _send_message(self, email_message):
        raise EmailError(u"ERROR")

AVAILABLE_SETTINGS = [
    "EMAIL_CHARSET", "EMAIL_CHARSETS",
    "EMAIL_CHARSET_ALIASES", "EMAIL_CHARSET_CODECS",
    "EMAIL_ALL_FORWARD", "EMAIL_USE_LOCALTIME",
    "EMAIL_BACKEND",
]

class MailTestCase(object):
    ADMINS = (('Admin', 'admin@example.net'),)
    MANAGERS = (('Manager', 'manager@example.net'),)
    TIME_ZONE = None
    DEFAULT_CHARSET = None
    DEBUG = None
    EMAIL_CHARSET = None
    EMAIL_CHARSETS = None
    EMAIL_CHARSET_ALIASES = None
    EMAIL_CHARSET_CODECS = None
    EMAIL_ALL_FORWARD = None
    EMAIL_USE_LOCALTIME = None
    EMAIL_BACKEND = 'beproud.django.mailer.backends.locmem.EmailBackend' 

    def assertEllipsisMatch(self, first, second, msg=None):
        from doctest import _ellipsis_match
        if not _ellipsis_match(first, second):
            raise self.failureException, \
                (msg or '%r != %r' % (first, second))
    
    def setUp(self):
        from beproud.django.mailer.models import init_mailer
        from email import charset

        self._old_email_CHARSETS = charset.CHARSETS
        self._old_email_ALIASES = charset.ALIASES
        self._old_email_CODEC_MAP = charset.ALIASES

        self._old_ADMINS = settings.ADMINS
        if self.ADMINS is not None:
            settings.ADMINS = self.ADMINS
        self._old_MANAGERS = settings.MANAGERS
        if self.MANAGERS is not None:
            settings.MANAGERS = self.MANAGERS
        self._old_DEFAULT_CHARSET = settings.DEFAULT_CHARSET
        if self.DEFAULT_CHARSET is not None:
            settings.DEFAULT_CHARSET = self.DEFAULT_CHARSET
        self._old_DEBUG = settings.DEBUG
        if self.DEBUG is not None:
            settings.DEBUG = self.DEBUG
        self._old_TIME_ZONE = settings.TIME_ZONE
        if self.TIME_ZONE is not None:
            settings.TIME_ZONE = self.TIME_ZONE

        os.environ['TZ'] = settings.TIME_ZONE
        time.tzset()

        for setting_name in AVAILABLE_SETTINGS:
            setting_value = getattr(self, setting_name, None)
            if setting_value:
                setattr(self, "_old_"+setting_name, getattr(settings, setting_name, None))
                setattr(settings, setting_name, setting_value)
        init_mailer()

    def tearDown(self):
        from email import charset
        from beproud.django.mailer.signals import mail_pre_send, mail_post_send
        mail_pre_send.recievers = []
        mail_post_send.recievers = []

        charset.CHARSETS = self._old_email_CHARSETS
        charset.ALIASES = self._old_email_ALIASES
        charset.ALIASES = self._old_email_CODEC_MAP

        if self.DEFAULT_CHARSET != self._old_DEFAULT_CHARSET:
            settings.DEFAULT_CHARSET = self._old_DEFAULT_CHARSET
        if self.DEBUG != self._old_DEBUG:
            settings.DEBUG = self._old_DEBUG
        if self.TIME_ZONE != self._old_TIME_ZONE:
            settings.TIME_ZONE = self._old_TIME_ZONE

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
            '''Content-Type: text/plain; charset="UTF-8"\n'''
            '''Content-Transfer-Encoding: base64\n'''
            '''Subject: =?UTF-8?b?5Lu25ZCN?=\n'''
            '''From: =?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>\n'''
            '''To: =?UTF-8?b?5a6b5YWI?= <example@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''5pys5paH\n''',
            message.as_string())

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

class DjangoMailISO2022JPTestCase(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'iso-2022-jp'

    def test_send_mail(self):
        django_mail.send_mail(
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

class DjangoMailUTF8TestCase(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'utf8'

    def test_send_mail(self):
        django_mail.send_mail(
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example@example.net>'],
        )
        
        message = django_mail.outbox[0].message()
        msg_str = message.as_string()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="UTF-8"\n'''
            '''Content-Transfer-Encoding: base64\n'''
            '''Subject: =?UTF-8?b?5Lu25ZCN?=\n'''
            '''From: =?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>\n'''
            '''To: =?UTF-8?b?5a6b5YWI?= <example@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''5pys5paH\n''',
            message.as_string())

class SignalTest(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'utf8'
    EMAIL_CHARSET = 'iso-2022-jp'

    def test_pre_send_singnal(self):
        from beproud.django.mailer.signals import mail_pre_send
        def pre_send_signal(sender, message, **kwargs):
            message.from_email = message.from_email.replace(u'\uff5e', u'\u301c')
            message.to = map(lambda x: x.replace(u'\uff5e', u'\u301c'), message.to)
            message.bcc = map(lambda x: x.replace(u'\uff5e', u'\u301c'), message.bcc)
            message.subject = message.subject.replace(u'\uff5e', u'\u301c')
            message.body = message.body.replace(u'\uff5e', u'\u301c')
        mail_pre_send.connect(pre_send_signal)

        send_mail(
           u'件名',
           u'本文～テスト',
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
            '''\x1b$BK\\J8!A%F%9%H\x1b(B''',
            message.as_string())

    def test_post_send_singnal(self):
        from beproud.django.mailer.signals import mail_post_send
        
        test_list = []

        def post_send_signal(sender, message, **kwargs):
            self.assertEqual(message.subject, u'件名')
            self.assertEqual(message.body, u'本文')
            test_list.append("arrived")
        mail_post_send.connect(post_send_signal)

        send_mail(
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example@example.net>'],
        )

        self.assertTrue(test_list, ["arrived"])

class MassMailTest(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'utf8'

    def test_mass_mail(self):
        send_mass_mail(((
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example%s@example.net>' % i],
        ) for i in range(10)))

        for i in range(10):
            message = django_mail.outbox[i].message()
            self.assertEllipsisMatch((
                '''MIME-Version: 1.0\n'''
                '''Content-Type: text/plain; charset="UTF-8"\n'''
                '''Content-Transfer-Encoding: base64\n'''
                '''Subject: =?UTF-8?b?5Lu25ZCN?=\n'''
                '''From: =?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>\n'''
                '''To: =?UTF-8?b?5a6b5YWI?= <example%s@example.net>\n'''
                '''Date: ...\n'''
                '''Message-ID: <...>\n'''
                '''\n'''
                '''5pys5paH\n''') % i,
                message.as_string())

    def test_mass_mail_encoding(self):
        send_mass_mail(((
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example%s@example.net>' % i],
        ) for i in range(10)), encoding='iso-2022-jp')

        for i in range(10):
            message = django_mail.outbox[i].message()
            self.assertEllipsisMatch((
                '''MIME-Version: 1.0\n'''
                '''Content-Type: text/plain; charset="ISO-2022-JP"\n'''
                '''Content-Transfer-Encoding: 7bit\n'''
                '''Subject: =?ISO-2022-JP?b?GyRCN29MPhsoQg==?=\n'''
                '''From: =?ISO-2022-JP?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>\n'''
                '''To: =?ISO-2022-JP?b?GyRCMDhAaBsoQg==?= <example%s@example.net>\n'''
                '''Date: ...\n'''
                '''Message-ID: <...>\n'''
                '''\n'''
                '''\x1b$BK\\J8\x1b(B''') % i,
                message.as_string())

    def test_mass_mail_encoding_inline(self):
        send_mass_mail((
            (
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example0@example.net>'],
               'iso-2022-jp',
            ),
            (
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example1@example.net>'],
            ),
            (
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example2@example.net>'],
               'iso-2022-jp',
            )
        ))

        message = django_mail.outbox[0].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="ISO-2022-JP"\n'''
            '''Content-Transfer-Encoding: 7bit\n'''
            '''Subject: =?ISO-2022-JP?b?GyRCN29MPhsoQg==?=\n'''
            '''From: =?ISO-2022-JP?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>\n'''
            '''To: =?ISO-2022-JP?b?GyRCMDhAaBsoQg==?= <example0@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''\x1b$BK\\J8\x1b(B''',
            message.as_string())

        message = django_mail.outbox[1].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="UTF-8"\n'''
            '''Content-Transfer-Encoding: base64\n'''
            '''Subject: =?UTF-8?b?5Lu25ZCN?=\n'''
            '''From: =?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>\n'''
            '''To: =?UTF-8?b?5a6b5YWI?= <example1@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''5pys5paH\n''',
            message.as_string())

        message = django_mail.outbox[2].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="ISO-2022-JP"\n'''
            '''Content-Transfer-Encoding: 7bit\n'''
            '''Subject: =?ISO-2022-JP?b?GyRCN29MPhsoQg==?=\n'''
            '''From: =?ISO-2022-JP?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>\n'''
            '''To: =?ISO-2022-JP?b?GyRCMDhAaBsoQg==?= <example2@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''\x1b$BK\\J8\x1b(B''',
            message.as_string())

    def test_mass_mail_encoding_inline2(self):
        send_mass_mail((
            (
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example0@example.net>'],
               'iso-2022-jp',
            ),
            (
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example1@example.net>'],
            ),
            (
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example2@example.net>'],
               'iso-2022-jp',
            )
        ), encoding='cp932')

        message = django_mail.outbox[0].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="ISO-2022-JP"\n'''
            '''Content-Transfer-Encoding: 7bit\n'''
            '''Subject: =?ISO-2022-JP?b?GyRCN29MPhsoQg==?=\n'''
            '''From: =?ISO-2022-JP?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>\n'''
            '''To: =?ISO-2022-JP?b?GyRCMDhAaBsoQg==?= <example0@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''\x1b$BK\\J8\x1b(B''',
            message.as_string())

        message = django_mail.outbox[1].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="SHIFT-JIS"\n'''
            '''Content-Transfer-Encoding: 8bit\n'''
            '''Subject: =?SHIFT-JIS?b?jI+WvA==?=\n'''
            '''From: =?SHIFT-JIS?b?jbePb5Bs?= <example-from@example.net>\n'''
            '''To: =?SHIFT-JIS?b?iLaQ5g==?= <example1@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''\x96{\x95\xb6''',
            message.as_string())

        message = django_mail.outbox[2].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="ISO-2022-JP"\n'''
            '''Content-Transfer-Encoding: 7bit\n'''
            '''Subject: =?ISO-2022-JP?b?GyRCN29MPhsoQg==?=\n'''
            '''From: =?ISO-2022-JP?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>\n'''
            '''To: =?ISO-2022-JP?b?GyRCMDhAaBsoQg==?= <example2@example.net>\n'''
            '''Date: ...\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''\x1b$BK\\J8\x1b(B''',
            message.as_string())


    def test_mass_mail_pre_send(self):
        from beproud.django.mailer.signals import mail_pre_send
        
        test_list = []

        def pre_send_signal(sender, message, **kwargs):
            self.assertEqual(message.subject, u'件名')
            self.assertEqual(message.body, u'本文')
            test_list.extend(message.to)
        mail_pre_send.connect(pre_send_signal)


        send_mass_mail(((
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example%s@example.net>' % i],
        ) for i in range(10)), encoding='iso-2022-jp')

        self.assertEqual(test_list, 
            [
                u'宛先 <example0@example.net>',
                u'宛先 <example1@example.net>',
                u'宛先 <example2@example.net>',
                u'宛先 <example3@example.net>',
                u'宛先 <example4@example.net>',
                u'宛先 <example5@example.net>',
                u'宛先 <example6@example.net>',
                u'宛先 <example7@example.net>',
                u'宛先 <example8@example.net>',
                u'宛先 <example9@example.net>',
            ]
        )

    def test_mass_mail_post_send(self):
        from beproud.django.mailer.signals import mail_post_send
        
        test_list = []

        def post_send_signal(sender, message, **kwargs):
            self.assertEqual(message.subject, u'件名')
            self.assertEqual(message.body, u'本文')
            test_list.extend(message.to)
        mail_post_send.connect(post_send_signal)


        send_mass_mail(((
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example%s@example.net>' % i],
        ) for i in range(10)), encoding='iso-2022-jp')

        self.assertEqual(test_list, 
            [
                u'宛先 <example0@example.net>',
                u'宛先 <example1@example.net>',
                u'宛先 <example2@example.net>',
                u'宛先 <example3@example.net>',
                u'宛先 <example4@example.net>',
                u'宛先 <example5@example.net>',
                u'宛先 <example6@example.net>',
                u'宛先 <example7@example.net>',
                u'宛先 <example8@example.net>',
                u'宛先 <example9@example.net>',
            ]
        )

    def test_mass_mail_message_obj(self):
        from itertools import chain
        send_mass_mail(chain(((
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example%s@example.net>' % i],
            ) for i in range(4)),
            (EmailMessage(u'件名',u'本文', u'差出人 <example-from@example.net>', [u'宛先 <example4@example.net>']),),
            ((
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example%s@example.net>' % i],
            ) for i in range(5, 9)),
            (EmailMessage(u'件名',u'本文', u'差出人 <example-from@example.net>', [u'宛先 <example9@example.net>']),)
        ))

        for i in range(10):
            message = django_mail.outbox[i].message()
            self.assertEllipsisMatch((
                '''MIME-Version: 1.0\n'''
                '''Content-Type: text/plain; charset="UTF-8"\n'''
                '''Content-Transfer-Encoding: base64\n'''
                '''Subject: =?UTF-8?b?5Lu25ZCN?=\n'''
                '''From: =?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>\n'''
                '''To: =?UTF-8?b?5a6b5YWI?= <example%s@example.net>\n'''
                '''Date: ...\n'''
                '''Message-ID: <...>\n'''
                '''\n'''
                '''5pys5paH\n''') % i,
                message.as_string())


class UTCTimeTestCase(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'utf-8'
    TIME_ZONE='Asia/Tokyo'
    EMAIL_USE_LOCALTIME=False

    def test_email_utc_strict(self):
        send_mail(
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="UTF-8"\n'''
            '''Content-Transfer-Encoding: base64\n'''
            '''Subject: =?UTF-8?b?5Lu25ZCN?=\n'''
            '''From: =?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>\n'''
            '''To: =?UTF-8?b?5a6b5YWI?= <example@example.net>\n'''
            '''Date: ...-0000\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''5pys5paH\n''',
            message.as_string())

class LocalTimeTestCase(MailTestCase, DjangoTestCase):
    DEFAULT_CHARSET = 'utf-8'
    TIME_ZONE='Asia/Tokyo'
    EMAIL_USE_LOCALTIME=True

    def test_email_localtime_strict(self):
        send_mail(
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()
        self.assertEllipsisMatch(
            '''MIME-Version: 1.0\n'''
            '''Content-Type: text/plain; charset="UTF-8"\n'''
            '''Content-Transfer-Encoding: base64\n'''
            '''Subject: =?UTF-8?b?5Lu25ZCN?=\n'''
            '''From: =?UTF-8?b?5beu5Ye65Lq6?= <example-from@example.net>\n'''
            '''To: =?UTF-8?b?5a6b5YWI?= <example@example.net>\n'''
            '''Date: ...+0900\n'''
            '''Message-ID: <...>\n'''
            '''\n'''
            '''5pys5paH\n''',
            message.as_string())

class FailSilentlyTestCase(MailTestCase, DjangoTestCase):
    EMAIL_BACKEND='beproud.django.mailer.tests.ErrorEmailBackend'

    def test_fail_silently(self):
        send_mail(
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example@example.net>'],
           fail_silently=True,
        )
        send_template_mail(
            u'mailer/mail.tpl',
            u'差出人 <example-from@example.net>',
            [u'宛先 <example@example.net>'],
            extra_context={
                'subject': u'件名',
                'body': u'本文',
            },
            fail_silently=True,
        )
        send_mass_mail(((
           u'件名',
           u'本文',
           u'差出人 <example-from@example.net>',
           [u'宛先 <example%s@example.net>' % i],
        ) for i in range(10)), fail_silently=True)
        mail_managers(
           u'件名',
           u'本文',
           fail_silently=True,
        )
        mail_managers_template(
           u'mailer/mail.tpl',
            extra_context={
                'subject': u'件名',
                'body': u'本文',
            },
           fail_silently=True,
        )
        mail_admins(
           u'件名',
           u'本文',
           fail_silently=True,
        )

    def test_fail_loud(self):
        try:
            send_mail(
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example@example.net>'],
            )
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            send_template_mail(
                u'mailer/mail.tpl',
                u'差出人 <example-from@example.net>',
                [u'宛先 <example@example.net>'],
                extra_context={
                    'subject': u'件名',
                    'body': u'本文',
                },
            )
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            send_mass_mail(((
               u'件名',
               u'本文',
               u'差出人 <example-from@example.net>',
               [u'宛先 <example%s@example.net>' % i],
            ) for i in range(10)))
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            mail_managers(
               u'件名',
               u'本文',
            )
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            mail_managers_template(
               u'mailer/mail.tpl',
                extra_context={
                    'subject': u'件名',
                    'body': u'本文',
                },
            )
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            mail_admins(
               u'件名',
               u'本文',
            )
            self.fail("Expected Error")
        except EmailError:
            pass

