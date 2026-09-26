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
        if code == config.FALLBACK_LOCALE:
            # The fallback locale itself is required: without it there is
            # nothing left to fall back to, so let the error surface.
            raise
        print(
            f"[DiscordRPC] Unknown locale '{code}', "
            f"falling back to '{config.FALLBACK_LOCALE}'."
        )
        return _load_locale(config.FALLBACK_LOCALE)

    _cache[code] = module.STRINGS
    return module.STRINGS


def t(key: str, **kwargs) -> str:
    """Fetch a localized string by key and format it with kwargs.

    Falls back to the FALLBACK_LOCALE string if the active locale is
    missing that particular key, and to the raw key itself as a last
    resort so a typo never crashes the plugin.
    """
    strings = _load_locale(config.ACTIVE_LOCALE)
    template = strings.get(key)

    if template is None:
        template = _load_locale(config.FALLBACK_LOCALE).get(key, key)

    return template.format(**kwargs)
