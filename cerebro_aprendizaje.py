from __future__ import annotations

import json
import os
import requests

import aprendizaje


OLLAMA_URL = os.environ.get(
    "JARVIS_OLLAMA_URL",
    "http://127.0.0.1:11434"
)


MODELOS_PREFERIDOS = [
    os.environ.get(
        "JARVIS_MODEL",
        ""
    ),
    "qwen3:8b",
    "qwen2.5-coder:7b",
]


HERRAMIENTAS = {
    "abrir_app":
        "abre cualquier aplicacion instalada",

    "abrir_ruta":
        "abre un archivo o carpeta",

    "abrir_carpeta_especial":
        "abre Escritorio, Descargas, Documentos, Imagenes o Videos",

    "abrir_explorador":
        "abre el Explorador de archivos",

    "abrir_terminal":
        "abre la terminal de Windows",

    "mover":
        "mueve archivos o carpetas",

    "copiar":
        "copia archivos o carpetas",

    "renombrar":
        "renombra archivos o carpetas",

    "crear_carpeta":
        "crea una carpeta",

    "crear_archivo":
        "crea un archivo",

    "buscar":
        "busca archivos por nombre",

    "buscar_comprimidos":
        "busca RAR ZIP 7Z y otros comprimidos",

    "extraer":
        "extrae archivos comprimidos",

    "eliminar":
        "elimina un archivo o carpeta",

    "listar_apps":
        "lista aplicaciones instaladas",

    "buscar_app":
        "busca una aplicacion instalada",

    "listar_procesos":
        "lista procesos activos",

    "proceso_existe":
        "comprueba si un proceso esta abierto",

    "cerrar_proceso":
        "cierra un proceso",

    "listar_ventanas":
        "lista ventanas abiertas",

    "enfocar_ventana":
        "lleva una ventana al frente",

    "minimizar_ventana":
        "minimiza una ventana",

    "maximizar_ventana":
        "maximiza una ventana",

    "cerrar_ventana":
        "cierra una ventana",

    "escribir":
        "escribe texto usando el teclado",

    "tecla":
        "presiona una tecla",

    "click":
        "hace click con el raton",

    "doble_click":
        "hace doble click",

    "mover_mouse":
        "mueve el raton",

    "scroll":
        "hace scroll",

    "captura_pantalla":
        "captura la pantalla",

    "posicion_mouse":
        "dice la posicion actual del raton",

    "informacion_sistema":
        "muestra informacion del PC",
}


def modelos():

    try:

        response = requests.get(
            OLLAMA_URL + "/api/tags",
            timeout=5
        )

        response.raise_for_status()

        return [
            modelo.get("name")
            for modelo in response.json().get(
                "models",
                []
            )
            if modelo.get("name")
        ]

    except Exception:
        return []


def elegir_modelo():

    disponibles = modelos()

    for preferido in MODELOS_PREFERIDOS:

        if not preferido:
            continue

        if preferido in disponibles:
            return preferido

        base = preferido.split(":")[0]

        for modelo in disponibles:

            if modelo.startswith(
                base + ":"
            ):
                return modelo

    if disponibles:
        return disponibles[0]

    return "qwen3:8b"


def pensar(
    objetivo,
    error_anterior=None,
    plan_anterior=None,
):

    contexto = aprendizaje.contexto_para_jarvis(
        objetivo
    )

    memoria = json.dumps(
        contexto,
        ensure_ascii=False,
        indent=2
    )

    herramientas = json.dumps(
        HERRAMIENTAS,
        ensure_ascii=False,
        indent=2
    )

    correccion = ""

    if error_anterior:

        correccion = f"""
La estrategia anterior fallo.

ERROR:
{error_anterior}

PLAN ANTERIOR:
{plan_anterior}

Debes buscar una estrategia diferente.
"""

    prompt = f"""
Eres el cerebro de JARVIS.

Tu trabajo es comprender objetivos,
razonar, planificar, elegir herramientas,
ejecutarlas mediante otro modulo y aprender
de los resultados.

No simules emociones.
No inventes resultados.

MEMORIA:
{memoria}

HERRAMIENTAS DISPONIBLES:
{herramientas}

{correccion}

Devuelve SOLO JSON valido.

Para conversar:

{{
  "tipo": "conversacion",
  "respuesta": "respuesta"
}}

Para ejecutar:

{{
  "tipo": "plan",
  "objetivo": "objetivo resumido",
  "acciones": [
    {{
      "herramienta": "informacion_sistema",
      "argumentos": {{}}
    }}
  ],
  "respuesta_final": "respuesta breve"
}}

REGLAS:

1. Comprende la intencion, no solo las palabras exactas.
2. Elige la herramienta correcta.
3. Puedes usar varias herramientas en una tarea.
4. Usa experiencias aprendidas cuando sean relevantes.
5. Si una estrategia fallo, busca otra.
6. No inventes aplicaciones.
7. No inventes rutas.
8. No inventes resultados.
9. No elimines archivos automaticamente.
10. Las acciones sensibles deben poder confirmarse.
11. Usa la menor cantidad de acciones necesarias.
12. Cuando una herramienta devuelve datos reales del PC,
    utiliza esos datos literalmente.
13. No inventes numeros, nombres de hardware ni resultados.
14. Si una herramienta devuelve un diccionario con datos,
    basa la respuesta final exclusivamente en ese resultado.
15. Si el resultado contiene 'cpu', 'ram_total_gb' o 'gpus',
    utiliza esos valores reales.


OBJETIVO:
{objetivo}
"""

    payload = {
        "model":
            elegir_modelo(),

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

        "think": False,

        "options": {
            "temperature": 0.1,
            "num_ctx": 2048,
            "num_predict": 512,
        }
    }

    response = requests.post(
        OLLAMA_URL + "/api/chat",
        json=payload,
        timeout=180
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

    try:

        return json.loads(
            contenido
        )

    except Exception:

        return {
            "tipo":
                "conversacion",

            "respuesta":
                contenido,
        }
