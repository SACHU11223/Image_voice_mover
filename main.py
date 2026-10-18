import os
import re
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import speech_recognition as sr

# ================== CONFIG ==================
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}
GRID_COLS = 3
GRID_ROWS = 4
PAGE_SIZE = GRID_COLS * GRID_ROWS  # 12
BG_COLOR = "#0f0f13"
ACCENT = "#00d4ff"
NUMBER_COLORS = ["#ff4757", "#2ed573", "#1e90ff", "#ffa502", "#a55eea",
                 "#ff6b81", "#7bed9f", "#70a1ff", "#eccc68", "#5352ed",
                 "#ff6348", "#2f3542"]

class ImageVoiceMover:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Voice Mover")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        self.current_folder = None
        self.image_paths = []
        self.page = 0
        self.photo_refs = []          # keep references
        self.listening = False
        self.mic_label = None
        self.status_var = tk.StringVar(value="Select a Drive first")

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

        sub = tk.Label(frame, text="Sort photos with your voice",
                       font=("Segoe UI", 14), fg="#aaaaaa", bg=BG_COLOR)
        sub.pack(pady=(0, 40))

        # Drive selection
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

        # Folder button
        btn = tk.Button(frame, text="2. Select Folder & Start",
                        font=("Segoe UI", 14, "bold"),
                        bg=ACCENT, fg="#000000", activebackground="#00b8e0",
                        relief="flat", padx=30, pady=12,
                        command=self._select_folder)
        btn.pack(pady=40)

        status = tk.Label(frame, textvariable=self.status_var,
                          font=("Segoe UI", 10), fg="#888888", bg=BG_COLOR)
        status.pack(side="bottom", pady=20)

        # Instructions
        info = tk.Label(frame,
                        text="After start: Press  M  to speak  |  ← →  change page  |  Esc exit",
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
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                files.append(os.path.join(self.current_folder, f))
        files.sort(key=lambda x: os.path.basename(x).lower())
        self.image_paths = files
        self.page = 0

    # ---------- FULLSCREEN GRID ----------
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

        # Top bar
        top = tk.Frame(self.root, bg="#16161e", height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.page_label = tk.Label(top, text="", font=("Segoe UI", 12, "bold"),
                                   fg="#ffffff", bg="#16161e")
        self.page_label.pack(side="left", padx=20)

        self.status_label = tk.Label(top, text="Press M to speak command",
                                     font=("Segoe UI", 11), fg=ACCENT, bg="#16161e")
        self.status_label.pack(side="right", padx=20)

        # Grid container
        self.grid_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.grid_frame.pack(expand=True, fill="both", padx=8, pady=8)

        self._render_page()

    def _exit_fullscreen(self):
        self.root.attributes("-fullscreen", False)
        self.root.unbind("<Escape>")
        self.root.unbind("<Left>")
        self.root.unbind("<Right>")
        self.root.unbind("<m>")
        self.root.unbind("<M>")
        self._build_start_ui()

    def _change_page(self, delta):
        max_page = max(0, (len(self.image_paths) - 1) // PAGE_SIZE)
        new_page = self.page + delta
        if 0 <= new_page <= max_page:
            self.page = new_page
            self._render_page()

    def _render_page(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.photo_refs.clear()

        start = self.page * PAGE_SIZE
        end = min(start + PAGE_SIZE, len(self.image_paths))
        page_imgs = self.image_paths[start:end]

        total_pages = max(1, (len(self.image_paths) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.config(text=f"Page {self.page + 1} / {total_pages}   |   {len(self.image_paths)} images")

        # Calculate cell size
        self.root.update_idletasks()
        w = self.grid_frame.winfo_width()
        h = self.grid_frame.winfo_height()
        if w < 100 or h < 100:
            w, h = self.root.winfo_screenwidth() - 20, self.root.winfo_screenheight() - 70

        cell_w = w // GRID_COLS
        cell_h = h // GRID_ROWS

        for idx, path in enumerate(page_imgs):
            row = idx // GRID_COLS
            col = idx % GRID_COLS
            number = idx + 1  # 1-12 on this page

            cell = tk.Frame(self.grid_frame, bg=BG_COLOR, width=cell_w, height=cell_h)
            cell.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            cell.grid_propagate(False)
            self.grid_frame.grid_rowconfigure(row, weight=1)
            self.grid_frame.grid_columnconfigure(col, weight=1)

            try:
                img = Image.open(path)
                img.thumbnail((cell_w - 4, cell_h - 4), Image.Resampling.LANCZOS)

                # Draw number badge
                badge_size = 36
                badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(badge)
                color = NUMBER_COLORS[idx % len(NUMBER_COLORS)]
                draw.ellipse([0, 0, badge_size - 1, badge_size - 1], fill=color)
                try:
                    font = ImageFont.truetype("arial.ttf", 18)
                except:
                    font = ImageFont.load_default()
                text = str(number)
                bbox = draw.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text(((badge_size - tw) // 2, (badge_size - th) // 2 - 1),
                          text, fill="white", font=font)

                # Paste badge top-right
                img = img.convert("RGBA")
                pos = (img.width - badge_size - 6, 6)
                img.paste(badge, pos, badge)

                photo = ImageTk.PhotoImage(img)
                self.photo_refs.append(photo)

                lbl = tk.Label(cell, image=photo, bg=BG_COLOR)
                lbl.place(relx=0.5, rely=0.5, anchor="center")

                # Mic placeholder under 11th image (index 10)
                if number == 11:
                    self.mic_container = tk.Frame(cell, bg=BG_COLOR)
                    self.mic_container.place(relx=0.5, rely=0.92, anchor="s")
                    self.mic_label = tk.Label(self.mic_container, text="🎙", font=("Segoe UI", 22),
                                              fg="#555555", bg=BG_COLOR)
                    self.mic_label.pack()

            except Exception as e:
                err = tk.Label(cell, text="Error", fg="red", bg=BG_COLOR)
                err.place(relx=0.5, rely=0.5, anchor="center")

    # ---------- VOICE ----------
    def _start_listening(self):
        if self.listening:
            return
        self.listening = True
        self.status_label.config(text="🎙 Listening... speak now", fg="#ff4757")
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
        self.root.after(400, self._pulse_mic)

    def _listen_thread(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.4)
                audio = r.listen(source, timeout=6, phrase_time_limit=8)
            text = r.recognize_google(audio, language="en-US")
            self.root.after(0, lambda: self._process_command(text))
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self._finish_listen("Timeout - try again"))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self._finish_listen("Could not understand"))
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

        text = text.lower().strip()
        self.status_label.config(text=f"Heard: {text}", fg=ACCENT)

        # Parse: take 1,5,7,8 and move to xxx
        # or take 1 5 7 move to xxx
        numbers = re.findall(r"\b([1-9]|1[0-2])\b", text)
        numbers = [int(n) for n in numbers]
        numbers = list(dict.fromkeys(numbers))  # unique keep order

        # Find target folder
        move_match = re.search(r"(?:move|send|put)\s+(?:to|into)\s+(.+)", text)
        if not move_match:
            self.status_label.config(text="Say: take 1,3,5 and move to FolderName", fg="#ff4757")
            return

        target_name = move_match.group(1).strip().rstrip(".")
        # Clean common words
        target_name = re.sub(r"^(the|a|an)\s+", "", target_name)

        if not numbers:
            self.status_label.config(text="No valid numbers (1-12) found", fg="#ff4757")
            return

        # Resolve target path
        if os.path.isabs(target_name) or ":" in target_name:
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
                dest = os.path.join(dest_dir, os.path.basename(src))
                try:
                    shutil.move(src, dest)
                    moved.append(os.path.basename(src))
                except Exception as e:
                    print("Move error:", e)

        # Refresh list
        self._load_images()
        max_page = max(0, (len(self.image_paths) - 1) // PAGE_SIZE)
        if self.page > max_page:
            self.page = max_page
        self._render_page()

        if moved:
            self.status_label.config(
                text=f"✅ Moved {len(moved)} images → {os.path.basename(dest_dir)}",
                fg="#2ed573")
        else:
            self.status_label.config(text="No images moved", fg="#ff4757")


if __name__ == "__main__":
    ImageVoiceMover()
