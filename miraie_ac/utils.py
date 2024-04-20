# Write a function check if the given string is a valid email address.

import re


def is_valid_email(addr):
    if re.match(r"^[0-9a-zA-Z\.\_]+\@[0-9a-zA-Z]+\.[0-9a-zA-Z]+$", addr):
        return True
    else:
        return False


def toFloat(value: str) -> float:
    if value is None:
        return -1.0
    try:
        return float(value)
    except ValueError:
        return -1.0
