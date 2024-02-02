import logging
import os
import time
import unittest
from itertools import chain
from logging.handlers import BufferingHandler
from unittest import mock

from django.conf import settings
from django.core import mail as django_mail
from django.test import TestCase as DjangoTestCase
from django.test import override_settings

from beproud.django.mailer import (
    EmailMessage,
    EmailMultiAlternatives,
    mail_admins,
    mail_managers,
    mail_managers_template,
    send_mail,
    send_mass_mail,
    send_template_mail,
)
from beproud.django.mailer import api as mailer_api
from beproud.django.mailer import tasks as mailer_tasks
from beproud.django.mailer.backends.base import BaseEmailBackend
from beproud.django.mailer.models import init_mailer
from beproud.django.mailer.signals import mail_post_send, mail_pre_send

# Suppress logging
logging.getLogger("").handlers = [BufferingHandler(0)]

__all__ = (
    'EncodingTestCaseUTF8',
    'EncodingTestCaseISO2022JP',
    'EmailAllForwardTestCase',
    'EmailAllForwardTestCase2',
    'TemplateTestCase',
    'TemplateContextTestCase',
    'DjangoMailISO2022JPTestCase',
    'DjangoMailUTF8TestCase',
    'SignalTest',
    'MassMailTest',
    'UTCTimeTestCase',
    'LocalTimeTestCase',
    'FailSilentlyTestCase',
    'AttachmentTestCase',
    'HtmlMailTestCase',

    'TaskTests',
)


class EmailError(Exception):
    pass


class ErrorEmailBackend(BaseEmailBackend):
    def _send_message(self, email_message):
        raise EmailError("ERROR")


class MailTestCase:
    def setUp(self):
        os.environ['TZ'] = settings.TIME_ZONE
        time.tzset()
        init_mailer()

    def tearDown(self):
        mail_pre_send.recievers = []
        mail_post_send.recievers = []


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class EmailMessageEncodingTestCase(MailTestCase, DjangoTestCase):
    def test_email_message_default(self):
        message_obj = EmailMessage(
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example4@example.net>']
            )

        message = message_obj.message()

        self.assertEqual(message['Subject'], '=?utf-8?b?5Lu25ZCN?=')

    def test_email_message_utf_8(self):
        message_obj = EmailMessage(
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example4@example.net>']
            )
        message_obj.encoding = 'utf-8'
        message = message_obj.message()

        self.assertEqual(message['Subject'], '=?utf-8?b?5Lu25ZCN?=')

    # FIXME
    @unittest.skip("Py3.6から動かない")
    def test_email_message_utf_8_alias(self):
        message_obj = EmailMessage(
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example4@example.net>']
            )
        message_obj.encoding = 'UTF'
        message = message_obj.message()

        self.assertEqual(message['Subject'], '=?utf-8?b?5Lu25ZCN?=')

    # FIXME
    @unittest.skip("Py3.6から動かない")
    def test_email_message_cp932_alias_sjis(self):
        message_obj = EmailMessage(
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example4@example.net>'],
            )
        message_obj.encoding = 'cp932'
        message = message_obj.message()

        self.assertEqual(message['Subject'], '=?shift-jis?b?jI+WvA==?=')

    def test_email_message_iso_2022_jp(self):
        message_obj = EmailMessage(
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example4@example.net>'],
            )
        message_obj.encoding = 'iso-2022-jp'
        message = message_obj.message()

        self.assertEqual(message['Subject'], '=?iso-2022-jp?b?GyRCN29MPhsoQg==?=')

    def test_email_message_iso_2022_jp_alias(self):
        message_obj = EmailMessage(
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example4@example.net>'],
            )
        message_obj.encoding = 'iso2022jp'
        message = message_obj.message()

        self.assertEqual(message['Subject'], '=?iso-2022-jp?b?GyRCN29MPhsoQg==?=')


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class EncodingTestCaseUTF8(MailTestCase, DjangoTestCase):

    def test_send_mail(self):
        send_mail(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
        )
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].body, '本文')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), 'example@example.net')
        self.assertEqual(str(message['From']), 'example-from@example.net')

    def test_email_charset_strict(self):
        send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()

        self.assertEqual(str(message['Subject']), "=?utf-8?b?5Lu25ZCN?=")
        self.assertEqual(str(message['To']), "=?utf-8?b?5a6b5YWI?= <example@example.net>")
        self.assertEqual(str(message['From']),
                         "=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="utf-8"')
        self.assertEqual(message.get_payload(decode=True), '本文'.encode())

    def test_cc(self):
        send_mail(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
            cc=['cc@example.net'],
        )
        self.assertEqual(len(django_mail.outbox), 1)

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['To']), 'example@example.net')
        self.assertEqual(str(message['Cc']), 'cc@example.net')
        self.assertEqual(str(message['From']), 'example-from@example.net')

    def test_bcc(self):
        send_mail(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
            bcc=['bcc@example.net'],
        )
        self.assertEqual(len(django_mail.outbox), 1)

        message = django_mail.outbox[0].message()

        self.assertEqual(str(message['To']), 'example@example.net')
        self.assertEqual(str(message['From']), 'example-from@example.net')

        # Bcc is not included in email headers
        self.assertEqual(message['Bcc'], None)

        self.assertTrue('bcc@example.net' in django_mail.outbox[0].bcc)


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(EMAIL_CHARSET='iso-2022-jp')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class EncodingTestCaseISO2022JP(MailTestCase, DjangoTestCase):
    # TODO: Set ALIASES and CODECS

    def test_send_mail_encoding(self):
        send_mail(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
            encoding="utf-8",
        )
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].body, '本文')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), 'example@example.net')
        self.assertEqual(str(message['From']), 'example-from@example.net')

    def test_email_charset(self):
        send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].body, '本文')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?iso-2022-jp?b?GyRCN29MPhsoQg==?=')
        self.assertEqual(str(message['To']),
                          '=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example@example.net>')
        self.assertEqual(str(message['From']),
                          '=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>')

    def test_email_charset_strict(self):
        send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()

        self.assertEqual(str(message['Subject']), "=?iso-2022-jp?b?GyRCN29MPhsoQg==?=")
        self.assertEqual(str(message['To']),
                         "=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example@example.net>")
        self.assertEqual(str(message['From']),
                         "=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="iso-2022-jp"')
        self.assertEqual(message.get_payload(), "\x1b$BK\\J8\x1b(B")


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(DEBUG=True)
@override_settings(EMAIL_ALL_FORWARD='all-forward@example.net')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class EmailAllForwardTestCase(MailTestCase, DjangoTestCase):
    def test_email_all_forward(self):
        send_mail(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
        )
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].body, '本文')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), 'all-forward@example.net')
        self.assertEqual(str(message['From']), 'all-forward@example.net')


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(DEBUG=False)
@override_settings(EMAIL_ALL_FORWARD='all-forward@example.net')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class EmailAllForwardTestCase2(MailTestCase, DjangoTestCase):

    def test_email_all_forward(self):
        send_mail(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
        )
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].body, '本文')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), 'example@example.net')
        self.assertEqual(str(message['From']), 'example-from@example.net')


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class TemplateTestCase(MailTestCase, DjangoTestCase):
    # TODO: Set ALIASES and CODECS

    def test_template_mail(self):
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
            extra_context={
                'subject': '件名',
                'body': '本文',
            },
            fail_silently=False,
        )

        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].body, '本文\n')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), '=?utf-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEqual(str(message['From']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')

    def test_multi_line_subject(self):
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
            extra_context={
                'subject': 'これは\r改行\nの\nある\r\n件名',
                'body': '本文',
            },
            fail_silently=False,
        )

        self.assertEqual(len(django_mail.outbox), 1)

        mail_message = django_mail.outbox[0]
        self.assertEqual(mail_message.subject, 'これは改行のある件名')
        self.assertEqual(mail_message.body, '本文\n')

        message = mail_message.message()
        self.assertEqual(str(message['Subject']),
                          '=?utf-8?b?44GT44KM44Gv5pS56KGM44Gu44GC44KL5Lu25ZCN?=')
        self.assertEqual(str(message['To']), '=?utf-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEqual(str(message['From']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')

    def test_cc(self):
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['差出人 <example-from@example.net>'],
            cc=['宛先 <example@example.net>'],
            extra_context={
                'subject': 'これは\r改行\nの\nある\r\n件名',
                'body': '本文',
            },
            fail_silently=False,
        )

        self.assertEqual(len(django_mail.outbox), 1)

        mail_message = django_mail.outbox[0]

        message = mail_message.message()
        self.assertEqual(str(message['To']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')
        self.assertEqual(str(message['Cc']), '=?utf-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEqual(str(message['From']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')

    def test_bcc(self):
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['差出人 <example-from@example.net>'],
            bcc=['宛先 <example@example.net>'],
            extra_context={
                'subject': 'これは\r改行\nの\nある\r\n件名',
                'body': '本文',
            },
            fail_silently=False,
        )

        self.assertEqual(len(django_mail.outbox), 1)

        mail_message = django_mail.outbox[0]

        message = mail_message.message()
        self.assertEqual(str(message['To']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')
        self.assertEqual(str(message['From']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')

        # Bcc is not included in email headers
        self.assertEqual(message['Bcc'], None)

        self.assertTrue('宛先 <example@example.net>' in django_mail.outbox[0].bcc)


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(EMAIL_DEFAULT_CONTEXT={"subject": "件名"})
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class TemplateContextTestCase(MailTestCase, DjangoTestCase):

    def test_email_default_context(self):
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
            extra_context={
                'body': '本文',
            },
            fail_silently=False,
        )

        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].body, '本文\n')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), '=?utf-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEqual(str(message['From']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')

    def test_email_default_context_override(self):
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
            extra_context={
                'subject': 'overwrite',
                'body': '本文',
            },
            fail_silently=False,
        )

        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].body, '本文\n')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), 'overwrite')
        self.assertEqual(str(message['To']), '=?utf-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEqual(str(message['From']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')

    def test_email_default_context_overwrite(self):
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
            extra_context={
                'subject': 'overwrite',
                'body': '本文',
            },
            fail_silently=False,
        )

        # Check to make sure we don't overwrite the data in
        # settings.EMAIL_DEFAULT_CONTEXT
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
            extra_context={
                'body': '本文',
            },
            fail_silently=False,
        )

        self.assertEqual(len(django_mail.outbox), 2)
        self.assertEqual(django_mail.outbox[1].body, '本文\n')

        message = django_mail.outbox[1].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), '=?utf-8?b?5a6b5YWI?= <example@example.net>')
        self.assertEqual(str(message['From']),
                          '=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>')


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='iso-2022-jp')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class DjangoMailISO2022JPTestCase(MailTestCase, DjangoTestCase):

    def test_send_mail(self):
        django_mail.send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()

        self.assertEqual(str(message['Subject']), "=?iso-2022-jp?b?GyRCN29MPhsoQg==?=")
        self.assertEqual(str(message['To']),
                         "=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example@example.net>")
        self.assertEqual(str(message['From']),
                         "=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="iso-2022-jp"')
        self.assertEqual(message.get_payload(), "\x1b$BK\\J8\x1b(B")


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class DjangoMailUTF8TestCase(MailTestCase, DjangoTestCase):
    def test_send_mail(self):
        django_mail.send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()

        self.assertEqual(str(message['Subject']), "=?utf-8?b?5Lu25ZCN?=")
        self.assertEqual(str(message['To']), "=?utf-8?b?5a6b5YWI?= <example@example.net>")
        self.assertEqual(str(message['From']),
                         "=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="utf-8"')
        self.assertEqual(message.get_payload(decode=True), '本文'.encode())


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(EMAIL_CHARSET='iso-2022-jp')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class SignalTest(MailTestCase, DjangoTestCase):

    def test_pre_send_signal(self):
        def pre_send_signal(sender, message, **kwargs):
            message.from_email = message.from_email.replace('\uff5e', '\u301c')
            message.to = [x.replace('\uff5e', '\u301c') for x in message.to]
            message.bcc = [x.replace('\uff5e', '\u301c') for x in message.bcc]
            message.subject = message.subject.replace('\uff5e', '\u301c')
            message.body = message.body.replace('\uff5e', '\u301c')
        mail_pre_send.connect(pre_send_signal)

        send_mail(
            '件名',
            '本文～テスト',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()

        self.assertEqual(str(message['Subject']), "=?iso-2022-jp?b?GyRCN29MPhsoQg==?=")
        self.assertEqual(str(message['To']),
                         "=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example@example.net>")
        self.assertEqual(str(message['From']),
                         "=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="iso-2022-jp"')
        self.assertEqual(message.get_payload(), "\x1b$BK\\J8!A%F%9%H\x1b(B")

    def test_post_send_signal(self):
        test_list = []

        def post_send_signal(sender, message, **kwargs):
            self.assertEqual(message.subject, '件名')
            self.assertEqual(message.body, '本文')
            test_list.append("arrived")
        mail_post_send.connect(post_send_signal)

        send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        self.assertTrue(test_list, ["arrived"])


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf8')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class MassMailTest(MailTestCase, DjangoTestCase):

    def test_mass_mail(self):
        send_mass_mail((
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example%s@example.net>' % i],
        ) for i in range(10))

        for i in range(10):
            message = django_mail.outbox[i].message()

            self.assertEqual(str(message['Subject']), "=?utf-8?b?5Lu25ZCN?=")
            self.assertEqual(str(message['To']),
                             "=?utf-8?b?5a6b5YWI?= <example%s@example.net>" % i)
            self.assertEqual(str(message['From']),
                             "=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>")
            self.assertEqual(message['Content-Transfer-Encoding'], '8bit')
            self.assertEqual(message['Content-Type'], 'text/plain; charset="utf-8"')
            self.assertEqual(message.get_payload(decode=True), '本文'.encode())

    def test_mass_mail_encoding(self):
        send_mass_mail(((
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example%s@example.net>' % i],
        ) for i in range(10)), encoding='iso-2022-jp')

        for i in range(10):
            message = django_mail.outbox[i].message()

            self.assertEqual(str(message['Subject']), "=?iso-2022-jp?b?GyRCN29MPhsoQg==?=")
            self.assertEqual(str(message['To']),
                             "=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example%s@example.net>" % i)
            self.assertEqual(str(message['From']),
                             "=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>")
            self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
            self.assertEqual(message['Content-Type'], 'text/plain; charset="iso-2022-jp"')
            self.assertEqual(message.get_payload(), "\x1b$BK\\J8\x1b(B")

    def test_mass_mail_encoding_inline(self):
        send_mass_mail((
            (
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example0@example.net>'],
                'iso-2022-jp',
            ),
            (
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example1@example.net>'],
            ),
            (
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example2@example.net>'],
                'iso-2022-jp',
            )
        ))

        message = django_mail.outbox[0].message()

        self.assertEqual(str(message['Subject']), "=?iso-2022-jp?b?GyRCN29MPhsoQg==?=")
        self.assertEqual(str(message['To']),
                         "=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example0@example.net>")
        self.assertEqual(str(message['From']),
                         "=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="iso-2022-jp"')
        self.assertEqual(message.get_payload(), "\x1b$BK\\J8\x1b(B")

        message = django_mail.outbox[1].message()
        self.assertEqual(str(message['Subject']), "=?utf-8?b?5Lu25ZCN?=")
        self.assertEqual(str(message['To']), "=?utf-8?b?5a6b5YWI?= <example1@example.net>")
        self.assertEqual(str(message['From']),
                         "=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="utf-8"')
        self.assertEqual(message.get_payload(decode=True), '本文'.encode())

        message = django_mail.outbox[2].message()
        self.assertEqual(str(message['Subject']), "=?iso-2022-jp?b?GyRCN29MPhsoQg==?=")
        self.assertEqual(str(message['To']),
                         "=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example2@example.net>")
        self.assertEqual(str(message['From']),
                         "=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="iso-2022-jp"')
        self.assertEqual(message.get_payload(), "\x1b$BK\\J8\x1b(B")

    # FIXME
    @unittest.skip("Py3.6から動かない")
    def test_mass_mail_encoding_inline2(self):
        send_mass_mail((
            (
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example0@example.net>'],
                'iso-2022-jp',
            ),
            (
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example1@example.net>'],
            ),
            (
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example2@example.net>'],
                'iso-2022-jp',
            )
        ), encoding='cp932')

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), "=?iso-2022-jp?b?GyRCN29MPhsoQg==?=")
        self.assertEqual(str(message['To']),
                         "=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example0@example.net>")
        self.assertEqual(str(message['From']),
                         "=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="iso-2022-jp"')
        self.assertEqual(message.get_payload(), "\x1b$BK\\J8\x1b(B")

        message = django_mail.outbox[1].message()
        self.assertEqual(str(message['Subject']), "=?shift-jis?b?jI+WvA==?=")
        self.assertEqual(str(message['To']), "=?shift-jis?b?iLaQ5g==?= <example1@example.net>")
        self.assertEqual(str(message['From']),
                         "=?shift-jis?b?jbePb5Bs?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="shift-jis"')
        self.assertEqual(message.get_payload(), "\x96{\x95\xb6")

        message = django_mail.outbox[2].message()
        self.assertEqual(str(message['Subject']), "=?iso-2022-jp?b?GyRCN29MPhsoQg==?=")
        self.assertEqual(str(message['To']),
                         "=?iso-2022-jp?b?GyRCMDhAaBsoQg==?= <example2@example.net>")
        self.assertEqual(str(message['From']),
                         "=?iso-2022-jp?b?GyRCOjk9UD9NGyhC?= <example-from@example.net>")
        self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['Content-Type'], 'text/plain; charset="iso-2022-jp"')
        self.assertEqual(message.get_payload(), "\x1b$BK\\J8\x1b(B")

    def test_mass_mail_pre_send(self):
        test_list = []

        def pre_send_signal(sender, message, **kwargs):
            self.assertEqual(message.subject, '件名')
            self.assertEqual(message.body, '本文')
            test_list.extend(message.to)
        mail_pre_send.connect(pre_send_signal)

        send_mass_mail(((
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example%s@example.net>' % i],
        ) for i in range(10)), encoding='iso-2022-jp')

        self.assertEqual(test_list, [
            '宛先 <example0@example.net>',
            '宛先 <example1@example.net>',
            '宛先 <example2@example.net>',
            '宛先 <example3@example.net>',
            '宛先 <example4@example.net>',
            '宛先 <example5@example.net>',
            '宛先 <example6@example.net>',
            '宛先 <example7@example.net>',
            '宛先 <example8@example.net>',
            '宛先 <example9@example.net>',
        ])

    def test_mass_mail_post_send(self):
        test_list = []

        def post_send_signal(sender, message, **kwargs):
            self.assertEqual(message.subject, '件名')
            self.assertEqual(message.body, '本文')
            test_list.extend(message.to)
        mail_post_send.connect(post_send_signal)

        send_mass_mail(((
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example%s@example.net>' % i],
        ) for i in range(10)), encoding='iso-2022-jp')

        self.assertEqual(test_list, [
            '宛先 <example0@example.net>',
            '宛先 <example1@example.net>',
            '宛先 <example2@example.net>',
            '宛先 <example3@example.net>',
            '宛先 <example4@example.net>',
            '宛先 <example5@example.net>',
            '宛先 <example6@example.net>',
            '宛先 <example7@example.net>',
            '宛先 <example8@example.net>',
            '宛先 <example9@example.net>',
        ])

    def test_mass_mail_message_obj(self):
        send_mass_mail(chain((
            (
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example%s@example.net>' % i],
            ) for i in range(4)),
            (EmailMessage('件名', '本文', '差出人 <example-from@example.net>',
                          ['宛先 <example4@example.net>']),),
            ((
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example%s@example.net>' % i],
            ) for i in range(5, 9)),
            (EmailMessage('件名', '本文', '差出人 <example-from@example.net>',
                          ['宛先 <example9@example.net>']),)
        ))

        for i in range(10):
            message = django_mail.outbox[i].message()

            self.assertEqual(str(message['Subject']), "=?utf-8?b?5Lu25ZCN?=")
            self.assertEqual(str(message['To']),
                             "=?utf-8?b?5a6b5YWI?= <example%s@example.net>" % i)
            self.assertEqual(str(message['From']),
                             "=?utf-8?b?5beu5Ye65Lq6?= <example-from@example.net>")
            self.assertEqual(message['Content-Transfer-Encoding'], '8bit')
            self.assertEqual(message['Content-Type'], 'text/plain; charset="utf-8"')
            self.assertEqual(message.get_payload(decode=True), '本文'.encode())


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf-8')
@override_settings(TIME_ZONE='Asia/Tokyo')
@override_settings(EMAIL_USE_LOCALTIME=False)
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class UTCTimeTestCase(MailTestCase, DjangoTestCase):

    def test_email_utc_strict(self):
        send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()
        self.assertTrue(message['Date'].endswith("-0000"))


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf8')
@override_settings(TIME_ZONE='Asia/Tokyo')
@override_settings(EMAIL_USE_LOCALTIME=True)
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class LocalTimeTestCase(MailTestCase, DjangoTestCase):

    def test_email_localtime_strict(self):
        send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
        )

        message = django_mail.outbox[0].message()
        self.assertTrue(message['Date'].endswith("+0900"))


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf8')
@override_settings(EMAIL_BACKEND='tests.test_mail.ErrorEmailBackend')
class FailSilentlyTestCase(MailTestCase, DjangoTestCase):

    def test_fail_silently(self):
        send_mail(
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
            fail_silently=True,
        )
        send_template_mail(
            'mailer/mail.tpl',
            '差出人 <example-from@example.net>',
            ['宛先 <example@example.net>'],
            extra_context={
                'subject': '件名',
                'body': '本文',
            },
            fail_silently=True,
        )
        send_mass_mail(((
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example%s@example.net>' % i],
        ) for i in range(10)), fail_silently=True)
        mail_managers(
            '件名',
            '本文',
            fail_silently=True,
        )
        mail_managers_template(
            'mailer/mail.tpl',
            extra_context={
                'subject': '件名',
                'body': '本文',
            },
            fail_silently=True,
        )
        mail_admins(
            '件名',
            '本文',
            fail_silently=True,
        )

    def test_fail_loud(self):
        try:
            send_mail(
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example@example.net>'],
            )
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            send_template_mail(
                'mailer/mail.tpl',
                '差出人 <example-from@example.net>',
                ['宛先 <example@example.net>'],
                extra_context={
                    'subject': '件名',
                    'body': '本文',
                },
            )
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            send_mass_mail((
                '件名',
                '本文',
                '差出人 <example-from@example.net>',
                ['宛先 <example%s@example.net>' % i],
            ) for i in range(10))
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            mail_managers(
                '件名',
                '本文',
            )
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            mail_managers_template(
                'mailer/mail.tpl',
                extra_context={
                    'subject': '件名',
                    'body': '本文',
                },
            )
            self.fail("Expected Error")
        except EmailError:
            pass
        try:
            mail_admins(
                '件名',
                '本文',
            )
            self.fail("Expected Error")
        except EmailError:
            pass


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf8')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class AttachmentTestCase(MailTestCase, DjangoTestCase):

    def test_send_mail(self):
        send_mail(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
            attachments=[('test.txt', "データ", 'text/plain')],
        )

        message = django_mail.outbox[0]
        self.assertEqual(message.attachments, [('test.txt', "データ", 'text/plain')])

    def test_send_template_mail(self):
        send_template_mail(
            'mailer/mail.tpl',
            'example-from@example.net',
            ['example@example.net'],
            extra_context={
                'subject': '件名',
                'body': '本文',
                'html': "<h1>本文</h1>",
            },
            fail_silently=False,
            html_template_name='mailer/html_mail.tpl',
            attachments=[('test.txt', "データ", 'text/plain')],
        )

        message = django_mail.outbox[0]
        self.assertEqual(message.attachments, [('test.txt', "データ", 'text/plain')])

    def test_binary_attachment(self):
        message = EmailMessage(
            attachments=[('test.binary', "データ".encode(), None)]).message()

        payloads = message.get_payload()

        # 添付ファイルのペイロード
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]['Content-Transfer-Encoding'], 'base64')
        self.assertEqual(payloads[0]['Content-Type'], 'application/octet-stream')
        self.assertEqual(payloads[0]['Content-Disposition'], 'attachment; filename="test.binary"')
        self.assertEqual(payloads[0].get_payload(decode=True), 'データ'.encode())

    def test_text_attachment(self):
        message = EmailMessage(attachments=[('test.txt', "データ", None)]).message()

        payloads = message.get_payload()

        # 添付ファイルのペイロード
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(payloads[0]['Content-Type'], 'text/plain; charset="utf-8"')
        self.assertEqual(payloads[0]['Content-Disposition'], 'attachment; filename="test.txt"')
        self.assertEqual(payloads[0].get_payload(decode=True), 'データ'.encode())


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf8')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class HtmlMailTestCase(MailTestCase, DjangoTestCase):

    def test_send_mail_html(self):
        send_mail(
            "件名",
            "本文",
            'example-from@example.net',
            ['example@example.net'],
            html_message="<h1>本文</h1>",
        )
        self.assertEqual(len(django_mail.outbox), 1)

        email_message = django_mail.outbox[0]
        self.assertEqual(email_message.body, '本文')
        self.assertTrue(isinstance(email_message, EmailMultiAlternatives))

        self.assertTrue(("<h1>本文</h1>", "text/html") in email_message.alternatives)

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), 'example@example.net')
        self.assertEqual(str(message['From']), 'example-from@example.net')

        payloads = message.get_payload()

        # text + html ペイロード
        self.assertEqual(len(payloads), 2)
        self.assertEqual(payloads[0]['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(payloads[0]['Content-Type'], 'text/plain; charset="utf-8"')
        self.assertEqual(payloads[0].get_payload(decode=True), "本文".encode())
        self.assertEqual(payloads[1]['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(payloads[1]['Content-Type'], 'text/html; charset="utf-8"')
        self.assertEqual(payloads[1].get_payload(decode=True), "<h1>本文</h1>".encode())

    def test_html_template_mail(self):
        send_template_mail(
            'mailer/mail.tpl',
            'example-from@example.net',
            ['example@example.net'],
            extra_context={
                'subject': '件名',
                'body': '本文',
                'html': "<h1>本文</h1>",
            },
            fail_silently=False,
            html_template_name='mailer/html_mail.tpl',
        )

        self.assertEqual(len(django_mail.outbox), 1)

        email_message = django_mail.outbox[0]
        self.assertEqual(email_message.body, '本文\n')
        self.assertTrue(isinstance(email_message, EmailMultiAlternatives))

        self.assertTrue(("<h1>本文</h1>\n", "text/html") in email_message.alternatives)

        message = django_mail.outbox[0].message()
        self.assertEqual(str(message['Subject']), '=?utf-8?b?5Lu25ZCN?=')
        self.assertEqual(str(message['To']), 'example@example.net')
        self.assertEqual(str(message['From']), 'example-from@example.net')

        payloads = message.get_payload()

        # text + html ペイロード
        self.assertEqual(len(payloads), 2)
        self.assertEqual(payloads[0]['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(payloads[0]['Content-Type'], 'text/plain; charset="utf-8"')
        self.assertEqual(payloads[0].get_payload(decode=True), "本文\n".encode())
        self.assertEqual(payloads[1]['Content-Transfer-Encoding'], '8bit')
        self.assertEqual(payloads[1]['Content-Type'], 'text/html; charset="utf-8"')
        self.assertEqual(payloads[1].get_payload(decode=True), "<h1>本文</h1>\n".encode())


@override_settings(ADMINS=(('Admin', 'admin@example.net'),))
@override_settings(MANAGERS=(('Manager', 'manager@example.net'),))
@override_settings(DEFAULT_CHARSET='utf8')
@override_settings(EMAIL_BACKEND='beproud.django.mailer.backends.locmem.EmailBackend')
class TaskTests(MailTestCase, DjangoTestCase):

    @mock.patch.object(mailer_api, 'send_mail')
    def test_send_mail(self, send_mail):
        mailer_tasks.send_mail.delay(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
        )

        send_mail.assert_called_once_with(
            '件名',
            '本文',
            'example-from@example.net',
            ['example@example.net'],
        )

    @mock.patch.object(mailer_api, 'send_template_mail')
    def test_send_template_mail(self, send_template_mail):
        mailer_tasks.send_template_mail.delay(
            'mailer/mail.tpl',
            'example-from@example.net',
            ['example@example.net'],
            extra_context={
                'subject': '件名',
                'body': '本文',
                'html': "<h1>本文</h1>",
            },
            fail_silently=False,
            html_template_name='mailer/html_mail.tpl',
        )

        send_template_mail.assert_called_once_with(
            'mailer/mail.tpl',
            'example-from@example.net',
            ['example@example.net'],
            extra_context={
                'subject': '件名',
                'body': '本文',
                'html': "<h1>本文</h1>",
            },
            fail_silently=False,
            html_template_name='mailer/html_mail.tpl',
        )

    # FIXME:
    @unittest.skip("AssertionError: expected call not found.になるが現在使用していないのでskip")
    @mock.patch.object(mailer_api, 'send_mass_mail')
    def test_send_mass_mail(self, send_mass_mail):
        mailer_tasks.send_mass_mail.delay(list((
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example%s@example.net>' % i],
        ) for i in range(10)))

        send_mass_mail.assert_called_once_with(list((
            '件名',
            '本文',
            '差出人 <example-from@example.net>',
            ['宛先 <example%s@example.net>' % i],
        ) for i in range(10)))

    @mock.patch.object(mailer_api, 'mail_managers')
    def test_mail_managers(self, mail_managers):
        mailer_tasks.mail_managers.delay(
            '件名',
            '本文',
            fail_silently=True,
        )

        mail_managers.assert_called_once_with(
            '件名',
            '本文',
            fail_silently=True,
        )

    @mock.patch.object(mailer_api, 'mail_managers_template')
    def test_mail_managers_template(self, mail_managers_template):
        mailer_tasks.mail_managers_template.delay(
            'mailer/mail.tpl',
            extra_context={
                'subject': '件名',
                'body': '本文',
            },
            fail_silently=True,
        )

        mail_managers_template.assert_called_once_with(
            'mailer/mail.tpl',
            extra_context={
                'subject': '件名',
                'body': '本文',
            },
            fail_silently=True,
        )

    @mock.patch.object(mailer_api, 'mail_admins')
    def test_mail_admins(self, mail_admins):
        mailer_tasks.mail_admins.delay(
            '件名',
            '本文',
            fail_silently=True,
        )

        mail_admins.assert_called_once_with(
            '件名',
            '本文',
            fail_silently=True,
        )
