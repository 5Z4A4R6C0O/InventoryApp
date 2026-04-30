import sqlite3

def añadir_producto_nuevo():
    """Registra un producto que NO existe en el catálogo."""
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    print("\n--- AÑADIR NUEVO PRODUCTO AL CATÁLOGO ---")
    sku = input("SKU (Código único): ").upper()
    nombre = input("Nombre del producto: ")
    stock_inicial = int(input("Stock inicial: "))
    minimo = int(input("Stock mínimo para alerta: "))
    costo = float(input("Costo unitario inicial ($): "))

    try:
        cursor.execute("""
            INSERT INTO productos (sku, nombre, stock_actual, stock_minimo, costo_unitario_base)
            VALUES (?, ?, ?, ?, ?)
        """, (sku, nombre, stock_inicial, minimo, costo))
        
        conn.commit()
        print(f"✅ Producto '{nombre}' añadido con éxito.")
    except sqlite3.IntegrityError:
        print(f"❌ Error: El SKU '{sku}' ya existe en el sistema.")
    finally:
        conn.close()

def retirar_producto():
    """Registra una salida de stock (Venta, Daño, etc.)."""
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    print("\n--- RETIRAR / DAR DE BAJA PRODUCTO ---")
    sku = input("SKU del producto a retirar: ").upper()
    cantidad = int(input("Cantidad a retirar: "))
    motivo = input("Motivo (VENTA/DAÑO/PERDIDA): ").upper()

    try:
        # 1. Verificar existencia y stock
        cursor.execute("SELECT id_producto, stock_actual, costo_unitario_base FROM productos WHERE sku = ?", (sku,))
        resultado = cursor.fetchone()

        if not resultado:
            print("❌ Error: El SKU no existe.")
            return

        id_prod, stock_actual, costo = resultado

        if stock_actual < cantidad:
            print(f"❌ Stock insuficiente. Solo tienes {stock_actual} unidades.")
            return

        # 2. Restar del inventario
        cursor.execute("UPDATE productos SET stock_actual = stock_actual - ? WHERE id_producto = ?", (cantidad, id_prod))

        # 3. Registrar el movimiento (Salida)
        cursor.execute("""
            INSERT INTO movimientos (id_producto, tipo, cantidad, costo_momento)
            VALUES (?, 'SALIDA', ?, ?)
        """, (id_prod, cantidad, costo))

        conn.commit()
        print(f"✅ Retiro exitoso. Stock restante: {stock_actual - cantidad}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
    finally:
        conn.close()
