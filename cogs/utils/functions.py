from datetime import datetime, timezone, timedelta
from typing import Literal, Union


def to_timestamp(
    time_value: Union[int, datetime],
    format: Literal["t", "T", "d", "D", "f", "F", "R"],
    *,
    next_year: bool = False,
    previous_year: bool = False
) -> str:
    """Converts date data into a discord timestamp."""

    if format == "R" and isinstance(time_value, datetime):
        if next_year:
            _next_year = time_value.year + 1
            time_value = time_value.replace(year=_next_year)
        elif previous_year:
            _previous_year = time_value.year - 1
            time_value = time_value.replace(year=_previous_year)
    
    timestamp = int(time_value.timestamp()) if isinstance(time_value, datetime) else time_value

    return f"<t:{timestamp}:{format}>"


def to_ordinal(number: int) -> str:
    """Converts a number into a ordinal number (1 -> 1st, 2 -> 2nd, 3 -> 3rd, 4 -> 4th, etc.)"""
    number_str = str(number)
    if number_str.endswith("1") and not number_str.endswith("11"):
        return number_str + "st"
    elif number_str.endswith("2") and not number_str.endswith("12"):
        return number_str + "nd"
    elif number_str.endswith("3") and not number_str.endswith("13"):
        return number_str + "rd"
    else:
        return number_str + "th"

def parse_offset(offset: str | int) -> timezone:
    if isinstance(offset, int):
        return timezone(timedelta(hours=offset))
    elif isinstance(offset, str):
        try:
            return timezone(timedelta(hours=int(offset)))
        except ValueError:
            # Maybe its UTC+smth or UTC-smth
            if offset.startswith("UTC"):
                offset = offset[3:]
            return timezone(timedelta(hours=int(offset)))
