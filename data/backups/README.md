# Backup Directory

This directory contains automatic backups of `scripts.json`.

## Backup Policy

- **Frequency**: Backups are created at most once every 5 minutes when changes are saved
- **Retention**: Only the last 10 backups are kept
- **Format**: `scripts_YYYYMMDD_HHMMSS.json`

## Git Ignore

All `.json` files in this directory are gitignored to keep the repository clean.
Only this README is tracked by git.

## Manual Cleanup

To manually clean up old backups, you can delete files older than a certain date:

```bash
# Keep only the 5 most recent backups (PowerShell)
Get-ChildItem "data\backups\scripts_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -Skip 5 | Remove-Item -Force

# Keep only the 5 most recent backups (Bash)
ls -t data/backups/scripts_*.json | tail -n +6 | xargs rm -f
```

## Restoring from Backup

Backups can be restored via the web interface or manually:

```bash
# Manual restore (replace scripts.json with a backup)
cp data/backups/scripts_YYYYMMDD_HHMMSS.json data/scripts.json
```
