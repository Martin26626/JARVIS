from __future__ import annotations


def formatear(herramienta, resultado):
    if herramienta == "informacion_sistema":
        if not isinstance(resultado, dict):
            return str(resultado)

        partes = []

        ram = resultado.get("ram_total_gb")
        cpu = resultado.get("cpu")
        gpus = resultado.get("gpus", [])
        ram_disponible = resultado.get("ram_disponible_gb")
        nucleos = resultado.get("nucleos")
        hilos = resultado.get("hilos")

        if ram is not None:
            partes.append(f"RAM: {ram} GB")

        if cpu:
            partes.append(f"Procesador: {cpu}")

        if gpus:
            partes.append(
                "GPU: " + ", ".join(str(gpu) for gpu in gpus)
            )

        if ram_disponible is not None:
            partes.append(
                f"RAM disponible: {ram_disponible} GB"
            )

        if nucleos is not None:
            partes.append(
                f"Nucleos: {nucleos}"
            )

        if hilos is not None:
            partes.append(
                f"Hilos: {hilos}"
            )

        return "\n".join(partes)

    if herramienta == "listar_procesos":
        if isinstance(resultado, list):
            if not resultado:
                return "No encontre procesos."

            return "\n".join(
                f"{x.get('nombre', '?')} "
                f"(PID {x.get('pid', '?')})"
                for x in resultado[:30]
            )

    if herramienta == "listar_ventanas":
        if isinstance(resultado, list):
            if not resultado:
                return "No encontre ventanas abiertas."

            return "\n".join(
                x.get("titulo", "")
                for x in resultado[:30]
                if x.get("titulo")
            )

    if herramienta == "listar_apps":
        if isinstance(resultado, list):
            if not resultado:
                return "No encontre aplicaciones."

            return "\n".join(
                f"{x.get('name', '')} -> {x.get('path', '')}"
                for x in resultado[:50]
            )

    if herramienta in {
        "buscar",
        "buscar_comprimidos",
    }:
        if isinstance(resultado, list):
            if not resultado:
                return "No encontre archivos."

            return "\n".join(
                str(x)
                for x in resultado[:50]
            )

    return str(resultado)
