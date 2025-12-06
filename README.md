# WhisperApp v2.1 – Whisper Transcriber

WhisperApp is a Windows desktop app that uses [OpenAI Whisper](https://github.com/openai/whisper) and `ffmpeg` to turn audio or video files into text (and optionally `.srt` subtitle files).  
It runs locally on your machine and can automatically use your GPU if CUDA is available.

---

## Download (Windows)

Because the full app bundle is large (it includes Python, Whisper, PyTorch and ffmpeg),
the compiled `.exe` is hosted externally.

👉 **Download the Windows build here:**  
[WhisperApp v2.1 Windows ZIP](https://drive.google.com/file/d/1Kr06ZNmFblv06vzwvKk5DcMwKAr8XTwV/view?usp=sharing)

### After downloading

1. **Extract** the ZIP to a folder (for example: `C:\WhisperApp`).
2. You should see:
   - `WhisperApp_v2.1.exe`
   - `ffmpeg.exe`
   - an `_internal` folder and a few other files
3. Make sure `WhisperApp_v2.1.exe` and `ffmpeg.exe` stay in the **same folder**.
4. Double-click `WhisperApp_v2.1.exe` to start the app.

No extra installation or command line is required for normal use.

---

## Using the app

When you open the app, you’ll see the **Whisper Transcriber** window:

- **File**  
  The path to the audio or video file you want to transcribe.  
  Click **Browse…** to select a file (e.g. `.wav`, `.mp3`, `.m4a`, `.mp4`, etc.).

- **Model**  
  Choose which Whisper model to use (e.g. `tiny`, `base`, `small`, `medium`, `large`).  
  - Smaller models = faster, but slightly less accurate  
  - Larger models = slower, more accurate  

- **Language**  
  - Leave this **blank** to let Whisper auto-detect the language.  
  - Or type a language code (e.g. `en`, `zh`, `es`) to force a specific language.

- **Device**  
  - `auto` (default): the app will automatically choose:
    - **GPU** if a CUDA-capable GPU is available  
    - **CPU** otherwise  
  - You can override this manually (e.g. `cpu` or `cuda`) if you want to force a device.

- **Save .srt subtitles**  
  - If checked, the app will create a `.srt` subtitle file in addition to the plain text file.  
  - If unchecked, only a `.txt` transcript is created.

- **Transcribe button**  
  Starts the transcription. The progress bar at the bottom shows the current status.

### Output files

The output is saved in the **same folder as the input media file**:

- If your input file is `D:\Media\lecture.mp4`, you will get:
  - `D:\Media\lecture.txt`
  - and, if you checked **Save .srt subtitles**,  
    `D:\Media\lecture.srt`

---

## Requirements

- Windows 10 or 11 (64-bit)
- Enough disk space and RAM for the Whisper model you choose
- For GPU acceleration:
  - NVIDIA GPU with CUDA support  
  - Proper NVIDIA drivers and CUDA/cuDNN installed  
  - If CUDA is detected, `Device = auto` will run on GPU automatically

The app may download Whisper model files the first time you run a new model size
(e.g. `small`, `medium`). This only happens once per model.

---

## Source code and building from source

This repository contains the Python source and build configuration:

- `transcriber_app.py` – main application code (GUI + transcription logic)
- `hook-whisper.py` – PyInstaller hook for including Whisper assets
- `WhisperApp_v2.1.spec` – PyInstaller spec used to build the Windows executable

To build from source (for advanced users):

```bash
# Create and activate a virtual environment (Windows example)
py -3.11 -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -U pip
pip install openai-whisper torch ffmpeg-python pyinstaller

# Ensure ffmpeg.exe is in the project root, then run:
pyinstaller WhisperApp_v2.1.spec



