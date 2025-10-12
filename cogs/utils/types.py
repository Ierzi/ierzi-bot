from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

class Currency:
    def __init__(self, value: Any) -> None:
        if isinstance(value, Currency):
            self.value = value.value
        else:
            self.value = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @classmethod
    def from_string(cls, value: str) -> 'Currency':
        return cls(Decimal(value.replace(',', '')))

    @classmethod
    def none(cls) -> 'Currency':
        """Class method to represent zero currency."""
        return cls(0)
    
    zero = none

    def to_float(self) -> float:
        """Returns the currency value as a float."""
        return float(self.value)

    def to_decimal(self) -> Decimal:
        """Returns the currency value as a Decimal."""
        return self.value

    def __str__(self) -> str:
        return f"{self.value:,.2f}"

    def  __repr__(self) -> str:
        return f"Currency({self.value})"
    
    def __float__(self) -> float:
        return float(self.value)
    
    def __int__(self) -> int:
        return int(self.value)
    
    def __format__(self, format_spec):
        return format(self.value, format_spec)
    
    def __add__(self, other: Any) -> 'Currency':
        if isinstance(other, Currency):
            return Currency(self.value + other.value)
        
        return Currency(self.value + Decimal(other))

    def __sub__(self, other: Any) -> 'Currency':
        if isinstance(other, Currency):
            return Currency(self.value - other.value)
        
        return Currency(self.value - Decimal(other))
    
    def __mul__(self, other: Any) -> 'Currency':
        if isinstance(other, Currency):
            return Currency(self.value * other.value)
        
        return Currency(self.value * Decimal(other))
    
    def __truediv__(self, other: Any) -> 'Currency':
        if isinstance(other, Currency):
            return Currency(self.value / other.value)
        
        return Currency(self.value / Decimal(other))
    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Currency):
            return self.value == other.value
        
        return self.value == Decimal(other)

    def __neg__(self) -> 'Currency':
        return Currency(-self.value)

    def __pos__(self) -> 'Currency':
        return Currency(+self.value)

    def __eq__(self, value):
        if isinstance(value, Currency):
            return self.value == value.value
        
        return self.value == Decimal(value)
    
    def __ne__(self, value):
        return not self.__eq__(value)
    
    def __lt__(self, value):
        if isinstance(value, Currency):
            return self.value < value.value
        
        return self.value < Decimal(value)
    
    def __le__(self, value):
        if isinstance(value, Currency):
            return self.value <= value.value
        
        return self.value <= Decimal(value)
    
    def __gt__(self, value):
        if isinstance(value, Currency):
            return self.value > value.value
        
        return self.value > Decimal(value)
    
    def __ge__(self, value):
        if isinstance(value, Currency):
            return self.value >= value.value
        
        return self.value >= Decimal(value)
    
    def __hash__(self):
        return hash(self.value)

class BirthdayError(Exception):
    def __init__(self, message: str):
        self.message = message
    
    def __str__(self) -> str:
        return f"BirthdayError: {self.message}"

class Birthday:
    # I think its easier to just use a class for this
    def __init__(self, day: int, month: int, year: Optional[int] = None):
        if year is not None and year < 0:
            raise BirthdayError("Year cannot be negative.")
        if day < 1 or day > 31:
            raise BirthdayError("Day must be between 1 and 31.")
        if month < 1 or month > 12:
            raise BirthdayError("Month must be between 1 and 12.")
        
        self.day = day
        self.month = month
        self.year = year
    
    @classmethod
    def from_datetime(cls, datetime: datetime) -> 'Birthday':
        return cls(datetime.day, datetime.month, datetime.year)
    
    def to_datetime(self, year: Optional[int] = None) -> datetime:
        if year is None:
            year = self.year if self.year is not None else datetime.now().year
        return datetime(year, self.month, self.day)

    def get_age(self) -> int:
        if self.year is None:
            raise BirthdayError("Year is required to get age.")
        
        return datetime.now().year - self.year

    def total_days(self) -> int:
        return self.to_datetime().total_seconds() / 86400

    def __str__(self) -> str:
        return f"{self.day}/{self.month}" if self.year is None else f"{self.day}/{self.month}/{self.year}"
    
    def __repr__(self) -> str:
        return f"Birthday({self.day}/{self.month})" if self.year is None else f"Birthday({self.day}/{self.month}/{self.year})"
    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Birthday):
            if self.year is None or other.year is None:
                return self.day == other.day and self.month == other.month
            
            return self.day == other.day and self.month == other.month and self.year == other.year
        
        if isinstance(other, datetime):
            return self.to_datetime() == other

        return NotImplemented
    
    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)
    
