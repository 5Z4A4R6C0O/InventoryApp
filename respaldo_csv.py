import sqlite3
import csv
from datetime import datetime

def exportar_inventario_csv():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    # 1. Obtenemos los datos actuales
    cursor.execute("SELECT sku, nombre, stock_actual, stock_minimo, costo_unitario_base FROM productos")
    productos = cursor.fetchall()

    if not productos:
        print("❌ No hay datos para exportar.")
        conn.close()
        return

    # 2. Creamos un nombre de archivo con la fecha actual para no sobrescribir el anterior
    fecha_hoy = datetime.now().strftime("%Y-%m-%d_%H-%M")
    nombre_archivo = f"respaldo_inventario_{fecha_hoy}.csv"

    try:
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo:
            escritor_csv = csv.writer(archivo)
            
            # Escribimos los encabezados (la primera fila del Excel)
            escritor_csv.writerow(['SKU', 'Nombre', 'Stock Actual', 'Stock Minimo', 'Costo Base'])
            
            # Escribimos los datos de los productos
            escritor_csv.writerows(productos)
            
        print(f"✅ Respaldo creado exitosamente: {nombre_archivo}")
    except Exception as e:
        print(f"❌ Error al crear el respaldo: {e}")
    finally:
        conn.close()