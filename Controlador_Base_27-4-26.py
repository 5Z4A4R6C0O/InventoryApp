import sys
# Importamos las funciones de tus otros archivos si los separaste
from gestion_inventario import añadir_producto_nuevo, retirar_producto
from verificacion_inventario import mostrar_inventario
from registrar_compra import registrar_compra
from alerta_stock import mostrar_alertas_stock_bajo
from buscador import buscar_producto_inteligente
from historial_de_movimiento import ver_historial_producto
from respaldo_csv import exportar_inventario_csv
from import_data_csv import importar_desde_csv_flexible #para importar data de inventario desde un csv file
from valorizacion import reporte_valorizacion

def menu_principal():
    # Al iniciar el controlador base, verificamos alertas de stock bajo.

    while True:
        mostrar_alertas_stock_bajo()
        print("\n================================")
        print("   SISTEMA DE INVENTARIO V1.0")
        print("================================")
        print("1. Ver Inventario Completo.")
        print("2. Añadir Producto Nuevo (Catálogo).")
        print("3. Retirar Producto (Venta/Baja).")
        print("4. Registrar compra de producto.")
        print("5. Ver alertas de stock bajo.")
        print("6. Buscar producto por nombre.")
        print("7. Ver historial de movimiento de un producto.")
        print("8. Crear respaldo de Inventario.")
        print("9. Importar data desde un archivo csv.")
        print("10. Generar reporte de valorizacion de inventario.")
        print("0. Salir")
        
        opcion = input("\nSeleccione una opción: ")

        if opcion == "1":
            mostrar_inventario()
        elif opcion == "2":
            añadir_producto_nuevo()
        elif opcion == "3":
            retirar_producto()
        elif opcion == "4":
            registrar_compra()
        elif opcion == "5":
            mostrar_alertas_stock_bajo()
        elif opcion == "6":
            buscar_producto_inteligente()
        elif opcion =="7":
            ver_historial_producto()
        elif opcion == "8":
            exportar_inventario_csv()
        elif opcion == "9":
            importar_desde_csv_flexible()
        elif opcion == "10":
            reporte_valorizacion()
        elif opcion == "0":
            print("Saliendo del sistema... ¡Buen trabajo hoy!")
            sys.exit()
        else:
            print("❌ Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    menu_principal()