# vim:fileencoding=utf-8
from django.test import TestCase as DjangoTestCase
from django.core import mail as django_mail
from django.conf import settings

from mailer import *

class MailTestCase(DjangoTestCase):
    
    def setUp(self):
        self.charset = settings.DEFAULT_CHARSET
        self.email_charset = getattr(settings, 'EMAIL_CHARSET', settings.DEFAULT_CHARSET)

    def tearDown(self):
        settings.DEFAULT_CHARSET = self.charset
        settings.EMAIL_CHARSET = self.email_charset

    def test_send_mail(self):
        settings.DEFAULT_CHARSET = 'utf-8'

        send_mail(
            u'Test Subject',
            u'Test Body',
            'example-from@example.net',
            ['example@example.net'],
        )
        self.assertEquals(len(django_mail.outbox), 1)
        self.assertEquals(django_mail.outbox[0].body, u'Test Body')

        message = django_mail.outbox[0].message() 
        self.assertEquals(str(message['Subject']), '=?UTF-8?q?Test_Subject?=')
        self.assertEquals(str(message['To']), 'example@example.net')
        self.assertEquals(str(message['From']), 'example-from@example.net')

    def test_send_mail_utf8(self):
        settings.DEFAULT_CHARSET = 'utf-8'

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

    def test_send_basic_mail_encoding(self):
        settings.DEFAULT_CHARSET = 'iso-2022-jp'

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
        settings.EMAIL_CHARSET = 'iso-2022-jp'
         
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

    def test_template_mail(self):
        settings.DEFAULT_CHARSET = 'utf-8'
         
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
