# Image Voice Mover

**Voice + Drag-Drop image sorter for Windows 10**

Sort photos fast using voice commands or by dragging images into folders.

## What's New (Latest Update)

- ✅ **Much better voice recognition** (handles Indian accent better, clearer feedback)
- ✅ **Folder side panel** – see all folders next to the 12 images
- ✅ **Drag & Drop** images directly onto any folder
- ✅ Press **`N`** after moving images to refill the empty slots with next photos
- ✅ Create new folders from the panel

## Features

| Feature | Description |
|---------|-------------|
| Drive + Folder select | Start by choosing drive then folder |
| Fullscreen 3×4 grid | Clean grid, no borders/cards |
| Colorful number badges | Top-right circle on every image |
| Voice (`M` key) | Speak: `take 1 5 7 and move to Family` |
| Side Folder Panel | All sub-folders visible |
| Drag & Drop | Drag any image onto a folder |
| Refill (`N` key) | After moves, press N to fill empty slots |
| New Folder button | Create folders on the fly |

## How to Run

```bash
pip install -r requirements.txt
python main.py
```

> If PyAudio fails on Windows, download the correct `.whl` from  
> https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio  and install it.

## Controls

| Key / Action | What it does |
|--------------|--------------|
| **M** | Start microphone (speak command) |
| **N** | Refill the 12-image grid after you have moved some |
| **← / →** | Previous / Next page |
| **Esc** | Exit fullscreen |
| **Drag image** | Drop onto any folder in the right panel |

## Voice Examples (speak clearly)

```
take 1 3 5 and move to Family
take 2, 4, 7 move to Vacation
move 1 6 9 to Work
take one five eight and move to Photos
```

After the move you will see the remaining images.  
Press **N** only when you have finished checking the current 12 images and want the empty places filled with the next photos.

## Tips for better voice recognition

1. Speak a little slowly and clearly
2. Keep microphone close
3. Reduce background noise
4. Internet is required (Google Speech API)

---
Made for quick photo sorting.
