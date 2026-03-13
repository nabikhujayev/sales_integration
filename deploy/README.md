# Server Deployment

This folder contains the systemd unit files for running the integration on the Linux server.

---

## Files

| File | Purpose |
|------|---------|
| `sales-integration-saleswork.service` | Runs `docker compose up saleswork` (one-shot) |
| `sales-integration-saleswork.timer` | Triggers saleswork daily at 01:00 AM |
| `sales-integration-monolit.service` | Runs `docker compose up monolit` (one-shot) |
| `sales-integration-monolit.timer` | Triggers monolit daily at 20:00 PM |

---

## How It Works

```
timer fires at 01:00
  → starts sales-integration-saleswork.service
    → docker compose up saleswork
      → manager.py saleswork
        → runs main.py saleswork for sayonar, borjomi, royalstar
      → container exits
    → service completes (Type=oneshot)
  → timer waits until next 01:00

timer fires at 20:00
  → starts sales-integration-monolit.service
    → docker compose up monolit
      → manager.py monolit
        → runs main.py monolit for borjomi (others skipped)
      → container exits
    → service completes (Type=oneshot)
  → timer waits until next 20:00
```

**`Persistent=true`** — if the server was off at the scheduled time, the job runs immediately on next boot.

---

## Migration: Remove Old Timer (one-time)

If you previously had the single `sales-integration.timer` running at 02:00, remove it first:

```bash
sudo systemctl stop sales-integration.timer
sudo systemctl disable sales-integration.timer
sudo rm /etc/systemd/system/sales-integration.service
sudo rm /etc/systemd/system/sales-integration.timer
sudo systemctl daemon-reload
```

---

## Initial Setup (run once on the server)

```bash
# Copy unit files to systemd
cp sales-integration-saleswork.service /etc/systemd/system/
cp sales-integration-saleswork.timer /etc/systemd/system/
cp sales-integration-monolit.service /etc/systemd/system/
cp sales-integration-monolit.timer /etc/systemd/system/

# Reload systemd and enable both timers
systemctl daemon-reload
systemctl enable --now sales-integration-saleswork.timer
systemctl enable --now sales-integration-monolit.timer

# Verify timers are active
systemctl status sales-integration-saleswork.timer
systemctl status sales-integration-monolit.timer
```

Expected output: `Active: active (waiting)`

---

## Run Manually

```bash
# Saleswork
systemctl start sales-integration-saleswork.service

# Monolit
systemctl start sales-integration-monolit.service
```

Follow logs:

```bash
journalctl -u sales-integration-saleswork.service -f
journalctl -u sales-integration-monolit.service -f
```

---

## Check Next Scheduled Runs

```bash
systemctl list-timers sales-integration-*
```

---

## CD Pipeline (GitHub Actions)

When you trigger the CD workflow manually from GitHub Actions:

1. Runner checks out the latest code on the server
2. Builds a new Docker image: `docker compose build`
3. Copies `docker-compose.yml` to `/root/sales_integration/`
4. Restarts both timers

The next scheduled runs will use the newly built image automatically.
