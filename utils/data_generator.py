"""Dataset generator for products and transactions."""

import random
import string
from typing import Iterator, Optional
from dataclasses import dataclass
from models.models import Product, Order, OrderPriority

CATEGORIES = [
    "laptop", "phone", "tablet", "headphones", "camera", "watch", "speaker",
    "mouse", "keyboard", "monitor", "printer", "router", "charger", "cable",
    "case", "stand", "mount", "fan", "light", "bulb", "strip", "plug", "sensor",
    "tv", "fridge", "washer", "dryer", "microwave", "oven", "blender", "mixer",
    "iron", "vacuum", "drone", "console", "gamepad", "webcam", "ssd", "hdd",
    "ram", "gpu", "cpu", "motherboard", "psu", "case_pc", "cooling", "cable_net"
]

ADJECTIVES = [
    "premium", "wireless", "smart", "portable", "compact", "powerful", "ultra",
    "pro", "elite", "advanced", "essential", "classic", "modern", "sleek",
    "fast", "quiet", "energy", "digital", "automatic", "manual", "heavy", "light",
    "mini", "mega", "super", "hyper", "turbo", "eco", "biz", "home"
]

BRANDS = [
    "TechPro", "SmartGear", "ElectroMax", "PowerPlus", "DigiHub", "FutureTech",
    "PrimeElec", "UltraWare", "MegaSoft", "GlobalTech", "TechZone", "ElectroHub",
    "ProMax", "EliteGear", "TopLine", "PrimeTech", "ElectroPro", "MaxiTech"
]

# URLs de imágenes reutilizables (round-robin)
IMAGE_URLS = [
    f"https://picsum.photos/seed/{i}/300/300"
    for i in range(1, 11)
]


@dataclass
class Transaction:
    """Lightweight transaction event for fraud detection and top-K."""
    id: str
    user_id: str
    amount: float
    transaction_type: str  # 'purchase', 'refund', 'dispute'


def generate_sku() -> str:
    """Generate a random SKU with better distribution."""
    prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"SKU-{random.randint(100000, 999999)}-{prefix}"


def generate_product_name() -> str:
    """Generate a realistic product name."""
    adj = random.choice(ADJECTIVES)
    cat = random.choice(CATEGORIES)
    brand = random.choice(BRANDS)
    return f"{brand} {adj.title()} {cat.title()}"


def generate_products(count: int) -> Iterator[Product]:
    """Generate products lazily using a generator - memory efficient."""
    for i in range(count):
        category = random.choice(CATEGORIES)
        yield Product(
            id=f"prod_{i:08d}",
            sku=generate_sku(),
            name=generate_product_name(),
            price=round(random.uniform(9.99, 2999.99), 2),
            sales=random.randint(0, 500000),
            image_url=IMAGE_URLS[i % len(IMAGE_URLS)],
            category=category
        )


def generate_transactions(count: int) -> Iterator[Transaction]:
    """Generate transaction events lazily - does NOT store all in memory."""
    types = ['purchase', 'purchase', 'purchase', 'purchase', 'refund', 'dispute']
    for i in range(count):
        yield Transaction(
            id=f"txn_{i:010d}",
            user_id=f"user_{random.randint(1, 5000000):07d}",
            amount=round(random.uniform(5.0, 5000.0), 2),
            transaction_type=random.choice(types)
        )


def generate_orders_from_transactions(
    transactions: Iterator[Transaction],
    product_ids: list[str]
) -> Iterator[Order]:
    """Generate orders derived from transactions."""
    for txn in transactions:
        if txn.transaction_type == 'purchase':
            num_products = random.randint(1, min(5, len(product_ids)))
            yield Order(
                id=txn.id,
                customer_id=txn.user_id,
                product_ids=random.sample(product_ids, num_products),
                priority=random.choice(list(OrderPriority)),
                total=txn.amount
            )


def estimate_memory_size(products_count: int, transactions_count: int) -> dict:
    """Estimate memory usage for the dataset."""
    product_size = 150
    transaction_size = 80
    return {
        "products_count": products_count,
        "estimated_products_memory_mb": (products_count * product_size) / (1024 * 1024),
        "transactions_count": transactions_count,
        "estimated_transactions_memory_mb": (transactions_count * transaction_size) / (1024 * 1024),
        "note": "Transactions are NOT stored - only probabilistic structures"
    }
