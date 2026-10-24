"""
Media Tools Suite - Root Menu
3 Projects: Image Sorter | Media Mover | Duplicate Remover
"""

import tkinter as tk

BG = "#0a0a0e"
PANEL = "#12121a"
ACCENT = "#00d4ff"
CARD_BG = "#1a1a24"
PURPLE = "#a55eea"
GREEN = "#2ed573"


def show_main_menu(root=None):
    if root is None:
        root = tk.Tk()
        own = True
    else:
        own = False

    root.title("Media Tools Suite")
    root.configure(bg=BG)
    root.geometry("1050x620")
    root.minsize(900, 550)

    for w in root.winfo_children():
        w.destroy()

    # Header
    header = tk.Frame(root, bg=PANEL, height=65)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="🚀  Media Tools Suite",
             font=("Segoe UI", 20, "bold"), fg="white", bg=PANEL).pack(side="left", padx=22, pady=14)

    tk.Label(header, text="Choose a tool",
             font=("Segoe UI", 11), fg="#888", bg=PANEL).pack(side="right", padx=22)

    # Cards
    cards = tk.Frame(root, bg=BG)
    cards.pack(expand=True, fill="both", padx=25, pady=20)

    # ---- Card 1: Image Sorter ----
    card1 = tk.Frame(cards, bg=CARD_BG, highlightbackground=ACCENT, highlightthickness=2)
    card1.pack(side="left", expand=True, fill="both", padx=10, pady=8)

    tk.Label(card1, text="📷", font=("Segoe UI", 40), bg=CARD_BG, fg=ACCENT).pack(pady=(22, 4))
    tk.Label(card1, text="Image Sorter", font=("Segoe UI", 15, "bold"),
             bg=CARD_BG, fg="white").pack()
    tk.Label(card1, text="Photo grid sorter", font=("Segoe UI", 10),
             bg=CARD_BG, fg="#888").pack(pady=(0, 8))

    desc1 = "• Ctrl+Click multi-select\n• Drag & Drop to folders\n• Fast bulk sorting"
    tk.Label(card1, text=desc1, font=("Segoe UI", 10), bg=CARD_BG, fg="#bbb",
             justify="left").pack(pady=6)

    def launch_image():
        for w in root.winfo_children():
            w.destroy()
        from image_mover import ImageVoiceMover
        ImageVoiceMover(parent=root)

    tk.Button(card1, text="Open →", font=("Segoe UI", 11, "bold"),
              bg=ACCENT, fg="black", relief="flat", padx=16, pady=8,
              cursor="hand2", command=launch_image).pack(pady=16)

    # ---- Card 2: Media Mover ----
    card2 = tk.Frame(cards, bg=CARD_BG, highlightbackground=PURPLE, highlightthickness=2)
    card2.pack(side="left", expand=True, fill="both", padx=10, pady=8)

    tk.Label(card2, text="🎵", font=("Segoe UI", 40), bg=CARD_BG, fg=PURPLE).pack(pady=(22, 4))
    tk.Label(card2, text="Media Mover", font=("Segoe UI", 15, "bold"),
             bg=CARD_BG, fg="white").pack()
    tk.Label(card2, text="Audio + Video grid", font=("Segoe UI", 10),
             bg=CARD_BG, fg="#888").pack(pady=(0, 8))

    desc2 = "• Same as Image Sorter\n• Video thumbnails\n• mp4 3gp mkv mp3 +more"
    tk.Label(card2, text=desc2, font=("Segoe UI", 10), bg=CARD_BG, fg="#bbb",
             justify="left").pack(pady=6)

    def launch_media():
        for w in root.winfo_children():
            w.destroy()
        from media_classifier import MediaMover
        MediaMover(parent=root)

    tk.Button(card2, text="Open →", font=("Segoe UI", 11, "bold"),
              bg=PURPLE, fg="white", relief="flat", padx=16, pady=8,
              cursor="hand2", command=launch_media).pack(pady=16)

    # ---- Card 3: Duplicate Remover ----
    card3 = tk.Frame(cards, bg=CARD_BG, highlightbackground=GREEN, highlightthickness=2)
    card3.pack(side="left", expand=True, fill="both", padx=10, pady=8)

    tk.Label(card3, text="🖼️", font=("Segoe UI", 40), bg=CARD_BG, fg=GREEN).pack(pady=(22, 4))
    tk.Label(card3, text="Duplicate Remover", font=("Segoe UI", 15, "bold"),
             bg=CARD_BG, fg="white").pack()
    tk.Label(card3, text="Find & clean similar images", font=("Segoe UI", 10),
             bg=CARD_BG, fg="#888").pack(pady=(0, 8))

    desc3 = "• Scan all subfolders\n• Group 50%+ matches\n• Preserve selected → temp rest"
    tk.Label(card3, text=desc3, font=("Segoe UI", 10), bg=CARD_BG, fg="#bbb",
             justify="left").pack(pady=6)

    def launch_dup():
        for w in root.winfo_children():
            w.destroy()
        from duplicate_remover import DuplicateRemover
        DuplicateRemover(parent=root)

    tk.Button(card3, text="Open →", font=("Segoe UI", 11, "bold"),
              bg=GREEN, fg="black", relief="flat", padx=16, pady=8,
              cursor="hand2", command=launch_dup).pack(pady=16)

    # Footer
    footer = tk.Frame(root, bg=PANEL, height=36)
    footer.pack(fill="x", side="bottom")
    footer.pack_propagate(False)
    tk.Label(footer, text="Lightweight • Works on 4GB RAM • No heavy software",
             font=("Segoe UI", 9), fg="#666", bg=PANEL).pack(pady=8)

    if own:
        root.mainloop()


if __name__ == "__main__":
    show_main_menu()
