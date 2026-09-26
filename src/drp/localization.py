"""
Tiny localization loader.

Each locale lives in locales/<code>.py and exposes a STRINGS dict.
Adding a new language means adding one file there - nothing in this
module or anywhere else needs to change.
"""

import importlib

from . import config

_cache = {}


def _load_locale(code: str) -> dict:
    if code in _cache:
        return _cache[code]

    try:
        module = importlib.import_module(f".locales.{code}", package=__package__)
    except ImportError:
        if code == "en":
            raise  # en.py is required and must always exist
        print(f"[DiscordRPC] Unknown locale '{code}', falling back to 'en'.")
        return _load_locale("en")

    _cache[code] = module.STRINGS
    return module.STRINGS


def t(key: str, **kwargs) -> str:
    """Fetch a localized string by key and format it with kwargs.

    Falls back to the English string if the active locale is missing
    that particular key, and to the raw key itself as a last resort
    so a typo never crashes the plugin.
    """
    strings = _load_locale(config.ACTIVE_LOCALE)
    template = strings.get(key)

    if template is None:
        template = _load_locale("en").get(key, key)

    return template.format(**kwargs)
