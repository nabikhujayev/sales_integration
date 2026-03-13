# CI/CD Design — sales_integration

**Date:** 2026-02-17
**Status:** Approved

---

## Overview

Add a CI/CD pipeline to the `sales_integration` project using GitHub Actions, Docker, and Docker Compose. CI runs automatically on every push and PR. CD is triggered manually and builds a Docker image on the Linux server where the integration runs. The existing systemd service is replaced with a systemd timer + service pair that runs `docker compose up` on a daily schedule.

---

## Goals

- Run lint and tests automatically on every push/PR to `main`
- Allow manual Docker image builds and deployment via GitHub Actions
- Replace venv-based systemd service with a Docker Compose-based setup
- Schedule daily execution at 02:00 AM via systemd timer
- Keep `.env` files off the repo and off the Docker image — mount them as read-only volumes at runtime

---

## Files to Create

```
sales_integration/
├── .github/
│   └── workflows/
│       ├── ci.yml            ← lint + tests on push/PR
│       └── cd.yml            ← manual: docker compose build + systemd reload
├── Dockerfile                ← image definition
├── docker-compose.yml        ← service + volume mounts
└── .dockerignore             ← excludes secrets, venv, logs, backups
```

---

## CI Workflow (`ci.yml`)

**Trigger:** `push` and `pull_request` to `main`
**Runner:** GitHub-hosted `ubuntu-latest`

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install dependencies from `requirements.txt` + install `ruff`
4. Write a test `.env` file from the GitHub Secret `CI_ENV_CONTENT`
5. Run `ruff check .` for linting
6. Run `pytest` for tests

**GitHub Secret required:**
- `CI_ENV_CONTENT` — contents of a minimal `.env` file with dummy/safe values so `pydantic-settings` can load without real credentials

---

## CD Workflow (`cd.yml`)

**Trigger:** `workflow_dispatch` (manual button in GitHub UI)
**Runner:** Self-hosted Linux runner (tagged `self-hosted`)

**Steps:**
1. Checkout latest `main`
2. Run `docker compose build`
3. Run `systemctl restart sales-integration.timer`

No Docker registry is used. The image is built and stored locally on the Linux server only.

---

## Dockerfile

- Base image: `python:3.11-slim`
- Copy `requirements.txt`, install dependencies
- Copy source code
- `WORKDIR /app`
- `CMD ["python", "manager.py"]`

---

## .dockerignore

Excludes the following from the image:
- `venv/`
- `.env*`
- `backups/`
- `logs/`
- `__pycache__/`
- `tests/`
- `.git/`
- `docs/`

---

## docker-compose.yml

```yaml
services:
  sales_integration:
    build: .
    volumes:
      - /root/sales_integration/envs/.env.sayonar:/app/.env.sayonar:ro
      - /root/sales_integration/envs/.env.borjomi:/app/.env.borjomi:ro
      - /root/sales_integration/envs/.env.royalstar:/app/.env.royalstar:ro
    restart: "no"
```

The `.env` files live in `/root/sales_integration/envs/` on the Linux server and are never committed to the repo or copied into the image.

---

## Systemd Setup (one-time manual update on server)

Two unit files replace the existing venv-based service:

**`/etc/systemd/system/sales-integration.service`**
```ini
[Unit]
Description=Sales Integration

[Service]
Type=oneshot
WorkingDirectory=/root/sales_integration
ExecStart=docker compose up
```

**`/etc/systemd/system/sales-integration.timer`**
```ini
[Unit]
Description=Sales Integration Daily Timer

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable with:
```bash
systemctl daemon-reload
systemctl enable --now sales-integration.timer
```

---

## One-Time Prerequisites

1. Create a GitHub repository and push local code to `main`
2. Add GitHub Secret `CI_ENV_CONTENT` with dummy `.env` values
3. Install and register GitHub Actions self-hosted runner on the Linux server
4. Create `/root/sales_integration/envs/` on the server and place real `.env` files there
5. Update the systemd unit files on the server as described above

---

## Out of Scope

- Docker registry / image publishing
- Reusable workflows in a separate repo
- Healthchecks.io / monitoring (future consideration)
- Pre-commit hooks (future consideration)
- Telegram notifications (future consideration)
