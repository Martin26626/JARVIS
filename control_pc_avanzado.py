from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from pathlib import Path


def _powershell_value(comando: str):
    try:
        resultado = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                comando,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="ignore",
        )

        if resultado.returncode != 0:
            return None

        valor = resultado.stdout.strip()

        return valor or None

    except Exception:
        return None


def obtener_nombre_cpu() -> str:
    # Método principal: Win32_Processor
    valor = _powershell_value(
        "(Get-CimInstance Win32_Processor).Name"
    )

    if valor:
        return valor

    # Respaldo
    valor = _powershell_value(
        "(Get-WmiObject Win32_Processor).Name"
    )

    if valor:
        return valor

    return platform.processor() or "Desconocido"


def obtener_gpu() -> list[str]:
    try:
        resultado = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_VideoController).Name",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="ignore",
        )

        if resultado.returncode != 0:
            return []

        return [
            linea.strip()
            for linea in resultado.stdout.splitlines()
            if linea.strip()
        ]

    except Exception:
        return []


def informacion_sistema():

    informacion = {
        "computadora":
            os.environ.get(
                "COMPUTERNAME",
                ""
            ),

        "usuario":
            os.environ.get(
                "USERNAME",
                ""
            ),

        "windows":
            os.environ.get(
                "OS",
                ""
            ),

        "cpu":
            obtener_nombre_cpu(),

        "gpus":
            obtener_gpu(),
    }

    try:

        import psutil

        memoria = psutil.virtual_memory()

        informacion["ram_total_gb"] = round(
            memoria.total / (1024 ** 3),
            2
        )

        informacion["ram_disponible_gb"] = round(
            memoria.available / (1024 ** 3),
            2
        )

        informacion["ram_usable_gb"] = round(
            memoria.total / (1024 ** 3),
            2
        )

        informacion["cpu_porcentaje"] = round(
            psutil.cpu_percent(
                interval=0.5
            ),
            1
        )

        informacion["nucleos"] = (
            psutil.cpu_count(
                logical=False
            )
        )

        informacion["hilos"] = (
            psutil.cpu_count(
                logical=True
            )
        )

    except Exception as exc:

        informacion["error_psutil"] = str(
            exc
        )

    return informacion


if __name__ == "__main__":

    print(
        json.dumps(
            informacion_sistema(),
            ensure_ascii=False,
            indent=2
        )
    )

def listar_ventanas():
    try:
        import win32gui
    except ImportError:
        return {
            "error": "pywin32 no esta instalado."
        }

    ventanas = []

    def callback(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return

            titulo = win32gui.GetWindowText(hwnd).strip()

            if not titulo:
                return

            ventanas.append({
                "hwnd": hwnd,
                "titulo": titulo,
            })

        except Exception:
            pass

    win32gui.EnumWindows(callback, None)

    return ventanas


def buscar_ventana(titulo):
    objetivo = str(titulo).lower().strip()

    ventanas = listar_ventanas()

    if not isinstance(ventanas, list):
        return None

    for ventana in ventanas:
        if objetivo in ventana.get(
            "titulo",
            ""
        ).lower():
            return ventana

    return None


def enfocar_ventana(titulo):
    try:
        import win32gui
        import win32con
    except ImportError:
        return "ERROR: pywin32 no esta instalado."

    ventana = buscar_ventana(titulo)

    if not ventana:
        return f"No encontre la ventana: {titulo}"

    try:
        win32gui.ShowWindow(
            ventana["hwnd"],
            win32con.SW_RESTORE
        )

        win32gui.SetForegroundWindow(
            ventana["hwnd"]
        )

        return (
            "Ventana enfocada: "
            + ventana["titulo"]
        )

    except Exception as exc:
        return f"ERROR enfocando ventana: {exc}"


def minimizar_ventana(titulo):
    try:
        import win32gui
        import win32con
    except ImportError:
        return "ERROR: pywin32 no esta instalado."

    ventana = buscar_ventana(titulo)

    if not ventana:
        return f"No encontre la ventana: {titulo}"

    try:
        win32gui.ShowWindow(
            ventana["hwnd"],
            win32con.SW_MINIMIZE
        )

        return (
            "Ventana minimizada: "
            + ventana["titulo"]
        )

    except Exception as exc:
        return f"ERROR minimizando ventana: {exc}"


def maximizar_ventana(titulo):
    try:
        import win32gui
        import win32con
    except ImportError:
        return "ERROR: pywin32 no esta instalado."

    ventana = buscar_ventana(titulo)

    if not ventana:
        return f"No encontre la ventana: {titulo}"

    try:
        win32gui.ShowWindow(
            ventana["hwnd"],
            win32con.SW_MAXIMIZE
        )

        win32gui.SetForegroundWindow(
            ventana["hwnd"]
        )

        return (
            "Ventana maximizada: "
            + ventana["titulo"]
        )

    except Exception as exc:
        return f"ERROR maximizando ventana: {exc}"


def cerrar_ventana(titulo):
    try:
        import win32gui
        import win32con
    except ImportError:
        return "ERROR: pywin32 no esta instalado."

    ventana = buscar_ventana(titulo)

    if not ventana:
        return f"No encontre la ventana: {titulo}"

    try:
        win32gui.PostMessage(
            ventana["hwnd"],
            win32con.WM_CLOSE,
            0,
            0
        )

        return (
            "Cierre solicitado para: "
            + ventana["titulo"]
        )

    except Exception as exc:
        return f"ERROR cerrando ventana: {exc}"

import psutil

def listar_procesos(filtro=None, limite=30):

    procesos = []

    for proceso in psutil.process_iter(
        ["pid", "name", "memory_info"]
    ):

        try:
            nombre = proceso.info["name"] or ""

            if filtro and filtro.lower() not in nombre.lower():
                continue

            memoria_mb = round(
                proceso.info["memory_info"].rss / 1024 / 1024,
                1
            )

            procesos.append({
                "pid": proceso.info["pid"],
                "nombre": nombre,
                "ram_mb": memoria_mb,
            })

        except Exception:
            continue

    procesos.sort(
        key=lambda x: x["ram_mb"],
        reverse=True
    )

    return procesos[:int(limite)]
