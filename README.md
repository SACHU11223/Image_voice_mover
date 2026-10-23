# Media Tools Suite

**Image Sorter + Audio/Video Classifier**  
One repo → two useful tools. Lightweight, free, works on 4GB RAM laptops.

---

## 🚀 How to Run

```bash
pip install -r requirements.txt
python main.py
```

A menu will open with **two big options**:

| Icon | Project | What it does |
|------|---------|--------------|
| 📷 | **Image Sorter** | Fast bulk photo sorting with Ctrl+Click + Drag & Drop |
| 🎵 | **Media Classifier** | Auto sort + **rename** Audio/Video into Bhakti / Old / New folders |

---

## 📷 Project 1: Image Sorter (Image Voice Mover)

**Fast image sorter for Windows**  
Ctrl+Click multi-select + Drag & Drop to folders

### Features
- ✅ **3 columns × 5 rows** = 15 images per page
- ✅ **Full grid** – zero space, zero borders between photos
- ✅ **Ctrl + Click** multi-select
- ✅ Selected images turn **Black & White + blue highlight**
- ✅ **Drag any selected image** onto a folder → all selected images move
- ✅ Clicking a folder name also moves the selected images
- ✅ Mic / voice system completely removed
- ✅ Drag & drop fixed and reliable

### Controls

| Action | Result |
|--------|--------|
| **Normal Click** | Select only that image |
| **Ctrl + Click** | Add / remove from selection |
| **Drag selected image** → Folder | Move all selected images |
| **Click folder name** | Also moves currently selected images |
| **N** | Refill the grid with remaining images |
| **← / →** | Change page |
| **Esc** | Exit fullscreen |
| **+ New Folder** | Create folder in the side panel |

### Workflow
1. Select Drive → Select Folder
2. Fullscreen opens with 15 photos (3×5)
3. **Ctrl + Click** the photos you want
4. Drag any of them to a folder on the right (or just click the folder)
5. Photos move instantly
6. Press **N** when you want the empty places filled with next images

---

## 🎵 Project 2: Media Classifier (Audio + Video Sorter)

**Automatic sorter + renamer for songs & videos**  
Creates 6 + 1 folders, optionally renames files from online lookup, then moves them.

### Target Folders Created
```
Audio/
  ├── Bhakti
  ├── New_Song_2000_2026
  └── Old_Song_Till_1999
Video/
  ├── Bhakti
  ├── New_Song_2000_2026
  └── Old_Song_Till_1999
Unsorted/          ← if year unknown
```

### What it does (step by step)

1. **Local tags** (`mutagen`) → read Title / Artist / Year
2. **Online lookup** (`pyacoustid`) → optional fingerprint match (audio only)
3. **Auto-rename** → if good Title/Artist found → rename to `Artist - Title.ext`
4. **Bhakti check** → keywords like bhajan, shiv, ram, krishna, hanuman, chalisa...
5. **Year sort** → ≤1999 = Old, 2000-2026 = New
6. **Move** to correct folder

### Supported Formats
- **Audio**: `.mp3` `.wav` `.flac` `.m4a` `.ogg` `.aac`
- **Video**: `.mp4` `.mkv` `.avi` `.mov` `.webm` `.wmv`

### How to Use Media Classifier
1. Open the app → click **Media Classifier**
2. Select **Source folder**
3. (Optional) Select different Destination
4. **Tick the checkbox** “Use online fingerprint (pyacoustid) + auto-rename”
5. Click **START CLASSIFY + RENAME + MOVE**
6. Watch the log – it shows old name → new name → folder

### Important Notes
- Online lookup is **optional**. If checkbox is off or internet/fpcalc fails → still sorts using local tags + filename.
- Rename only happens when good Title (or Artist + Title) is found.
- Video files mainly use filename + local tags (pyacoustid works best on audio).

### Install Extra Libraries
```bash
pip install mutagen pyacoustid
```

> **fpcalc note (for pyacoustid):**  
> Download Chromaprint from https://acoustid.org/chromaprint and put `fpcalc.exe` in PATH.  
> Or just uncheck the box – local mode still works fine.

---

## 📦 Requirements

```
Pillow>=10.0.0      # Image Sorter
mutagen>=1.47.0     # Media Classifier (tags)
pyacoustid>=1.3.0   # Media Classifier (optional online match + rename)
```

All free & lightweight. No heavy AI models. Runs fine on 4GB RAM.

---

## File Structure
```
Image_voice_mover/
├── main.py                 ← Root menu (start here)
├── image_mover.py          ← Image Sorter code
├── media_classifier.py     ← Audio/Video Classifier + Renamer
├── requirements.txt
└── README.md
```

---

Made for quick media organization on everyday laptops.
