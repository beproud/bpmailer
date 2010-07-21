設定
====================

bpmailerは以下の設定に対応します。プロジェクトの settings.py に設定します。

.. _setting-email-logger:

EMAIL_LOGGER
------------------------------

電子メールに関するロガーの名前。 `Python の標準 logging モジュール`_ を使って、設定のロガーの名前として、ロガーを作成します。
デフォールトは python の logging モジュールのロートロガーです。

.. _setting-email-charset:

EMAIL_CHARSET
----------------------------

電子メールのデフォールトメールエンコーディング。 ``EMAIL_CHARSET`` を指定しなければ、Django の `DEFAULT_CHARSET`_ を使います。

例:

.. code-block:: python

    EMAIL_CHARSET="utf8" 

.. code-block:: python

    EMAIL_CHARSET="cp932" 

.. _setting-email-all-forward:

EMAIL_ALL_FORWARD
----------------------------

デバグ用の設定です。この設定を指定して、DEBUG は True になった時に、指定したメールアドレスにすべてのメールを転送します。

例:

.. code-block:: python

    EMAIL_ALL_FORWARD="example@example.com" 


.. _setting-email-charsets:

EMAIL_CHARSETS
------------------------------

`Python email モジュール`_ に追従する文字コードのエンコーディング設定。ここで、メールのヘッダーとボディのエンコーディングを設定できます。ここで設定したエンコーディングを ``add_charset()`` で `Python email モジュール`_ に登録する。

bpmailer のデフォールト設定は以下になります。

.. code-block:: python 

    from email.charset import SHORTEST, BASE64


    EMAIL_CHARSETS = {
        'UTF-8': {
            'header_enc': SHORTEST,
            'body_enc': BASE64,
            'output_charset': None,
        },
        'SHIFT-JIS': {
            'header_enc': BASE64,
            'body_enc': None,
            'output_charset': None,
        },
        'ISO-2022-JP': {
            'header_enc': BASE64,
            'body_enc': None,
            'output_charset': None,
        },
        'ISO-2022-JP-2': {
            'header_enc': BASE64,
            'body_enc': None,
            'output_charset': None,
        },
        'ISO-2022-JP-3': {
            'header_enc': BASE64,
            'body_enc': None,
            'output_charset': None,
        },
        'ISO-2022-JP-EXT': {
            'header_enc': BASE64,
            'body_enc': None,
            'output_charset': None,
        },
    }

.. _setting-email-charset-aliases:

EMAIL_CHARSET_ALIASES
------------------------------

`Python email モジュール`_ に追従する文字コードのエーリアす設定。ここで、エーリアすの文字コードの正式名称を設定できます。ここで設定したエーリアすを ``add_alias()`` で `Python email モジュール`_ に登録する。

bpmailer のデフォールト設定は以下になります。

.. code-block:: python 

    EMAIL_CHARSET_ALIASES = {
        # UTF-8
        "utf8": "UTF-8",
        "utf_8": "UTF-8",
        "U8": "UTF-8",
        "UTF": "UTF-8",
        "utf8": "UTF-8",
        "utf-8": "UTF-8",

        # Shift-JIS
        "cp932": "SHIFT-JIS",
        "932": "SHIFT-JIS",
        "ms932": "SHIFT-JIS",
        "mskanji": "SHIFT-JIS",
        "ms-kanji": "SHIFT-JIS",

        "shift_jis": "SHIFT-JIS",
        "csshiftjis": "SHIFT-JIS",
        "shiftjis": "SHIFT-JIS",
        "sjis": "SHIFT-JIS",
        "s_jis": "SHIFT-JIS",
        
        #"shift_jis_2004": "SHIFT-JIS",
        #"shiftjis2004": "SHIFT-JIS",
        #"sjis_2004": "SHIFT-JIS",
        #"sjis2004": "SHIFT-JIS",
        #
        #"shift_jisx0213": "SHIFT-JIS",
        #"shiftjisx0213": "SHIFT-JIS",
        #"sjisx0213": "SHIFT-JIS",
        #"s_jisx0213": "SHIFT-JIS",

        # ISO-2022-JP
        "iso2022_jp": "ISO-2022-JP",
        "scsiso2022jp": "ISO-2022-JP",
        "iso2022jp": "ISO-2022-JP",
        "iso-2022-jp": "ISO-2022-JP",
        "iso-2022-jp": "ISO-2022-JP",
        "iso-2022-jp-1": "ISO-2022-JP",

        "iso-2022-jp-2": "ISO-2022-JP-2",
        "iso2022_jp_2": "ISO-2022-JP-2",
        "iso2022jp-2": "ISO-2022-JP-2",
        "iso2022_jp_2004": "ISO-2022-JP-2",
        "iso2022jp-2004": "ISO-2022-JP-2",
        "iso-2022-jp-2004": "ISO-2022-JP-2",

        "iso2022_jp_3": "ISO-2022-JP-3",
        "iso2022jp-3": "ISO-2022-JP-3",
        "iso-2022-jp-3": "ISO-2022-JP-3",

        # TODO: 携帯は対応してないと
        "iso2022_jp_ext": "ISO-2022-JP-EXT",
        "iso2022jp-ext": "ISO-2022-JP-EXT",
        "iso-2022-jp-ext": "ISO-2022-JP-EXT",
    }

.. _setting-email-charset-codecs:

EMAIL_CHARSET_CODECS
------------------------------
`Python email モジュール`_ に追従する文字コードの正式名称を内部文字コードにマッピングする設定。ここで、文字コードの正式名称を設定できます。ここで設定したコーデックを ``add_codec()`` で `Python email モジュール`_ に登録する。

bpmailer のデフォールト設定は以下になります。

.. code-block:: python 

    EMAIL_CHARSET_CODECS = {
        'ISO-2022-JP': 'iso-2022-jp',
        'ISO-2022-JP-2': 'iso-2022-jp-2',
        'ISO-2022-JP-3': 'iso-2022-jp-3',
        'ISO-2022-JP-EXT': 'iso2022jp-ext',
        'UTF-8': 'utf-8',
        'SHIFT-JIS': 'cp932',
    }

.. _`Python email モジュール`: http://www.python.jp/doc/2.5/lib/module-email.charset.html
.. _`DEFAULT_CHARSET`: http://djangoproject.jp/doc/ja/1.0/ref/settings.html#default-charset
.. _`Python の標準 logging モジュール`: http://www.python.jp/doc/2.5/lib/module-logging.html
