# processing/fft.py
import hashlib
import os
import pickle
import numpy as np
from scipy.io import wavfile
from scipy.signal import spectrogram

# Fingerprint store (one level up from processing/)
DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "fingerprints.pkl")
)

def _load_db():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "rb") as f:
            return pickle.load(f)
    return {}  # song_name → list of (hash, offset)

def _save_db(db):
    with open(DATA_PATH, "wb") as f:
        pickle.dump(db, f)

def _fingerprint(path):
    sr, data = wavfile.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)  # stereo→mono
    f, t, S = spectrogram(data, sr, nperseg=2048, noverlap=1024)
    thresh = np.percentile(S, 92)
    peaks = np.argwhere(S > thresh)
    for y, x in peaks:
        h = hashlib.sha1(f"{int(f[y])}|{int(t[x]*1000)}".encode()) \
               .hexdigest()[:20]
        yield h, int(t[x] * 1000)

def enroll(path, name):
    """Enroll a .wav under the given name."""
    db = _load_db()
    db[name] = list(_fingerprint(path))  # overwrite if existing
    _save_db(db)

def identify(path):
    """Identify the song in path; returns (best_name, score) or (None, None)."""
    sample = list(_fingerprint(path))
    if not sample:
        return None, None

    db = _load_db()
    best, best_score = None, 0

    for song, prints in db.items():
        lookup = {}
        for h, off in prints:
            lookup.setdefault(h, []).append(off)
        score = 0
        for h, off in sample:
            for ref_off in lookup.get(h, []):
                if abs(ref_off - off) < 100:
                    score += 1
        if score > best_score:
            best, best_score = song, score

    if best_score > 0:
        return best, best_score
    return None, None
