import random as _random
import string as _string

_PREFIX_SUFFIX_FORMAT = "{prefix}_{suffix}"

def name_with_identifier(prefix: str, id_length: int = 4) -> str:
    suffix: str = "".join(_random.choices(_string.ascii_uppercase + _string.digits, k=id_length))
    return _PREFIX_SUFFIX_FORMAT.format(prefix=prefix, suffix=suffix)

def name_with_suffix(prefix: str, suffix: str) -> str:
    return _PREFIX_SUFFIX_FORMAT.format(prefix=prefix, suffix=suffix)
