from pathlib import Path
import ast
import json
import os
import re
import sys
import hashlib
import platform
import subprocess
from collections import Counter, defaultdict
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "AUDITORIA_JARVIS_COMPLETA.txt"

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
}

TEXT_EXTS = {
    ".py", ".json", ".txt", ".md", ".ini", ".cfg", ".conf",
    ".yaml", ".yml", ".ps1", ".bat", ".cmd", ".toml"
}

MODEL_EXTS = {
    ".onnx", ".pt", ".pth", ".bin", ".safetensors", ".gguf",
    ".ckpt", ".pb", ".tflite"
}

MEDIA_EXTS = {
    ".wav", ".mp3", ".ogg", ".flac", ".m4a", ".png", ".jpg",
    ".jpeg", ".webp", ".bmp", ".gif"
}

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)

def size_human(n):
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024:
            return f"{x:.2f} {u}"
        x /= 1024
    return f"{x:.2f} PB"

def sha256_file(p: Path):
    h = hashlib.sha256()
    try:
        with p.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()
    except Exception:
        return "ERROR"

def iter_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        try:
            parts = set(p.relative_to(ROOT).parts)
        except Exception:
            continue
        if parts & EXCLUDE_DIRS:
            continue
        yield p

files = sorted(iter_files(), key=lambda x: str(x).lower())
py_files = [p for p in files if p.suffix.lower() == ".py"]
text_files = [p for p in files if p.suffix.lower() in TEXT_EXTS]
model_files = [p for p in files if p.suffix.lower() in MODEL_EXTS]
media_files = [p for p in files if p.suffix.lower() in MEDIA_EXTS]

report = []

def H(title):
    report.append("\n" + "=" * 80)
    report.append(title)
    report.append("=" * 80)

def S(text=""):
    report.append(str(text))

# ------------------------------------------------------------
# SISTEMA
# ------------------------------------------------------------
H("1. INFORMACION DEL ENTORNO")

S(f"Fecha de auditoria: {datetime.now().isoformat()}")
S(f"Proyecto: {ROOT}")
S(f"Python ejecutado: {sys.executable}")
S(f"Python: {sys.version}")
S(f"Plataforma: {platform.platform()}")
S(f"Arquitectura: {platform.architecture()[0]}")
S(f"Procesador: {platform.processor()}")
S(f"Windows: {platform.win32_ver()}")

# ------------------------------------------------------------
# RESUMEN DE ARCHIVOS
# ------------------------------------------------------------
H("2. RESUMEN DE ARCHIVOS")

ext_counter = Counter()
total_bytes = 0

for p in files:
    ext_counter[p.suffix.lower() or "<sin extension>"] += 1
    try:
        total_bytes += p.stat().st_size
    except Exception:
        pass

S(f"Archivos totales: {len(files)}")
S(f"Archivos Python: {len(py_files)}")
S(f"Archivos texto/config: {len(text_files)}")
S(f"Modelos IA: {len(model_files)}")
S(f"Archivos multimedia: {len(media_files)}")
S(f"Tamano total: {size_human(total_bytes)}")
S("")
S("Extensiones:")
for ext, n in sorted(ext_counter.items(), key=lambda x: (-x[1], x[0])):
    S(f"  {ext}: {n}")

# ------------------------------------------------------------
# INVENTARIO COMPLETO
# ------------------------------------------------------------
H("3. INVENTARIO COMPLETO DEL PROYECTO")

for p in files:
    try:
        st = p.stat()
        S(
            f"{rel(p)} | {size_human(st.st_size)} | "
            f"modificado={datetime.fromtimestamp(st.st_mtime).isoformat()}"
        )
    except Exception:
        S(f"{rel(p)} | ERROR")

# ------------------------------------------------------------
# HASHES
# ------------------------------------------------------------
H("4. HASH SHA256 DE ARCHIVOS PYTHON")

for p in py_files:
    S(f"{rel(p)} | {sha256_file(p)}")

# ------------------------------------------------------------
# ANALISIS AST PYTHON
# ------------------------------------------------------------
H("5. ANALISIS PROFUNDO DE PYTHON")

all_imports = defaultdict(set)
local_imports = defaultdict(set)
external_imports = Counter()
functions_by_file = defaultdict(list)
classes_by_file = defaultdict(list)
methods_by_file = defaultdict(list)
globals_by_file = defaultdict(list)
syntax_errors = []
dangerous_calls = defaultdict(list)
urls_by_file = defaultdict(set)
env_vars_by_file = defaultdict(set)
todo_by_file = defaultdict(list)
strings_by_file = defaultdict(list)
decorators_by_file = defaultdict(list)

local_modules = set()
for p in py_files:
    local_modules.add(p.stem)

for p in py_files:
    relp = rel(p)

    try:
        source = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        syntax_errors.append((relp, f"No se pudo leer: {e}"))
        continue

    try:
        tree = ast.parse(source, filename=relp)
    except SyntaxError as e:
        syntax_errors.append((relp, f"{e.msg} linea={e.lineno} columna={e.offset}"))
        continue
    except Exception as e:
        syntax_errors.append((relp, f"{type(e).__name__}: {e}"))
        continue

    # URLs
    for m in re.findall(r'https?://[^\s\'"\)\]]+', source):
        urls_by_file[relp].add(m)

    # Variables de entorno
    for m in re.findall(
        r'os\.environ\.get\(\s*[\'"]([^\'"]+)[\'"]|'
        r'os\.getenv\(\s*[\'"]([^\'"]+)[\'"]|'
        r'environ\[\s*[\'"]([^\'"]+)[\'"]',
        source
    ):
        for item in m:
            if item:
                env_vars_by_file[relp].add(item)

    # TODO / FIXME / HACK / XXX
    for i, line in enumerate(source.splitlines(), 1):
        if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line, re.I):
            todo_by_file[relp].append(f"linea {i}: {line.strip()}")

    class Visitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                name = alias.name
                all_imports[relp].add(name)
                root_name = name.split(".")[0]
                if root_name in local_modules:
                    local_imports[relp].add(root_name)
                else:
                    external_imports[root_name] += 1
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            mod = node.module or ""
            all_imports[relp].add(mod)

            root_name = mod.split(".")[0] if mod else ""
            if root_name in local_modules:
                local_imports[relp].add(root_name)
            elif root_name:
                external_imports[root_name] += 1

            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            item = f"{node.name}() linea {node.lineno}"
            functions_by_file[relp].append(item)

            for deco in node.decorator_list:
                try:
                    decorators_by_file = decorators_by_file
                except Exception:
                    pass

            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            functions_by_file[relp].append(
                f"async {node.name}() linea {node.lineno}"
            )
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            classes_by_file[relp].append(
                f"{node.name} linea {node.lineno}"
            )
            self.generic_visit(node)

        def visit_Attribute(self, node):
            if node.attr in {
                "system", "popen", "run", "Popen", "call",
                "check_output", "eval", "exec"
            }:
                dangerous_calls[relp].append(
                    f"{node.attr}() linea {getattr(node, 'lineno', '?')}"
                )
            self.generic_visit(node)

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec"}:
                    dangerous_calls[relp].append(
                        f"{node.func.id}() linea {node.lineno}"
                    )
            self.generic_visit(node)

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id.isupper() or target.id.startswith("_"):
                        globals_by_file[relp].append(
                            f"{target.id} linea {node.lineno}"
                        )
            self.generic_visit(node)

    Visitor().visit(tree)

    # strings interesantes
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.strip()
            if (
                len(value) >= 4
                and any(k in value.lower() for k in [
                    "ollama", "whisper", "kokoro", "piper",
                    "whatsapp", "telegram", "selenium",
                    "jarvis", "titan", "http://", "https://"
                ])
            ):
                strings_by_file[relp].append(value[:250])

    # decorators, separadamente
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for deco in node.decorator_list:
                try:
                    decorators_by_file.setdefault(relp, []).append(
                        ast.unparse(deco)
                    )
                except Exception:
                    pass

for p in py_files:
    relp = rel(p)
    S("")
    S(f"--- {relp} ---")
    if functions_by_file[relp]:
        S("Funciones:")
        for x in functions_by_file[relp]:
            S(f"  {x}")
    else:
        S("Funciones: ninguna")

    if classes_by_file[relp]:
        S("Clases:")
        for x in classes_by_file[relp]:
            S(f"  {x}")
    else:
        S("Clases: ninguna")

    if all_imports[relp]:
        S("Imports:")
        for x in sorted(all_imports[relp]):
            S(f"  {x}")

    if local_imports[relp]:
        S("Dependencias locales:")
        for x in sorted(local_imports[relp]):
            S(f"  {x}")

    if globals_by_file[relp]:
        S("Constantes/variables destacadas:")
        for x in globals_by_file[relp][:200]:
            S(f"  {x}")

    if decorators_by_file.get(relp):
        S("Decoradores:")
        for x in sorted(set(decorators_by_file[relp])):
            S(f"  {x}")

# ------------------------------------------------------------
# IMPORTS EXTERNOS
# ------------------------------------------------------------
H("6. MODULOS EXTERNOS DETECTADOS")

for mod, n in sorted(external_imports.items(), key=lambda x: (-x[1], x[0])):
    S(f"{mod} | referencias={n}")

# ------------------------------------------------------------
# DEPENDENCIAS LOCALES / GRAFO
# ------------------------------------------------------------
H("7. GRAFO DE MODULOS LOCALES")

for src in sorted(local_imports):
    deps = ", ".join(sorted(local_imports[src]))
    S(f"{src} -> {deps or '(ninguna)'}")

# módulos aparentemente no conectados
referenced_local = set()
for deps in local_imports.values():
    referenced_local |= deps

candidates = []
for mod in sorted(local_modules):
    if mod == "__init__":
        continue
    imported_by_anyone = any(mod in deps for deps in local_imports.values())
    if not imported_by_anyone and mod not in {"jarvis"}:
        candidates.append(mod)

H("8. MODULOS LOCALES APARENTEMENTE NO IMPORTADOS")
for mod in candidates:
    S(f"{mod}.py")
if not candidates:
    S("(ninguno detectado por analisis estatico)")

# ------------------------------------------------------------
# DUPLICADOS
# ------------------------------------------------------------
H("9. FUNCIONES DUPLICADAS ENTRE ARCHIVOS")

function_names = defaultdict(list)

for p in py_files:
    relp = rel(p)
    for item in functions_by_file[relp]:
        name = item.split("(")[0].replace("async ", "").strip()
        function_names[name].append(relp)

dupes_found = False
for name, locations in sorted(function_names.items()):
    if len(locations) > 1:
        dupes_found = True
        S(f"{name} -> {', '.join(sorted(set(locations)))}")

if not dupes_found:
    S("(ninguna detectada)")

# ------------------------------------------------------------
# SYNTAX
# ------------------------------------------------------------
H("10. ERRORES DE SINTAXIS / LECTURA")

if syntax_errors:
    for path, err in syntax_errors:
        S(f"{path} -> {err}")
else:
    S("Todos los .py pudieron analizarse correctamente.")

# ------------------------------------------------------------
# LLAMADAS ESPECIALES
# ------------------------------------------------------------
H("11. LLAMADAS SENSIBLES / EJECUCION EXTERNA")

for path, calls in dangerous_calls.items():
    S(f"--- {path} ---")
    for c in sorted(set(calls)):
        S(f"  {c}")

if not dangerous_calls:
    S("(ninguna detectada)")

# ------------------------------------------------------------
# URLS
# ------------------------------------------------------------
H("12. URLS Y SERVICIOS DETECTADOS")

for path in sorted(urls_by_file):
    S(f"--- {path} ---")
    for u in sorted(urls_by_file[path]):
        S(f"  {u}")

# ------------------------------------------------------------
# VARIABLES DE ENTORNO
# ------------------------------------------------------------
H("13. VARIABLES DE ENTORNO UTILIZADAS")

for path in sorted(env_vars_by_file):
    S(f"--- {path} ---")
    for v in sorted(env_vars_by_file[path]):
        S(f"  {v}")

# ------------------------------------------------------------
# TODO / FIXME
# ------------------------------------------------------------
H("14. TODO / FIXME / HACK / XXX")

if todo_by_file:
    for path in sorted(todo_by_file):
        S(f"--- {path} ---")
        for line in todo_by_file[path]:
            S(f"  {line}")
else:
    S("(ninguno detectado)")

# ------------------------------------------------------------
# MODELOS
# ------------------------------------------------------------
H("15. MODELOS Y ARCHIVOS IA")

if model_files:
    for p in model_files:
        try:
            st = p.stat()
            S(f"{rel(p)} | {size_human(st.st_size)}")
        except Exception:
            S(f"{rel(p)} | ERROR")
else:
    S("(no se encontraron extensiones de modelos conocidas)")

# ------------------------------------------------------------
# MULTIMEDIA
# ------------------------------------------------------------
H("16. RECURSOS MULTIMEDIA")

if media_files:
    for p in media_files:
        try:
            st = p.stat()
            S(f"{rel(p)} | {size_human(st.st_size)}")
        except Exception:
            S(f"{rel(p)} | ERROR")
else:
    S("(no se encontraron archivos multimedia)")

# ------------------------------------------------------------
# CONFIG.JSON
# ------------------------------------------------------------
H("17. ANALISIS DE CONFIGURACION")

config_files = list(ROOT.rglob("config.json"))

if config_files:
    for p in config_files:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            S(f"Archivo: {rel(p)}")
            S("Claves:")
            if isinstance(data, dict):
                for k, v in sorted(data.items()):
                    # ocultar valores que parezcan secretos
                    keylow = str(k).lower()
                    if any(x in keylow for x in ["token", "password", "clave", "secret", "api_key", "apikey"]):
                        shown = "***REDACTADO***"
                    elif isinstance(v, (dict, list)):
                        shown = f"<{type(v).__name__}>"
                    else:
                        shown = repr(v)
                    S(f"  {k} = {shown}")
            else:
                S(f"Tipo raiz: {type(data).__name__}")
        except Exception as e:
            S(f"{rel(p)} -> ERROR: {e}")
else:
    S("No se encontro config.json")

# ------------------------------------------------------------
# REQUIREMENTS
# ------------------------------------------------------------
H("18. REQUIREMENTS")

req = ROOT / "requirements.txt"
if req.exists():
    try:
        for i, line in enumerate(
            req.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if line.strip():
                S(f"{i}: {line}")
    except Exception as e:
        S(f"ERROR leyendo requirements.txt: {e}")
else:
    S("No existe requirements.txt")

# ------------------------------------------------------------
# BACKUPS
# ------------------------------------------------------------
H("19. BACKUPS DEL PROYECTO")

backups = []
for p in files:
    if "backup" in p.name.lower() or "bak" in p.name.lower():
        backups.append(p)

if backups:
    for p in backups:
        S(rel(p))
else:
    S("(ningun backup detectado por nombre)")

# ------------------------------------------------------------
# JARVIS / OLLAMA / SERVICIOS
# ------------------------------------------------------------
H("20. REFERENCIAS A COMPONENTES CLAVE")

keywords = [
    "ollama", "whisper", "kokoro", "piper", "sounddevice",
    "selenium", "whatsapp", "telegram", "openai", "huggingface",
    "transformers", "diffusers", "tkinter", "pyautogui",
    "pywinauto", "keyboard", "psutil", "pywin32", "web",
    "memoria", "aprendizaje", "verificador", "planificador",
    "cerebro", "agente", "herramientas"
]

for p in py_files:
    try:
        source = p.read_text(encoding="utf-8", errors="replace").lower()
    except Exception:
        continue

    found = [k for k in keywords if k in source]
    if found:
        S(f"{rel(p)} -> {', '.join(found)}")

# ------------------------------------------------------------
# GIT
# ------------------------------------------------------------
H("21. ESTADO GIT")

git_dir = ROOT / ".git"

if git_dir.exists():
    try:
        r = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        S("git status --short:")
        S(r.stdout.strip() or "(limpio)")
    except Exception as e:
        S(f"No se pudo consultar Git: {e}")

    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        S(f"Rama: {r.stdout.strip()}")
    except Exception:
        pass
else:
    S("No hay carpeta .git")

# ------------------------------------------------------------
# POSIBLES ENTRADAS
# ------------------------------------------------------------
H("22. ARCHIVOS CANDIDATOS A PUNTO DE ENTRADA")

entry_candidates = [
    p for p in py_files
    if p.name.lower() in {
        "jarvis.py",
        "main.py",
        "__main__.py",
        "app.py",
        "run.py",
        "start.py"
    }
]

if entry_candidates:
    for p in entry_candidates:
        S(rel(p))
else:
    S("(no se detectaron nombres de entrada comunes)")

# ------------------------------------------------------------
# ESTADISTICAS FINALES
# ------------------------------------------------------------
H("23. ESTADISTICAS FINALES")

total_functions = sum(len(v) for v in functions_by_file.values())
total_classes = sum(len(v) for v in classes_by_file.values())
total_imports = sum(len(v) for v in all_imports.values())
total_local_imports = sum(len(v) for v in local_imports.values())

S(f"Archivos totales: {len(files)}")
S(f"Python: {len(py_files)}")
S(f"Funciones/metodos detectados: {total_functions}")
S(f"Clases detectadas: {total_classes}")
S(f"Imports unicos por archivo: {total_imports}")
S(f"Dependencias locales detectadas: {total_local_imports}")
S(f"Errores de sintaxis/lectura: {len(syntax_errors)}")
S(f"Modulos aparentemente desconectados: {len(candidates)}")
S(f"Archivos de modelos: {len(model_files)}")
S(f"Recursos multimedia: {len(media_files)}")
S(f"Backups detectados: {len(backups)}")

H("24. FIN DE AUDITORIA")

S("Esta auditoria es estatica: inspecciona el proyecto sin ejecutar jarvis.py.")
S("No prueba por si sola el comportamiento real de cada funcion.")
S("Los modulos aparentemente desconectados son candidatos, no una prueba de que sean inutiles.")

OUT.write_text("\n".join(report), encoding="utf-8")

print("")
print("=" * 70)
print("AUDITORIA JARVIS COMPLETADA")
print("=" * 70)
print(f"Reporte: {OUT}")
print(f"Archivos: {len(files)}")
print(f"Python: {len(py_files)}")
print(f"Funciones/metodos: {total_functions}")
print(f"Clases: {total_classes}")
print(f"Errores de sintaxis: {len(syntax_errors)}")
print(f"Modulos aparentemente desconectados: {len(candidates)}")
print("=" * 70)
