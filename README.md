# audiocatalog

**Local acoustic-fingerprint index for duplicate audio.**

![audiocatalog cover](demo/cover.png)

Index audio with Chromaprint, search near-identical recordings, and audit duplicate libraries locally.

![audiocatalog workbench](demo/dashboard.png)

## What ships

- A deterministic domain analysis engine with explicit scope
- JSON API and responsive local browser workbench
- CLI demo and file-driven analysis
- Docker image, unit tests, and GitHub Actions matrix
- No API keys and no uploaded user data

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

## Current basis

- [Chromaprint](https://acoustid.org/chromaprint)

## Demo result

Four tracks produce six candidate pairs. A renamed and re-encoded master matches at 98.65% while unrelated material stays below the 92% threshold. The integration test fingerprints real WAV audio with `fpcalc` and persists it in SQLite.

## Scope

Chromaprint is optimized for near-identical full recordings and long-stream monitoring. It is not a general musical-similarity or short-sample plagiarism detector; duration and fingerprint thresholds should be calibrated on each library.

## Test

```bash
python -m unittest discover -s tests -v
```

MIT licensed.
