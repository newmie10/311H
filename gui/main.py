import datetime
import tkinter as tk
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import threading
from tkinter import messagebox
import os

# Audio settings
DURATION = 5  # seconds
FS = 44100    # sample rate
OUTPUT_FOLDER = "recordings"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


# def generate_filename():
#     timestamp = datetime.time.asctime()
#     timestamp = str(timestamp[tm_mon] + timestamp[tm_mday] + timestamp[tm_]
#     return f"audio_{timestamp}.wav"

def record_audio():
    print("Recording started...")
    recording = sd.rec(int(DURATION * FS), samplerate=FS, channels=2)
    sd.wait()  # Wait until recording is finished
    filename = "output.wav"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    write(filepath, FS, np.int16(recording * 32767))
    print(f'Recording saved to {filepath}')

def start_recording_thread():
    # Run audio recording in a separate thread to avoid freezing the UI
    threading.Thread(target=record_audio).start()

def toggle_recording():
    global is_recording
    if not is_recording:
        is_recording = True
        start_recording_thread()



def quit_app():
    root.destroy()

# Create the main application window
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Audio Fingerprinting Prototype")
    root.geometry('700x400+250+200')

    # Create a frame for layout (optional)
    frame = tk.Frame(root, padx=20, pady=20)
    # frame.pack()

    # Add a button to start recording/processing
    # record_button = tk.Button(frame, text="Start Recording", command=start_recording, width=20)
    # record_button.pack(pady=5)

    # Add an exit button
    exit_button = tk.Button(text="Quit", command=root.destroy, width=20).pack(anchor="nw", padx=10, pady=10)  # anchor top left with optional padding
    record_button = tk.Button(text="Record Audio", command=start_recording_thread, width=20).pack()

    # Start the Tkinter event loop
    root.mainloop()