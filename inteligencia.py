from __future__ import annotations

import agente


def procesar(
    texto,
    log_fn=None,
):

    return agente.ejecutar_objetivo(
        texto,
        log_fn
    )
