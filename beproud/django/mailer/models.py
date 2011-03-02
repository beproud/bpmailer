# vim:fileencoding=utf-8

from django.conf import settings

from email import charset
from email.charset import (
    add_alias, add_charset, add_codec,
    QP, BASE64, SHORTEST,
)

__all__ = ('init_mailer')

# Uppercase charset aliases cause inequality checks
# with input and output encodings to fail thus causing
# double encoding of base64 body text parts.
_OldCharset = charset.Charset
class SafeCharset(_OldCharset):
    def __str__(self):
        return self.input_charset
charset.Charset = SafeCharset

# Python charset => mail header charset mapping
# TODO: Add more encodings
CHARSETS = getattr(settings, "EMAIL_CHARSETS", {
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
})

ALIASES = getattr(settings, "EMAIL_CHARSET_ALIASES", {
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
})
CODECS = getattr(settings, "EMAIL_CHARSET_CODECS", {
    'ISO-2022-JP': 'iso-2022-jp',
    'ISO-2022-JP-2': 'iso-2022-jp-2',
    'ISO-2022-JP-3': 'iso-2022-jp-3',
    'ISO-2022-JP-EXT': 'iso2022jp-ext',
    'UTF-8': 'utf-8',
    'SHIFT-JIS': 'cp932',
})

def init_mailer():
    if CHARSETS:
        for canonical, charset_dict in CHARSETS.iteritems():
            add_charset(canonical, **charset_dict)

    if ALIASES:
        for alias, canonical in ALIASES.iteritems():
            add_alias(alias, canonical)

    if CODECS:
        for canonical, codec_name in CODECS.iteritems():
            add_codec(canonical, codec_name)

init_mailer()
