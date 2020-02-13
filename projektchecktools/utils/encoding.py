# -*- coding: utf-8 -*-

def encode(text):
    """encode text to CP1252"""
    if not isinstance(text, unicode):
        try:
            u = text.decode('utf8')
        except UnicodeDecodeError:
            u = text.decode('latin1')
        except UnicodeDecodeError:
            u = text.decode('CP1252')
    else:
        u = text
    text_cp1252 = u.encode('CP1252')
    return text_cp1252
