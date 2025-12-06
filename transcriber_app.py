#!/usr/bin/env python
"""
transcriber_app.py  –  Whisper GUI + CLI
2025-06-03 • progress bar • Auto/GPU/CPU selector • ffmpeg guard
"""

# ────────────────────────── stdlib
import os, sys, threading, queue, pathlib, shutil, argparse, inspect

# ────────────────────────── optional GUI
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    GUI_AVAILABLE = True
except ModuleNotFoundError:
    GUI_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════
# Helper: make sure ffmpeg is reachable
# ═══════════════════════════════════════════════════════════════════════
def ensure_ffmpeg():
    if shutil.which("ffmpeg"):
        return
    # when frozen, look next to the EXE
    if getattr(sys, "frozen", False):
        exe_dir = pathlib.Path(sys.executable).parent
        if (exe_dir / "ffmpeg.exe").exists():
            os.environ["PATH"] += os.pathsep + str(exe_dir)
            return
    raise RuntimeError(
        "ffmpeg.exe not found.\n"
        "Place ffmpeg.exe next to this program or add it to PATH."
    )

ensure_ffmpeg()

# ═══════════════════════════════════════════════════════════════════════
# Subtitle helper
# ═══════════════════════════════════════════════════════════════════════
def _sec_to_ts(sec: float) -> str:
    h, m = divmod(int(sec), 3600)
    m, s = divmod(m, 60)
    ms   = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def _write_srt(segments, out_path: pathlib.Path):
    with out_path.open("w", encoding="utf-8") as fh:
        for i, seg in enumerate(segments, 1):
            fh.write(f"{i}\n")
            fh.write(f"{_sec_to_ts(seg['start'])} --> {_sec_to_ts(seg['end'])}\n")
            fh.write(seg["text"].lstrip() + "\n\n")

# ═══════════════════════════════════════════════════════════════════════
# Background worker
# ═══════════════════════════════════════════════════════════════════════
def transcribe_worker(args, q: queue.Queue):
    """
    Runs in a background thread (for GUI) or foreground (CLI).

    args ➜ (audio_path, model, lang, save_srt, device_choice, want_prog)
    q    ➜ Queue for progress/status messages (GUI); ignored in CLI
    """
    (audio_path, model, lang, save_srt,
     device_choice, want_prog) = args

    import whisper, torch                                   # heavy imports here

    # ── resolve final torch device
    if device_choice == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    elif device_choice == "gpu":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = "cpu"

    if device_choice == "gpu" and device == "cpu":
        q.put(("status", "CUDA not found → running on CPU"))

    model_obj = whisper.load_model(model, device=device)

    # ── build kwargs with version-safe progress support
    kw = {}
    if lang:
        kw["language"] = lang

    if want_prog and "progress_callback" in inspect.signature(
        whisper.Whisper.transcribe).parameters:
        def _cb(p): q.put(("progress", p))
        kw["progress_callback"] = _cb
        kw["progress_interval"] = 0.2
    else:
        want_prog = False

    q.put(("status", f"Transcribing on {device}…"))

    result = model_obj.transcribe(audio_path, **kw)

    txt_path = pathlib.Path(audio_path).with_suffix(".txt")
    txt_path.write_text(result["text"], encoding="utf-8")

    if save_srt:
        _write_srt(result["segments"],
                   pathlib.Path(audio_path).with_suffix(".srt"))

    q.put(("done", str(txt_path)))

# ═══════════════════════════════════════════════════════════════════════
# GUI front-end
# ═══════════════════════════════════════════════════════════════════════
def run_gui():
    root = tk.Tk(); root.title("Whisper Transcriber")

    # ── form state
    f_var  = tk.StringVar()
    m_var  = tk.StringVar(value="small")
    l_var  = tk.StringVar(value="")
    d_var  = tk.StringVar(value="auto")
    srt_v  = tk.BooleanVar(value=False)

    # ── widgets
    def browse():
        f = filedialog.askopenfilename(
            title="Choose audio/video",
            filetypes=[("Media", "*.wav *.mp3 *.m4a *.mp4 *.flac *.ogg"),
                       ("All", "*.*")]
        )
        if f: f_var.set(f)

    tk.Label(root, text="File:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
    tk.Entry(root, textvariable=f_var, width=50).grid(row=0, column=1, padx=4)
    tk.Button(root, text="Browse…", command=browse).grid(row=0, column=2, padx=4)

    tk.Label(root, text="Model:").grid(row=1, column=0, sticky="w", padx=4)
    ttk.Combobox(root, textvariable=m_var,
                 values=["tiny","small","medium","large"],
                 state="readonly", width=10)\
        .grid(row=1, column=1, sticky="w", padx=4)

    tk.Label(root, text="Language:").grid(row=2, column=0, sticky="w", padx=4)
    ttk.Combobox(root, textvariable=l_var,
                 values=["","en","zh","es","fr","de","hi","ja","ko","ru"],
                 state="readonly", width=10)\
        .grid(row=2, column=1, sticky="w", padx=4)
    tk.Label(root, text="(blank = auto)").grid(row=2, column=2, sticky="w")

    tk.Label(root, text="Device:").grid(row=3, column=0, sticky="w", padx=4)
    ttk.Combobox(root, textvariable=d_var,
                 values=["auto","gpu","cpu"],
                 state="readonly", width=10)\
        .grid(row=3, column=1, sticky="w", padx=4)

    ttk.Checkbutton(root, text="Save .srt subtitles", variable=srt_v)\
        .grid(row=4, column=0, columnspan=2, sticky="w", padx=4, pady=(2,8))

    go_b = tk.Button(root, text="Transcribe")
    go_b.grid(row=5, column=0, columnspan=3, pady=6)

    prog = ttk.Progressbar(root, mode="indeterminate", length=260)
    prog.grid(row=6, column=0, columnspan=3, padx=4, pady=(0,6))
    status_l = tk.Label(root, text="", anchor="w")
    status_l.grid(row=7, column=0, columnspan=3, sticky="w", padx=4)

    # ── background thread plumbing
    q_msg = queue.Queue()

    def process_q():
        try:
            while True:
                typ, val = q_msg.get_nowait()
                if typ == "progress":
                    prog["mode"] = "determinate"
                    prog["value"] = val * 100
                elif typ == "status":
                    status_l.config(text=val)
                elif typ == "done":
                    prog["value"] = 100
                    status_l.config(text="✓ Done")
                    messagebox.showinfo("Finished", f"Transcript saved:\n{val}")
                    go_b["state"] = "normal"
        except queue.Empty:
            pass
        root.after(100, process_q)

    def start():
        path = f_var.get()
        if not path:
            messagebox.showerror("No file", "Please choose a media file."); return
        # reset UI
        prog["value"] = 0; prog["mode"] = "indeterminate"; prog.start(8)
        status_l.config(text="Loading model…"); go_b["state"] = "disabled"

        args = (path, m_var.get(), l_var.get(), srt_v.get(), d_var.get(), True)
        threading.Thread(target=transcribe_worker, args=(args,q_msg),
                         daemon=True).start()

    go_b.config(command=start)
    root.after(100, process_q)
    root.mainloop()

# ═══════════════════════════════════════════════════════════════════════
# CLI fallback
# ═══════════════════════════════════════════════════════════════════════
def run_cli():
    ap = argparse.ArgumentParser(prog="whisper_transcriber")
    ap.add_argument("file")
    ap.add_argument("-m", "--model", default="small",
                    choices=["tiny","small","medium","large"])
    ap.add_argument("--lang", default="")
    ap.add_argument("--srt", action="store_true")
    ap.add_argument("--device", default="auto", choices=["auto","gpu","cpu"])
    args = ap.parse_args()

    q_dummy = queue.Queue()   # unused in CLI
    transcribe_worker((args.file, args.model, args.lang,
                       args.srt, args.device, False), q_dummy)

# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if GUI_AVAILABLE:
        run_gui()
    else:
        run_cli()
