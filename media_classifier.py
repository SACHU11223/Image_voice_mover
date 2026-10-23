"""
Media Classifier - Audio & Video Sorter
Lightweight (works on 4GB RAM)
Folders created:
  Audio/Bhakti
  Audio/New_Song_2000_2026
  Audio/Old_Song_Till_1999
  Video/Bhakti
  Video/New_Song_2000_2026
  Video/Old_Song_Till_1999
  Unsorted (fallback)
"""

import os
import re
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Optional libraries
try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

try:
    import acoustid
    HAS_ACOUSTID = True
except ImportError:
    HAS_ACOUSTID = False

# ================== CONFIG ==================
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv"}

BHAKTI_KEYWORDS = [
    "bhajan", "bhakti", "shiv", "shiva", "ram", "rama", "krishna", "krishan",
    "hanuman", "chalisa", "aarti", "arti", "devotional", "bhagwan", "ganesh",
    "ganesha", "durga", "maa", "mata", "om", "mantra", "stotra", "kirtan",
    "sai", "baba", "vishnu", "lakshmi", "saraswati", "radhe", "radha",
    "mahabharat", "ramayan", "geeta", "gita", "bhakti sangeet", "devi"
]

# AcoustID free API key (user can change; public demo key works limited)
ACOUSTID_API_KEY = "8XaBELgH"   # free public key for testing; get your own at acoustid.org

BG = "#0a0a0e"
PANEL = "#12121a"
ACCENT = "#00d4ff"
GREEN = "#2ed573"
RED = "#ff4757"
ORANGE = "#ffa502"


class MediaClassifierApp:
    def __init__(self, parent=None):
        if parent is None:
            self.root = tk.Tk()
            self.own_root = True
        else:
            self.root = parent
            self.own_root = False

        self.root.title("Media Classifier - Audio & Video Sorter")
        self.root.configure(bg=BG)
        self.root.geometry("900x650")
        self.root.minsize(700, 500)

        self.source_path = None
        self.dest_path = None
        self.log_text = None

        self._build_ui()
        if self.own_root:
            self.root.mainloop()

    def _build_ui(self):
        for w in self self.root.winfo_children():
            w.destroy()

        # Header
        header = tk.Frame(self.root, bg=PANEL, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🎵  Media Classifier  (Audio + Video Sorter)",
                 font=("Segoe UI", 18, "bold"), fg="white", bg=PANEL).pack(side="left", padx=20, pady=12)

        if not self.own_root:
            tk.Button(header, text="← Menu", font=("Segoe UI", 10),
                      bg="#333", fg="white", relief="flat", padx=12,
                      command=self._go_back).pack(side="right", padx=15, pady=12)

        # Main content
        main = tk.Frame(self.root, bg=BG)
        main.pack(expand=True, fill="both", padx=25, pady=15)

        # Info
        info = tk.Label(main,
                        text="Scans folder → Detects Audio/Video → Sorts into Bhakti / Old Songs (≤1999) / New Songs (2000-2026)",
                        font=("Segoe UI", 11), fg="#aaaaaa", bg=BG, wraplength=800)
        info.pack(pady=(0, 15))

        # Source folder
        src_frame = tk.Frame(main, bg=BG)
        src_frame.pack(fill="x", pady=6)
        tk.Label(src_frame, text="Source Folder:", font=("Segoe UI", 11, "bold"),
                 fg="#ccc", bg=BG, width=14, anchor="w").pack(side="left")
        self.src_var = tk.StringVar(value="Not selected")
        tk.Label(src_frame, textvariable=self.src_var, font=("Segoe UI", 10),
                 fg=ACCENT, bg=BG, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(src_frame, text="Browse", font=("Segoe UI", 10),
                  bg=ACCENT, fg="black", relief="flat", padx=12,
                  command=self._select_source).pack(side="right")

        # Dest folder
        dst_frame = tk.Frame(main, bg=BG)
        dst_frame.pack(fill="x", pady=6)
        tk.Label(dst_frame, text="Destination:", font=("Segoe UI", 11, "bold"),
                 fg="#ccc", bg=BG, width=14, anchor="w").pack(side="left")
        self.dst_var = tk.StringVar(value="Same as Source (subfolders will be created)")
        tk.Label(dst_frame, textvariable=self.dst_var, font=("Segoe UI", 10),
                 fg="#888", bg=BG, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(dst_frame, text="Browse", font=("Segoe UI", 10),
                  bg="#444", fg="white", relief="flat", padx=12,
                  command=self._select_dest).pack(side="right")

        # Options
        opt_frame = tk.Frame(main, bg=BG)
        opt_frame.pack(fill="x", pady=10)

        self.use_acoustid = tk.BooleanVar(value=HAS_ACOUSTID)
        tk.Checkbutton(opt_frame, text="Use online fingerprint (pyacoustid) for unknown files",
                       variable=self.use_acoustid, font=("Segoe UI", 10),
                       fg="#ccc", bg=BG, selectcolor="#222", activebackground=BG,
                       activeforeground="white").pack(side="left")

        # Status of libs
        lib_status = []
        lib_status.append("mutagen ✅" if HAS_MUTAGEN else "mutagen ❌")
        lib_status.append("pyacoustid ✅" if HAS_ACOUSTID else "pyacoustid ❌")
        tk.Label(opt_frame, text="  |  Libs: " + "  ".join(lib_status),
                 font=("Segoe UI", 9), fg="#666", bg=BG).pack(side="left", padx=10)

        # Run button
        self.run_btn = tk.Button(main, text="▶  START CLASSIFY & MOVE",
                                 font=("Segoe UI", 13, "bold"),
                                 bg=GREEN, fg="black", relief="flat",
                                 padx=30, pady=10, command=self._run)
        self.run_btn.pack(pady=12)

        # Progress
        self.progress = ttk.Progressbar(main, mode="determinate", length=700)
        self.progress.pack(pady=5)

        # Log area
        tk.Label(main, text="Log:", font=("Segoe UI", 10, "bold"), fg="#ccc", bg=BG).pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(main, height=14, font=("Consolas", 9),
                                                  bg="#111118", fg="#dddddd",
                                                  insertbackground="white", relief="flat")
        self.log_text.pack(fill="both", expand=True, pady=5)

        self._log("Ready. Select Source folder and click START.")
        if not HAS_MUTAGEN:
            self._log("⚠ Install mutagen:  pip install mutagen")
        if not HAS_ACOUSTID:
            self._log("⚠ Install pyacoustid:  pip install pyacoustid   (optional, needs fpcalc)")

    def _go_back(self):
        for w in self.root.winfo_children():
            w.destroy()
        from main import show_main_menu
        show_main_menu(self.root)

    def _select_source(self):
        path = filedialog.askdirectory(title="Select Source Folder (contains audio/video)")
        if path:
            self.source_path = path
            self.src_var.set(path)
            if not self.dest_path:
                self.dst_var.set(path + "  (subfolders will be created here)")

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
            messagebox.showwarning("Missing", "Please select Source folder first.")
            return

        dest_root = self.dest_path or self.source_path
        self.run_btn.config(state="disabled", text="Working...")
        self.progress["value"] = 0
        self._log("\n" + "="*50)
        self._log(f"Source : {self.source_path}")
        self._log(f"Dest   : {dest_root}")
        self._log("="*50)

        try:
            self._classify_and_move(self.source_path, dest_root)
        except Exception as e:
            self._log(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.run_btn.config(state="normal", text="▶  START CLASSIFY & MOVE")

    def _classify_and_move(self, source, dest_root):
        source = Path(source)
        dest_root = Path(dest_root)

        # Create target folders
        folders = {
            "audio_bhakti": dest_root / "Audio" / "Bhakti",
            "audio_new":    dest_root / "Audio" / "New_Song_2000_2026",
            "audio_old":    dest_root / "Audio" / "Old_Song_Till_1999",
            "video_bhakti": dest_root / "Video" / "Bhakti",
            "video_new":    dest_root / "Video" / "New_Song_2000_2026",
            "video_old":    dest_root / "Video" / "Old_Song_Till_1999",
            "unsorted":     dest_root / "Unsorted",
        }
        for p in folders.values():
            p.mkdir(parents=True, exist_ok=True)

        # Collect files
        files = []
        for f in source.rglob("*"):
            if f.is_file() and f.suffix.lower() in (AUDIO_EXTS | VIDEO_EXTS):
                # skip already inside our target folders
                if any(str(f).startswith(str(p)) for p in folders.values()):
                    continue
                files.append(f)

        total = len(files)
        if total == 0:
            self._log("No audio/video files found.")
            return

        self._log(f"Found {total} media files. Starting classification...\n")
        self.progress["maximum"] = total

        stats = {k: 0 for k in folders}
        moved = 0

        for i, fpath in enumerate(files, 1):
            self.progress["value"] = i
            try:
                category = self._decide_category(fpath)
                target_dir = folders[category]
                dest_file = target_dir / fpath.name

                # avoid overwrite
                if dest_file.exists():
                    stem = fpath.stem
                    suffix = fpath.suffix
                    c = 1
                    while dest_file.exists():
                        dest_file = target_dir / f"{stem}_{c}{suffix}"
                        c += 1

                shutil.move(str(fpath), str(dest_file))
                stats[category] += 1
                moved += 1
                self._log(f"[{i}/{total}] {fpath.name}  →  {category}")
            except Exception as e:
                self._log(f"[{i}/{total}] FAIL {fpath.name}: {e}")
                stats["unsorted"] += 1

        self._log("\n" + "="*40)
        self._log(f"✅ Done! Moved {moved} files")
        for k, v in stats.items():
            if v:
                self._log(f"   {k}: {v}")
        self._log("="*40)
        messagebox.showinfo("Finished", f"Moved {moved} files successfully!")

    def _decide_category(self, fpath: Path) -> str:
        """Return one of: audio_bhakti, audio_new, audio_old, video_bhakti, ... unsorted"""
        is_audio = fpath.suffix.lower() in AUDIO_EXTS
        prefix = "audio_" if is_audio else "video_"

        title = fpath.stem.lower()
        year = None
        meta_title = ""

        # 1. Local metadata with mutagen
        if HAS_MUTAGEN:
            try:
                audio = MutagenFile(fpath, easy=True)
                if audio is not None:
                    if "title" in audio:
                        meta_title = " ".join(audio["title"]).lower()
                    if "date" in audio:
                        year = self._extract_year(str(audio["date"][0]))
                    elif "year" in audio:
                        year = self._extract_year(str(audio["year"][0]))
            except Exception:
                pass

        # 2. Online fingerprint (only for audio, optional)
        if is_audio and self.use_acoustid.get() and HAS_ACOUSTID and (not year or not meta_title):
            try:
                results = acoustid.match(ACOUSTID_API_KEY, str(fpath), parse=False)
                for score, rid, title, artist in results:
                    if score > 0.5:
                        if title:
                            meta_title = (meta_title + " " + title).lower()
                        # year not always available from simple match
                        break
            except Exception:
                pass

        # Combine titles for keyword search
        search_text = (title + " " + meta_title).lower()

        # 3. Bhakti check
        for kw in BHAKTI_KEYWORDS:
            if kw in search_text:
                return prefix + "bhakti"

        # 4. Year based
        if year is None:
            year = self._extract_year(title)  # try from filename

        if year is not None:
            if year <= 1999:
                return prefix + "old"
            elif 2000 <= year <= 2026:
                return prefix + "new"

        # Fallback
        return "unsorted"

    def _extract_year(self, text: str):
        """Find 4-digit year between 1900-2026 in text"""
        if not text:
            return None
        matches = re.findall(r"\b(19[0-9]{2}|20[0-2][0-6])\b", str(text))
        if matches:
            return int(matches[0])
        return None


if __name__ == "__main__":
    MediaClassifierApp()
