# Image Voice Mover

**Fast image sorter for Windows 10**  
Ctrl+Click multi-select + Drag & Drop to folders

## Latest Changes

- ✅ **3 columns × 5 rows** = 15 images per page
- ✅ **Full grid** – zero space, zero borders between photos
- ✅ **Ctrl + Click** multi-select
- ✅ Selected images turn **Black & White + blue highlight** (real-time)
- ✅ **Drag any selected image** onto a folder → all selected images move
- ✅ Clicking a folder name also moves the selected images
- ✅ Mic / voice system completely removed
- ✅ Drag & drop fixed and reliable

## How to Run

```bash
pip install -r requirements.txt
python main.py
```

Only need **Pillow** now (no speech packages).

## Controls

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

## Selection Highlight

- Selected photos become **Black & White**
- Blue border + light blue tint appears
- Highlight stays only until you move them

## Workflow

1. Select Drive → Select Folder
2. Fullscreen opens with 15 photos (3×5)
3. **Ctrl + Click** the photos you want
4. Drag any of them to a folder on the right (or just click the folder)
5. Photos move instantly
6. Press **N** when you want the empty places filled with next images

---
Made for quick bulk photo sorting.
