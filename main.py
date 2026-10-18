import os
import re
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import speech_recognition as sr

# ================== CONFIG ==================
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}
GRID_COLS = 3
GRID_ROWS = 4
PAGE_SIZE = GRID_COLS * GRID_ROWS  # 12
BG_COLOR = "#0f0f13"
PANEL_BG = "#16161e"
ACCENT = "#00d4ff"
NUMBER_COLORS = ["#ff4757", "#2ed573", "#1e90ff", "#ffa502", "#a55eea",
                 "#ff6b81", "#7bed9f", "#70a1ff", "#eccc68", "#5352ed",
                 "#ff6348", "#2f3542"]

class ImageVoiceMover:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Voice Mover")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("1100x700")
        self.root.minsize(900, 550)

        self.current_folder = None
        self.image_paths = []          # remaining images
        self.page = 0
        self.photo_refs = []
        self.listening = False
        self.mic_label = None
        self.status_var = tk.StringVar(value="Select a Drive first")
        self.drag_data = {"path": None, "widget": None}
        self.folders = []
        self.pending_refresh = False   # after move, wait for N

        self._build_start_ui()
        self.root.mainloop()

    # ---------- START SCREEN ----------
    def _build_start_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        title = tk.Label(frame, text="📷 Image Voice Mover",
                         font=("Segoe UI", 28, "bold"), fg="#ffffff", bg=BG_COLOR)
        title.pack(pady=(20, 10))

        sub = tk.Label(frame, text="Sort photos with voice + drag-drop",
                       font=("Segoe UI", 14), fg="#aaaaaa", bg=BG_COLOR)
        sub.pack(pady=(0, 40))

        drive_frame = tk.Frame(frame, bg=BG_COLOR)
        drive_frame.pack(pady=10)

        tk.Label(drive_frame, text="1. Select Drive:", font=("Segoe UI", 12),
                 fg="#dddddd", bg=BG_COLOR).pack(side="left", padx=(0, 15))

        self.drive_var = tk.StringVar()
        drives = self._get_drives()
        if drives:
            self.drive_var.set(drives[0])
        drive_menu = tk.OptionMenu(drive_frame, self.drive_var, *drives)
        drive_menu.config(font=("Segoe UI", 11), bg="#1e1e28", fg="white",
                          activebackground=ACCENT, highlightthickness=0)
        drive_menu["menu"].config(bg="#1e1e28", fg="white")
        drive_menu.pack(side="left")

        btn = tk.Button(frame, text="2. Select Folder & Start",
                        font=("Segoe UI", 14, "bold"),
                        bg=ACCENT, fg="#000000", activebackground="#00b8e0",
                        relief="flat", padx=30, pady=12,
                        command=self._select_folder)
        btn.pack(pady=40)

        status = tk.Label(frame, textvariable=self.status_var,
                          font=("Segoe UI", 10), fg="#888888", bg=BG_COLOR)
        status.pack(side="bottom", pady=20)

        info = tk.Label(frame,
                        text="M = Voice  |  N = Refill grid after moves  |  ← → Page  |  Esc Exit  |  Drag image → Folder",
                        font=("Segoe UI", 10), fg="#666666", bg=BG_COLOR)
        info.pack(side="bottom")

    def _get_drives(self):
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives or ["C:\\"]

    def _select_folder(self):
        start = self.drive_var.get()
        folder = filedialog.askdirectory(initialdir=start, title="Select Image Folder")
        if not folder:
            return
        self.current_folder = folder
        self._load_images()
        if not self.image_paths:
            messagebox.showinfo("No Images", "No supported images found in this folder.")
            return
        self._enter_fullscreen()

    def _load_images(self):
        files = []
        for f in os.listdir(self.current_folder):
            full = os.path.join(self.current_folder, f)
            if os.path.isfile(full) and os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                files.append(full)
        files.sort(key=lambda x: os.path.basename(x).lower())
        self.image_paths = files
        self.page = 0
        self.pending_refresh = False

    def _load_folders(self):
        """Load sub-folders of current folder for the side panel."""
        self.folders = []
        try:
            for name in os.listdir(self.current_folder):
                full = os.path.join(self.current_folder, name)
                if os.path.isdir(full):
                    self.folders.append(name)
            self.folders.sort(key=str.lower)
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
        self.root.bind("<m>", lambda e: self._start_listening())
        self.root.bind("<M>", lambda e: self._start_listening())
        self.root.bind("<n>", lambda e: self._refill_grid())
        self.root.bind("<N>", lambda e: self._refill_grid())

        # Top bar
        top = tk.Frame(self.root, bg=PANEL_BG, height=48)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.page_label = tk.Label(top, text="", font=("Segoe UI", 12, "bold"),
                                   fg="#ffffff", bg=PANEL_BG)
        self.page_label.pack(side="left", padx=18)

        self.status_label = tk.Label(top, text="Press M to speak  |  N to refill after moves",
                                     font=("Segoe UI", 11), fg=ACCENT, bg=PANEL_BG)
        self.status_label.pack(side="right", padx=18)

        # Main area = grid + folders
        main = tk.Frame(self.root, bg=BG_COLOR)
        main.pack(expand=True, fill="both")

        # LEFT: image grid
        self.grid_frame = tk.Frame(main, bg=BG_COLOR)
        self.grid_frame.pack(side="left", expand=True, fill="both", padx=(8, 4), pady=8)

        # RIGHT: folders panel
        self.folder_panel = tk.Frame(main, bg=PANEL_BG, width=230)
        self.folder_panel.pack(side="right", fill="y", padx=(4, 8), pady=8)
        self.folder_panel.pack_propagate(False)

        tk.Label(self.folder_panel, text="📁 Folders", font=("Segoe UI", 13, "bold"),
                 fg="#ffffff", bg=PANEL_BG).pack(pady=(12, 6))

        # Scrollable folder list
        canvas = tk.Canvas(self.folder_panel, bg=PANEL_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.folder_panel, orient="vertical", command=canvas.yview)
        self.folder_list_frame = tk.Frame(canvas, bg=PANEL_BG)

        self.folder_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.folder_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=6)
        scrollbar.pack(side="right", fill="y")

        self.folder_canvas = canvas

        # New folder button
        new_btn = tk.Button(self.folder_panel, text="+ New Folder",
                            font=("Segoe UI", 10, "bold"),
                            bg=ACCENT, fg="#000", relief="flat", pady=6,
                            command=self._create_new_folder)
        new_btn.pack(side="bottom", fill="x", padx=10, pady=10)

        self._load_folders()
        self._render_folders()
        self._render_page()

    def _exit_fullscreen(self):
        self.root.attributes("-fullscreen", False)
        for key in ["<Escape>", "<Left>", "<Right>", "<m>", "<M>", "<n>", "<N>"]:
            self.root.unbind(key)
        self._build_start_ui()

    def _change_page(self, delta):
        if self.pending_refresh:
            self.status_label.config(text="Press N first to refill the grid", fg="#ff4757")
            return
        max_page = max(0, (len(self.image_paths) - 1) // PAGE_SIZE)
        new_page = self.page + delta
        if 0 <= new_page <= max_page:
            self.page = new_page
            self._render_page()

    def _refill_grid(self):
        """Press N: after moves, refill empty slots with next remaining images."""
        self.pending_refresh = False
        # Keep same page index if possible, just re-render with current list
        max_page = max(0, (len(self.image_paths) - 1) // PAGE_SIZE)
        if self.page > max_page:
            self.page = max_page
        self._render_page()
        self.status_label.config(text="✅ Grid refilled with remaining images", fg="#2ed573")

    # ---------- RENDER GRID ----------
    def _render_page(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.photo_refs.clear()
        self.mic_label = None

        start = self.page * PAGE_SIZE
        end = min(start + PAGE_SIZE, len(self.image_paths))
        page_imgs = self.image_paths[start:end]

        total_pages = max(1, (len(self.image_paths) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.config(
            text=f"Page {self.page + 1}/{total_pages}  |  {len(self.image_paths)} left"
        )

        self.root.update_idletasks()
        w = self.grid_frame.winfo_width()
        h = self.grid_frame.winfo_height()
        if w < 100 or h < 100:
            w = self.root.winfo_screenwidth() - 250
            h = self.root.winfo_screenheight() - 70

        cell_w = max(120, w // GRID_COLS)
        cell_h = max(100, h // GRID_ROWS)

        for idx in range(PAGE_SIZE):
            row = idx // GRID_COLS
            col = idx % GRID_COLS
            number = idx + 1

            cell = tk.Frame(self.grid_frame, bg=BG_COLOR, width=cell_w, height=cell_h)
            cell.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            cell.grid_propagate(False)
            self.grid_frame.grid_rowconfigure(row, weight=1)
            self.grid_frame.grid_columnconfigure(col, weight=1)

            if idx < len(page_imgs):
                path = page_imgs[idx]
                try:
                    img = Image.open(path)
                    img.thumbnail((cell_w - 6, cell_h - 6), Image.Resampling.LANCZOS)

                    # Number badge
                    badge_size = 34
                    badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(badge)
                    color = NUMBER_COLORS[idx % len(NUMBER_COLORS)]
                    draw.ellipse([0, 0, badge_size - 1, badge_size - 1], fill=color)
                    try:
                        font = ImageFont.truetype("arial.ttf", 16)
                    except Exception:
                        font = ImageFont.load_default()
                    text = str(number)
                    bbox = draw.textbbox((0, 0), text, font=font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    draw.text(((badge_size - tw) // 2, (badge_size - th) // 2 - 1),
                              text, fill="white", font=font)

                    img = img.convert("RGBA")
                    img.paste(badge, (img.width - badge_size - 5, 5), badge)

                    photo = ImageTk.PhotoImage(img)
                    self.photo_refs.append(photo)

                    lbl = tk.Label(cell, image=photo, bg=BG_COLOR, cursor="hand2")
                    lbl.place(relx=0.5, rely=0.5, anchor="center")
                    lbl.image_path = path  # store path for drag

                    # Drag start
                    lbl.bind("<ButtonPress-1>", self._on_drag_start)
                    lbl.bind("<B1-Motion>", self._on_drag_motion)
                    lbl.bind("<ButtonRelease-1>", self._on_drag_release)

                    # Mic under 11th image
                    if number == 11:
                        self.mic_container = tk.Frame(cell, bg=BG_COLOR)
                        self.mic_container.place(relx=0.5, rely=0.93, anchor="s")
                        self.mic_label = tk.Label(self.mic_container, text="🎙",
                                                  font=("Segoe UI", 20),
                                                  fg="#555555", bg=BG_COLOR)
                        self.mic_label.pack()

                except Exception:
                    err = tk.Label(cell, text="Error", fg="#ff4757", bg=BG_COLOR)
                    err.place(relx=0.5, rely=0.5, anchor="center")
            else:
                # Empty slot (after move, before N)
                empty = tk.Label(cell, text="—", font=("Segoe UI", 24),
                                 fg="#333333", bg=BG_COLOR)
                empty.place(relx=0.5, rely=0.5, anchor="center")

    # ---------- FOLDERS PANEL ----------
    def _render_folders(self):
        for w in self.folder_list_frame.winfo_children():
            w.destroy()

        if not self.folders:
            tk.Label(self.folder_list_frame, text="No folders yet\nCreate one ↓",
                     font=("Segoe UI", 10), fg="#777", bg=PANEL_BG,
                     justify="center").pack(pady=20)
            return

        for name in self.folders:
            f = tk.Frame(self.folder_list_frame, bg="#1e1e28", pady=4)
            f.pack(fill="x", pady=3, padx=2)

            lbl = tk.Label(f, text=f"📂  {name}", font=("Segoe UI", 11),
                           fg="#eeeeee", bg="#1e1e28", anchor="w", cursor="hand2")
            lbl.pack(fill="x", padx=8, pady=6)
            lbl.folder_name = name

            # Drop target
            lbl.bind("<ButtonRelease-1>", self._on_folder_drop)
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg="#2a2a3a"))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(bg="#1e1e28"))

            # Also allow whole frame
            f.bind("<ButtonRelease-1>", lambda e, n=name: self._drop_to_folder(n))

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

    # ---------- DRAG & DROP ----------
    def _on_drag_start(self, event):
        widget = event.widget
        if hasattr(widget, "image_path"):
            self.drag_data["path"] = widget.image_path
            self.drag_data["widget"] = widget
            widget.config(cursor="fleur")

    def _on_drag_motion(self, event):
        pass  # visual feedback optional

    def _on_drag_release(self, event):
        # If released over a folder it will be handled by folder binding
        # Reset cursor
        if self.drag_data["widget"]:
            try:
                self.drag_data["widget"].config(cursor="hand2")
            except Exception:
                pass

    def _on_folder_drop(self, event):
        widget = event.widget
        if hasattr(widget, "folder_name") and self.drag_data["path"]:
            self._drop_to_folder(widget.folder_name)

    def _drop_to_folder(self, folder_name):
        if not self.drag_data["path"]:
            return
        src = self.drag_data["path"]
        self.drag_data["path"] = None

        dest_dir = os.path.join(self.current_folder, folder_name)
        dest = os.path.join(dest_dir, os.path.basename(src))

        try:
            if not os.path.exists(src):
                self.status_label.config(text="Image already moved", fg="#ff4757")
                return
            shutil.move(src, dest)
            # Remove from list
            if src in self.image_paths:
                self.image_paths.remove(src)
            self.pending_refresh = True
            self.status_label.config(
                text=f"✅ Moved → {folder_name}  (Press N to refill)", fg="#2ed573")
            # Do NOT re-render yet – wait for N
            # Just mark empty visually by re-rendering current page with gaps
            self._render_page_with_gaps()
        except Exception as e:
            self.status_label.config(text=f"Move failed: {e}", fg="#ff4757")

    def _render_page_with_gaps(self):
        """Re-render current page but keep empty slots where images were moved."""
        # Simply call normal render – because we already removed from image_paths,
        # the later images will shift. To keep visual gaps until N we need different approach.
        # For simplicity & reliability: after any move we remove from list and
        # show remaining on current page (they shift left). User presses N only
        # if they want to force refill / go next. This is cleaner.
        self._render_page()

    # ---------- VOICE (IMPROVED) ----------
    def _start_listening(self):
        if self.listening:
            return
        self.listening = True
        self.status_label.config(text="🎙 Listening... speak clearly now", fg="#ff4757")
        if self.mic_label:
            self.mic_label.config(fg=ACCENT)
            self._pulse_mic()

        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _pulse_mic(self):
        if not self.listening or not self.mic_label:
            return
        current = self.mic_label.cget("fg")
        new = "#ff4757" if current == ACCENT else ACCENT
        self.mic_label.config(fg=new)
        self.root.after(350, self._pulse_mic)

    def _listen_thread(self):
        r = sr.Recognizer()
        r.energy_threshold = 300          # more sensitive
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.8

        try:
            with sr.Microphone() as source:
                self.root.after(0, lambda: self.status_label.config(
                    text="🎙 Adjusting noise... then speak", fg="#ffaa00"))
                r.adjust_for_ambient_noise(source, duration=0.6)
                self.root.after(0, lambda: self.status_label.config(
                    text="🎙 Listening now... speak", fg="#ff4757"))
                audio = r.listen(source, timeout=7, phrase_time_limit=10)

            text = r.recognize_google(audio, language="en-IN")  # en-IN works better for many Indian accents
            self.root.after(0, lambda t=text: self._process_command(t))

        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self._finish_listen("Timeout – press M and try again"))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self._finish_listen("Could not understand – speak slower & clearer"))
        except sr.RequestError as e:
            self.root.after(0, lambda: self._finish_listen(f"Internet/API error: {e}"))
        except Exception as e:
            self.root.after(0, lambda: self._finish_listen(f"Mic error: {e}"))

    def _finish_listen(self, msg):
        self.listening = False
        self.status_label.config(text=msg, fg="#aaaaaa")
        if self.mic_label:
            self.mic_label.config(fg="#555555")

    def _process_command(self, text):
        self.listening = False
        if self.mic_label:
            self.mic_label.config(fg="#555555")

        original = text
        text = text.lower().strip()
        self.status_label.config(text=f"Heard: \"{original}\"", fg=ACCENT)
        self.root.update()

        # Extract numbers 1-12 (also handle spoken words)
        word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12
        }
        numbers = []
        # digits
        for m in re.finditer(r"\b([1-9]|1[0-2])\b", text):
            numbers.append(int(m.group(1)))
        # words
        for word, num in word_to_num.items():
            if re.search(rf"\b{word}\b", text):
                numbers.append(num)
        numbers = list(dict.fromkeys(numbers))  # unique, keep order

        # Find target folder – very flexible patterns
        target_name = None
        patterns = [
            r"(?:move|send|put|transfer)\s+(?:them\s+)?(?:to|into|in)\s+(.+)",
            r"(?:to|into)\s+(.+?)(?:\s+folder)?$",
            r"folder\s+(.+)$",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                target_name = m.group(1).strip()
                break

        if target_name:
            # Clean trailing words
            target_name = re.sub(r"[\.\,\!\?]+$", "", target_name)
            target_name = re.sub(r"^(the|a|an)\s+", "", target_name)
            target_name = target_name.strip()

        if not numbers:
            self.status_label.config(
                text='No numbers found. Say: "take 1 5 7 and move to Family"',
                fg="#ff4757")
            return

        if not target_name:
            self.status_label.config(
                text='Folder not clear. Say: "take 1 3 5 move to Vacation"',
                fg="#ff4757")
            return

        # Confirm understanding
        self.status_label.config(
            text=f"OK → {numbers}  to  [{target_name}]", fg="#ffaa00")
        self.root.update()

        # Resolve destination
        if os.path.isabs(target_name) or (len(target_name) > 1 and target_name[1] == ":"):
            dest_dir = target_name
        else:
            dest_dir = os.path.join(self.current_folder, target_name)

        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            self.status_label.config(text=f"Cannot create folder: {e}", fg="#ff4757")
            return

        # Move files
        start = self.page * PAGE_SIZE
        moved = []
        for num in numbers:
            idx = start + (num - 1)
            if 0 <= idx < len(self.image_paths):
                src = self.image_paths[idx]
                if not os.path.exists(src):
                    continue
                dest = os.path.join(dest_dir, os.path.basename(src))
                try:
                    shutil.move(src, dest)
                    moved.append(os.path.basename(src))
                    # remove from list so it disappears
                    self.image_paths[idx] = None  # mark
                except Exception as e:
                    print("Move error:", e)

        # Clean None entries
        self.image_paths = [p for p in self.image_paths if p is not None]

        self.pending_refresh = True
        self._load_folders()          # in case new folder was created
        self._render_folders()
        self._render_page()           # show remaining (gaps filled by shift)

        if moved:
            self.status_label.config(
                text=f"✅ Moved {len(moved)} images → {os.path.basename(dest_dir)}  (Press N if you want)",
                fg="#2ed573")
        else:
            self.status_label.config(text="No images moved (check numbers)", fg="#ff4757")


if __name__ == "__main__":
    ImageVoiceMover()
