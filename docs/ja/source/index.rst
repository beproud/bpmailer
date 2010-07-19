bpmailer ドキュメント
==========================

bpmailerとは？
--------------------------

bpmailerはエンコーディングを守って、メールヘッダーを安定に生成して、 テンプレートでメール内応をかける Djangoアプリです。

Djangoの標準メールAPIを使えば、簡単に電子メールを送信できるんですが、文字コードまわりの問題がいくつかあります。日本の携帯電話にメールを送ると、文字化けがよく起こります。

Django標準APIを使うと下記の問題があります:

1. Djangoは内部的に `DEFAULT_CHARSET`_ を使ってしまって、 Djangoの `DEFAULT_CHARSET`_ 以外のエンコーディングを、 ``send_mail`` や、 ``mail_managers`` に指定することができません。
2. Django1.2 で改善されていたんですが、 Django 1.1 では、 `EmailMessage`_ クラスの ``encoding`` プロパティを使って、その指定したエンコーディングで送信することができますが、メールのヘッダーはどうしても、 `DEFAULT_CHARSET`_ でエンコードされます。
3. `DEFAULT_CHARSET`_ を変えても、pythonの内部エンコーディング文字列 (cp932、iso-2022-jp-2等) を使って、そのままにヘッダーに入れてしまって、メールクライアントがそのエンコーディングを認識することを失敗して、メールの内応が化けてしまうことが多い。

bpmailerは世界的に使っているエンコード文字列をヘッダーに入れてちゃんとクライアントが読めるように、文字コードを守っているアプリです。 `DEFAULT_CHARSET`_ 以外のエンコーディングを設定することもできます。

ソースリポジトリ
--------------------------

https://project.beproud.jp/hg/bpmailer/

目次:

.. toctree::
  :numbered:
  :maxdepth: 1

  sending_mail
  settings
.. api
.. templates
.. supported_encodings
.. logging

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _`DEFAULT_CHARSET`: http://djangoproject.jp/doc/ja/1.0/ref/settings.html#default-charset
.. _`EmailMessage`: http://djangoproject.jp/doc/ja/1.0/topics/email.html#emailmessage-smtpconnection
