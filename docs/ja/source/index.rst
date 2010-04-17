bpmailer ドキュメント
==========================

bpmailerとは？
--------------------------

bpmailerはエンコーディングを守って、メールヘッダーを安定に生成して、 テンプレートでメール内応をかける Djangoアプリです。

Djangoの標準メールAPIを使えば、簡単に電子メールを送信できるんですが、Djangoは内部的にDEFAULT_ENCODINGを使ってしまって、
DjangoのDEFAULT_ENCODING以外のエンコーディングで、標準APIで送信することはできません。EmailMessageクラスのencoding
プロパティを使って、その指定したエンコーディングで送信出来ると思ったら、メールのヘッダーはどうしても、DEFAULT_ENCODING
でエンコードされます。DEFAULT_ENCODINGを変えても、pythonの内部エンコーディング文字列を使って、そのままにヘッダーに
入れてしまって、メールクライアントがそのエンコーディングを認識することを失敗して、メールの内応が化けてしまうことが多い。

bpmailerは世界的に、使っているエンコード文字列をヘッダーに入れてちゃんとクライアントが読めるように、文字コードを
守っているアプリです。DEFAULT_ENCODING以外のエンコーディングを設定することもできます。

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
