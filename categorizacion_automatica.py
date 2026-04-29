import json
import os
import sqlite3
import unicodedata
from functools import lru_cache


RUTA_CATEGORIAS = "categorias.json"
DEFAULT_CATEGORIA = "sin_categoria"


def _normalizar_texto(texto):
    texto = (texto or "").strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return texto


def _normalizar_diccionario(data):
    normalizado = {}
    for cat, claves in data.items():
        categoria = _normalizar_texto(cat)
        if not categoria:
            continue
        lista = []
        for clave in claves:
            clave_norm = _normalizar_texto(clave)
            if clave_norm:
                lista.append(clave_norm)
        if lista:
            normalizado[categoria] = sorted(set(lista), key=len, reverse=True)
    return normalizado


@lru_cache(maxsize=16)
def _cargar_diccionario_cacheado(ruta, mtime):
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _normalizar_diccionario(data)


def cargar_diccionario_categorias(ruta=RUTA_CATEGORIAS):
    if not os.path.exists(ruta):
        return {}
    mtime = int(os.path.getmtime(ruta))
    return _cargar_diccionario_cacheado(ruta, mtime)


def guardar_diccionario_categorias(diccionario, ruta=RUTA_CATEGORIAS):
    serializable = {str(cat).strip(): sorted(set(claves)) for cat, claves in diccionario.items() if str(cat).strip()}
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=4)
    _cargar_diccionario_cacheado.cache_clear()


def construir_motor_categorizacion(diccionario=None, ruta=RUTA_CATEGORIAS):
    diccionario = diccionario if diccionario is not None else cargar_diccionario_categorias(ruta=ruta)
    motor = []
    for categoria, palabras_clave in diccionario.items():
        set_claves = set(palabras_clave)
        motor.append((categoria, set_claves))
    return motor


def categorizar_nombre_producto(nombre_producto, diccionario=None, motor=None):
    # Nota: la normalizacion de tildes YA se aplica aqui ("cafe" == "café")
    if motor is None:
        motor = construir_motor_categorizacion(diccionario=diccionario)

    nombre_norm = _normalizar_texto(nombre_producto)
    if not nombre_norm:
        return DEFAULT_CATEGORIA

    # Puntaje por coincidencias de palabras clave.
    # Gana la categoria con mas matches.
    tokens = set(nombre_norm.replace("-", " ").replace("/", " ").split())
    mejor_categoria = DEFAULT_CATEGORIA
    mejor_puntaje = 0
    mejor_cobertura = 0

    for categoria, palabras_clave in motor:
        puntaje = 0
        cobertura = 0
        for palabra in palabras_clave:
            if " " in palabra:
                if palabra in nombre_norm:
                    puntaje += 2
                    cobertura += len(palabra)
            elif palabra in tokens or palabra in nombre_norm:
                puntaje += 1
                cobertura += len(palabra)

        if puntaje > mejor_puntaje or (puntaje == mejor_puntaje and cobertura > mejor_cobertura):
            mejor_puntaje = puntaje
            mejor_cobertura = cobertura
            mejor_categoria = categoria

    if mejor_puntaje > 0:
        return mejor_categoria
    return DEFAULT_CATEGORIA


def obtener_puntajes_categorizacion(nombre_producto, diccionario=None, motor=None):
    if motor is None:
        motor = construir_motor_categorizacion(diccionario=diccionario)

    nombre_norm = _normalizar_texto(nombre_producto)
    tokens = set(nombre_norm.replace("-", " ").replace("/", " ").split())
    resultado = []

    for categoria, palabras_clave in motor:
        puntaje = 0
        matches = []
        for palabra in palabras_clave:
            if " " in palabra:
                if palabra in nombre_norm:
                    puntaje += 2
                    matches.append(palabra)
            elif palabra in tokens or palabra in nombre_norm:
                puntaje += 1
                matches.append(palabra)
        resultado.append({"categoria": categoria, "puntaje": puntaje, "coincidencias": sorted(set(matches))})

    resultado.sort(key=lambda x: (x["puntaje"], len(" ".join(x["coincidencias"]))), reverse=True)
    return resultado


def asegurar_columna_categoria(db_path="inventario.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(productos)")
    columnas = [col[1] for col in cursor.fetchall()]
    if "categoria" not in columnas:
        cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'sin_categoria'")
        conn.commit()
    conn.close()


def categorizar_todos_los_productos(db_path="inventario.db", ruta_categorias=RUTA_CATEGORIAS):
    asegurar_columna_categoria(db_path=db_path)
    motor = construir_motor_categorizacion(ruta=ruta_categorias)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id_producto, nombre FROM productos")
    productos = cursor.fetchall()

    updates = []
    for id_producto, nombre in productos:
        categoria = categorizar_nombre_producto(nombre, motor=motor)
        updates.append((categoria, id_producto))

    if updates:
        cursor.executemany("UPDATE productos SET categoria = ? WHERE id_producto = ?", updates)
        conn.commit()
    conn.close()
    return len(updates)


def obtener_categorias_disponibles(db_path="inventario.db"):
    asegurar_columna_categoria(db_path=db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND categoria != '' ORDER BY categoria ASC")
    categorias = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categorias


def obtener_categorias_configuradas(ruta=RUTA_CATEGORIAS):
    diccionario = cargar_diccionario_categorias(ruta=ruta)
    return sorted(diccionario.keys())


def obtener_palabras_categoria(categoria, ruta=RUTA_CATEGORIAS):
    diccionario = cargar_diccionario_categorias(ruta=ruta)
    cat_norm = _normalizar_texto(categoria)
    return diccionario.get(cat_norm, [])


def agregar_categoria(categoria, ruta=RUTA_CATEGORIAS):
    diccionario = cargar_diccionario_categorias(ruta=ruta)
    cat_norm = _normalizar_texto(categoria)
    if not cat_norm:
        raise ValueError("Nombre de categoria invalido.")
    if cat_norm not in diccionario:
        diccionario[cat_norm] = []
        guardar_diccionario_categorias(diccionario, ruta=ruta)


def eliminar_categoria(categoria, ruta=RUTA_CATEGORIAS):
    diccionario = cargar_diccionario_categorias(ruta=ruta)
    cat_norm = _normalizar_texto(categoria)
    if cat_norm in diccionario:
        del diccionario[cat_norm]
        guardar_diccionario_categorias(diccionario, ruta=ruta)


def agregar_palabra_clave(categoria, palabra, ruta=RUTA_CATEGORIAS):
    diccionario = cargar_diccionario_categorias(ruta=ruta)
    cat_norm = _normalizar_texto(categoria)
    palabra_norm = _normalizar_texto(palabra)
    if not cat_norm or not palabra_norm:
        raise ValueError("Categoria o palabra invalida.")
    if cat_norm not in diccionario:
        diccionario[cat_norm] = []
    if palabra_norm not in diccionario[cat_norm]:
        diccionario[cat_norm].append(palabra_norm)
        diccionario[cat_norm] = sorted(set(diccionario[cat_norm]), key=len, reverse=True)
        guardar_diccionario_categorias(diccionario, ruta=ruta)


def eliminar_palabra_clave(categoria, palabra, ruta=RUTA_CATEGORIAS):
    diccionario = cargar_diccionario_categorias(ruta=ruta)
    cat_norm = _normalizar_texto(categoria)
    palabra_norm = _normalizar_texto(palabra)
    if cat_norm in diccionario and palabra_norm in diccionario[cat_norm]:
        diccionario[cat_norm].remove(palabra_norm)
        guardar_diccionario_categorias(diccionario, ruta=ruta)
