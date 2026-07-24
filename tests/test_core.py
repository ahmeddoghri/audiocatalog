import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from audiocatalog.core import Catalog, DEMO, analyze, fingerprint


def tone(path: Path, frequency: float) -> None:
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, 11025, 0, "NONE", "not compressed"))
        output.writeframes(b"".join(struct.pack("<h", int(9000 * math.sin(2 * math.pi * frequency * index / 11025))) for index in range(132300)))


class AudioCatalogTest(unittest.TestCase):
    def test_demo_finds_renamed_master(self):
        result = analyze(DEMO)
        self.assertEqual(result["duplicate_pairs"], 1)
        self.assertGreater(result["matches"][0]["similarity"], 0.98)

    def test_fpcalc_and_sqlite_index_real_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            first, duplicate = Path(directory) / "first.wav", Path(directory) / "duplicate.wav"
            tone(first, 440)
            duplicate.write_bytes(first.read_bytes())
            item_a, item_b = fingerprint(str(first)), fingerprint(str(duplicate))
            catalog = Catalog(str(Path(directory) / "catalog.db"))
            catalog.add(item_a)
            catalog.add(item_b)
            result = analyze({"tracks": catalog.tracks(), "threshold": 0.99})
            self.assertEqual(result["duplicate_pairs"], 1)


if __name__ == "__main__":
    unittest.main()
