====================
メールの送信
====================

.. module:: mailer
   :synopsis: メール送信

Djangoのmailモジュールで電子メールを便利に送信できますが、ヘッダーと本文でそれぞれ違うエンコーディングを使う場合もあり、
本文をテンプレートからレンダリングすることができませんので、mailerモジュールを作りました。

send_mail()
--------------------

bpmailerが提供しているAPIはDjangoの標準 `django.core.mail`_ をすべて実装しています。以下のインポートを簡単にbpmailerに変更する
ことができます。

send_mailはこう定義されています。 `Django 1.1 send_mail()`_ と同じAPIです。

.. _`Django 1.1 send_mail()`: http://djangoproject.jp/doc/ja/1.0/topics/email.html#send-mail
.. _`django.core.mail`: http://djangoproject.jp/doc/ja/1.0/topics/email.html#module-django.core.mail

.. function:: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None)


.. code-block:: python

    from django.core.mail import send_mail

.. code-block:: python

    from mailer import send_mail

send_mailの呼び出し方は、Djangoと一緒です。

.. code-block:: python
    
    from mailer import send_mail

    send_mail('Subject here', 'Here is the message.', 'from@example.com',
        ['to@example.com'], fail_silently=False)

日本語ももちろん大丈夫です。

.. code-block:: python
    
    from mailer import send_mail

    send_mail(u'件名', u'メッセージ', 'from@example.com',
        ['to@example.com'], fail_silently=False)

send_basic_mail()
--------------------

Djangoの標準メールモジュールの上に拡張している send_basic_mailでも、メールを送信することができます。 send_mailの使い方と基本的に同じなんですけど、send_basic_mailでは、encodingを指定することができます。

send_basic_mailはこう定義されています。

.. function:: send_basic_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, encoding=None)

.. code-block:: python
    
    from mailer import send_basic_mail

    send_basic_mail(u'件名', u'メッセージ', 'from@example.com',
        ['to@example.com'], fail_silently=False, encoding="iso-2022-jp-2")

send_template_mail()
--------------------

テンプレートを使ってメールを送信することも可能です。コンテキストを渡せば、テンプレートをレンダリングして、送信します。

send_template_mailはこう定義されています。

.. function:: send_template_mail(template_name, from_email, recipient_list, extra_context={}, fail_silently=True, auth_user=None, auth_password=None, encoding=None)

.. code-block:: python
    
    from mailer import send_template_mail

    send_template_mail('mail/example.txt' 'from@example.com', extra_context={"user": user_obj},
        ['to@example.com'], fail_silently=False, encoding="iso-2022-jp-2")

