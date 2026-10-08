from __future__ import annotations
import datetime

from pathlib import Path

import json
from dataclasses import dataclass, field
from typing import Any


# ============================================================
# ESTADOS
# ============================================================

class Estado:
    NUEVO = "nuevo"
    ANALIZANDO = "analizando"
    PLANIFICANDO = "planificando"
    EJECUTANDO = "ejecutando"
    VERIFICANDO = "verificando"
    COMPLETADO = "completado"
    ERROR = "error"


# ============================================================
# OBJETIVO
# ============================================================

@dataclass
class Objetivo:

    texto: str

    intencion: str = ""

    prioridad: str = "normal"

    solo_observar: bool = False

    requiere_confirmacion: bool = False

    requisitos: list[str] = field(
        default_factory=list
    )

    riesgos: list[str] = field(
        default_factory=list
    )


# ============================================================
# ACCION
# ============================================================

@dataclass
class Accion:

    nombre: str

    argumentos: dict[str, Any] = field(
        default_factory=dict
    )

    motivo: str = ""

    peligrosa: bool = False


# ============================================================
# PLAN
# ============================================================

@dataclass
class Plan:

    objetivo: str

    acciones: list[Accion] = field(
        default_factory=list
    )

    verificacion: str = ""

    alternativa: str = ""

    valido: bool = False


# ============================================================
# RESULTADO
# ============================================================

@dataclass
class Resultado:

    exito: bool

    mensaje: str

    datos: Any = None

    error: str | None = None


# ============================================================
# CEREBRO
# ============================================================

MEMORIA_ARCHIVO = Path("memoria_cerebro.json")


class CerebroJARVIS:

    def __init__(self):

        self.estado = Estado.NUEVO

        self.objetivo_actual: Objetivo | None = None

        self.plan_actual: Plan | None = None

        self.historial: list[dict[str, Any]] = []

        self.conocimientos: dict[str, Any] = {}

        self.cargar_memoria()

    # --------------------------------------------------------
    # V18.2.1 - MOTOR CONVERSACIONAL PROPIO
    # --------------------------------------------------------

    def obtener_contexto_conversacional(
        self,
        limite=10
    ):
        """
        Obtiene los últimos turnos conversacionales
        relevantes del historial.
        """

        if limite <= 0:
            return []

        conversaciones = []

        for registro in reversed(self.historial):

            if not isinstance(
                registro,
                dict
            ):
                continue

            if registro.get(
                "tipo"
            ) != "conversacion":
                continue

            conversaciones.append(
                registro
            )

            if len(
                conversaciones
            ) >= limite:
                break

        conversaciones.reverse()

        return conversaciones


    def construir_contexto_conversacional(
        self,
        limite=10
    ):
        """
        Convierte el contexto conversacional
        en texto legible para el cerebro.
        """

        registros = (
            self.obtener_contexto_conversacional(
                limite
            )
        )

        if not registros:

            return ""


        partes = []

        for registro in registros:

            usuario = str(
                registro.get(
                    "usuario",
                    ""
                )
            ).strip()

            respuesta = str(
                registro.get(
                    "respuesta",
                    ""
                )
            ).strip()

            if usuario:

                partes.append(
                    "Usuario: "
                    + usuario
                )

            if respuesta:

                partes.append(
                    "JARVIS: "
                    + respuesta
                )


        return "\n".join(
            partes
        )


    def preparar_mensaje_con_contexto(
        self,
        mensaje,
        limite=10
    ):
        """
        Combina el mensaje actual con el contexto
        conversacional reciente.
        """

        mensaje = str(
            mensaje
        ).strip()

        contexto = (
            self.construir_contexto_conversacional(
                limite
            )
        )

        if not contexto:

            return (
                "MENSAJE ACTUAL:\n"
                + mensaje
            )

        return (
            "CONTEXTO CONVERSACIONAL:\n"
            + contexto
            + "\n\n"
            + "MENSAJE ACTUAL:\n"
            + mensaje
        )


    def preparar_respuesta_contextual(
        self,
        mensaje,
        limite=10
    ):
        """
        Prepara la informacion que el motor de respuesta
        necesita para responder teniendo en cuenta el contexto.
        """

        interpretacion = (
            self.interpretar_mensaje_con_contexto(
                mensaje,
                limite
            )
        )

        respuesta = {
            "mensaje": mensaje,
            "usar_contexto":
                interpretacion.get(
                    "necesita_contexto",
                    False
                ),
            "es_independiente":
                interpretacion.get(
                    "es_independiente",
                    False
                ),
            "tema":
                interpretacion.get(
                    "tema_detectado"
                ),
            "ultimo_turno":
                interpretacion.get(
                    "ultimo_turno"
                ),
            "contexto":
                interpretacion.get(
                    "contexto",
                    []
                )
        }

        if respuesta["usar_contexto"]:

            respuesta["instruccion"] = (
                "Responder teniendo en cuenta "
                "la conversación anterior."
            )

        else:

            respuesta["instruccion"] = (
                "Responder únicamente al "
                "mensaje actual."
            )

        return respuesta


    def interpretar_mensaje_con_contexto(
        self,
        mensaje,
        limite=10
    ):
        """
        Decide si el mensaje actual continúa la conversación
        o representa una consulta independiente.
        """

        import unicodedata

        mensaje_original = str(
            mensaje
        ).strip()

        def normalizar(texto):

            texto = unicodedata.normalize(
                "NFD",
                str(texto).lower()
            )

            return "".join(
                caracter
                for caracter in texto
                if unicodedata.category(
                    caracter
                ) != "Mn"
            ).strip()

        texto_mensaje = normalizar(
            mensaje_original
        )

        datos = (
            self.analizar_mensaje_con_contexto(
                mensaje_original,
                limite
            )
        )

        contexto = datos.get(
            "contexto",
            []
        )

        ultimo_turno = (
            contexto[-1]
            if contexto
            else None
        )

        referencias_directas = [
            "eso",
            "esa",
            "ese",
            "esto",
            "esta",
            "este",
            "lo anterior",
            "el anterior",
            "la anterior",
            "lo que dije",
            "lo que te dije",
            "lo que hablamos",
            "ese programa",
            "ese juego",
            "esa cosa"
        ]

        contiene_referencia = any(
            referencia in texto_mensaje
            for referencia in referencias_directas
        )

        # ----------------------------------------------------
        # DETECCION DE CONTINUIDAD
        # ----------------------------------------------------

        conectores = [
            "y ",
            "tambien ",
            "ademas ",
            "entonces ",
            "pero ",
            "aunque ",
            "por eso ",
            "por lo tanto ",
            "y si ",
            "porque "
        ]

        comienza_conector = any(
            texto_mensaje.startswith(
                conector
            )
            for conector in conectores
        )

        preguntas_independientes = [
            "que hora es",
            "que dia es",
            "que fecha es",
            "como esta el clima",
            "que tiempo hace",
            "como esta el tiempo"
        ]

        es_independiente = any(
            pregunta in texto_mensaje
            for pregunta in preguntas_independientes
        )

        # Las consultas independientes siempre tienen prioridad.
        necesita_contexto = False

        if not es_independiente and contexto:

            if contiene_referencia:

                necesita_contexto = True

            elif comienza_conector:

                necesita_contexto = True

            else:

                indicadores_continuidad = [
                    "como empiezo",
                    "como sigo",
                    "por donde empiezo",
                    "que hago ahora",
                    "que puedo hacer",
                    "me sirve",
                    "me sirve para",
                    "como lo hago",
                    "como hacerlo",
                    "puedo hacerlo",
                    "puedo usarlo",
                    "que sigue",
                    "y despues",
                    "y para que sirve",
                    "para que sirve",
                    "y que hace",
                    "y como funciona",
                    "y como se usa",
                    "y para que se usa"
                ]

                es_continuacion_natural = any(
                    indicador in texto_mensaje
                    for indicador in indicadores_continuidad
                )

                if es_continuacion_natural:

                    necesita_contexto = True

                else:

                    palabras_mensaje = set(
                        texto_mensaje.split()
                    )

                    ultimo_usuario = normalizar(
                        ultimo_turno.get(
                            "usuario",
                            ""
                        )
                        if ultimo_turno
                        else ""
                    )

                    palabras_ultimo = set(
                        ultimo_usuario.split()
                    )

                    palabras_comunes = (
                        palabras_mensaje
                        & palabras_ultimo
                    )

                    palabras_utiles = {
                        palabra
                        for palabra in palabras_comunes
                        if len(palabra) > 3
                    }

                    if palabras_utiles:

                        necesita_contexto = True

        tema = None

        if necesita_contexto and contexto:

            texto_contexto = normalizar(
                " ".join(
                    str(
                        registro.get(
                            "usuario",
                            ""
                        )
                    )
                    for registro in contexto[-3:]
                )
            )

            temas = [
                ("python", "python"),
                ("programacion", "programacion"),
                ("programación", "programacion"),
                ("jarvis", "jarvis"),
                ("minecraft", "minecraft"),
                ("roblox", "roblox"),
                ("trabajo", "trabajo"),
                ("estudio", "estudio"),
                ("juego", "juegos"),
                ("pc", "pc")
            ]

            for palabra, nombre in temas:

                if palabra in texto_contexto:

                    tema = nombre
                    break

        return {
            "mensaje": mensaje_original,
            "contexto": contexto,
            "tiene_contexto":
                bool(contexto),
            "necesita_contexto":
                necesita_contexto,
            "es_independiente":
                es_independiente,
            "contiene_referencia":
                contiene_referencia,
            "tema_detectado":
                tema,
            "ultimo_turno":
                ultimo_turno,
            "texto_contextualizado":
                (
                    datos.get(
                        "texto_contextualizado",
                        ""
                    )
                    if necesita_contexto
                    else
                    "MENSAJE ACTUAL:\n"
                    + mensaje_original
                )
        }


    def analizar_mensaje_con_contexto(
        self,
        mensaje,
        limite=10
    ):
        """
        Prepara la informacion necesaria para que
        el cerebro pueda interpretar el mensaje
        teniendo en cuenta la conversacion reciente.
        """

        mensaje = str(
            mensaje
        ).strip()

        contexto = (
            self.obtener_contexto_conversacional(
                limite
            )
        )

        texto_contextualizado = (
            self.preparar_mensaje_con_contexto(
                mensaje,
                limite
            )
        )

        return {
            "mensaje": mensaje,
            "contexto": contexto,
            "texto_contextualizado":
                texto_contextualizado,
            "tiene_contexto":
                bool(contexto)
        }


    def contexto_conversacional(
        self,
        limite=10
    ):
        """
        Devuelve los últimos turnos
        conversacionales.
        """

        return self.obtener_contexto_conversacional(
            limite
        )


    def registrar_turno_conversacion(
        self,
        usuario,
        respuesta
    ):
        """Guarda un turno de conversación en el historial."""

        registro = {
            "tipo": "conversacion",
            "usuario": str(usuario),
            "respuesta": str(respuesta)
        }

        self.historial.append(
            registro
        )

        try:
            self.guardar_memoria()
        except Exception:
            pass

        return registro


    def clasificar_mensaje_conversacional(
        self,
        texto
    ):
        """Clasifica un mensaje conversacional básico."""

        import unicodedata

        t = str(
            texto
        ).lower().strip()

        def normalizar(valor):

            valor = unicodedata.normalize(
                "NFD",
                valor
            )

            return "".join(
                caracter
                for caracter in valor
                if unicodedata.category(
                    caracter
                ) != "Mn"
            )

        t = normalizar(t)

        if not t:
            return "vacio"

        saludos = [
            "hola",
            "buenas",
            "buenos dias",
            "buenas tardes",
            "buenas noches",
            "hey",
            "holi",
            "que tal",
            "como estas"
        ]

        despedidas = [
            "adios",
            "hasta luego",
            "nos vemos",
            "me voy",
            "hasta despues",
            "buenas noches"
        ]

        agradecimientos = [
            "gracias",
            "muchas gracias",
            "te agradezco",
            "gracias jarvis"
        ]

        identidad = [
            "quien eres",
            "que eres",
            "como te llamas",
            "cual es tu nombre"
        ]

        capacidad = [
            "que puedes hacer",
            "que sabes hacer",
            "que haces",
            "para que sirves"
        ]

        confirmacion = [
            "ok",
            "okay",
            "vale",
            "perfecto",
            "entendido",
            "de acuerdo"
        ]

        hora = [
            "que hora es",
            "dime la hora",
            "decime la hora",
            "hora actual",
            "que hora tienes",
            "me dices la hora",
            "me decis la hora"
        ]

        if any(
            frase in t
            for frase in saludos
        ):
            return "saludo"

        if any(
            frase in t
            for frase in despedidas
        ):
            return "despedida"

        if any(
            frase in t
            for frase in agradecimientos
        ):
            return "agradecimiento"

        if any(
            frase in t
            for frase in identidad
        ):
            return "identidad"

        if any(
            frase in t
            for frase in capacidad
        ):
            return "capacidades"

        if any(
            frase in t
            for frase in confirmacion
        ):
            return "confirmacion"

        if any(
            frase in t
            for frase in hora
        ):
            return "hora"

        return "conversacion"



    def resumir_informacion_web_propia(
        self,
        pregunta,
        resultados
    ):
        """
        Selecciona una respuesta directa y natural
        priorizando definiciones y explicaciones.
        """

        import re

        if not resultados:
            return None

        pregunta_lower = (
            str(pregunta)
            .lower()
            .strip()
        )

        es_definicion = (
            "que es " in pregunta_lower
            or
            "qué es " in pregunta_lower
        )

        es_persona = (
            "quien es " in pregunta_lower
            or
            "quién es " in pregunta_lower
        )

        es_funcion = (
            "como funciona " in pregunta_lower
            or
            "cómo funciona " in pregunta_lower
        )

        candidatos = []

        for resultado in resultados:

            cuerpo = str(
                resultado.get(
                    "texto",
                    ""
                )
            ).strip()

            url = str(
                resultado.get(
                    "url",
                    ""
                )
            ).strip()

            titulo = str(
                resultado.get(
                    "titulo",
                    ""
                )
            ).strip()

            if not cuerpo:
                continue

            if "aclick" in url.lower():
                continue

            cuerpo = re.sub(
                r"\s+",
                " ",
                cuerpo
            ).strip()

            # ------------------------------------------------
            # LIMPIEZA DE METADATOS
            # ------------------------------------------------

            patrones_fecha = [
                r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\s*[-:·]?\s*",
                r"^(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\s*[-:·]?\s*",
                r"^\d+\s+(?:days?|weeks?|months?|years?)\s+ago\s*[-:·]?\s*"
            ]

            for patron in patrones_fecha:

                cuerpo = re.sub(
                    patron,
                    "",
                    cuerpo,
                    flags=re.IGNORECASE
                )

            cuerpo = re.sub(
                r"\[[0-9]+\]",
                "",
                cuerpo
            )

            cuerpo = re.sub(
                r"\s+",
                " ",
                cuerpo
            ).strip()

            if not cuerpo:
                continue

            frases = re.split(
                r"(?<=[.!?])\s+",
                cuerpo
            )

            for frase in frases:

                frase = frase.strip(
                    " -:;,.'\""
                )

                palabras = frase.split()

                if len(palabras) < 7:
                    continue

                if len(palabras) > 45:
                    continue

                frase_lower = (
                    frase.lower()
                )

                # ------------------------------------------------
                # DESCARTAR FRAGMENTOS
                # ------------------------------------------------

                basura = [
                    "diccionario de la lengua española:",
                    "definición rae",
                    "definicion rae",
                    "curso completo",
                    "inicia tu carrera",
                    "aprende conceptos básicos",
                    "aprende conceptos basicos",
                    "ha sido visitado",
                    "visitado por",
                    "gusta de jugar al contraste",
                    "viaje desde",
                    "retrieved",
                    "archived from the original"
                ]

                if any(
                    termino in frase_lower
                    for termino in basura
                ):
                    continue

                puntuacion = 0

                # ------------------------------------------------
                # PRIORIDAD DE FUENTES
                # ------------------------------------------------

                url_lower = url.lower()

                if "rae.es" in url_lower:
                    puntuacion += 35

                if "docs.python.org" in url_lower:
                    puntuacion += 35

                if "argentina.gob.ar" in url_lower:
                    puntuacion += 30

                if "gob.es" in url_lower:
                    puntuacion += 30

                if "ibm.com" in url_lower:
                    puntuacion += 25

                if "developers.google.com" in url_lower:
                    puntuacion += 25

                if "wikipedia.org" in url_lower:
                    puntuacion += 10

                # ------------------------------------------------
                # DEFINICIONES
                # ------------------------------------------------

                if es_definicion:

                    if re.search(
                        r"\bes\b",
                        frase_lower
                    ):
                        puntuacion += 35

                    if "consiste en" in frase_lower:
                        puntuacion += 30

                    if "se define como" in frase_lower:
                        puntuacion += 30

                    if "se trata de" in frase_lower:
                        puntuacion += 20

                # ------------------------------------------------
                # PERSONAS
                # ------------------------------------------------

                if es_persona:

                    if " fue " in frase_lower:
                        puntuacion += 35

                    if "físico" in frase_lower:
                        puntuacion += 5

                    if "fisico" in frase_lower:
                        puntuacion += 5

                    if "científico" in frase_lower:
                        puntuacion += 5

                    if "cientifico" in frase_lower:
                        puntuacion += 5

                    if "teoría" in frase_lower:
                        puntuacion += 5

                    if "teoria" in frase_lower:
                        puntuacion += 5

                # ------------------------------------------------
                # COMO FUNCIONA
                # ------------------------------------------------

                if es_funcion:

                    if "funciona" in frase_lower:
                        puntuacion += 35

                    if "interpreta" in frase_lower:
                        puntuacion += 30

                    if "ejecuta" in frase_lower:
                        puntuacion += 30

                    if "procesa" in frase_lower:
                        puntuacion += 25

                    if "compila" in frase_lower:
                        puntuacion += 25

                    if "convierte" in frase_lower:
                        puntuacion += 20

                    if "código" in frase_lower:
                        puntuacion += 12

                    if "codigo" in frase_lower:
                        puntuacion += 12

                    if (
                        "es un lenguaje"
                        in frase_lower
                    ):
                        puntuacion -= 20

                candidatos.append(
                    (
                        puntuacion,
                        frase,
                        titulo,
                        url
                    )
                )

        if not candidatos:
            return None

        candidatos.sort(
            key=lambda item: item[0],
            reverse=True
        )

        # ------------------------------------------------
        # SELECCIONAR LA MEJOR FRASE
        # ------------------------------------------------

        respuesta = candidatos[0][1]

        # Para definiciones, exigir una forma
        # claramente definicional.
        if es_definicion:

            for puntuacion, frase, titulo, url in candidatos:

                frase_lower = frase.lower()

                if (
                    " es " in frase_lower
                    or
                    " consiste en " in frase_lower
                    or
                    "se define como" in frase_lower
                    or
                    "se trata de" in frase_lower
                ):

                    respuesta = frase
                    break

        # Para personas, exigir que explique quién fue.
        elif es_persona:

            for puntuacion, frase, titulo, url in candidatos:

                if (
                    " fue " in frase.lower()
                ):

                    respuesta = frase
                    break

        # Para funcionamiento, evitar definiciones puras.
        elif es_funcion:

            for puntuacion, frase, titulo, url in candidatos:

                frase_lower = frase.lower()

                if any(
                    termino in frase_lower
                    for termino in [
                        "funciona",
                        "interpreta",
                        "ejecuta",
                        "procesa",
                        "compila",
                        "convierte",
                        "código",
                        "codigo"
                    ]
                ):

                    respuesta = frase
                    break

        # ------------------------------------------------
        # LIMPIEZA FINAL
        # ------------------------------------------------

        respuesta = re.sub(
            r"\s+",
            " ",
            respuesta
        ).strip(
            " -:;,.\"'"
        )

        for patron in patrones_fecha:

            respuesta = re.sub(
                patron,
                "",
                respuesta,
                flags=re.IGNORECASE
            )

        respuesta = respuesta.strip()

        if not respuesta:
            return None

        if not respuesta.endswith(
            "."
        ):
            respuesta += "."

        return respuesta



    def investigar_web_propia(
        self,
        pregunta,
        max_resultados=5
    ):
        """
        Busca informacion en Internet cuando el
        conocimiento local no es suficiente.

        No usa Ollama.
        """

        import re

        pregunta = str(
            pregunta
        ).strip()

        if not pregunta:
            return None

        # --------------------------------------------------------
        # Evitar busquedas de contenido sexual explicito.
        # --------------------------------------------------------

        terminos_no_buscar = [
            "pornografia",
            "porno",
            "porn",
            "xxx",
            "sexo explicito",
            "sex explicit",
            "nudes",
            "desnudos sexuales",
            "videos sexuales"
        ]

        pregunta_normalizada = (
            pregunta.lower()
        )

        if any(
            termino in pregunta_normalizada
            for termino in terminos_no_buscar
        ):

            return {
                "encontrado": False,
                "respuesta":
                    "No puedo realizar busquedas "
                    "de contenido sexual explicito.",
                "fuentes": []
            }

        try:

            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

        except Exception as exc:

            return {
                "encontrado": False,
                "respuesta":
                    "El buscador web no esta disponible: "
                    + str(exc),
                "fuentes": []
            }

        try:

            resultados = []

            pregunta_limpia = (
                pregunta
                .replace("¿", "")
                .replace("?", "")
                .strip()
            )

            pregunta_lower = (
                pregunta_limpia.lower()
            )

            consultas = [
                pregunta_limpia
            ]

            if (
                "que es" in pregunta_lower
                or
                "qué es" in pregunta_lower
            ):
                consultas.extend([
                    pregunta_limpia,
                    "definicion " + pregunta_limpia,
                    pregunta_limpia + " definicion"
                ])

            elif (
                "quien es" in pregunta_lower
                or
                "quién es" in pregunta_lower
            ):
                consultas.extend([
                    pregunta_limpia,
                    pregunta_limpia + " biografia",
                    pregunta_limpia + " aportes"
                ])

            elif (
                "como funciona" in pregunta_lower
                or
                "cómo funciona" in pregunta_lower
            ):
                consultas.extend([
                    pregunta_limpia,
                    pregunta_limpia + " como funciona",
                    pregunta_limpia + " explicacion tecnica"
                ])

            else:
                consultas.extend([
                    "informacion sobre " + pregunta_limpia,
                    pregunta_limpia
                ])

            vistas = set()

            for consulta in consultas:

                consulta = (
                    str(consulta)
                    .strip()
                )

                if not consulta:
                    continue

                if consulta.lower() in vistas:
                    continue

                vistas.add(
                    consulta.lower()
                )

                try:

                    with DDGS() as ddgs:

                        busqueda = ddgs.text(
                            consulta,
                            max_results=max_resultados
                        )

                        for item in busqueda:

                            titulo = str(
                                item.get(
                                    "title",
                                    ""
                                )
                            ).strip()

                            cuerpo = str(
                                item.get(
                                    "body",
                                    ""
                                )
                            ).strip()

                            enlace = str(
                                item.get(
                                    "href",
                                    ""
                                )
                            ).strip()

                            if not titulo and not cuerpo:
                                continue

                            resultados.append({
                                "titulo": titulo,
                                "texto": cuerpo,
                                "url": enlace
                            })

                    if resultados:
                        break

                except Exception:
                    continue

            if not resultados:

                return {
                    "encontrado": False,
                    "respuesta":
                        "No encontre resultados suficientes.",
                    "fuentes": []
                }

            partes = []

            for resultado in resultados:

                titulo = resultado.get(
                    "titulo",
                    ""
                )

                cuerpo = resultado.get(
                    "texto",
                    ""
                )

                if cuerpo:

                    partes.append(
                        titulo
                        + ": "
                        + cuerpo
                    )

            resumen = " ".join(
                partes
            )

            # Limitar el tamano para mantener
            # controlado el contexto.
            resumen = re.sub(
                r"\\s+",
                " ",
                resumen
            ).strip()

            resumen = resumen[:5000]

            respuesta_resumida = (
                self.resumir_informacion_web_propia(
                    pregunta,
                    resultados
                )
            )

            if respuesta_resumida is None:
                respuesta_resumida = (
                    "Encontré información, "
                    "pero no pude resumirla correctamente."
                )

            return {
                "encontrado": True,
                "pregunta": pregunta,
                "respuesta": respuesta_resumida,
                "fuentes": resultados
            }

        except Exception as exc:

            return {
                "encontrado": False,
                "respuesta":
                    "No pude investigar en Internet: "
                    + str(exc),
                "fuentes": []
            }



    def normalizar_conocimiento_web_propio(
        self,
        pregunta,
        respuesta,
        fuentes=None
    ):
        """
        Convierte un conocimiento simple en una
        estructura organizada.
        """

        pregunta = str(
            pregunta
        ).strip()

        respuesta = str(
            respuesta
        ).strip()

        fuentes = fuentes or []

        concepto = (
            pregunta
            .replace("¿", "")
            .replace("?", "")
            .strip()
        )

        fecha = datetime.datetime.now().isoformat(
            timespec="seconds"
        )

        confianza = 0.75

        if len(fuentes) >= 3:
            confianza = 0.85

        if len(fuentes) >= 5:
            confianza = 0.90

        return {
            "concepto": concepto,
            "pregunta": pregunta,
            "respuesta": respuesta,
            "fuentes": fuentes,
            "fecha_aprendizaje": fecha,
            "confianza": confianza
        }


    def cargar_conocimiento_web_propio(
        self
    ):
        """
        Carga conocimiento y migra automaticamente
        entradas antiguas al formato estructurado.
        """

        import json
        import datetime

        ruta = (
            Path(__file__).resolve().parent
            / "conocimiento_web_propio.json"
        )

        if not ruta.exists():
            return {}

        try:

            datos = json.loads(
                ruta.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:
            return {}

        if not isinstance(
            datos,
            dict
        ):
            return {}

        modificado = False

        for clave, entrada in list(
            datos.items()
        ):

            if not isinstance(
                entrada,
                dict
            ):
                continue

            # ------------------------------------------------
            # Entrada antigua:
            # {
            #   "respuesta": "...",
            #   "fuentes": [...]
            # }
            # ------------------------------------------------

            if (
                "concepto" not in entrada
                or
                "confianza" not in entrada
                or
                "fecha_aprendizaje" not in entrada
            ):

                pregunta = entrada.get(
                    "pregunta",
                    clave
                )

                respuesta = entrada.get(
                    "respuesta",
                    ""
                )

                fuentes = entrada.get(
                    "fuentes",
                    []
                )

                confianza = 0.75

                if isinstance(
                    fuentes,
                    list
                ):

                    if len(fuentes) >= 3:
                        confianza = 0.85

                    if len(fuentes) >= 5:
                        confianza = 0.90

                entrada["concepto"] = (
                    str(
                        pregunta
                    )
                    .replace(
                        "¿",
                        ""
                    )
                    .replace(
                        "?",
                        ""
                    )
                    .strip()
                )

                entrada["pregunta"] = (
                    str(
                        pregunta
                    ).strip()
                )

                entrada["respuesta"] = (
                    str(
                        respuesta
                    ).strip()
                )

                entrada["fuentes"] = (
                    fuentes
                    if isinstance(
                        fuentes,
                        list
                    )
                    else []
                )

                entrada["fecha_aprendizaje"] = (
                    datetime.datetime.now().isoformat(
                        timespec="seconds"
                    )
                )

                entrada["confianza"] = confianza

                modificado = True

            datos[clave] = entrada

        # Guardar migración.
        if modificado:

            try:

                ruta.write_text(
                    json.dumps(
                        datos,
                        ensure_ascii=False,
                        indent=2
                    ),
                    encoding="utf-8"
                )

            except Exception:
                pass

        return datos



    def guardar_conocimiento_web_propio(
        self,
        pregunta,
        respuesta,
        fuentes=None
    ):
        """
        Guarda conocimiento estructurado.
        """

        pregunta = str(
            pregunta
        ).strip()

        respuesta = str(
            respuesta
        ).strip()

        if not pregunta or not respuesta:
            return False

        ruta = (
            Path(__file__).resolve().parent
            / "conocimiento_web_propio.json"
        )

        conocimiento = (
            self.cargar_conocimiento_web_propio()
        )

        clave = (
            pregunta
            .lower()
            .replace("¿", "")
            .replace("?", "")
            .strip()
        )

        entrada = (
            self.normalizar_conocimiento_web_propio(
                pregunta,
                respuesta,
                fuentes
            )
        )

        conocimiento[clave] = entrada

        try:

            ruta.write_text(
                json.dumps(
                    conocimiento,
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )

            return True

        except Exception:
            return False



    def buscar_conocimiento_web_propio(
        self,
        pregunta
    ):
        """
        Recupera conocimiento estructurado.
        """

        pregunta = str(
            pregunta
        ).strip()

        clave = (
            pregunta
            .lower()
            .replace("¿", "")
            .replace("?", "")
            .strip()
        )

        conocimiento = (
            self.cargar_conocimiento_web_propio()
        )

        entrada = conocimiento.get(
            clave
        )

        if not isinstance(
            entrada,
            dict
        ):
            return None

        respuesta = entrada.get(
            "respuesta"
        )

        if not respuesta:
            return None

        return entrada



    def responder_consulta_propia(
        self,
        texto
    ):
        """
        Primer motor de conocimiento propio.
        Responde consultas concretas sin Ollama.
        """

        conocimiento_aprendido = (
            self.buscar_conocimiento_web_propio(
                texto
            )
        )

        if conocimiento_aprendido:

            return conocimiento_aprendido.get(
                "respuesta"
            )

        import unicodedata

        original = str(
            texto
        ).strip()

        normalizado = unicodedata.normalize(
            "NFD",
            original.lower()
        )

        normalizado = "".join(
            caracter
            for caracter in normalizado
            if unicodedata.category(
                caracter
            ) != "Mn"
        )

        respuestas = [

            (
                [
                    "que es python",
                    "que es python?",
                    "python que es"
                ],
                (
                    "Python es un lenguaje de "
                    "programación de alto nivel, "
                    "usado para crear aplicaciones, "
                    "automatizaciones, herramientas "
                    "y sistemas de inteligencia artificial."
                )
            ),

            (
                [
                    "que es programacion",
                    "que es programacion?"
                ],
                (
                    "La programación consiste en "
                    "crear instrucciones que una "
                    "computadora puede ejecutar para "
                    "resolver problemas o realizar tareas."
                )
            ),

            (
                [
                    "que es jarvis",
                    "que es jarvis?"
                ],
                (
                    "JARVIS es el asistente local "
                    "que estamos construyendo para "
                    "que pueda comprender, recordar, "
                    "razonar y controlar funciones "
                    "de tu PC."
                )
            ),

            (
                [
                    "que es minecraft",
                    "que es minecraft?"
                ],
                (
                    "Minecraft es un videojuego de "
                    "construcción y exploración basado "
                    "en un mundo de bloques, donde "
                    "puedes explorar, recolectar recursos "
                    "y crear estructuras."
                )
            ),


            (
                [
                    "que es roblox",
                    "que es roblox?"
                ],
                (
                    "Roblox es una plataforma en línea "
                    "donde puedes jugar y crear experiencias "
                    "interactivas desarrolladas por usuarios."
                )
            ),

            (
                [
                    "que es una computadora",
                    "que es una computadora?",
                    "que es computadora",
                    "que es computadora?"
                ],
                (
                    "Una computadora es una máquina electrónica "
                    "que procesa datos y ejecuta instrucciones "
                    "para realizar distintas tareas."
                )
            )
        ]

        for patrones, respuesta in respuestas:

            for patron in patrones:

                if patron in normalizado:

                    return respuesta

        return None


    def pensar_propio(
        self,
        objetivo,
        error_anterior=None,
        plan_anterior=None
    ):
        """
        Motor de pensamiento propio.

        Prioridad:
        1. Respuestas conversacionales directas.
        2. Intenciones accionables.
        3. Conversación contextual.
        """

        texto = str(
            objetivo
        ).strip()

        if not texto:

            return {
                "tipo": "conversacion",
                "respuesta":
                    "No recibí ningún mensaje."
            }

        # ----------------------------------------------------
        # 1. RESPUESTAS CONVERSACIONALES DIRECTAS
        # ----------------------------------------------------

        categoria = (
            self.clasificar_mensaje_conversacional(
                texto
            )
        )

        categorias_directas = {
            "vacio",
            "saludo",
            "despedida",
            "agradecimiento",
            "identidad",
            "capacidades",
            "confirmacion",
            "hora"
        }

        if categoria in categorias_directas:

            respuesta = (
                self.generar_respuesta_conversacional(
                    texto
                )
            )

            if respuesta is not None:

                return {
                    "tipo": "conversacion",
                    "respuesta": respuesta
                }

        # ----------------------------------------------------
        # 2. CONOCIMIENTO PROPIO
        # ----------------------------------------------------

        respuesta_propia = (
            self.responder_consulta_propia(
                texto
            )
        )

        if respuesta_propia is not None:

            return {
                "tipo": "conversacion",
                "respuesta": respuesta_propia
            }

        # ----------------------------------------------------
        # 3. INTENCION REAL
        # ----------------------------------------------------

        intencion = (
            self.interpretar_intencion(
                texto
            )
        )

        intenciones_accionables = {
            "abrir",
            "listar_procesos",
            "investigar",
            "desinstalar"
        }

        if intencion in intenciones_accionables:

            try:

                plan = self.decidir(
                    texto
                )

            except Exception as exc:

                return {
                    "tipo": "error",
                    "mensaje":
                        "No pude generar un plan: "
                        + str(exc)
                }

            if not getattr(
                plan,
                "valido",
                False
            ):

                return {
                    "tipo": "error",
                    "mensaje":
                        "No pude preparar un plan "
                        "válido para ese objetivo."
                }

            acciones = []

            for accion in getattr(
                plan,
                "acciones",
                []
            ):

                acciones.append({
                    "herramienta":
                        getattr(
                            accion,
                            "nombre",
                            ""
                        ),

                    "argumentos":
                        getattr(
                            accion,
                            "argumentos",
                            {}
                        ),

                    "requiere_confirmacion":
                        getattr(
                            accion,
                            "requiere_confirmacion",
                            False
                        )
                })

            return {
                "tipo": "plan",
                "objetivo": texto,
                "acciones": acciones,
                "respuesta_final":
                    "Plan preparado por el cerebro propio."
            }

        # ----------------------------------------------------
        # 4. CONSULTA / CONVERSACION CONTEXTUAL
        # ----------------------------------------------------

        respuesta = (
            self.generar_respuesta_conversacional(
                texto
            )
        )

        if respuesta is not None:

            return {
                "tipo": "conversacion",
                "respuesta": respuesta
            }

        # ----------------------------------------------------
        # 5. FALLBACK DE CONOCIMIENTO
        # ----------------------------------------------------

        intencion_consulta = (
            intencion == "consultar"
        )

        if intencion_consulta:

            investigacion = (
                self.investigar_web_propia(
                    texto
                )
            )

            if investigacion.get(
                "encontrado",
                False
            ):

                respuesta_web = (
                    investigacion.get(
                        "respuesta",
                        ""
                    )
                )

                fuentes_web = (
                    investigacion.get(
                        "fuentes",
                        []
                    )
                )

                self.guardar_conocimiento_web_propio(
                    texto,
                    respuesta_web,
                    fuentes_web
                )

                return {
                    "tipo":
                        "investigacion_web",

                    "pregunta":
                        texto,

                    "respuesta":
                        respuesta_web,

                    "fuentes":
                        fuentes_web
                }

            return {
                "tipo":
                    "consulta",

                "pregunta":
                    texto,

                "respuesta":
                    investigacion.get(
                        "respuesta"
                    )
            }

        # ----------------------------------------------------
        # 6. FALLBACK
        # ----------------------------------------------------

        return {
            "tipo": "error",
            "mensaje":
                "Todavía no tengo una respuesta propia "
                "para ese objetivo."
        }



    def generar_respuesta_conversacional(
        self,
        texto
    ):
        """Genera respuestas conversacionales básicas sin Ollama."""

        contexto = (
            self.preparar_respuesta_contextual(
                texto
            )
        )

        categoria = (
            self.clasificar_mensaje_conversacional(
                texto
            )
        )

        respuestas = {

            "hora":
                __import__("datetime").datetime.now().strftime(
                    "Son las %H:%M."
                ),

            "vacio":
                "No recibí ningún mensaje.",

            "saludo":
                "Hola. ¿En qué puedo ayudarte?",

            "despedida":
                "Hasta luego.",

            "agradecimiento":
                "De nada.",

            "identidad":
                "Soy JARVIS, tu asistente local.",

            "capacidades":
                (
                    "Puedo ayudarte a analizar problemas, "
                    "usar herramientas y controlar funciones "
                    "de tu sistema."
                ),

            "confirmacion":
                "Perfecto.",

        }

        respuesta = respuestas.get(
            categoria
        )

        if respuesta is not None:
            return respuesta

        if contexto.get(
            "usar_contexto",
            False
        ):

            tema = contexto.get(
                "tema"
            )

            if tema:

                return (
                    "Entiendo. "
                    "Seguimos con el tema de "
                    + str(tema)
                    + "."
                )

        return None


    def interpretar_intencion(
        self,
        texto: str
    ) -> str:

        import re

        t = str(
            texto
        ).lower().strip()

        # ====================================================
        # PROCESOS
        # ====================================================

        señales_procesos = [
            "muestra mis procesos",
            "mostrar mis procesos",
            "lista mis procesos",
            "listar mis procesos",
            "muestra los procesos",
            "mostrar los procesos",
            "lista los procesos",
            "listar los procesos",
            "que procesos estan abiertos",
            "qué procesos están abiertos",
            "que procesos tengo abiertos",
            "qué procesos tengo abiertos"
        ]

        if any(
            señal in t
            for señal in señales_procesos
        ):
            return "listar_procesos"

        # ====================================================
        # DESINSTALAR / ELIMINAR
        # ====================================================

        patrones_desinstalar_directos = [
            r"^\s*desinstala(?:r)?\b",
            r"^\s*elimina(?:r)?\b",
            r"^\s*borra(?:r)?\b",
            r"^\s*saca(?:r)?\b"
        ]

        if any(
            re.match(
                patron,
                t
            )
            for patron in patrones_desinstalar_directos
        ):
            return "desinstalar"

        patrones_desinstalar_peticion = [
            "quiero desinstalar",
            "quiero desinstalar el",
            "quiero desinstalar la",
            "quiero eliminar",
            "quiero borrar",
            "quiero sacar",
            "puedes desinstalar",
            "podés desinstalar",
            "podes desinstalar",
            "puedes eliminar",
            "podés eliminar",
            "podes eliminar",
            "puedes borrar",
            "podés borrar",
            "podes borrar",
            "puedes sacar",
            "podés sacar",
            "podes sacar"
        ]

        if any(
            frase in t
            for frase in patrones_desinstalar_peticion
        ):
            return "desinstalar"

        # ====================================================
        # INVESTIGAR
        # ====================================================

        señales_investigar = [
            "investiga",
            "investigar",
            "averigua",
            "averiguar",
            "diagnostica",
            "diagnosticar",
            "analiza",
            "analizar",
            "revisa",
            "revisar",
            "comprueba",
            "comprobar",
            "verifica",
            "verificar",
            "quiero saber",
            "necesito saber",
            "qué está pasando",
            "que esta pasando",
            "qué podría estar pasando",
            "que podria estar pasando"
        ]

        if any(
            señal in t
            for señal in señales_investigar
        ):
            return "investigar"

        # ====================================================
        # ABRIR
        # Solo al principio de la orden.
        # ====================================================

        patrones_abrir = [
            r"^\s*abrí\b",
            r"^\s*abrir\b",
            r"^\s*abre\b",
            r"^\s*quiero abrir\b",
            r"^\s*puedes abrir\b",
            r"^\s*podés abrir\b",
            r"^\s*podes abrir\b",
            r"^\s*ejecuta\b",
            r"^\s*ejecutar\b",
            r"^\s*inicia\b",
            r"^\s*iniciar\b",
            r"^\s*lanza\b",
            r"^\s*lanzar\b",
            r"^\s*arranca\b",
            r"^\s*arrancar\b"
        ]

        if any(
            re.match(
                patron,
                t
            )
            for patron in patrones_abrir
        ):
            return "abrir"

        # ====================================================
        # CONSULTAR
        # ====================================================

        señales_consulta = [
            "que es",
            "qué es",
            "quien es",
            "quién es",
            "cuanto",
            "cuánto",
            "como funciona",
            "cómo funciona",
            "como se hace",
            "cómo se hace",
            "para que sirve",
            "para qué sirve",
            "dime",
            "decime",
            "explica",
            "explicame",
            "explícame",
            "contame",
            "cuéntame"
        ]

        if any(
            palabra in t
            for palabra in señales_consulta
        ):
            return "consultar"

        # ====================================================
        # SISTEMA / PROBLEMAS
        # ====================================================

        señales_sistema = [
            "pc",
            "computadora",
            "ordenador",
            "máquina",
            "sistema",
            "procesador",
            "cpu",
            "ram",
            "memoria",
            "recursos",
            "aplicación",
            "aplicacion",
            "programa",
            "disco",
            "almacenamiento",
            "espacio",
            "archivo",
            "archivos",
            "red",
            "internet",
            "conexión",
            "conexion",
            "explorer",
            "windows"
        ]

        señales_problema = [
            "lenta",
            "lento",
            "lleno",
            "llena",
            "casi lleno",
            "casi llena",
            "poco espacio",
            "sin espacio",
            "arrastr",
            "tard",
            "calient",
            "sobrecalent",
            "rar",
            "mal",
            "fall",
            "problema",
            "error",
            "congela",
            "congel",
            "no responde",
            "deja de responder",
            "funciona mal",
            "se cierra",
            "no abre",
            "no se puede abrir",
            "demasiad",
            "consumiendo",
            "consumo alto"
        ]

        if (
            any(
                palabra in t
                for palabra in señales_sistema
            )
            and
            any(
                palabra in t
                for palabra in señales_problema
            )
        ):
            return "investigar"

        # ====================================================
        # ALMACENAMIENTO
        # ====================================================

        señales_almacenamiento = [
            "mi disco está lleno",
            "mi disco esta lleno",
            "mi disco está casi lleno",
            "mi disco esta casi lleno",
            "tengo poco espacio",
            "me queda poco espacio",
            "quiero liberar espacio",
            "liberar espacio",
            "liberar almacenamiento",
            "almacenamiento lleno",
            "almacenamiento está lleno",
            "almacenamiento esta lleno"
        ]

        if any(
            frase in t
            for frase in señales_almacenamiento
        ):
            return "investigar"

        return "conversar"






    def analizar(
        self,
        texto
    ):

        orden = str(
            texto
        )

        orden_normalizada = (
            orden
            .lower()
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )

        self.ultima_orden = orden

        restricciones = []


        reglas = {

            "no_cerrar_procesos": [
                "no cierres procesos",
                "no cerrar procesos",
                "no cierres proceso",
                "no cerrar proceso"
            ],

            "no_bloquear_procesos": [
                "no bloquees procesos",
                "no bloquear procesos",
                "no bloquees conexiones",
                "no bloquear conexiones",
                "no bloquees el proceso",
                "no bloquear el proceso"
            ],

            "no_eliminar_procesos": [
                "no elimines procesos",
                "no eliminar procesos",
                "no elimines proceso",
                "no eliminar proceso"
            ],

            "no_eliminar_archivos": [
                "no elimines archivos",
                "no eliminar archivos",
                "no elimines nada",
                "no eliminar nada"
            ],

            "no_formatear_disco": [
                "no formatees el disco",
                "no formatear el disco",
                "no formatees discos",
                "no formatear discos"
            ],

            "no_cambiar_permisos": [
                "no cambies permisos",
                "no cambiar permisos",
                "no modifiques permisos",
                "no modificar permisos"
            ],

            "no_desactivar_inicio": [
                "no desactives el inicio",
                "no desactivar el inicio",
                "no desactives el inicio automatico",
                "no desactivar el inicio automatico"
            ],

            "no_deshabilitar_servicios": [
                "no deshabilites servicios",
                "no deshabilitar servicios",
                "no deshabilites el servicio",
                "no deshabilitar el servicio"
            ],

            "no_eliminar_tareas": [
                "no elimines tareas programadas",
                "no eliminar tareas programadas",
                "no deshabilites tareas programadas",
                "no deshabilitar tareas programadas"
            ],

            "no_desactivar_proteccion_termica": [
                "no desactives protecciones termicas",
                "no desactivar protecciones termicas",
                "no desactives la proteccion termica",
                "no desactivar la proteccion termica"
            ],

            "no_cambiar_energia": [
                "no cambies configuraciones de energia",
                "no cambiar configuraciones de energia",
                "no cambies configuracion de energia",
                "no cambiar configuracion de energia"
            ],

            "no_reiniciar": [
                "no reinicies el equipo",
                "no reiniciar el equipo",
                "no reinicies nada",
                "no reiniciar nada",
                "no reinicies"
            ],

            "no_desinstalar_actualizaciones": [
                "no desinstales actualizaciones",
                "no desinstalar actualizaciones",
                "no desinstales la actualizacion",
                "no desinstalar la actualizacion"
            ],

            "no_administrador": [
                "no ejecutes nada como administrador",
                "no ejecutar nada como administrador",
                "no ejecutes como administrador",
                "no ejecutar como administrador"
            ],

            "no_abrir_fuente": [
                "no abras la fuente",
                "no abrir la fuente",
                "no abras fuentes",
                "no abrir fuentes"
            ],

            "no_reparaciones_destructivas": [
                "no ejecutes herramientas de reparacion destructivas",
                "no ejecutar herramientas de reparacion destructivas",
                "no ejecutes reparaciones destructivas",
                "no ejecutar reparaciones destructivas"
            ]
        }


        for nombre, frases in reglas.items():

            if any(
                frase in orden_normalizada
                for frase in frases
            ):

                restricciones.append(
                    nombre
                )


        self.restricciones_actuales = set(
            restricciones
        )


        intencion = self.interpretar_intencion(
            orden
        )

        objetivo = Objetivo(
            texto=orden,
            intencion=intencion,
            solo_observar=True,
            requisitos=[],
            riesgos=[]
        )

        self.objetivo_actual = objetivo

        return objetivo

    def generar_plan_basico(
        self,
        objetivo: Objetivo
    ) -> Plan:

        plan = Plan(
            objetivo=objetivo.texto
        )

        texto = objetivo.texto.lower()

        # ------------------------------------
        # OPERA GX
        # ------------------------------------

        if (
            "opera gx" in texto
            and objetivo.intencion
            == "abrir"
        ):

            plan.acciones.append(
                Accion(
                    nombre="abrir_app",
                    argumentos={
                        "nombre": "Opera GX"
                    },
                    motivo=(
                        "Abrir la aplicación "
                        "solicitada."
                    ),
                )
            )

            plan.verificacion = (
                "Comprobar que Opera GX "
                "se encuentre abierto."
            )

            plan.valido = True

            return plan

        # ------------------------------------
        # HARDWARE
        # ------------------------------------

        if any(
            palabra in texto
            for palabra in [
                "ram",
                "procesador",
                "cpu",
                "gpu",
                "hardware",
            ]
        ):

            plan.acciones.append(
                Accion(
                    nombre="informacion_sistema",
                    argumentos={},
                    motivo=(
                        "Consultar la información "
                        "real del PC."
                    ),
                )
            )

            plan.verificacion = (
                "Comprobar que se recibieron "
                "datos del sistema."
            )

            plan.valido = True

            return plan

        # ------------------------------------
        # VENTANAS
        # ------------------------------------

        if (
            "ventana" in texto
            and any(
                palabra in texto
                for palabra in [
                    "muestra",
                    "mostrar",
                    "lista",
                    "listar",
                ]
            )
        ):

            plan.acciones.append(
                Accion(
                    nombre="listar_ventanas",
                    argumentos={},
                    motivo=(
                        "Consultar las "
                        "ventanas abiertas."
                    ),
                )
            )

            plan.verificacion = (
                "Comprobar que se recibió "
                "una lista."
            )

            plan.valido = True

            return plan

        # ------------------------------------
        # DIAGNOSTICO DE PC
        # ------------------------------------

        if any(
            palabra in texto
            for palabra in [
                "pc esta lenta",
                "pc está lenta",
                "computadora esta lenta",
                "computadora está lenta",
                "por que mi pc",
                "por qué mi pc",
                "por que mi computadora",
                "por qué mi computadora",
                "diagnostica mi pc",
                "analiza mi pc",
                "investiga mi pc",
            ]
        ):

            plan.acciones.extend([
                Accion(
                    nombre="informacion_sistema",
                    argumentos={},
                    motivo="Comprobar el estado general del PC.",
                ),

                Accion(
                    nombre="listar_procesos",
                    argumentos={
                        "limite": 30
                    },
                    motivo="Revisar los procesos activos.",
                ),

                Accion(
                    nombre="listar_ventanas",
                    argumentos={},
                    motivo="Comprobar las ventanas abiertas.",
                ),
            ])

            plan.verificacion = (
                "Comparar los resultados para buscar "
                "posibles causas."
            )

            plan.alternativa = (
                "Si no aparece una causa clara, "
                "revisar almacenamiento y programas de inicio."
            )

            plan.valido = True

            return plan


        # ------------------------------------
        # PROCESOS
        # ------------------------------------

        if (
            "proceso" in texto
            and any(
                palabra in texto
                for palabra in [
                    "muestra",
                    "mostrar",
                    "lista",
                    "listar",
                ]
            )
        ):

            plan.acciones.append(
                Accion(
                    nombre="listar_procesos",
                    argumentos={
                        "limite": 30
                    },
                    motivo=(
                        "Consultar procesos "
                        "activos."
                    ),
                )
            )

            plan.verificacion = (
                "Comprobar que se recibió "
                "una lista."
            )

            plan.valido = True

            return plan

        return plan

    # --------------------------------------------------------
    # REFLEXION
    # --------------------------------------------------------

    def revisar_plan(
        self,
        plan: Plan
    ) -> bool:

        if not plan.acciones:
            return False

        for accion in plan.acciones:

            if not accion.nombre:
                return False

        if not plan.verificacion:
            return False

        return True

    # --------------------------------------------------------
    # USAR LO APRENDIDO
    # --------------------------------------------------------

    def decidir_con_memoria(
        self,
        texto: str
    ):

        experiencia = self.usar_experiencia(
            texto
        )

        if experiencia:

            accion = experiencia.get(
                "accion"
            )

            if experiencia.get(
                "funciono",
                False
            ):

                return {
                    "tipo": "memoria",
                    "accion": accion,
                    "motivo": (
                        "Usar una solución que "
                        "ya funcionó."
                    ),
                }

        return None


    # --------------------------------------------------------
    # DECIDIR
    # --------------------------------------------------------

    def decidir(
        self,
        texto: str
    ) -> Plan:

        objetivo = self.analizar(
            texto
        )

        self.estado = (
            Estado.PLANIFICANDO
        )

        plan = self.generar_plan_basico(
            objetivo
        )

        plan.valido = (
            self.revisar_plan(
                plan
            )
        )

        self.plan_actual = plan

        return plan

    # --------------------------------------------------------
    # ANALIZAR RESULTADOS
    # --------------------------------------------------------

    def analizar_resultados(
        self,
        resultados: list[dict]
    ) -> dict:
        """
        Analiza resultados reales de herramientas
        y determina problemas o siguientes pasos.
        """

        analisis = {
            "problemas": [],
            "causas_posibles": [],
            "siguiente_paso": None,
        }

        for resultado in resultados:

            datos = resultado.get(
                "datos"
            )

            herramienta = resultado.get(
                "herramienta"
            )

            valor = resultado.get(
                "resultado"
            )

            # ====================================================
            # ANALISIS DE PROCESOS
            # ====================================================

            if (
                herramienta == "listar_procesos"
                or
                herramienta == "procesos"
            ):

                procesos = valor

                if not isinstance(
                    procesos,
                    list
                ):
                    continue

                procesos_validos = []

                for proceso in procesos:

                    if not isinstance(
                        proceso,
                        dict
                    ):
                        continue

                    nombre = proceso.get(
                        "nombre"
                    )

                    ram = proceso.get(
                        "ram_mb"
                    )

                    if not nombre:
                        continue

                    if ram is None:
                        ram = 0

                    try:
                        ram = float(
                            ram
                        )
                    except Exception:
                        ram = 0

                    procesos_validos.append(
                        {
                            "nombre":
                                str(nombre),
                            "ram_mb":
                                ram
                        }
                    )

                # --------------------------------------------
                # PROCESOS CONSUMIENDO MUCHA RAM
                # --------------------------------------------

                for proceso in procesos_validos:

                    if (
                        proceso["ram_mb"]
                        >= 1000
                    ):

                        analisis[
                            "problemas"
                        ].append(
                            (
                                f"{proceso['nombre']} "
                                f"está usando "
                                f"{proceso['ram_mb']:.0f} MB de RAM."
                            )
                        )

                        analisis[
                            "causas_posibles"
                        ].append(
                            (
                                f"{proceso['nombre']} "
                                "puede estar consumiendo "
                                "una cantidad importante de RAM."
                            )
                        )

                # --------------------------------------------
                # BUSCAR MAYORES CONSUMIDORES
                # --------------------------------------------

                procesos_ordenados = sorted(
                    procesos_validos,
                    key=lambda p: p["ram_mb"],
                    reverse=True
                )

                if procesos_ordenados:

                    mayor = (
                        procesos_ordenados[0]
                    )

                    if (
                        mayor["ram_mb"]
                        >= 500
                    ):

                        analisis[
                            "siguiente_paso"
                        ] = (
                            "Revisar los procesos que "
                            "más RAM están consumiendo."
                        )

            # ====================================================
            # ANALISIS DE ESTADO DEL SISTEMA
            # ====================================================

            if (
                isinstance(
                    datos,
                    dict
                )
            ):

                cpu = datos.get(
                    "cpu_porcentaje"
                )

                ram = datos.get(
                    "ram_disponible_gb"
                )

                if (
                    cpu is not None
                    and cpu >= 90
                ):

                    analisis[
                        "problemas"
                    ].append(
                        "Uso de CPU muy alto."
                    )

                    analisis[
                        "causas_posibles"
                    ].append(
                        "Un proceso puede estar consumiendo demasiado CPU."
                    )

                if (
                    ram is not None
                    and ram <= 2
                ):

                    analisis[
                        "problemas"
                    ].append(
                        "Hay poca RAM disponible."
                    )

                    analisis[
                        "causas_posibles"
                    ].append(
                        "Puede haber demasiados programas abiertos."
                    )

        # ========================================================
        # DETERMINAR SIGUIENTE PASO
        # ========================================================

        if not analisis[
            "siguiente_paso"
        ]:

            if analisis[
                "problemas"
            ]:

                analisis[
                    "siguiente_paso"
                ] = (
                    "Revisar los problemas detectados."
                )

            else:

                analisis[
                    "siguiente_paso"
                ] = (
                    "No se detectaron problemas "
                    "evidentes con estos datos."
                )

        # Evitar duplicados.
        analisis[
            "problemas"
        ] = list(
            dict.fromkeys(
                analisis["problemas"]
            )
        )

        analisis[
            "causas_posibles"
        ] = list(
            dict.fromkeys(
                analisis["causas_posibles"]
            )
        )

        return analisis



    def obtener_estado_real(self) -> dict:

        try:

            import control_pc_avanzado

            sistema = (
                control_pc_avanzado
                .informacion_sistema()
            )

            procesos = (
                control_pc_avanzado
                .listar_procesos(
                    None,
                    30
                )
            )

            ventanas = (
                control_pc_avanzado
                .listar_ventanas()
            )

            return {
                "sistema": sistema,
                "procesos": procesos,
                "ventanas": ventanas,
            }

        except Exception as exc:

            return {
                "error": str(exc)
            }


    # --------------------------------------------------------
    # DETECTAR PROBLEMAS INTERMITENTES
    # --------------------------------------------------------

    def detectar_intermitencia(
        self,
        mediciones: list
    ) -> dict:

        problemas = []

        if not mediciones:

            return {
                "intermitente":
                    False,

                "problemas":
                    [],

                "decision":
                    "sin_datos"
            }

        # ====================================================
        # PERIFERICOS
        # ====================================================

        nombres_perifericos = set()

        for medicion in mediciones:

            for periferico in medicion.get(
                "perifericos",
                []
            ):

                nombres_perifericos.add(
                    periferico.get(
                        "nombre"
                    )
                )

        for nombre in nombres_perifericos:

            estados = []

            for medicion in mediciones:

                for periferico in medicion.get(
                    "perifericos",
                    []
                ):

                    if (
                        periferico.get("nombre")
                        == nombre
                    ):

                        estados.append(
                            periferico.get(
                                "responde"
                            )
                        )

            estados_validos = [
                estado
                for estado in estados
                if estado is not None
            ]

            if len(
                set(
                    estados_validos
                )
            ) > 1:

                problemas.append(
                    f"El periférico {nombre} deja de responder y vuelve a funcionar."
                )

        # ====================================================
        # PROGRAMAS
        # ====================================================

        estados_programa = []

        for medicion in mediciones:

            if "programa_responde" in medicion:

                estados_programa.append(
                    medicion.get(
                        "programa_responde"
                    )
                )

        if (
            len(
                set(
                    estados_programa
                )
            ) > 1
        ):

            problemas.append(
                "El programa deja de responder y vuelve a funcionar."
            )

        # ====================================================
        # GENERAR RESULTADO
        # ====================================================

        if problemas:

            return {
                "intermitente":
                    True,

                "problemas":
                    problemas,

                "decision":
                    "seguir_observando"
            }

        return {
            "intermitente":
                False,

            "problemas":
                [],

            "decision":
                "sin_patron"
        }

    def priorizar_problemas(
        self,
        problemas: list[str]
    ) -> list[dict]:

        prioridades = []

        vistos = set()

        for problema in problemas:

            if problema in vistos:
                continue

            vistos.add(
                problema
            )

            texto = problema.lower()

            if "temperatura" in texto:

                prioridad = "critica"

            elif "cpu" in texto:

                prioridad = "alta"

            elif "ram" in texto:

                prioridad = "alta"

            elif "disco" in texto:

                prioridad = "media"

            else:

                prioridad = "baja"

            prioridades.append({
                "problema":
                    problema,

                "prioridad":
                    prioridad
            })

        orden = {
            "critica": 1,
            "alta": 2,
            "media": 3,
            "baja": 4
        }

        prioridades.sort(
            key=lambda x:
                orden.get(
                    x["prioridad"],
                    99
                )
        )

        return prioridades





    def buscar_causas(
        self,
        estado: dict
    ) -> dict:

        causas = []

        sistema = estado.get(
            "sistema",
            {}
        )

        cpu_total = sistema.get(
            "cpu_porcentaje"
        )

        ram = sistema.get(
            "ram_disponible_gb"
        )

        if (
            cpu_total is not None
            and
            cpu_total >= 80
        ):

            causas.append({

                "causa":
                    (
                        f"El sistema presenta un uso de CPU "
                        f"elevado ({cpu_total}%)."
                    ),

                "tipo":
                    "consumo_cpu",

                "confianza":
                    "alta"
            })

        if (
            ram is not None
            and
            ram <= 4
        ):

            causas.append({

                "causa":
                    (
                        f"La memoria RAM disponible es baja "
                        f"({ram} GB)."
                    ),

                "tipo":
                    "consumo_ram",

                "confianza":
                    "alta"
            })

        procesos = estado.get(
            "procesos",
            []
        )

        clasificacion = {}

        for proceso in procesos:

            nombre = proceso.get(
                "nombre",
                "Proceso desconocido"
            )

            ruta = str(
                proceso.get(
                    "ruta",
                    ""
                )
            ).lower().replace(
                chr(92),
                "/"
            )

            firma = str(
                proceso.get(
                    "firma_digital",
                    ""
                )
            ).lower()

            editor = str(
                proceso.get(
                    "editor",
                    ""
                )
            ).strip()

            hash_conocido = proceso.get(
                "hash_conocido"
            )

            aplicacion = proceso.get(
                "aplicacion_relacionada"
            )

            inicio_coherente = proceso.get(
                "inicio_automatico_coherente"
            )

            conexiones = proceso.get(
                "conexiones_red",
                []
            )

            cpu_proceso = proceso.get(
                "cpu_porcentaje",
                0
            )

            ram_proceso = proceso.get(
                "ram_mb",
                0
            )

            señales_legitimas = []
            señales_sospechosas = []

            if (
                "program files"
                in ruta
            ):

                señales_legitimas.append(
                    "ruta en Program Files"
                )

            if firma in {
                "valida",
                "valid"
            }:

                señales_legitimas.append(
                    "firma digital válida"
                )

            if editor:

                señales_legitimas.append(
                    "editor conocido"
                )

            if hash_conocido is True:

                señales_legitimas.append(
                    "hash conocido"
                )

            if aplicacion:

                señales_legitimas.append(
                    "aplicación relacionada"
                )

            if inicio_coherente is True:

                señales_legitimas.append(
                    "inicio automático coherente"
                )

            dominio_conocido = False
            dominio_desconocido = False

            for conexion in conexiones:

                if conexion.get(
                    "conocido"
                ) is True:

                    dominio_conocido = True

                if conexion.get(
                    "conocido"
                ) is False:

                    dominio_desconocido = True

            if dominio_conocido:

                señales_legitimas.append(
                    "dominio de red conocido"
                )

            if "/temp/" in ruta:

                señales_sospechosas.append(
                    "ejecutable en Temp"
                )

            if firma in {
                "invalida",
                "invalid",
                "no valido",
                "no válida",
                "no firmado"
            }:

                señales_sospechosas.append(
                    "firma digital no válida"
                )

            if hash_conocido is False:

                señales_sospechosas.append(
                    "hash desconocido"
                )

            if not aplicacion:

                señales_sospechosas.append(
                    "sin aplicación relacionada"
                )

            if inicio_coherente is False:

                señales_sospechosas.append(
                    "inicio automático incoherente"
                )

            if dominio_desconocido:

                señales_sospechosas.append(
                    "dominio de red desconocido"
                )

            # =================================================
            # CONSUMO
            # =================================================

            if cpu_proceso >= 50:

                causas.append({

                    "causa":
                        (
                            f"{nombre} consume "
                            f"{cpu_proceso}% de CPU."
                        ),

                    "proceso":
                        nombre,

                    "tipo":
                        "consumo_proceso",

                    "confianza":
                        "alta"
                })

            if ram_proceso >= 1500:

                causas.append({

                    "causa":
                        (
                            f"{nombre} utiliza "
                            f"{ram_proceso} MB de RAM."
                        ),

                    "proceso":
                        nombre,

                    "tipo":
                        "memoria_proceso",

                    "confianza":
                        "alta"
                })

            # =================================================
            # LEGITIMIDAD
            # =================================================

            if (
                len(señales_legitimas) >= 4
                and
                not señales_sospechosas
            ):

                clasificacion[
                    nombre
                ] = {

                    "resultado":
                        "probablemente_legitimo",

                    "evidencia":
                        señales_legitimas,

                    "no_cerrar_automaticamente":
                        True
                }

                causas.append({

                    "causa":
                        (
                            f"{nombre} presenta evidencia "
                            "consistente con un proceso legítimo."
                        ),

                    "proceso":
                        nombre,

                    "tipo":
                        "proceso_legitimo",

                    "confianza":
                        "alta"
                })

            # =================================================
            # SOSPECHOSO
            # =================================================

            elif len(
                señales_sospechosas
            ) >= 3:

                clasificacion[
                    nombre
                ] = {

                    "resultado":
                        "sospechoso",

                    "evidencia":
                        señales_sospechosas,

                    "accion_inmediata":
                        "investigar_mas",

                    "no_eliminar_automaticamente":
                        True
                }

                causas.append({

                    "causa":
                        (
                            f"{nombre} presenta múltiples "
                            "indicadores que requieren investigación."
                        ),

                    "proceso":
                        nombre,

                    "tipo":
                        "proceso_sospechoso",

                    "confianza":
                        "alta"
                })

            else:

                clasificacion[
                    nombre
                ] = {

                    "resultado":
                        "indeterminado",

                    "evidencia":
                        señales_legitimas
                        + señales_sospechosas,

                    "accion_inmediata":
                        "investigar_mas"
                }

        if not causas:

            causas.append({

                "causa":
                    (
                        "No hay suficiente información "
                        "para determinar una causa."
                    ),

                "confianza":
                    "baja"
            })

        return {

            "causas":
                causas,

            "clasificacion":
                clasificacion,

            "necesita_mas_datos":
                all(
                    causa.get(
                        "confianza",
                        "baja"
                    ) == "baja"

                    for causa in causas
                )
        }

    def elegir_causa_principal(
        self,
        causas: dict
    ) -> dict:

        lista = causas.get(
            "causas",
            []
        )

        if not lista:

            return {
                "causa":
                    "No hay causas disponibles.",

                "proceso":
                    None,

                "confianza":
                    "baja",

                "puntuacion":
                    0,

                "motivo":
                    "No se encontraron causas."
            }

        # ====================================================
        # AGRUPAR DOMINIOS
        # ====================================================

        dominios = set()

        for causa in lista:

            tipo = str(
                causa.get(
                    "tipo",
                    ""
                )
            ).lower()

            if tipo:

                dominio = tipo.split(
                    "_"
                )[0]

                dominios.add(
                    dominio
                )

        # ====================================================
        # SI HAY MUCHOS PROBLEMAS INDEPENDIENTES
        # ====================================================

        if len(dominios) >= 3:

            causas_altas = [

                causa

                for causa in lista

                if causa.get(
                    "confianza"
                ) == "alta"
            ]

            if len(
                causas_altas
            ) >= 2:

                return {
                    "causa":
                        (
                            "Hay múltiples problemas independientes "
                            "y no existe evidencia suficiente para "
                            "establecer una única causa principal."
                        ),

                    "proceso":
                        None,

                    "confianza":
                        "baja",

                    "puntuacion":
                        0,

                    "motivo":
                        (
                            "Se detectaron causas de varios dominios "
                            "independientes. JARVIS debe investigarlas "
                            "por separado en lugar de inventar una "
                            "causa común."
                        )
                }

        # ====================================================
        # PUNTUAR CAUSAS
        # ====================================================

        def puntuacion(causa):

            confianza = str(
                causa.get(
                    "confianza",
                    "baja"
                )
            ).lower()

            tipo = str(
                causa.get(
                    "tipo",
                    ""
                )
            ).lower()

            puntos = {

                "alta":
                    30,

                "media":
                    20,

                "baja":
                    10
            }.get(
                confianza,
                10
            )

            # Relaciones causales directas pesan más.
            if tipo in {
                "causalidad_temporal",
                "dns",
                "dns_servidor",
                "permisos",
                "puerto_usb",
                "servicio",
                "servicio_dependencia",
                "proceso_sospechoso"
            }:

                puntos += 10

            return puntos

        mejor = max(
            lista,
            key=puntuacion
        )

        return {
            "causa":
                mejor.get(
                    "causa"
                ),

            "proceso":
                mejor.get(
                    "proceso"
                ),

            "confianza":
                mejor.get(
                    "confianza",
                    "baja"
                ),

            "puntuacion":
                puntuacion(
                    mejor
                ),

            "motivo":
                (
                    "Se eligió la causa con mayor evidencia "
                    "y relación causal."
                )
        }

    def clasificar_limpieza(
        self,
        almacenamiento: dict
    ) -> dict:

        categorias = []

        # ----------------------------------------------------
        # TEMPORALES
        # ----------------------------------------------------

        temporales = almacenamiento.get(
            "temporales_mb",
            0
        )

        if temporales > 0:

            categorias.append({
                "categoria":
                    "temporales",

                "tamano_mb":
                    temporales,

                "tipo":
                    "basura",

                "riesgo":
                    "bajo",

                "requiere_confirmacion":
                    True,

                "puede_eliminarse":
                    True
            })

        # ----------------------------------------------------
        # CACHE
        # ----------------------------------------------------

        cache = almacenamiento.get(
            "cache_mb",
            0
        )

        if cache > 0:

            categorias.append({
                "categoria":
                    "cache",

                "tamano_mb":
                    cache,

                "tipo":
                    "basura",

                "riesgo":
                    "medio",

                "requiere_confirmacion":
                    True,

                "puede_eliminarse":
                    True
            })

        # ----------------------------------------------------
        # PAPELERA
        # ----------------------------------------------------

        papelera = almacenamiento.get(
            "papelera_mb",
            0
        )

        if papelera > 0:

            categorias.append({
                "categoria":
                    "papelera",

                "tamano_mb":
                    papelera,

                "tipo":
                    "datos_eliminados",

                "riesgo":
                    "medio",

                "requiere_confirmacion":
                    True,

                "puede_eliminarse":
                    True
            })

        # ----------------------------------------------------
        # DESCARGAS
        # ----------------------------------------------------

        descargas = almacenamiento.get(
            "descargas_mb",
            0
        )

        if descargas > 0:

            categorias.append({
                "categoria":
                    "descargas",

                "tamano_mb":
                    descargas,

                "tipo":
                    "datos_personales",

                "riesgo":
                    "alto",

                "requiere_confirmacion":
                    True,

                "puede_eliminarse":
                    False
            })

        # ----------------------------------------------------
        # DOCUMENTOS
        # ----------------------------------------------------

        documentos = almacenamiento.get(
            "documentos_mb",
            0
        )

        if documentos > 0:

            categorias.append({
                "categoria":
                    "documentos",

                "tamano_mb":
                    documentos,

                "tipo":
                    "datos_personales",

                "riesgo":
                    "critico",

                "requiere_confirmacion":
                    True,

                "puede_eliminarse":
                    False
            })

        # ----------------------------------------------------
        # FOTOS
        # ----------------------------------------------------

        fotos = almacenamiento.get(
            "fotos_mb",
            0
        )

        if fotos > 0:

            categorias.append({
                "categoria":
                    "fotos",

                "tamano_mb":
                    fotos,

                "tipo":
                    "datos_personales",

                "riesgo":
                    "critico",

                "requiere_confirmacion":
                    True,

                "puede_eliminarse":
                    False
            })

        # ----------------------------------------------------
        # SISTEMA
        # ----------------------------------------------------

        sistema = almacenamiento.get(
            "archivos_sistema_mb",
            0
        )

        if sistema > 0:

            categorias.append({
                "categoria":
                    "archivos_sistema",

                "tamano_mb":
                    sistema,

                "tipo":
                    "sistema",

                "riesgo":
                    "critico",

                "requiere_confirmacion":
                    True,

                "puede_eliminarse":
                    False
            })

        espacio_seguro = sum(
            categoria["tamano_mb"]
            for categoria in categorias
            if categoria["puede_eliminarse"]
        )

        return {
            "categorias":
                categorias,

            "espacio_seguro_mb":
                espacio_seguro,

            "requiere_confirmacion":
                any(
                    categoria[
                        "requiere_confirmacion"
                    ]
                    for categoria in categorias
                    if categoria[
                        "puede_eliminarse"
                    ]
                )
        }



    def evaluar_pc(
        self,
        estado: dict
    ) -> dict:

        problemas = []

        sistema = estado.get(
            "sistema",
            {}
        )

        cpu = sistema.get(
            "cpu_porcentaje"
        )

        ram = sistema.get(
            "ram_disponible_gb"
        )

        temperatura_cpu = sistema.get(
            "temperatura_cpu_c"
        )

        temperatura_cpu_normal = sistema.get(
            "temperatura_cpu_normal_c"
        )

        gpu = sistema.get(
            "uso_gpu_porcentaje"
        )

        temperatura_gpu = sistema.get(
            "temperatura_gpu_c"
        )

        temperatura_gpu_normal = sistema.get(
            "temperatura_gpu_normal_c"
        )

        # CPU

        if cpu is not None:

            if cpu >= 90:

                problemas.append(
                    "Uso de CPU muy alto."
                )

            elif cpu >= 70:

                problemas.append(
                    "Uso de CPU elevado."
                )

        # RAM

        if ram is not None:

            if ram <= 2:

                problemas.append(
                    "Hay muy poca RAM disponible."
                )

            elif ram <= 4:

                problemas.append(
                    "La RAM disponible es baja."
                )

        # CPU temperatura

        if temperatura_cpu is not None:

            if temperatura_cpu >= 90:

                problemas.append(
                    "La temperatura de CPU es muy alta."
                )

            elif temperatura_cpu >= 80:

                problemas.append(
                    "La temperatura de CPU es elevada."
                )

        if (
            temperatura_cpu is not None
            and
            temperatura_cpu_normal is not None
            and
            temperatura_cpu
            >
            temperatura_cpu_normal + 20
        ):

            problemas.append(
                "La temperatura de CPU está muy por encima de su valor normal."
            )

        # GPU

        if gpu is not None:

            if gpu >= 90:

                problemas.append(
                    "Uso de GPU muy alto."
                )

        if temperatura_gpu is not None:

            if temperatura_gpu >= 90:

                problemas.append(
                    "La temperatura de GPU es muy alta."
                )

            elif temperatura_gpu >= 80:

                problemas.append(
                    "La temperatura de GPU es elevada."
                )

        if (
            temperatura_gpu is not None
            and
            temperatura_gpu_normal is not None
            and
            temperatura_gpu
            >
            temperatura_gpu_normal + 15
        ):

            problemas.append(
                "La temperatura de GPU está por encima de su valor normal."
            )

        # ENERGIA

        energia = estado.get(
            "energia",
            {}
        )

        potencia = energia.get(
            "potencia_actual_w"
        )

        potencia_normal = energia.get(
            "potencia_normal_w"
        )

        limite = energia.get(
            "limite_estimado_w"
        )

        voltaje = energia.get(
            "voltaje_entrada_v"
        )

        voltaje_normal = energia.get(
            "voltaje_normal_v"
        )

        if (
            potencia is not None
            and
            potencia_normal is not None
            and
            potencia
            >
            potencia_normal * 1.5
        ):

            problemas.append(
                "El consumo de energía es elevado respecto del valor normal."
            )

        if (
            potencia is not None
            and
            limite is not None
            and
            potencia
            >=
            limite * 0.85
        ):

            problemas.append(
                "El consumo se aproxima al límite estimado del sistema."
            )

        if (
            voltaje is not None
            and
            voltaje_normal is not None
            and
            abs(
                voltaje - voltaje_normal
            ) >= 10
        ):

            problemas.append(
                "El voltaje de entrada presenta una desviación importante."
            )

        # EVENTOS

        eventos = estado.get(
            "eventos_energia",
            []
        )

        for evento in eventos:

            tipo = str(
                evento.get(
                    "tipo",
                    ""
                )
            ).lower()

            causa = str(
                evento.get(
                    "causa_registrada",
                    ""
                )
            ).lower()

            if (
                tipo == "apagado_inesperado"
                and
                evento.get(
                    "reciente"
                ) is True
            ):

                problemas.append(
                    "Se registró un apagado inesperado reciente."
                )

            if causa == "thermal":

                problemas.append(
                    "Existe evidencia de un evento relacionado con protección térmica."
                )

        # APLICACION

        aplicacion = estado.get(
            "aplicacion",
            {}
        )

        if aplicacion.get(
            "responde"
        ) is False:

            problemas.append(
                "La aplicación no responde correctamente."
            )

        if aplicacion.get(
            "errores_recientes",
            0
        ) >= 3:

            problemas.append(
                "La aplicación presenta varios errores recientes."
            )

        return {

            "estado":
                "revisar"
                if problemas
                else
                "bien",

            "problemas":
                problemas,

            "necesita_investigacion":
                bool(problemas)
        }

    def decidir_siguiente_paso(
        self,
        resultados: list[dict]
    ) -> Accion | None:

        if not resultados:
            return None

        # ------------------------------------
        # BUSCAR CPU / RAM ALTA
        # ------------------------------------

        for resultado in resultados:

            datos = resultado.get(
                "datos"
            )

            if not isinstance(
                datos,
                dict
            ):
                continue

            cpu = datos.get(
                "cpu_porcentaje"
            )

            ram = datos.get(
                "ram_disponible_gb"
            )

            if (
                cpu is not None
                and cpu >= 90
            ):

                return Accion(
                    nombre="listar_procesos",
                    argumentos={
                        "limite": 30
                    },
                    motivo=(
                        "El uso de CPU es alto. "
                        "Revisar procesos para "
                        "buscar la causa."
                    )
                )

            if (
                ram is not None
                and ram <= 2
            ):

                return Accion(
                    nombre="listar_procesos",
                    argumentos={
                        "limite": 30
                    },
                    motivo=(
                        "Hay poca RAM disponible. "
                        "Revisar procesos."
                    )
                )

        # ------------------------------------
        # SI NO HAY PROBLEMAS
        # ------------------------------------

        problemas = self.analizar_resultados(
            resultados
        ).get(
            "problemas",
            []
        )

        if not problemas:

            return None

        return Accion(
            nombre="listar_procesos",
            argumentos={
                "limite": 30
            },
            motivo=(
                "Se encontró un posible problema. "
                "Revisar procesos."
            )
        )


    # --------------------------------------------------------
    # COMPROBAR SI EL PROBLEMA MEJORO
    # --------------------------------------------------------


    def comprobar_resultado(
        self,
        estado_antes: dict,
        estado_despues: dict
    ) -> dict:

        cambios = []

        sistema_a = estado_antes.get(
            "sistema",
            {}
        )

        sistema_d = estado_despues.get(
            "sistema",
            {}
        )

        energia_a = estado_antes.get(
            "energia",
            {}
        )

        energia_d = estado_despues.get(
            "energia",
            {}
        )

        mejoro = False

        # CPU

        cpu_a = sistema_a.get(
            "cpu_porcentaje"
        )

        cpu_d = sistema_d.get(
            "cpu_porcentaje"
        )

        if (
            cpu_a is not None
            and
            cpu_d is not None
            and
            cpu_d < cpu_a
        ):

            cambios.append(
                f"El uso de CPU bajó de {cpu_a}% a {cpu_d}%."
            )

            mejoro = True

        # CPU temperatura

        temp_cpu_a = sistema_a.get(
            "temperatura_cpu_c"
        )

        temp_cpu_d = sistema_d.get(
            "temperatura_cpu_c"
        )

        if (
            temp_cpu_a is not None
            and
            temp_cpu_d is not None
            and
            temp_cpu_d < temp_cpu_a
        ):

            cambios.append(
                (
                    "La temperatura de CPU bajó de "
                    f"{temp_cpu_a} C a {temp_cpu_d} C."
                )
            )

            mejoro = True

        # GPU temperatura

        temp_gpu_a = sistema_a.get(
            "temperatura_gpu_c"
        )

        temp_gpu_d = sistema_d.get(
            "temperatura_gpu_c"
        )

        if (
            temp_gpu_a is not None
            and
            temp_gpu_d is not None
            and
            temp_gpu_d < temp_gpu_a
        ):

            cambios.append(
                (
                    "La temperatura de GPU bajó de "
                    f"{temp_gpu_a} C a {temp_gpu_d} C."
                )
            )

            mejoro = True

        # CONSUMO

        potencia_a = energia_a.get(
            "potencia_actual_w"
        )

        potencia_d = energia_d.get(
            "potencia_actual_w"
        )

        if (
            potencia_a is not None
            and
            potencia_d is not None
            and
            potencia_d < potencia_a
        ):

            cambios.append(
                (
                    "El consumo bajó de "
                    f"{potencia_a} W a {potencia_d} W."
                )
            )

            mejoro = True

        # VOLTAJE

        voltaje_a = energia_a.get(
            "voltaje_entrada_v"
        )

        voltaje_d = energia_d.get(
            "voltaje_entrada_v"
        )

        normal_d = energia_d.get(
            "voltaje_normal_v"
        )

        if (
            voltaje_d is not None
            and
            normal_d is not None
            and
            abs(
                voltaje_d - normal_d
            )
            <
            5
        ):

            cambios.append(
                "El voltaje volvió a un rango cercano al normal."
            )

            mejoro = True

        # EVENTOS

        eventos_d = estado_despues.get(
            "eventos_energia",
            []
        )

        if not eventos_d:

            eventos_a = estado_antes.get(
                "eventos_energia",
                []
            )

            if eventos_a:

                cambios.append(
                    "No quedan eventos de energía anormales recientes."
                )

                mejoro = True

        if mejoro:

            return {

                "mejoro":
                    True,

                "cambios":
                    cambios,

                "estado":
                    "mejoro"
            }

        return {

            "mejoro":
                False,

            "cambios":
                cambios,

            "estado":
                "sin_resolver"
        }

    def ciclo_diagnostico_simulado(self):

        estado_antes = {
            "sistema": {
                "cpu_porcentaje": 95,
                "ram_disponible_gb": 1.5
            }
        }

        evaluacion = self.evaluar_pc(
            estado_antes
        )

        siguiente = self.decidir_siguiente_paso(
            [
                {
                    "datos":
                        estado_antes["sistema"]
                }
            ]
        )

        estado_despues = {
            "sistema": {
                "cpu_porcentaje": 35,
                "ram_disponible_gb": 7.5
            }
        }

        verificacion = self.comprobar_resultado(
            estado_antes,
            estado_despues
        )

        return {
            "estado_inicial":
                evaluacion,

            "siguiente_accion":
                (
                    siguiente.nombre
                    if siguiente
                    else None
                ),

            "motivo":
                (
                    siguiente.motivo
                    if siguiente
                    else ""
                ),

            "verificacion":
                verificacion
        }


    # --------------------------------------------------------
    # APRENDER
    # --------------------------------------------------------

    def aprender(
        self,
        objetivo: str,
        resultado: Resultado
    ):

        registro = {
            "objetivo":
                objetivo,

            "exito":
                resultado.exito,

            "mensaje":
                resultado.mensaje,

            "datos":
                resultado.datos,

            "error":
                resultado.error,
        }

        self.historial.append(
            registro
        )

    # --------------------------------------------------------
    # GUARDAR Y RECORDAR
    # --------------------------------------------------------

    def guardar_experiencia(
        self,
        objetivo: str,
        accion: str,
        resultado: dict
    ):

        experiencia = {
            "objetivo": objetivo,
            "accion": accion,
            "resultado": resultado,
        }

        self.historial.append(
            experiencia
        )

        self.conocimientos[
            objetivo.lower().strip()
        ] = experiencia

    def recordar(
        self,
        objetivo: str
    ) -> dict | None:

        clave = objetivo.lower().strip()

        return self.conocimientos.get(
            clave
        )


    # --------------------------------------------------------
    # APRENDER DE UNA EXPERIENCIA
    # --------------------------------------------------------

    def aprender_experiencia(
        self,
        objetivo: str,
        accion: str,
        resultado: dict,
        funciono: bool
    ):

        experiencia = {
            "objetivo": objetivo,
            "accion": accion,
            "resultado": resultado,
            "funciono": funciono,
        }

        self.conocimientos[
            objetivo.lower().strip()
        ] = experiencia

        self.historial.append(
            experiencia
        )

    def usar_experiencia(
        self,
        objetivo: str
    ):

        return self.conocimientos.get(
            objetivo.lower().strip()
        )


    # --------------------------------------------------------
    # 1. MEMORIA INTELIGENTE
    # --------------------------------------------------------

    def memoria_parecida(
        self,
        objetivo: str
    ):

        objetivo = objetivo.lower().strip()

        equivalencias = {
            "pc": "computadora",
            "ordenador": "computadora",
            "anda": "esta",
            "está": "esta",
            "lenta": "lento",
        }

        def normalizar(texto):

            palabras = []

            for palabra in texto.split():

                palabra = equivalencias.get(
                    palabra,
                    palabra
                )

                palabras.append(
                    palabra
                )

            return set(palabras)

        palabras_objetivo = normalizar(
            objetivo
        )

        mejor = None
        mejor_puntuacion = 0.0

        for clave, experiencia in self.conocimientos.items():

            if not experiencia.get(
                "funciono",
                False
            ):
                continue

            palabras_memoria = normalizar(
                clave
            )

            if (
                not palabras_objetivo
                or not palabras_memoria
            ):
                continue

            comunes = len(
                palabras_objetivo
                & palabras_memoria
            )

            total = len(
                palabras_objetivo
                | palabras_memoria
            )

            puntuacion = (
                comunes / total
                if total
                else 0
            )

            if puntuacion > mejor_puntuacion:

                mejor_puntuacion = puntuacion
                mejor = experiencia

        if (
            mejor is not None
            and mejor_puntuacion >= 0.25
        ):

            return {
                "experiencia": mejor,
                "similitud": round(
                    mejor_puntuacion,
                    2
                )
            }

        return None


    # --------------------------------------------------------
    # 2. REINTENTOS
    # --------------------------------------------------------

    def siguiente_intento(
        self,
        accion_fallida: str
    ):

        alternativas = {
            "listar_procesos":
                "informacion_sistema",

            "informacion_sistema":
                "listar_procesos",

            "listar_ventanas":
                "informacion_sistema",

            "abrir_app":
                "buscar",
        }

        siguiente = alternativas.get(
            accion_fallida
        )

        if not siguiente:
            return None

        return Accion(
            nombre=siguiente,
            argumentos={},
            motivo=(
                "La primera acción falló. "
                "Intentar otra comprobación."
            )
        )


    # --------------------------------------------------------
    # 3. SEGURIDAD
    # --------------------------------------------------------

    def revisar_seguridad(
        self,
        accion: Accion
    ) -> dict:

        peligrosas = {
            "cerrar_ventana",
            "eliminar_archivo",
            "mover_archivo",
            "renombrar",
            "crear_archivo",
            "crear_carpeta",
            "terminar_proceso",
            "ejecutar_comando",
            "modificar_registro",
        }

        if accion.nombre in peligrosas:

            return {
                "permitido": False,
                "requiere_confirmacion": True,
                "motivo": (
                    "La acción puede modificar "
                    "el sistema."
                )
            }

        return {
            "permitido": True,
            "requiere_confirmacion": False,
            "motivo": "Acción segura."
        }


    # --------------------------------------------------------
    # 4. ELEGIR MEJOR OPCION
    # --------------------------------------------------------

    def elegir_mejor_accion(
        self,
        acciones: list[Accion]
    ):

        if not acciones:
            return None

        puntuadas = []

        for accion in acciones:

            seguridad = self.revisar_seguridad(
                accion
            )

            puntuacion = 100

            if not seguridad["permitido"]:
                puntuacion -= 50

            if accion.peligrosa:
                puntuacion -= 30

            if accion.nombre in {
                "informacion_sistema",
                "listar_procesos",
                "listar_ventanas",
            }:
                puntuacion += 20

            puntuadas.append(
                (
                    puntuacion,
                    accion
                )
            )

        puntuadas.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return puntuadas[0][1]


    # --------------------------------------------------------
    # 5. SABER CUANDO NO HACER NADA
    # --------------------------------------------------------

    def decidir_no_hacer_nada(
        self,
        evaluacion: dict
    ) -> bool:

        if not isinstance(
            evaluacion,
            dict
        ):
            return False

        estado = evaluacion.get(
            "estado"
        )

        problemas = evaluacion.get(
            "problemas",
            []
        )

        return (
            estado == "bien"
            and not problemas
        )


    # --------------------------------------------------------
    # 6. DECISION FINAL
    # --------------------------------------------------------

    # --------------------------------------------------------
    # COMPARAR ESTRATEGIAS
    # --------------------------------------------------------

    # --------------------------------------------------------
    # ELEGIR ESTRATEGIA USANDO EXPERIENCIA
    # --------------------------------------------------------

    # --------------------------------------------------------
    # DECISION CON MEMORIA Y CONTEXTO
    # --------------------------------------------------------

    def elegir_con_experiencia_contextual(
        self,
        situacion: str,
        estrategias: list[dict],
        estado: dict | None = None
    ) -> dict:

        memoria = self.recordar_experiencia(
            situacion
        )

        # ----------------------------------------------------
        # EVALUAR SI LA MEMORIA ES REALMENTE COMPATIBLE
        # ----------------------------------------------------

        usar_memoria = False

        experiencia = None

        if memoria:

            experiencia = memoria.get(
                "experiencia"
            )

            if experiencia:

                funciono = experiencia.get(
                    "funciono",
                    False
                )

                accion_aprendida = experiencia.get(
                    "accion"
                )

                if funciono and accion_aprendida:

                    usar_memoria = True

        # ----------------------------------------------------
        # CONTEXTO ACTUAL
        # ----------------------------------------------------

        sistema = (
            estado.get(
                "sistema",
                {}
            )
            if estado
            else {}
        )

        temperatura = sistema.get(
            "temperatura_cpu_c"
        )

        # Si existe una temperatura crítica,
        # no copiar automáticamente una experiencia antigua.
        if (
            temperatura is not None
            and temperatura >= 90
        ):

            usar_memoria = False

        # ----------------------------------------------------
        # USAR MEMORIA SI ES COMPATIBLE
        # ----------------------------------------------------

        if usar_memoria:

            for estrategia in estrategias:

                if estrategia.get(
                    "nombre"
                ) == experiencia.get(
                    "accion"
                ):

                    return {
                        "seleccionada":
                            estrategia,

                        "origen":
                            "memoria",

                        "motivo":
                            "La experiencia anterior es compatible con la situación actual."
                    }

        # ----------------------------------------------------
        # SI NO, COMPARAR DE NUEVO
        # ----------------------------------------------------

        resultado = self.comparar_estrategias(
            estrategias
        )

        return {
            "seleccionada":
                resultado.get(
                    "seleccionada"
                ),

            "origen":
                "comparacion",

            "motivo":
                (
                    "La memoria no fue considerada suficiente "
                    "para esta situación, así que se compararon "
                    "las estrategias nuevamente."
                )
        }


    # --------------------------------------------------------
    # APRENDER DE LOS ERRORES
    # --------------------------------------------------------

    def aprender_de_error(
        self,
        situacion: str,
        accion: str,
        resultado: dict
    ) -> dict:

        experiencia = {
            "situacion": situacion,
            "accion": accion,
            "resultado": resultado,
            "funciono": False,
            "tipo": "error"
        }

        clave = (
            "error:"
            + situacion.lower().strip()
        )

        self.conocimientos[
            clave
        ] = experiencia

        self.historial.append(
            experiencia
        )

        try:
            self.guardar_memoria()
        except Exception:
            pass

        return experiencia


    def recordar_error(
        self,
        situacion: str
    ) -> dict | None:

        objetivo = (
            "error:"
            + situacion.lower().strip()
        )

        experiencia = self.conocimientos.get(
            objetivo
        )

        if not experiencia:
            return None

        return experiencia


    # --------------------------------------------------------
    # APRENDER CON CONTEXTO
    # --------------------------------------------------------

    # --------------------------------------------------------
    # MEMORIA CON CONTEXTO PROFUNDO
    # --------------------------------------------------------

    def evaluar_compatibilidad_memoria(
        self,
        experiencia: dict,
        contexto_actual: dict
    ) -> dict:

        puntuacion = 0

        coincidencias = []
        diferencias = []

        # ====================================================
        # FUNCIONES AUXILIARES
        # ====================================================

        def agregar_coincidencia(
            texto
        ):

            if texto not in coincidencias:

                coincidencias.append(
                    texto
                )

        def agregar_diferencia(
            texto
        ):

            if texto not in diferencias:

                diferencias.append(
                    texto
                )

        # ====================================================
        # TEXTO DE LA EXPERIENCIA
        # ====================================================

        situacion = str(
            experiencia.get(
                "situacion",
                ""
            )
        ).lower()

        resultado_experiencia = experiencia.get(
            "resultado",
            {}
        )

        # ====================================================
        # DOMINIO DE LA EXPERIENCIA
        # ====================================================

        dominios_memoria = set()

        if any(
            palabra in situacion
            for palabra in [
                "mouse",
                "ratón",
                "raton",
                "teclado",
                "periférico",
                "periferico",
                "usb",
                "controlador",
                "driver",
                "puerto"
            ]
        ):

            dominios_memoria.add(
                "perifericos"
            )

        if any(
            palabra in situacion
            for palabra in [
                "permiso",
                "permisos",
                "escritura",
                "acceso denegado",
                "administrador"
            ]
        ):

            dominios_memoria.add(
                "permisos"
            )

        if any(
            palabra in situacion
            for palabra in [
                "archivo corrupto",
                "corrupción",
                "corrupcion",
                "archivo dañado",
                "archivo danado"
            ]
        ):

            dominios_memoria.add(
                "corrupcion_archivo"
            )

        if any(
            palabra in situacion
            for palabra in [
                "archivo bloqueado",
                "bloqueado por otro proceso",
                "archivo en uso"
            ]
        ):

            dominios_memoria.add(
                "bloqueo_archivo"
            )

        if any(
            palabra in situacion
            for palabra in [
                "red",
                "internet",
                "dns",
                "latencia",
                "paquetes"
            ]
        ):

            dominios_memoria.add(
                "red"
            )

        if any(
            palabra in situacion
            for palabra in [
                "servicio",
                "dependencia"
            ]
        ):

            dominios_memoria.add(
                "servicios"
            )

        if any(
            palabra in situacion
            for palabra in [
                "explorer",
                "escritorio",
                "barra de tareas"
            ]
        ):

            dominios_memoria.add(
                "windows_shell"
            )

        # ====================================================
        # DETECTAR DETALLES DEL PERIFERICO EN EXPERIENCIA
        # ====================================================

        perif_memoria = None

        if (
            "periferico" in resultado_experiencia
            or "periférico" in resultado_experiencia
        ):

            perif_memoria = (
                resultado_experiencia.get(
                    "periferico"
                )
                or
                resultado_experiencia.get(
                    "periférico"
                )
            )

        if not perif_memoria:

            perif_memoria = {}

        periferico_nombre_memoria = str(
            perif_memoria.get(
                "nombre",
                ""
            )
        ).lower()

        if "mouse" in situacion or "ratón" in situacion or "raton" in situacion:

            perif_memoria_tipo = "mouse"

        elif "teclado" in situacion:

            perif_memoria_tipo = "teclado"

        elif (
            "periférico" in situacion
            or
            "periferico" in situacion
        ):

            perif_memoria_tipo = "periferico"

        else:

            perif_memoria_tipo = None

        # ====================================================
        # PUERTO / CONTROLADOR / INTERMITENCIA EN MEMORIA
        # ====================================================

        puerto_memoria = (
            resultado_experiencia.get(
                "puerto",
                {}
            )
        )

        if not isinstance(
            puerto_memoria,
            dict
        ):

            puerto_memoria = {}

        puerto_estado_memoria = str(
            puerto_memoria.get(
                "estado",
                ""
            )
        ).lower()

        controlador_memoria = (
            resultado_experiencia.get(
                "controlador",
                {}
            )
        )

        if not isinstance(
            controlador_memoria,
            dict
        ):

            controlador_memoria = {}

        controlador_estado_memoria = str(
            controlador_memoria.get(
                "estado",
                ""
            )
        ).lower()

        # ====================================================
        # INTERMITENCIA EN MEMORIA
        # ====================================================

        intermitencia_memoria = False

        if (
            "intermitente" in situacion
            or "intermitencia" in situacion
            or "por momentos" in situacion
            or "deja de responder" in situacion
            or "vuelve a funcionar" in situacion
        ):

            intermitencia_memoria = True

        if isinstance(
            perif_memoria,
            dict
        ):

            if perif_memoria.get(
                "intermitente"
            ) is True:

                intermitencia_memoria = True

        # ====================================================
        # DOMINIO ACTUAL
        # ====================================================

        dominios_actuales = set()

        perifericos_actuales = contexto_actual.get(
            "perifericos",
            []
        )

        puertos_actuales = contexto_actual.get(
            "puertos_usb",
            []
        )

        controladores_actuales = contexto_actual.get(
            "controladores",
            []
        )

        if perifericos_actuales:

            dominios_actuales.add(
                "perifericos"
            )

        if puertos_actuales:

            dominios_actuales.add(
                "perifericos"
            )

        if controladores_actuales:

            dominios_actuales.add(
                "perifericos"
            )

        archivos_actuales = contexto_actual.get(
            "archivos",
            {}
        )

        archivo_actual = archivos_actuales.get(
            "archivo_problema",
            {}
        )

        permisos_actuales = contexto_actual.get(
            "permisos",
            {}
        )

        if (
            archivo_actual.get(
                "puede_escribir"
            ) is False

            or

            archivo_actual.get(
                "permiso_escritura"
            ) is False

            or

            permisos_actuales.get(
                "puede_escribir_archivo"
            ) is False
        ):

            dominios_actuales.add(
                "permisos"
            )

        if archivo_actual.get(
            "bloqueado"
        ) is True:

            dominios_actuales.add(
                "bloqueo_archivo"
            )

        if archivo_actual.get(
            "corrupcion_detectada"
        ) is True:

            dominios_actuales.add(
                "corrupcion_archivo"
            )

        if contexto_actual.get(
            "red"
        ):

            dominios_actuales.add(
                "red"
            )

        if contexto_actual.get(
            "servicios"
        ):

            dominios_actuales.add(
                "servicios"
            )

        # ====================================================
        # DOMINIO COMUN
        # ====================================================

        comunes = (
            dominios_memoria
            &
            dominios_actuales
        )

        if comunes:

            puntuacion += 60

            for dominio in comunes:

                agregar_coincidencia(
                    f"El dominio del problema coincide: {dominio}."
                )

        else:

            if dominios_memoria:

                puntuacion -= 30

                agregar_diferencia(
                    "El dominio del problema es diferente."
                )

        # ====================================================
        # PERIFERICO: TIPO
        # ====================================================

        tipo_actual = None

        for periferico in perifericos_actuales:

            tipo = str(
                periferico.get(
                    "tipo",
                    ""
                )
            ).lower()

            nombre = str(
                periferico.get(
                    "nombre",
                    ""
                )
            ).lower()

            if (
                "mouse" in tipo
                or "mouse" in nombre
                or "ratón" in nombre
                or "raton" in nombre
            ):

                tipo_actual = "mouse"

                break

            if "teclado" in tipo or "teclado" in nombre:

                tipo_actual = "teclado"

                break

        if (
            perif_memoria_tipo
            and tipo_actual
        ):

            if (
                perif_memoria_tipo
                == tipo_actual
            ):

                puntuacion += 25

                agregar_coincidencia(
                    "El tipo de periférico coincide."
                )

            else:

                puntuacion -= 20

                agregar_diferencia(
                    "El tipo de periférico es diferente."
                )

        # ====================================================
        # PERIFERICO: NOMBRE EXACTO
        # ====================================================

        nombres_actuales = [
            str(
                periferico.get(
                    "nombre",
                    ""
                )
            ).lower()

            for periferico in perifericos_actuales
        ]

        if periferico_nombre_memoria:

            if any(
                periferico_nombre_memoria
                in nombre
                or
                nombre
                in periferico_nombre_memoria

                for nombre in nombres_actuales

                if nombre
            ):

                puntuacion += 15

                agregar_coincidencia(
                    "El periférico coincide."
                )

        # ====================================================
        # INTERMITENCIA
        # ====================================================

        intermitencia_actual = False

        for periferico in perifericos_actuales:

            if periferico.get(
                "intermitente"
            ) is True:

                intermitencia_actual = True

            if (
                periferico.get(
                    "responde"
                ) is False
            ):

                errores = periferico.get(
                    "errores_recientes",
                    0
                )

                if errores:

                    intermitencia_actual = True

        if (
            intermitencia_memoria
            and intermitencia_actual
        ):

            puntuacion += 25

            agregar_coincidencia(
                "El comportamiento intermitente coincide."
            )

        elif intermitencia_memoria != intermitencia_actual:

            puntuacion -= 15

            agregar_diferencia(
                "La intermitencia es diferente."
            )

        # ====================================================
        # PUERTO USB
        # ====================================================

        puerto_actual_problematico = False

        for puerto in puertos_actuales:

            estado_puerto = str(
                puerto.get(
                    "estado",
                    ""
                )
            ).lower()

            if estado_puerto not in {
                "",
                "normal",
                "ok"
            }:

                puerto_actual_problematico = True

                break

        if puerto_memoria:

            if (
                puerto_actual_problematico
                and
                puerto_estado_memoria not in {
                    "",
                    "normal",
                    "ok"
                }
            ):

                puntuacion += 20

                agregar_coincidencia(
                    "El estado problemático del puerto USB coincide."
                )

            elif (
                puerto_actual_problematico
                !=
                (
                    puerto_estado_memoria
                    not in {
                        "",
                        "normal",
                        "ok"
                    }
                )
            ):

                puntuacion -= 10

                agregar_diferencia(
                    "El estado del puerto USB es diferente."
                )

        # ====================================================
        # CONTROLADOR
        # ====================================================

        controlador_actual_problematico = False

        for controlador in controladores_actuales:

            errores = controlador.get(
                "errores",
                0
            )

            estado_controlador = str(
                controlador.get(
                    "estado",
                    ""
                )
            ).lower()

            if (
                errores >= 3
                or
                estado_controlador in {
                    "error",
                    "fallando",
                    "inactivo"
                }
            ):

                controlador_actual_problematico = True

                break

        if controlador_memoria:

            memoria_controlador_problematico = (
                controlador_estado_memoria
                in {
                    "error",
                    "fallando",
                    "inactivo"
                }
            )

            if (
                controlador_actual_problematico
                and
                memoria_controlador_problematico
            ):

                puntuacion += 15

                agregar_coincidencia(
                    "El estado del controlador coincide."
                )

        # ====================================================
        # EXPERIENCIA EXITOSA
        # ====================================================

        if experiencia.get(
            "funciono"
        ) is True:

            puntuacion += 10

            agregar_coincidencia(
                "La experiencia anterior funcionó."
            )

        else:

            puntuacion -= 20

            agregar_diferencia(
                "La experiencia anterior falló."
            )

        # ====================================================
        # HARDWARE: SOLO CONTEXTO SECUNDARIO
        # ====================================================

        sistema_memoria = (
            resultado_experiencia.get(
                "sistema",
                {}
            )
        )

        sistema_actual = contexto_actual.get(
            "sistema",
            {}
        )

        cpu_memoria = sistema_memoria.get(
            "cpu_porcentaje"
        )

        cpu_actual = sistema_actual.get(
            "cpu_porcentaje"
        )

        if (
            cpu_memoria is not None
            and cpu_actual is not None
        ):

            if abs(
                cpu_memoria
                -
                cpu_actual
            ) <= 15:

                puntuacion += 3

            else:

                agregar_diferencia(
                    "El nivel de CPU es diferente."
                )

        ram_memoria = sistema_memoria.get(
            "ram_disponible_gb"
        )

        ram_actual = sistema_actual.get(
            "ram_disponible_gb"
        )

        if (
            ram_memoria is not None
            and ram_actual is not None
        ):

            if abs(
                ram_memoria
                -
                ram_actual
            ) <= 2:

                puntuacion += 3

            else:

                agregar_diferencia(
                    "La RAM disponible es diferente."
                )

        temperatura_memoria = sistema_memoria.get(
            "temperatura_cpu_c"
        )

        temperatura_actual = sistema_actual.get(
            "temperatura_cpu_c"
        )

        if (
            temperatura_memoria is not None
            and temperatura_actual is not None
        ):

            if abs(
                temperatura_memoria
                -
                temperatura_actual
            ) <= 10:

                puntuacion += 3

            else:

                agregar_diferencia(
                    "La temperatura es diferente."
                )

        # ====================================================
        # NIVELES
        # ====================================================

        if puntuacion >= 70:

            compatible = True
            nivel = "alta"

        elif puntuacion >= 45:

            compatible = True
            nivel = "media"

        else:

            compatible = False
            nivel = "baja"

        return {
            "compatible":
                compatible,

            "puntuacion":
                puntuacion,

            "nivel":
                nivel,

            "coincidencias":
                coincidencias,

            "diferencias":
                diferencias
        }





    def elegir_memoria_mas_util(
        self,
        experiencias: list[dict],
        contexto_actual: dict
    ) -> dict:

        def normalizar(texto):

            if texto is None:
                return ""

            return (
                str(texto)
                .lower()
                .replace("á", "a")
                .replace("é", "e")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ú", "u")
            )

        dominios = {

            "energia": {
                "temperatura",
                "cpu",
                "gpu",
                "consumo",
                "potencia",
                "voltaje",
                "apagado",
                "termica",
                "térmica",
                "proteccion",
                "protección"
            },

            "procesos": {
                "proceso",
                "ejecutable",
                "programa",
                "aplicacion",
                "aplicación",
                "cpu",
                "ram"
            },

            "almacenamiento": {
                "disco",
                "archivo",
                "espacio",
                "almacenamiento",
                "escritura",
                "lectura"
            },

            "red": {
                "red",
                "internet",
                "dns",
                "gateway",
                "dominio",
                "ip"
            },

            "perifericos": {
                "mouse",
                "teclado",
                "usb",
                "periferico",
                "puerto"
            },

            "servicios": {
                "servicio",
                "arranque",
                "inicio",
                "dependencia"
            }
        }

        subtipos = {

            "temperatura_cpu": {
                "temperatura cpu",
                "cpu alta temperatura",
                "cpu elevada",
                "cpu caliente",
                "cpu muy alta",
                "sobrecalentamiento cpu"
            },

            "temperatura_gpu": {
                "temperatura gpu",
                "gpu alta temperatura",
                "gpu elevada",
                "gpu caliente",
                "gpu muy alta",
                "sobrecalentamiento gpu"
            },

            "carga_hardware": {
                "carga alta",
                "alta carga",
                "carga intensa",
                "cpu y gpu trabajan",
                "trabajando intensamente"
            },

            "consumo_energia": {
                "consumo de energia",
                "consumo de energía",
                "consumo electrico",
                "consumo eléctrico",
                "potencia elevada",
                "potencia alta"
            },

            "apagado_inesperado": {
                "apagado inesperado",
                "se apago",
                "se apagó",
                "apagado repentino",
                "apagado inesperado"
            },

            "proteccion_termica": {
                "proteccion termica",
                "protección térmica",
                "proteccion termica activada",
                "protección térmica activada"
            },

            "proceso_recursos": {
                "consume mucho cpu",
                "consume mucha cpu",
                "consume ram",
                "consume mucha ram",
                "uso de cpu",
                "uso de ram"
            },

            "proceso_legitimo": {
                "firma valida",
                "firma digital valida",
                "hash conocido",
                "programa instalado",
                "aplicacion instalada",
                "aplicacion relacionada",
                "dominio conocido"
            },

            "archivo_bloqueado": {
                "archivo bloqueado",
                "archivo no permite escribir",
                "otro proceso lo mantiene bloqueado",
                "otro programa lo tiene abierto"
            },

            "espacio_disco": {
                "poco espacio",
                "espacio libre",
                "disco lleno",
                "almacenamiento lleno"
            },

            "dns": {
                "dns",
                "nombres no resuelven",
                "nombre de dominio no resuelve",
                "resolucion dns"
            },

            "periferico_usb": {
                "mouse usb",
                "teclado usb",
                "puerto usb",
                "periferico usb"
            },

            "intermitencia": {
                "intermitente",
                "intermitencia",
                "por momentos",
                "deja de responder y vuelve"
            },

            "servicio_arranque": {
                "servicio de windows",
                "servicio tarda",
                "retrasa el arranque",
                "inicio de windows"
            }
        }


        def detectar(texto, grupos):

            texto = normalizar(
                texto
            )

            encontrados = set()

            for nombre, claves in grupos.items():

                for clave in claves:

                    if normalizar(clave) in texto:

                        encontrados.add(
                            nombre
                        )

                        break

            return encontrados


        # ====================================================
        # CONSTRUIR CONTEXTO ACTUAL
        # ====================================================

        partes = []

        if contexto_actual.get("situacion"):
            partes.append(
                str(
                    contexto_actual.get(
                        "situacion"
                    )
                )
            )

        if contexto_actual.get("problema"):
            partes.append(
                str(
                    contexto_actual.get(
                        "problema"
                    )
                )
            )

        if contexto_actual.get("accion"):
            partes.append(
                str(
                    contexto_actual.get(
                        "accion"
                    )
                )
            )

        sistema = contexto_actual.get(
            "sistema",
            {}
        )

        if sistema:

            if sistema.get(
                "temperatura_cpu_c"
            ) is not None:

                partes.append(
                    "temperatura cpu"
                )

            if sistema.get(
                "temperatura_gpu_c"
            ) is not None:

                partes.append(
                    "temperatura gpu"
                )

            if sistema.get(
                "cpu_porcentaje",
                0
            ) >= 80:

                partes.append(
                    "carga alta"
                )

        energia = contexto_actual.get(
            "energia",
            {}
        )

        if energia:

            if energia.get(
                "potencia_actual_w"
            ) is not None:

                partes.append(
                    "consumo de energia"
                )

            if energia.get(
                "voltaje_entrada_v"
            ) is not None:

                partes.append(
                    "voltaje"
                )

        eventos = contexto_actual.get(
            "eventos_energia",
            []
        )

        for evento in eventos:

            if evento.get(
                "tipo"
            ) == "apagado_inesperado":

                partes.append(
                    "apagado inesperado"
                )

            if str(
                evento.get(
                    "causa_registrada",
                    ""
                )
            ).lower() == "thermal":

                partes.append(
                    "proteccion termica"
                )


        archivos = contexto_actual.get(
            "archivos",
            {}
        )

        if archivos:

            archivo = archivos.get(
                "archivo_problema",
                {}
            )

            if archivo.get(
                "bloqueado"
            ) is True:

                partes.append(
                    "archivo bloqueado"
                )


        procesos = contexto_actual.get(
            "procesos",
            []
        )

        if procesos:

            partes.append(
                "proceso"
            )

        texto_actual = " ".join(
            partes
        )

        dominios_actuales = detectar(
            texto_actual,
            dominios
        )

        subtipos_actuales = detectar(
            texto_actual,
            subtipos
        )


        # ====================================================
        # PRIORIDAD TERMICA
        # ====================================================

        termicos = {
            "temperatura_cpu",
            "temperatura_gpu",
            "carga_hardware",
            "consumo_energia",
            "apagado_inesperado",
            "proteccion_termica"
        }

        tiene_contexto_termico = bool(
            subtipos_actuales
            &
            termicos
        )


        # ====================================================
        # EVALUAR EXPERIENCIAS
        # ====================================================

        mejor = None
        mejor_eval = None
        historial = []


        for experiencia in experiencias:

            situacion = normalizar(
                experiencia.get(
                    "situacion",
                    ""
                )
            )

            accion = normalizar(
                experiencia.get(
                    "accion",
                    ""
                )
            )

            texto_experiencia = (
                situacion
                + " "
                + accion
            )

            dominios_exp = detectar(
                texto_experiencia,
                dominios
            )

            subtipos_exp = detectar(
                texto_experiencia,
                subtipos
            )

            puntuacion = 0
            coincidencias = []
            diferencias = []


            # =================================================
            # PRIORIDAD TERMICA
            # =================================================

            termicos_exp = (
                subtipos_exp
                &
                termicos
            )

            termicos_compartidos = (
                subtipos_actuales
                &
                termicos_exp
            )

            if termicos_compartidos:

                puntuacion += 90

                coincidencias.append(
                    "Coincide el subtipo térmico: "
                    + ", ".join(
                        sorted(
                            termicos_compartidos
                        )
                    )
                )


            # =================================================
            # SUBTIPO GENERAL
            # =================================================

            subtipos_compartidos = (
                subtipos_actuales
                &
                subtipos_exp
            )

            # Un subtipo general de proceso no debe
            # sobreescribir una coincidencia térmica.
            subtipos_generales = (
                subtipos_compartidos
                - termicos
            )

            if subtipos_generales:

                puntuacion += (
                    60
                    if not tiene_contexto_termico
                    else 20
                )

                coincidencias.append(
                    "Coincide el subtipo: "
                    + ", ".join(
                        sorted(
                            subtipos_generales
                        )
                    )
                )


            # =================================================
            # DOMINIO
            # =================================================

            dominios_compartidos = (
                dominios_actuales
                &
                dominios_exp
            )

            if "energia" in dominios_compartidos:

                if tiene_contexto_termico:

                    puntuacion += 30

                    coincidencias.append(
                        "Coincide el dominio energético."
                    )

            elif dominios_compartidos:

                puntuacion += 30

                coincidencias.append(
                    "Coincide el dominio: "
                    + ", ".join(
                        sorted(
                            dominios_compartidos
                        )
                    )
                )


            # =================================================
            # EXPERIENCIA EXITOSA
            # =================================================

            if experiencia.get(
                "funciono"
            ) is True:

                puntuacion += 10

                coincidencias.append(
                    "La experiencia anterior funcionó."
                )


            # =================================================
            # EVITAR FALSOS POSITIVOS
            # =================================================

            if (
                tiene_contexto_termico
                and
                not termicos_compartidos
            ):

                puntuacion = min(
                    puntuacion,
                    40
                )

                diferencias.append(
                    "La experiencia no coincide con el patrón térmico."
                )


            puntuacion = max(
                0,
                puntuacion
            )


            compatible = (
                puntuacion >= 50
            )

            nivel = (

                "alta"
                if puntuacion >= 80

                else
                (
                    "media"
                    if puntuacion >= 50

                    else
                    "baja"
                )
            )


            evaluacion = {

                "compatible":
                    compatible,

                "puntuacion":
                    puntuacion,

                "nivel":
                    nivel,

                "coincidencias":
                    coincidencias,

                "diferencias":
                    diferencias
            }


            historial.append({

                "experiencia":
                    experiencia,

                "evaluacion":
                    evaluacion
            })


            if (
                mejor_eval is None
                or
                puntuacion
                >
                mejor_eval.get(
                    "puntuacion",
                    -1
                )
            ):

                mejor = experiencia
                mejor_eval = evaluacion


        if mejor is None:

            return {

                "experiencia":
                    None,

                "evaluacion":
                    None,

                "usar_memoria":
                    False,

                "historial":
                    [],

                "motivo":
                    "No hay experiencias disponibles."
            }


        usar_memoria = (
            mejor_eval.get(
                "puntuacion",
                0
            )
            >=
            50
        )


        return {

            "experiencia":
                mejor,

            "evaluacion":
                mejor_eval,

            "usar_memoria":
                usar_memoria,

            "historial":
                sorted(
                    historial,
                    key=lambda item:
                        item[
                            "evaluacion"
                        ].get(
                            "puntuacion",
                            0
                        ),
                    reverse=True
                )[:5],

            "motivo":
                (
                    "La experiencia coincide suficientemente "
                    "con el patrón y dominio actuales."

                    if usar_memoria

                    else

                    "La memoria se conserva como referencia, "
                    "pero la coincidencia no es suficiente."
                )
        }

    def decidir_con_error_contextual(
        self,
        situacion: str,
        estrategias: list[dict],
        estado: dict | None = None
    ) -> dict:

        error = self.recordar_error(
            situacion
        )

        # Si no hay un error previo, decidir normalmente.
        if not error:

            return self.comparar_estrategias(
                estrategias
            )

        accion_fallida = error.get(
            "accion"
        )

        # ----------------------------------------------------
        # COMPROBAR SI EL CONTEXTO ACTUAL ES PARECIDO
        # ----------------------------------------------------

        sistema = (
            estado.get(
                "sistema",
                {}
            )
            if estado
            else {}
        )

        temperatura = sistema.get(
            "temperatura_cpu_c"
        )

        cpu = sistema.get(
            "cpu_porcentaje"
        )

        # Por defecto, evitar la acción fallida.
        compatibles = [
            estrategia
            for estrategia in estrategias
            if estrategia.get(
                "nombre"
            ) != accion_fallida
        ]

        # ----------------------------------------------------
        # SI EL CONTEXTO CAMBIO MUCHO,
        # PERMITIR CONSIDERAR NUEVAMENTE LA ACCION
        # ----------------------------------------------------

        contexto_diferente = False

        if temperatura is not None:

            if temperatura >= 90:
                contexto_diferente = True

        if cpu is not None:

            if cpu >= 90:
                contexto_diferente = True

        if contexto_diferente:

            compatibles = estrategias

        resultado = self.comparar_estrategias(
            compatibles
        )

        if contexto_diferente:

            motivo = (
                "La situación actual es suficientemente diferente "
                "como para volver a considerar la acción anterior."
            )

        else:

            motivo = (
                "La acción anterior falló en un contexto parecido, "
                "por eso se evita automáticamente."
            )

        return {
            "seleccionada":
                resultado.get(
                    "seleccionada"
                ),

            "origen":
                "memoria_contextual",

            "motivo":
                motivo
        }


    def evitar_acciones_fallidas(
        self,
        situacion: str,
        estrategias: list[dict]
    ) -> list[dict]:

        error = self.recordar_error(
            situacion
        )

        if not error:
            return estrategias

        accion_fallida = error.get(
            "accion"
        )

        filtradas = [
            estrategia
            for estrategia in estrategias
            if estrategia.get(
                "nombre"
            ) != accion_fallida
        ]

        return filtradas


    # --------------------------------------------------------
    # RESOLVER CONFLICTOS ENTRE EXPERIENCIAS
    # --------------------------------------------------------

    def elegir_experiencia_mejor(
        self,
        situaciones: list[dict]
    ) -> dict | None:

        if not situaciones:
            return None

        mejor = None
        mejor_puntuacion = -1

        for experiencia in situaciones:

            funciono = experiencia.get(
                "funciono",
                False
            )

            if not funciono:
                continue

            puntuacion = 0

            # Una experiencia que funcionó
            # parte con ventaja.
            puntuacion += 50

            # Cuanto más reciente,
            # mejor.
            antiguedad = experiencia.get(
                "antiguedad",
                0
            )

            puntuacion += max(
                0,
                20 - antiguedad
            )

            # Más confianza si el resultado
            # tiene información útil.
            resultado = experiencia.get(
                "resultado",
                {}
            )

            if resultado:
                puntuacion += 5

            if puntuacion > mejor_puntuacion:

                mejor_puntuacion = puntuacion
                mejor = experiencia

        return mejor


    def elegir_con_experiencia(
        self,
        situacion: str,
        estrategias: list[dict]
    ) -> dict:

        memoria = self.recordar_experiencia(
            situacion
        )

        if memoria:
            experiencia = memoria.get(
                "experiencia",
                {}
            )

            accion_aprendida = experiencia.get(
                "accion"
            )

            funciono = experiencia.get(
                "funciono",
                False
            )

            if (
                accion_aprendida
                and funciono
            ):

                for estrategia in estrategias:

                    if estrategia.get(
                        "nombre"
                    ) == accion_aprendida:

                        return {
                            "seleccionada":
                                estrategia,

                            "origen":
                                "memoria",

                            "motivo":
                                "Una experiencia parecida funcionó anteriormente."
                        }

        resultado = self.comparar_estrategias(
            estrategias
        )

        seleccionada = resultado.get(
            "seleccionada"
        )

        return {
            "seleccionada":
                seleccionada,

            "origen":
                "comparacion",

            "motivo":
                resultado.get(
                    "motivo",
                    "Se eligió comparando las estrategias."
                )
        }


    def comparar_estrategias(
        self,
        estrategias: list[dict]
    ) -> dict:

        if not estrategias:

            return {
                "seleccionada": None,
                "motivo":
                    "No hay estrategias disponibles."
            }

        mejor = None
        mejor_puntuacion = -1

        for estrategia in estrategias:

            nombre = estrategia.get(
                "nombre"
            )

            utilidad = estrategia.get(
                "utilidad",
                0
            )

            riesgo = estrategia.get(
                "riesgo",
                0
            )

            confirmacion = estrategia.get(
                "requiere_confirmacion",
                False
            )

            prioridad = estrategia.get(
                "prioridad",
                0
            )

            # ------------------------------------------------
            # PUNTUACION
            # ------------------------------------------------

            puntuacion = (
                utilidad
                + prioridad
                - riesgo
            )

            # Una acción que requiere confirmación
            # pierde prioridad frente a otra igual de útil
            # que sea segura.
            if confirmacion:
                puntuacion -= 2

            estrategia_evaluada = {
                "nombre":
                    nombre,

                "utilidad":
                    utilidad,

                "riesgo":
                    riesgo,

                "prioridad":
                    prioridad,

                "requiere_confirmacion":
                    confirmacion,

                "puntuacion":
                    puntuacion
            }

            if puntuacion > mejor_puntuacion:

                mejor_puntuacion = puntuacion
                mejor = estrategia_evaluada

        return {
            "seleccionada":
                mejor,

            "motivo":
                "Se eligio la estrategia con mejor equilibrio entre utilidad, prioridad y riesgo."
        }


    # --------------------------------------------------------
    # PLANIFICACION ADAPTATIVA
    # --------------------------------------------------------

    def crear_plan_adaptativo(
        self,
        pasos: list[dict]
    ) -> dict:

        plan = []

        for indice, paso in enumerate(
            pasos,
            start=1
        ):

            nombre = paso.get(
                "nombre"
            )

            motivo = paso.get(
                "motivo",
                ""
            )

            si_funciona = paso.get(
                "si_funciona",
                "terminar"
            )

            si_falla = paso.get(
                "si_falla",
                "continuar"
            )

            plan.append({
                "paso": indice,
                "accion": nombre,
                "motivo": motivo,
                "si_funciona": si_funciona,
                "si_falla": si_falla
            })

        return {
            "pasos": plan,
            "cantidad": len(plan)
        }


    def siguiente_paso_plan(
        self,
        plan: dict,
        resultado: dict
    ) -> dict | None:

        pasos = plan.get(
            "pasos",
            []
        )

        if not pasos:
            return None

        paso_actual = resultado.get(
            "paso_actual",
            1
        )

        funciono = resultado.get(
            "funciono"
        )

        if paso_actual > len(pasos):
            return None

        paso = pasos[
            paso_actual - 1
        ]

        if funciono:

            accion = paso.get(
                "si_funciona",
                "terminar"
            )

        else:

            accion = paso.get(
                "si_falla",
                "continuar"
            )

        if accion == "terminar":

            return {
                "decision":
                    "terminar",
                "motivo":
                    "El paso funcionó y no hace falta continuar."
            }

        for siguiente in pasos:

            if siguiente["paso"] > paso_actual:

                return {
                    "decision":
                        "continuar",
                    "siguiente_paso":
                        siguiente,
                    "motivo":
                        (
                            "El paso anterior no fue suficiente. "
                            "Continuar con otra estrategia."
                        )
                }

        return {
            "decision":
                "terminar",
            "motivo":
                "No quedan más estrategias disponibles."
        }








    def decision_final(
        self,
        evaluacion: dict,
        acciones: list
    ) -> dict:

        if not acciones:

            return {

                "accion":
                    None,

                "hacer_nada":
                    True,

                "requiere_confirmacion":
                    False,

                "bloqueada":
                    False,

                "nivel_riesgo":
                    "bajo",

                "motivo":
                    "No existe una acción."
            }


        accion = acciones[0]

        nombre = getattr(
            accion,
            "nombre",
            ""
        )


        restricciones = set(
            getattr(
                self,
                "restricciones_actuales",
                set()
            )
        )


        # ====================================================
        # ALIAS DE RESTRICCIONES GENERALES
        # ====================================================

        if "no_eliminar_archivos" in restricciones:

            restricciones.add(
                "no_eliminar_procesos"
            )


        if "no_desactivar_inicio" in restricciones:

            restricciones.add(
                "no_deshabilitar_servicios"
            )

            restricciones.add(
                "no_eliminar_tareas"
            )


        # ====================================================
        # MAPA CENTRAL DE SEGURIDAD
        # ====================================================

        bloqueo = {

            "cerrar_proceso":
                "no_cerrar_procesos",

            "bloquear_proceso":
                "no_bloquear_procesos",

            "eliminar_proceso":
                "no_eliminar_procesos",

            "eliminar_archivos":
                "no_eliminar_archivos",

            "formatear_disco":
                "no_formatear_disco",

            "cambiar_permisos_archivo":
                "no_cambiar_permisos",

            "desactivar_inicio_proceso":
                "no_desactivar_inicio",

            "desactivar_inicio_automatico":
                "no_desactivar_inicio",

            "deshabilitar_servicio_inicio":
                "no_deshabilitar_servicios",

            "deshabilitar_tarea_programada":
                "no_eliminar_tareas",

            "desactivar_proteccion_termica":
                "no_desactivar_proteccion_termica",

            "cambiar_configuracion_energia":
                "no_cambiar_energia",

            "reiniciar_sistema":
                "no_reiniciar",

            "desinstalar_actualizacion":
                "no_desinstalar_actualizaciones",

            "ejecutar_como_administrador":
                "no_administrador",

            "abrir_fuente":
                "no_abrir_fuente"
        }


        restriccion = bloqueo.get(
            nombre
        )


        if (
            restriccion
            and
            restriccion in restricciones
        ):

            nivel = "critico"

            if nombre in {
                "cerrar_proceso",
                "reiniciar_sistema"
            }:

                nivel = "alto"


            return {

                "accion":
                    nombre,

                "hacer_nada":
                    False,

                "requiere_confirmacion":
                    True,

                "bloqueada":
                    True,

                "nivel_riesgo":
                    nivel,

                "motivo":
                    (
                        "La acción contradice una "
                        "restricción explícita del usuario."
                    )
            }


        # ====================================================
        # ACCIONES MODIFICADORAS
        # ====================================================

        acciones_modificadoras = {

            "cerrar_proceso",
            "bloquear_proceso",
            "eliminar_proceso",

            "desactivar_inicio_proceso",
            "ejecutar_como_administrador",

            "eliminar_archivos",
            "formatear_disco",
            "cambiar_permisos_archivo",

            "desactivar_inicio_automatico",
            "deshabilitar_servicio_inicio",
            "deshabilitar_tarea_programada",

            "desactivar_proteccion_termica",
            "cambiar_configuracion_energia",

            "reiniciar_sistema",
            "desinstalar_actualizacion",

            "abrir_fuente"
        }


        if nombre in acciones_modificadoras:

            nivel = "medio"

            if nombre in {
                "bloquear_proceso",
                "eliminar_proceso",
                "eliminar_archivos",
                "formatear_disco",
                "ejecutar_como_administrador",
                "desactivar_proteccion_termica",
                "abrir_fuente"
            }:

                nivel = "critico"


            return {

                "accion":
                    nombre,

                "hacer_nada":
                    False,

                "requiere_confirmacion":
                    True,

                "bloqueada":
                    False,

                "nivel_riesgo":
                    nivel,

                "motivo":
                    "La acción puede modificar el sistema."
            }


        return {

            "accion":
                nombre,

            "hacer_nada":
                False,

            "requiere_confirmacion":
                False,

            "bloqueada":
                False,

            "nivel_riesgo":
                "bajo",

            "motivo":
                ""
        }

    def cargar_memoria(self):

        try:

            if MEMORIA_ARCHIVO.exists():

                datos = json.loads(
                    MEMORIA_ARCHIVO.read_text(
                        encoding="utf-8"
                    )
                )

                if isinstance(datos, dict):

                    self.conocimientos = datos.get(
                        "conocimientos",
                        {}
                    )

                    self.historial = datos.get(
                        "historial",
                        []
                    )

        except Exception:

            self.conocimientos = {}
            self.historial = []


    def guardar_memoria(self):

        datos = {
            "conocimientos":
                self.conocimientos,

            "historial":
                self.historial,
        }

        MEMORIA_ARCHIVO.write_text(
            json.dumps(
                datos,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )


    def registrar_experiencia(
        self,
        situacion: str,
        razon: str,
        accion: str,
        resultado: dict,
        funciono: bool
    ):

        experiencia = {
            "situacion":
                situacion,

            "razon":
                razon,

            "accion":
                accion,

            "resultado":
                resultado,

            "funciono":
                funciono,
        }

        clave = situacion.lower().strip()

        self.conocimientos[
            clave
        ] = experiencia

        self.historial.append(
            experiencia
        )

        self.guardar_memoria()

        return experiencia


    def recordar_experiencia(
        self,
        situacion: str
    ):

        return self.memoria_parecida(
            situacion
        )


    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    def informacion(self):

        return {
            "estado":
                self.estado,

            "objetivo":
                (
                    self.objetivo_actual.texto
                    if self.objetivo_actual
                    else None
                ),

            "intencion":
                (
                    self.objetivo_actual.intencion
                    if self.objetivo_actual
                    else None
                ),

            "plan_valido":
                (
                    self.plan_actual.valido
                    if self.plan_actual
                    else False
                ),

            "historial":
                len(
                    self.historial
                ),
        }


# ============================================================
# PRUEBA
# ============================================================

if __name__ == "__main__":

    cerebro = (
        CerebroJARVIS()
    )

    pruebas = [
        "Abre Opera GX",
        "Dime cuanta RAM tengo",
        "Muestra las ventanas que estan abiertas",
        "Muestra los procesos activos",
        "Investiga por que mi PC esta lenta",
    ]

    for texto in pruebas:

        print()
        print(
            "OBJETIVO:"
        )
        print(
            texto
        )

        plan = cerebro.decidir(
            texto
        )

        print()
        print(
            json.dumps(
                {
                    "estado":
                        cerebro.estado,

                    "intencion":
                        cerebro.objetivo_actual.intencion,

                    "plan_valido":
                        plan.valido,

                    "acciones": [
                        {
                            "nombre":
                                accion.nombre,

                            "argumentos":
                                accion.argumentos,

                            "motivo":
                                accion.motivo,
                        }

                        for accion
                        in plan.acciones
                    ],

                    "verificacion":
                        plan.verificacion,
                },

                ensure_ascii=False,

                indent=2
            )
        )
