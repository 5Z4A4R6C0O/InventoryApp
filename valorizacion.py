import sqlite3

def reporte_valorizacion():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    print("\n--- REPORTE DE VALORIZACIÓN DE INVENTARIO ---")

    # Calculamos (stock * costo) por producto y la suma total
    query = """
        SELECT 
            sku, 
            nombre, 
            stock_actual, 
            costo_unitario_base,
            (stock_actual * costo_unitario_base) AS valor_total_producto
        FROM productos
        ORDER BY valor_total_producto DESC
    """
    
    try:
        cursor.execute(query)
        productos = cursor.fetchall()

        if not productos:
            print("La base de datos está vacía. No hay valores que calcular.")
            return

        valor_total_almacen = 0
        print(f"{'SKU':<10} | {'PRODUCTO':<20} | {'STOCK':<6} | {'VALOR TOTAL'}")
        print("-" * 60)

        for p in productos:
            sku, nombre, stock, costo, valor_fila = p
            valor_total_almacen += valor_fila
            print(f"{sku:<10} | {nombre:<20} | {stock:<6} | ${valor_fila:>10.2f}")

        # Resumen Final
        producto_top = productos[0] # El primero de la lista por el ORDER BY DESC
        
        print("-" * 60)
        print(f"💵 VALOR TOTAL DEL INVENTARIO: ${valor_total_almacen:,.2f}")
        print(f"🔥 MAYOR INVERSIÓN: {producto_top[1]} ({producto_top[0]}) con ${producto_top[4]:,.2f}")

    except Exception as e:
        print(f"❌ Error al calcular finanzas: {e}")
    finally:
        conn.close()