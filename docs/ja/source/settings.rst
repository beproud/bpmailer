設定
====================

bpmailerは以下の設定に対応します。プロジェクトの settings.py に設定します。

EMAIL_HEADER_CHARSET_MAP
------------------------------

Pythonの文字コード名前から、メールヘッダーで使う文字コードの名前にマッピングする辞書です。
通常で対応しているエンコーディングは shift-jis, utf8, iso-2022-jp

EMAIL_LOGGER
------------------------------

電子メールに関するロガーの名前。python の標準 logging モジュールを使って、設定のロガーの名前として、ロガーを作成します。
デフォールトは python の logging モジュールのロートロガーです。

EMAIL_CHARSET
----------------------------

電子メールのデフォールトメールエンコーディング。EMAIL_CHARSET を指定しなければ、Django の DEFAULT_ENCODING を使います。

例:

.. code-block:: python

    EMAIL_CHARSET="utf8" 

.. code-block:: python

    EMAIL_CHARSET="cp932" 


EMAIL_ALL_FORWARD
----------------------------

デバグ用の設定です。この設定を指定して、DEBUG は True になった時に、指定したメールアドレスにすべてのメールを転送します。

例:

.. code-block:: python

    EMAIL_ALL_FORWARD="example@example.com" 

EMAIL_DEFAULT_CONTEXT
----------------------------

テンプレートをレンダリングする時に、この設定をテンプレートのコンテキストに通常に入れます。

例:

.. code-block:: python

    EMAIL_DEFAULT_CONTEXT = {
        "site_name": u"マイサイト",
        "copyright": u"2009",
    }

