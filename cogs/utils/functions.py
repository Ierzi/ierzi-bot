from datetime import datetime, timezone, timedelta
from typing import Literal, Union, Optional
from zoneinfo import ZoneInfo


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

def parse_offset(offset: Optional[str | int]) -> Union[timezone, ZoneInfo]:
    if offset is None:
        return timezone.utc
    
    if isinstance(offset, int):
        if not -24 <= offset <= 24:
            raise ValueError(f"Hour offset must be between -24 and 24, got {offset}")
        return timezone(timedelta(hours=offset))
    
    if isinstance(offset, str):
        s = offset.strip()
        
        if not s:
            raise ValueError("Empty timezone string")
        
        if s.upper() == "UTC":
            return timezone.utc
        
        if s.upper().startswith("UTC"):
            utc_offset = s[3:].strip()
            if not utc_offset:
                return timezone.utc
            
            try:
                if utc_offset.startswith(('+', '-')):
                    hours = _parse_hour_offset(utc_offset)
                else:
                    hours = float(utc_offset)
                
                if not -24 <= hours <= 24:
                    raise ValueError(f"UTC offset must be between -24 and 24 hours, got {hours}")
                
                return timezone(timedelta(hours=hours))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid UTC offset format: {utc_offset}") from e
        
        if s.startswith(('+', '-')):
            try:
                hours = _parse_hour_offset(s)
                if not -24 <= hours <= 24:
                    raise ValueError(f"Hour offset must be between -24 and 24, got {hours}")
                return timezone(timedelta(hours=hours))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid offset format: {s}") from e
        
        try:
            hours = float(s)
            if not -24 <= hours <= 24:
                raise ValueError(f"Hour offset must be between -24 and 24, got {hours}")
            return timezone(timedelta(hours=hours))
        except ValueError:
            pass
        
        try:
            return ZoneInfo(s)
        except Exception as e:
            raise ValueError(f"Invalid timezone: {s}") from e

def _parse_hour_offset(offset_str: str) -> float:
    if not offset_str or not offset_str.startswith(('+', '-')):
        raise ValueError(f"Offset must start with + or -, got: {offset_str}")
    
    sign = 1 if offset_str[0] == '+' else -1
    time_part = offset_str[1:].strip()
    
    if not time_part:
        raise ValueError("Missing time part after +/-")
    
    if len(time_part) == 4 and time_part.isdigit():
        hours = int(time_part[:2])
        minutes = int(time_part[2:])
        if minutes >= 60:
            raise ValueError(f"Invalid minutes: {minutes}")
        return sign * (hours + minutes / 60.0)
    
    if ':' in time_part:
        try:
            parts = time_part.split(':')
            if len(parts) != 2:
                raise ValueError("Invalid HH:MM format")
            hours = int(parts[0])
            minutes = int(parts[1])
            if minutes >= 60:
                raise ValueError(f"Invalid minutes: {minutes}")
            return sign * (hours + minutes / 60.0)
        except ValueError as e:
            raise ValueError(f"Invalid HH:MM format: {time_part}") from e
    
    try:
        return sign * float(time_part)
    except ValueError as e:
        raise ValueError(f"Invalid hour format: {time_part}") from e

def tz_to_str(offset: ZoneInfo | timezone) -> str:
    dt = datetime.now(offset)
    return dt.tzname()
