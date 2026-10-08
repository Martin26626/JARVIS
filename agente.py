from __future__ import annotations

from cerebro_propio import CerebroJARVIS

_cerebro_propio = CerebroJARVIS()


import re

import aprendizaje
import cerebro_aprendizaje
import herramientas
import memoria_rapida
import planificador
import verificador
import formateador_respuestas


MAX_INTENTOS = 2


def _normalizar_objetivo(objetivo):
    """Normaliza errores frecuentes sin alterar el significado de la orden."""
    texto = str(objetivo or "").strip()

    reemplazos = {
        r"\babrime\b": "abre",
        r"\babreme\b": "abre",
        r"\bmostrame\b": "muestra",
        r"\bmuestrame\b": "muestra",
        r"\bprocezos\b": "procesos",
        r"\bintelijencia\b": "inteligencia",
        r"\bq\s+es\b": "que es",
    }

    for patron, reemplazo in reemplazos.items():
        texto = re.sub(
            patron,
            reemplazo,
            texto,
            flags=re.IGNORECASE,
        )

    return texto


def _log(log_fn, texto):
    if log_fn:
        try:
            log_fn(texto, "accion")
        except Exception:
            pass


def _ejecutar_directo(
    objetivo,
    herramienta,
    argumentos,
    log_fn=None,
):
    try:

        _log(
            log_fn,
            f"Ejecutando {herramienta} directamente..."
        )

        resultado = herramientas.ejecutar(
            herramienta,
            argumentos
        )

        correcto = verificador.verificar(
            herramienta,
            argumentos,
            resultado
        )

        aprendizaje.aprender(
            objetivo,
            herramienta,
            argumentos,
            resultado,
            correcto,
            None if correcto else str(resultado)
        )

        if not correcto:
            return {
                "exito": False,
                "ruta_rapida": True,
                "respuesta": str(resultado),
            }

        return {
            "exito": True,
            "ruta_rapida": True,
            "desde_memoria": False,
            "respuesta":
                formateador_respuestas.formatear(
                    herramienta,
                    resultado
                ),
            "resultado_real": resultado,
        }

    except Exception as exc:

        return {
            "exito": False,
            "ruta_rapida": True,
            "respuesta": str(exc),
        }


def _extraer_objetivo_ventana(texto):
    texto = texto.strip()

    patrones = [
        r"(?:enfoca|enfocÃ¡|enfocar|pon(?:Ã©)? al frente|trae al frente|traÃ© al frente)"
        r"(?:\s+(?:la|el))?\s+(?:ventana\s+(?:de|del|de la)\s+)?(.+)$",

        r"(?:minimiza|minimizÃ¡|minimizar)"
        r"(?:\s+(?:la|el))?\s+(?:ventana\s+(?:de|del|de la)\s+)?(.+)$",

        r"(?:maximiza|maximizÃ¡|maximizar)"
        r"(?:\s+(?:la|el))?\s+(?:ventana\s+(?:de|del|de la)\s+)?(.+)$",

        r"(?:cierra|cerrÃ¡|cerrar)"
        r"(?:\s+(?:la|el))?\s+(?:ventana\s+(?:de|del|de la)\s+)?(.+)$",
    ]

    for patron in patrones:

        m = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if m:

            objetivo = m.group(1).strip()

            objetivo = re.sub(
                r"\s+$",
                "",
                objetivo
            )

            return objetivo

    return None


def _ruta_directa_pc(
    objetivo,
    log_fn=None,
):

    texto = objetivo.lower().strip()

    # ========================================================
    # HARDWARE
    # ========================================================

    palabras_hardware = [
        "ram",
        "memoria ram",
        "procesador",
        "cpu",
        "gpu",
        "tarjeta grafica",
        "tarjeta grÃ¡fica",
        "hardware",
        "especificaciones",
        "componentes de mi pc",
        "componentes de la pc",
        "informacion de mi pc",
        "informaciÃ³n de mi pc",
        "datos de mi pc",
    ]

    if any(
    re.search(
        r"(?<!\w)" + re.escape(palabra) + r"(?!\w)",
        texto
    )
    for palabra in palabras_hardware
):

        return _ejecutar_directo(
            objetivo,
            "informacion_sistema",
            {},
            log_fn
        )

    # ========================================================
    # CONSULTAR VENTANAS
    # ========================================================

    consultar_ventanas = [
        "muestra las ventanas",
        "mostrame las ventanas",
        "muÃ©strame las ventanas",
        "que ventanas tengo abiertas",
        "quÃ© ventanas tengo abiertas",
        "que tengo abierto",
        "quÃ© tengo abierto",
        "que esta abierto",
        "quÃ© estÃ¡ abierto",
        "ventanas abiertas",
        "lista las ventanas",
        "listar las ventanas",
        "lista de ventanas",
        "dime las ventanas abiertas",
        "decime las ventanas abiertas",
    ]

    if any(
        frase in texto
        for frase in consultar_ventanas
    ):

        return _ejecutar_directo(
            objetivo,
            "listar_ventanas",
            {},
            log_fn
        )

    # ========================================================
    # ORDENES SOBRE UNA VENTANA
    # ========================================================

    if any(
        palabra in texto
        for palabra in [
            "enfoca",
            "enfocÃ¡",
            "enfocar",
            "trae al frente",
            "traÃ© al frente",
            "pon al frente",
            "ponÃ© al frente",
        ]
    ):

        objetivo_ventana = _extraer_objetivo_ventana(
            objetivo
        )

        if objetivo_ventana:

            return _ejecutar_directo(
                objetivo,
                "enfocar_ventana",
                {
                    "titulo":
                        objetivo_ventana
                },
                log_fn
            )

    if any(
        palabra in texto
        for palabra in [
            "minimiza",
            "minimizÃ¡",
            "minimizar",
        ]
    ):

        objetivo_ventana = _extraer_objetivo_ventana(
            objetivo
        )

        if objetivo_ventana:

            return _ejecutar_directo(
                objetivo,
                "minimizar_ventana",
                {
                    "titulo":
                        objetivo_ventana
                },
                log_fn
            )

    if any(
        palabra in texto
        for palabra in [
            "maximiza",
            "maximizÃ¡",
            "maximizar",
        ]
    ):

        objetivo_ventana = _extraer_objetivo_ventana(
            objetivo
        )

        if objetivo_ventana:

            return _ejecutar_directo(
                objetivo,
                "maximizar_ventana",
                {
                    "titulo":
                        objetivo_ventana
                },
                log_fn
            )

    if any(
        palabra in texto
        for palabra in [
            "cierra",
            "cerrÃ¡",
            "cerrar",
        ]
    ) and "ventana" in texto:

        objetivo_ventana = _extraer_objetivo_ventana(
            objetivo
        )

        if objetivo_ventana:

            return _ejecutar_directo(
                objetivo,
                "cerrar_ventana",
                {
                    "titulo":
                        objetivo_ventana
                },
                log_fn
            )

    # ========================================================
    # PROCESOS
    # ========================================================

    frases_procesos = [
        "muestra los procesos",
        "muÃ©strame los procesos",
        "mostrame los procesos",
        "que procesos tengo abiertos",
        "quÃ© procesos tengo abiertos",
        "procesos abiertos",
        "lista los procesos",
        "listar los procesos",
        "lista de procesos",
        "que programas estan ejecutandose",
        "quÃ© programas estÃ¡n ejecutÃ¡ndose",
        "que programas estan abiertos",
        "quÃ© programas estÃ¡n abiertos",
    ]

    if any(
        frase in texto
        for frase in frases_procesos
    ):

        return _ejecutar_directo(
            objetivo,
            "listar_procesos",
            {
                "limite":
                    30
            },
            log_fn
        )

    return None


def _ejecutar_memoria(
    objetivo,
    experiencia,
    log_fn
):

    herramienta = experiencia.get(
        "herramienta"
    )

    argumentos = experiencia.get(
        "argumentos",
        {}
    )

    _log(
        log_fn,
        (
            "Usando memoria rÃ¡pida "
            f"(similitud {experiencia.get('similitud', 0)})"
        )
    )

    try:

        resultado = herramientas.ejecutar(
            herramienta,
            argumentos
        )

        correcto = verificador.verificar(
            herramienta,
            argumentos,
            resultado
        )

        aprendizaje.aprender(
            objetivo,
            herramienta,
            argumentos,
            resultado,
            correcto,
            None if correcto else str(resultado)
        )

        if correcto:

            memoria_rapida.registrar_uso(
                objetivo
            )

            return {
                "exito": True,
                "desde_memoria": True,
                "respuesta":
                    formateador_respuestas.formatear(
                        herramienta,
                        resultado
                    ),
                "resultado_real":
                    resultado,
            }

        return {
            "exito": False,
            "desde_memoria": True,
            "respuesta":
                str(resultado),
        }

    except Exception as exc:

        return {
            "exito": False,
            "desde_memoria": True,
            "respuesta":
                str(exc),
        }


def ejecutar_objetivo(
    objetivo,
    log_fn=None,
):

    objetivo = _normalizar_objetivo(objetivo)

    aprendizaje.aprender_de_usuario(
        objetivo
    )

    # ========================================================
    # 1. RUTAS DIRECTAS
    # ========================================================

    directo = _ruta_directa_pc(
        objetivo,
        log_fn
    )

    if directo is not None:
        return directo

    # ========================================================
    # 2. MEMORIA RAPIDA
    # ========================================================

    experiencia = memoria_rapida.buscar(
        objetivo,
        umbral=0.90
    )

    if experiencia:

        resultado = _ejecutar_memoria(
            objetivo,
            experiencia,
            log_fn
        )

        if resultado.get("exito"):
            return resultado

    # ========================================================
    # 3. OLLAMA
    # ========================================================

    error_anterior = None
    plan_anterior = None

    for intento in range(
        1,
        MAX_INTENTOS + 1
    ):

        _log(
            log_fn,
            f"Razonando ({intento}/{MAX_INTENTOS})..."
        )

        try:

            plan_raw = cerebro_aprendizaje.pensar(
                objetivo,
                error_anterior,
                plan_anterior
            )

        except Exception as exc:

            return {
                "exito": False,
                "respuesta":
                    f"No pude comunicarme con Ollama: {exc}",
            }

        plan = planificador.validar(
            plan_raw
        )

        # JARVIS_ALPHA_PLAN_VACIO_FALLBACK
        # Si el segundo intento devuelve un plan vacio
        # despues de un fallo real, usar una estrategia
        # alternativa segura.

        if (
            plan_anterior is not None
            and error_anterior is not None
            and isinstance(plan, dict)
            and not plan.get("acciones")
        ):

            acciones_previas = (
                plan_anterior.get(
                    "acciones",
                    []
                )
                if isinstance(
                    plan_anterior,
                    dict
                )
                else []
            )

            if acciones_previas:

                accion_previa = acciones_previas[0]

                if isinstance(
                    accion_previa,
                    dict
                ):

                    herramienta_previa = (
                        accion_previa.get(
                            "herramienta",
                            ""
                        )
                    )

                    if herramienta_previa == "buscar_app":

                        nombre_previo = (
                            accion_previa
                            .get(
                                "argumentos",
                                {}
                            )
                            .get(
                                "nombre",
                                ""
                            )
                        )

                        plan = {
                            "tipo": "plan",
                            "objetivo": (
                                "comprobar procesos para "
                                "verificar si la aplicacion "
                                "esta ejecutandose"
                            ),
                            "acciones": [
                                {
                                    "herramienta": "listar_procesos",
                                    "argumentos": {
                                        "limite": 30
                                    },
                                    "requiere_confirmacion": False
                                }
                            ],
                            "respuesta_final": (
                                f"No encontre {nombre_previo}. "
                                "Comprobare los procesos "
                                "para verificar si esta ejecutandose."
                            )
                        }

        # ====================================================
        # EVITAR REPETIR EXACTAMENTE EL MISMO PLAN FALLIDO
        # ====================================================

        if (
            plan_anterior is not None
            and error_anterior is not None
        ):

            acciones_nuevas = (
                plan.get(
                    "acciones",
                    []
                )
            )

            acciones_anteriores = (
                plan_anterior.get(
                    "acciones",
                    []
                )
                if isinstance(
                    plan_anterior,
                    dict
                )
                else []
            )

            if (
                acciones_nuevas
                and
                acciones_anteriores
                and
                acciones_nuevas
                == acciones_anteriores
            ):

                herramienta_original = acciones_nuevas[0].get(
                    "herramienta",
                    ""
                )

                if herramienta_original == "buscar_app":

                    nombre_original = (
                        acciones_nuevas[0]
                        .get("argumentos", {})
                        .get("nombre", "")
                    )

                    plan = {
                        "tipo": "plan",
                        "objetivo": (
                            "comprobar de forma alternativa "
                            "si la aplicacion esta ejecutandose"
                        ),
                        "acciones": [
                            {
                                "herramienta": "listar_procesos",
                                "argumentos": {
                                    "limite": 30
                                },
                                "requiere_confirmacion": False
                            }
                        ],
                        "respuesta_final": (
                            f"No encontre {nombre_original}. "
                            "Comprobare los procesos para verificar "
                            "si esta ejecutandose."
                        )
                    }

                else:

                    return {
                        "exito": False,
                        "respuesta":
                            (
                                "La primera estrategia fallo "
                                "y el siguiente intento propone "
                                "exactamente la misma accion. "
                                "No la repetire."
                            ),
                        "error":
                            error_anterior,
                        "plan_repetido":
                            True
                    }

        if plan.get("tipo") == "conversacion":

            return {
                "exito": True,
                "respuesta":
                    plan.get(
                        "respuesta",
                        ""
                    ),
            }

        if plan.get("tipo") == "error":

            return {
                "exito": False,
                "respuesta":
                    plan.get(
                        "mensaje",
                        "Plan invalido."
                    ),
            }

        if not planificador.hay_acciones(
            plan
        ):

            return {
                "exito": True,
                "respuesta":
                    plan.get(
                        "respuesta_final",
                        "Entendido."
                    ),
            }

        resultados = []
        fallo = None
        plan_anterior = plan

        for accion in plan["acciones"]:

            herramienta = accion[
                "herramienta"
            ]

            argumentos = accion[
                "argumentos"
            ]

            if accion.get(
                "requiere_confirmacion"
            ):

                return {
                    "exito": False,
                    "requiere_confirmacion": True,
                    "respuesta":
                        (
                            "Necesito confirmacion "
                            f"para usar {herramienta}."
                        ),
                }

            try:

                resultado = herramientas.ejecutar(
                    herramienta,
                    argumentos
                )

                correcto = verificador.verificar(
                    herramienta,
                    argumentos,
                    resultado
                )

                aprendizaje.aprender(
                    objetivo,
                    herramienta,
                    argumentos,
                    resultado,
                    correcto,
                    None if correcto else str(resultado)
                )

                resultados.append({
                    "herramienta":
                        herramienta,
                    "argumentos":
                        argumentos,
                    "resultado":
                        resultado,
                    "correcto":
                        correcto,
                })


                # ====================================================
                # ANALISIS DEL RESULTADO CON EL CEREBRO PROPIO
                # ====================================================

                analisis_cerebro_propio = None

                try:

                    entrada_cerebro = [{
                        "herramienta":
                            herramienta,

                        "argumentos":
                            argumentos,

                        "resultado":
                            resultado,

                        "correcto":
                            correcto,

                        "datos":
                            resultado
                            if isinstance(
                                resultado,
                                dict
                            )
                            else {}
                    }]

                    analisis_cerebro_propio = (
                        _cerebro_propio.analizar_resultados(
                            entrada_cerebro
                        )
                    )

                except Exception as exc:

                    analisis_cerebro_propio = {
                        "problemas": [],
                        "causas_posibles": [],
                        "siguiente_paso": None,
                        "error": str(exc)
                    }

                resultados[-1][
                    "analisis_cerebro_propio"
                ] = analisis_cerebro_propio


                if not correcto:

                    fallo = (
                        f"{herramienta} fallo: "
                        f"{resultado}"
                    )

                    error_anterior = fallo
                    break

            except Exception as exc:

                aprendizaje.aprender(
                    objetivo,
                    herramienta,
                    argumentos,
                    "",
                    False,
                    str(exc)
                )

                fallo = str(exc)
                error_anterior = fallo
                break

        if fallo is None:

            if (
                len(
                    plan.get(
                        "acciones",
                        []
                    )
                ) == 1
                and len(resultados) == 1
                and resultados[0].get(
                    "correcto"
                )
            ):

                accion = plan[
                    "acciones"
                ][0]

                if not accion.get(
                    "requiere_confirmacion"
                ):

                    memoria_rapida.guardar(
                        objetivo,
                        accion[
                            "herramienta"
                        ],
                        accion.get(
                            "argumentos",
                            {}
                        ),
                        resultados[0].get(
                            "resultado"
                        )
                    )

            if len(resultados) == 1:

                primero = resultados[0]

                respuesta_base = (
                    formateador_respuestas.formatear(
                        primero[
                            "herramienta"
                        ],
                        primero[
                            "resultado"
                        ]
                    )
                )

                analisis = primero.get(
                    "analisis_cerebro_propio"
                )

                respuesta_final = respuesta_base

                if isinstance(
                    analisis,
                    dict
                ):

                    problemas = analisis.get(
                        "problemas",
                        []
                    )

                    siguiente_paso = analisis.get(
                        "siguiente_paso"
                    )

                    if problemas:

                        respuesta_final += (
                            " DetectÃ© lo siguiente: "
                            + " ".join(
                                str(problema)
                                for problema in problemas
                            )
                        )

                    elif siguiente_paso:

                        respuesta_final += (
                            " No detectÃ© un problema "
                            "evidente. "
                            + str(
                                siguiente_paso
                            )
                        )

                return {
                    "exito": True,
                    "desde_memoria": False,
                    "respuesta":
                        respuesta_final,
                    "resultado_real":
                        primero[
                            "resultado"
                        ],
                    "analisis":
                        analisis,
                    "resultados":
                        resultados,
                }

            return {
                "exito": True,
                "desde_memoria": False,
                "respuesta":
                    plan.get(
                        "respuesta_final",
                        "Tarea completada."
                    ),
                "resultados":
                    resultados,
            }

    return {
        "exito": False,
        "respuesta":
            "No pude completar la tarea."
    }

