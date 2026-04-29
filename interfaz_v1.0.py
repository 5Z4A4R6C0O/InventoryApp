import csv
import json
import os
import sqlite3
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from alerta_stock import obtener_alertas_stock_bajo
from categorizacion_automatica import (
    agregar_categoria,
    agregar_palabra_clave,
    asegurar_columna_categoria,
    construir_motor_categorizacion,
    categorizar_nombre_producto,
    categorizar_todos_los_productos,
    eliminar_categoria,
    eliminar_palabra_clave,
    obtener_categorias_configuradas,
    obtener_categorias_disponibles,
    obtener_palabras_categoria,
    obtener_puntajes_categorizacion,
)
from ordenes_compra import (
    asegurar_tablas_ordenes,
    cancelar_orden,
    crear_orden_borrador,
    finalizar_orden,
    listar_ordenes,
)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppInventario(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestion de Inventario V1.0")
        self.geometry("1280x760")
        self.minsize(1080, 680)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.tema_actual = ctk.StringVar(value="Sistema")

        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(12, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.grid(row=0, column=1, padx=16, pady=16, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)

        self._filas_actuales = []
        self._motor_categorizacion = construir_motor_categorizacion()

        self._build_sidebar()
        self._build_main_area()
        self._aplicar_estilo_por_tema()
        asegurar_columna_categoria()
        asegurar_tablas_ordenes()
        categorizar_todos_los_productos()
        self._actualizar_filtro_categorias()
        self._mostrar_alertas_inicio()
        self.mostrar_inventario()

    def _build_sidebar(self):
        ctk.CTkLabel(
            self.sidebar_frame,
            text="INVENTARIO\nV1.0",
            font=ctk.CTkFont(size=24, weight="bold"),
            justify="center",
        ).grid(row=0, column=0, padx=16, pady=(24, 8), sticky="ew")

        ctk.CTkLabel(
            self.sidebar_frame,
            text="Acciones principales",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=1, column=0, padx=16, pady=(12, 4), sticky="w")

        botones = [
            ("1) Ver Inventario", self.mostrar_inventario),
            ("2) Anadir Producto", self.abrir_ventana_agregar),
            ("3) Retirar Producto", self.abrir_ventana_retirar),
            ("4) Registrar Compra", self.abrir_ventana_compra),
            ("5) Alertas Stock Bajo", self.mostrar_alertas),
            ("6) Buscar Producto", self.abrir_ventana_buscar),
            ("7) Historial por SKU", self.abrir_ventana_historial),
            ("8) Exportar Respaldo CSV", self.exportar_respaldo),
            ("9) Importar CSV", self.importar_csv),
            ("10) Valorizacion", self.mostrar_valorizacion),
            ("11) Recategorizar Inventario", self.recategorizar_inventario),
            ("12) Cambiar Categoria", self.abrir_ventana_cambiar_categoria),
            ("13) Puntaje Categorizacion", self.abrir_ventana_puntajes),
            ("14) Reglas de Categorias", self.abrir_ventana_reglas_categorias),
            ("15) Ordenes de Compra", self.abrir_ventana_ordenes),
        ]

        fila_inicio = 2
        for idx, (texto, accion) in enumerate(botones, start=fila_inicio):
            ctk.CTkButton(
                self.sidebar_frame,
                text=texto,
                command=accion,
                height=34,
                anchor="w",
            ).grid(row=idx, column=0, padx=16, pady=4, sticky="ew")

        fila_despues_botones = fila_inicio + len(botones)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="Tema visual",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=fila_despues_botones, column=0, padx=16, pady=(10, 4), sticky="w")

        self.menu_tema = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Sistema", "Claro", "Oscuro"],
            variable=self.tema_actual,
            command=self._cambiar_tema,
        )
        self.menu_tema.grid(row=fila_despues_botones + 1, column=0, padx=16, pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            self.sidebar_frame,
            text="Salir",
            fg_color="#8B1A1A",
            hover_color="#6E1515",
            command=self.destroy,
        ).grid(row=fila_despues_botones + 2, column=0, padx=16, pady=16, sticky="ew")

    def _build_main_area(self):
        self._configurar_estilo_tabla()

        self.lbl_titulo = ctk.CTkLabel(
            self.main_frame,
            text="Panel de Inventario",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.lbl_titulo.grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        self.lbl_subtitulo = ctk.CTkLabel(
            self.main_frame,
            text="Visualizacion y operaciones del sistema",
            font=ctk.CTkFont(size=14),
            text_color="gray60",
        )
        self.lbl_subtitulo.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        self._build_kpi_cards()
        self._build_filtros()

        tabla_frame = ctk.CTkFrame(self.main_frame)
        tabla_frame.grid(row=4, column=0, padx=16, pady=8, sticky="nsew")
        tabla_frame.grid_columnconfigure(0, weight=1)
        tabla_frame.grid_rowconfigure(0, weight=1)

        columnas = ("id", "sku", "nombre", "categoria", "stock", "minimo", "costo", "valor")
        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=18)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.tag_configure("stock_bajo", background="#4A1F1F")

        encabezados = {
            "id": "ID",
            "sku": "SKU",
            "nombre": "NOMBRE",
            "categoria": "CATEGORIA",
            "stock": "STOCK",
            "minimo": "MINIMO",
            "costo": "COSTO",
            "valor": "VALOR TOTAL",
        }
        anchos = {
            "id": 60,
            "sku": 120,
            "nombre": 250,
            "categoria": 150,
            "stock": 90,
            "minimo": 90,
            "costo": 120,
            "valor": 140,
        }

        for col in columnas:
            self.tree.heading(col, text=encabezados[col])
            self.tree.column(col, width=anchos[col], anchor="center")
        self.tree.column("nombre", anchor="w")

        scroll_y = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll_y.set)

        bitacora_frame = ctk.CTkFrame(self.main_frame, corner_radius=12)
        bitacora_frame.grid(row=5, column=0, padx=16, pady=(8, 16), sticky="ew")
        bitacora_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bitacora_frame,
            text="Actividad Reciente",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.txt_estado = ctk.CTkTextbox(
            bitacora_frame,
            height=120,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="#202225",
            text_color="#E7EAF0",
            border_width=1,
            border_color="#3A3F4A",
        )
        self.txt_estado.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.txt_estado.insert("0.0", "Bienvenido. Selecciona una accion del menu lateral.\n")
        self.txt_estado.configure(state="disabled")

    def _configurar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), relief="flat")

    def _cambiar_tema(self, opcion):
        mapa = {"Sistema": "System", "Claro": "Light", "Oscuro": "Dark"}
        ctk.set_appearance_mode(mapa.get(opcion, "System"))
        self._aplicar_estilo_por_tema()
        self._set_estado(f"Tema cambiado a: {opcion}")

    def _aplicar_estilo_por_tema(self):
        modo = ctk.get_appearance_mode()
        style = ttk.Style()

        if modo == "Light":
            tree_bg = "#FFFFFF"
            tree_fg = "#202124"
            heading_bg = "#357ABD"
            heading_fg = "#FFFFFF"
            selected_bg = "#D6E9FF"
            selected_fg = "#10213A"
            stock_bajo_bg = "#FFD6D6"
            txt_bg = "#F4F6F9"
            txt_fg = "#1F2937"
            txt_border = "#CDD3DC"
        else:
            tree_bg = "#16181D"
            tree_fg = "#EDEFF2"
            heading_bg = "#2A5EA8"
            heading_fg = "#FFFFFF"
            selected_bg = "#2F7DD1"
            selected_fg = "#FFFFFF"
            stock_bajo_bg = "#4A1F1F"
            txt_bg = "#202225"
            txt_fg = "#E7EAF0"
            txt_border = "#3A3F4A"

        style.configure(
            "Treeview",
            background=tree_bg,
            fieldbackground=tree_bg,
            foreground=tree_fg,
            bordercolor="#2A2E36",
        )
        style.configure("Treeview.Heading", background=heading_bg, foreground=heading_fg)
        style.map("Treeview", background=[("selected", selected_bg)], foreground=[("selected", selected_fg)])

        self.tree.tag_configure("stock_bajo", background=stock_bajo_bg)
        self.txt_estado.configure(fg_color=txt_bg, text_color=txt_fg, border_color=txt_border)

    def _build_kpi_cards(self):
        kpi_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        kpi_frame.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        for i in range(4):
            kpi_frame.grid_columnconfigure(i, weight=1)

        self.kpi_total_productos = self._crear_kpi_card(kpi_frame, 0, "Total productos", "0")
        self.kpi_total_stock = self._crear_kpi_card(kpi_frame, 1, "Unidades en stock", "0")
        self.kpi_valor_total = self._crear_kpi_card(kpi_frame, 2, "Valor inventario", "$0.00")
        self.kpi_stock_bajo = self._crear_kpi_card(kpi_frame, 3, "Stock bajo", "0")

    def _crear_kpi_card(self, parent, col, titulo, valor):
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")
        ctk.CTkLabel(card, text=titulo, text_color="gray70", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=12, pady=(10, 2))
        lbl_valor = ctk.CTkLabel(card, text=valor, font=ctk.CTkFont(size=20, weight="bold"))
        lbl_valor.pack(anchor="w", padx=12, pady=(0, 10))
        return lbl_valor

    def _build_filtros(self):
        filtros_frame = ctk.CTkFrame(self.main_frame)
        filtros_frame.grid(row=3, column=0, padx=16, pady=(0, 8), sticky="ew")
        filtros_frame.grid_columnconfigure(1, weight=1)
        filtros_frame.grid_columnconfigure(2, weight=0)
        filtros_frame.grid_columnconfigure(3, weight=0)
        filtros_frame.grid_columnconfigure(4, weight=0)

        ctk.CTkLabel(filtros_frame, text="Filtro rapido:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=(12, 6), pady=10, sticky="w"
        )
        self.entry_filtro = ctk.CTkEntry(filtros_frame, placeholder_text="Buscar por SKU o nombre...")
        self.entry_filtro.grid(row=0, column=1, padx=6, pady=10, sticky="ew")
        self.entry_filtro.bind("<KeyRelease>", self._filtrar_en_tabla)

        self.var_categoria_filtro = ctk.StringVar(value="Todas")
        self.menu_categoria = ctk.CTkOptionMenu(
            filtros_frame,
            values=["Todas"],
            variable=self.var_categoria_filtro,
            command=lambda _opcion: self._filtrar_en_tabla(),
            width=170,
        )
        self.menu_categoria.grid(row=0, column=2, padx=6, pady=10)

        self.var_solo_stock_bajo = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            filtros_frame,
            text="Solo stock bajo",
            variable=self.var_solo_stock_bajo,
            command=self._filtrar_en_tabla,
        ).grid(row=0, column=3, padx=6, pady=10)

        ctk.CTkButton(filtros_frame, text="Limpiar", width=90, command=self._limpiar_filtros).grid(
            row=0, column=4, padx=(6, 12), pady=10
        )

    def _conexion(self):
        return sqlite3.connect("inventario.db")

    def _set_estado(self, mensaje):
        self.txt_estado.configure(state="normal")
        self.txt_estado.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}]  {mensaje}\n")
        self.txt_estado.see("end")
        self.txt_estado.configure(state="disabled")

    def _limpiar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _cargar_filas(self, filas):
        self._filas_actuales = list(filas)
        self._limpiar_tabla()
        for fila in filas:
            tags = ()
            if self._es_stock_bajo(fila):
                tags = ("stock_bajo",)
            self.tree.insert("", "end", values=fila, tags=tags)

    def _es_stock_bajo(self, fila):
        try:
            stock = int(fila[4])
            minimo = int(fila[5])
            return stock <= minimo
        except (ValueError, TypeError, IndexError):
            return False

    def _actualizar_filtro_categorias(self):
        try:
            categorias_db = set(obtener_categorias_disponibles())
            categorias_cfg = set(obtener_categorias_configuradas())
            categorias = sorted(categorias_db.union(categorias_cfg))
            opciones = ["Todas"] + [cat.title() for cat in categorias]
            self.menu_categoria.configure(values=opciones)
            if self.var_categoria_filtro.get() not in opciones:
                self.var_categoria_filtro.set("Todas")
        except Exception as exc:
            self._set_estado(f"No se pudo actualizar el filtro de categorias: {exc}")

    def _filtrar_en_tabla(self, _event=None):
        texto = self.entry_filtro.get().strip().upper()
        solo_bajo = self.var_solo_stock_bajo.get()
        categoria_seleccionada = self.var_categoria_filtro.get().strip().lower()

        filtradas = []
        for fila in self._filas_actuales:
            sku = str(fila[1]).upper() if len(fila) > 1 else ""
            nombre = str(fila[2]).upper() if len(fila) > 2 else ""
            categoria = str(fila[3]).strip().lower() if len(fila) > 3 else ""
            coincide = (texto in sku or texto in nombre) if texto else True
            cumple_stock = self._es_stock_bajo(fila) if solo_bajo else True
            cumple_categoria = categoria_seleccionada in ("", "todas") or categoria == categoria_seleccionada
            if coincide and cumple_stock and cumple_categoria:
                filtradas.append(fila)

        self._limpiar_tabla()
        for fila in filtradas:
            tags = ("stock_bajo",) if self._es_stock_bajo(fila) else ()
            self.tree.insert("", "end", values=fila, tags=tags)

    def _limpiar_filtros(self):
        self.entry_filtro.delete(0, "end")
        self.var_solo_stock_bajo.set(False)
        self.var_categoria_filtro.set("Todas")
        self._filtrar_en_tabla()

    def _actualizar_kpis(self):
        try:
            conn = self._conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(stock_actual), 0), COALESCE(SUM(stock_actual * costo_unitario_base), 0) FROM productos")
            total_productos, total_stock, valor_total = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM productos WHERE stock_actual <= stock_minimo")
            stock_bajo = cursor.fetchone()[0]
            conn.close()

            self.kpi_total_productos.configure(text=str(total_productos))
            self.kpi_total_stock.configure(text=str(total_stock))
            self.kpi_valor_total.configure(text=f"${valor_total:,.2f}")
            self.kpi_stock_bajo.configure(text=str(stock_bajo))
        except Exception as exc:
            self._set_estado(f"No se pudieron actualizar KPIs: {exc}")

    def _mostrar_alertas_inicio(self):
        try:
            alertas = obtener_alertas_stock_bajo()
            if alertas:
                self._set_estado(f"Hay {len(alertas)} producto(s) con stock bajo.")
        except Exception as exc:
            self._set_estado(f"No se pudieron cargar alertas al inicio: {exc}")

    def mostrar_inventario(self):
        self.lbl_titulo.configure(text="Inventario Completo")
        self.lbl_subtitulo.configure(text="Vista general de productos registrados")
        try:
            conn = self._conexion()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    id_producto,
                    sku,
                    nombre,
                    COALESCE(categoria, 'sin_categoria'),
                    stock_actual,
                    stock_minimo,
                    printf('$%.2f', costo_unitario_base),
                    printf('$%.2f', stock_actual * costo_unitario_base)
                FROM productos
                ORDER BY nombre ASC
                """
            )
            productos = cursor.fetchall()
            conn.close()
            self._actualizar_filtro_categorias()
            self._cargar_filas(productos)
            self._actualizar_kpis()
            self._filtrar_en_tabla()
            self._set_estado(f"Inventario actualizado: {len(productos)} producto(s).")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo cargar inventario:\n{exc}")

    def abrir_ventana_agregar(self):
        self._abrir_formulario_producto("Anadir Producto Nuevo", self._accion_agregar_producto)

    def _accion_agregar_producto(self, data):
        sku = data["sku"].upper().strip()
        nombre = data["nombre"].strip()
        stock = int(data["stock"])
        minimo = int(data["minimo"])
        costo = float(data["costo"])
        categoria = categorizar_nombre_producto(nombre, motor=self._motor_categorizacion)

        conn = self._conexion()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO productos (sku, nombre, categoria, stock_actual, stock_minimo, costo_unitario_base)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (sku, nombre, categoria, stock, minimo, costo),
            )
            conn.commit()
            self._set_estado(f"Producto agregado: {sku} - {nombre} [{categoria}].")
            self.mostrar_inventario()
            return True
        except sqlite3.IntegrityError:
            messagebox.showerror("SKU duplicado", f"El SKU '{sku}' ya existe.")
            return False
        finally:
            conn.close()

    def abrir_ventana_retirar(self):
        self._abrir_formulario_movimiento("Retirar Producto", self._accion_retirar_producto, incluir_costo=False)

    def _accion_retirar_producto(self, data):
        sku = data["sku"].upper().strip()
        cantidad = int(data["cantidad"])

        conn = self._conexion()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id_producto, stock_actual, costo_unitario_base FROM productos WHERE sku = ?",
                (sku,),
            )
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("No encontrado", f"SKU '{sku}' no existe.")
                return False

            id_prod, stock_actual, costo = row
            if stock_actual < cantidad:
                messagebox.showwarning("Stock insuficiente", f"Solo hay {stock_actual} unidad(es).")
                return False

            cursor.execute(
                "UPDATE productos SET stock_actual = stock_actual - ? WHERE id_producto = ?",
                (cantidad, id_prod),
            )
            cursor.execute(
                """
                INSERT INTO movimientos (id_producto, tipo, cantidad, costo_momento)
                VALUES (?, 'SALIDA', ?, ?)
                """,
                (id_prod, cantidad, costo),
            )
            conn.commit()
            self._set_estado(f"Retiro registrado para {sku}: {cantidad} unidad(es).")
            self.mostrar_inventario()
            return True
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo retirar producto:\n{exc}")
            return False
        finally:
            conn.close()

    def abrir_ventana_compra(self):
        self._abrir_formulario_movimiento("Registrar Compra", self._accion_registrar_compra, incluir_costo=True)

    def _accion_registrar_compra(self, data):
        sku = data["sku"].upper().strip()
        cantidad = int(data["cantidad"])
        costo = float(data["costo"])

        conn = self._conexion()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id_producto FROM productos WHERE sku = ?", (sku,))
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("No encontrado", f"SKU '{sku}' no existe.")
                return False

            id_prod = row[0]
            cursor.execute(
                """
                UPDATE productos
                SET stock_actual = stock_actual + ?, costo_unitario_base = ?
                WHERE id_producto = ?
                """,
                (cantidad, costo, id_prod),
            )
            cursor.execute(
                """
                INSERT INTO movimientos (id_producto, tipo, cantidad, costo_momento)
                VALUES (?, 'ENTRADA', ?, ?)
                """,
                (id_prod, cantidad, costo),
            )
            conn.commit()
            self._set_estado(f"Compra registrada para {sku}: +{cantidad} unidad(es) a ${costo:.2f}.")
            self.mostrar_inventario()
            return True
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo registrar compra:\n{exc}")
            return False
        finally:
            conn.close()

    def mostrar_alertas(self):
        self.lbl_titulo.configure(text="Alertas de Stock Bajo")
        self.lbl_subtitulo.configure(text="Productos en o por debajo del stock minimo")
        try:
            alertas = obtener_alertas_stock_bajo()
            filas = []
            for idx, (sku, nombre, stock_actual, stock_minimo) in enumerate(alertas, start=1):
                filas.append((idx, sku, nombre, "alerta_stock", stock_actual, stock_minimo, "-", "-"))
            self._cargar_filas(filas)
            self._actualizar_kpis()
            self._filtrar_en_tabla()
            self._set_estado(f"Alertas mostradas: {len(alertas)} producto(s).")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudieron obtener alertas:\n{exc}")

    def abrir_ventana_buscar(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Buscar Producto")
        ventana.geometry("380x180")
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="Ingrese SKU o nombre", font=ctk.CTkFont(size=14, weight="bold")).pack(
            padx=16, pady=(18, 8), anchor="w"
        )
        entrada = ctk.CTkEntry(ventana, placeholder_text="Ej: P001 o Mouse")
        entrada.pack(fill="x", padx=16, pady=8)
        entrada.focus_set()

        def ejecutar():
            termino = entrada.get().strip()
            if not termino:
                messagebox.showwarning("Dato requerido", "Ingrese un termino de busqueda.")
                return
            self.buscar_producto(termino)
            ventana.destroy()

        ctk.CTkButton(ventana, text="Buscar", command=ejecutar).pack(padx=16, pady=12)
        ventana.bind("<Return>", lambda _event: ejecutar())

    def buscar_producto(self, termino):
        self.lbl_titulo.configure(text=f"Resultados de Busqueda: {termino}")
        self.lbl_subtitulo.configure(text="Coincidencias por SKU o nombre")
        try:
            conn = self._conexion()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    id_producto, sku, nombre, COALESCE(categoria, 'sin_categoria'), stock_actual, stock_minimo,
                    printf('$%.2f', costo_unitario_base),
                    printf('$%.2f', stock_actual * costo_unitario_base)
                FROM productos
                WHERE UPPER(sku) LIKE ? OR UPPER(nombre) LIKE ?
                ORDER BY nombre ASC
                """,
                (f"%{termino.upper()}%", f"%{termino.upper()}%"),
            )
            resultados = cursor.fetchall()
            conn.close()
            self._cargar_filas(resultados)
            self._actualizar_kpis()
            self._filtrar_en_tabla()
            self._set_estado(f"Busqueda '{termino}': {len(resultados)} coincidencia(s).")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo buscar:\n{exc}")

    def abrir_ventana_historial(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Historial por SKU")
        ventana.geometry("380x180")
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="SKU del producto", font=ctk.CTkFont(size=14, weight="bold")).pack(
            padx=16, pady=(18, 8), anchor="w"
        )
        entrada = ctk.CTkEntry(ventana, placeholder_text="Ej: P001")
        entrada.pack(fill="x", padx=16, pady=8)
        entrada.focus_set()

        def ejecutar():
            sku = entrada.get().strip()
            if not sku:
                messagebox.showwarning("Dato requerido", "Ingrese un SKU.")
                return
            self.mostrar_historial(sku)
            ventana.destroy()

        ctk.CTkButton(ventana, text="Ver Historial", command=ejecutar).pack(padx=16, pady=12)
        ventana.bind("<Return>", lambda _event: ejecutar())

    def mostrar_historial(self, sku):
        self.lbl_titulo.configure(text=f"Historial de Movimientos: {sku.upper()}")
        self.lbl_subtitulo.configure(text="Entradas y salidas registradas")
        try:
            conn = self._conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT id_producto, nombre FROM productos WHERE sku = ?", (sku.upper(),))
            producto = cursor.fetchone()
            if not producto:
                conn.close()
                messagebox.showerror("No encontrado", f"SKU '{sku}' no existe.")
                return

            id_prod, nombre = producto
            cursor.execute(
                """
                SELECT datetime(fecha, 'localtime'), tipo, cantidad, costo_momento
                FROM movimientos
                WHERE id_producto = ?
                ORDER BY fecha DESC
                """,
                (id_prod,),
            )
            movimientos = cursor.fetchall()
            conn.close()

            filas = []
            for idx, (fecha, tipo, cantidad, costo) in enumerate(movimientos, start=1):
                filas.append((idx, sku.upper(), f"{nombre} [{tipo}]", "movimiento", cantidad, "-", f"${costo:.2f}", fecha))
            self._cargar_filas(filas)
            self._actualizar_kpis()
            self._filtrar_en_tabla()
            self._set_estado(f"Historial de {sku.upper()}: {len(movimientos)} movimiento(s).")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo consultar historial:\n{exc}")

    def exportar_respaldo(self):
        try:
            conn = self._conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT sku, nombre, stock_actual, stock_minimo, costo_unitario_base FROM productos")
            productos = cursor.fetchall()
            conn.close()
            if not productos:
                messagebox.showwarning("Sin datos", "No hay productos para exportar.")
                return

            nombre_archivo = f"respaldo_inventario_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
            ruta = filedialog.asksaveasfilename(
                title="Guardar respaldo CSV",
                initialfile=nombre_archivo,
                defaultextension=".csv",
                filetypes=[("Archivo CSV", "*.csv")],
            )
            if not ruta:
                return

            with open(ruta, mode="w", newline="", encoding="utf-8") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(["SKU", "Nombre", "Stock Actual", "Stock Minimo", "Costo Base"])
                escritor.writerows(productos)

            self._set_estado(f"Respaldo exportado en: {ruta}")
            messagebox.showinfo("Exportacion completada", "Respaldo CSV creado correctamente.")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo exportar respaldo:\n{exc}")

    def importar_csv(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivo CSV", "*.csv"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return

        try:
            sinonimos = self._cargar_configuracion_import()
            conn = self._conexion()
            cursor = conn.cursor()
            self._motor_categorizacion = construir_motor_categorizacion()

            with open(ruta, mode="r", encoding="utf-8-sig") as archivo:
                lector = csv.DictReader(archivo)
                if not lector.fieldnames:
                    raise ValueError("El CSV no tiene encabezados.")

                mapeo_real = {}
                for db_col, lista_sinonimos in sinonimos.items():
                    for col_csv in lector.fieldnames:
                        if col_csv.lower().strip() in lista_sinonimos:
                            mapeo_real[db_col] = col_csv
                            break

                if "sku" not in mapeo_real or "nombre" not in mapeo_real:
                    raise ValueError("No se detectaron columnas criticas (SKU o nombre).")

                cursor.execute("SELECT sku FROM productos")
                skus_existentes = {row[0] for row in cursor.fetchall()}

                nuevos = 0
                actualizados = 0
                omitidos = 0
                batch_registros = []
                for fila in lector:
                    try:
                        sku = str(fila.get(mapeo_real["sku"], "")).upper().strip()
                        nombre = str(fila.get(mapeo_real["nombre"], "")).strip()
                        if not sku or not nombre:
                            omitidos += 1
                            continue

                        stock = int(float(fila.get(mapeo_real.get("stock_actual", ""), 0) or 0))
                        minimo = int(float(fila.get(mapeo_real.get("stock_minimo", ""), 5) or 5))
                        costo = float(fila.get(mapeo_real.get("costo_unitario_base", ""), 0.0) or 0.0)
                        categoria = categorizar_nombre_producto(nombre, motor=self._motor_categorizacion)
                        batch_registros.append((sku, nombre, categoria, stock, minimo, costo))

                        if sku in skus_existentes:
                            actualizados += 1
                        else:
                            nuevos += 1
                            skus_existentes.add(sku)
                    except Exception:
                        omitidos += 1
                        continue

                if batch_registros:
                    cursor.executemany(
                        """
                        INSERT INTO productos (sku, nombre, categoria, stock_actual, stock_minimo, costo_unitario_base)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(sku) DO UPDATE SET
                            nombre=excluded.nombre,
                            categoria=excluded.categoria,
                            stock_actual=excluded.stock_actual,
                            stock_minimo=excluded.stock_minimo,
                            costo_unitario_base=excluded.costo_unitario_base
                        """,
                        batch_registros,
                    )

                conn.commit()
                conn.close()

            self._set_estado(
                f"Importacion completada: {nuevos} nuevo(s), {actualizados} actualizado(s), {omitidos} omitido(s)."
            )
            messagebox.showinfo(
                "Importacion completada",
                f"Nuevos: {nuevos}\nActualizados: {actualizados}\nOmitidos: {omitidos}",
            )
            self.mostrar_inventario()
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo importar CSV:\n{exc}")

    def _cargar_configuracion_import(self):
        ruta_config = "config_import.json"
        if not os.path.exists(ruta_config):
            return {"sku": ["sku"], "nombre": ["nombre"]}
        with open(ruta_config, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("mapa_sinonimos", {})

    def mostrar_valorizacion(self):
        self.lbl_titulo.configure(text="Valorizacion de Inventario")
        self.lbl_subtitulo.configure(text="Valor total por producto y total general")
        try:
            conn = self._conexion()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    id_producto,
                    sku,
                    nombre,
                    COALESCE(categoria, 'sin_categoria'),
                    stock_actual,
                    stock_minimo,
                    printf('$%.2f', costo_unitario_base),
                    printf('$%.2f', stock_actual * costo_unitario_base)
                FROM productos
                ORDER BY stock_actual * costo_unitario_base DESC
                """
            )
            productos = cursor.fetchall()
            cursor.execute("SELECT COALESCE(SUM(stock_actual * costo_unitario_base), 0) FROM productos")
            total = cursor.fetchone()[0]
            conn.close()

            self._cargar_filas(productos)
            self._actualizar_kpis()
            self._filtrar_en_tabla()
            self._set_estado(f"Valor total del inventario: ${total:,.2f}")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo generar valorizacion:\n{exc}")

    def recategorizar_inventario(self):
        try:
            self._motor_categorizacion = construir_motor_categorizacion()
            total = categorizar_todos_los_productos()
            self._actualizar_filtro_categorias()
            self.mostrar_inventario()
            self._set_estado(f"Recategorizacion completada: {total} producto(s) actualizados.")
            messagebox.showinfo("Categorizacion", f"Productos recategorizados: {total}")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo recategorizar el inventario:\n{exc}")

    def abrir_ventana_cambiar_categoria(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Cambiar categoria manual")
        ventana.geometry("430x220")
        ventana.grab_set()

        seleccion = self.tree.selection()
        sku_prellenado = ""
        if seleccion:
            valores = self.tree.item(seleccion[0], "values")
            if len(valores) > 1:
                sku_prellenado = str(valores[1])

        ctk.CTkLabel(ventana, text="SKU del producto", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(16, 8), sticky="w"
        )
        entry_sku = ctk.CTkEntry(ventana, placeholder_text="Ej: P001")
        entry_sku.grid(row=0, column=1, padx=16, pady=(16, 8), sticky="ew")
        if sku_prellenado:
            entry_sku.insert(0, sku_prellenado)

        ctk.CTkLabel(ventana, text="Nueva categoria", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=1, column=0, padx=16, pady=8, sticky="w"
        )
        categorias = [cat.title() for cat in obtener_categorias_configuradas()] or ["Sin_Categoria"]
        var_categoria = ctk.StringVar(value=categorias[0])
        menu_categoria = ctk.CTkOptionMenu(ventana, values=categorias, variable=var_categoria)
        menu_categoria.grid(row=1, column=1, padx=16, pady=8, sticky="ew")
        ventana.grid_columnconfigure(1, weight=1)

        def guardar_cambio():
            sku = entry_sku.get().upper().strip()
            categoria = var_categoria.get().strip().lower()
            if not sku:
                messagebox.showwarning("Dato requerido", "Ingrese un SKU.")
                return

            conn = self._conexion()
            cursor = conn.cursor()
            cursor.execute("UPDATE productos SET categoria = ? WHERE sku = ?", (categoria, sku))
            actualizados = cursor.rowcount
            conn.commit()
            conn.close()

            if actualizados == 0:
                messagebox.showerror("No encontrado", f"No existe el SKU '{sku}'.")
                return

            self._actualizar_filtro_categorias()
            self.mostrar_inventario()
            self._set_estado(f"Categoria actualizada: {sku} -> {categoria}")
            ventana.destroy()

        ctk.CTkButton(ventana, text="Guardar", command=guardar_cambio).grid(
            row=2, column=1, padx=16, pady=16, sticky="e"
        )
        entry_sku.focus_set()
        ventana.bind("<Return>", lambda _event: guardar_cambio())

    def abrir_ventana_puntajes(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Puntaje de categorizacion")
        ventana.geometry("720x420")
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="Nombre del producto", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Ej: Cafe premium gamer")
        entry_nombre.pack(fill="x", padx=16, pady=(0, 10))

        salida = ctk.CTkTextbox(ventana, corner_radius=8)
        salida.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        def evaluar():
            nombre = entry_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Dato requerido", "Escribe un nombre de producto.")
                return
            self._motor_categorizacion = construir_motor_categorizacion()
            puntajes = obtener_puntajes_categorizacion(nombre, motor=self._motor_categorizacion)
            salida.configure(state="normal")
            salida.delete("0.0", "end")
            salida.insert("end", f"Producto analizado: {nombre}\n\n")
            for idx, item in enumerate(puntajes[:10], start=1):
                salida.insert(
                    "end",
                    f"{idx}. {item['categoria']}  | puntaje={item['puntaje']} | matches={', '.join(item['coincidencias']) or '-'}\n",
                )
            salida.configure(state="disabled")

        ctk.CTkButton(ventana, text="Analizar", command=evaluar).pack(padx=16, pady=(0, 12), anchor="e")
        entry_nombre.focus_set()
        ventana.bind("<Return>", lambda _event: evaluar())

    def abrir_ventana_reglas_categorias(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Reglas de categorias")
        ventana.geometry("760x520")
        ventana.grab_set()

        cont = ctk.CTkFrame(ventana)
        cont.pack(fill="both", expand=True, padx=12, pady=12)
        cont.grid_columnconfigure(0, weight=1)
        cont.grid_columnconfigure(1, weight=1)
        cont.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(cont, text="Categorias", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=10, pady=8, sticky="w"
        )
        ctk.CTkLabel(cont, text="Palabras clave", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=1, padx=10, pady=8, sticky="w"
        )

        lista_categorias = ctk.CTkTextbox(cont, width=280)
        lista_categorias.grid(row=1, column=0, padx=10, pady=8, sticky="nsew")
        lista_palabras = ctk.CTkTextbox(cont)
        lista_palabras.grid(row=1, column=1, padx=10, pady=8, sticky="nsew")

        barra = ctk.CTkFrame(cont)
        barra.grid(row=2, column=0, columnspan=2, padx=10, pady=(4, 10), sticky="ew")
        barra.grid_columnconfigure(1, weight=1)

        entry_categoria = ctk.CTkEntry(barra, placeholder_text="Categoria")
        entry_categoria.grid(row=0, column=0, padx=6, pady=6)
        entry_palabra = ctk.CTkEntry(barra, placeholder_text="Palabra clave")
        entry_palabra.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        def refrescar():
            categorias = obtener_categorias_configuradas()
            lista_categorias.configure(state="normal")
            lista_categorias.delete("0.0", "end")
            lista_categorias.insert("end", "\n".join(categorias) if categorias else "(sin categorias)")
            lista_categorias.configure(state="disabled")

            cat_sel = entry_categoria.get().strip()
            if cat_sel:
                palabras = obtener_palabras_categoria(cat_sel)
                lista_palabras.configure(state="normal")
                lista_palabras.delete("0.0", "end")
                lista_palabras.insert("end", "\n".join(palabras) if palabras else "(sin palabras)")
                lista_palabras.configure(state="disabled")

            self._actualizar_filtro_categorias()

        def preguntar_recategorizacion():
            if messagebox.askyesno("Recategorizar", "Deseas recategorizar todo el inventario con las nuevas reglas?"):
                self.recategorizar_inventario()

        def on_agregar_categoria():
            cat = entry_categoria.get().strip()
            if not cat:
                return
            agregar_categoria(cat)
            self._motor_categorizacion = construir_motor_categorizacion()
            refrescar()
            preguntar_recategorizacion()

        def on_eliminar_categoria():
            cat = entry_categoria.get().strip()
            if not cat:
                return
            eliminar_categoria(cat)
            self._motor_categorizacion = construir_motor_categorizacion()
            refrescar()
            preguntar_recategorizacion()

        def on_agregar_palabra():
            cat = entry_categoria.get().strip()
            palabra = entry_palabra.get().strip()
            if not cat or not palabra:
                return
            agregar_palabra_clave(cat, palabra)
            self._motor_categorizacion = construir_motor_categorizacion()
            refrescar()
            preguntar_recategorizacion()

        def on_eliminar_palabra():
            cat = entry_categoria.get().strip()
            palabra = entry_palabra.get().strip()
            if not cat or not palabra:
                return
            eliminar_palabra_clave(cat, palabra)
            self._motor_categorizacion = construir_motor_categorizacion()
            refrescar()
            preguntar_recategorizacion()

        ctk.CTkButton(barra, text="+ Categoria", command=on_agregar_categoria, width=110).grid(row=1, column=0, padx=6, pady=6)
        ctk.CTkButton(barra, text="- Categoria", command=on_eliminar_categoria, width=110).grid(row=1, column=1, padx=6, pady=6, sticky="w")
        ctk.CTkButton(barra, text="+ Palabra", command=on_agregar_palabra, width=110).grid(row=1, column=1, padx=128, pady=6, sticky="w")
        ctk.CTkButton(barra, text="- Palabra", command=on_eliminar_palabra, width=110).grid(row=1, column=1, padx=250, pady=6, sticky="w")
        ctk.CTkButton(barra, text="Refrescar", command=refrescar, width=100).grid(row=1, column=1, padx=6, pady=6, sticky="e")

        entry_categoria.bind("<KeyRelease>", lambda _event: refrescar())
        refrescar()

    def abrir_ventana_ordenes(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Ordenes de compra")
        ventana.geometry("860x560")
        ventana.grab_set()

        top = ctk.CTkFrame(ventana)
        top.pack(fill="x", padx=12, pady=12)
        top.grid_columnconfigure(3, weight=1)

        entry_cliente = ctk.CTkEntry(top, placeholder_text="Cliente")
        entry_cliente.grid(row=0, column=0, padx=6, pady=6)
        entry_items = ctk.CTkEntry(top, placeholder_text="Items (SKU:cant,SKU:cant) Ej: P001:2,P002:1")
        entry_items.grid(row=0, column=1, columnspan=3, padx=6, pady=6, sticky="ew")
        entry_orden = ctk.CTkEntry(top, placeholder_text="Codigo orden OC-...")
        entry_orden.grid(row=1, column=0, padx=6, pady=6)

        salida = ctk.CTkTextbox(ventana)
        salida.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        def parse_items(texto):
            items = []
            for chunk in texto.split(","):
                part = chunk.strip()
                if not part:
                    continue
                sku, cantidad = part.split(":")
                items.append({"sku": sku.strip().upper(), "cantidad": int(cantidad.strip())})
            return items

        def refrescar():
            ordenes = listar_ordenes(limit=200)
            salida.configure(state="normal")
            salida.delete("0.0", "end")
            for o in ordenes:
                salida.insert("end", f"{o[0]} | {o[1]} | {o[2]} | {o[3]} | {o[4] or '-'}\n")
            salida.configure(state="disabled")

        def crear():
            try:
                codigo = crear_orden_borrador(entry_cliente.get().strip(), parse_items(entry_items.get().strip()))
                self._set_estado(f"Orden creada en BORRADOR: {codigo}")
                entry_orden.delete(0, "end")
                entry_orden.insert(0, codigo)
                refrescar()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        def finalizar():
            try:
                codigo = entry_orden.get().strip()
                finalizar_orden(codigo)
                self._set_estado(f"Orden finalizada y stock descontado: {codigo}")
                self.mostrar_inventario()
                refrescar()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        def cancelar():
            try:
                codigo = entry_orden.get().strip()
                cancelar_orden(codigo)
                self._set_estado(f"Orden cancelada sin afectar stock: {codigo}")
                refrescar()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        ctk.CTkButton(top, text="Crear Borrador", command=crear).grid(row=1, column=1, padx=6, pady=6, sticky="w")
        ctk.CTkButton(top, text="Finalizar", command=finalizar).grid(row=1, column=2, padx=6, pady=6, sticky="w")
        ctk.CTkButton(top, text="Cancelar", command=cancelar).grid(row=1, column=3, padx=6, pady=6, sticky="w")
        ctk.CTkButton(top, text="Refrescar", command=refrescar).grid(row=1, column=3, padx=6, pady=6, sticky="e")
        refrescar()

    def _abrir_formulario_producto(self, titulo, callback):
        ventana = ctk.CTkToplevel(self)
        ventana.title(titulo)
        ventana.geometry("420x360")
        ventana.grab_set()

        campos = [
            ("SKU", "sku"),
            ("Nombre", "nombre"),
            ("Stock inicial", "stock"),
            ("Stock minimo", "minimo"),
            ("Costo unitario", "costo"),
        ]

        entradas = {}
        for idx, (texto, key) in enumerate(campos):
            ctk.CTkLabel(ventana, text=texto).grid(row=idx, column=0, padx=16, pady=8, sticky="w")
            entry = ctk.CTkEntry(ventana)
            entry.grid(row=idx, column=1, padx=16, pady=8, sticky="ew")
            entradas[key] = entry
        ventana.grid_columnconfigure(1, weight=1)

        def guardar():
            data = {k: v.get() for k, v in entradas.items()}
            if not all(data.values()):
                messagebox.showwarning("Datos requeridos", "Complete todos los campos.")
                return
            try:
                int(data["stock"])
                int(data["minimo"])
                float(data["costo"])
            except ValueError:
                messagebox.showerror("Formato invalido", "Stock/minimo deben ser enteros y costo numerico.")
                return
            ok = callback(data)
            if ok:
                ventana.destroy()

        ctk.CTkButton(ventana, text="Guardar", command=guardar).grid(row=len(campos), column=1, padx=16, pady=16, sticky="e")
        ventana.bind("<Return>", lambda _event: guardar())

    def _abrir_formulario_movimiento(self, titulo, callback, incluir_costo):
        ventana = ctk.CTkToplevel(self)
        ventana.title(titulo)
        ventana.geometry("400x280" if incluir_costo else "400x230")
        ventana.grab_set()

        campos = [("SKU", "sku"), ("Cantidad", "cantidad")]
        if incluir_costo:
            campos.append(("Costo unitario", "costo"))

        entradas = {}
        for idx, (texto, key) in enumerate(campos):
            ctk.CTkLabel(ventana, text=texto).grid(row=idx, column=0, padx=16, pady=8, sticky="w")
            entry = ctk.CTkEntry(ventana)
            entry.grid(row=idx, column=1, padx=16, pady=8, sticky="ew")
            entradas[key] = entry
        ventana.grid_columnconfigure(1, weight=1)

        def guardar():
            data = {k: v.get() for k, v in entradas.items()}
            if not all(data.values()):
                messagebox.showwarning("Datos requeridos", "Complete todos los campos.")
                return
            try:
                int(data["cantidad"])
                if incluir_costo:
                    float(data["costo"])
            except ValueError:
                messagebox.showerror("Formato invalido", "Cantidad y costo deben ser numericos.")
                return
            ok = callback(data)
            if ok:
                ventana.destroy()

        ctk.CTkButton(ventana, text="Guardar", command=guardar).grid(row=len(campos), column=1, padx=16, pady=16, sticky="e")
        ventana.bind("<Return>", lambda _event: guardar())


if __name__ == "__main__":
    app = AppInventario()
    app.mainloop()