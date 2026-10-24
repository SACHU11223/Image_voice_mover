"""
Image Duplicate Remover
=======================
- Scan folder + all subfolders
- Find truly similar images (~50%+ match)
- 4x4 responsive grid (grows with window)
- Scroll when many images
- Double-click = zoom, close button to exit zoom
- Select to PRESERVE, rest → temp/
"""

import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFont

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False

# ================== CONFIG ==================
IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif",
    ".heic", ".heif", ".ico", ".jfif", ".raw", ".cr2", ".nef", ".arw"
}

HASH_THRESHOLD = 8
GRID_COLS = 4

BG = "#0a0a0e"
PANEL = "#12121a"
ACCENT = "#00d4ff"
SELECT_COLOR = "#2ed573"
ORANGE = "#ffa502"
RED = "#ff4757"
GREEN = "#2ed573"

NUMBER_COLORS = ["#ff4757", "#2ed573", "#1e90ff", "#ffa502", "#a55eea",
                 "#ff6b81", "#7bed9f", "#70a1ff", "#eccc68", "#5352ed",
                 "#ff6348", "#2f3542", "#ff9ff3", "#54a0ff", "#5f27cd"]


class DuplicateRemover:
    def __init__(self, parent=None):
        if parent is None:
            self.root = tk.Tk()
            self.own_root = True
        else:
            self.root = parent
            self.own_root = False

        self.root.title("Image Duplicate Remover")
        self.root.configure(bg=BG)
        self.root.geometry("1150x720")
        self.root.minsize(900, 550)

        self.root_folder = None
        self.groups = []
        self.current_group_idx = 0
        self.selected = set()
        self.photo_refs = []
        self.status_var = tk.StringVar(value="Select a folder to scan")
        self.zoom_win = None

        self._build_start_ui()
        if self.own_root:
            self.root.mainloop()

    # ---------- START ----------
    def _build_start_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(expand=True, fill="both", padx=40, pady=30)

        tk.Label(frame, text="🖼️  Image Duplicate Remover",
                 font=("Segoe UI", 26, "bold"), fg="white", bg=BG).pack(pady=(10, 6))

        tk.Label(frame, text="Scan → Group similar images → Keep selected → Rest to temp",
                 font=("Segoe UI", 11), fg="#888", bg=BG).pack(pady=(0, 20))

        if not HAS_IMAGEHASH:
            tk.Label(frame, text="⚠ Required:  pip install imagehash",
                     font=("Segoe UI", 11, "bold"), fg=ORANGE, bg=BG).pack(pady=8)

        tk.Button(frame, text="📁  Select Folder & Scan",
                  font=("Segoe UI", 14, "bold"),
                  bg=ACCENT, fg="black", relief="flat", padx=30, pady=12,
                  command=self._select_and_scan).pack(pady=15)

        if not self.own_root:
            tk.Button(frame, text="← Back to Menu", font=("Segoe UI", 11),
                      bg="#333", fg="white", relief="flat", padx=16, pady=6,
                      command=self._go_back).pack(pady=10)

        tk.Label(frame, textvariable=self.status_var,
                 font=("Segoe UI", 10), fg="#666", bg=BG).pack(side="bottom", pady=10)

        info = ("• 4×4 grid – grows when you resize window\n"
                "• Scroll when many images\n"
                "• Double-click image = Zoom  |  Close to exit zoom\n"
                "• Ctrl+Click select → PRESERVE → rest goes to temp/")
        tk.Label(frame, text=info, font=("Segoe UI", 10), fg="#555", bg=BG,
                 justify="left").pack(side="bottom", pady=15)

    def _go_back(self):
        self._close_zoom()
        for w in self.root.winfo_children():
            w.destroy()
        from main import show_main_menu
        show_main_menu(self.root)

    def _select_and_scan(self):
        if not HAS_IMAGEHASH:
            messagebox.showerror("Missing Library", "Please install:\n\npip install imagehash")
            return

        folder = filedialog.askdirectory(title="Select Root Folder to Scan")
        if not folder:
            return

        self.root_folder = folder
        self.status_var.set("Scanning... please wait")
        self.root.update()

        try:
            self._scan_and_group(folder)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Scan failed")
            return

        if not self.groups:
            messagebox.showinfo("Done", "Koi similar images nahi mili.")
            self.status_var.set("No similar images found")
            return

        self.current_group_idx = 0
        self.selected.clear()
        self._show_group_ui()

    def _scan_and_group(self, root):
        root = Path(root)
        all_images = []

        for f in root.rglob("*"):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                if "temp" in [p.lower() for p in f.parts]:
                    continue
                all_images.append(f)

        total = len(all_images)
        self.status_var.set(f"Found {total} images. Computing hashes...")
        self.root.update()

        phashes, ahashes = {}, {}

        for i, path in enumerate(all_images):
            try:
                with Image.open(path) as im:
                    im = im.convert("RGB")
                    if max(im.size) > 1000:
                        im.thumbnail((1000, 1000))
                    phashes[str(path)] = imagehash.phash(im)
                    ahashes[str(path)] = imagehash.average_hash(im)
            except Exception:
                continue
            if i % 15 == 0:
                self.status_var.set(f"Hashing... {i+1}/{total}")
                self.root.update()

        paths = list(phashes.keys())
        n = len(paths)
        if n < 2:
            self.groups = []
            return

        parent = {p: p for p in paths}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        self.status_var.set("Grouping similar images...")
        self.root.update()

        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = paths[i], paths[j]
                if (phashes[p1] - phashes[p2]) <= HASH_THRESHOLD and \
                   (ahashes[p1] - ahashes[p2]) <= HASH_THRESHOLD + 2:
                    union(p1, p2)

        clusters = {}
        for p in paths:
            clusters.setdefault(find(p), []).append(p)

        self.groups = [g for g in clusters.values() if len(g) >= 2]
        self.groups.sort(key=len, reverse=True)
        self.status_var.set(f"Found {len(self.groups)} groups")

    # ---------- GROUP UI ----------
    def _show_group_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        if self.current_group_idx >= len(self.groups):
            self._show_finished()
            return

        group = self.groups[self.current_group_idx]
        self.selected = set()

        top = tk.Frame(self.root, bg=PANEL, height=48)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.page_label = tk.Label(top,
            text=f"Group {self.current_group_idx + 1} / {len(self.groups)}   •   {len(group)} similar images",
            font=("Segoe UI", 13, "bold"), fg="white", bg=PANEL)
        self.page_label.pack(side="left", padx=16, pady=10)

        self.status_label = tk.Label(top, text="Ctrl+Click select  •  Double-click = Zoom",
                                     font=("Segoe UI", 11), fg=ACCENT, bg=PANEL)
        self.status_label.pack(side="right", padx=16)

        main = tk.Frame(self.root, bg=BG)
        main.pack(expand=True, fill="both")

        # LEFT – scrollable responsive grid
        left = tk.Frame(main, bg=BG)
        left.pack(side="left", expand=True, fill="both", padx=4, pady=4)

        self.canvas = tk.Canvas(left, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(left, orient="vertical", command=self.canvas.yview)
        self.grid_inner = tk.Frame(self.canvas, bg=BG)

        self.grid_inner.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.grid_inner, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _wheel(e):
            self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _wheel)

        # Resize → re-render grid with new cell size
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self._resize_job = None

        # RIGHT panel
        right = tk.Frame(main, bg=PANEL, width=200)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="Actions", font=("Segoe UI", 12, "bold"),
                 fg="white", bg=PANEL).pack(pady=(14, 8))

        tk.Label(right, text="Select images to KEEP.\nUnselected → temp/",
                 font=("Segoe UI", 10), fg="#aaa", bg=PANEL, justify="center").pack(pady=6)

        tk.Button(right, text="✅  PRESERVE\nSelected",
                  font=("Segoe UI", 12, "bold"),
                  bg=GREEN, fg="black", relief="flat", padx=10, pady=12,
                  cursor="hand2", command=self._preserve_and_next).pack(fill="x", padx=14, pady=10)

        tk.Button(right, text="Skip group →", font=("Segoe UI", 10),
                  bg="#333", fg="white", relief="flat", pady=7,
                  command=self._skip_group).pack(fill="x", padx=14, pady=3)

        tk.Button(right, text="Select All", font=("Segoe UI", 10),
                  bg="#444", fg="white", relief="flat", pady=6,
                  command=self._select_all).pack(fill="x", padx=14, pady=3)

        tk.Button(right, text="Clear Selection", font=("Segoe UI", 10),
                  bg="#444", fg="white", relief="flat", pady=6,
                  command=self._clear_selection).pack(fill="x", padx=14, pady=3)

        if not self.own_root:
            tk.Button(right, text="← Menu", font=("Segoe UI", 10),
                      bg="#222", fg="#aaa", relief="flat", pady=6,
                      command=self._go_back).pack(side="bottom", fill="x", padx=14, pady=14)

        self.root.after(80, lambda: self._render_group(group))

    def _on_canvas_resize(self, event):
        # Debounce re-render on resize
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(150, self._refresh_selection)

    def _cell_size(self):
        """Compute cell size from current canvas width (4 columns)"""
        self.canvas.update_idletasks()
        w = self.canvas.winfo_width()
        if w < 50:
            w = 700
        # 4 columns, small padding
        size = max(100, (w - 24) // GRID_COLS)
        return size

    def _render_group(self, group):
        for w in self.grid_inner.winfo_children():
            w.destroy()
        self.photo_refs.clear()

        cell = self._cell_size()

        for idx, path in enumerate(group):
            row = idx // GRID_COLS
            col = idx % GRID_COLS

            frame = tk.Frame(self.grid_inner, bg=BG, width=cell, height=cell)
            frame.grid(row=row, column=col, padx=3, pady=3)
            frame.grid_propagate(False)

            self._place_image(frame, path, idx + 1, cell, cell)

        self.grid_inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _place_image(self, cell, path, number, cell_w, cell_h):
        try:
            img = Image.open(path).convert("RGB")
            img = ImageOps.fit(img, (max(40, cell_w - 6), max(40, cell_h - 6)),
                              method=Image.Resampling.LANCZOS)

            if path in self.selected:
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, img.width-1, img.height-1],
                               outline=SELECT_COLOR, width=5)
                overlay = Image.new("RGB", img.size, SELECT_COLOR)
                img = Image.blend(img, overlay, 0.12)

            # Number badge
            bs = max(18, min(28, cell_w // 8))
            badge = Image.new("RGBA", (bs, bs), (0, 0, 0, 0))
            d = ImageDraw.Draw(badge)
            color = NUMBER_COLORS[(number - 1) % len(NUMBER_COLORS)]
            d.ellipse([0, 0, bs-1, bs-1], fill=color)
            try:
                font = ImageFont.truetype("arial.ttf", max(9, bs - 12))
            except Exception:
                font = ImageFont.load_default()
            t = str(number)
            bb = d.textbbox((0, 0), t, font=font)
            tw, th = bb[2]-bb[0], bb[3]-bb[1]
            d.text(((bs-tw)//2, (bs-th)//2 - 1), t, fill="white", font=font)

            img = img.convert("RGBA")
            img.paste(badge, (img.width - bs - 3, 3), badge)

            photo = ImageTk.PhotoImage(img)
            self.photo_refs.append(photo)

            lbl = tk.Label(cell, image=photo, bg=BG, bd=0, cursor="hand2")
            lbl.place(x=0, y=0, relwidth=1, relheight=1)
            lbl.image_path = path

            lbl.bind("<Button-1>", self._on_click)
            lbl.bind("<Control-Button-1>", self._on_ctrl_click)
            lbl.bind("<Double-Button-1>", self._on_double_click)

        except Exception:
            tk.Label(cell, text="Error", fg=RED, bg=BG).place(relx=0.5, rely=0.5, anchor="center")

    # ---------- ZOOM ----------
    def _on_double_click(self, event):
        path = getattr(event.widget, "image_path", None)
        if path:
            self._open_zoom(path)

    def _open_zoom(self, path):
        self._close_zoom()

        win = tk.Toplevel(self.root)
        win.title(Path(path).name)
        win.configure(bg="#000")
        win.attributes("-topmost", True)

        # Fit to screen roughly
        sw = self.root.winfo_screenwidth() - 80
        sh = self.root.winfo_screenheight() - 100
        win.geometry(f"{min(1000, sw)}x{min(700, sh)}")

        try:
            img = Image.open(path).convert("RGB")
            # Fit inside window
            img.thumbnail((sw - 40, sh - 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            lbl = tk.Label(win, image=photo, bg="#000")
            lbl.image = photo
            lbl.pack(expand=True, fill="both", padx=8, pady=8)

            btn = tk.Button(win, text="✕  Close", font=("Segoe UI", 11, "bold"),
                            bg=RED, fg="white", relief="flat", padx=16, pady=6,
                            command=win.destroy)
            btn.pack(pady=8)

            win.bind("<Escape>", lambda e: win.destroy)
            self.zoom_win = win

        except Exception as e:
            win.destroy()
            messagebox.showerror("Zoom Error", str(e))

    def _close_zoom(self):
        if self.zoom_win and self.zoom_win.winfo_exists():
            try:
                self.zoom_win.destroy()
            except Exception:
                pass
        self.zoom_win = None

    # ---------- SELECTION ----------
    def _on_click(self, event):
        path = getattr(event.widget, "image_path", None)
        if not path:
            return
        self.selected.clear()
        self.selected.add(path)
        self._refresh_selection()

    def _on_ctrl_click(self, event):
        path = getattr(event.widget, "image_path", None)
        if not path:
            return
        if path in self.selected:
            self.selected.discard(path)
        else:
            self.selected.add(path)
        self._refresh_selection()

    def _refresh_selection(self):
        if self.current_group_idx >= len(self.groups):
            return
        group = self.groups[self.current_group_idx]
        self._render_group(group)
        count = len(self.selected)
        total = len(group)
        self.status_label.config(
            text=f"{count} KEEP  •  {total - count} → temp  •  Double-click = Zoom",
            fg=GREEN if count else ACCENT)

    def _select_all(self):
        self.selected = set(self.groups[self.current_group_idx])
        self._refresh_selection()

    def _clear_selection(self):
        self.selected.clear()
        self._refresh_selection()

    # ---------- ACTIONS ----------
    def _preserve_and_next(self):
        group = self.groups[self.current_group_idx]
        to_move = [p for p in group if p not in self.selected]

        if not to_move and not self.selected:
            self._next_group()
            return

        if to_move:
            temp_dir = Path(self.root_folder) / "temp"
            temp_dir.mkdir(exist_ok=True)
            moved = 0
            for src in to_move:
                try:
                    src_path = Path(src)
                    dest = temp_dir / src_path.name
                    if dest.exists():
                        stem, suffix = src_path.stem, src_path.suffix
                        c = 1
                        while dest.exists():
                            dest = temp_dir / f"{stem}_{c}{suffix}"
                            c += 1
                    shutil.move(str(src_path), str(dest))
                    moved += 1
                except Exception as e:
                    print("Move error:", e)
            self.status_label.config(text=f"Moved {moved} → temp/", fg=ORANGE)
            self.root.update()

        self._next_group()

    def _skip_group(self):
        self._next_group()

    def _next_group(self):
        self._close_zoom()
        self.current_group_idx += 1
        self.selected.clear()
        if self.current_group_idx >= len(self.groups):
            self._show_finished()
        else:
            self._show_group_ui()

    def _show_finished(self):
        self._close_zoom()
        for w in self.root.winfo_children():
            w.destroy()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="✅  All groups processed",
                 font=("Segoe UI", 22, "bold"), fg=GREEN, bg=BG).pack(pady=(80, 15))

        tk.Label(frame, text=f"Unselected images moved to:\n{self.root_folder}\\temp",
                 font=("Segoe UI", 12), fg="#ccc", bg=BG, justify="center").pack(pady=10)

        tk.Button(frame, text="Scan Another Folder",
                  font=("Segoe UI", 12, "bold"),
                  bg=ACCENT, fg="black", relief="flat", padx=20, pady=10,
                  command=self._build_start_ui).pack(pady=20)

        if not self.own_root:
            tk.Button(frame, text="← Back to Menu", font=("Segoe UI", 11),
                      bg="#333", fg="white", relief="flat", padx=16, pady=6,
                      command=self._go_back).pack(pady=8)


if __name__ == "__main__":
    DuplicateRemover()
