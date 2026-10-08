from __future__ import annotations

import control_pc


def verificar(
    herramienta,
    argumentos,
    resultado,
):
    if resultado is None:
        return False

    if isinstance(
        resultado,
        str
    ):

        if not resultado.strip():
            return False

        texto = resultado.lower()

        errores = [
            "error:",
            "not found",
            "not available",
            "could not",
            "no encontre",
            "no pude",
            "no disponible",
        ]

        if any(
            error in texto
            for error in errores
        ):
            return False

    try:

        if herramienta in {
            "buscar",
            "buscar_comprimidos",
        }:
            return bool(resultado)

        if herramienta == "proceso_existe":
            return bool(resultado)

        if herramienta == "abrir_app":

            return (
                control_pc.find_app(
                    argumentos.get(
                        "nombre",
                        ""
                    )
                )
                is not None
            )

        if herramienta == "buscar_app":

            nombre = argumentos.get(
                "nombre",
                ""
            )

            encontrado = control_pc.find_app(
                nombre
            )

            return encontrado is not None

        if herramienta == "crear_carpeta":

            return control_pc.path_exists(
                argumentos.get(
                    "ruta",
                    ""
                )
            )

        if herramienta == "crear_archivo":

            return control_pc.path_exists(
                argumentos.get(
                    "ruta",
                    ""
                )
            )

        return True

    except Exception:
        return False
