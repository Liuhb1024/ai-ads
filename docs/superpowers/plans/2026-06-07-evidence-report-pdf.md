# Evidence Report and PDF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Route downloaded video through Doubao, add auditable multi-agent analysis, and provide a professional Markdown/PDF report.

**Architecture:** The workflow passes local video, frames, and transcript into an evidence-first agent pipeline. A deterministic report builder renders structured analysis to Markdown and HTML, while WeasyPrint handles PDF output. Frontend report actions use the same backend exports.

**Tech Stack:** FastAPI, Python async clients, SQLite, unittest, Markdown, WeasyPrint, Next.js 14, React Markdown, CSS.

---

### Task 1: Lock Doubao Video Routing

**Files:**
- Modify: `backend/app/workflow.py`
- Test: `backend/tests/test_workflow.py`
- Test: `backend/tests/test_agent_pipeline.py`

- [x] Add a workflow test asserting `run_agent_pipeline` receives the persisted/downloaded `video_path`.
- [x] Add an agent test asserting `chat_completion_video` uses `doubao-seed-2-0-lite-260215`.
- [x] Run the focused tests and verify they fail before implementation.
- [x] Pass `video_path`, remote fallback URL, and frames into the pipeline.
- [x] Make video failure fall back to frame vision before text.
- [x] Run focused tests and verify they pass.

### Task 2: Evidence and Audit Agents

**Files:**
- Modify: `backend/app/agent_pipeline.py`
- Create: `backend/app/analysis_quality.py`
- Test: `backend/tests/test_analysis_quality.py`

- [x] Add deterministic normalization for evidence IDs, claim types, confidence, and audit output.
- [x] Replace free-form material analysis with a time-coded evidence ledger schema.
- [x] Require strategy, audience, and context claims to cite evidence.
- [x] Add a factuality auditor and anchored scoring prompts.
- [x] Add analysis metadata with model name, source mode, audit status, and fallback information.
- [x] Test invalid evidence references, unsupported observed claims, and trust-score normalization.

### Task 3: Creative Evaluation and Publishing

**Files:**
- Modify: `backend/app/publishing_pipeline.py`
- Test: `backend/tests/test_publishing_pipeline.py`

- [x] Generate two distinct editorial candidates from audited context.
- [x] Judge candidates in forward and reverse order.
- [x] Select a stable winner or synthesize when judge order disagrees.
- [x] Preserve deterministic fallback output.
- [x] Validate all publication sections and provenance fields.

### Task 4: Deterministic Professional Report

**Files:**
- Create: `backend/app/reporting.py`
- Modify: `backend/app/workflow.py`
- Modify: `backend/app/routers/ads.py`
- Test: `backend/tests/test_reporting.py`
- Test: `backend/tests/test_jobs_api.py`

- [x] Build Markdown from structured analysis and publication output.
- [x] Include cover, executive summary, trust panel, evidence ledger, scorecard, insights, risks, publication package, and methodology.
- [x] Use the builder for both existing ads and automatic jobs.
- [x] Add attachment endpoints for `.md` and `.pdf`.
- [x] Return correct content types and filenames.

### Task 5: PDF Renderer

**Files:**
- Create: `backend/app/pdf_export.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_pdf_export.py`

- [x] Convert Markdown to HTML using a controlled extension set.
- [x] Add an editorial print stylesheet with CJK font fallbacks and page-break rules.
- [x] Render valid PDF bytes with WeasyPrint.
- [x] Test PDF signature, non-empty content, and failure handling.

### Task 6: Frontend Report Experience

**Files:**
- Modify: `frontend/components/PublicationWorkspace.tsx`
- Modify: `frontend/components/MarkdownPreview.tsx`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/globals.css`

- [x] Add trust and provenance masthead information.
- [x] Add one-click Markdown and PDF download actions.
- [x] Restyle rendered Markdown as a refined editorial dossier.
- [x] Add responsive tables, evidence chips, print-safe spacing, and accessible button states.

### Task 7: Verification

**Files:**
- Update: `findings.md`
- Update: `progress.md`
- Update: `task_plan.md`

- [x] Run backend unit tests.
- [x] Run Python compilation.
- [x] Run frontend production build.
- [x] Start backend/frontend and verify report pages in the browser.
- [x] Run a real Douyin job and verify logs/results show the Doubao model and video source mode.
- [x] Download and inspect Markdown and PDF artifacts.

