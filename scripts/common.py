"""Shared paths and helpers for the job_agents skill.

All private data (CV text, verified profile, tracker DB, generated documents)
lives OUTSIDE the skill source tree, in JOB_AGENTS_HOME (default ~/.job_agents),
created with owner-only permissions. Nothing personal is ever written into the
skill directory or printed to logs by these scripts.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "config" / "search_config.json"


def data_home() -> Path:
    home = Path(os.environ.get("JOB_AGENTS_HOME", Path.home() / ".job_agents")).expanduser()
    home.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(home, 0o700)
    except OSError:
        pass
    return home


def private_path(*parts: str) -> Path:
    p = data_home().joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_private(path: Path, text: str) -> None:
    """Write a file readable only by the owner (0600)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.chmod(path, 0o600)


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def profile_path() -> Path:
    return private_path("profile.json")


def load_profile() -> dict:
    p = profile_path()
    if not p.exists():
        raise SystemExit(
            f"No verified profile at {p}. Run: python3 scripts/cv_profile.py extract <cv.pdf> "
            "and then build profile.json as described in SKILL.md (Workflow step 1)."
        )
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def norm(s: str | None) -> str:
    """Lower-case, strip punctuation and collapse whitespace."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9+#.]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()
