from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

import aprendizaje
import memoria_rapida
import control_pc_avanzado


OLLAMA_URL = os.environ.get(
    "JARVIS_OLLAMA_URL",
    "http://127.0.0.1:11434"
)

MODELO_NORMAL = "qwen2.5-coder:7b"
MODELO_PROFUNDO = "qwen3:8b"


HERRAMIENTAS = {
    "abrir_app":
        "abrir una aplicacion",

    "abrir_ruta":
        "abrir un archivo o carpeta",

    "abrir_carpeta_especial":
        "abrir una carpeta especial",

    "abrir_explorador":
        "abrir el Explorador de archivos",

    "buscar":
        "buscar archivos",

    "buscar_comprimidos":
        "buscar RAR ZIP 7Z",

    "extraer":
        "extraer archivos comprimidos",

    "crear_carpeta":
        "crear una carpeta",

    "crear_archivo":
        "crear un archivo",

    "mover":
        "mover un archivo o carpeta",

    "copiar":
        "copiar un archivo o carpeta",

    "renombrar":
        "renombrar un archivo o carpeta",

    "listar_ventanas":
        "consultar ventanas abiertas",

    "enfocar_ventana":
        "enfocar una ventana",

    "minimizar_ventana":
        "minimizar una ventana",

    "maximizar_ventana":
        "maximizar una ventana",

    "listar_procesos":
        "consultar procesos",

    "proceso_existe":
        "comprobar si un proceso esta activo",

    "listar_apps":
        "consultar aplicaciones instaladas",

    "informacion_sistema":
        "consultar hardware y estado del PC",

    "captura_pantalla":
        "capturar la pantalla",
}


PALABRAS_PROFUNDAS = [
    "investiga",
    "investigar",
    "diagnostica",
    "diagnosticar",
    "analiza",
    "analizar",
    "encuentra la causa",
    "encuentra el problema",
    "soluciona",
    "solucionar",
    "repara",
    "reparar",
    "optimiza",
    "optimizar",
    "compara",
    "comparar",
    "evalua",
    "evaluar",
    "planifica",
    "planificar",
    "diseña",
    "diseñar",
    "razona",
    "razonamiento",
    "explica por que",
    "explica porque",
    "por que falla",
    "porque falla",
]


def modelos_disponibles() -> list[str]:
    try:
        response = requests.get(
            OLLAMA_URL + "/api/tags",
            timeout=5
        )

        response.raise_for_status()

        return [
            item.get("name")
            for item in response.json().get(
                "models",
                []
            )
            if item.get("name")
        ]

    except Exception:
        return []


def modelo_disponible(modelo: str) -> bool:
    disponibles = modelos_disponibles()

    if modelo in disponibles:
        return True

    base = modelo.split(":")[0]

    return any(
        item.startswith(base + ":")
        for item in disponibles
    )


def obtener_estado_pc() -> dict[str, Any]:
    estado = {}

    try:
        estado["sistema"] = (
            control_pc_avanzado.informacion_sistema()
        )
    except Exception:
        estado["sistema"] = {}

    try:
        ventanas = (
            control_pc_avanzado.listar_ventanas()
        )

        if isinstance(
            ventanas,
            list
        ):
            estado["ventanas"] = [
                item.get("titulo", "")
                for item in ventanas[:20]
                if item.get("titulo")
            ]
        else:
            estado["ventanas"] = []

    except Exception:
        estado["ventanas"] = []

    try:
        procesos = (
            control_pc_avanzado.listar_procesos(
                None,
                30
            )
        )

        if isinstance(
            procesos,
            list
        ):
            estado["procesos"] = [
                {
                    "nombre":
                        item.get("nombre"),
                    "pid":
                        item.get("pid"),
                    "ram_mb":
                        item.get("ram_mb"),
                }
                for item in procesos[:30]
            ]
        else:
            estado["procesos"] = []

    except Exception:
        estado["procesos"] = []

    return estado


def clasificar(
    objetivo: str
) -> dict[str, Any]:

    texto = objetivo.lower().strip()

    experiencia = memoria_rapida.buscar(
        objetivo,
        umbral=0.90
    )

    if experiencia:

        return {
            "nivel":
                "memoria",

            "usar_ia":
                False,

            "modelo":
                None,

            "motivo":
                "Existe una experiencia aprendida reutilizable.",

            "experiencia":
                experiencia,
        }

    directas = [
        "ram",
        "memoria ram",
        "procesador",
        "cpu",
        "gpu",
        "hardware",
        "ventanas abiertas",
        "ventanas que estan abiertas",
        "ventanas que están abiertas",
        "muestra las ventanas",
        "muestra las ventanas abiertas",
        "mostrame las ventanas",
        "muéstrame las ventanas",
        "lista las ventanas",
        "listar las ventanas",
        "procesos abiertos",
        "procesos activos",
        "muestra los procesos",
        "mostrame los procesos",
        "muéstrame los procesos",
        "lista los procesos",
        "listar los procesos",
        "aplicaciones instaladas",
        "lista mis aplicaciones",
        "lista las aplicaciones",
    ]

    if any(
        palabra in texto
        for palabra in directas
    ):

        return {
            "nivel":
                "directo",

            "usar_ia":
                False,

            "modelo":
                None,

            "motivo":
                "La consulta puede resolverse directamente.",
        }

    for palabra in PALABRAS_PROFUNDAS:

        if palabra in texto:

            modelo = (
                MODELO_PROFUNDO
                if modelo_disponible(
                    MODELO_PROFUNDO
                )
                else MODELO_NORMAL
            )

            return {
                "nivel":
                    "profundo",

                "usar_ia":
                    True,

                "modelo":
                    modelo,

                "motivo":
                    "La tarea requiere análisis adicional.",
            }

    verbos = [
        "abre",
        "abrir",
        "busca",
        "buscar",
        "mueve",
        "mover",
        "copia",
        "copiar",
        "crea",
        "crear",
        "extrae",
        "extraer",
        "revisa",
        "revisar",
        "comprueba",
        "comprobar",
    ]

    cantidad = sum(
        1
        for verbo in verbos
        if re.search(
            rf"\b{re.escape(verbo)}\b",
            texto
        )
    )

    if cantidad >= 2:

        return {
            "nivel":
                "multipaso",

            "usar_ia":
                True,

            "modelo":
                MODELO_NORMAL,

            "motivo":
                "La tarea contiene varias acciones.",
        }

    return {
        "nivel":
            "normal",

        "usar_ia":
            True,

        "modelo":
            MODELO_NORMAL,

        "motivo":
            "No hay una ruta directa conocida.",
    }


def contexto_minimo(
    objetivo: str
) -> dict[str, Any]:

    memoria = (
        aprendizaje.contexto_para_jarvis(
            objetivo
        )
    )

    estado = obtener_estado_pc()

    return {
        "memoria":
            {
                "experiencias":
                    memoria.get(
                        "experiencias",
                        []
                    )[:3]
            },

        "estado_pc":
            estado,
    }


def plan_local(
    objetivo: str
) -> dict[str, Any] | None:

    texto = objetivo.lower().strip()

    if any(
        palabra in texto
        for palabra in [
            "ram",
            "procesador",
            "cpu",
            "gpu",
            "hardware",
            "especificaciones",
        ]
    ):

        return {
            "tipo":
                "tarea",

            "origen":
                "local",

            "intencion":
                "consultar hardware",

            "objetivo":
                objetivo,

            "plan": [
                {
                    "paso":
                        1,

                    "herramienta":
                        "informacion_sistema",

                    "argumentos":
                        {},

                    "motivo":
                        "Consultar información real del sistema.",
                }
            ],

            "riesgos":
                [],

            "verificacion":
                "Comprobar que se recibieron datos reales.",

            "respuesta":
                "Consultaré el estado del PC.",
        }

    if any(
        frase in texto
        for frase in [
            "muestra las ventanas",
            "muestra las ventanas abiertas",
            "mostrame las ventanas",
            "muéstrame las ventanas",
            "que ventanas tengo abiertas",
            "qué ventanas tengo abiertas",
            "lista las ventanas",
            "listar las ventanas",
        ]
    ):

        return {
            "tipo":
                "tarea",

            "origen":
                "local",

            "intencion":
                "consultar ventanas",

            "objetivo":
                objetivo,

            "plan": [
                {
                    "paso":
                        1,

                    "herramienta":
                        "listar_ventanas",

                    "argumentos":
                        {},

                    "motivo":
                        "Consultar ventanas reales.",
                }
            ],

            "riesgos":
                [],

            "verificacion":
                "Comprobar que se recibió una lista.",

            "respuesta":
                "Consultaré las ventanas abiertas.",
        }

    if any(
        frase in texto
        for frase in [
            "muestra los procesos",
            "mostrame los procesos",
            "muéstrame los procesos",
            "que procesos tengo abiertos",
            "qué procesos tengo abiertos",
            "procesos abiertos",
            "procesos activos",
            "lista los procesos",
        ]
    ):

        return {
            "tipo":
                "tarea",

            "origen":
                "local",

            "intencion":
                "consultar procesos",

            "objetivo":
                objetivo,

            "plan": [
                {
                    "paso":
                        1,

                    "herramienta":
                        "listar_procesos",

                    "argumentos":
                        {
                            "limite":
                                30
                        },

                    "motivo":
                        "Consultar procesos activos.",
                }
            ],

            "riesgos":
                [],

            "verificacion":
                "Comprobar la lista recibida.",

            "respuesta":
                "Consultaré los procesos activos.",
        }

    return None


def reflexion_local(
    plan: dict[str, Any],
    estado_pc: dict[str, Any]
) -> dict[str, Any]:

    problemas = []

    pasos = plan.get(
        "plan",
        []
    )

    if not pasos:
        problemas.append(
            "El plan no tiene pasos."
        )

    for paso in pasos:

        herramienta = paso.get(
            "herramienta"
        )

        if herramienta not in HERRAMIENTAS:

            problemas.append(
                "Herramienta desconocida: "
                + str(herramienta)
            )

    if (
        "abrir_app" in [
            paso.get("herramienta")
            for paso in pasos
        ]
        and not estado_pc
    ):
        problemas.append(
            "No hay suficiente contexto del sistema."
        )

    return {
        "aprobado":
            len(problemas) == 0,

        "puntuacion":
            100
            if not problemas
            else 0,

        "problemas":
            problemas,

        "correcciones":
            [],

        "motivo":
            (
                "El plan es coherente con el estado conocido."
                if not problemas
                else
                "El plan necesita revisión."
            ),
    }


def razonamiento_ia(
    objetivo: str,
    clasificacion: dict[str, Any],
    contexto: dict[str, Any],
):

    prompt = f"""
Eres el planificador de JARVIS.

Debes comprender el objetivo usando el estado
REAL actual de la computadora.

OBJETIVO:
{objetivo}

CONTEXTO:
{json.dumps(contexto, ensure_ascii=False)}

HERRAMIENTAS:
{json.dumps(HERRAMIENTAS, ensure_ascii=False)}

Crea el menor plan posible.

No ejecutes nada.
No inventes resultados.
No inventes datos que no aparezcan en CONTEXTO.

Devuelve SOLO JSON:

{{
  "tipo": "tarea",
  "origen": "ia",
  "intencion": "",
  "objetivo": "",
  "plan": [
    {{
      "paso": 1,
      "herramienta": "",
      "argumentos": {{}},
      "motivo": ""
    }}
  ],
  "riesgos": [],
  "verificacion": "",
  "respuesta": ""
}}
"""

    payload = {
        "model":
            clasificacion["modelo"],

        "think":
            False,

        "stream":
            False,

        "messages": [
            {
                "role":
                    "system",

                "content":
                    prompt,
            },
            {
                "role":
                    "user",

                "content":
                    objetivo,
            },
        ],

        "options": {
            "temperature":
                0.1,

            "num_ctx":
                768,

            "num_predict":
                300,
        },
    }

    response = requests.post(
        OLLAMA_URL + "/api/chat",
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    contenido = (
        response
        .json()
        .get("message", {})
        .get("content", "")
        .strip()
    )

    contenido = (
        contenido
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    inicio = contenido.find("{")
    fin = contenido.rfind("}")

    if inicio >= 0 and fin > inicio:

        contenido = contenido[
            inicio:fin + 1
        ]

    return json.loads(
        contenido
    )


def razonar(
    objetivo: str
) -> dict[str, Any]:

    clasificacion = clasificar(
        objetivo
    )

    contexto = contexto_minimo(
        objetivo
    )

    # --------------------------------------------------------
    # MEMORIA
    # --------------------------------------------------------

    if clasificacion["nivel"] == "memoria":

        experiencia = (
            clasificacion["experiencia"]
        )

        return {
            "tipo":
                "tarea",

            "origen":
                "memoria",

            "seleccion":
                clasificacion,

            "contexto":
                contexto,

            "plan": [
                {
                    "paso":
                        1,

                    "herramienta":
                        experiencia.get(
                            "herramienta"
                        ),

                    "argumentos":
                        experiencia.get(
                            "argumentos",
                            {}
                        ),

                    "motivo":
                        "Reutilizar una experiencia exitosa.",
                }
            ],

            "reflexion":
                {
                    "aprobado":
                        True,

                    "puntuacion":
                        100,

                    "problemas":
                        [],
                },

            "verificacion":
                "Comprobar el resultado nuevamente.",
        }

    # --------------------------------------------------------
    # RUTA LOCAL
    # --------------------------------------------------------

    local = plan_local(
        objetivo
    )

    if local is not None:

        local["contexto"] = (
            contexto
        )

        local["seleccion"] = (
            clasificacion
        )

        local["reflexion"] = (
            reflexion_local(
                local,
                contexto.get(
                    "estado_pc",
                    {}
                )
            )
        )

        return local

    # --------------------------------------------------------
    # IA
    # --------------------------------------------------------

    if clasificacion["usar_ia"]:

        try:

            plan = razonamiento_ia(
                objetivo,
                clasificacion,
                contexto
            )

            plan["contexto"] = (
                contexto
            )

            plan["seleccion"] = (
                clasificacion
            )

            plan["reflexion"] = (
                reflexion_local(
                    plan,
                    contexto.get(
                        "estado_pc",
                        {}
                    )
                )
            )

            return plan

        except Exception as exc:

            return {
                "tipo":
                    "error",

                "origen":
                    "ia",

                "seleccion":
                    clasificacion,

                "contexto":
                    contexto,

                "mensaje":
                    (
                        "La IA no respondió a tiempo. "
                        "El sistema rápido sigue disponible."
                    ),

                "error":
                    str(exc),
            }

    return {
        "tipo":
            "error",

        "mensaje":
            "No se pudo crear el plan.",
    }


if __name__ == "__main__":

    import sys

    if len(sys.argv) > 1:
        objetivo = " ".join(
            sys.argv[1:]
        )
    else:
        objetivo = input(
            "Objetivo JARVIS > "
        ).strip()

    if not objetivo:
        raise SystemExit(
            "No se proporcionó un objetivo."
        )

    resultado = razonar(
        objetivo
    )

    print(
        json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2
        )
    )
