from decimal import Decimal, ROUND_HALF_UP
from typing import Any

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
        return float(self.value)

    def to_decimal(self) -> Decimal:
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

