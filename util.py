import re
from datetime import datetime


def date_format(date: datetime) -> str:
    return date.strftime('%a %d %b %Y, %H:%M')

def fee_format(fee: int) -> str:
    return '${:,d}'.format(fee)


def split_name(name: str) -> tuple[str, str]:
    result = re.split(r",\s*", name, maxsplit=1)
    return result[1] if len(result) > 1 else '', result[0]
