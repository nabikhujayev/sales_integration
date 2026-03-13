# CI/CD Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add GitHub Actions CI/CD, Docker, and Docker Compose to the sales_integration project so tests run on every push and a Docker image can be built and deployed manually to a Linux server running systemd.

**Architecture:** CI runs on GitHub-hosted runners (lint + tests on every push/PR). CD runs on a self-hosted Linux runner (manual trigger, builds Docker image locally, no registry). Systemd timer triggers `docker compose up` daily at 02:00 AM using the pre-built image.

**Tech Stack:** GitHub Actions, Docker, Docker Compose, Python 3.11, ruff, pytest, systemd

---

## Important: Import Compatibility Fix

The codebase has two import styles:
- `main.py`: `from core.config import settings` (works when CWD is project root)
- Service files: `from sales_integration.core.config import settings` (requires package in sys.path)

The Dockerfile resolves this by setting `WORKDIR /sales_integration` (matching the package name) and `ENV PYTHONPATH=/`. This makes both import styles work without changing any source files.

---

## Task 1: Create `.dockerignore`

**Files:**
- Create: `.dockerignore`

**Step 1: Create the file**

```
venv/
.env*
backups/
logs/
__pycache__/
*.pyc
.git/
.github/
docs/
tests/
*.md
```

**Step 2: Commit**

```bash
git add .dockerignore
git commit -m "chore: add .dockerignore"
```

---

## Task 2: Create `Dockerfile`

**Files:**
- Create: `Dockerfile`

**Step 1: Create the file**

```dockerfile
FROM python:3.11-slim

WORKDIR /sales_integration

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create __init__.py so 'from sales_integration.x import y' style imports work
# when PYTHONPATH=/ (service files use this style)
RUN touch __init__.py

ENV PYTHONPATH=/

CMD ["python", "manager.py"]
```

**Step 2: Verify syntax is correct**

Read the file back and confirm no typos.

**Step 3: Commit**

```bash
git add Dockerfile
git commit -m "chore: add Dockerfile"
```

---

## Task 3: Create `docker-compose.yml`

**Files:**
- Create: `docker-compose.yml`

**Step 1: Create the file**

```yaml
services:
  sales_integration:
    build: .
    image: sales_integration:latest
    volumes:
      - /root/sales_integration/envs/.env.sayonar:/sales_integration/.env.sayonar:ro
      - /root/sales_integration/envs/.env.borjomi:/sales_integration/.env.borjomi:ro
      - /root/sales_integration/envs/.env.royalstar:/sales_integration/.env.royalstar:ro
    restart: "no"
```

> **Note:** `image:` + `build:` together means `docker compose up` uses the existing named image if it exists (no rebuild). `docker compose build` explicitly rebuilds and re-tags it. This is intentional — CD builds the image, systemd just runs it.

> **Note:** Volume mounts use `/sales_integration/` as the container path (matching `WORKDIR` in the Dockerfile) so the `.env` files are found at the path `manager.py` expects.

**Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: add docker-compose.yml"
```

---

## Task 4: Create CI Workflow (`.github/workflows/ci.yml`)

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create the directories**

```bash
mkdir -p .github/workflows
```

**Step 2: Create the file**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff

      - name: Write test .env file
        run: echo "${{ secrets.CI_ENV_CONTENT }}" > .env

      - name: Lint with ruff
        run: ruff check .

      - name: Run tests
        run: pytest tests/ -v
```

**Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add CI workflow (lint + tests)"
```

---

## Task 5: Create CD Workflow (`.github/workflows/cd.yml`)

**Files:**
- Create: `.github/workflows/cd.yml`

**Step 1: Create the file**

```yaml
name: CD

on:
  workflow_dispatch:

jobs:
  deploy:
    runs-on: self-hosted

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image
        run: docker compose build

      - name: Copy docker-compose.yml to server deploy directory
        run: cp docker-compose.yml /root/sales_integration/docker-compose.yml

      - name: Reload systemd timer
        run: sudo systemctl restart sales-integration.timer
```

**Step 2: Commit and push everything to GitHub**

```bash
git add .github/workflows/cd.yml
git commit -m "ci: add CD workflow (manual Docker build + deploy)"
git push origin main
```

---

## Task 6: Create GitHub Repository and Push Code

**Step 1: Go to https://github.com/new and create a new private repository**

Name it `sales_integration`. Do not initialize with README, .gitignore, or license.

**Step 2: Add GitHub as remote origin**

```bash
git remote add origin https://github.com/YOUR_USERNAME/sales_integration.git
```

**Step 3: Push**

```bash
git push -u origin main
```

**Step 4: Verify**

Open the repository on GitHub and confirm all files are present, including `.github/workflows/`.

---

## Task 7: Add GitHub Secret for CI

**Step 1: Go to repository Settings → Secrets and variables → Actions → New repository secret**

Name: `CI_ENV_CONTENT`

Value (paste exactly, replace nothing — these are dummy values for test isolation):
```
SMARTUP_SERVER_URL=http://localhost
SMARTUP_CLIENT_ID=test_client
SMARTUP_CLIENT_SECRET=test_secret
COMPANY_ID=1
FILIAL_ID=1
TEMPLATE_ID=1
SFTP_SERVER=localhost
SFTP_PORT=22
SFTP_USERNAME=test
SFTP_PASSWORD=test
SFTP_REMOTE_PATH=/tmp
EMAIL_SENDER=test@test.com
EMAIL_PASSWORD=test
EMAIL_RECIPIENTS=test@test.com
SMTP_SERVER=localhost
SMTP_PORT=587
```

**Step 2: Verify**

Push a small change to `main` (e.g., add a blank line to README). Go to the Actions tab and confirm the CI workflow triggers and completes — lint and tests pass.

---

## Task 8: Install Self-Hosted Runner on Linux Server

> Run all commands on the Linux server as the user that will run the runner (e.g., `ubuntu` or `deploy`).

**Step 1: Go to GitHub repo → Settings → Actions → Runners → New self-hosted runner**

Select: Linux, x64. Follow the exact commands GitHub shows on that page. They look like:

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-X.X.X.tar.gz -L https://github.com/actions/runner/releases/download/...
tar xzf ./actions-runner-linux-x64-X.X.X.tar.gz
./config.sh --url https://github.com/YOUR_USERNAME/sales_integration --token YOUR_TOKEN
```

**Step 2: Install and start as a systemd service (so it survives reboots)**

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

**Step 3: Verify**

Go to GitHub → Settings → Actions → Runners. The runner should show as **Idle** (green dot).

---

## Task 9: Set Up Server Directories and Env Files

> Run on the Linux server.

**Step 1: Create the deploy directory**

```bash
sudo mkdir -p /root/sales_integration/envs
```

**Step 2: Place real `.env` files**

Copy each `.env` file to the server:

```bash
sudo cp .env.sayonar /root/sales_integration/envs/.env.sayonar
sudo cp .env.borjomi /root/sales_integration/envs/.env.borjomi
sudo cp .env.royalstar /root/sales_integration/envs/.env.royalstar
```

**Step 3: Lock down permissions**

```bash
sudo chmod 600 /root/sales_integration/envs/.env.*
```

**Step 4: Grant runner user sudo access for systemctl (this service only)**

```bash
sudo visudo -f /etc/sudoers.d/github-runner
```

Add this line (replace `runner_user` with the actual runner username):

```
runner_user ALL=(ALL) NOPASSWD: /bin/systemctl restart sales-integration.timer
```

---

## Task 10: Create Systemd Unit Files on Server

> Run on the Linux server.

**Step 1: Create the service unit**

```bash
sudo nano /etc/systemd/system/sales-integration.service
```

Paste:

```ini
[Unit]
Description=Sales Integration

[Service]
Type=oneshot
WorkingDirectory=/root/sales_integration
ExecStart=/usr/bin/docker compose up
```

**Step 2: Create the timer unit**

```bash
sudo nano /etc/systemd/system/sales-integration.timer
```

Paste:

```ini
[Unit]
Description=Sales Integration Daily Timer

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Step 3: Enable the timer**

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sales-integration.timer
```

**Step 4: Verify timer is active**

```bash
systemctl status sales-integration.timer
```

Expected: `Active: active (waiting)`

---

## Task 11: First CD Run and Verification

**Step 1: Trigger the CD workflow manually**

Go to GitHub → Actions → CD → Run workflow → Run workflow (on `main`).

**Step 2: Watch the workflow run**

Each step should succeed:
- Checkout ✓
- `docker compose build` ✓ (takes a few minutes first time)
- `cp docker-compose.yml ...` ✓
- `sudo systemctl restart sales-integration.timer` ✓

**Step 3: Verify the image exists on the server**

```bash
docker images | grep sales_integration
```

Expected: `sales_integration   latest   <id>   <time>   <size>`

**Step 4: Test a manual one-off run**

```bash
sudo systemctl start sales-integration.service
journalctl -u sales-integration.service -f
```

Verify the service starts, connects, and completes (or fails with an expected error like auth failure — not a crash).

**Step 5: Verify the timer fires correctly**

```bash
systemctl list-timers sales-integration.timer
```

Confirm the `NEXT` column shows the next 02:00:00 run time.

---

## Summary of What Was Built

| File | Purpose |
|------|---------|
| `.dockerignore` | Keeps secrets and build artifacts out of the image |
| `Dockerfile` | Builds `python:3.11-slim` image, handles import compatibility |
| `docker-compose.yml` | Defines service, volumes for env files, no-restart policy |
| `.github/workflows/ci.yml` | Lint + tests on every push/PR |
| `.github/workflows/cd.yml` | Manual Docker build + systemd reload on self-hosted runner |
| `/etc/systemd/system/sales-integration.service` | Runs `docker compose up` (one-shot) |
| `/etc/systemd/system/sales-integration.timer` | Triggers service daily at 02:00 AM |
