"""
Image Duplicate Remover
=======================
- Scan folder + all subfolders
- Find truly similar images (~50%+ match, strict)
- Show ALL matching images of a group in scrollable grid
- Select images to PRESERVE
- Unselected ones move to temp/ folder in root
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

# STRICT threshold (~50%+ visual match)
HASH_THRESHOLD = 8

GRID_COLS = 4          # columns in grid
THUMB_SIZE = 160       # each image size in grid

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

        self._build_start_ui()
        if self.own_root:
            self.root.mainloop()

    def _build_start_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(expand=True, fill="both", padx=40, pady=30)

        tk.Label(frame, text="🖼️  Image Duplicate Remover",
                 font=("Segoe UI", 26, "bold"), fg="white", bg=BG).pack(pady=(10, 6))

        tk.Label(frame, text="Scan folder + subfolders → Group similar images → Keep selected → Move rest to temp",
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

        info = ("How it works:\n"
                "1. Select root folder (all subfolders scanned)\n"
                "2. Similar images shown together (ALL images of group)\n"
                "3. Ctrl+Click select images you want to KEEP\n"
                "4. Click PRESERVE → unselected move to temp/ folder")
        tk.Label(frame, text=info, font=("Segoe UI", 10), fg="#555", bg=BG,
                 justify="left").pack(side="bottom", pady=15)

    def _go_back(self):
        for w in self.root.winfo_children():
            w.destroy()
        from main import show_main_menu
        show_main_menu(self.root)

    def _select_and_scan(self):
        if not HAS_IMAGEHASH:
            messagebox.showerror("Missing Library",
                                 "Please install:\n\npip install imagehash")
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

        phashes = {}
        ahashes = {}

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
                p_dist = phashes[p1] - phashes[p2]
                a_dist = ahashes[p1] - ahashes[p2]
                if p_dist <= HASH_THRESHOLD and a_dist <= HASH_THRESHOLD + 2:
                    union(p1, p2)

        clusters = {}
        for p in paths:
            root_p = find(p)
            clusters.setdefault(root_p, []).append(p)

        self.groups = [g for g in clusters.values() if len(g) >= 2]
        self.groups.sort(key=len, reverse=True)

        self.status_var.set(f"Found {len(self.groups)} groups of similar images")

    def _show_group_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        if self.current_group_idx >= len(self.groups):
            self._show_finished()
            return

        group = self.groups[self.current_group_idx]
        self.selected = set()

        # Top bar
        top = tk.Frame(self.root, bg=PANEL, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.page_label = tk.Label(top,
            text=f"Group {self.current_group_idx + 1} / {len(self.groups)}   •   {len(group)} similar images",
            font=("Segoe UI", 13, "bold"), fg="white", bg=PANEL)
        self.page_label.pack(side="left", padx=16, pady=10)

        self.status_label = tk.Label(top, text="Select images to KEEP (Ctrl+Click)",
                                     font=("Segoe UI", 11), fg=ACCENT, bg=PANEL)
        self.status_label.pack(side="right", padx=16)

        # Main
        main = tk.Frame(self.root, bg=BG)
        main.pack(expand=True, fill="both")

        # LEFT: scrollable grid (shows ALL images of group)
        left = tk.Frame(main, bg=BG)
        left.pack(side="left", expand=True, fill="both", padx=6, pady=6)

        canvas = tk.Canvas(left, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(left, orient="vertical", command=canvas.yview)
        self.grid_inner = tk.Frame(canvas, bg=BG)

        self.grid_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.grid_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas = canvas

        # Mouse wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # RIGHT panel
        right = tk.Frame(main, bg=PANEL, width=210)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="Actions", font=("Segoe UI", 12, "bold"),
                 fg="white", bg=PANEL).pack(pady=(16, 10))

        tk.Label(right, text="Select images you want\nto KEEP.\n\nUnselected will go to\ntemp/ folder.",
                 font=("Segoe UI", 10), fg="#aaa", bg=PANEL, justify="center").pack(pady=8)

        tk.Button(right, text="✅  PRESERVE\nSelected",
                  font=("Segoe UI", 12, "bold"),
                  bg=GREEN, fg="black", relief="flat",
                  padx=12, pady=14, cursor="hand2",
                  command=self._preserve_and_next).pack(fill="x", padx=16, pady=12)

        tk.Button(right, text="Skip this group →",
                  font=("Segoe UI", 10),
                  bg="#333", fg="white", relief="flat", pady=8,
                  command=self._skip_group).pack(fill="x", padx=16, pady=4)

        tk.Button(right, text="Select All",
                  font=("Segoe UI", 10),
                  bg="#444", fg="white", relief="flat", pady=6,
                  command=self._select_all).pack(fill="x", padx=16, pady=4)

        tk.Button(right, text="Clear Selection",
                  font=("Segoe UI", 10),
                  bg="#444", fg="white", relief="flat", pady=6,
                  command=self._clear_selection).pack(fill="x", padx=16, pady=4)

        if not self.own_root:
            tk.Button(right, text="← Menu",
                      font=("Segoe UI", 10),
                      bg="#222", fg="#aaa", relief="flat", pady=6,
                      command=self._go_back).pack(side="bottom", fill="x", padx=16, pady=16)

        self._render_group(group)

    def _render_group(self, group):
        """Show ALL images in the group (scrollable)"""
        for w in self.grid_inner.winfo_children():
            w.destroy()
        self.photo_refs.clear()

        # Show every image in the group
        for idx, path in enumerate(group):
            row = idx // GRID_COLS
            col = idx % GRID_COLS

            cell = tk.Frame(self.grid_inner, bg=BG, width=THUMB_SIZE, height=THUMB_SIZE)
            cell.grid(row=row, column=col, padx=4, pady=4)
            cell.grid_propagate(False)

            self._place_image(cell, path, idx + 1, THUMB_SIZE, THUMB_SIZE)

        # Force scrollregion update
        self.grid_inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _place_image(self, cell, path, number, cell_w, cell_h):
        try:
            img = Image.open(path).convert("RGB")
            img = ImageOps.fit(img, (cell_w - 4, cell_h - 4), method=Image.Resampling.LANCZOS)

            is_sel = path in self.selected

            if is_sel:
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, img.width-1, img.height-1], outline=SELECT_COLOR, width=5)
                overlay = Image.new("RGB", img.size, SELECT_COLOR)
                img = Image.blend(img, overlay, 0.12)

            badge_size = 24
            badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
            d = ImageDraw.Draw(badge)
            color = NUMBER_COLORS[(number - 1) % len(NUMBER_COLORS)]
            d.ellipse([0, 0, badge_size-1, badge_size-1], fill=color)
            try:
                font = ImageFont.truetype("arial.ttf", 11)
            except Exception:
                font = ImageFont.load_default()
            text = str(number)
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            d.text(((badge_size-tw)//2, (badge_size-th)//2 - 1), text, fill="white", font=font)

            img = img.convert("RGBA")
            img.paste(badge, (img.width - badge_size - 3, 3), badge)

            photo = ImageTk.PhotoImage(img)
            self.photo_refs.append(photo)

            lbl = tk.Label(cell, image=photo, bg=BG, bd=0, cursor="hand2")
            lbl.place(x=0, y=0, relwidth=1, relheight=1)
            lbl.image_path = path

            lbl.bind("<Button-1>", self._on_click)
            lbl.bind("<Control-Button-1>", self._on_ctrl_click)

        except Exception:
            err = tk.Label(cell, text="Error", fg=RED, bg=BG)
            err.place(relx=0.5, rely=0.5, anchor="center")

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
        group = self.groups[self.current_group_idx]
        self._render_group(group)
        count = len(self.selected)
        total = len(group)
        self.status_label.config(
            text=f"{count} selected to KEEP  •  {total - count} will go to temp",
            fg=GREEN if count else ACCENT)

    def _select_all(self):
        group = self.groups[self.current_group_idx]
        self.selected = set(group)
        self._refresh_selection()

    def _clear_selection(self):
        self.selected.clear()
        self._refresh_selection()

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

            self.status_label.config(text=f"Moved {moved} images to temp/", fg=ORANGE)
            self.root.update()

        self._next_group()

    def _skip_group(self):
        self._next_group()

    def _next_group(self):
        self.current_group_idx += 1
        self.selected.clear()
        if self.current_group_idx >= len(self.groups):
            self._show_finished()
        else:
            self._show_group_ui()

    def _show_finished(self):
        for w in self.root.winfo_children():
            w.destroy()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="✅  All groups processed",
                 font=("Segoe UI", 22, "bold"), fg=GREEN, bg=BG).pack(pady=(80, 15))

        tk.Label(frame, text="Unselected images have been moved to:\n"
                             f"{self.root_folder}\\temp",
                 font=("Segoe UI", 12), fg="#ccc", bg=BG, justify="center").pack(pady=10)

        tk.Button(frame, text="Scan Another Folder",
                  font=("Segoe UI", 12, "bold"),
                  bg=ACCENT, fg="black", relief="flat", padx=20, pady=10,
                  command=self._build_start_ui).pack(pady=20)

        if not self.own_root:
            tk.Button(frame, text="← Back to Menu",
                      font=("Segoe UI", 11),
                      bg="#333", fg="white", relief="flat", padx=16, pady=6,
                      command=self._go_back).pack(pady=8)


if __name__ == "__main__":
    DuplicateRemover()
