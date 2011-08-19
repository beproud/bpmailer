====================================
メールの送信
====================================

.. module:: mailer
   :synopsis: メール送信
.. currentmodule:: mailer.api

Djangoのmailモジュールで電子メールを便利に送信できますが、ヘッダーと本文でそれぞれ違うエンコーディングを使う場合もあり、
本文をテンプレートからレンダリングすることができませんので、mailerモジュールを作りました。

単純なメール送信
------------------------------------

bpmailerが提供しているAPIはDjangoの標準 `django.core.mail`_ をすべて実装しています。以下のインポートを簡単にbpmailerに変更することができます。

旧インポート::

    from django.core.mail import send_mail

新しいインポート::

    from mailer import send_mail

send_mail()
++++++++++++++++++++++++++++++++++++

send_mailはこう定義されています。 `Django 1.1 send_mail()`_ と同じAPIですが、 ``encoding`` という文字コードを指定できる引数が追加されてます。 ``encoding`` を指定しない場合、 :ref:`EMAIL_CHARSET <setting-email-charset>` という設定を使います。 :ref:`EMAIL_CHARSET <setting-email-charset>` が設定してない場合は `DEFAULT_CHARSET`_ を対かます。

.. function:: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, encoding=None, connection=None, html_message=None)

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


テンプレートからメールを送信
------------------------------------

テンプレートを使ってメールを送信することも可能です。コンテキストとテンプレート名を指定すれば、テンプレートをレンダリングして、送信します。

send_template_mail()
++++++++++++++++++++++++++++++++++++

send_template_mailはこう定義されています。

.. function:: send_template_mail(template_name, from_email, recipient_list, extra_context={}, fail_silently=True, auth_user=None, auth_password=None, encoding=None, connection=None, html_template_name=None)

.. code-block:: python
    
    from mailer import send_template_mail

    send_template_mail('mail/example.txt' 'from@example.com', ['to@example.com'],
        extra_context={"user": user_obj}, fail_silently=False, encoding="iso-2022-jp-2")

テキストテンプレートの作成
++++++++++++++++++++++++++++++++++++

メールのテンプレートは普通のテンプレートの違う特徴が一つあります。テンプレートの一行目はメールの件名になります::

    会員登録ありがとうございました
    {{ user.username }}様、

    会員登録、誠にありがとうございました。

    宜しくお願いします。

`HTMLの自動エスケープ`_ や、件名に入れたユーザデータには改行が入っているのを毎回チェックするのが面倒くさいので、メールテンプレートを簡単に書けるために、メールのベーステンプレートを提供します。 ``mailer/mail.tpl`` を継承して、カスタマイズすることができて、そのまま使えることもできます。

``subject`` と ``body`` をコンテキストでテンプレートに渡せば、 ``mailer/mail.tpl`` をそのまま使えることができます。件名に改行が入っている場合、自動的に削ります。例えば、以下の例のように、「これは\\n件名」を件名にすると、送信するメールの件名は「これは件名」になります。

.. code-block:: python

    from mailer import send_template_mail

    send_template_mail('mailer/mail.tpl' 'from@example.com', ['to@example.com'],
        extra_context={"subject": u"これは\n件名", "body": u"これは本文"},
        fail_silently=False, encoding="iso-2022-jp-2")

上の例では、 ``send_template_mail`` を ``send_mail`` と同じように使えますが、 ``send_template_mail`` の便利性は ``mailer/mail.tpl`` を継承して、メールの内容をテンプレートで管理することで発揮されます::

    {% extends "mailer/mail.tpl" %}

    {% block subject %}会員登録ありがとうございました{% endblock %} 

    {% block body %}{{ user.username }}様、

    会員登録、誠にありがとうございました。

    宜しくお願いします。{% endblock %}

このようにテンプレートを書きますと、HTML自動エスケープ、改行等、あまり気にせずにメールテンプレートを書けます。

HTMLテンプレート作成
------------------------------

``html_template_name`` を ``send_template_mail()`` に指定すると、bpmailer は マルチパートメールを作成し、
HTMLのパートを追加します。

``mailer/html_mail.tpl`` というテンプレートを用意しています。 直接使う場合は、 ``html`` のコンテキスト変数を
テンプレートに渡せば、テンプレートに追加できます。

.. code-block:: python

    from mailer import send_template_mail

    send_template_mail('mailer/html_mail.tpl' 'from@example.com', ['to@example.com'],
        extra_context={"subject": u"これは\n件名", "body": u"これは本文",
                       "html": "<p>これは<strong>HTML</strong>本文</p>"},
        fail_silently=False, encoding="iso-2022-jp-2")

HTMLテンプレートはテキスト文章のテンプレートの同じように作成しますが、HTMLテンプレートの場合はメールの件名が含まれません。
件名はテキスト用のテンプレートの件名を使います。HTML用のベーステンプレートも用意していますので、 ``mailer/html_mail.tpl``
を継承すれば、HTML メールのテンプレートを簡単に作成できます::

    {% extends "mailer/html_mail.tpl" %}

    {% block body %}
    <div>
      <p><strong>{{ user.username }}様</strong>、</p>

      <p>会員登録、<em>誠にありがとうございました</em>。</p>

      <p>宜しくお願いします。</p>
    </div> 
    {% endblock %}

"mailer/html_mail.tpl" を使えば、HTML自動エスケープを気にせずにメールテンプレートを書けます。

.. _`Django 1.1 send_mail()`: http://djangoproject.jp/doc/ja/1.0/topics/email.html#send-mail
.. _`DEFAULT_CHARSET`: http://djangoproject.jp/doc/ja/1.0/ref/settings.html#default-charset
.. _`django.core.mail`: http://djangoproject.jp/doc/ja/1.0/topics/email.html#module-django.core.mail
.. _`HTMLの自動エスケープ`: http://djangoproject.jp/doc/ja/1.0/topics/templates.html#html
