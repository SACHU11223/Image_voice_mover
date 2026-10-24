"""
Media Mover - Grid style sorter (same as Image Sorter)
=====================================================
- Grid view of Audio + Video files
- Ctrl+Click multi-select
- Drag & Drop to folders
- No year / auto classification
- Many formats supported
- Lightweight (no extra software)
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps

# ================== CONFIG ==================
AUDIO_EXTS = {
    ".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma",
    ".aiff", ".aif", ".opus", ".amr", ".m4b", ".mp2"
}
VIDEO_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".3gp", ".3g2", ".mpg", ".mpeg", ".ts", ".m2ts",
    ".vob", ".ogv", ".mts", ".f4v", ".asf", ".rm", ".rmvb"
}
ALL_EXTS = AUDIO_EXTS | VIDEO_EXTS

GRID_COLS = 4
GRID_ROWS = 4
PAGE_SIZE = GRID_COLS * GRID_ROWS  # 16

BG_COLOR = "#0a0a0e"
PANEL_BG = "#12121a"
ACCENT = "#00d4ff"
SELECT_COLOR = "#1e90ff"
CARD_BG = "#1a1a24"
CARD_BG_SEL = "#1e3a5f"

NUMBER_COLORS = ["#ff4757", "#2ed573", "#1e90ff", "#ffa502", "#a55eea",
                 "#ff6b81", "#7bed9f", "#70a1ff", "#eccc68", "#5352ed",
                 "#ff6348", "#2f3542", "#ff9ff3", "#54a0ff", "#5f27cd", "#00d2d3"]


class MediaMover:
    def __init__(self, parent=None):
        if parent is None:
            self.root = tk.Tk()
            self.own_root = True
        else:
            self.root = parent
            self.own_root = False

        self.root.title("Media Mover - Audio & Video")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("1200x750")
        self.root.minsize(950, 600)

        self.current_folder = None
        self.media_paths = []
        self.page = 0
        self.photo_refs = []
        self.selected = set()
        self.folders = []
        self.status_var = tk.StringVar(value="Select a Drive first")
        self.cell_labels = {}

        self._build_start_ui()
        if self.own_root:
            self.root.mainloop()

    # ---------- START SCREEN ----------
    def _build_start_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        title = tk.Label(frame, text="🎵 Media Mover",
                         font=("Segoe UI", 28, "bold"), fg="#ffffff", bg=BG_COLOR)
        title.pack(pady=(20, 8))

        sub = tk.Label(frame, text="Audio + Video • Grid view • Ctrl+Click • Drag to folders",
                       font=("Segoe UI", 13), fg="#888888", bg=BG_COLOR)
        sub.pack(pady=(0, 25))

        # Formats info
        fmt = tk.Label(frame,
                       text="Supports: mp4 mkv avi mov 3gp webm flv  |  mp3 wav flac m4a aac ogg + more",
                       font=("Segoe UI", 10), fg="#555", bg=BG_COLOR)
        fmt.pack(pady=(0, 20))

        drive_frame = tk.Frame(frame, bg=BG_COLOR)
        drive_frame.pack(pady=8)

        tk.Label(drive_frame, text="1. Select Drive:", font=("Segoe UI", 12),
                 fg="#cccccc", bg=BG_COLOR).pack(side="left", padx=(0, 12))

        self.drive_var = tk.StringVar()
        drives = self._get_drives()
        if drives:
            self.drive_var.set(drives[0])
        drive_menu = tk.OptionMenu(drive_frame, self.drive_var, *drives)
        drive_menu.config(font=("Segoe UI", 11), bg="#1a1a24", fg="white",
                          activebackground=ACCENT, highlightthickness=0)
        drive_menu["menu"].config(bg="#1a1a24", fg="white")
        drive_menu.pack(side="left")

        btn = tk.Button(frame, text="2. Select Folder & Start",
                        font=("Segoe UI", 14, "bold"),
                        bg=ACCENT, fg="#000000", activebackground="#00b8e0",
                        relief="flat", padx=32, pady=12,
                        command=self._select_folder)
        btn.pack(pady=30)

        if not self.own_root:
            back_btn = tk.Button(frame, text="← Back to Menu",
                                 font=("Segoe UI", 11),
                                 bg="#333", fg="white", relief="flat", padx=16, pady=6,
                                 command=self._go_back)
            back_btn.pack(pady=8)

        status = tk.Label(frame, textvariable=self.status_var,
                          font=("Segoe UI", 10), fg="#666666", bg=BG_COLOR)
        status.pack(side="bottom", pady=12)

        info = tk.Label(frame,
                        text="Ctrl+Click = multi select   |   Drag → Folder   |   N = Refill   |   Esc = Exit",
                        font=("Segoe UI", 10), fg="#555555", bg=BG_COLOR)
        info.pack(side="bottom")

    def _go_back(self):
        for w in self.root.winfo_children():
            w.destroy()
        from main import show_main_menu
        show_main_menu(self.root)

    def _get_drives(self):
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives or ["C:\\"]

    def _select_folder(self):
        start = self.drive_var.get()
        folder = filedialog.askdirectory(initialdir=start, title="Select Media Folder")
        if not folder:
            return
        self.current_folder = folder
        self._load_media()
        if not self.media_paths:
            messagebox.showinfo("No Media", "Is folder me koi supported audio/video nahi mili.")
            return
        self._enter_fullscreen()

    def _load_media(self):
        files = []
        for f in os.listdir(self.current_folder):
            full = os.path.join(self.current_folder, f)
            if os.path.isfile(full) and os.path.splitext(f)[1].lower() in ALL_EXTS:
                files.append(full)
        files.sort(key=lambda x: os.path.basename(x).lower())
        self.media_paths = files
        self.page = 0
        self.selected.clear()

    def _load_folders(self):
        self.folders = []
        try:
            for name in sorted(os.listdir(self.current_folder), key=str.lower):
                full = os.path.join(self.current_folder, name)
                if os.path.isdir(full):
                    self.folders.append(name)
        except Exception:
            pass

    # ---------- FULLSCREEN ----------
    def _enter_fullscreen(self):
        for w in self.root.winfo_children():
            w.destroy()

        self.root.attributes("-fullscreen", True)
        self.root.configure(bg=BG_COLOR)
        self.root.bind("<Escape>", lambda e: self._exit_fullscreen())
        self.root.bind("<Left>", lambda e: self._change_page(-1))
        self.root.bind("<Right>", lambda e: self._change_page(1))
        self.root.bind("<n>", lambda e: self._refill_grid())
        self.root.bind("<N>", lambda e: self._refill_grid())

        # Top bar
        top = tk.Frame(self.root, bg=PANEL_BG, height=44)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.page_label = tk.Label(top, text="", font=("Segoe UI", 12, "bold"),
                                   fg="#ffffff", bg=PANEL_BG)
        self.page_label.pack(side="left", padx=16)

        self.status_label = tk.Label(top, text="Ctrl+Click to select  •  Drag to folder",
                                     font=("Segoe UI", 11), fg=ACCENT, bg=PANEL_BG)
        self.status_label.pack(side="right", padx=16)

        # Main area
        main = tk.Frame(self.root, bg=BG_COLOR)
        main.pack(expand=True, fill="both")

        self.grid_frame = tk.Frame(main, bg=BG_COLOR)
        self.grid_frame.pack(side="left", expand=True, fill="both")

        # RIGHT panel
        self.folder_panel = tk.Frame(main, bg=PANEL_BG, width=220)
        self.folder_panel.pack(side="right", fill="y")
        self.folder_panel.pack_propagate(False)

        tk.Label(self.folder_panel, text="📁  Folders", font=("Segoe UI", 12, "bold"),
                 fg="#ffffff", bg=PANEL_BG).pack(pady=(10, 4))

        canvas = tk.Canvas(self.folder_panel, bg=PANEL_BG, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(self.folder_panel, orient="vertical", command=canvas.yview,
                                 bg=PANEL_BG, troughcolor=PANEL_BG)
        self.folder_list_frame = tk.Frame(canvas, bg=PANEL_BG)

        self.folder_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.folder_list_frame, anchor="nw", width=200)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=4)
        scrollbar.pack(side="right", fill="y")
        self.folder_canvas = canvas

        new_btn = tk.Button(self.folder_panel, text="+ New Folder",
                            font=("Segoe UI", 10, "bold"),
                            bg=ACCENT, fg="#000", relief="flat", pady=7,
                            command=self._create_new_folder)
        new_btn.pack(side="bottom", fill="x", padx=8, pady=8)

        self._load_folders()
        self._render_folders()
        self._render_page()

    def _exit_fullscreen(self):
        self.root.attributes("-fullscreen", False)
        for key in ["<Escape>", "<Left>", "<Right>", "<n>", "<N>"]:
            self.root.unbind(key)
        self._build_start_ui()

    def _change_page(self, delta):
        max_page = max(0, (len(self.media_paths) - 1) // PAGE_SIZE)
        new_page = self.page + delta
        if 0 <= new_page <= max_page:
            self.page = new_page
            self.selected.clear()
            self._render_page()

    def _refill_grid(self):
        max_page = max(0, (len(self.media_paths) - 1) // PAGE_SIZE)
        if self.page > max_page:
            self.page = max_page
        self.selected.clear()
        self._render_page()
        self.status_label.config(text="✅ Grid refilled", fg="#2ed573")

    # ---------- RENDER GRID ----------
    def _render_page(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.photo_refs.clear()
        self.cell_labels.clear()

        start = self.page * PAGE_SIZE
        end = min(start + PAGE_SIZE, len(self.media_paths))
        page_items = self.media_paths[start:end]

        total_pages = max(1, (len(self.media_paths) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.config(
            text=f"Page {self.page + 1}/{total_pages}   •   {len(self.media_paths)} left   •   {len(self.selected)} selected"
        )

        self.root.update_idletasks()
        w = self.grid_frame.winfo_width()
        h = self.grid_frame.winfo_height()
        if w < 50 or h < 50:
            w = self.root.winfo_screenwidth() - 220
            h = self.root.winfo_screenheight() - 50

        cell_w = w // GRID_COLS
        cell_h = h // GRID_ROWS

        for idx in range(PAGE_SIZE):
            row = idx // GRID_COLS
            col = idx % GRID_COLS
            number = idx + 1

            cell = tk.Frame(self.grid_frame, bg=BG_COLOR, width=cell_w, height=cell_h,
                            highlightthickness=0, bd=0)
            cell.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            cell.grid_propagate(False)
            self.grid_frame.grid_rowconfigure(row, weight=1, minsize=0)
            self.grid_frame.grid_columnconfigure(col, weight=1, minsize=0)

            if idx < len(page_items):
                path = page_items[idx]
                self._place_media(cell, path, number, cell_w, cell_h)
            else:
                empty = tk.Label(cell, text="", bg=BG_COLOR)
                empty.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _place_media(self, cell, path, number, cell_w, cell_h):
        is_selected = path in self.selected
        is_video = os.path.splitext(path)[1].lower() in VIDEO_EXTS

        bg = CARD_BG_SEL if is_selected else CARD_BG
        card = tk.Frame(cell, bg=bg, highlightthickness=3 if is_selected else 1,
                        highlightbackground=SELECT_COLOR if is_selected else "#2a2a3a")
        card.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)

        # Icon
        icon = "🎬" if is_video else "🎵"
        icon_lbl = tk.Label(card, text=icon, font=("Segoe UI", 36),
                            bg=bg, fg="#ffffff")
        icon_lbl.place(relx=0.5, rely=0.32, anchor="center")

        # Filename (truncated)
        name = os.path.basename(path)
        if len(name) > 28:
            name = name[:25] + "..."
        name_lbl = tk.Label(card, text=name, font=("Segoe UI", 9),
                            bg=bg, fg="#dddddd", wraplength=cell_w - 30)
        name_lbl.place(relx=0.5, rely=0.68, anchor="center")

        # Type badge
        ext = os.path.splitext(path)[1].upper().replace(".", "")
        type_lbl = tk.Label(card, text=ext, font=("Segoe UI", 8, "bold"),
                            bg="#00d4ff" if is_video else "#a55eea", fg="#000",
                            padx=6, pady=1)
        type_lbl.place(relx=0.05, rely=0.05)

        # Number badge
        num_color = NUMBER_COLORS[(number - 1) % len(NUMBER_COLORS)]
        num_lbl = tk.Label(card, text=str(number), font=("Segoe UI", 9, "bold"),
                           bg=num_color, fg="white", width=2)
        num_lbl.place(relx=0.95, rely=0.05, anchor="ne")

        # Bind events to all parts of card
        for widget in (card, icon_lbl, name_lbl, type_lbl, num_lbl):
            widget.media_path = path
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Control-Button-1>", self._on_ctrl_click)
            widget.bind("<B1-Motion>", self._on_drag_motion)
            widget.bind("<ButtonRelease-1>", self._on_drag_release)
            widget.bind("<Double-Button-1>", self._on_double_click)

        self.cell_labels[path] = card

    # ---------- SELECTION ----------
    def _on_click(self, event):
        path = getattr(event.widget, "media_path", None)
        if not path:
            return
        self.selected.clear()
        self.selected.add(path)
        self._update_selection_visual()
        self._update_status()

    def _on_ctrl_click(self, event):
        path = getattr(event.widget, "media_path", None)
        if not path:
            return
        if path in self.selected:
            self.selected.discard(path)
        else:
            self.selected.add(path)
        self._update_selection_visual()
        self._update_status()

    def _on_double_click(self, event):
        """Open file with default player"""
        path = getattr(event.widget, "media_path", None)
        if path and os.path.exists(path):
            try:
                os.startfile(path)   # Windows
            except Exception:
                pass

    def _update_selection_visual(self):
        self._render_page()

    def _update_status(self):
        count = len(self.selected)
        if count == 0:
            self.status_label.config(text="Ctrl+Click to select  •  Drag to folder", fg=ACCENT)
        else:
            self.status_label.config(
                text=f"{count} selected  •  Drag any selected item to a folder",
                fg="#ffaa00")
        total_pages = max(1, (len(self.media_paths) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.config(
            text=f"Page {self.page + 1}/{total_pages}   •   {len(self.media_paths)} left   •   {count} selected"
        )

    # ---------- DRAG & DROP ----------
    def _on_drag_motion(self, event):
        if self.selected:
            event.widget.config(cursor="fleur")

    def _on_drag_release(self, event):
        widget = event.widget
        path = getattr(widget, "media_path", None)
        if not path:
            return

        if path not in self.selected:
            self.selected.clear()
            self.selected.add(path)

        x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        y = self.root.winfo_pointery() - self.root.winfo_rooty()

        fx = self.folder_panel.winfo_rootx() - self.root.winfo_rootx()
        fy = self.folder_panel.winfo_rooty() - self.root.winfo_rooty()
        fw = self.folder_panel.winfo_width()
        fh = self.folder_panel.winfo_height()

        if fx <= x <= fx + fw and fy <= y <= fy + fh:
            target_folder = self._find_folder_under_pointer()
            if target_folder:
                self._move_selected_to(target_folder)
            else:
                self.status_label.config(text="Drop on a folder name", fg="#ff4757")

        try:
            widget.config(cursor="hand2")
        except Exception:
            pass

    def _find_folder_under_pointer(self):
        px = self.root.winfo_pointerx()
        py = self.root.winfo_pointery()
        for child in self.folder_list_frame.winfo_children():
            try:
                for sub in child.winfo_children():
                    if hasattr(sub, "folder_name"):
                        sx = sub.winfo_rootx()
                        sy = sub.winfo_rooty()
                        sw = sub.winfo_width()
                        sh = sub.winfo_height()
                        if sx <= px <= sx + sw and sy <= py <= sy + sh:
                            return sub.folder_name
            except Exception:
                continue
        return None

    def _move_selected_to(self, folder_name):
        if not self.selected:
            return

        dest_dir = os.path.join(self.current_folder, folder_name)
        moved = 0
        to_remove = []

        for src in list(self.selected):
            if not os.path.exists(src):
                continue
            dest = os.path.join(dest_dir, os.path.basename(src))
            try:
                shutil.move(src, dest)
                to_remove.append(src)
                moved += 1
            except Exception as e:
                print("Move error:", e)

        for p in to_remove:
            if p in self.media_paths:
                self.media_paths.remove(p)
            self.selected.discard(p)

        self._load_folders()
        self._render_folders()
        self._render_page()

        if moved:
            self.status_label.config(
                text=f"✅ Moved {moved} files → {folder_name}", fg="#2ed573")
        else:
            self.status_label.config(text="Nothing moved", fg="#ff4757")

    # ---------- FOLDERS ----------
    def _render_folders(self):
        for w in self.folder_list_frame.winfo_children():
            w.destroy()

        if not self.folders:
            tk.Label(self.folder_list_frame, text="No folders\nCreate one ↓",
                     font=("Segoe UI", 10), fg="#666", bg=PANEL_BG,
                     justify="center").pack(pady=25)
            return

        for name in self.folders:
            f = tk.Frame(self.folder_list_frame, bg="#1a1a24", pady=2)
            f.pack(fill="x", pady=2, padx=2)

            lbl = tk.Label(f, text=f"📂  {name}", font=("Segoe UI", 11),
                           fg="#eeeeee", bg="#1a1a24", anchor="w", cursor="hand2",
                           padx=8, pady=8)
            lbl.pack(fill="x")
            lbl.folder_name = name

            lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg="#2a2a3a"))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(bg="#1a1a24"))
            lbl.bind("<Button-1>", lambda e, n=name: self._on_folder_click(n))

    def _on_folder_click(self, folder_name):
        if self.selected:
            self._move_selected_to(folder_name)

    def _create_new_folder(self):
        name = simpledialog.askstring("New Folder", "Enter folder name:", parent=self.root)
        if not name:
            return
        name = name.strip()
        if not name:
            return
        path = os.path.join(self.current_folder, name)
        try:
            os.makedirs(path, exist_ok=True)
            self._load_folders()
            self._render_folders()
            self.status_label.config(text=f"Folder created: {name}", fg="#2ed573")
        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg="#ff4757")


if __name__ == "__main__":
    MediaMover()
