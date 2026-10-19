"""End to end on real audio: ffmpeg renders it, fpcalc fingerprints it.

The demo fixture is hand-written illustrative data. This renders actual
files, transcodes one of them, and checks the thing the tool claims: a
re-encoded export matches its source, and a different recording does not.
Skipped when ffmpeg or fpcalc is unavailable.
"""
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from audiocatalog.core import fingerprint, similarity

NEEDS = shutil.which("ffmpeg") and shutil.which("fpcalc")


def _render(directory: Path) -> dict[str, Path]:
    song = directory / "song.wav"
    export = directory / "song-export.mp3"
    other = directory / "other.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", "sine=frequency=330:duration=20,tremolo=f=5:d=0.7",
                    "-ac", "2", "-ar", "44100", str(song)], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(song),
                    "-codec:a", "libmp3lame", "-b:a", "128k", str(export)], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", "sine=frequency=550:duration=20,vibrato=f=7",
                    "-ac", "2", "-ar", "44100", str(other)], check=True)
    return {"song": song, "export": export, "other": other}


@unittest.skipUnless(NEEDS, "needs ffmpeg and fpcalc")
class RealAudioTest(unittest.TestCase):
    def test_a_transcoded_export_matches_its_source_and_a_different_recording_does_not(self):
        with TemporaryDirectory() as directory:
            files = _render(Path(directory))
            prints = {name: fingerprint(str(path))["fingerprint"] for name, path in files.items()}
        duplicate = similarity(prints["song"], prints["export"])
        unrelated = similarity(prints["song"], prints["other"])
        self.assertGreaterEqual(duplicate, 0.92, duplicate)
        self.assertLess(unrelated, 0.92, unrelated)
        self.assertGreater(duplicate - unrelated, 0.15, (duplicate, unrelated))

    def test_real_fingerprint_words_use_the_full_32_bit_range(self):
        # The old value-dependent normalization was distorted precisely
        # because real words are ~30 bits while the demo fixture is 8-16.
        with TemporaryDirectory() as directory:
            files = _render(Path(directory))
            words = fingerprint(str(files["song"]))["fingerprint"]
        self.assertGreater(max(words), 2 ** 28)


if __name__ == "__main__":
    unittest.main()
