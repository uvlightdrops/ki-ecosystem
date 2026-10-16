# KI Ecosystem CI/CD via Polling

Automatic `git pull` on all target hosts every 5 minutes using systemd.

## One-Time Setup on Target Host

```bash
# Clone setup script and run it
cd /tmp
git clone https://github.com/uvlightdrops/ki-ecosystem.git
sudo bash ki-ecosystem/scripts/setup-polling.sh
```

Or if you already have ki-ecosystem cloned locally:

```bash
sudo bash ~/dev_flow/ki-ecosystem/scripts/setup-polling.sh
```

The setup script will:
1. Clone ki-ecosystem repo to ~/dev_flow/ki-ecosystem (if not exists)
2. Copy systemd service and timer to /etc/systemd/system/
3. Run `systemctl daemon-reload`
4. Enable and start the timer
5. Show status and next steps

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

## Updating Setup

When you change `deploy-polling.sh` or systemd files in ki-ecosystem repo:

```bash
# On target host:
cd ~/dev_flow/ki-ecosystem
git pull

# Re-copy to systemd and reload
sudo cp scripts/ki-ecosystem-polling.service /etc/systemd/system/
sudo cp scripts/ki-ecosystem-polling.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart ki-ecosystem-polling.timer
```

Or just run the setup script again:
```bash
sudo bash ~/dev_flow/ki-ecosystem/scripts/setup-polling.sh
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

Edit `/etc/systemd/system/ki-ecosystem-polling.timer` to change interval:
```
# Every 10 minutes instead:
OnUnitActiveSec=10min

# Every minute for testing:
OnUnitActiveSec=1min
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ki-ecosystem-polling.timer
```
