import sqlite3

def ver_historial_producto():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    print("\n--- AUDITORÍA DE MOVIMIENTOS POR SKU ---")
    sku = input("Ingrese el SKU del producto: ").upper()

    # 1. Primero obtenemos el ID y nombre para confirmar que existe
    cursor.execute("SELECT id_producto, nombre FROM productos WHERE sku = ?", (sku,))
    producto = cursor.fetchone()

    if not producto:
        print(f"❌ El SKU '{sku}' no existe en el sistema.")
        conn.close()
        return

    id_prod, nombre = producto
    
    # 2. Consultamos todos los movimientos de ese ID
    cursor.execute("""
        SELECT tipo, cantidad, costo_momento, datetime(fecha, 'localtime') 
        FROM movimientos 
        WHERE id_producto = ? 
        ORDER BY fecha DESC
    """, (id_prod,))
    
    movimientos = cursor.fetchall()

    print(f"\nHistorial para: {nombre} ({sku})")
    print(f"{'FECHA Y HORA':<20} | {'TIPO':<8} | {'CANT':<5} | {'COSTO/REF'}")
    print("-" * 60)

    if not movimientos:
        print("No hay registros de movimientos para este producto.")
    else:
        for m in movimientos:
            # m[3] es la fecha local, m[0] tipo, m[1] cantidad, m[2] costo
            print(f"{m[3]:<20} | {m[0]:<8} | {m[1]:<5} | ${m[2]}")

    conn.close()