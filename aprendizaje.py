from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "aprendizaje"

DATA_DIR.mkdir(parents=True, exist_ok=True)

EXPERIENCIAS = DATA_DIR / "experiencias.json"
PREFERENCIAS = DATA_DIR / "preferencias.json"
CONOCIMIENTO = DATA_DIR / "conocimiento.json"


def _leer(path, defecto):
    if not path.exists():
        return defecto

    try:
        texto = path.read_text(
            encoding="utf-8-sig"
        )

        if not texto.strip():
            return defecto

        return json.loads(texto)

    except Exception:
        return defecto


def _guardar(path, data):
    temporal = path.with_suffix(".tmp")

    temporal.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    temporal.replace(path)


def normalizar(texto):
    texto = str(texto).strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto


def registrar_experiencia(
    objetivo,
    herramienta,
    argumentos,
    resultado,
    correcto,
    error=None,
):
    experiencias = _leer(
        EXPERIENCIAS,
        []
    )

    experiencias.append({
        "fecha": datetime.now().isoformat(),
        "objetivo": objetivo,
        "herramienta": herramienta,
        "argumentos": argumentos or {},
        "resultado": str(resultado),
        "correcto": bool(correcto),
        "error": error,
    })

    experiencias = experiencias[-1000:]

    _guardar(
        EXPERIENCIAS,
        experiencias
    )


def aprender(
    objetivo,
    herramienta,
    argumentos,
    resultado,
    correcto,
    error=None,
):
    registrar_experiencia(
        objetivo,
        herramienta,
        argumentos,
        resultado,
        correcto,
        error,
    )


def registrar_conocimiento(
    clave,
    valor,
):
    conocimiento = _leer(
        CONOCIMIENTO,
        {}
    )

    conocimiento[str(clave)] = {
        "valor": valor,
        "fecha": datetime.now().isoformat(),
    }

    _guardar(
        CONOCIMIENTO,
        conocimiento
    )


def aprender_de_usuario(texto):
    patrones = [
        r"^recordá que (.+)$",
        r"^recuerda que (.+)$",
        r"^a partir de ahora (.+)$",
        r"^desde ahora (.+)$",
        r"^siempre (.+)$",
    ]

    texto = str(texto).strip()

    for patron in patrones:

        m = re.match(
            patron,
            texto,
            re.IGNORECASE
        )

        if m:

            informacion = (
                m.group(1)
                .strip()
            )

            registrar_conocimiento(
                normalizar(informacion),
                informacion
            )

            return informacion

    return None


def buscar_experiencias(
    consulta,
    limite=8,
):
    consulta = normalizar(
        consulta
    )

    experiencias = _leer(
        EXPERIENCIAS,
        []
    )

    palabras = [
        p for p in consulta.split()
        if len(p) > 2
    ]

    resultados = []

    for experiencia in experiencias:

        texto = normalizar(
            " ".join([
                str(
                    experiencia.get(
                        "objetivo",
                        ""
                    )
                ),
                str(
                    experiencia.get(
                        "herramienta",
                        ""
                    )
                ),
                str(
                    experiencia.get(
                        "argumentos",
                        ""
                    )
                ),
                str(
                    experiencia.get(
                        "resultado",
                        ""
                    )
                ),
            ])
        )

        puntuacion = sum(
            1
            for palabra in palabras
            if palabra in texto
        )

        if puntuacion:

            resultados.append(
                (
                    puntuacion,
                    experiencia
                )
            )

    resultados.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        item
        for _, item in resultados[:limite]
    ]


def contexto_para_jarvis(
    consulta
):
    return {
        "experiencias":
            buscar_experiencias(
                consulta
            ),
        "preferencias":
            _leer(
                PREFERENCIAS,
                {}
            ),
        "conocimiento":
            _leer(
                CONOCIMIENTO,
                {}
            ),
    }


def estadisticas():
    experiencias = _leer(
        EXPERIENCIAS,
        []
    )

    exitos = sum(
        1
        for e in experiencias
        if e.get("correcto")
    )

    fallos = (
        len(experiencias)
        - exitos
    )

    return {
        "experiencias":
            len(experiencias),
        "exitos":
            exitos,
        "fallos":
            fallos,
        "tasa_exito":
            round(
                exitos / len(experiencias),
                3
            )
            if experiencias
            else 0,
    }


if __name__ == "__main__":
    print(
        json.dumps(
            estadisticas(),
            ensure_ascii=False,
            indent=2
        )
    )
