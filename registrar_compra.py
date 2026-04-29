import sqlite3

def registrar_compra():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    print("\n--- REGISTRAR ENTRADA DE MERCANCÍA ---")
    sku = input("SKU del producto: ").upper()
    cantidad = int(input("Cantidad recibida: "))
    nuevo_costo = float(input("Costo unitario de esta compra ($): "))

    try:
        # 1. Buscamos el producto por SKU
        cursor.execute("SELECT id_producto, stock_actual FROM productos WHERE sku = ?", (sku,))
        producto = cursor.fetchone()

        if not producto:
            print("❌ Error: El SKU no existe. Primero debes crear el producto.")
            return

        id_prod, stock_viejo = producto

        # 2. Actualizamos el stock y el costo base en la tabla 'productos'
        cursor.execute("""
            UPDATE productos 
            SET stock_actual = stock_actual + ?, 
                costo_unitario_base = ? 
            WHERE id_producto = ?
        """, (cantidad, nuevo_costo, id_prod))

        # 3. Guardamos el movimiento en el historial para el cálculo de finanzas futuro
        cursor.execute("""
            INSERT INTO movimientos (id_producto, tipo, cantidad, costo_momento) 
            VALUES (?, 'ENTRADA', ?, ?)
        """, (id_prod, cantidad, nuevo_costo))

        conn.commit()
        print(f"✅ Éxito. Nuevo stock: {stock_viejo + cantidad}. Costo actualizado a ${nuevo_costo}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error en la transacción: {e}")
    finally:
        conn.close()

"""if __name__ == "__main__":
    registrar_compra()"""