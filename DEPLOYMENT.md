# KI Ecosystem CI/CD via Polling

Automatic `git pull` on all target hosts every 5 minutes using systemd.

## Setup on Target Host

```bash
# Copy scripts to system directories
sudo cp /path/to/ki-ecosystem/scripts/deploy-polling.sh /opt/
sudo chmod +x /opt/deploy-polling.sh

sudo cp /path/to/ki-ecosystem/scripts/ki-ecosystem-polling.{service,timer} /etc/systemd/system/

# Enable and start the timer
sudo systemctl daemon-reload
sudo systemctl enable --now ki-ecosystem-polling.timer

# Verify it's running
sudo systemctl status ki-ecosystem-polling.timer
sudo systemctl list-timers ki-ecosystem-polling
```

## How It Works

1. **Every 5 minutes**, systemd timer runs `deploy-polling.sh`
2. **Script executes**: `stackctl pull` in ~/dev_flow/ki-ecosystem
3. **All repos pull** latest from origin (via git in each repository)
4. **Django apps auto-reload** code (if they're running)
5. **Logs** to `~/.ki-ecosystem/polling.log`

## Local Development Workflow

On your dev machine:
```bash
cd ~/dev_flow/ki-ecosystem
# ... make code changes ...
git add .
git commit -m "Your change"
git push

# stackctl push at any time to update all remotes:
stackctl push
```

Then on target hosts, within 5 minutes:
- `stackctl pull` runs automatically
- All repos update with your changes
- Django reloads code
- kicli-assist: you restart manual when needed

## Monitoring

Check polling logs on target host:
```bash
tail -f ~/.ki-ecosystem/polling.log
```

Check systemd logs:
```bash
sudo journalctl -u ki-ecosystem-polling.service -f
```

Check timer schedule:
```bash
sudo systemctl list-timers ki-ecosystem-polling
```

## Troubleshooting

If pulling fails on a target host:

```bash
# Manual pull
cd ~/dev_flow/ki-ecosystem
stackctl pull

# Check repo status
stackctl repo-status

# Check if specific repo is dirty/ahead
cd <repo>
git status
git log --oneline -n 5
```

## Disabling

```bash
sudo systemctl stop ki-ecosystem-polling.timer
sudo systemctl disable ki-ecosystem-polling.timer
```

## Customization

Edit `ki-ecosystem-polling.timer` to change interval:
```
# Every 10 minutes instead:
OnUnitActiveSec=10min

# Every minute for testing:
OnUnitActiveSec=1min
```

Then reload: `sudo systemctl daemon-reload && sudo systemctl restart ki-ecosystem-polling.timer`
