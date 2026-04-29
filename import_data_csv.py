import sqlite3
import csv
import os
import json

def cargar_configuracion():
    """Carga los sinónimos desde el archivo JSON externo."""
    ruta_config = "config_import.json"
    if not os.path.exists(ruta_config):
        # Si no existe, devolvemos un mapa básico para que no rompa
        return {"sku": ["sku"], "nombre": ["nombre"]}
    
    with open(ruta_config, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("mapa_sinonimos", {})

def importar_desde_csv_flexible():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    # Cargamos el mapa desde el archivo externo
    sinonimos = cargar_configuracion()

    print("\n--- IMPORTACIÓN MASIVA (CONFIGURACIÓN EXTERNA) ---")
    nombre_archivo = input("Nombre del archivo CSV: ")

    if not os.path.exists(nombre_archivo):
        print("❌ Archivo no encontrado.")
        return

    try:
        with open(nombre_archivo, mode='r', encoding='utf-8-sig') as archivo:
            lector = csv.DictReader(archivo)
            mapeo_real = {}
            encabezados_archivo = lector.fieldnames
            
            # Buscamos qué columna del CSV encaja con nuestra DB
            for db_col, lista_sinonimos in sinonimos.items():
                for col_csv in encabezados_archivo:
                    if col_csv.lower().strip() in lista_sinonimos:
                        mapeo_real[db_col] = col_csv
                        break

            if 'sku' not in mapeo_real or 'nombre' not in mapeo_real:
                print("❌ Error: No se detectaron columnas críticas (SKU o Nombre).")
                return

            conteo_nuevos = 0
            conteo_actualizados = 0

            for fila in lector:
                try:
                    sku = fila[mapeo_real['sku']].upper().strip()
                    nombre = fila[mapeo_real['nombre']].strip()
                    stock = int(fila.get(mapeo_real.get('stock_actual', ''), 0))
                    minimo = int(fila.get(mapeo_real.get('stock_minimo', ''), 5))
                    costo = float(fila.get(mapeo_real.get('costo_unitario_base', ''), 0.0))

                    cursor.execute("""
                        INSERT INTO productos (sku, nombre, stock_actual, stock_minimo, costo_unitario_base)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(sku) DO UPDATE SET
                            nombre=excluded.nombre,
                            stock_actual=excluded.stock_actual,
                            stock_minimo=excluded.stock_minimo,
                            costo_unitario_base=excluded.costo_unitario_base
                    """, (sku, nombre, stock, minimo, costo))
                    
                    if cursor.rowcount == 1: conteo_nuevos += 1
                    else: conteo_actualizados += 1

                except Exception as e:
                    print(f"⚠️ Error en fila SKU {sku}: {e}")

            conn.commit()
            print(f"\n✅ Éxito: {conteo_nuevos} nuevos, {conteo_actualizados} actualizados.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        conn.close()