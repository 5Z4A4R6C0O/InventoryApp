import sqlite3


def obtener_alertas_stock_bajo():
    """Devuelve productos con stock actual menor o igual al mínimo aceptable."""
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT sku, nombre, stock_actual, stock_minimo
        FROM productos
        WHERE stock_actual <= stock_minimo
        ORDER BY stock_actual ASC, nombre ASC
        """
    )
    alertas = cursor.fetchall()
    conn.close()
    return alertas


def mostrar_alertas_stock_bajo():
    """Muestra por consola las alertas de stock bajo."""
    alertas = obtener_alertas_stock_bajo()
    print("\n--- ALERTAS DE STOCK BAJO ---")

    if not alertas:
        print("✅ No hay productos con stock bajo en este momento.")
        return

    print(f"{'SKU':<10} | {'PRODUCTO':<22} | {'STOCK':<8} | {'MINIMO':<8}")
    print("-" * 60)
    for sku, nombre, stock_actual, stock_minimo in alertas:
        print(f"{sku:<10} | {nombre:<22} | {stock_actual:<8} | {stock_minimo:<8}")
