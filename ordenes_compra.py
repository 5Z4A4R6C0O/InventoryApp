import sqlite3
from datetime import datetime


def asegurar_tablas_ordenes(db_path="inventario.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ordenes_compra (
            id_orden INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_orden TEXT UNIQUE NOT NULL,
            cliente TEXT,
            estado TEXT CHECK(estado IN ('BORRADOR', 'FINALIZADA', 'CANCELADA')) NOT NULL DEFAULT 'BORRADOR',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_cierre TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
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
        """
    )
    conn.commit()
    conn.close()


def crear_orden_borrador(cliente, items, db_path="inventario.db"):
    """
    items: [{"sku": "P001", "cantidad": 2}, ...]
    """
    if not items:
        raise ValueError("La orden no puede crearse sin items.")

    asegurar_tablas_ordenes(db_path=db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    codigo_orden = f"OC-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
    cursor.execute(
        "INSERT INTO ordenes_compra (codigo_orden, cliente, estado) VALUES (?, ?, 'BORRADOR')",
        (codigo_orden, cliente or "Consumidor final"),
    )
    id_orden = cursor.lastrowid

    for item in items:
        sku = item["sku"].upper().strip()
        cantidad = int(item["cantidad"])
        if cantidad <= 0:
            raise ValueError(f"Cantidad invalida para SKU {sku}.")

        cursor.execute(
            "SELECT id_producto, nombre, costo_unitario_base FROM productos WHERE sku = ?",
            (sku,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"SKU no existe: {sku}")
        id_prod, nombre, costo = row

        cursor.execute(
            """
            INSERT INTO ordenes_compra_items (id_orden, id_producto, sku, nombre_producto, cantidad, costo_momento)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (id_orden, id_prod, sku, nombre, cantidad, costo),
        )

    conn.commit()
    conn.close()
    return codigo_orden


def finalizar_orden(codigo_orden, db_path="inventario.db"):
    asegurar_tablas_ordenes(db_path=db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id_orden, estado FROM ordenes_compra WHERE codigo_orden = ?", (codigo_orden,))
    orden = cursor.fetchone()
    if not orden:
        conn.close()
        raise ValueError("La orden no existe.")
    id_orden, estado = orden
    if estado != "BORRADOR":
        conn.close()
        raise ValueError(f"La orden no se puede finalizar (estado actual: {estado}).")

    cursor.execute(
        "SELECT id_producto, sku, cantidad, costo_momento FROM ordenes_compra_items WHERE id_orden = ?",
        (id_orden,),
    )
    items = cursor.fetchall()
    if not items:
        conn.close()
        raise ValueError("La orden no tiene items.")

    for id_producto, sku, cantidad, _costo in items:
        cursor.execute("SELECT stock_actual FROM productos WHERE id_producto = ?", (id_producto,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Producto inexistente en orden: {sku}")
        if row[0] < cantidad:
            conn.close()
            raise ValueError(f"Stock insuficiente para {sku}. Disponible: {row[0]}, requerido: {cantidad}")

    for id_producto, _sku, cantidad, costo in items:
        cursor.execute(
            "UPDATE productos SET stock_actual = stock_actual - ? WHERE id_producto = ?",
            (cantidad, id_producto),
        )
        cursor.execute(
            """
            INSERT INTO movimientos (id_producto, tipo, cantidad, costo_momento)
            VALUES (?, 'SALIDA', ?, ?)
            """,
            (id_producto, cantidad, costo),
        )

    cursor.execute(
        "UPDATE ordenes_compra SET estado = 'FINALIZADA', fecha_cierre = CURRENT_TIMESTAMP WHERE id_orden = ?",
        (id_orden,),
    )
    conn.commit()
    conn.close()


def cancelar_orden(codigo_orden, db_path="inventario.db"):
    asegurar_tablas_ordenes(db_path=db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT estado FROM ordenes_compra WHERE codigo_orden = ?", (codigo_orden,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("La orden no existe.")
    if row[0] != "BORRADOR":
        conn.close()
        raise ValueError(f"La orden no se puede cancelar (estado actual: {row[0]}).")

    cursor.execute(
        "UPDATE ordenes_compra SET estado = 'CANCELADA', fecha_cierre = CURRENT_TIMESTAMP WHERE codigo_orden = ?",
        (codigo_orden,),
    )
    conn.commit()
    conn.close()


def listar_ordenes(limit=100, db_path="inventario.db"):
    asegurar_tablas_ordenes(db_path=db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT codigo_orden, cliente, estado, datetime(fecha_creacion, 'localtime'), datetime(fecha_cierre, 'localtime')
        FROM ordenes_compra
        ORDER BY fecha_creacion DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
