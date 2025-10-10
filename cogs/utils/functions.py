from typing import Optional, Union, Literal
from datetime import datetime


def to_timestamp(
    time_value: Union[int, datetime],
    format: Literal["t", "T", "d", "D", "f", "F", "R"]
) -> str:
    """Converts date data into a discord timestamp."""

    timestamp = int(time_value.timestamp()) if isinstance(time_value, datetime) else time_value

    return f"<t:{timestamp}:{format}>"