import sqlite3

def buscar_producto_inteligente():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    print("\n--- BUSCADOR INTELIGENTE DE PRODUCTOS ---")
    termino = input("Ingrese nombre o SKU a buscar: ").upper()

    # Usamos LIKE con % para búsqueda parcial
    query = """
        SELECT id_producto, sku, nombre, stock_actual, costo_unitario_base 
        FROM productos 
        WHERE sku LIKE ? OR nombre LIKE ?
    """
    params = (f"%{termino}%", f"%{termino}%")
    cursor.execute(query, params)
    resultados = cursor.fetchall()

    if not resultados:
        print(f"No se encontraron productos que coincidan con: '{termino}'")
    else:
        print(f"\n{'ID':<4} | {'SKU':<10} | {'NOMBRE':<22} | {'STOCK':<8}")
        print("-" * 50)
        for p in resultados:
            print(f"{p[0]:<4} | {p[1]:<10} | {p[2]:<22} | {p[3]:<8}")
        
        # Opcional: Ver historial del primer resultado si solo hay uno o si el usuario elige
        if len(resultados) == 1:
            ver_historial = input("\n¿Desea ver los últimos 5 movimientos de este producto? (s/n): ").lower()
            if ver_historial == 's':
                mostrar_historial_reciente(resultados[0][0])

    conn.close()

def mostrar_historial_reciente(id_prod):
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    
    # Usamos 'localtime' para que SQLite convierta UTC a tu hora local
    cursor.execute("""
        SELECT tipo, cantidad, datetime(fecha, 'localtime') 
        FROM movimientos 
        WHERE id_producto = ? 
        ORDER BY fecha DESC 
        LIMIT 5
    """, (id_prod,))
    
    movs = cursor.fetchall()
    print("\n--- ÚLTIMOS 5 MOVIMIENTOS (Hora Local) ---")
    for m in movs:
        # m[2] ahora tendrá la fecha corregida
        print(f"[{m[2]}] {m[0]}: {m[1]} unidades")
    
    conn.close()