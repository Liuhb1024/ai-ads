# Findings

## Product Intent
- ai-ad is a local advertising creative analysis tool focused on short-video ads.
- Intended input is a shared video URL, with manual form entry as fallback.
- Intended output is an editorial-style Markdown insight note, quantitative creative scoring, reusable creative DNA, and a searchable Swipe File.

## Documented Architecture
- Frontend: Next.js 14 App Router.
- Backend: FastAPI, Python, SQLite.
- Current and planned analysis stages include link parsing, media understanding, live intelligence, multi-agent analysis, scoring, and knowledge-base indexing.

## Version Drift
- README labels v0.1 Mock as current and v0.2 as largely designed.
- `docs/TASKS.md` says the Editorial Swiss UI, link parsing, Mock scoring, and Swipe File are implemented.
- Actual source inspection is required before describing current capabilities.

## Actual Main Workflow
- The frontend parses a shared URL and uses returned metadata to prefill `ad_title`, `ad_copy`, and `platform`.
- The backend `AdCreateRequest` does not accept or persist `source_url`; the extra frontend field is ignored by Pydantic.
- The main `/ads/{id}/analyze` route builds analysis input only from stored text fields.
- If `DMXAPI_API_KEY` is configured, it runs a real six-agent LLM pipeline; otherwise it runs deterministic heuristic Mock analysis.
- The main route does not pass a video URL, local video, extracted frames, or transcript into the real agent pipeline.

## Implemented But Disconnected
- `/api/analyze-media` can download a video, extract scene-change frames, and run faster-whisper transcription.
- Vision and video input clients exist in the LLM layer.
- These capabilities are not connected to ad creation or the primary analysis button.
- `ocr.py` does not perform OCR yet; it resizes frames and converts them to base64 for a vision model.

## Current Storage and Swipe File
- SQLite has only the v0.1 `ads` table, not the documented v0.2 tag, intelligence, or embedding tables.
- Database contains 6 completed analyses.
- Swipe File is a client-side filtered view of completed ads, loading at most 50 rows.
- Search is substring matching across brand, product, takeaway, and industry, not semantic search.
- FAISS, sentence-transformers, and newsbox are not present in runtime dependencies.

## Scoring
- Mock and real pipelines expose scoring, creative DNA, and swipe tags.
- The implemented score has 20 numeric dimensions across 7 categories, despite docs and UI copy calling it 28 dimensions.
- Five of six persisted analyses contain a `scoring` object, but only three expose the expected nested `overall_score`; historical/LLM output shape is not fully consistent.

## Verification
- Python `compileall` passed for backend application and services.
- FastAPI loaded with 8 distinct `/api` route paths.
- Current environment reports the LLM client as configured.
- Next.js production build completed successfully for `/`, `/ads`, `/ads/[id]`, and `/swipe`.

## Optimization Implementation
- Full Douyin share text now extracts the short URL and creates a job without manual form fields.
- The native Douyin parser now exposes its embedded playback URL; direct download was verified with a 9.1 MB, 24.5-second video.
- Main workflow now persists stages and connects download, 155-character Whisper transcript, 16 timestamped frames, six-agent analysis, and publishing.
- Real test job `4942f181` completed with a 65 score, 874-character Douyin article, 75-second spoken script, and three Xiaohongshu title options.
- Browser verification covered the redesigned intake, insight, Douyin, Xiaohongshu, and clipboard fallback behavior.

## Evidence Report Upgrade
- `DOUBAO_VIDEO_MODEL` already defaults to `doubao-seed-2-0-lite-260215`.
- The automatic workflow calls `run_agent_pipeline` with frames only; it never passes `media.video_path`, so the Doubao branch cannot run.
- The agent pipeline already supports local video base64 input, but a failed video request currently skips frame vision and falls directly to text.
- Existing report Markdown is generated freely by the LLM, which makes format stability and PDF parity weak.
- Existing export only returns Markdown. The backend has no PDF dependency or endpoint.
- The frontend report uses React Markdown but has no download controls or structured trust/provenance presentation.

## Evidence Report Verification
- Real job `f3073efa` called `doubao-seed-2-0-lite-260215` with `source_mode=video` and no fallback error.
- The full-video pass produced 8 timestamped evidence records after the final rerun.
- Claim-ID audit approved 13 claims and rejected 6; exact rejected claims did not appear in publication copy.
- Trust calibration retained the model score (0) and local deterministic score (78), exposing a final calibrated score of 63 rather than hiding the disagreement.
- Position-balanced judging selected the same final candidate in both orders.
- Final exports were a 20 KB Markdown report and a 304 KB PDF 1.7 document.
- Desktop and 390 px mobile browser checks passed with no console errors.
