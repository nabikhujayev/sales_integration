# Server Deployment

This folder contains the systemd unit files for running the integration on the Linux server.

---

## Files

| File | Purpose |
|------|---------|
| `sales-integration.service` | Runs `docker compose up` once (one-shot job) |
| `sales-integration.timer` | Triggers the service daily at 02:00 AM |

---

## How It Works

```
timer fires at 02:00
  → starts sales-integration.service
    → docker compose up
      → container runs manager.py
        → runs main.py for sayonar
        → runs main.py for borjomi
        → runs main.py for royalstar
      → container exits
    → service completes (Type=oneshot)
  → timer waits until next 02:00
```

**`Persistent=true`** — if the server was off at 02:00, the job runs immediately on next boot.

---

## Initial Setup (run once on the server)

```bash
# Copy unit files to systemd
cp sales-integration.service /etc/systemd/system/
cp sales-integration.timer /etc/systemd/system/

# Reload systemd and enable the timer
systemctl daemon-reload
systemctl enable --now sales-integration.timer

# Verify timer is active
systemctl status sales-integration.timer
```

Expected output: `Active: active (waiting)`

---

## Run Manually

```bash
systemctl start sales-integration.service
```

Follow logs:

```bash
journalctl -u sales-integration.service -f
```

---

## Check Next Scheduled Run

```bash
systemctl list-timers sales-integration.timer
```

---

## CD Pipeline (GitHub Actions)

When you trigger the CD workflow manually from GitHub Actions:

1. Runner checks out the latest code on the server
2. Builds a new Docker image: `docker compose build`
3. Copies `docker-compose.yml` to `/root/sales_integration/`
4. Restarts the timer: `sudo systemctl restart sales-integration.timer`

The next 02:00 run will use the newly built image automatically.
