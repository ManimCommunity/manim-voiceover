import gettext
import os
from typing import Callable, Optional


def get_gettext(locale: Optional[str] = None, domain: Optional[str] = None) -> Callable[[str], str]:
    ret: Callable[[str], str] = gettext.gettext

    if locale is None:
        locale = os.getenv("LOCALE")

    if domain is None:
        domain = os.getenv("DOMAIN")

    if locale is not None and domain is None:
        raise ValueError("LOCALE is set but DOMAIN is not.")

    if locale is not None:
        assert domain is not None
        # Set gettext language
        trans = gettext.translation(
            domain,
            localedir="locale",
            languages=[locale],
        )
        trans.install()
        ret = trans.gettext

    return ret
