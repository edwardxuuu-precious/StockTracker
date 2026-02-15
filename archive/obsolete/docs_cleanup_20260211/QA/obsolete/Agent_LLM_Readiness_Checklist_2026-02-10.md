# Agent LLM Readiness Checklist (2026-02-10)

## Purpose
Ensure the Agent is truly LLM-capable before opening to real users.

## Required Environment Variables
Set these in `backend/.env`:

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=YOUR_REAL_KEY
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

AGENT_REQUIRE_LLM=true
AGENT_STARTUP_CHECK_LLM=true
AGENT_STARTUP_PROBE_LLM=true
AGENT_STARTUP_LLM_TIMEOUT_SECONDS=8.0
```

`AGENT_REQUIRE_LLM=true` means:
- No LLM = no agent generation/reporting.
- API returns `503` instead of degrading to deterministic templates.

## Startup Gate Behavior
Backend startup now validates LLM readiness:
- Config check (provider/model/key)
- Live probe check (if `AGENT_STARTUP_PROBE_LLM=true`)

If check fails, backend startup fails fast.

## Health Endpoint
### Config-only check
```bash
GET /api/v1/agent/health
```

### Live probe check
```bash
GET /api/v1/agent/health?probe=true
```

Expected:
- `200` when ready
- `503` when not ready

## CLI Readiness Check Script
From repo root:

```bash
python backend/scripts/check_agent_health.py --base-url http://localhost:8000 --probe
```

Exit codes:
- `0`: healthy
- `1`: endpoint responded but not healthy
- `2`: request/network failure

## Quick Go/No-Go
Go-live only if:
1. `python backend/scripts/check_agent_health.py --probe` exits `0`
2. `GET /api/v1/agent/health?probe=true` returns `200`
3. One full flow passes:
   - prompt -> generate strategy -> backtest -> report

## Release Gate Integration
`backend/scripts/release_gate.py` now includes `agent-health` check.

Recommended prod gate command:

```bash
python backend/scripts/release_gate.py \
  --profile prod \
  --agent-health-mode required \
  --agent-health-url http://localhost:8000 \
  --agent-health-probe
```

Notes:
- `--agent-health-mode auto` maps to: `dev=off`, `staging=optional`, `prod=required`
- If `mode=required`, missing or unhealthy Agent endpoint will fail release gate
