from __future__ import annotations

import control_pc
import control_pc_avanzado


def ejecutar(
    nombre,
    argumentos=None,
):
    a = argumentos or {}

    acciones = {

        # ----------------------------------------------------
        # CONTROL PC BASICO
        # ----------------------------------------------------

        "abrir_app":
            lambda:
            control_pc.open_app(
                a.get("nombre", "")
            ),

        "abrir_ruta":
            lambda:
            control_pc.open_path(
                a.get("ruta", "")
            ),

        "abrir_carpeta_especial":
            lambda:
            control_pc.open_special_folder(
                a.get("nombre", "")
            ),

        "mover":
            lambda:
            control_pc.move_item(
                a.get("origen", ""),
                a.get("destino", "")
            ),

        "copiar":
            lambda:
            control_pc.copy_item(
                a.get("origen", ""),
                a.get("destino", "")
            ),

        "renombrar":
            lambda:
            control_pc.rename_item(
                a.get("origen", ""),
                a.get("nuevo_nombre", "")
            ),

        "crear_carpeta":
            lambda:
            control_pc.create_folder(
                a.get("ruta", "")
            ),

        "crear_archivo":
            lambda:
            control_pc.create_file(
                a.get("ruta", ""),
                a.get("contenido", "")
            ),

        "buscar":
            lambda:
            control_pc.search_files(
                a.get("consulta", ""),
                a.get("ruta")
            ),

        "buscar_comprimidos":
            lambda:
            control_pc.find_archives(
                a.get("ruta")
            ),

        "extraer":
            lambda:
            control_pc.extract_archive(
                a.get("archivo", ""),
                a.get("destino")
            ),

        "eliminar":
            lambda:
            control_pc.delete_item(
                a.get("ruta", "")
            ),

        "listar_apps":
            lambda:
            control_pc.list_installed_apps(
                limit=int(
                    a.get("limite", 100)
                )
            ),

        "buscar_app":
            lambda:
            control_pc.find_app(
                a.get("nombre", "")
            ),

        # ----------------------------------------------------
        # PROCESOS
        # ----------------------------------------------------

        "listar_procesos":
            lambda:
            control_pc_avanzado.listar_procesos(
                a.get("filtro"),
                int(a.get("limite", 100))
            ),

        "proceso_existe":
            lambda:
            control_pc_avanzado.proceso_existe(
                a.get("nombre", "")
            ),

        "cerrar_proceso":
            lambda:
            control_pc_avanzado.cerrar_proceso(
                a.get("nombre", "")
            ),

        # ----------------------------------------------------
        # VENTANAS
        # ----------------------------------------------------

        "listar_ventanas":
            lambda:
            control_pc_avanzado.listar_ventanas(),

        "enfocar_ventana":
            lambda:
            control_pc_avanzado.enfocar_ventana(
                a.get("titulo", "")
            ),

        "minimizar_ventana":
            lambda:
            control_pc_avanzado.minimizar_ventana(
                a.get("titulo", "")
            ),

        "maximizar_ventana":
            lambda:
            control_pc_avanzado.maximizar_ventana(
                a.get("titulo", "")
            ),

        "cerrar_ventana":
            lambda:
            control_pc_avanzado.cerrar_ventana(
                a.get("titulo", "")
            ),

        # ----------------------------------------------------
        # TECLADO / MOUSE
        # ----------------------------------------------------

        "escribir":
            lambda:
            control_pc_avanzado.escribir(
                a.get("texto", "")
            ),

        "tecla":
            lambda:
            control_pc_avanzado.tecla(
                a.get("nombre", "")
            ),

        "click":
            lambda:
            control_pc_avanzado.click(
                a.get("x"),
                a.get("y"),
                a.get("boton", "left")
            ),

        "doble_click":
            lambda:
            control_pc_avanzado.doble_click(
                a.get("x"),
                a.get("y")
            ),

        "mover_mouse":
            lambda:
            control_pc_avanzado.mover_mouse(
                a.get("x"),
                a.get("y")
            ),

        "scroll":
            lambda:
            control_pc_avanzado.scroll(
                a.get("cantidad", 1)
            ),

        # ----------------------------------------------------
        # PANTALLA
        # ----------------------------------------------------

        "captura_pantalla":
            lambda:
            control_pc_avanzado.capturar_pantalla(
                a.get("destino")
            ),

        "posicion_mouse":
            lambda:
            control_pc_avanzado.posicion_mouse(),

        # ----------------------------------------------------
        # EXPLORADOR / TERMINAL
        # ----------------------------------------------------

        "abrir_explorador":
            lambda:
            control_pc_avanzado.abrir_explorador(
                a.get("ruta")
            ),

        "abrir_terminal":
            lambda:
            control_pc_avanzado.abrir_terminal(),

        # ----------------------------------------------------
        # SISTEMA
        # ----------------------------------------------------

        "informacion_sistema":
            lambda:
            control_pc_avanzado.informacion_sistema(),
    }

    funcion = acciones.get(nombre)

    if funcion is None:
        return (
            "ERROR: herramienta no disponible: "
            f"{nombre}"
        )

    try:
        return funcion()

    except Exception as exc:
        return f"ERROR: {exc}"

