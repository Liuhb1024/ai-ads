# Evidence-Driven Report Optimization Plan

## Goal
Make Doubao full-video understanding the primary analysis source, strengthen all agents with auditable evidence and independent review, and deliver a professional report with one-click Markdown/PDF export.

## Product Decisions
- Input is a full share message or URL; the system extracts the first supported URL.
- Parsing starts immediately after paste.
- Complete metadata flows directly into analysis.
- Missing brand/product/industry pauses at a minimal confirmation screen.
- Primary outputs are Douyin article copy and a 60-90 second spoken script.
- Xiaohongshu copy is generated as a secondary channel adaptation.
- Insight report, Douyin output, and Xiaohongshu output use separate result views.
- Long-running work uses persisted stages instead of a single opaque synchronous request.

## Phases
- [x] Inspect the current video, agent, report, and export paths
- [x] Confirm strict quality mode and write the design specification
- [x] Write the implementation plan
- [x] Route downloaded video through Doubao and test fallback behavior
- [x] Add evidence normalization, claim provenance, audit, and scoring rubrics
- [x] Add competing editorial candidates and position-balanced judging
- [x] Build professional deterministic Markdown and PDF exports
- [x] Upgrade the report frontend
- [x] Run automated, browser, artifact, and real-model verification

## Constraints
- Workspace is not a Git repository; commit steps cannot be executed.
- Preserve the existing SQLite data through additive migrations.
- Never log or expose API keys.
- Media or model failures must retain actionable error and retry state.

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| Workspace has no `.git` directory | 1 | Save design and plan files without commit operations |
| zsh reserves `status` as a read-only variable | 1 | Renamed the polling variable to `job_status` |
| Running `next build` invalidated assets used by the active dev process | 1 | Stop dev before production build, then restart dev |
| Planning skill recommends a Git worktree, but this workspace has no `.git` directory | 1 | Continue in-place while preserving file-based plans and verification logs |
| Direct workflow rerun from repository root could not import `services` | 1 | Run the verification script from `backend/`, matching the application import path |
