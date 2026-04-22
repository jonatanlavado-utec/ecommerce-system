"""
Script para agregar URLs de imágenes a los productos existentes en app_state.pkl.
Ejecutar desde el directorio ecommerce-system:
    python update_images.py
"""
import pickle
import random
import pathlib
from collections import defaultdict

BASE_DIR = pathlib.Path(__file__).parent.resolve()
STATE_FILE = BASE_DIR / "data" / "app_state.pkl"

# Conjunto pequeño de URLs de imágenes reutilizables (picsum para imágenes reales)
# Usamos un grupo pequeño de IDs para no saturar el servicio
IMAGE_URLS = [
    f"https://picsum.photos/seed/{i}/300/300"
    for i in range(1, 11)  # 10 imágenes distintas
]

# Alternativa: imágenes placeholder estáticas (más confiable)
# IMAGE_URLS = [
#     f"https://placehold.co/300x300/2563eb/white?text=Product+{i}"
#     for i in range(1, 11)
# ]


def add_image_urls_to_products(products: list) -> list:
    """Agregar image_url a cada producto usando round-robin."""
    for i, product in enumerate(products):
        if hasattr(product, 'image_url'):
            product.image_url = IMAGE_URLS[i % len(IMAGE_URLS)]
    return products


def rebuild_indexes(products: list) -> dict:
    """Reconstruir índices después de modificar productos."""
    from services.search_service import SearchService
    from services.autocomplete_service import AutocompleteService
    from services.topk_service import TopKService
    from services.fraud_service import FraudService
    from services.order_service import OrderService

    indexes = {
        "search_service": SearchService(),
        "autocomplete_service": AutocompleteService(),
        "topk_service": TopKService(),
        "fraud_service": FraudService(),
        "order_service": OrderService(),
    }

    for product in products:
        indexes["search_service"].add_product(product)
        indexes["autocomplete_service"].add_product(product)
        indexes["topk_service"].add_product(product)

    return indexes


def main():
    print(f"[UPDATE] Buscando estado en: {STATE_FILE}")

    if not STATE_FILE.exists():
        print(f"[ERROR] No se encontró el archivo: {STATE_FILE}")
        return

    # Cargar estado existente
    print(f"[UPDATE] Cargando estado...")
    with open(STATE_FILE, "rb") as f:
        data = pickle.load(f)

    products = data.get("products", [])
    transaction_ids = data.get("transaction_ids", [])
    orders = data.get("orders", [])

    print(f"[UPDATE] Productos actuales: {len(products)}")
    print(f"[UPDATE] Transacciones: {len(transaction_ids)}")
    print(f"[UPDATE] Órdenes: {len(orders)}")

    # Verificar si ya tienen image_url
    sample = products[0] if products else None
    if sample and hasattr(sample, 'image_url') and sample.image_url:
        print(f"[UPDATE] Los productos ya tienen image_url, verificando...")
        # Contar cuántos tienen URL
        with_url = sum(1 for p in products if hasattr(p, 'image_url') and p.image_url)
        print(f"[UPDATE] Productos con image_url: {with_url}/{len(products)}")
        if with_url == len(products):
            print(f"[UPDATE] Ya están actualizados. No hay nada que hacer.")
            return
        print(f"[UPDATE] Actualizando URLs existentes...")

    # Agregar URLs de imágenes
    print(f"[UPDATE] Agregando URLs de imágenes...")
    products = add_image_urls_to_products(products)

    # Reconstruir índices
    print(f"[UPDATE] Reconstruyendo índices...")
    indexes = rebuild_indexes(products)

    # Para transacciones: rebuild fraud service
    for txn_id in transaction_ids:
        indexes["fraud_service"].add_transaction(txn_id)

    # Para órdenes: rebuild order service
    for order in orders:
        actual_order = order[2] if isinstance(order, tuple) and len(order) == 3 else order
        indexes["order_service"].add_order(actual_order)

    # Guardar estado actualizado
    print(f"[UPDATE] Guardando estado actualizado...")
    temp_file = STATE_FILE.with_suffix('.tmp')

    save_data = {
        "initialized": data.get("initialized", True),
        "products_count": len(products),
        "transactions_count": len(transaction_ids),
        "products": products,
        "transaction_ids": transaction_ids,
        "orders": orders,
    }

    with open(temp_file, "wb") as f:
        pickle.dump(save_data, f)

    temp_file.rename(STATE_FILE)

    # Verificar
    with open(STATE_FILE, "rb") as f:
        verify = pickle.load(f)

    sample_products = verify.get("products", [])[:5]
    print(f"\n[UPDATE] ✓ Estado actualizado y guardado")
    print(f"[UPDATE] Total productos: {len(verify.get('products', []))}")
    print(f"[UPDATE] Muestra de URLs asignadas:")
    for p in sample_products:
        print(f"  - {p.sku}: {p.image_url}")


if __name__ == "__main__":
    main()