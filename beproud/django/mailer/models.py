#:coding=utf-8:
import six

from django.conf import settings

from email import charset
from email.charset import (
    add_alias, add_charset, add_codec,
    BASE64, SHORTEST,
)

__all__ = ('init_mailer',)


# Uppercase charset aliases cause inequality checks
# with input and output encodings to fail thus causing
# double encoding of base64 body text parts.
if six.PY2:
    def _safe_str(self):
        return self.input_charset
    charset.Charset.__str__ = _safe_str


# Python charset => mail header charset mapping
# TODO: Add more encodings
CHARSETS = getattr(settings, "EMAIL_CHARSETS", {
    'utf-8': {
        'header_enc': SHORTEST,
        'body_enc': None,
        'output_charset': None,
    },
    'shift-jis': {
        'header_enc': BASE64,
        'body_enc': None,
        'output_charset': None,
    },
    'iso-2022-jp': {
        'header_enc': BASE64,
        'body_enc': None,
        'output_charset': None,
    },
    'iso-2022-jp-2': {
        'header_enc': BASE64,
        'body_enc': None,
        'output_charset': None,
    },
    'iso-2022-jp-3': {
        'header_enc': BASE64,
        'body_enc': None,
        'output_charset': None,
    },
    'iso-2022-jp-ext': {
        'header_enc': BASE64,
        'body_enc': None,
        'output_charset': None,
    },
})

ALIASES = getattr(settings, "EMAIL_CHARSET_ALIASES", {
    # utf-8
    "utf8": "utf-8",
    "utf_8": "utf-8",
    "U8": "utf-8",
    "UTF": "utf-8",
    "utf8": "utf-8",
    "utf-8": "utf-8",

    # Shift-JIS
    "cp932": "shift-jis",
    "932": "shift-jis",
    "ms932": "shift-jis",
    "mskanji": "shift-jis",
    "ms-kanji": "shift-jis",

    "shift_jis": "shift-jis",
    "csshiftjis": "shift-jis",
    "shiftjis": "shift-jis",
    "sjis": "shift-jis",
    "s_jis": "shift-jis",

    #"shift_jis_2004": "shift-jis",
    #"shiftjis2004": "shift-jis",
    #"sjis_2004": "shift-jis",
    #"sjis2004": "shift-jis",
    #
    #"shift_jisx0213": "shift-jis",
    #"shiftjisx0213": "shift-jis",
    #"sjisx0213": "shift-jis",
    #"s_jisx0213": "shift-jis",

    # ISO-2022-JP
    "iso2022_jp": "iso-2022-jp",
    "scsiso2022jp": "iso-2022-jp",
    "iso2022jp": "iso-2022-jp",
    "iso-2022-jp": "iso-2022-jp",
    "iso-2022-jp": "iso-2022-jp",
    "iso-2022-jp-1": "iso-2022-jp",

    "iso-2022-jp-2": "iso-2022-jp-2",
    "iso2022_jp_2": "iso-2022-jp-2",
    "iso2022jp-2": "iso-2022-jp-2",
    "iso2022_jp_2004": "iso-2022-jp-2",
    "iso2022jp-2004": "iso-2022-jp-2",
    "iso-2022-jp-2004": "iso-2022-jp-2",

    "iso2022_jp_3": "iso-2022-jp-3",
    "iso2022jp-3": "iso-2022-jp-3",
    "iso-2022-jp-3": "iso-2022-jp-3",

    # TODO: 携帯は対応してないと
    "iso2022_jp_ext": "iso-2022-jp-ext",
    "iso2022jp-ext": "iso-2022-jp-ext",
    "iso-2022-jp-ext": "iso-2022-jp-ext",
})
CODECS = getattr(settings, "EMAIL_CHARSET_CODECS", {
    'iso-2022-jp': 'iso-2022-jp',
    'iso-2022-jp-2': 'iso-2022-jp-2',
    'iso-2022-jp-3': 'iso-2022-jp-3',
    'iso-2022-jp-ext': 'iso2022jp-ext',
    'utf-8': 'utf-8',
    'shift-jis': 'cp932',
})


def init_mailer():
    if CHARSETS:
        for canonical, charset_dict in six.iteritems(CHARSETS):
            add_charset(canonical, **charset_dict)

    if ALIASES:
        for alias, canonical in six.iteritems(ALIASES):
            add_alias(alias, canonical)

    if CODECS:
        for canonical, codec_name in six.iteritems(CODECS):
            add_codec(canonical, codec_name)


init_mailer()
