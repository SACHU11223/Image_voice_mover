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
| 🎵 | **Media Classifier** | Auto sort Audio + Video into Bhakti / Old / New folders |

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

**Automatic sorter for songs & videos**  
Creates 6 + 1 folders and moves files correctly.

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

### Sorting Logic (3 Steps)

1. **Metadata & Fingerprinting**
   - `mutagen` → reads local ID3 tags (title, year)
   - `pyacoustid` → (optional) online free database match for unknown files

2. **Bhakti / Devotional Check**
   - Keywords in title/filename/metadata:
     `bhajan, bhakti, shiv, ram, krishna, hanuman, chalisa, aarti, mantra, kirtan...`
   - If found → goes to **Bhakti** folder

3. **Year-based Sorting**
   - Year ≤ 1999 → **Old_Song_Till_1999**
   - Year 2000–2026 → **New_Song_2000_2026**
   - Year unknown → **Unsorted**

### Supported Formats
- **Audio**: `.mp3` `.wav` `.flac` `.m4a` `.ogg` `.aac`
- **Video**: `.mp4` `.mkv` `.avi` `.mov` `.webm` `.wmv`

### How to Use Media Classifier
1. Open the app → click **Media Classifier**
2. Select **Source folder** (where your mixed songs/videos are)
3. (Optional) Select different Destination
4. Tick “Use online fingerprint” if you want better name detection
5. Click **START CLASSIFY & MOVE**
6. Watch the log → files move automatically

### Install Extra Libraries (only for Media Classifier)
```bash
pip install mutagen pyacoustid
```

> **Note about pyacoustid**:  
> It needs `fpcalc` (Chromaprint) for fingerprinting.  
> On Windows you can download it from: https://acoustid.org/chromaprint  
> Or just skip the checkbox – mutagen + filename is enough for most cases.

---

## 📦 Requirements

```
Pillow>=10.0.0      # Image Sorter
mutagen>=1.47.0     # Media Classifier (tags)
pyacoustid>=1.3.0   # Media Classifier (optional online match)
```

All free & lightweight. No heavy AI models. Runs fine on 4GB RAM.

---

## File Structure
```
Image_voice_mover/
├── main.py                 ← Root menu (start here)
├── image_mover.py          ← Image Sorter code
├── media_classifier.py     ← Audio/Video Classifier code
├── requirements.txt
└── README.md
```

---

Made for quick media organization on everyday laptops.
