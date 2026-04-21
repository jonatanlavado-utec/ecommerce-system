"""Data models for the ecommerce system."""

from dataclasses import dataclass
from enum import IntEnum


class OrderPriority(IntEnum):
    """Order priority levels."""
    EXPRESS = 1
    STANDARD = 2
    SCHEDULED = 3


@dataclass
class Product:
    """Product model."""
    id: str
    sku: str
    name: str
    price: float
    sales: int


@dataclass
class Order:
    """Order model."""
    id: str
    customer_id: str
    product_ids: list[str]
    priority: OrderPriority
    total: float
