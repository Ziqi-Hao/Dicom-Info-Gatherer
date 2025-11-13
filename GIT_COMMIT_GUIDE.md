# Git Commit Guide

## Quick Commit

```bash
# 1. Check status
git status

# 2. Add all changes
git add -A

# 3. Commit
git commit -m "v2.0.0: Major Python rewrite with GUI and advanced features"

# 4. Push
git push origin main
```

## Configure Git (First Time)

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

## GitHub Authentication

GitHub no longer supports password authentication. Use:

1. **Personal Access Token** (recommended for quick setup)
   - Create token: https://github.com/settings/tokens
   - Use token as password when pushing

2. **SSH** (recommended for long-term use)
   - Generate SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
   - Add to GitHub: https://github.com/settings/keys
   - Change remote: `git remote set-url origin git@github.com:username/repo.git`

## Credential Caching

```bash
# Cache credentials for 1 hour
git config --global credential.helper 'cache --timeout=3600'

# Or store permanently (less secure)
git config --global credential.helper store
```
