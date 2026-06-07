# Link-Only Publishing Workflow Design

## Objective

Transform ai-ad from a text-form analysis tool into a link-first product. A user pastes a complete platform share message, and the system extracts the URL, resolves video metadata, understands the media, runs advertising analysis, and creates publication-ready content.

The primary publishing channel is Douyin. Xiaohongshu is a secondary adaptation.

## User Experience

### 1. Automatic Intake

The home page contains one dominant paste area. It accepts either:

- a direct supported URL;
- a full share message such as `3.89 ... https://v.douyin.com/... 复制此链接...`.

As soon as pasted content contains a supported URL, the frontend creates an analysis job. There is no manual advertising form on the main page.

### 2. Metadata Confirmation

The backend parses title, author, description, source platform, cover, and video metadata. It then uses media and model evidence to infer brand, product, and industry.

If brand, product, and industry are sufficiently complete, processing continues automatically. If any critical field is missing, the job enters `needs_confirmation`, and the user sees a minimal page containing only missing fields plus the resolved cover/title.

### 3. Progress

The progress page displays persisted stages:

1. resolving link;
2. downloading media;
3. transcribing audio;
4. extracting and understanding frames;
5. identifying advertising metadata;
6. running advertising analysis;
7. writing channel content;
8. completed.

Each stage stores status, public progress text, and an actionable error. Failed stages can be retried without creating a duplicate record.

### 4. Result Navigation

Completed analyses expose a result workspace with separate views:

- `Insight`: professional advertising analysis, score, evidence, strategy, and creative DNA;
- `Douyin Article`: publishable title, opening, body, closing prompt, and hashtags;
- `Douyin Script`: 60-90 second spoken script split into hook, body beats, and CTA;
- `Xiaohongshu`: title alternatives, concise body, topic tags, and image-card suggestions.

Each publishing view has copy controls and preserves the original generated content.

## System Architecture

### Intake Boundary

`share_text.py` owns URL extraction and platform validation. It accepts arbitrary user text and returns a normalized supported URL. Link parsers receive URLs only.

### Persistence

The existing `ads` table is migrated additively with:

- `source_text`, `source_url`, `source_platform`;
- parsed title, author, cover, and metadata JSON;
- media path, transcript JSON, frame summary JSON;
- workflow stage and progress;
- inferred metadata confidence;
- publishing output JSON;
- failure stage and retryable error.

Existing records remain readable.

### Workflow Service

`analysis_workflow.py` owns orchestration. API routes do not perform media or LLM work directly. The service updates database state after each stage.

The first implementation uses FastAPI background tasks and persisted SQLite state. This is appropriate for a local single-user product and avoids adding Redis/Celery. The workflow interface remains separable so a durable worker can replace it later.

### Media and Agent Integration

The existing media pipeline becomes part of the main workflow. Transcript text and sampled frames feed Agent 1. Metadata inference runs before the full six-agent pipeline so missing critical fields can trigger confirmation.

Frame timestamps must come from ffmpeg/ffprobe evidence rather than being estimated from frame array position. OCR remains a vision-model responsibility for this iteration and is not presented as a standalone OCR engine.

### Publishing Output

Advertising analysis and publishing are separate model responsibilities:

- analysis produces evidence-grounded strategy and scoring;
- publishing receives the completed analysis and creates channel-specific content.

Publishing output uses a validated JSON schema. It must avoid invented performance claims, distinguish observation from inference, and omit unsupported statistics.

## Frontend Direction

The interface uses a research-desk/editorial aesthetic rather than a generic dashboard:

- warm paper background, charcoal typography, vermilion action accent;
- one oversized intake surface with sample share text;
- strong Chinese editorial typography and numbered processing stages;
- asymmetrical result workspace with a compact left navigation and generous reading column;
- publication pages resemble an editor's manuscript, not configuration forms.

The memorable interaction is the paste surface turning into a live analysis dossier without requiring form completion.

## API Shape

### Create Job

`POST /api/jobs`

```json
{"share_text": "full share message or direct URL"}
```

Returns `202` with `id`, `status`, `stage`, and `next_url`.

### Job State

`GET /api/jobs/{id}`

Returns metadata, workflow state, progress, missing fields, and available result views.

### Confirm Missing Metadata

`PATCH /api/jobs/{id}/metadata`

Accepts only `brand_name`, `product_name`, and `industry`, then resumes the workflow.

### Retry

`POST /api/jobs/{id}/retry`

Restarts from the failed stage when possible.

Existing `/api/ads` read endpoints remain available for historical records during migration.

## Error Handling

- Unsupported or absent URL: reject before job creation with a Chinese validation message.
- Link metadata failure: retain the normalized URL and try media download.
- Media download failure: mark `failed` with the platform-specific reason and retry action.
- Audio unavailable: continue with frames and metadata.
- Frame extraction unavailable: continue with transcript and metadata.
- Critical metadata missing: enter confirmation, not failure.
- LLM response invalid: retry once, then persist the failing stage and raw diagnostic summary without secrets.
- Publishing generation failure: preserve completed insight analysis and allow publishing-only retry.

## Testing Strategy

- Unit tests for full-share-message URL extraction and unsupported input.
- API tests for automatic job creation, confirmation transitions, and retry behavior.
- Workflow tests with injected fake parser, media pipeline, and model services.
- Schema tests for publishing outputs.
- Regression tests proving `source_url` is persisted and media evidence reaches Agent 1.
- Frontend production build and browser tests for paste-to-progress, confirmation, and result navigation.

## Out of Scope

- Multi-user authentication.
- Distributed queues.
- Automatic posting to Douyin or Xiaohongshu.
- Semantic FAISS search and live-news ingestion.
- A standalone OCR engine.
