import sqlite3

def mostrar_inventario():
    # Nos conectamos al archivo que acabas de crear
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    print("\n--- ESTADO ACTUAL DEL INVENTARIO ---")
    
    # Pedimos todos los productos
    cursor.execute("SELECT id_producto, sku, nombre, stock_actual, costo_unitario_base FROM productos")
    productos = cursor.fetchall()

    if not productos:
        print("La base de datos está vacía.")
    else:
        # Formateamos la salida para que sea legible
        print(f"{'ID':<4} | {'SKU':<8} | {'NOMBRE':<20} | {'STOCK':<7} | {'COSTO':<8}")
        print("-" * 60)
        for p in productos:
            print(f"{p[0]:<4} | {p[1]:<8} | {p[2]:<20} | {p[3]:<7} | ${p[4]:<8}")

    conn.close()

if __name__ == "__main__":
    mostrar_inventario()