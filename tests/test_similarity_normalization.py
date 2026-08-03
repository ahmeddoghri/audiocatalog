import random
import unittest

from audiocatalog.core import DEMO, FINGERPRINT_WORD_BITS, analyze, similarity


def _correct_similarity(left, right, bits=32):
    length = min(len(left), len(right))
    if not length:
        return 0.0
    different = sum(bin(int(l) ^ int(r)).count("1") for l, r in zip(left, right))
    return 1 - different / (bits * length)


class SimilarityNormalizationTest(unittest.TestCase):
    """similarity() previously normalized each fingerprint word's bit
    difference by bit_length() -- the minimum bits needed to represent
    that specific integer value -- instead of Chromaprint's fixed 32-bit
    word width. That makes the denominator depend on the numeric
    magnitude of the fingerprint words, not their actual bit width, which
    is a genuinely different (and non-standard) metric."""

    def test_matches_fixed_32_bit_hamming_similarity(self):
        left = [1023, 4095, 3855, 255, 43690, 61680]
        right = [1023, 4095, 3855, 255, 43690, 61681]
        self.assertAlmostEqual(similarity(left, right), _correct_similarity(left, right), places=9)

    def test_word_width_constant_is_32_bits(self):
        self.assertEqual(FINGERPRINT_WORD_BITS, 32)

    def test_small_magnitude_values_no_longer_distort_unrelated_pair_scores(self):
        """The demo's own illustrative fingerprint values are all well
        under 65536 (far smaller than real fpcalc's ~30-bit-magnitude
        output). Under the old bit_length()-based normalization, that
        alone dragged unrelated pairs' scores down to ~0.38-0.46, an
        artificially wide "separation" from the 0.92 threshold that had
        nothing to do with genuine acoustic dissimilarity. Confirm the
        corrected metric no longer depends on the fingerprint values'
        numeric magnitude."""
        small_left, small_right = [3, 5, 9], [12, 20, 36]
        large_left = [value << 20 for value in small_left]
        large_right = [value << 20 for value in small_right]
        self.assertAlmostEqual(similarity(small_left, small_right), similarity(large_left, large_right), places=9)

    def test_ranking_matches_correct_metric_on_realistic_random_fingerprints(self):
        """Stress test against realistic (uniformly random 32-bit word)
        fingerprints: a near-duplicate (a handful of bits flipped) must
        always rank above an unrelated fingerprint, matching the
        theoretically correct 32-bit Hamming similarity."""
        rng = random.Random(7)

        def make_fp(n=120):
            return [rng.getrandbits(32) for _ in range(n)]

        def perturb(fp, flips):
            out = fp[:]
            for _ in range(flips):
                idx = rng.randrange(len(out))
                out[idx] ^= 1 << rng.randrange(32)
            return out

        for _ in range(30):
            base = make_fp()
            near_dup = perturb(base, flips=8)
            unrelated = make_fp()
            self.assertGreater(similarity(base, near_dup), similarity(base, unrelated))

    def test_demo_still_finds_exactly_one_duplicate_pair(self):
        result = analyze(DEMO)
        self.assertEqual(result["duplicate_pairs"], 1)
        self.assertGreater(result["matches"][0]["similarity"], 0.99)
        for track_a in DEMO["tracks"]:
            for track_b in DEMO["tracks"]:
                if track_a is track_b:
                    continue
                pair = {track_a["path"], track_b["path"]}
                if pair != {"masters/song-final.wav", "exports/song-final-v7.mp3"}:
                    self.assertLess(similarity(track_a["fingerprint"], track_b["fingerprint"]), 0.92)


if __name__ == "__main__":
    unittest.main()
