# audiocatalog

**Rename a file, re-encode it, and it's still the same recording — your filesystem just can't tell anymore.**

![audiocatalog cover](demo/cover.png)

A music library that grew across a decade of imports, exports, and format conversions ends up with the same song under three different filenames and two different codecs, and no directory listing will ever show you that. audiocatalog fingerprints the actual audio content with Chromaprint (the engine behind AcoustID), so "song-final.wav" and "song-final-v7.mp3" get recognized as duplicates because they sound the same, not because their names happen to match.

![audiocatalog workbench](demo/dashboard.png)

## How it works

Run every file through `fpcalc` to get a real Chromaprint acoustic fingerprint, store it in SQLite, and compare every pair of fingerprints for similarity above a calibrated threshold. Filename, format, and bitrate never enter the comparison — a WAV master and an MP3 export of the same recording collapse to a near-identical fingerprint even though every byte of the file itself is different.

## What ships

- Real Chromaprint fingerprinting via `fpcalc`, not a filename or metadata heuristic
- Pairwise similarity search across a library with a calibrated duplicate threshold
- SQLite-backed index so re-scanning a library doesn't mean re-fingerprinting everything
- CLI, JSON API, browser workbench, Docker, tests, and CI

## Run it end to end

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -e .
audiocatalog demo
audiocatalog index ~/Music --database music.db
audiocatalog serve
```

Open <http://127.0.0.1:8090>. Analyze your own JSON input with `audiocatalog analyze input.json`.

## API

- `GET /api/demo` returns the committed fixture and result.
- `POST /api/analyze` runs the same engine on a JSON body.

## The result

Four tracks produce six candidate pairs. One pair — a renamed, re-encoded copy of the same master — matches at 98.65% similarity, while every unrelated pair stays under the 92% threshold with real separation, not a near-miss. The integration test doesn't stop at fixture data: it fingerprints real WAV audio with `fpcalc` and persists the result in SQLite.

## Scope

Chromaprint is built for near-identical full recordings and long-stream monitoring, not general musical similarity, cover-song detection, or short-sample plagiarism matching. Duration and threshold should be calibrated per library — a classical recording archive and a DJ mix collection want different cutoffs.

## Test

```bash
python -m unittest discover -s tests -v
```

## Research basis

- [Chromaprint](https://acoustid.org/chromaprint)

MIT licensed.
