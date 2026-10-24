"""
Image Voice Mover + Media Mover
Root menu with two options
"""

import tkinter as tk

BG = "#0a0a0e"
PANEL = "#12121a"
ACCENT = "#00d4ff"
CARD_BG = "#1a1a24"
PURPLE = "#a55eea"


def show_main_menu(root=None):
    if root is None:
        root = tk.Tk()
        own = True
    else:
        own = False

    root.title("Media Tools - Choose Project")
    root.configure(bg=BG)
    root.geometry("900x600")
    root.minsize(750, 500)

    for w in root.winfo_children():
        w.destroy()

    # Header
    header = tk.Frame(root, bg=PANEL, height=70)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="🚀  Media Tools Suite",
             font=("Segoe UI", 22, "bold"), fg="white", bg=PANEL).pack(side="left", padx=25, pady=15)

    tk.Label(header, text="Choose what you want to do",
             font=("Segoe UI", 11), fg="#888", bg=PANEL).pack(side="right", padx=25)

    # Cards area
    cards = tk.Frame(root, bg=BG)
    cards.pack(expand=True, fill="both", padx=40, pady=30)

    # ---- Card 1: Image Mover ----
    card1 = tk.Frame(cards, bg=CARD_BG, highlightbackground=ACCENT, highlightthickness=2)
    card1.pack(side="left", expand=True, fill="both", padx=15, pady=10)

    tk.Label(card1, text="📷", font=("Segoe UI", 48), bg=CARD_BG, fg=ACCENT).pack(pady=(30, 5))
    tk.Label(card1, text="Image Sorter", font=("Segoe UI", 18, "bold"),
             bg=CARD_BG, fg="white").pack()
    tk.Label(card1, text="Image Voice Mover", font=("Segoe UI", 11),
             bg=CARD_BG, fg="#888").pack(pady=(0, 10))

    desc1 = ("• Ctrl + Click multi-select\n"
             "• Drag & Drop to folders\n"
             "• Fast bulk photo sorting\n"
             "• Fullscreen 3×5 grid")
    tk.Label(card1, text=desc1, font=("Segoe UI", 11), bg=CARD_BG, fg="#bbbbbb",
             justify="left").pack(pady=10)

    def launch_image():
        for w in root.winfo_children():
            w.destroy()
        from image_mover import ImageVoiceMover
        ImageVoiceMover(parent=root)

    btn1 = tk.Button(card1, text="Open Image Sorter →",
                     font=("Segoe UI", 12, "bold"),
                     bg=ACCENT, fg="black", relief="flat",
                     padx=20, pady=10, cursor="hand2",
                     command=launch_image)
    btn1.pack(pady=25)

    # ---- Card 2: Media Mover ----
    card2 = tk.Frame(cards, bg=CARD_BG, highlightbackground=PURPLE, highlightthickness=2)
    card2.pack(side="left", expand=True, fill="both", padx=15, pady=10)

    tk.Label(card2, text="🎵", font=("Segoe UI", 48), bg=CARD_BG, fg=PURPLE).pack(pady=(30, 5))
    tk.Label(card2, text="Media Mover", font=("Segoe UI", 18, "bold"),
             bg=CARD_BG, fg="white").pack()
    tk.Label(card2, text="Audio + Video Grid Sorter", font=("Segoe UI", 11),
             bg=CARD_BG, fg="#888").pack(pady=(0, 10))

    desc2 = ("• Same style as Image Sorter\n"
             "• Grid + Ctrl+Click + Drag\n"
             "• mp4 mkv 3gp avi mp3 wav +more\n"
             "• No auto sort / No year logic")
    tk.Label(card2, text=desc2, font=("Segoe UI", 11), bg=CARD_BG, fg="#bbbbbb",
             justify="left").pack(pady=10)

    def launch_media():
        for w in root.winfo_children():
            w.destroy()
        from media_classifier import MediaMover
        MediaMover(parent=root)

    btn2 = tk.Button(card2, text="Open Media Mover →",
                     font=("Segoe UI", 12, "bold"),
                     bg=PURPLE, fg="white", relief="flat",
                     padx=20, pady=10, cursor="hand2",
                     command=launch_media)
    btn2.pack(pady=25)

    # Footer
    footer = tk.Frame(root, bg=PANEL, height=40)
    footer.pack(fill="x", side="bottom")
    footer.pack_propagate(False)
    tk.Label(footer, text="No heavy software • Works on 4GB RAM • Same controls as Image Sorter",
             font=("Segoe UI", 9), fg="#666", bg=PANEL).pack(pady=10)

    if own:
        root.mainloop()


if __name__ == "__main__":
    show_main_menu()
