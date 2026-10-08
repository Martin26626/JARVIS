from __future__ import annotations

import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "aprendizaje"
CACHE = DATA_DIR / "memoria_rapida.json"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


HERRAMIENTAS_SEGURAS = {
    "abrir_app",
    "abrir_ruta",
    "abrir_carpeta_especial",
    "buscar",
    "buscar_comprimidos",
    "crear_carpeta",
    "crear_archivo",
    "copiar",
    "mover",
    "renombrar",
    "extraer",
}


def _leer():
    if not CACHE.exists():
        return []

    try:
        data = json.loads(
            CACHE.read_text(
                encoding="utf-8-sig"
            )
        )

        return data if isinstance(
            data,
            list
        ) else []

    except Exception:
        return []


def _guardar(data):
    temporal = CACHE.with_suffix(
        ".tmp"
    )

    temporal.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    temporal.replace(CACHE)


def normalizar(texto):
    texto = str(texto).lower().strip()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    reemplazos = {
        "abrime": "abre",
        "abrir": "abre",
        "abrí": "abre",
        "lanzar": "abre",
        "lanza": "abre",
        "iniciar": "abre",
        "inicia": "abre",
        "ejecutar": "abre",
        "ejecuta": "abre",
    }

    for viejo, nuevo in reemplazos.items():
        texto = re.sub(
            rf"\b{re.escape(viejo)}\b",
            nuevo,
            texto
        )

    texto = re.sub(
        r"[¿?¡!.,;:]+",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def similitud(a, b):
    return SequenceMatcher(
        None,
        normalizar(a),
        normalizar(b)
    ).ratio()


def guardar(
    objetivo,
    herramienta,
    argumentos,
    resultado,
):
    if herramienta not in HERRAMIENTAS_SEGURAS:
        return

    datos = _leer()

    objetivo_n = normalizar(
        objetivo
    )

    for item in datos:

        if normalizar(
            item.get(
                "objetivo",
                ""
            )
        ) == objetivo_n:

            item["herramienta"] = herramienta
            item["argumentos"] = (
                argumentos or {}
            )
            item["resultado"] = str(
                resultado
            )

            _guardar(data)

            return

    datos.append({
        "objetivo": objetivo,
        "herramienta": herramienta,
        "argumentos":
            argumentos or {},
        "resultado":
            str(resultado),
        "veces_usado": 0,
    })

    datos = datos[-500:]

    _guardar(datos)


def buscar(
    objetivo,
    umbral=0.90,
):
    datos = _leer()

    mejor = None
    mejor_score = 0

    for item in datos:

        if item.get(
            "herramienta"
        ) not in HERRAMIENTAS_SEGURAS:
            continue

        score = similitud(
            objetivo,
            item.get(
                "objetivo",
                ""
            )
        )

        if score > mejor_score:

            mejor_score = score
            mejor = item

    if mejor is None:
        return None

    if mejor_score < umbral:
        return None

    resultado = dict(
        mejor
    )

    resultado["similitud"] = round(
        mejor_score,
        3
    )

    return resultado


def registrar_uso(
    objetivo
):
    datos = _leer()

    objetivo_n = normalizar(
        objetivo
    )

    for item in datos:

        if normalizar(
            item.get(
                "objetivo",
                ""
            )
        ) == objetivo_n:

            item["veces_usado"] = (
                int(
                    item.get(
                        "veces_usado",
                        0
                    )
                ) + 1
            )

            break

    _guardar(datos)


def listar():
    return _leer()


if __name__ == "__main__":
    print(
        json.dumps(
            listar(),
            ensure_ascii=False,
            indent=2
        )
    )
