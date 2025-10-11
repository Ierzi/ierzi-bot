from typing import Optional, Union, Literal
from datetime import datetime


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