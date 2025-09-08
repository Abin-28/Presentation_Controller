## SlideSense [Presentation Controller]

A gesture‑controlled slide presenter with live speech‑to‑text and embedded camera preview. Use your hands to navigate slides, draw annotations, erase, and pinch‑zoom. The camera preview (with detection overlay) is shown at the top‑right of the slide, and the slide window opens in fullscreen automatically.

### Features
- Fullscreen slides using your current screen resolution
- Top‑right embedded camera preview with hand landmarks and gesture threshold line
- One‑hand gestures: previous/next, draw, erase
- Two‑hand pinch distance for smooth zoom in/out
- Simple Tkinter window showing live speech transcription (Google Speech Recognition)

### Requirements
- Python 3.11 (recommended)
- Webcam and microphone
- Windows (tested); other OS may require small tweaks

Install dependencies:
```
pip install -r requirements.txt
```

### How to Run
1) Create and activate a virtual environment (Windows PowerShell):
```
python -m venv venv
.\venv\Scripts\Activate
```
2) (Optional) Set execution policy if activation is blocked:
```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
3) Install dependencies:
```
pip install -r requirements.txt
```
4) Run the app:
```
python main.py
```

Slides are loaded from the `Presentation/` folder (PNG files). The window opens fullscreen and shows the active slide with a small camera preview at the top‑right.

### Gestures
- Two hands: pinch distance change → zoom in/out (1.0 to 3.0)
- One hand above threshold height:
  - Thumb only up `[1,0,0,0,0]` → Previous slide
  - Little finger only up `[0,0,0,0,1]` → Next slide
- Drawing:
  - Index only `[0,1,0,0,0]` → Draw freehand (red)
  - Index + middle `[0,1,1,0,0]` → Pointer dot
  - Index + middle + ring `[0,1,1,1,0]` → Undo last stroke

Notes:
- The gesture threshold line and landmarks are drawn only inside the camera preview, keeping slides clean.

### Performance Tips
- Ensure good lighting; close other apps using the camera.
- If you see lag, reduce internal resolution or detection scale in `main.py`:
  - Lower `width,height` (screen size fallback is 1280x720).
  - Reduce `det_scale` from `0.5` to `0.4`.
- Keep only one monitor mirrored if your GPU/CPU is limited.

### Folder Structure
```
Presenation Controller/
  main.py               # main application
  Presentation/        # slide images (1.png, 2.png, ...)
  requirements.txt     # Python dependencies
  README.md            # this documentation
```

### Troubleshooting
- Module not found (e.g., cvzone): ensure your venv is activated and `pip install -r requirements.txt` ran successfully.
- Microphone issues: verify default input device and system permissions.
- Webcam not showing: check camera permissions; try changing the backend to `cv2.CAP_MSMF`.


