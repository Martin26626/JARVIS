from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
import glob
from pathlib import Path
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None


# ============================================================
# CONFIG
# ============================================================

HOME = Path.home()
DESKTOP = HOME / "Desktop"
ONEDRIVE_DESKTOP = HOME / "OneDrive" / "Desktop"
DOWNLOADS = HOME / "Downloads"
DOCUMENTS = HOME / "Documents"
PICTURES = HOME / "Pictures"
VIDEOS = HOME / "Videos"

COMMON_APP_DIRS = [
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    Path(os.environ.get("LOCALAPPDATA", str(HOME / "AppData" / "Local"))),
    Path(os.environ.get("APPDATA", str(HOME / "AppData" / "Roaming"))),
    Path(r"C:\ProgramData"),
]

START_MENU_DIRS = [
    Path(os.environ.get("APPDATA", "")) /
    "Microsoft" / "Windows" / "Start Menu" / "Programs",
    Path(os.environ.get("ProgramData", r"C:\ProgramData")) /
    "Microsoft" / "Windows" / "Start Menu" / "Programs",
]

ARCHIVE_EXTENSIONS = {".rar", ".zip", ".7z", ".tar", ".gz", ".bz2", ".xz"}
EXECUTABLE_EXTENSIONS = {".exe", ".com", ".bat", ".cmd", ".py", ".lnk"}

APP_ALIASES = {
    "opera": ["opera gx", "opera"],
    "opera gx": ["opera gx", "opera"],
    "explorador": ["file explorer", "explorer"],
    "explorador de archivos": ["file explorer", "explorer"],
    "bloc de notas": ["notepad"],
    "notepad": ["notepad"],
    "calculadora": ["calculator"],
    "calculator": ["calculator"],
    "steam": ["steam"],
    "discord": ["discord"],
    "obs": ["obs", "obs studio"],
    "obs studio": ["obs", "obs studio"],
    "roblox": ["roblox"],
}


# ============================================================
# HELPERS
# ============================================================

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip()).lower()


def _expand_path(value: str | Path) -> Path:
    text = os.path.expandvars(os.path.expanduser(str(value).strip().strip('"')))

    replacements = {
        "%desktop%": str(DESKTOP),
        "%onedrive_desktop%": str(ONEDRIVE_DESKTOP),
        "%downloads%": str(DOWNLOADS),
        "%documents%": str(DOCUMENTS),
        "%pictures%": str(PICTURES),
        "%videos%": str(VIDEOS),
    }

    low = text.lower()

    for key, replacement in replacements.items():
        if low.startswith(key):
            text = replacement + text[len(key):]
            break

    return Path(text)


def _candidate_desktops() -> list[Path]:
    result = []

    for path in [DESKTOP, ONEDRIVE_DESKTOP]:
        if path.exists() and path not in result:
            result.append(path)

    return result


def _run_hidden(command: list[str]) -> subprocess.CompletedProcess:
    startupinfo = None

    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    return subprocess.run(
        command,
        startupinfo=startupinfo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def _normalize_name(name: str) -> str:
    name = _clean(name)
    name = re.sub(r"\.(exe|lnk|bat|cmd)$", "", name)
    return name


# ============================================================
# FILES AND FOLDERS
# ============================================================

def path_exists(path: str) -> bool:
    return _expand_path(path).exists()


def create_folder(path: str) -> str:
    target = _expand_path(path)
    target.mkdir(parents=True, exist_ok=True)
    return f"Folder created: {target}"


def create_file(path: str, content: str = "") -> str:
    target = _expand_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"File created: {target}"


def copy_item(source: str, destination: str) -> str:
    src = _expand_path(source)
    dst = _expand_path(destination)

    if not src.exists():
        return f"Source not found: {src}"

    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.is_dir():
        final = dst / src.name if dst.exists() and dst.is_dir() else dst
        shutil.copytree(src, final, dirs_exist_ok=True)
    else:
        final = dst / src.name if dst.exists() and dst.is_dir() else dst
        shutil.copy2(src, final)

    return f"Copied: {src} -> {final}"


def move_item(source: str, destination: str) -> str:
    src = _expand_path(source)
    dst = _expand_path(destination)

    if not src.exists():
        return f"Source not found: {src}"

    dst.parent.mkdir(parents=True, exist_ok=True)

    final = dst / src.name if dst.exists() and dst.is_dir() else dst
    shutil.move(str(src), str(final))

    return f"Moved: {src} -> {final}"


def rename_item(source: str, new_name: str) -> str:
    src = _expand_path(source)

    if not src.exists():
        return f"Source not found: {src}"

    new_name = str(new_name).strip()
    final = src.parent / new_name

    if final.exists():
        return f"Destination already exists: {final}"

    src.rename(final)
    return f"Renamed: {src.name} -> {final.name}"


def delete_item(path: str) -> str:
    target = _expand_path(path)

    if not target.exists():
        return f"Not found: {target}"

    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()

    return f"Deleted: {target}"


def open_path(path: str) -> str:
    target = _expand_path(path)

    if not target.exists():
        return f"Not found: {target}"

    os.startfile(str(target))
    return f"Opened: {target}"


def reveal_in_explorer(path: str) -> str:
    target = _expand_path(path)

    if not target.exists():
        return f"Not found: {target}"

    if target.is_file():
        subprocess.Popen(["explorer.exe", "/select,", str(target)])
    else:
        subprocess.Popen(["explorer.exe", str(target)])

    return f"Shown in Explorer: {target}"


def search_files(
    query: str,
    root: str | None = None,
    extension: str | None = None,
    max_results: int = 100,
) -> list[str]:
    root_path = _expand_path(root) if root else ONEDRIVE_DESKTOP

    if not root_path.exists():
        root_path = DESKTOP

    query_clean = _clean(query)
    ext_clean = ""

    if extension:
        ext_clean = extension.lower().strip()
        if not ext_clean.startswith("."):
            ext_clean = "." + ext_clean

    results = []

    for current_root, dirs, files in os.walk(root_path):
        dirs[:] = [
            d for d in dirs
            if d not in {
                "$Recycle.Bin",
                "System Volume Information",
                "node_modules",
                "__pycache__",
            }
        ]

        for filename in files:
            if ext_clean and Path(filename).suffix.lower() != ext_clean:
                continue

            if query_clean and query_clean not in _clean(filename):
                continue

            results.append(str(Path(current_root) / filename))

            if len(results) >= max_results:
                return results

    return results


def find_archives(
    root: str | None = None,
    max_results: int = 100,
) -> list[str]:
    results = []
    root_path = _expand_path(root) if root else DOWNLOADS

    if not root_path.exists():
        return results

    for current_root, dirs, files in os.walk(root_path):
        for filename in files:
            if Path(filename).suffix.lower() in ARCHIVE_EXTENSIONS:
                results.append(str(Path(current_root) / filename))

                if len(results) >= max_results:
                    return results

    return results


# ============================================================
# ARCHIVES
# ============================================================

def find_7zip() -> Optional[str]:
    candidates = [
        Path(r"C:\Program Files\7-Zip\7z.exe"),
        Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "7-Zip" / "7z.exe",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    try:
        result = _run_hidden(["where", "7z"])
        if result.returncode == 0:
            line = result.stdout.strip().splitlines()
            if line:
                return line[0].strip()
    except Exception:
        pass

    return None


def find_winrar() -> Optional[str]:
    candidates = [
        Path(r"C:\Program Files\WinRAR\WinRAR.exe"),
        Path(r"C:\Program Files (x86)\WinRAR\WinRAR.exe"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    try:
        result = _run_hidden(["where", "winrar"])
        if result.returncode == 0:
            line = result.stdout.strip().splitlines()
            if line:
                return line[0].strip()
    except Exception:
        pass

    return None


def extract_archive(archive: str, destination: str | None = None) -> str:
    src = _expand_path(archive)

    if not src.exists():
        return f"Archive not found: {src}"

    if src.suffix.lower() not in ARCHIVE_EXTENSIONS:
        return f"Not a supported archive: {src}"

    dest = _expand_path(destination) if destination else src.parent / src.stem
    dest.mkdir(parents=True, exist_ok=True)

    seven_zip = find_7zip()

    if seven_zip:
        result = _run_hidden([
            seven_zip,
            "x",
            str(src),
            f"-o{dest}",
            "-y",
        ])

        if result.returncode == 0:
            return f"Archive extracted to: {dest}"

    winrar = find_winrar()

    if winrar:
        result = _run_hidden([
            winrar,
            "x",
            "-y",
            str(src),
            str(dest) + "\\",
        ])

        if result.returncode == 0:
            return f"Archive extracted to: {dest}"

    return (
        "I found the archive, but 7-Zip or WinRAR was not found. "
        "Install one of them to extract RAR/ZIP/7Z files automatically."
    )


# ============================================================
# APPLICATION DISCOVERY
# ============================================================

def scan_start_menu_apps() -> list[dict]:
    apps = []

    for root in START_MENU_DIRS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if path.suffix.lower() in {".lnk", ".exe", ".bat", ".cmd"}:
                apps.append({
                    "name": _normalize_name(path.stem),
                    "path": str(path),
                    "type": path.suffix.lower(),
                })

    return apps


def scan_program_executables() -> list[dict]:
    apps = []

    for root in COMMON_APP_DIRS:
        if not root.exists():
            continue

        try:
            for path in root.rglob("*.exe"):
                name = _normalize_name(path.stem)

                if name in {
                    "uninstall",
                    "unins000",
                    "setup",
                    "update",
                    "uninstaller",
                }:
                    continue

                apps.append({
                    "name": name,
                    "path": str(path),
                    "type": ".exe",
                })

                if len(apps) >= 3000:
                    return apps
        except (PermissionError, OSError):
            continue

    return apps


def list_installed_apps(limit: int = 500) -> list[dict]:
    apps = []
    seen = set()

    for item in scan_start_menu_apps() + scan_program_executables():
        key = _clean(item["name"])

        if not key or key in seen:
            continue

        seen.add(key)
        apps.append(item)

        if len(apps) >= limit:
            break

    return apps


def _score_app(query: str, app_name: str) -> int:
    q = _normalize_name(query)
    n = _normalize_name(app_name)

    if q == n:
        return 1000

    if q in n:
        return 800

    parts = q.split()

    score = 0

    for part in parts:
        if part in n:
            score += 100

    return score


def find_app(query: str) -> Optional[dict]:
    q = _clean(query)

    aliases = APP_ALIASES.get(q, [q])

    candidates = list_installed_apps()

    best = None
    best_score = 0

    for app in candidates:
        for alias in aliases:
            score = _score_app(alias, app["name"])

            if score > best_score:
                best_score = score
                best = app

    return best


def open_app(query: str) -> str:
    q = _clean(query)

    # Special native Windows applications
    native_apps = {
        "explorador": "explorer.exe",
        "explorador de archivos": "explorer.exe",
        "file explorer": "explorer.exe",
        "notepad": "notepad.exe",
        "bloc de notas": "notepad.exe",
        "calculator": "calc.exe",
        "calculadora": "calc.exe",
        "terminal": "wt.exe",
    }

    if q in native_apps:
        subprocess.Popen([native_apps[q]])
        return f"Opened: {query}"

    app = find_app(query)

    if not app:
        return f"Application not found: {query}"

    path = app["path"]

    try:
        if path.lower().endswith(".lnk"):
            os.startfile(path)
        else:
            subprocess.Popen([path])

        return f"Opened: {app['name']}"
    except Exception as exc:
        return f"Could not open {app['name']}: {exc}"


# ============================================================
# PROCESS CONTROL
# ============================================================

def list_processes(query: str | None = None, limit: int = 100) -> list[dict]:
    if psutil is None:
        return []

    result = []
    q = _clean(query) if query else ""

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info["name"] or ""

            if q and q not in _clean(name):
                continue

            result.append({
                "pid": proc.info["pid"],
                "name": name,
            })

            if len(result) >= limit:
                break

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return result


def close_process(query: str) -> str:
    if psutil is None:
        return "psutil is not available."

    q = _clean(query)
    closed = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info["name"] or ""

            if q in _clean(name):
                proc.terminate()
                closed.append(name)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not closed:
        return f"Process not found: {query}"

    return "Closed: " + ", ".join(sorted(set(closed)))


# ============================================================
# WINDOW CONTROL
# ============================================================

def list_windows() -> list[dict]:
    if win32gui is None:
        return []

    windows = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd).strip()

        if not title:
            return

        windows.append({
            "hwnd": hwnd,
            "title": title,
        })

    win32gui.EnumWindows(callback, None)
    return windows


def focus_window(search: str) -> str:
    if win32gui is None:
        return "pywin32 is not available."

    q = _clean(search)

    for item in list_windows():
        if q in _clean(item["title"]):
            hwnd = item["hwnd"]

            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return f"Focused: {item['title']}"
            except Exception as exc:
                return f"Could not focus window: {exc}"

    return f"Window not found: {search}"


# ============================================================
# KEYBOARD AND MOUSE
# ============================================================

def type_text(text: str) -> str:
    if pyautogui is None:
        return "pyautogui is not available."

    pyautogui.write(str(text), interval=0.01)
    return "Text typed."


def press_key(key: str) -> str:
    if pyautogui is None:
        return "pyautogui is not available."

    pyautogui.press(str(key))
    return f"Key pressed: {key}"


def click(x: int | None = None, y: int | None = None, button: str = "left") -> str:
    if pyautogui is None:
        return "pyautogui is not available."

    if x is None or y is None:
        pyautogui.click(button=button)
    else:
        pyautogui.click(x=int(x), y=int(y), button=button)

    return "Click done."


def move_mouse(x: int, y: int, duration: float = 0.2) -> str:
    if pyautogui is None:
        return "pyautogui is not available."

    pyautogui.moveTo(int(x), int(y), duration=duration)
    return "Mouse moved."


# ============================================================
# SYSTEM
# ============================================================

def system_info() -> dict:
    info = {
        "computer": os.environ.get("COMPUTERNAME", ""),
        "user": os.environ.get("USERNAME", ""),
        "home": str(HOME),
        "desktop": str(ONEDRIVE_DESKTOP if ONEDRIVE_DESKTOP.exists() else DESKTOP),
        "downloads": str(DOWNLOADS),
        "documents": str(DOCUMENTS),
        "python": os.sys.version,
    }

    if psutil:
        info["ram_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        info["cpu_percent"] = psutil.cpu_percent(interval=0.2)

    return info


def open_special_folder(name: str) -> str:
    q = _clean(name)

    folders = {
        "escritorio": ONEDRIVE_DESKTOP if ONEDRIVE_DESKTOP.exists() else DESKTOP,
        "desktop": ONEDRIVE_DESKTOP if ONEDRIVE_DESKTOP.exists() else DESKTOP,
        "descargas": DOWNLOADS,
        "downloads": DOWNLOADS,
        "documentos": DOCUMENTS,
        "documents": DOCUMENTS,
        "imagenes": PICTURES,
        "pictures": PICTURES,
        "videos": VIDEOS,
    }

    path = folders.get(q)

    if not path:
        return f"Special folder not found: {name}"

    os.startfile(str(path))
    return f"Opened: {path}"


# ============================================================
# HIGH LEVEL ACTIONS
# ============================================================

def execute(action: str, **kwargs):
    """
    Generic dispatcher for future JARVIS integration.
    """

    action = _clean(action)

    actions = {
        "open_app": open_app,
        "open_path": open_path,
        "open_folder": open_path,
        "open_special_folder": open_special_folder,
        "create_folder": create_folder,
        "create_file": create_file,
        "copy": copy_item,
        "copy_item": copy_item,
        "move": move_item,
        "move_item": move_item,
        "rename": rename_item,
        "rename_item": rename_item,
        "delete": delete_item,
        "delete_item": delete_item,
        "search": search_files,
        "search_files": search_files,
        "find_archives": find_archives,
        "extract_archive": extract_archive,
        "list_apps": list_installed_apps,
        "find_app": find_app,
        "list_processes": list_processes,
        "close_process": close_process,
        "list_windows": list_windows,
        "focus_window": focus_window,
        "type_text": type_text,
        "press_key": press_key,
        "click": click,
        "move_mouse": move_mouse,
        "system_info": system_info,
    }

    func = actions.get(action)

    if not func:
        return f"Unknown control action: {action}"

    return func(**kwargs)


# ============================================================
# QUICK SELF TEST
# ============================================================

if __name__ == "__main__":
    print("JARVIS CONTROL PC")
    print("=" * 50)
    print("Home:", HOME)
    print("Desktop:", ONEDRIVE_DESKTOP if ONEDRIVE_DESKTOP.exists() else DESKTOP)
    print("Downloads:", DOWNLOADS)

    print("\nTesting app discovery...")
    apps = list_installed_apps(limit=20)

    for app in apps[:20]:
        print(" -", app["name"], "=>", app["path"])

    print("\nOpera GX search:")
    print(find_app("Opera GX"))

    print("\n7-Zip:", find_7zip())
    print("WinRAR:", find_winrar())

    print("\nControl module loaded successfully.")
