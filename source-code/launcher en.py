import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
import json
import zipfile
from pathlib import Path, PureWindowsPath

import customtkinter as ctk
import requests
import tkinter as tk
from PIL import Image, ImageDraw

try:
    from pypresence import Presence as DiscordPresence
    _PYPRESENCE_AVAILABLE = True
except ImportError:
    _PYPRESENCE_AVAILABLE = False

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
    
ctk.set_default_color_theme("blue")

APP_LANG = "en"

CATALOGUE_URL = "https://github.com/mini9dev/fakeGames/releases/download/Catalogue/catalogue.json"
ADS_URL       = "https://github.com/mini9dev/fakeGames/releases/download/ADS/ads.json"
DOWNLOADS_DIR = Path("downloads")
USER_DIR = Path("user")
IMAGE_CACHE_DIR = USER_DIR / "cache_images"
CUSTOM_DIR = Path("customGames")
ADS_FILE = Path("ads.json")
WINDOW_SIZE = "1100x620"
CATALOGUE_CACHE = USER_DIR / "catalogue_cache.json"
VERSION_URL = "https://github.com/mini9dev/fakeGames/releases/download/Version/version.json"
CURRENT_VERSION = "2.2"
SETTINGS_FILE = USER_DIR / "settings.json"
DISCORD_CLIENT_ID = "1513657360013459486"

for d in (DOWNLOADS_DIR, IMAGE_CACHE_DIR, CUSTOM_DIR, USER_DIR):
    d.mkdir(parents=True, exist_ok=True)

THEMES = {
    "Dark": {
        "BG_DARK":    "#0b0d12",
        "BG_CARD":    "#151923",
        "BG_SIDEBAR": "#0f1219",
        "BG_HEADER":  "#0a0c11",
        "BG_MODAL":   "#0f1117",
        "BG_INPUT":   "#101622",
        "BG_PANEL":   "#111722",
        "ACCENT":     "#5865f2",
        "ACCENT_HOVER":"#4752c4",
        "ACCENT2":    "#57f287",
        "ACCENT3":    "#f0a030",
        "TEXT_PRIMARY":"#e8eaf0",
        "TEXT_MUTED": "#7b8099",
        "BORDER":     "#242a3a",
        "CARD_HOVER": "#1a2030",
        "RED_SOFT":   "#ed4245",
        "CTK_MODE":   "dark",
    },
    "Light": {
        "BG_DARK":    "#e8eaed",
        "BG_CARD":    "#ffffff",
        "BG_SIDEBAR": "#dde0e6",
        "BG_HEADER":  "#d0d4dc",
        "BG_MODAL":   "#f0f2f5",
        "BG_INPUT":   "#e0e3e8",
        "BG_PANEL":   "#e4e7ec",
        "ACCENT":     "#4752c4",
        "ACCENT_HOVER":"#3a44ad",
        "ACCENT2":    "#1e8a3a",
        "ACCENT3":    "#b86e00",
        "TEXT_PRIMARY":"#0d0f1a",
        "TEXT_MUTED": "#3a4255",
        "BORDER":     "#b0b5c2",
        "CARD_HOVER": "#d8dce6",
        "RED_SOFT":   "#c0282b",
        "CTK_MODE":   "light",
    },
    "Purple": {
        "BG_DARK":    "#0e0a1a",
        "BG_CARD":    "#1a1428",
        "BG_SIDEBAR": "#120e20",
        "BG_HEADER":  "#0c0916",
        "BG_MODAL":   "#110d1e",
        "BG_INPUT":   "#150f24",
        "BG_PANEL":   "#16102a",
        "ACCENT":     "#9b59f5",
        "ACCENT_HOVER":"#7c3fd4",
        "ACCENT2":    "#57f287",
        "ACCENT3":    "#f0a030",
        "TEXT_PRIMARY":"#ede8ff",
        "TEXT_MUTED": "#8878aa",
        "BORDER":     "#2e2050",
        "CARD_HOVER": "#1e1638",
        "RED_SOFT":   "#ed4245",
        "CTK_MODE":   "dark",
    },
}


def load_settings() -> dict:
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"theme": "Dark", "discord_presence": True}


def save_settings(data: dict):
    try:
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def apply_theme(name: str):
    global BG_DARK, BG_CARD, BG_SIDEBAR, BG_HEADER, BG_MODAL, BG_INPUT, BG_PANEL
    global ACCENT, ACCENT_HOVER, ACCENT2, ACCENT3, TEXT_PRIMARY, TEXT_MUTED
    global BORDER, CARD_HOVER, RED_SOFT
    t = THEMES.get(name, THEMES["Dark"])
    BG_DARK     = t["BG_DARK"]
    BG_CARD     = t["BG_CARD"]
    BG_SIDEBAR  = t["BG_SIDEBAR"]
    BG_HEADER   = t["BG_HEADER"]
    BG_MODAL    = t["BG_MODAL"]
    BG_INPUT    = t["BG_INPUT"]
    BG_PANEL    = t["BG_PANEL"]
    ACCENT      = t["ACCENT"]
    ACCENT_HOVER= t["ACCENT_HOVER"]
    ACCENT2     = t["ACCENT2"]
    ACCENT3     = t["ACCENT3"]
    TEXT_PRIMARY= t["TEXT_PRIMARY"]
    TEXT_MUTED  = t["TEXT_MUTED"]
    BORDER      = t["BORDER"]
    CARD_HOVER  = t["CARD_HOVER"]
    RED_SOFT    = t["RED_SOFT"]
    ctk.set_appearance_mode(t["CTK_MODE"])


# ── Discord Rich Presence ───────────────────────────────────────────────────
class DiscordRPC:
    def __init__(self):
        self._rpc = None
        self._connected = False
        self._lock = threading.Lock()

    def connect(self):
        if not _PYPRESENCE_AVAILABLE:
            return
        def _try():
            try:
                rpc = DiscordPresence(DISCORD_CLIENT_ID)
                rpc.connect()
                with self._lock:
                    self._rpc = rpc
                    self._connected = True
                self.set_idle()
            except Exception:
                pass
        threading.Thread(target=_try, daemon=True).start()

    def set_idle(self):
        self._update(
            details="FakeGames Launcher",
            state="Bypass the orbs system with ease ;)",
            large_image="fg-logo",
            large_text="v" + CURRENT_VERSION,
            buttons=[{"label": "Install the launcher", "url": "https://github.com/mini9dev/fakeGames"}],
        )

    def set_playing(self, game_name: str):
        self._update(
            details="FakeGames Launcher",
            state=f"Pretending to play {game_name} to get more orbs :P",
            large_image="fg-logo",
            large_text="v" + CURRENT_VERSION,
            buttons=[{"label": "Install the launcher", "url": "https://github.com/mini9dev/fakeGames"}],
        )

    def _update(self, **kwargs):
        def _do():
            with self._lock:
                if not self._connected or self._rpc is None:
                    return
                try:
                    self._rpc.update(start=int(time.time()), **kwargs)
                except Exception:
                    self._connected = False
        threading.Thread(target=_do, daemon=True).start()

    def disconnect(self):
        with self._lock:
            if self._rpc and self._connected:
                try:
                    self._rpc.close()
                except Exception:
                    pass
            self._rpc = None
            self._connected = False


_discord_rpc = DiscordRPC()

# Load and apply saved theme on startup
_settings = load_settings()
_active_theme = _settings.get("theme", "Dark")
apply_theme(_active_theme)

_IMAGE_MEMORY_CACHE = {}


def sanitize_name(name: str) -> str:
    cleaned = "".join(ch for ch in name if ch not in r'<>:"/\|?*').strip()
    return cleaned.rstrip(". ")


def parse_fake_game_path(game_name: str, raw_path: str):
    raw_path = (raw_path or game_name).strip().replace("/", "\\")
    parts = [sanitize_name(p) for p in PureWindowsPath(raw_path).parts if sanitize_name(p)]

    if not parts:
        fallback = sanitize_name(game_name) or "game"
        return fallback, [], fallback

    exe_name = parts[-1]
    if exe_name.lower().endswith(".exe"):
        exe_name = exe_name[:-4]
    exe_name = sanitize_name(exe_name) or sanitize_name(game_name) or "game"

    path_parts = parts[:-1]
    root_folder = path_parts[0] if path_parts else exe_name
    root_folder = sanitize_name(root_folder) or exe_name

    return root_folder, path_parts, exe_name


def find_executable(folder: Path):
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".exe"):
                return Path(root) / f
    return None


def make_placeholder_image(size=(160, 90), custom=False):
    img = Image.new("RGB", size, "#1a1d2e")
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2
    if custom:
        import math
        color = "#f0a030"
        draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill="#2a2010")
        draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=color)
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill="#1a1d2e")
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = cx + int(14 * math.cos(rad))
            y1 = cy + int(14 * math.sin(rad))
            x2 = cx + int(20 * math.cos(rad))
            y2 = cy + int(20 * math.sin(rad))
            draw.line([x1, y1, x2, y2], fill=color, width=4)
    else:
        draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill="#2a2d42")
        draw.polygon([(cx - 7, cy - 10), (cx - 7, cy + 10), (cx + 12, cy)], fill=ACCENT)
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)


def load_image_cached(url: str, size=(160, 90)):
    if not url:
        return None
    cache_key = (url, size)
    if cache_key in _IMAGE_MEMORY_CACHE:
        return _IMAGE_MEMORY_CACHE[cache_key]
    local = IMAGE_CACHE_DIR / sanitize_name(url.split("/")[-1])
    try:
        if not local.exists():
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            local.write_bytes(r.content)
        img = Image.open(local).convert("RGB").resize(size, Image.LANCZOS)
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        _IMAGE_MEMORY_CACHE[cache_key] = photo
        return photo
    except Exception:
        return None


def load_local_image(path: str, size=(420, 160)):
    cache_key = (str(path), size)
    if cache_key in _IMAGE_MEMORY_CACHE:
        return _IMAGE_MEMORY_CACHE[cache_key]
    try:
        img_path = Path(path)
        if not img_path.exists():
            return None
        img = Image.open(img_path).convert("RGB").resize(size, Image.LANCZOS)
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        _IMAGE_MEMORY_CACHE[cache_key] = photo
        return photo
    except Exception:
        return None


def load_catalogue_cache():
    try:
        if CATALOGUE_CACHE.exists():
            data = json.loads(CATALOGUE_CACHE.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
    except Exception:
        pass
    return []


def save_catalogue_cache(data: list):
    try:
        CATALOGUE_CACHE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def fetch_remote_catalogue():
    r = requests.get(CATALOGUE_URL, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else [data]


def check_for_update():
    try:
        r = requests.get(VERSION_URL, timeout=6)
        r.raise_for_status()
        info = r.json()
        latest = str(info.get("version", "")).strip()
        url    = info.get("url", "")
        # changelog peut etre une liste (ancienne spec) ou un dict {fr:[], en:[]}
        raw = info.get("changelog", [])
        if isinstance(raw, dict):
            changelog = raw.get(APP_LANG, raw.get("fr", []))
        else:
            changelog = raw
        if latest and latest != CURRENT_VERSION:
            return latest, url, changelog
    except Exception:
        pass
    return None, None, []


def _t(field):
    """Resout un champ bilingue {fr:..., en:...} ou retourne la valeur directe."""
    if isinstance(field, dict):
        return field.get(APP_LANG, field.get("fr", ""))
    return field or ""


def default_ad():
    return {
        "title": {"fr": "Sponsor FakeGames", "en": "FakeGames Sponsor"},
        "text":  {"fr": "Merci de patienter quelques secondes avant le telechargement.",
                  "en": "Please wait a few seconds before the download starts."},
        "button":{"fr": "Ouvrir le sponsor", "en": "Open sponsor"},
        "url": "",
        "image": "",
        "seconds": 6,
    }


def load_ads():
    def normalize(data):
        if isinstance(data, dict):
            data = [data]
        result = []
        for ad in data:
            if not isinstance(ad, dict):
                continue
            result.append({
                "title":   _t(ad.get("title", "")),
                "text":    _t(ad.get("text", "")),
                "button":  _t(ad.get("button", "")),
                "url":     ad.get("url", ""),
                "image":   ad.get("image", ""),
                "seconds": ad.get("seconds", 6),
            })
        return result or [default_ad()]

    try:
        if ADS_FILE.exists():
            import json
            return normalize(json.loads(ADS_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass

    return [default_ad()]


def fetch_remote_ads():
    def normalize(data):
        if isinstance(data, dict):
            data = [data]
        result = []
        for ad in data:
            if not isinstance(ad, dict):
                continue
            result.append({
                "title":   _t(ad.get("title", "")),
                "text":    _t(ad.get("text", "")),
                "button":  _t(ad.get("button", "")),
                "url":     ad.get("url", ""),
                "image":   ad.get("image", ""),
                "seconds": ad.get("seconds", 6),
            })
        return result

    r = requests.get(ADS_URL, timeout=8)
    r.raise_for_status()
    return normalize(r.json())


def get_folder_size_mb(folder: Path) -> float:
    total = 0
    if folder.exists():
        for f in folder.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except Exception:
                    pass
    return total / (1024 * 1024)


def safe_extract_zip(zip_path: str, target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    target_root = target_dir.resolve()
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            target = (target_dir / member.filename).resolve()
            if target_root != target and target_root not in target.parents:
                raise ValueError("Invalid ZIP archive: dangerous path detected.")
        z.extractall(target_dir)


def download_zip_with_progress(url, target_dir, progress_cb=None, retry_cb=None, max_retries=3):
    last_err = ""
    read_timeouts = [30, 60, 120]
    for attempt in range(max_retries):
        tmp_name = None
        try:
            if not url:
                return False, "Download URL missing."
            if attempt > 0 and retry_cb:
                retry_cb(attempt, max_retries)
            with requests.get(url, stream=True, timeout=(10, read_timeouts[min(attempt, 2)])) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length") or 0)
                downloaded = 0
                with tempfile.NamedTemporaryFile(delete=False) as tmpf:
                    tmp_name = tmpf.name
                    for chunk in r.iter_content(chunk_size=65536):
                        if not chunk:
                            continue
                        tmpf.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb:
                            progress_cb(downloaded, total)
            try:
                safe_extract_zip(tmp_name, target_dir)
            except zipfile.BadZipFile:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(tmp_name, target_dir / "game.exe")
                return True, ""
            finally:
                if tmp_name and os.path.exists(tmp_name):
                    os.remove(tmp_name)
            return True, ""
        except requests.exceptions.Timeout:
            last_err = f"Delai depasse (tentative {attempt + 1}/{max_retries})"
            if tmp_name and os.path.exists(tmp_name):
                os.remove(tmp_name)
            if progress_cb:
                progress_cb(0, 1)
        except Exception as e:
            last_err = str(e)
            if tmp_name and os.path.exists(tmp_name):
                os.remove(tmp_name)
            break
    return False, last_err



FAKE_GAME_SOURCE = r'''
import ctypes

TITLE = {title!r}
MESSAGE = (
    TITLE + "\n\n"
    "The game is running.\n"
    "Cliquez OK to close."
)

user32 = ctypes.windll.user32


def main():
    user32.MessageBoxW(None, MESSAGE, TITLE, 0x00000040)


if __name__ == "__main__":
    main()
'''


def _find_python() -> str:
    if not getattr(sys, "frozen", False):
        return sys.executable
    for candidate in ("python", "python3", "python.exe", "python3.exe", "py"):
        found = shutil.which(candidate)
        if found:
            return found
    raise FileNotFoundError(
        "Impossible de trouver Python dans PATH.\n"
        "Make sure Python is installed and in your PATH."
    )


def _prepare_fake_game_pyinstaller_args(python_bin: str, tmp: Path, log_cb=None):
    if log_cb:
        log_cb("Native Windows fake game: lightweight build, no tkinter.")
    return ["--exclude-module", "tkinter", "--exclude-module", "_tkinter"], ""


def _cleanup_existing_pyinstaller_spec(tmp: Path, build_name: str):
    spec = tmp / f"{build_name}.spec"
    if spec.exists():
        try:
            spec.unlink()
        except Exception:
            pass


def _normalize_build_name(name: str):
    return sanitize_name(name).replace(" ", "_SPACE_") or "fake_game"


def _rename_generated_exe(tmp: Path, build_name: str, exe_basename: str):
    generated = tmp / "dist" / f"{build_name}.exe"
    if not generated.exists():
        return None
    renamed = tmp / "dist" / f"{exe_basename}.exe"
    if generated != renamed:
        generated.rename(renamed)
    return renamed


def _copy_fake_game_to_destination(generated: Path, dest_folder: Path, path_parts, exe_basename: str):
    inner = dest_folder
    for part in path_parts:
        inner = inner / part
    inner.mkdir(parents=True, exist_ok=True)
    final = inner / f"{exe_basename}.exe"
    shutil.copy2(str(generated), str(final))
    return final


def _run_pyinstaller(cmd, tmp: Path, log_cb=None):
    proc = subprocess.Popen(
        cmd,
        cwd=str(tmp),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for line in proc.stdout:
        line = line.rstrip()
        if line and log_cb:
            log_cb(line)
    proc.wait()
    return proc.returncode


def _is_pyinstaller_missing_error(exc: Exception):
    return isinstance(exc, FileNotFoundError)


def _pyinstaller_failed_message():
    return "PyInstaller failed. Make sure pyinstaller is installed."


def _missing_generated_exe_message():
    return "No .exe found after compilation."


def _pyinstaller_missing_message():
    return "PyInstaller not found. Install it with: pip install pyinstaller"


def _safe_done(done_cb, ok, value):
    if done_cb:
        done_cb(ok, value)


def _write_fake_game_source(src: Path, game_name: str):
    src.write_text(FAKE_GAME_SOURCE.format(title=game_name), encoding="utf-8")


def _fake_game_build_command(python_bin: str, build_name: str, src: Path, pyinstaller_args):
    return [
        python_bin,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        build_name,
        *pyinstaller_args,
        str(src),
    ]


def _build_fake_game_in_tmp(game_name, exe_path, dest_folder, tmp, log_cb=None):
    root_folder, path_parts, exe_basename = parse_fake_game_path(game_name, exe_path)
    src = tmp / "fake_game.py"
    _write_fake_game_source(src, game_name)

    python_bin = _find_python()
    build_name = _normalize_build_name(exe_basename)
    _cleanup_existing_pyinstaller_spec(tmp, build_name)

    pyinstaller_args, err = _prepare_fake_game_pyinstaller_args(python_bin, tmp, log_cb=log_cb)
    if pyinstaller_args is None:
        return False, err

    cmd = _fake_game_build_command(python_bin, build_name, src, pyinstaller_args)
    if _run_pyinstaller(cmd, tmp, log_cb=log_cb) != 0:
        return False, _pyinstaller_failed_message()

    generated = _rename_generated_exe(tmp, build_name, exe_basename)
    if generated is None:
        return False, _missing_generated_exe_message()

    final = _copy_fake_game_to_destination(generated, dest_folder, path_parts, exe_basename)
    (dest_folder / ".fakegame_meta").write_text(game_name, encoding="utf-8")
    return True, str(final)


def _report_build_exception(exc: Exception):
    if _is_pyinstaller_missing_error(exc):
        return _pyinstaller_missing_message()
    return str(exc)


def _start_daemon_thread(target):
    threading.Thread(target=target, daemon=True).start()


def _noop():
    return None


def _unused_compatibility_marker():
    return _noop()


def build_fake_game(game_name: str, exe_path: str, dest_folder: Path, log_cb=None, done_cb=None):
    def worker():
        tmp = Path(tempfile.mkdtemp(prefix="fg_build_"))
        try:
            ok, value = _build_fake_game_in_tmp(game_name, exe_path, dest_folder, tmp, log_cb=log_cb)
            _safe_done(done_cb, ok, value)
        except Exception as e:
            _safe_done(done_cb, False, _report_build_exception(e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    _start_daemon_thread(worker)


_active_toasts = []


class Toast(ctk.CTkToplevel):
    def __init__(self, parent, message, color=ACCENT2, duration=3500):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=BG_DARK)
        self._parent = parent
        frame = ctk.CTkFrame(
            self, fg_color=BG_PANEL, corner_radius=8, border_width=1, border_color=BORDER
        )
        frame.pack(padx=1, pady=1, ipadx=0, ipady=0)
        ctk.CTkFrame(frame, width=4, height=34, fg_color=color, corner_radius=2).pack(
            side="left", padx=(8, 8), pady=8
        )
        ctk.CTkLabel(
            frame,
            text=message,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
            wraplength=280,
            justify="left",
        ).pack(side="left", padx=(0, 14), pady=10)
        self.update_idletasks()
        _active_toasts.append(self)
        Toast._reposition_all()
        self.attributes("-alpha", 0.0)
        self._fade_in()
        self.after(duration, self._fade_out)

    @staticmethod
    def _reposition_all():
        margin = 16
        gap = 8
        y_offset = margin
        for t in reversed(_active_toasts[:]):
            if not t.winfo_exists():
                _active_toasts.remove(t)
                continue
            t.update_idletasks()
            tw = t.winfo_reqwidth()
            th = t.winfo_reqheight()
            try:
                px = t._parent.winfo_x()
                py = t._parent.winfo_y()
                pww = t._parent.winfo_width()
                pwh = t._parent.winfo_height()
            except Exception:
                continue
            t.geometry(f"+{px + pww - tw - margin}+{py + pwh - th - y_offset}")
            y_offset += th + gap

    def _fade_in(self, alpha=0.0):
        alpha = min(alpha + 0.1, 1.0)
        self.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.after(14, lambda: self._fade_in(alpha))

    def _fade_out(self, alpha=1.0):
        if not self.winfo_exists():
            return
        alpha = max(alpha - 0.08, 0.0)
        self.attributes("-alpha", alpha)
        if alpha > 0:
            self.after(14, lambda: self._fade_out(alpha))
        else:
            if self in _active_toasts:
                _active_toasts.remove(self)
            try:
                self.destroy()
            except Exception:
                pass


class CreateGameModal(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.title("Create a fake game")
        self.geometry("560x540")
        self.resizable(False, False)
        self.configure(fg_color=BG_MODAL)
        self.grab_set()
        self.attributes("-topmost", True)
        self._parent = parent
        self._on_success = on_success
        self._building = False

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 560) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 540) // 2
        self.geometry(f"560x540+{px}+{py}")
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color=BG_HEADER, height=56, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text="CREATE A FAKE GAME",
            font=ctk.CTkFont(family="Segoe UI Black", size=15, weight="bold"),
            text_color=ACCENT3,
        ).pack(side="left", padx=20, pady=14)
        ctk.CTkButton(
            hdr,
            text="X",
            width=36,
            height=28,
            fg_color="transparent",
            hover_color="#2a1520",
            text_color=TEXT_MUTED,
            corner_radius=6,
            command=self._safe_close,
        ).pack(side="right", padx=12, pady=14)

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=(18, 8))

        self.game_name_var = ctk.StringVar()
        self.exe_name_var = ctk.StringVar()

        self._field(form, "Game name  (shown in the fake game window)", "ex: Rune Dice", self.game_name_var)

        ctk.CTkLabel(
            form,
            text="Path or name of the real game .exe",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(
            form,
            text="Paste the full path or just the name. The folder structure will be recreated.",
            font=ctk.CTkFont(size=10),
            text_color=TEXT_MUTED,
            anchor="w",
            wraplength=480,
        ).pack(fill="x", pady=(0, 4))
        ctk.CTkEntry(
            form,
            textvariable=self.exe_name_var,
            placeholder_text="e.g. Rune Dice\\Rune Dice\\Binaries\\Win64\\Rune Dice.exe",
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
            height=36,
            corner_radius=8,
        ).pack(fill="x", pady=(0, 8))

        preview_row = ctk.CTkFrame(form, fg_color="transparent")
        preview_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            preview_row, text="Detected final path:", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED
        ).pack(side="left")
        self.preview_lbl = ctk.CTkLabel(
            preview_row, text="-", font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT3
        )
        self.preview_lbl.pack(side="left", padx=(6, 0))

        self.exe_name_var.trace_add("write", self._update_preview)
        self.game_name_var.trace_add("write", self._update_preview)
        self._update_preview()

        info = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        info.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(
            info,
            text=(
                "Le jeu sera cree dans : customGames/<dossier racine>/\n"
                "PyInstaller must be installed: pip install pyinstaller\n"
                "Compilation: approx. 30 to 60 seconds."
            ),
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
            justify="left",
            anchor="w",
        ).pack(padx=14, pady=10)

        self.build_btn = ctk.CTkButton(
            self,
            text="Compile fake game",
            fg_color=ACCENT3,
            hover_color="#c07820",
            text_color="#0d0f14",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            command=self._start_build,
        )
        self.build_btn.pack(fill="x", padx=24, pady=(0, 10))

        log_frame = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=10, border_width=1, border_color=BORDER)
        log_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self.log_label = ctk.CTkLabel(
            log_frame,
            text="Waiting...",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=490,
        )
        self.log_label.pack(anchor="nw", padx=10, pady=8)

        self.pbar = ctk.CTkProgressBar(self, progress_color=ACCENT3, fg_color=BG_PANEL, height=6, corner_radius=3)
        self.pbar.set(0)
        self.pbar.pack(fill="x", padx=24, pady=(0, 16))
        self.pbar.pack_forget()

    def _field(self, parent, label, placeholder, var):
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))
        entry = ctk.CTkEntry(
            parent,
            textvariable=var,
            placeholder_text=placeholder,
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=8,
        )
        entry.pack(fill="x", pady=(0, 14))
        return entry

    def _update_preview(self, *_):
        gname = self.game_name_var.get().strip()
        ename = self.exe_name_var.get().strip() or gname
        root_folder, path_parts, exe_basename = parse_fake_game_path(gname, ename)
        final = CUSTOM_DIR / root_folder
        for part in path_parts:
            final = final / part
        final = final / f"{exe_basename}.exe"
        self.preview_lbl.configure(text=str(final))

    def _start_build(self):
        if self._building:
            return
        gname = self.game_name_var.get().strip()
        ename = self.exe_name_var.get().strip() or gname
        if not gname:
            self._log("Enter a game name.", color=RED_SOFT)
            return

        root_folder, _, _ = parse_fake_game_path(gname, ename)
        dest = CUSTOM_DIR / root_folder

        self._building = True
        self.build_btn.configure(state="disabled", text="Compiling...")
        self.pbar.pack(fill="x", padx=24, pady=(0, 16))
        self.pbar.configure(mode="indeterminate")
        self.pbar.start()
        self._log(f"Compiling '{ename}' ...")

        build_fake_game(game_name=gname, exe_path=ename, dest_folder=dest, log_cb=self._log, done_cb=self._done)

    def _log(self, line, color=None):
        color = color or TEXT_MUTED
        self.after(0, lambda: self.log_label.configure(text=line[-160:], text_color=color))

    def _done(self, ok, path_or_err):
        self._building = False
        self.after(0, self.pbar.stop)
        self.after(0, self.pbar.pack_forget)
        if ok:
            self.after(
                0,
                lambda: self.log_label.configure(text="Success! Closing in 2 seconds...", text_color=ACCENT2),
            )
            self.after(0, lambda: self._on_success(path_or_err))
            self.after(2000, self._safe_close)
        else:
            self.after(0, lambda: self.log_label.configure(text=f"Error: {path_or_err}", text_color=RED_SOFT))
            self.after(0, lambda: self.build_btn.configure(state="normal", text="Retry"))

    def _safe_close(self):
        if self._building:
            return
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class AdModal(ctk.CTkToplevel):
    def __init__(self, parent, ad, on_continue, on_cancel):
        super().__init__(parent)
        self.title("Sponsor")
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(fg_color=BG_MODAL)
        self.grab_set()
        self.attributes("-topmost", True)
        self._parent = parent
        self._ad = ad
        self._on_continue = on_continue
        self._on_cancel = on_cancel
        self._total_seconds = max(3, int(ad.get("seconds", 6) or 6))
        self._elapsed_ms = 0
        self._closed = False
        self._can_continue = False

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 520) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 420) // 2
        self.geometry(f"520x420+{px}+{py}")

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build_ui()
        self._tick()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color=BG_MODAL, height=56, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        title_wrap = ctk.CTkFrame(hdr, fg_color="transparent")
        title_wrap.pack(side="left", padx=18, pady=9)
        ctk.CTkLabel(
            title_wrap,
            text="Partner",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_wrap,
            text="The download will start after this short wait",
            font=ctk.CTkFont(size=10),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")
        ctk.CTkButton(
            hdr,
            text="X",
            width=34,
            height=26,
            fg_color="transparent",
            hover_color="#2a1520",
            text_color=TEXT_MUTED,
            command=self._cancel,
        ).pack(side="right", padx=12, pady=13)

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=22, pady=18)

        image_ref = self._ad.get("image") or ""
        self.image_slot = ctk.CTkFrame(body, fg_color=BG_INPUT, corner_radius=8, border_width=1, border_color=BORDER)
        self.image_slot.pack(fill="x", pady=(0, 16))
        self.image_label = ctk.CTkLabel(self.image_slot, text="")
        self.image_label.pack(fill="x")
        self._set_ad_placeholder()
        if image_ref:
            threading.Thread(target=lambda: self._load_ad_image_async(image_ref), daemon=True).start()

        ctk.CTkLabel(
            body,
            text=self._ad.get("title", "Sponsor"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            body,
            text=self._ad.get("text", ""),
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            justify="left",
            wraplength=450,
        ).pack(anchor="w", pady=(6, 14))

        bottom = ctk.CTkFrame(body, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", pady=(8, 0))

        actions = ctk.CTkFrame(bottom, fg_color="transparent")
        actions.pack(fill="x")

        sponsor_url = self._ad.get("url") or ""
        if sponsor_url:
            ctk.CTkButton(
                actions,
                text=self._ad.get("button", "Open sponsor"),
                fg_color=BG_INPUT,
                hover_color=CARD_HOVER,
                border_width=1,
                border_color=BORDER,
                text_color=TEXT_PRIMARY,
                height=36,
                corner_radius=7,
                command=lambda: webbrowser.open(sponsor_url),
            ).pack(side="left")

        self.continue_width = 220
        self.continue_height = 36
        self.continue_canvas = tk.Canvas(
            actions,
            width=self.continue_width,
            height=self.continue_height,
            bg=BG_MODAL,
            highlightthickness=0,
            bd=0,
        )
        self.continue_canvas.pack(side="right")
        self.continue_bg = self.continue_canvas.create_rectangle(
            1, 1, self.continue_width - 1, self.continue_height - 1,
            fill=BG_INPUT, outline=BORDER, width=1,
        )
        self.continue_fill = self.continue_canvas.create_rectangle(
            1, 1, 1, self.continue_height - 1, fill=ACCENT, outline="",
        )
        self.continue_text = self.continue_canvas.create_text(
            self.continue_width // 2, self.continue_height // 2,
            text="Please wait...",
            fill=TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
        )
        self.continue_canvas.bind("<Button-1>", self._try_continue)
        self.continue_canvas.bind("<Enter>", self._continue_hover)
        self.continue_canvas.bind("<Leave>", self._continue_leave)

    def _set_ad_placeholder(self):
        for child in self.image_slot.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self.image_slot,
            text="FAKEGAMES",
            font=ctk.CTkFont(family="Segoe UI Black", size=26, weight="bold"),
            text_color=ACCENT,
        ).pack(pady=(28, 2))
        ctk.CTkLabel(
            self.image_slot,
            text="Partner space",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).pack(pady=(0, 28))

    def _load_ad_image_async(self, image_ref):
        if image_ref.startswith("http://") or image_ref.startswith("https://"):
            img = load_image_cached(image_ref, size=(440, 150))
        else:
            img = load_local_image(image_ref, size=(440, 150))
        if img and not self._closed:
            self.after(0, lambda: self._set_ad_image(img))

    def _set_ad_image(self, img):
        if self._closed:
            return
        for child in self.image_slot.winfo_children():
            child.destroy()
        self.image_label = ctk.CTkLabel(self.image_slot, text="", image=img)
        self.image_label.image = img
        self.image_label.pack(fill="x")

    def _tick(self):
        if self._closed:
            return
        total_ms = self._total_seconds * 1000
        progress = self._elapsed_ms / total_ms
        self._draw_continue_button(max(0, min(progress, 1)))
        remaining = max(0, int((total_ms - self._elapsed_ms + 999) / 1000))
        if self._elapsed_ms >= total_ms:
            self._can_continue = True
            self._draw_continue_button(1, text="Continue")
            return
        self._set_continue_text(f"Continue in {remaining}s")
        self._elapsed_ms += 100
        self.after(100, self._tick)

    def _draw_continue_button(self, progress, text=None):
        fill_width = 1 + int((self.continue_width - 2) * progress)
        self.continue_canvas.coords(self.continue_fill, 1, 1, fill_width, self.continue_height - 1)
        if text is not None:
            self._set_continue_text(text)

    def _set_continue_text(self, text):
        self.continue_canvas.itemconfigure(self.continue_text, text=text)

    def _try_continue(self, _event=None):
        if self._can_continue:
            self._continue()

    def _continue_hover(self, _event=None):
        if self._can_continue:
            self.continue_canvas.itemconfigure(self.continue_fill, fill=ACCENT_HOVER)

    def _continue_leave(self, _event=None):
        self.continue_canvas.itemconfigure(self.continue_fill, fill=ACCENT)

    def _continue(self):
        self._closed = True
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        self._on_continue()

    def _cancel(self):
        self._closed = True
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        self._on_cancel()


class GameCard(ctk.CTkFrame):
    def __init__(
        self, parent, game, on_download, on_launch, on_uninstall,
        on_ad_before_download=None, installed=False, is_custom=False,
    ):
        super().__init__(parent, corner_radius=10, fg_color=BG_CARD, border_width=1, border_color=BORDER)
        self.game = game
        self.installed = installed
        self.is_custom = is_custom
        self.on_download = on_download
        self.on_launch = on_launch
        self.on_uninstall = on_uninstall
        self.on_ad_before_download = on_ad_before_download
        self._downloading = False

        self.grid_columnconfigure(1, weight=1)
        self.img_frame = ctk.CTkFrame(
            self, width=168, height=94, corner_radius=8, fg_color=BG_INPUT, border_width=1, border_color=BORDER
        )
        self.img_frame.grid(row=0, column=0, rowspan=3, padx=(14, 12), pady=14, sticky="nw")
        self.img_frame.grid_propagate(False)
        self.img_label = ctk.CTkLabel(self.img_frame, text="")
        self.img_label.place(relx=0.5, rely=0.5, anchor="center")
        ph = make_placeholder_image(custom=is_custom)
        self.img_label.configure(image=ph)
        self.img_label.image = ph

        name = game.get("name", "Inconnu")
        desc = game.get("description", "Fake game created locally." if is_custom else "No description available.")

        name_lbl = ctk.CTkLabel(
            self, text=name,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY, anchor="w",
        )
        name_lbl.grid(row=0, column=1, sticky="sw", padx=(0, 10), pady=(15, 2))

        desc_lbl = ctk.CTkLabel(
            self, text=desc,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED, anchor="w", justify="left", wraplength=340,
        )
        desc_lbl.grid(row=1, column=1, sticky="nw", padx=(0, 8))

        badge_text = "Installed" if installed else "Available"
        badge_color = ACCENT2 if installed else ACCENT3
        self.badge = ctk.CTkLabel(
            self, text=badge_text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=badge_color, fg_color=BG_PANEL, corner_radius=5, width=82, height=22,
        )
        self.badge.grid(row=2, column=1, sticky="nw", padx=(0, 8), pady=(4, 12))

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, rowspan=3, padx=(0, 16), pady=14, sticky="e")

        if installed or is_custom:
            self._build_installed_buttons(name)
        else:
            self._build_download_button()

        for w in (self, name_lbl, desc_lbl):
            w.bind("<Enter>", lambda _e: self.configure(fg_color=CARD_HOVER))
            w.bind("<Leave>", lambda _e: self.configure(fg_color=BG_CARD))

    def _build_installed_buttons(self, name=None):
        name = name or self.game.get("name", "")
        base = CUSTOM_DIR if self.is_custom else DOWNLOADS_DIR
        folder_key = self.game.get("_folder", sanitize_name(name)) if self.is_custom else sanitize_name(name)
        folder = base / folder_key
        self.action_btn = ctk.CTkButton(
            self.btn_frame, text="Lancer", width=115, height=36,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=7,
            command=lambda: self.on_launch(folder),
        )
        self.action_btn.pack(pady=(0, 6))
        ctk.CTkButton(
            self.btn_frame, text="Delete", width=115, height=30,
            fg_color="transparent", hover_color="#2a1520",
            border_width=1, border_color=RED_SOFT, text_color=RED_SOFT,
            font=ctk.CTkFont(size=11), corner_radius=7,
            command=lambda: self.on_uninstall(self.game, self),
        ).pack()

    def _build_download_button(self):
        self.action_btn = ctk.CTkButton(
            self.btn_frame, text="Download", width=115, height=36,
            fg_color=BG_INPUT, hover_color=CARD_HOVER,
            border_width=1, border_color=ACCENT, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=7,
            command=self._trigger_download,
        )
        self.action_btn.pack(pady=(0, 6))
        self.pbar = ctk.CTkProgressBar(
            self.btn_frame, width=115, height=6, progress_color=ACCENT, fg_color="#1e2240", corner_radius=3
        )
        self.pbar.set(0)
        self.pbar_label = ctk.CTkLabel(self.btn_frame, text="", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED)

    def _trigger_download(self):
        if self._downloading:
            return
        self._downloading = True
        self.action_btn.configure(state="disabled", text="In progress...")
        self.pbar.pack()
        self.pbar_label.pack()

        def start_after_ad():
            self.on_download(self.game, self._progress_cb, self._retry_cb, self._on_done)

        def cancel_after_ad():
            self._downloading = False
            self.pbar.pack_forget()
            self.pbar_label.pack_forget()
            self.action_btn.configure(state="normal", text="Download")

        if self.on_ad_before_download and not self.is_custom:
            self.on_ad_before_download(start_after_ad, cancel_after_ad)
        else:
            start_after_ad()

    def _progress_cb(self, downloaded, total):
        val = downloaded / total if total else 0
        self.after(0, lambda: self.pbar.set(val))
        self.after(0, lambda: self.pbar_label.configure(text=f"{int(val * 100)}%"))

    def _retry_cb(self, attempt, max_retries):
        self.after(0, lambda: self.pbar_label.configure(
            text=f"Retry {attempt}/{max_retries}...", text_color=ACCENT3))
        self.after(0, lambda: self.pbar.set(0))

    def _on_done(self, ok, err):
        self._downloading = False
        self.after(0, self.pbar.pack_forget)
        self.after(0, self.pbar_label.pack_forget)
        if ok:
            self.after(0, self._switch_to_installed)
            self.after(0, lambda: self.badge.configure(text="Installed", text_color=ACCENT2))
        else:
            self.after(0, lambda: self.action_btn.configure(
                text="Retry", state="normal",
                fg_color="transparent", hover_color=ACCENT,
                border_width=1, border_color=ACCENT, text_color=TEXT_PRIMARY,
            ))

    def _switch_to_installed(self):
        for w in self.btn_frame.winfo_children():
            w.destroy()
        self._build_installed_buttons()

    def set_image(self, photo):
        self.img_label.configure(image=photo)
        self.img_label.image = photo


class UpdateModal(ctk.CTkToplevel):
    def __init__(self, parent, latest_version, setup_url, changelog=None):
        super().__init__(parent)
        self._url        = setup_url
        self._parent     = parent
        self._cancelled  = False
        self._changelog  = changelog or []

        n          = min(len(self._changelog), 8)
        height     = 320 + n * 22  # hauteur minimale augmentee pour que les boutons soient visibles
        self.title("Update available")
        self.geometry(f"460x{height}")
        self.resizable(False, False)
        self.configure(fg_color=BG_MODAL)
        self.grab_set()
        self.attributes("-topmost", True)

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - 460) // 2
        py = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"460x{height}+{px}+{py}")
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build_ui(latest_version)

    def _build_ui(self, version):
        hdr = ctk.CTkFrame(self, fg_color=BG_HEADER, height=50, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="UPDATE AVAILABLE",
                     font=ctk.CTkFont(family="Segoe UI Black", size=13, weight="bold"),
                     text_color=ACCENT2).pack(side="left", padx=20, pady=13)
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(body,
                     text=f"Version v{version} available  (current: v{CURRENT_VERSION})",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(body,
                     text="The setup will be downloaded and launched automatically.",
                     font=ctk.CTkFont(size=11),
                     text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        # Changelog
        if self._changelog:
            cl = ctk.CTkFrame(body, fg_color=BG_PANEL, corner_radius=8,
                              border_width=1, border_color=BORDER)
            cl.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(cl, text="What's new:",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=ACCENT2).pack(anchor="w", padx=12, pady=(8, 4))
            for line in self._changelog[:8]:
                row = ctk.CTkFrame(cl, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=1)
                ctk.CTkLabel(row, text="•", text_color=ACCENT2,
                             font=ctk.CTkFont(size=11), width=14).pack(side="left")
                ctk.CTkLabel(row, text=str(line),
                             font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY,
                             anchor="w", wraplength=380).pack(side="left", padx=(4, 0))
            if len(self._changelog) > 8:
                ctk.CTkLabel(cl,
                             text=f"+ {len(self._changelog) - 8} more change(s)",
                             font=ctk.CTkFont(size=10),
                             text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(2, 8))
            else:
                ctk.CTkFrame(cl, height=6, fg_color="transparent").pack()

        # Barre de progression (cachee au depart)
        self.pbar = ctk.CTkProgressBar(body, progress_color=ACCENT2,
                                        fg_color=BG_PANEL, height=8, corner_radius=4)
        self.pbar.set(0)

        self.status_lbl = ctk.CTkLabel(body, text="",
                                        font=ctk.CTkFont(size=10),
                                        text_color=TEXT_MUTED)

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", pady=(8, 0))

        self.update_btn = ctk.CTkButton(
            btn_row, text="Update now",
            fg_color=ACCENT2, hover_color=ACCENT2,
            text_color=BG_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36, corner_radius=7,
            command=self._start_download)
        self.update_btn.pack(side="left", padx=(0, 10))

        self.later_btn = ctk.CTkButton(
            btn_row, text="Later",
            fg_color="transparent", hover_color=CARD_HOVER,
            border_width=1, border_color=BORDER, text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12), height=36, corner_radius=7,
            command=self._cancel)
        self.later_btn.pack(side="left")

    def _start_download(self):
        self.update_btn.configure(state="disabled", text="Downloading...")
        self.later_btn.configure(state="disabled")
        self.pbar.pack(fill="x", pady=(0, 4))
        self.pbar.set(0)
        self.status_lbl.pack(anchor="w", pady=(0, 4))
        self.status_lbl.configure(text="Starting...")
        self.update_idletasks()
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        # Fallback out of l'URL du setup si absente ou invalide dans version.json
        FALLBACK_URL = "https://github.com/mini9dev/fakeGames/releases/download/SETUP/setup_FakeGames.exe"
        if not self._url or not self._url.startswith("http"):
            self._url = FALLBACK_URL
        tmp_path = None
        try:
            tmp_dir  = Path(tempfile.mkdtemp(prefix="fg_upd_"))
            tmp_path = tmp_dir / "FakeGames_Setup.exe"

            self.after(0, lambda: self.status_lbl.configure(text="Connecting..."))

            with requests.get(self._url, stream=True, timeout=(10, 120)) as r:
                r.raise_for_status()
                total      = int(r.headers.get("content-length") or 0)
                downloaded = 0
                with open(tmp_path, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=65536):
                        if self._cancelled:
                            return
                        if not chunk:
                            continue
                        fh.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            v = downloaded / total
                            p = int(v * 100)
                            self.after(0, lambda _v=v: self.pbar.set(_v))
                            self.after(0, lambda _p=p:
                                       self.status_lbl.configure(
                                           text=f"Downloading... {_p}%"))
                        else:
                            mb = downloaded / (1024 * 1024)
                            self.after(0, lambda _m=mb:
                                       self.status_lbl.configure(
                                           text=f"Downloading... {_m:.1f} MB"))

            if self._cancelled:
                return

            self.after(0, lambda: self.pbar.set(1.0))
            self.after(0, lambda: self.status_lbl.configure(
                text="Ready — launching setup..."))
            self.after(600, lambda: self._launch_setup(tmp_path))

        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self._on_error(
                "Connection failed. Check your network."))
        except requests.exceptions.Timeout:
            self.after(0, lambda: self._on_error(
                "Delai depasse. Reessayez ou ouvrez GitHub."))
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            self.after(0, lambda c=code: self._on_error(f"HTTP Error {c}"))
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_error(err))

    def _launch_setup(self, setup_path: Path):
        try:
            subprocess.Popen(
                [str(setup_path)],
                creationflags=subprocess.DETACHED_PROCESS |
                              subprocess.CREATE_NEW_PROCESS_GROUP
            )
        except Exception:
            try:
                os.startfile(str(setup_path))
            except Exception:
                pass
        os._exit(0)

    def _on_error(self, err: str):
        print(f"[UpdateModal] Download error: {err}")  # log console pour debug
        self.status_lbl.configure(text=f"Error: {err[:90]}")
        self.update_btn.configure(
            state="normal", text="Retry",
            fg_color=ACCENT2, hover_color="#3db866",
            text_color="#0d0f14",
            command=self._start_download)
        self.later_btn.configure(state="normal")

    def _cancel(self):
        self._cancelled = True
        self._close()

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


class Launcher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FakeGames Launcher")
        self.geometry(WINDOW_SIZE)
        icon_path = resource_path("FG-logo.ico")
        self.iconbitmap(icon_path)
        self.resizable(True, True)
        self.minsize(820, 500)
        self.configure(fg_color=BG_DARK)
        self.bind("<Configure>", lambda _e: Toast._reposition_all() if _active_toasts else None)
        self.catalog = []
        self.ads = load_ads()
        self._render_after_id = None
        self._disk_refresh_pending = False
        self._last_disk_refresh = 0
        self._current_tab = "catalogue"
        self._build_ui()
        self.set_status("Loading catalogue...", ACCENT)
        threading.Thread(target=self._load_catalogue, daemon=True).start()
        threading.Thread(target=self._refresh_ads, daemon=True).start()
        threading.Thread(target=self._check_update, daemon=True).start()
        # Discord Presence
        settings = load_settings()
        if settings.get("discord_presence", True):
            _discord_rpc.connect()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _section_label(self, parent, text, pady=(18, 6)):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=pady)

    def _divider(self, parent, pady=14):
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(fill="x", padx=14, pady=pady)

    def _empty_state(self, title, subtitle, accent=ACCENT):
        wrap = ctk.CTkFrame(self.scroll, fg_color="transparent")
        wrap.pack(expand=True, fill="both", padx=28, pady=42)
        panel = ctk.CTkFrame(wrap, fg_color=BG_PANEL, corner_radius=10, border_width=1, border_color=BORDER)
        panel.pack(expand=True)
        ctk.CTkLabel(
            panel, text="FG",
            font=ctk.CTkFont(family="Segoe UI Black", size=26, weight="bold"),
            text_color=accent, fg_color="#0b0f18", corner_radius=8, width=72, height=52,
        ).pack(padx=46, pady=(30, 14))
        ctk.CTkLabel(panel, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY).pack(padx=46)
        ctk.CTkLabel(
            panel, text=subtitle, font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED, wraplength=360, justify="center",
        ).pack(padx=46, pady=(6, 30))

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color=BG_HEADER, height=64, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        brand = ctk.CTkFrame(hdr, fg_color="transparent")
        brand.pack(side="left", padx=20, pady=9)
        brand_title = ctk.CTkFrame(brand, fg_color="transparent")
        brand_title.pack(anchor="w")
        ctk.CTkLabel(brand_title, text="FAKEGAMES",
                     font=ctk.CTkFont(family="Segoe UI Black", size=21, weight="bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(brand_title, text="LAUNCHER",
                     font=ctk.CTkFont(family="Segoe UI", size=21),
                     text_color=TEXT_MUTED).pack(side="left", padx=(6, 0))
        ctk.CTkLabel(brand, text="Catalogue & custom fake games",
                     font=ctk.CTkFont(size=10), text_color="#4f5870").pack(anchor="w")

        status_box = ctk.CTkFrame(hdr, fg_color=BG_PANEL, corner_radius=8, border_width=1, border_color=BORDER)
        status_box.pack(side="right", padx=18, pady=14)
        self.status_dot = ctk.CTkLabel(status_box, text="*", font=ctk.CTkFont(size=12), text_color=ACCENT)
        self.status_dot.pack(side="left", padx=(10, 6))
        self.status_lbl = ctk.CTkLabel(status_box, text="", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.status_lbl.pack(side="left", padx=(0, 10), pady=5)

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(body, width=220, fg_color=BG_SIDEBAR, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self._section_label(sidebar, "NAVIGATION", pady=(18, 7))

        self.tab_catalogue_btn = ctk.CTkButton(
            sidebar, text="Catalogue",
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12, weight="bold"), height=38, corner_radius=7,
            command=lambda: self._switch_tab("catalogue"),
        )
        self.tab_catalogue_btn.pack(fill="x", padx=14, pady=(0, 4))

        self.tab_custom_btn = ctk.CTkButton(
            sidebar, text="My custom games",
            fg_color="transparent", hover_color=CARD_HOVER,
            border_width=1, border_color=BORDER, text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12, weight="bold"), height=38, corner_radius=7,
            command=lambda: self._switch_tab("custom"),
        )
        self.tab_custom_btn.pack(fill="x", padx=14, pady=(0, 4))

        self.tab_settings_btn = ctk.CTkButton(
            sidebar, text="Settings",
            fg_color="transparent", hover_color=CARD_HOVER,
            border_width=1, border_color=BORDER, text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12, weight="bold"), height=38, corner_radius=7,
            command=lambda: self._switch_tab("settings"),
        )
        self.tab_settings_btn.pack(fill="x", padx=14, pady=(0, 14))

        self._divider(sidebar, pady=(0, 14))

        self.search_slot = ctk.CTkFrame(sidebar, fg_color="transparent", height=132)
        self.search_slot.pack(fill="x")
        self.search_slot.pack_propagate(False)

        self.search_section = ctk.CTkFrame(self.search_slot, fg_color="transparent")
        self.search_section.pack(fill="x")
        self._section_label(self.search_section, "FILTRES & TRIS", pady=(0, 6))
        self.search_var = ctk.StringVar()
        ctk.CTkEntry(
            self.search_section, textvariable=self.search_var,
            placeholder_text="Search...",
            fg_color=BG_INPUT, border_color=BORDER, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12), height=36, corner_radius=7,
        ).pack(fill="x", padx=14, pady=(0, 10))
        self.search_var.trace_add("write", lambda *_: self._schedule_render())

        self.sort_var = ctk.StringVar(value="Catalogue order")
        ctk.CTkOptionMenu(
            self.search_section, variable=self.sort_var,
            values=["Catalogue order", "Name (A-Z)", "Installed first"],
            fg_color=BG_INPUT, button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12), corner_radius=7, height=34,
            command=lambda _: self._render(),
        ).pack(fill="x", padx=14, pady=(0, 14))

        self.stats_panel = ctk.CTkFrame(sidebar, fg_color=BG_PANEL, corner_radius=8, border_width=1, border_color=BORDER)
        self.stats_panel.pack(fill="x", padx=14, pady=(0, 2))
        self.count_lbl = ctk.CTkLabel(self.stats_panel, text="", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.count_lbl.pack(anchor="w", padx=12, pady=(9, 2))
        self.installed_count_lbl = ctk.CTkLabel(
            self.stats_panel, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT2
        )
        self.installed_count_lbl.pack(anchor="w", padx=12, pady=(0, 9))

        self._divider(sidebar, pady=14)

        ctk.CTkButton(
            sidebar, text="+ Create a fake game",
            fg_color=ACCENT3, hover_color="#c07820", text_color="#0d0f14",
            font=ctk.CTkFont(size=12, weight="bold"), height=38, corner_radius=7,
            command=self._open_create_modal,
        ).pack(fill="x", padx=14, pady=(0, 8))



        ctk.CTkFrame(sidebar, height=1, fg_color=BORDER).pack(side="bottom", fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(sidebar, text=f"v{CURRENT_VERSION} - FakeGames Launcher", font=ctk.CTkFont(size=9), text_color=TEXT_MUTED).pack(
            side="bottom", pady=(0, 4)
        )
        self.disk_lbl = ctk.CTkLabel(sidebar, text="0 MB used", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED)
        self.disk_lbl.pack(side="bottom", pady=(0, 2))

        self.scroll = ctk.CTkScrollableFrame(
            body, fg_color=BG_DARK, scrollbar_button_color=BORDER, scrollbar_button_hover_color=ACCENT
        )
        self.scroll.pack(side="left", fill="both", expand=True)
        self.scroll.grid_columnconfigure(0, weight=1)

    def _switch_tab(self, tab):
        self._current_tab = tab
        # Reset tous les boutons nav
        for btn in (self.tab_catalogue_btn, self.tab_custom_btn, self.tab_settings_btn):
            btn.configure(fg_color="transparent", hover_color=CARD_HOVER,
                          text_color=TEXT_MUTED, border_width=1, border_color=BORDER)
        if tab == "catalogue":
            self.tab_catalogue_btn.configure(
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                text_color=TEXT_PRIMARY, border_width=0)
            if not self.search_section.winfo_manager():
                self.search_section.pack(fill="x")
        elif tab == "custom":
            self.tab_custom_btn.configure(
                fg_color=ACCENT3, hover_color="#c07820",
                text_color="#0d0f14", border_width=0)
            self.search_section.pack_forget()
        elif tab == "settings":
            self.tab_settings_btn.configure(
                fg_color="#3a3f52", hover_color="#4a5068",
                text_color=TEXT_PRIMARY, border_width=0)
            self.search_section.pack_forget()
        self._render()


    def set_status(self, txt, color=TEXT_MUTED):
        self.status_lbl.configure(text=txt)
        self.status_dot.configure(text_color=color)

    def toast(self, msg, color=ACCENT2):
        try:
            Toast(self, msg, color=color)
        except Exception:
            pass

    def _schedule_render(self, delay=160):
        if self._render_after_id:
            self.after_cancel(self._render_after_id)
        self._render_after_id = self.after(delay, self._run_scheduled_render)

    def _run_scheduled_render(self):
        self._render_after_id = None
        self._render()

    def _refresh_ads(self):
        try:
            ads = fetch_remote_ads()
            if ads:
                self.after(0, lambda: setattr(self, "ads", ads))
        except Exception:
            pass

    def _load_catalogue(self):
        cached = load_catalogue_cache()
        if cached:
            self.catalog = cached
            self.after(0, lambda: self.set_status(
                f"{len(self.catalog)} games (cached)", ACCENT2))
            self.after(0, self._render)

        def _refresh():
            try:
                fresh = fetch_remote_catalogue()
                save_catalogue_cache(fresh)
                changed = (fresh != self.catalog)
                self.catalog = fresh
                self.after(0, lambda: self.set_status(
                    f"{len(self.catalog)} games available", ACCENT2))
                if changed:
                    self.after(0, self._render)
            except Exception as e:
                if not cached:
                    self.catalog = []
                    self.after(0, lambda: self.set_status("Loading error", RED_SOFT))
                    self.after(0, lambda: self.toast(
                        f"Catalogue unavailable: {e}", RED_SOFT))
                    self.after(0, self._render)

        threading.Thread(target=_refresh, daemon=True).start()


    def _is_installed(self, name):
        return (DOWNLOADS_DIR / sanitize_name(name)).exists()

    def _render(self):
        if self._current_tab == "catalogue":
            self._render_catalogue()
        elif self._current_tab == "custom":
            self._render_custom()
        elif self._current_tab == "settings":
            self._render_settings()

    def _clear_scroll(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.scroll.update_idletasks()

    def _render_catalogue(self):
        self._clear_scroll()
        query = self.search_var.get().lower()
        filtered = [g for g in self.catalog if query in g.get("name", "").lower()]
        sv = self.sort_var.get()
        if sv == "Installeds en premier":
            filtered.sort(key=lambda g: not self._is_installed(g.get("name", "")))
        elif sv == "Name (A-Z)":
            filtered.sort(key=lambda g: g.get("name", "").lower())
        self._update_counts(len(filtered))
        if not filtered:
            self._empty_state(
                "No game found",
                "Change your search or reset the sort to see the full catalogue.",
                accent=ACCENT,
            )
            return
        for i, game in enumerate(filtered):
            card = GameCard(
                self.scroll, game,
                on_download=self._start_download,
                on_launch=self._launch,
                on_uninstall=self._uninstall,
                on_ad_before_download=self._show_ad_before_download,
                installed=self._is_installed(game.get("name", "")),
                is_custom=False,
            )
            card.pack(fill="x", padx=18, pady=(8 if i == 0 else 4, 4))
            img_url = game.get("image")
            if img_url:
                threading.Thread(target=lambda u=img_url, c=card: self._load_img(u, c), daemon=True).start()

    def _render_custom(self):
        self._clear_scroll()
        custom_games = []
        if CUSTOM_DIR.exists():
            for folder in sorted(CUSTOM_DIR.iterdir()):
                if folder.is_dir():
                    meta = folder / ".fakegame_meta"
                    display_name = meta.read_text(encoding="utf-8").strip() if meta.exists() else folder.name
                    custom_games.append({
                        "name": display_name,
                        "_folder": folder.name,
                        "description": "Fake game created locally.",
                        "_path": str(folder),
                    })
        self._update_counts()
        if not custom_games:
            self._empty_state(
                "No custom games yet",
                "Create your first fake game using the orange button in the sidebar.",
                accent=ACCENT3,
            )
            return
        for i, game in enumerate(custom_games):
            card = GameCard(
                self.scroll, game,
                on_download=self._start_download,
                on_launch=self._launch,
                on_uninstall=self._uninstall_custom,
                on_ad_before_download=None,
                installed=True, is_custom=True,
            )
            card.pack(fill="x", padx=18, pady=(8 if i == 0 else 4, 4))

    def _render_settings(self):
        self._clear_scroll()
        current = load_settings().get("theme", "Dark")

        def _section(title, color=TEXT_PRIMARY):
            ctk.CTkLabel(self.scroll, text=title,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=color).pack(anchor="w", padx=32, pady=(18, 6))
            ctk.CTkFrame(self.scroll, height=1, fg_color=BORDER).pack(fill="x", padx=32, pady=(0, 8))

        def _on_theme_select(name):
            s = load_settings()
            s["theme"] = name
            save_settings(s)
            self.toast(f"Theme '{name}' applied — restart the app for full effect.", ACCENT)
            self._render_settings()

        # ── Titre ──
        ctk.CTkLabel(self.scroll, text="Settings",
                     font=ctk.CTkFont(family="Segoe UI Black", size=20, weight="bold"),
                     text_color=ACCENT).pack(anchor="w", padx=32, pady=(24, 4))

        # ── Thème ──
        _section("Appearance — Visual theme")

        for name, desc, acc in [
            ("Dark",   "Dark background, blue accent",  "#5865f2"),
            ("Light",  "Light background, dark text",    "#5865f2"),
            ("Purple", "Dark background, purple accent", "#9b59f5"),
        ]:
            is_active = (name == current)
            row = ctk.CTkFrame(self.scroll,
                               fg_color=BG_CARD if is_active else "transparent",
                               corner_radius=8, border_width=1,
                               border_color=acc if is_active else BORDER)
            row.pack(fill="x", padx=32, pady=3)

            ctk.CTkFrame(row, width=12, height=12, fg_color=acc,
                         corner_radius=6).pack(side="left", padx=(14, 10), pady=16)
            ctk.CTkLabel(row, text=name,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(row, text=f"  —  {desc}",
                         font=ctk.CTkFont(size=11),
                         text_color=TEXT_MUTED).pack(side="left")

            if is_active:
                ctk.CTkLabel(row, text="✓ Active",
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=acc).pack(side="right", padx=14)
            else:
                ctk.CTkButton(row, text="Select", width=80, height=28,
                              corner_radius=6, fg_color="transparent",
                              hover_color=CARD_HOVER, border_width=1,
                              border_color=BORDER, text_color=TEXT_MUTED,
                              font=ctk.CTkFont(size=11),
                              command=lambda n=name: _on_theme_select(n),
                              ).pack(side="right", padx=14, pady=8)

        # ── Discord Presence ──
        _section("Discord Presence")

        discord_enabled = load_settings().get("discord_presence", True)

        discord_row = ctk.CTkFrame(self.scroll,
                                   fg_color=BG_CARD if discord_enabled else "transparent",
                                   corner_radius=8, border_width=1,
                                   border_color="#5865f2" if discord_enabled else BORDER)
        discord_row.pack(fill="x", padx=32, pady=3)

        ctk.CTkFrame(discord_row, width=12, height=12, fg_color="#5865f2",
                     corner_radius=6).pack(side="left", padx=(14, 10), pady=16)
        ctk.CTkLabel(discord_row, text="Show status on Discord",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(discord_row, text="  —  Rich Presence on your profile",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")

        def _toggle_discord():
            s = load_settings()
            new_val = not s.get("discord_presence", True)
            s["discord_presence"] = new_val
            save_settings(s)
            if new_val:
                _discord_rpc.connect()
                self.toast("Discord Presence enabled", "#5865f2")
            else:
                _discord_rpc.disconnect()
                self.toast("Discord Presence disabled", TEXT_MUTED)
            self._render_settings()

        toggle_text = "✓ Enabled" if discord_enabled else "Enable"
        toggle_fg   = "#5865f2" if discord_enabled else "transparent"
        ctk.CTkButton(discord_row, text=toggle_text, width=90, height=28,
                      corner_radius=6, fg_color=toggle_fg,
                      hover_color="#4752c4", border_width=0 if discord_enabled else 1,
                      border_color=BORDER,
                      text_color=TEXT_PRIMARY if discord_enabled else TEXT_MUTED,
                      font=ctk.CTkFont(size=11),
                      command=_toggle_discord,
                      ).pack(side="right", padx=14, pady=8)

        # ── Danger ──
        _section("Danger zone", color=RED_SOFT)

        ctk.CTkLabel(self.scroll,
                     text="Deletes all downloaded games, custom games and image cache.",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
                     wraplength=600, justify="left").pack(anchor="w", padx=32, pady=(0, 8))

        ctk.CTkButton(self.scroll, text="Reset cache & games",
                      fg_color="transparent", hover_color="#2a1520",
                      border_width=1, border_color=RED_SOFT, text_color=RED_SOFT,
                      font=ctk.CTkFont(size=12), height=36, corner_radius=7,
                      command=self._reset_cache).pack(anchor="w", padx=32, pady=(0, 24))

    def _load_img(self, url, card):
        img = load_image_cached(url, size=(160, 90))
        if img:
            self.after(0, lambda: card.set_image(img) if card.winfo_exists() else None)

    def _show_ad_before_download(self, on_continue, on_cancel):
        ad = random.choice(self.ads or [default_ad()])
        AdModal(self, ad=ad, on_continue=on_continue, on_cancel=on_cancel)

    def _start_download(self, game, progress_cb, retry_cb, done_cb):
        name = game.get("name", "")
        url = game.get("download_url") or game.get("url")
        dest = DOWNLOADS_DIR / sanitize_name(name)

        def _ui_retry(attempt, max_retries):
            self.after(0, lambda: self.set_status(f"Timeout - attempt {attempt}/{max_retries}...", ACCENT3))
            self.after(0, lambda: self.toast(f"Slow connection - attempt {attempt}/{max_retries}", ACCENT3))

        def worker():
            ok, err = download_zip_with_progress(
                url, dest, progress_cb=progress_cb,
                retry_cb=lambda a, m: (retry_cb(a, m), _ui_retry(a, m))
            )
            if ok:
                self.after(0, lambda: self.set_status(f"{name} installed", ACCENT2))
                self.after(0, lambda: self.toast(f"{name} successfully installed!"))
                self.after(0, self._update_counts)
            else:
                friendly = err
                if "timed out" in err.lower() or "timeout" in err.lower():
                    friendly = "Failed after 3 attempts.\nCheck your connection and try again."
                self.after(0, lambda: self.toast(f"Error: {friendly}", RED_SOFT))
            done_cb(ok, err)

        threading.Thread(target=worker, daemon=True).start()

    def _update_counts(self, filtered_count=None):
        installed = sum(1 for g in self.catalog if self._is_installed(g.get("name", "")))
        custom_count = sum(1 for f in CUSTOM_DIR.iterdir() if f.is_dir()) if CUSTOM_DIR.exists() else 0
        self.installed_count_lbl.configure(text=f"{installed} installed  |  {custom_count} custom")
        if filtered_count is not None:
            total = len(self.catalog)
            if filtered_count == total:
                self.count_lbl.configure(text=f"{total} game(s) in catalogue")
            else:
                self.count_lbl.configure(text=f"{filtered_count} out of {total} game(s)")
        elif self._current_tab == "custom":
            self.count_lbl.configure(text=f"{custom_count} custom game(s)")
        elif self._current_tab == "settings":
            self.count_lbl.configure(text="Settings")
        self._schedule_disk_refresh()

    def _schedule_disk_refresh(self):
        now = time.monotonic()
        if self._disk_refresh_pending or now - self._last_disk_refresh < 1.5:
            return
        self._disk_refresh_pending = True
        self._last_disk_refresh = now

        def worker():
            mb = get_folder_size_mb(DOWNLOADS_DIR) + get_folder_size_mb(CUSTOM_DIR)
            self.after(0, lambda: self._finish_disk_refresh(mb))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_disk_refresh(self, mb):
        self._disk_refresh_pending = False
        self.disk_lbl.configure(text=f"{mb / 1024:.2f} GB used" if mb >= 1024 else f"{mb:.1f} MB used")

    def _launch(self, path: Path):
        exe = find_executable(path)
        try:
            if exe:
                os.startfile(str(exe))
            else:
                os.startfile(str(path))
            self.toast(f"Launching {path.name}...")
            if load_settings().get("discord_presence", True):
                _discord_rpc.set_playing(path.name)
        except Exception as e:
            self.toast(f"Error: {e}", RED_SOFT)

    def _uninstall(self, game, card):
        name = game.get("name", "")
        folder = DOWNLOADS_DIR / sanitize_name(name)
        try:
            shutil.rmtree(folder)
            self.toast(f"{name} deleted", TEXT_MUTED)
            self._render()
        except PermissionError:
            self.toast(f"Close '{name}' before deleting it.", RED_SOFT)
        except Exception as e:
            self.toast(f"Error: {e}", RED_SOFT)

    def _uninstall_custom(self, game, card):
        name = game.get("name", "")
        folder_name = game.get("_folder", sanitize_name(name))
        folder = CUSTOM_DIR / folder_name
        try:
            shutil.rmtree(folder)
            self.toast(f"Custom game '{name}' deleted", TEXT_MUTED)
            self._render()
        except PermissionError:
            self.toast(f"Close '{name}' before deleting it.", RED_SOFT)
        except Exception as e:
            self.toast(f"Error: {e}", RED_SOFT)

    def _reset_cache(self):
        try:
            if CATALOGUE_CACHE.exists():
                CATALOGUE_CACHE.unlink()
        except Exception:
            pass
        self.set_status("Resetting...", ACCENT3)

        def worker():
            for folder in (IMAGE_CACHE_DIR, DOWNLOADS_DIR, CUSTOM_DIR):
                try:
                    if folder.exists():
                        shutil.rmtree(folder)
                    folder.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    self.after(0, lambda: self.toast("Reset failed. Close all open games first.", RED_SOFT))
                    self.after(0, lambda: self.set_status("Reset blocked", RED_SOFT))
                    return
                except Exception as e:
                    self.after(0, lambda err=e: self.toast(f"Reset error: {err}", RED_SOFT))
                    self.after(0, lambda: self.set_status("Reset error", RED_SOFT))
                    return
            _IMAGE_MEMORY_CACHE.clear()
            self.after(0, self._finish_reset_cache)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_reset_cache(self):
        self.toast("Cache and games cleared", TEXT_MUTED)
        self.set_status("Cache cleared")
        self._last_disk_refresh = 0
        self._render()

    def _open_create_modal(self):
        modal = CreateGameModal(self, on_success=self._on_custom_game_created)
        modal.focus()

    def _check_update(self):
        latest, url, changelog = check_for_update()
        if latest:
            self.after(800, lambda: UpdateModal(self, latest, url, changelog))

    def _on_close(self):
        _discord_rpc.disconnect()
        self.destroy()

    def _on_custom_game_created(self, exe_path):
        self.toast("Custom game created!", ACCENT3)
        self._update_counts()
        self.after(600, lambda: self._switch_tab("custom"))


if __name__ == "__main__":
    Launcher().mainloop()
