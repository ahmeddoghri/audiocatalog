from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any


DEMO = {
    "threshold": 0.92,
    "tracks": [
        {"path": "masters/song-final.wav", "duration": 184, "fingerprint": [1023, 4095, 3855, 255, 43690, 61680]},
        {"path": "exports/song-final-v7.mp3", "duration": 183, "fingerprint": [1023, 4095, 3855, 255, 43690, 61681]},
        {"path": "archive/live-take.flac", "duration": 242, "fingerprint": [65535, 1, 32768, 21845, 13107, 255]},
        {"path": "samples/kick-loop.wav", "duration": 8, "fingerprint": [43690, 21845, 61680, 3855, 255, 65280]},
    ],
}


FINGERPRINT_WORD_BITS = 32  # Chromaprint raw fingerprint words are 32-bit unsigned integers


def similarity(left: list[int], right: list[int]) -> float:
    """Fraction of matching bits across the shared fingerprint words,
    normalized to Chromaprint's actual 32-bit word width. Normalizing by
    each value's bit_length() instead (the minimum bits needed to
    represent that specific number) makes the denominator depend on the
    numeric magnitude of the fingerprint words rather than their fixed
    width -- a genuinely different, non-standard, and misleading metric,
    not just a rounding difference."""
    length = min(len(left), len(right))
    if not length:
        return 0.0
    different = sum((int(left[index]) ^ int(right[index])).bit_count() for index in range(length))
    return 1 - different / (FINGERPRINT_WORD_BITS * length)


def fingerprint(path: str) -> dict[str, Any]:
    process = subprocess.run(["fpcalc", "-raw", "-json", path], capture_output=True, text=True)
    if process.returncode:
        raise ValueError("fpcalc failed: " + process.stderr.strip())
    payload = json.loads(process.stdout)
    raw = payload.get("fingerprint", [])
    if isinstance(raw, str):
        raw = [int(value) for value in raw.split(",") if value]
    return {"path": path, "duration": int(round(float(payload.get("duration", 0)))), "fingerprint": raw}


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    tracks = payload.get("tracks", [])
    if len(tracks) < 2:
        raise ValueError("at least two tracks are required")
    threshold = float(payload.get("threshold", 0.92))
    matches = []
    for index, left in enumerate(tracks):
        for right in tracks[index + 1:]:
            duration_gap = abs(float(left.get("duration", 0)) - float(right.get("duration", 0)))
            score = similarity(left.get("fingerprint", []), right.get("fingerprint", []))
            if score >= threshold and duration_gap <= 5:
                matches.append({"left": left["path"], "right": right["path"], "similarity": round(score, 4), "duration_gap_seconds": duration_gap})
    matches.sort(key=lambda item: item["similarity"], reverse=True)
    return {"track_count": len(tracks), "pairs_compared": len(tracks) * (len(tracks) - 1) // 2, "duplicate_pairs": len(matches), "threshold": threshold, "matches": matches}


class Catalog:
    def __init__(self, database: str) -> None:
        self.connection = sqlite3.connect(database)
        self.connection.execute("CREATE TABLE IF NOT EXISTS tracks(path TEXT PRIMARY KEY, duration INTEGER, fingerprint TEXT)")

    def add(self, item: dict[str, Any]) -> None:
        self.connection.execute("INSERT OR REPLACE INTO tracks VALUES(?,?,?)", (item["path"], item["duration"], json.dumps(item["fingerprint"])))
        self.connection.commit()

    def tracks(self) -> list[dict[str, Any]]:
        return [{"path": row[0], "duration": row[1], "fingerprint": json.loads(row[2])} for row in self.connection.execute("SELECT path,duration,fingerprint FROM tracks ORDER BY path")]


def index_directory(directory: str, database: str) -> dict[str, Any]:
    root = Path(directory)
    if not root.is_dir():
        raise ValueError(f"directory not found: {directory}")
    catalog = Catalog(database)
    extensions = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac"}
    for path in sorted(item for item in root.rglob("*") if item.suffix.lower() in extensions):
        catalog.add(fingerprint(str(path)))
    return analyze({"tracks": catalog.tracks(), "threshold": 0.92}) if len(catalog.tracks()) >= 2 else {"track_count": len(catalog.tracks()), "matches": []}
