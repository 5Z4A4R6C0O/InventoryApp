import sqlite3

def inicializar_db():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        categoria TEXT DEFAULT 'sin_categoria',
        stock_actual INTEGER DEFAULT 0,
        stock_minimo INTEGER DEFAULT 5,
        costo_unitario_base DECIMAL(10, 2)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos (
        id_move INTEGER PRIMARY KEY AUTOINCREMENT,
        id_producto INTEGER,
        tipo TEXT CHECK(tipo IN ('ENTRADA', 'SALIDA')) NOT NULL,
        cantidad INTEGER NOT NULL,
        costo_momento DECIMAL(10, 2),
        precio_venta_momento DECIMAL(10, 2),
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ordenes_compra (
        id_orden INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_orden TEXT UNIQUE NOT NULL,
        cliente TEXT,
        estado TEXT CHECK(estado IN ('BORRADOR', 'FINALIZADA', 'CANCELADA')) NOT NULL DEFAULT 'BORRADOR',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_cierre TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ordenes_compra_items (
        id_item INTEGER PRIMARY KEY AUTOINCREMENT,
        id_orden INTEGER NOT NULL,
        id_producto INTEGER NOT NULL,
        sku TEXT NOT NULL,
        nombre_producto TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        costo_momento DECIMAL(10, 2),
        FOREIGN KEY (id_orden) REFERENCES ordenes_compra(id_orden),
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
    )
    """)

    try:
        cursor.execute("INSERT INTO productos (sku, nombre, stock_actual, costo_unitario_base) VALUES ('P001', 'Mouse Gamer', 20, 10.00)")
        cursor.execute("INSERT INTO productos (sku, nombre, stock_actual, costo_unitario_base) VALUES ('P002', 'Teclado', 10, 25.00)")
        conn.commit()
        print("✅ ¡Base de datos y tablas creadas con éxito!")
    except sqlite3.IntegrityError:
        print("⚠️ La base de datos ya existía con esos productos.")
    
    conn.close()

if __name__ == "__main__":
    inicializar_db()
