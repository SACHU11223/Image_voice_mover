"""
Media Classifier - Safe & Lightweight Version
=============================================
- NO extra software needed (no fpcalc, no chromaprint)
- Only uses mutagen (optional) + filename
- Dry Run mode by default (safe)
- Strict rules so random files are NOT moved
"""

import os
import re
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Optional - pure Python
try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

# ================== CONFIG ==================
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv"}

# Strong Bhakti keywords only (to avoid random matches)
BHAKTI_KEYWORDS = [
    "bhajan", "bhakti", "chalisa", "aarti", "arti", "kirtan",
    "hanuman", "shiv", "shiva", "ram bhajan", "krishna bhajan",
    "radhe", "radha", "sai baba", "devotional", "bhagwan",
    "ganesh aarti", "durga aarti", "om namah", "mantra",
    "ramayan", "mahabharat", "geeta", "gita"
]

BG = "#0a0a0e"
PANEL = "#12121a"
ACCENT = "#00d4ff"
GREEN = "#2ed573"
ORANGE = "#ffa502"
RED = "#ff4757"


class MediaClassifierApp:
    def __init__(self, parent=None):
        if parent is None:
            self.root = tk.Tk()
            self.own_root = True
        else:
            self.root = parent
            self.own_root = False

        self.root.title("Media Classifier - Safe Mode")
        self.root.configure(bg=BG)
        self.root.geometry("920x700")
        self.root.minsize(700, 520)

        self.source_path = None
        self.dest_path = None

        self._build_ui()
        if self.own_root:
            self.root.mainloop()

    def _build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        # Header
        header = tk.Frame(self.root, bg=PANEL, height=58)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🎵  Media Classifier  (Safe Mode)",
                 font=("Segoe UI", 17, "bold"), fg="white", bg=PANEL).pack(side="left", padx=18, pady=12)

        if not self.own_root:
            tk.Button(header, text="← Menu", font=("Segoe UI", 10),
                      bg="#333", fg="white", relief="flat", padx=12,
                      command=self._go_back).pack(side="right", padx=14, pady=12)

        main = tk.Frame(self.root, bg=BG)
        main.pack(expand=True, fill="both", padx=22, pady=10)

        # Info
        tk.Label(main,
                 text="No extra software needed. Uses only filename + optional mutagen tags.\n"
                      "Dry Run ON = sirf dikhayega kya hoga (safe). Dry Run OFF = actually move karega.",
                 font=("Segoe UI", 10), fg="#aaaaaa", bg=BG, justify="left").pack(anchor="w", pady=(0, 10))

        # Source
        src_frame = tk.Frame(main, bg=BG)
        src_frame.pack(fill="x", pady=4)
        tk.Label(src_frame, text="Source Folder:", font=("Segoe UI", 11, "bold"),
                 fg="#ccc", bg=BG, width=13, anchor="w").pack(side="left")
        self.src_var = tk.StringVar(value="Not selected")
        tk.Label(src_frame, textvariable=self.src_var, font=("Segoe UI", 10),
                 fg=ACCENT, bg=BG, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(src_frame, text="Browse", font=("Segoe UI", 10),
                  bg=ACCENT, fg="black", relief="flat", padx=12,
                  command=self._select_source).pack(side="right")

        # Dest
        dst_frame = tk.Frame(main, bg=BG)
        dst_frame.pack(fill="x", pady=4)
        tk.Label(dst_frame, text="Destination:", font=("Segoe UI", 11, "bold"),
                 fg="#ccc", bg=BG, width=13, anchor="w").pack(side="left")
        self.dst_var = tk.StringVar(value="Same as Source")
        tk.Label(dst_frame, textvariable=self.dst_var, font=("Segoe UI", 10),
                 fg="#888", bg=BG, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(dst_frame, text="Browse", font=("Segoe UI", 10),
                  bg="#444", fg="white", relief="flat", padx=12,
                  command=self._select_dest).pack(side="right")

        # Options
        opt = tk.Frame(main, bg=BG)
        opt.pack(fill="x", pady=10)

        self.dry_run = tk.BooleanVar(value=True)   # DEFAULT SAFE
        tk.Checkbutton(opt, text="Dry Run (recommended) - sirf dikhayega, move nahi karega",
                       variable=self.dry_run, font=("Segoe UI", 10, "bold"),
                       fg=ORANGE, bg=BG, selectcolor="#222",
                       activebackground=BG, activeforeground=ORANGE).pack(anchor="w")

        self.only_bhakti = tk.BooleanVar(value=False)
        tk.Checkbutton(opt, text="Only sort bas Bhakti files (baaki chhod do)",
                       variable=self.only_bhakti, font=("Segoe UI", 10),
                       fg="#ccc", bg=BG, selectcolor="#222",
                       activebackground=BG, activeforeground="white").pack(anchor="w", pady=2)

        self.rename_files = tk.BooleanVar(value=False)
        tk.Checkbutton(opt, text="Rename files if good Title found in tags",
                       variable=self.rename_files, font=("Segoe UI", 10),
                       fg="#ccc", bg=BG, selectcolor="#222",
                       activebackground=BG, activeforeground="white").pack(anchor="w")

        # Lib status
        status = "mutagen ✅" if HAS_MUTAGEN else "mutagen ❌ (pip install mutagen)"
        tk.Label(opt, text=f"Library: {status}", font=("Segoe UI", 9),
                 fg="#666", bg=BG).pack(anchor="w", pady=4)

        # Buttons
        btn_frame = tk.Frame(main, bg=BG)
        btn_frame.pack(pady=8)

        self.run_btn = tk.Button(btn_frame, text="▶  START (Dry Run)",
                                 font=("Segoe UI", 12, "bold"),
                                 bg=GREEN, fg="black", relief="flat",
                                 padx=28, pady=9, command=self._run)
        self.run_btn.pack(side="left", padx=6)

        # Progress
        self.progress = ttk.Progressbar(main, mode="determinate", length=720)
        self.progress.pack(pady=4)

        # Log
        tk.Label(main, text="Log:", font=("Segoe UI", 10, "bold"), fg="#ccc", bg=BG).pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(main, height=14, font=("Consolas", 9),
                                                  bg="#111118", fg="#dddddd",
                                                  insertbackground="white", relief="flat")
        self.log_text.pack(fill="both", expand=True, pady=4)

        self._log("Ready.")
        self._log("• Dry Run ON = safe (sirf dikhayega)")
        self._log("• Dry Run OFF = actually folders bana ke files move karega")
        if not HAS_MUTAGEN:
            self._log("⚠ Better results ke liye:  pip install mutagen")

    def _go_back(self):
        for w in self.root.winfo_children():
            w.destroy()
        from main import show_main_menu
        show_main_menu(self.root)

    def _select_source(self):
        path = filedialog.askdirectory(title="Select Source Folder")
        if path:
            self.source_path = path
            self.src_var.set(path)
            if not self.dest_path:
                self.dst_var.set(path + "  (subfolders yahin banenge)")

    def _select_dest(self):
        path = filedialog.askdirectory(title="Select Destination Folder")
        if path:
            self.dest_path = path
            self.dst_var.set(path)

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _run(self):
        if not self.source_path:
            messagebox.showwarning("Missing", "Pehle Source folder select karo.")
            return

        dest_root = self.dest_path or self.source_path
        is_dry = self.dry_run.get()

        self.run_btn.config(state="disabled", text="Working...")
        self.progress["value"] = 0

        self._log("\n" + "="*55)
        self._log(f"Mode     : {'DRY RUN (safe)' if is_dry else 'REAL MOVE'}")
        self._log(f"Source   : {self.source_path}")
        self._log(f"Dest     : {dest_root}")
        self._log("="*55)

        try:
            self._process(self.source_path, dest_root, is_dry)
        except Exception as e:
            self._log(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.run_btn.config(state="normal",
                                text="▶  START (Dry Run)" if self.dry_run.get() else "▶  START REAL MOVE")

    def _process(self, source, dest_root, is_dry):
        source = Path(source)
        dest_root = Path(dest_root)

        folders = {
            "audio_bhakti": dest_root / "Audio" / "Bhakti",
            "audio_new":    dest_root / "Audio" / "New_Song_2000_2026",
            "audio_old":    dest_root / "Audio" / "Old_Song_Till_1999",
            "video_bhakti": dest_root / "Video" / "Bhakti",
            "video_new":    dest_root / "Video" / "New_Song_2000_2026",
            "video_old":    dest_root / "Video" / "Old_Song_Till_1999",
            "unsorted":     dest_root / "Unsorted",
        }

        if not is_dry:
            for p in folders.values():
                p.mkdir(parents=True, exist_ok=True)

        # Collect files
        files = []
        for f in source.rglob("*"):
            if f.is_file() and f.suffix.lower() in (AUDIO_EXTS | VIDEO_EXTS):
                # skip already inside target folders
                if any(str(f).startswith(str(p)) for p in folders.values()):
                    continue
                files.append(f)

        total = len(files)
        if total == 0:
            self._log("Koi audio/video file nahi mili.")
            return

        self._log(f"Found {total} files\n")
        self.progress["maximum"] = total

        stats = {k: 0 for k in folders}
        will_move = 0
        skipped = 0

        for i, fpath in enumerate(files, 1):
            self.progress["value"] = i
            try:
                category, new_name, reason = self._decide(fpath)

                if category is None:
                    # Not confident → skip
                    skipped += 1
                    self._log(f"[{i}/{total}] SKIP  {fpath.name}")
                    self._log(f"         reason: {reason}")
                    continue

                target_dir = folders[category]
                final_name = new_name if (new_name and self.rename_files.get()) else fpath.name
                dest_file = target_dir / final_name

                # unique name
                if not is_dry and dest_file.exists():
                    stem = Path(final_name).stem
                    suffix = Path(final_name).suffix
                    c = 1
                    while dest_file.exists():
                        dest_file = target_dir / f"{stem}_{c}{suffix}"
                        c += 1

                stats[category] += 1
                will_move += 1

                action = "WOULD MOVE" if is_dry else "MOVED"
                self._log(f"[{i}/{total}] {action}  {fpath.name}")
                if new_name and self.rename_files.get() and new_name != fpath.name:
                    self._log(f"         → rename : {final_name}")
                self._log(f"         → folder : {category}")
                self._log(f"         → reason : {reason}")

                if not is_dry:
                    shutil.move(str(fpath), str(dest_file))

            except Exception as e:
                self._log(f"[{i}/{total}] FAIL {fpath.name}: {e}")

        self._log("\n" + "="*50)
        if is_dry:
            self._log(f"DRY RUN complete")
            self._log(f"Would move : {will_move} files")
            self._log(f"Skipped    : {skipped} files (not confident)")
            self._log("\nAgar sahi lag raha hai to Dry Run OFF karke phir se chalao.")
        else:
            self._log(f"REAL MOVE complete")
            self._log(f"Moved   : {will_move} files")
            self._log(f"Skipped : {skipped} files")

        for k, v in stats.items():
            if v:
                self._log(f"   {k}: {v}")
        self._log("="*50)

        if is_dry:
            messagebox.showinfo("Dry Run Done",
                                f"Would move {will_move} files\nSkipped {skipped} files\n\n"
                                "Check log. Agar theek hai to Dry Run OFF karke dubara chalao.")
        else:
            messagebox.showinfo("Done", f"Moved {will_move} files\nSkipped {skipped} files")

    def _decide(self, fpath: Path):
        """
        Returns (category or None, new_name or None, reason)
        category = None means SKIP (not confident)
        """
        is_audio = fpath.suffix.lower() in AUDIO_EXTS
        prefix = "audio_" if is_audio else "video_"
        name_lower = fpath.stem.lower()

        title = ""
        artist = ""
        year = None

        # ---- 1. Local tags (mutagen) ----
        if HAS_MUTAGEN:
            try:
                meta = MutagenFile(fpath, easy=True)
                if meta:
                    if "title" in meta and meta["title"]:
                        title = str(meta["title"][0]).strip()
                    if "artist" in meta and meta["artist"]:
                        artist = str(meta["artist"][0]).strip()
                    if "date" in meta and meta["date"]:
                        year = self._extract_year(str(meta["date"][0]))
                    elif "year" in meta and meta["year"]:
                        year = self._extract_year(str(meta["year"][0]))
            except Exception:
                pass

        search_text = f"{name_lower} {title} {artist}".lower()

        # ---- 2. Strong Bhakti check ----
        is_bhakti = any(kw in search_text for kw in BHAKTI_KEYWORDS)

        if is_bhakti:
            new_name = self._make_name(artist, title, fpath.suffix) if title else None
            return prefix + "bhakti", new_name, "Bhakti keyword found"

        # If user selected "Only Bhakti" → stop here
        if self.only_bhakti.get():
            return None, None, "Only Bhakti mode - no keyword"

        # ---- 3. Year based (only if clear year found) ----
        if year is None:
            year = self._extract_year(name_lower)
            if year is None and title:
                year = self._extract_year(title)

        if year is not None:
            new_name = self._make_name(artist, title, fpath.suffix) if title else None
            if year <= 1999:
                return prefix + "old", new_name, f"Year {year} (Old)"
            elif 2000 <= year <= 2026:
                return prefix + "new", new_name, f"Year {year} (New)"

        # ---- 4. Not confident → SKIP ----
        return None, None, "No clear Bhakti keyword or Year found"

    def _make_name(self, artist, title, ext):
        def clean(s):
            if not s:
                return ""
            s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s[:70]

        title = clean(title)
        artist = clean(artist)
        if not title:
            return None
        if artist:
            return f"{artist} - {title}{ext}"
        return f"{title}{ext}"

    def _extract_year(self, text):
        if not text:
            return None
        matches = re.findall(r"\b(19[5-9][0-9]|20[0-2][0-6])\b", str(text))
        if matches:
            return int(matches[0])
        return None


if __name__ == "__main__":
    MediaClassifierApp()
