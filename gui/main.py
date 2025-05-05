# gui/main.py
import sys, os
# so "processing/fft.py" can be imported
sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))

import queue, threading, time
import tkinter as tk
from tkinter import filedialog, simpledialog
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as wavwrite
from processing.fft import enroll, identify, DATA_PATH

REC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recordings"))
os.makedirs(REC_DIR, exist_ok=True)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Shazam (Custom Recordings)")
        self.geometry("460x300")
        self.resizable(False, False)

        tk.Label(self, text="Mini Shazam Demo", font=("Helvetica", 18, "bold"))\
          .pack(pady=10)

        tk.Button(self, text="Enroll a WAV file", width=30,
                  command=self.enroll_file).pack(pady=5)

        tk.Button(self, text="Record & Enroll (Custom)", width=30,
                  command=lambda: self.record(enroll_mode=True)).pack(pady=5)

        tk.Button(self, text="Record & Identify (Custom)", width=30,
                  command=lambda: self.record(enroll_mode=False)).pack(pady=15)

        self.status = tk.Label(self, text="", fg="blue")
        self.status.pack(pady=8)

        tk.Label(self, text=f"Fingerprint store: {os.path.basename(DATA_PATH)}")\
          .pack(side="bottom")

    def enroll_file(self):
        path = filedialog.askopenfilename(filetypes=[("WAV files","*.wav")])
        if not path:
            return
        name = os.path.splitext(os.path.basename(path))[0]
        self.set_status(f"Enrolling '{name}' …")
        threading.Thread(target=self._enroll_bg, args=(path, name), daemon=True).start()

    def _enroll_bg(self, path, name):
        try:
            enroll(path, name)
            self.set_status(f"✓ Enrolled '{name}'")
        except Exception as e:
            self.set_status(f"Error enrolling: {e}")

    def record(self, enroll_mode):
        # Ask user for duration
        dur = simpledialog.askinteger(
            "Recording Duration",
            "Enter duration (seconds):",
            initialvalue=7,
            minvalue=1, maxvalue=300,
            parent=self)
        if dur is None:
            return

        # If enrolling, ask for a name
        name = None
        if enroll_mode:
            name = simpledialog.askstring(
                "Recording Name",
                "Enter a name for this recording:",
                parent=self)
            if not name:
                return

        fs = 44100
        q = queue.Queue()

        def callback(indata, frames, time_, status):
            q.put(indata.copy())

        self.set_status(f"Recording {dur}s …")
        with sd.InputStream(channels=1, samplerate=fs, callback=callback):
            buf = []
            start = time.time()
            while time.time() - start < dur:
                buf.append(q.get())

        # Concatenate chunks and convert to 16-bit PCM
        audio_np = np.concatenate(buf, axis=0)
        audio_int16 = (audio_np * 32767).astype(np.int16).flatten()

        wav_path = os.path.join(REC_DIR, f"tmp_{int(time.time())}.wav")
        wavwrite(wav_path, fs, audio_int16)

        if enroll_mode:
            self.set_status(f"Enrolling '{name}' …")
            threading.Thread(
                target=self._enroll_bg,
                args=(wav_path, name),
                daemon=True
            ).start()
        else:
            self.set_status("Identifying …")
            threading.Thread(
                target=self._identify_bg,
                args=(wav_path,),
                daemon=True
            ).start()

    def _identify_bg(self, path):
        try:
            song, score = identify(path)
            if song:
                self.set_status(f"◎  Match: '{song}'  (score {score})")
            else:
                self.set_status("✗  No match found")
        except Exception as e:
            self.set_status(f"Error identifying: {e}")

    def set_status(self, txt):
        self.status["text"] = txt
        self.update_idletasks()

if __name__ == "__main__":
    App().mainloop()