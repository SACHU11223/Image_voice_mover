# Image Voice Mover

**Voice-controlled image sorter for Windows 10**

Sort your photos fast using voice commands. No extra software install needed (only Python packages via pip).

## Features

- Select **Drive** then **Folder**
- Goes **fullscreen** automatically
- Shows images in clean **3 columns × 4 rows** grid (12 images at a time)
- **Colorful numbered circles** on top-right of every image
- Press **`M`** → Microphone opens
- Mic appears under the **11th image** and pulses while you speak
- Speak in English, example:
  > `take 1, 5, 7, 8 and move to vacation`
- Selected images move to the target folder (creates it if missing)

## How to Run (Windows 10)

1. Install Python 3.10+ from python.org (check "Add to PATH")
2. Open Command Prompt in this folder
3. Run:
```bash
pip install -r requirements.txt
python main.py
```

> **Note about PyAudio**: If `pip install pyaudio` fails, download the matching `.whl` from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install it with `pip install filename.whl`

## Controls

| Key | Action |
|-----|--------|
| `M` | Start voice listening |
| `←` / `→` | Previous / Next page |
| `Esc` | Exit fullscreen / Quit |
| Mouse click on image | (optional future) |

## Voice Command Format

```
take 1,3,5 and move to FolderName
take 2 4 6 move to C:\\Backup\\Photos
```

- Numbers = the red/blue circles you see (1-12 on current page)
- Folder can be relative (created inside current folder) or full path

## Screenshots / UI

- Dark modern theme
- No borders / cards – pure grid
- Smooth numbered badges
- Animated mic while listening

Made for quick photo sorting with voice.
