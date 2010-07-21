====================================
メールロギング
====================================

bpmailer は `Python の logging モジュール`_ を使っています。メールを送信する時、エラーが起こる時等に、ログに記録します。

bpmailer は :ref:`EMAIL_LOGGER <setting-email-logger>` のロガーを使います。 ``EMAIL_LOGGER`` が設定されてない場合は、
``logging`` モジュールのルートロガーを使います。

メールログを記録する
---------------------------

メールを送信する時に、 ``INFO`` レベルでロギングします。 ``INFO`` レベルのロギングを設定すると、メールログをとれます。

ファイルでロギングする場合

.. code-block:: python

    import logging
    LOG_FILENAME="/path/to/app_mail.log"
    EMAIL_LOGGER="email"
    logger = logging.getLogger(EMAIL_LOGGER)
    logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(
                  LOG_FILENAME, maxBytes=20, backupCount=5)

    my_logger.addHandler(handler)

`Jogging`_ を使う場合

.. code-block:: python

    import logging
    from jogging.handlers import DatabaseHandler, EmailHandler

    EMAIL_LOGGER = 'mail'
    GLOBAL_LOG_LEVEL = logging.WARNING
    GLOBAL_LOG_HANDLERS = [DatabaseHandler()] # takes any Handler object that Python's logging takes
    LOGGING = {
        EMAIL_LOGGER: {
            'handlers': [
                { 'handler': EmailHandler(fail_silently=True), 'level': logging.ERROR },
            ]
        },
    }

.. _`Python の logging モジュール`: http://www.python.jp/doc/2.5/lib/module-logging.html
.. _`Jogging`: http://bitbucket.org/beproud/jogging/
