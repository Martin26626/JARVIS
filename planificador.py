from __future__ import annotations


HERRAMIENTAS_PERMITIDAS = {
    # PC
    "abrir_app",
    "abrir_ruta",
    "abrir_carpeta_especial",
    "abrir_explorador",
    "abrir_terminal",

    "mover",
    "copiar",
    "renombrar",
    "crear_carpeta",
    "crear_archivo",

    "buscar",
    "buscar_comprimidos",
    "extraer",
    "eliminar",

    "listar_apps",
    "buscar_app",

    # Procesos
    "listar_procesos",
    "proceso_existe",
    "cerrar_proceso",

    # Ventanas
    "listar_ventanas",
    "enfocar_ventana",
    "minimizar_ventana",
    "maximizar_ventana",
    "cerrar_ventana",

    # Mouse / teclado
    "escribir",
    "tecla",
    "click",
    "doble_click",
    "mover_mouse",
    "scroll",

    # Pantalla
    "captura_pantalla",
    "posicion_mouse",

    # Sistema
    "informacion_sistema",
}


PELIGROSAS = {
    "eliminar",
    "cerrar_proceso",
    "cerrar_ventana",

    "escribir",
    "tecla",
    "click",
    "doble_click",
    "mover_mouse",
    "scroll",

    "abrir_terminal",
}


def validar(plan):

    if not isinstance(plan, dict):
        return {
            "tipo": "error",
            "mensaje": "Plan invalido."
        }

    if plan.get("tipo") != "plan":
        return plan

    acciones = plan.get(
        "acciones",
        []
    )

    if not isinstance(acciones, list):
        return {
            "tipo": "error",
            "mensaje": "Acciones invalidas."
        }

    nuevas = []

    for accion in acciones:

        if not isinstance(
            accion,
            dict
        ):
            continue

        herramienta = accion.get(
            "herramienta"
        )

        argumentos = accion.get(
            "argumentos",
            {}
        )

        if herramienta not in (
            HERRAMIENTAS_PERMITIDAS
        ):
            continue

        if not isinstance(
            argumentos,
            dict
        ):
            argumentos = {}

        nuevas.append({
            "herramienta":
                herramienta,

            "argumentos":
                argumentos,

            "requiere_confirmacion":
                herramienta in PELIGROSAS,
        })

    return {
        "tipo":
            "plan",

        "objetivo":
            plan.get(
                "objetivo",
                ""
            ),

        "acciones":
            nuevas,

        "respuesta_final":
            plan.get(
                "respuesta_final",
                "Tarea completada."
            ),
    }


def hay_acciones(plan):
    return bool(
        isinstance(
            plan,
            dict
        )
        and plan.get(
            "tipo"
        ) == "plan"
        and plan.get(
            "acciones"
        )
    )
