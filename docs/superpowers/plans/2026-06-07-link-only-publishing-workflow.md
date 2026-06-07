# Link-Only Publishing Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow a full platform share message to create and run an evidence-grounded video advertising analysis automatically, with confirmation only for missing metadata and separate Douyin/Xiaohongshu publishing views.

**Architecture:** Add a normalized job API and persisted workflow around the existing `ads` table. A focused orchestration service connects link parsing, media understanding, metadata confirmation, six-agent analysis, and channel publishing while the Next.js frontend becomes a paste-first job workspace.

**Tech Stack:** FastAPI, Pydantic 2, aiosqlite, httpx, yt-dlp, ffmpeg, faster-whisper, Next.js 14, React 18, TypeScript, Tailwind CSS 4.

---

## File Map

- Create `backend/app/share_text.py`: extract and normalize supported URLs from arbitrary share text.
- Create `backend/app/workflow.py`: persisted job stages and orchestration.
- Create `backend/app/publishing_pipeline.py`: validated Douyin and Xiaohongshu output generation.
- Create `backend/tests/test_share_text.py`: URL extraction regression tests.
- Create `backend/tests/test_jobs_api.py`: job lifecycle API tests.
- Modify `backend/app/database.py`: additive migration and workflow helpers.
- Modify `backend/app/schemas.py`: job, confirmation, state, and publishing schemas.
- Modify `backend/app/routers/ads.py`: job endpoints and background workflow dispatch.
- Modify `backend/app/agent_pipeline.py`: accept media evidence and normalize scoring output.
- Modify `backend/services/media_pipeline.py`: return durable evidence and accurate stage errors.
- Modify `backend/services/frame_extractor.py`: report actual frame timestamps.
- Create `frontend/app/jobs/[id]/page.tsx`: progress and confirmation workspace.
- Create `frontend/app/jobs/[id]/insight/page.tsx`: insight report.
- Create `frontend/app/jobs/[id]/douyin/page.tsx`: Douyin article and script.
- Create `frontend/app/jobs/[id]/xiaohongshu/page.tsx`: Xiaohongshu adaptation.
- Create `frontend/components/ShareIntake.tsx`: automatic paste intake.
- Create `frontend/components/JobProgress.tsx`: persisted stage display.
- Create `frontend/components/MetadataConfirmation.tsx`: missing-field confirmation.
- Create `frontend/components/ResultNav.tsx`: separate output navigation.
- Modify `frontend/app/page.tsx`, `frontend/app/layout.tsx`, `frontend/app/globals.css`, and `frontend/lib/api.ts`.

### Task 1: Share Text Normalization ✅

**Files:**
- Create: `backend/app/share_text.py`
- Create: `backend/tests/test_share_text.py`

- [ ] Write tests proving a full Douyin share message yields `https://v.douyin.com/zQB8XLGqE4I/`, direct URLs remain unchanged, punctuation is trimmed, and missing/unsupported URLs raise a validation error.
- [ ] Run `backend/.venv/bin/python -m unittest backend.tests.test_share_text -v` and verify RED because `extract_supported_url` does not exist.
- [ ] Implement `extract_supported_url(text: str) -> str` using URL parsing and the supported hostname allowlist from `link_parser`.
- [ ] Re-run the unit test and verify all cases pass.

### Task 2: Additive Job Persistence ✅

**Files:**
- Modify: `backend/app/database.py`
- Modify: `backend/app/schemas.py`
- Create: `backend/tests/test_database_migration.py`

- [ ] Write a migration test that initializes a temporary v0.1 `ads` table and asserts all workflow columns are added without deleting its row.
- [ ] Run the migration test and verify RED on missing columns.
- [ ] Add idempotent `ALTER TABLE` migration helpers for source, parsed metadata, workflow, media evidence, confirmation confidence, publishing output, and failure stage.
- [ ] Add `JobCreateRequest`, `JobStateResponse`, and `MetadataConfirmationRequest` Pydantic models.
- [ ] Re-run migration and schema tests.

### Task 3: Persisted Workflow State Machine ✅

**Files:**
- Create: `backend/app/workflow.py`
- Create: `backend/tests/test_workflow.py`

- [ ] Write fake-service tests for `resolving → media → identifying → needs_confirmation` and `resolving → media → identifying → analyzing → publishing → completed`.
- [ ] Run tests and verify RED because the workflow service does not exist.
- [ ] Implement stage constants, database stage updates, dependency injection for parser/media/analyzer/publisher, confirmation gating, and failure persistence.
- [ ] Ensure transcript/frame failures can degrade when at least one evidence source remains.
- [ ] Run workflow tests and verify both paths pass.

### Task 4: Connect Video Evidence to Analysis ✅

**Files:**
- Modify: `backend/services/frame_extractor.py`
- Modify: `backend/services/media_pipeline.py`
- Modify: `backend/app/agent_pipeline.py`
- Create: `backend/tests/test_media_evidence.py`

- [ ] Write regression tests proving frame records use ffmpeg-derived timestamps and Agent 1 receives transcript plus frame payloads.
- [ ] Run tests and verify RED on estimated timestamps/disconnected transcript.
- [ ] Capture frame timestamps with ffmpeg `showinfo` or timestamp-bearing filenames.
- [ ] Build an Agent 1 media context containing transcript, timestamped frames, and parsed metadata.
- [ ] Normalize Agent 6 responses so both wrapped and unwrapped scoring JSON produce one stable shape.
- [ ] Re-run media and agent tests.

### Task 5: Professional Publishing Pipeline ✅

**Files:**
- Create: `backend/app/publishing_pipeline.py`
- Create: `backend/tests/test_publishing_pipeline.py`

- [ ] Write schema tests for Douyin article, 60-90 second script, and Xiaohongshu output.
- [ ] Verify RED before implementation.
- [ ] Add prompts that require evidence-grounded copy, strong but non-deceptive hooks, publishable Chinese prose, CTA, hashtags, spoken beats, and image-card suggestions.
- [ ] Validate and normalize model JSON; preserve completed insight if publishing fails.
- [ ] Verify tests pass with fake model responses.

### Task 6: Job API ✅

**Files:**
- Modify: `backend/app/routers/ads.py`
- Create: `backend/tests/test_jobs_api.py`

- [ ] Write API tests for full-share-message job creation, `needs_confirmation`, metadata PATCH resume, job state retrieval, and retry.
- [ ] Verify RED because `/api/jobs` does not exist.
- [ ] Add `POST /api/jobs`, `GET /api/jobs/{id}`, `PATCH /api/jobs/{id}/metadata`, and `POST /api/jobs/{id}/retry`.
- [ ] Dispatch workflow through `BackgroundTasks`; return `202` immediately.
- [ ] Re-run API tests and existing health/ad smoke tests.

### Task 7: Paste-First Frontend ✅

**Files:**
- Create: `frontend/components/ShareIntake.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/app/layout.tsx`

- [ ] Add a lightweight Node test for frontend URL detection/auto-submit behavior in a pure helper.
- [ ] Verify RED before implementing the helper.
- [ ] Replace the manual form home page with an oversized share-text intake that auto-submits after a valid URL appears.
- [ ] Add sample share copy, paste feedback, graceful validation, and a fallback submit button for accessibility.
- [ ] Apply the research-desk editorial design tokens and responsive typography.
- [ ] Run the helper test and `npm run build`.

### Task 8: Progress, Confirmation, and Separate Results ✅

**Files:**
- Create: `frontend/app/jobs/[id]/page.tsx`
- Create: `frontend/app/jobs/[id]/insight/page.tsx`
- Create: `frontend/app/jobs/[id]/douyin/page.tsx`
- Create: `frontend/app/jobs/[id]/xiaohongshu/page.tsx`
- Create: `frontend/components/JobProgress.tsx`
- Create: `frontend/components/MetadataConfirmation.tsx`
- Create: `frontend/components/ResultNav.tsx`

- [ ] Implement polling against persisted job state and stop polling on confirmation, failure, or completion.
- [ ] Render only missing metadata fields on confirmation and resume after PATCH.
- [ ] Build distinct manuscript-style pages for insight, Douyin article/script tabs, and Xiaohongshu adaptation.
- [ ] Add copy buttons and empty/error states without mutating generated content.
- [ ] Run TypeScript production build.

### Task 9: End-to-End Verification and Documentation ✅

**Files:**
- Modify: `README.md`
- Modify: `docs/API.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/CHANGELOG.md`

- [ ] Run all backend unit and API tests.
- [ ] Run Python compilation and frontend production build.
- [ ] Start or reload local services.
- [ ] Use the browser to paste the supplied Douyin share message and verify automatic navigation.
- [ ] Verify either automatic completion or the minimal confirmation path using visible UI state.
- [ ] Verify result navigation and copy controls on desktop and mobile viewport.
- [ ] Document actual implemented behavior and remaining platform limitations.

## Self-Review

- Spec coverage: automatic intake, confirmation gate, media integration, progress, professional outputs, separate pages, retry, and browser verification are each mapped to tasks.
- Type consistency: publishing output remains one `publishing_output` object with `douyin_article`, `douyin_script`, and `xiaohongshu`.
- Scope: automatic posting, distributed queues, semantic search, live news, and standalone OCR remain excluded.
- Workspace exception: commit steps are omitted because this directory is not a Git repository.
