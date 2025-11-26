import os, threading, requests, zipfile, shutil, tempfile, subprocess
from pathlib import Path
from io import BytesIO
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import messagebox

# ---------------- CONFIG ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

CATALOGUE_URL = "https://github.com/mini9dev/fakeGames/releases/download/Catalogue/catalogue.json"
DOWNLOADS_DIR = Path("fakeGames_downloads")
IMAGE_CACHE_DIR = Path("cache_images")
WINDOW_SIZE = "980x540"

DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- UTIL ----------------
def sanitize_name(name: str) -> str:
    return "".join(ch for ch in name if ch not in '<>:"/\\|?*').strip()

def find_executable(folder: Path):
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".exe"):
                return Path(root) / f
    return None

def load_image_cached(url: str, size=(128, 72)):
    if not url:
        return None
    local = IMAGE_CACHE_DIR / url.split("/")[-1]
    try:
        if not local.exists():
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            local.write_bytes(r.content)
        img = Image.open(local)
        img.thumbnail(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def download_zip_with_progress(url: str, target_dir: Path, progress_cb=None):
    try:
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length") or 0)
            downloaded = 0
            with tempfile.NamedTemporaryFile(delete=False) as tmpf:
                tmp_name = tmpf.name
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    tmpf.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb:
                        progress_cb(downloaded, total)
        try:
            with zipfile.ZipFile(tmp_name, 'r') as z:
                target_dir.mkdir(parents=True, exist_ok=True)
                z.extractall(target_dir)
        except zipfile.BadZipFile:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(tmp_name, target_dir / "game.exe")
            return True, ""
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        return True, ""
    except Exception as e:
        return False, str(e)

# ---------------- GUI ----------------
class Launcher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FakeGames Launcher")
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)
        self.font_title = ctk.CTkFont(size=18, weight="bold")
        self.font_subtitle = ctk.CTkFont(size=13)
        self.font_small = ctk.CTkFont(size=11)

        # HEADER
        header = ctk.CTkFrame(self, fg_color="#1c1c1c", height=60, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="🎮 FakeGames Launcher", font=self.font_title, padx=12).pack(side="left", pady=10)
        self.status_label = ctk.CTkLabel(header, text="", anchor="e")
        self.status_label.pack(side="right", padx=14)

        # MAIN SPLIT
        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True)

        # LEFT PANEL (barre de recherche + catalogue)
        left_panel = ctk.CTkFrame(content, corner_radius=10)
        left_panel.pack(side="left", fill="both", expand=True, padx=(12,6), pady=10)

        # Barre de recherche + reset cache (PERMANENTS)
        search_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_frame.pack(fill="x", padx=8, pady=(4,2))

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            width=420,
            textvariable=self.search_var,
            placeholder_text="Rechercher un jeu..."
        )
        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", lambda e: self.render_catalogue())

        reset_btn = ctk.CTkButton(
            search_frame,
            text="Reset cache",
            width=130,
            command=self.reset_cache
        )
        reset_btn.pack(side="right", padx=(6,0))

        # ScrollableFrame catalogue (SEULEMENT les cartes jeux)
        self.left_scroll = ctk.CTkScrollableFrame(left_panel, corner_radius=10)
        self.left_scroll.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # RIGHT: téléchargés
        right = ctk.CTkFrame(content, width=260, corner_radius=10)
        right.pack(side="right", fill="y", padx=(6,12), pady=10)
        ctk.CTkLabel(right, text="Jeux installés", font=self.font_subtitle).pack(pady=(10,4))
        self.right_scroll = ctk.CTkScrollableFrame(right)
        self.right_scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # FOOTER
        footer = ctk.CTkFrame(self, height=40)
        footer.pack(fill="x", pady=(0,10))
        self.global_progress = ctk.CTkProgressBar(footer, width=400)
        self.global_progress.set(0)
        self.global_progress.pack_forget()

        # data
        self.catalog = []
        self.cards = []
        self.set_status("Chargement du catalogue...")
        threading.Thread(target=self.load_catalogue, daemon=True).start()
        self.refresh_downloaded_list()

    def set_status(self, txt):
        self.status_label.configure(text=txt)

    def load_catalogue(self):
        try:
            r = requests.get(CATALOGUE_URL, timeout=10)
            r.raise_for_status()
            data = r.json()
            self.catalog = data if isinstance(data, list) else [data]
        except Exception as e:
            self.catalog = []
            self.after(0, lambda: messagebox.showerror("Erreur", f"Chargement du catalogue impossible:\n{e}"))
        self.after(0, self.render_catalogue)

    def render_catalogue(self):
        # on efface UNIQUEMENT le contenu du scroll, pas la barre de recherche
        for w in self.left_scroll.winfo_children():
            w.destroy()

        query = self.search_var.get().lower() if hasattr(self, "search_var") else ""
        filtered_catalog = [game for game in self.catalog if query in game.get("name", "").lower()]

        if not filtered_catalog:
            ctk.CTkLabel(self.left_scroll, text="Aucun jeu dans le catalogue.").pack(pady=12)
            return

        self.cards.clear()

        for game in filtered_catalog:
            name = game.get("name", "Inconnu")
            desc = game.get("description", "")
            url = game.get("download_url") or game.get("url")
            image_url = game.get("image")

            frame = ctk.CTkFrame(self.left_scroll, corner_radius=12)
            frame.pack(fill="x", pady=8, padx=8)

            img_label = ctk.CTkLabel(frame, text="")
            img_label.pack(side="left", padx=8, pady=8)
            if image_url:
                threading.Thread(target=lambda: self.load_image(image_url, img_label), daemon=True).start()

            info = ctk.CTkFrame(frame, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=8, pady=8)
            ctk.CTkLabel(info, text=name, font=self.font_subtitle, anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=desc, font=self.font_small, anchor="w", justify="left").pack(fill="x", pady=(4,0))

            right = ctk.CTkFrame(frame, fg_color="transparent", width=140)
            right.pack(side="right", padx=8, pady=8)

            pbar = ctk.CTkProgressBar(right, width=120)
            pbar.set(0)
            pbar.pack_forget()

            folder = DOWNLOADS_DIR / sanitize_name(name)
            btn = ctk.CTkButton(
                right,
                text="Lancer" if folder.exists() else "Télécharger",
                width=110,
                command=(lambda p=folder: self.launch_folder_or_exe(p))
                if folder.exists()
                else (lambda g=game, pb=pbar: self.start_download(g, pb))
            )
            btn.pack()
            self.cards.append({"game": game, "pbar": pbar, "btn": btn})

        self.set_status(f"{len(filtered_catalog)} jeux chargés")

    def load_image(self, url, label):
        img = load_image_cached(url)
        if img:
            self.after(0, lambda: (label.configure(image=img), setattr(label, "image", img)))

    def start_download(self, game, pbar):
        name = game.get("name", "Jeu")
        url = game.get("download_url") or game.get("url")
        dest = DOWNLOADS_DIR / sanitize_name(name)
        if dest.exists():
            return messagebox.showinfo("Info", "Déjà téléchargé.")

        def cb(dl, total):
            val = dl / total if total else 0
            self.after(0, lambda: (pbar.set(val), self.global_progress.set(val)))
            self.set_status(f"Téléchargement {name}: {int(val*100)}%")

        def worker():
            self.after(0, lambda: pbar.pack(pady=(4,6)))
            self.after(0, lambda: self.global_progress.pack(pady=10))

            ok, err = download_zip_with_progress(url, dest, progress_cb=cb)

            self.after(0, lambda: pbar.pack_forget())
            self.after(0, lambda: self.global_progress.pack_forget())
            self.after(0, self.global_progress.set, 0)

            if ok:
                self.set_status(f"{name} installé")
                self.refresh_downloaded_list()
                self.after(0, self.update_btn_for(name))
            else:
                messagebox.showerror("Erreur", err)

        threading.Thread(target=worker, daemon=True).start()

    def update_btn_for(self, name):
        for c in self.cards:
            if c["game"].get("name") == name:
                folder = DOWNLOADS_DIR / sanitize_name(name)
                c["btn"].configure(text="Lancer", command=lambda: self.launch_folder_or_exe(folder))

    def refresh_downloaded_list(self):
        for w in self.right_scroll.winfo_children():
            w.destroy()
        for entry in DOWNLOADS_DIR.iterdir():
            if not entry.is_dir():
                continue
            display_name = entry.name
            if len(display_name) > 11:
                display_name = display_name[:9] + ".."
            frame = ctk.CTkFrame(self.right_scroll)
            frame.pack(fill="x", padx=8, pady=6)
            ctk.CTkLabel(frame, text=display_name, font=self.font_subtitle).pack(side="left", padx=10)
            ctk.CTkButton(frame, text="Lancer", width=90,
                          command=lambda p=entry: self.launch_folder_or_exe(p)).pack(side="right", padx=8)

    def launch_folder_or_exe(self, path):
        exe = find_executable(path)
        try:
            if exe:
                os.startfile(str(exe))
            else:
                os.startfile(str(path))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def reset_cache(self):
        for folder in [IMAGE_CACHE_DIR, DOWNLOADS_DIR]:
            try:
                if folder.exists():
                    shutil.rmtree(folder)
                folder.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Erreur: Assurez-vous que tout est bien fermé.", f"Impossible de réinitialiser {folder} : {e}")
        self.set_status("Cache et téléchargements supprimés.")
        self.refresh_downloaded_list()
        self.render_catalogue()

if __name__ == "__main__":
    Launcher().mainloop()
