# vim:fileencoding=utf-8

from django.conf import settings
from email.charset import ALIASES

# Python charset => mail header charset mapping
# TODO: Add more encodings
ALIASES.update(getattr(settings, "EMAIL_CHARSET_ALIASES", {
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
    
    "shift_jis_2004": "SHIFT-JIS",
    "shiftjis2004": "SHIFT-JIS",
    "sjis_2004": "SHIFT-JIS",
    "sjis2004": "SHIFT-JIS",
    
    "shift_jisx0213": "SHIFT-JIS",
    "shiftjisx0213": "SHIFT-JIS",
    "sjisx0213": "SHIFT-JIS",
    "s_jisx0213": "SHIFT-JIS",

    # ISO-2022-JP
    "iso2022_jp": "ISO-2022-JP",
    "scsiso2022jp": "ISO-2022-JP",
    "iso2022jp": "ISO-2022-JP",
    "iso-2022-jp": "ISO-2022-JP",
    "iso-2022-jp": "ISO-2022-JP",
    "iso-2022-jp-1": "ISO-2022-JP",
    "iso2022_jp_2": "ISO-2022-JP",
    "iso2022jp-2": "ISO-2022-JP",
    "iso-2022-jp-2": "ISO-2022-JP",
    "iso-2022-jp-2": "ISO-2022-JP",
    "iso2022_jp_2004": "ISO-2022-JP",
    "iso2022jp-2004": "ISO-2022-JP",
    "iso-2022-jp-2004": "ISO-2022-JP",
    "iso2022_jp_3": "ISO-2022-JP",
    "iso2022jp-3": "ISO-2022-JP",
    "iso-2022-jp-3": "ISO-2022-JP",
    "iso2022_jp_ext": "ISO-2022-JP",
    "iso2022jp-ext": "ISO-2022-JP",
    "iso-2022-jp-ext": "ISO-2022-JP",
}))

