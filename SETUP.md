# Animated terminal GitHub profile

This repository contains the profile README, terminal-style SVG artwork, a Python generator, and a daily GitHub Actions workflow.

## Generate the artwork locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/generate_profile_art.py
```

The generator fetches the public avatar and contribution calendar for `callmetechnophile`. It fails instead of fabricating data if GitHub's contribution calendar markup is unavailable.

## Automation

Open **Actions → Refresh animated profile art → Run workflow** to run it manually. It is also scheduled daily at 06:17 UTC. The workflow requires repository Actions to be enabled and contents write permission.

## Notes

- The README uses SVG animation. Some clients may display the SVGs as static images.
- GitHub's contribution calendar HTML can change; if the action fails, inspect its log and update the parser.
- The README is in `MyIntro`, which is not the special repository name required to show automatically on the account profile page. To show this README on `github.com/callmetechnophile`, the repository must be named exactly `callmetechnophile`. This commit updates MyIntro as requested but does not rename it.
