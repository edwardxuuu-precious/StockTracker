# Frontend Configuration Guide

## Purpose

This guide explains how frontend API configuration works and how to debug connectivity issues quickly.

## Source of Truth

- API base URL is loaded from `VITE_API_URL`.
- Fallback is `http://localhost:8001` (development only).
- Startup scripts can override env values at runtime.

## Where Configuration Is Used

- `frontend/src/config/config.js`: validation and normalized config
- `frontend/src/services/api.js`: axios client and network diagnostics
- `frontend/scripts/preflight.cjs`: startup checks before build/dev

## Local Setup

1. Ensure backend is running.
2. Set `frontend/.env`:

```env
VITE_API_URL=http://localhost:8001
```

3. Start frontend:

```bash
npm run dev
```

## Validation and Diagnostics

- Preflight checks:

```bash
npm run preflight
```

- Build (includes preflight):

```bash
npm run build
```

- If network requests fail:
  - Check backend with `curl <VITE_API_URL>/api/v1/portfolios/`
  - Verify `VITE_API_URL` format
  - Restart frontend after `.env` changes

## Notes

- Do not hardcode backend ports in app logic.
- Keep user-facing error text clear and action-oriented.
- Use runtime-configured URL in all troubleshooting output.
