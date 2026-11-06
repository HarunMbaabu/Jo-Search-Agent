#!/usr/bin/env python3
"""Optional scheduled job searches via macOS launchd (OFF by default).

Times come from config/search_config.json -> schedule.times_local (Africa/Nairobi):
08:00, 11:00, 14:00, 17:00, 20:00. They are converted to the Mac's local timezone at install time.

  schedule.py preview                          show the plist that WOULD be installed (no changes)
  schedule.py install --user-approved          install + load the LaunchAgent (needs explicit approval)
  schedule.py uninstall                        unload + remove it
  schedule.py status                           show whether it is installed/loaded

Scheduled runs only search, score and record jobs (scripts/scheduled_search.sh). They never prepare
or submit applications.
"""
from __future__ import annotations

import argparse
import json
import plistlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SKILL_DIR, load_config, private_path, write_private  # noqa: E402

LABEL = "com.claude.job_agents.search"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def local_times(times: list[str], tz_name: str) -> list[dict]:
    src = ZoneInfo(tz_name)
    today = datetime.now(src).date()
    out = []
    for t in times:
        h, m = (int(x) for x in t.split(":"))
        local = datetime(today.year, today.month, today.day, h, m, tzinfo=src).astimezone()
        out.append({"Hour": local.hour, "Minute": local.minute})
    return out


def build_plist() -> dict:
    cfg = load_config()
    logs = private_path("logs", ".keep").parent
    return {
        "Label": LABEL,
        "ProgramArguments": ["/bin/zsh", str(SKILL_DIR / "scripts" / "scheduled_search.sh")],
        "StartCalendarInterval": local_times(cfg["schedule"]["times_local"], cfg["timezone"]),
        "StandardOutPath": str(logs / "launchd.out.log"),
        "StandardErrorPath": str(logs / "launchd.err.log"),
        "RunAtLoad": False,
        "ProcessType": "Background",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preview")
    i = sub.add_parser("install")
    i.add_argument("--user-approved", action="store_true",
                   help="required: confirms the user explicitly approved enabling scheduled searches")
    sub.add_parser("uninstall")
    sub.add_parser("status")
    a = ap.parse_args()

    if a.cmd == "preview":
        cfg = load_config()
        print(f"Nairobi times: {', '.join(cfg['schedule']['times_local'])}  (Mac local tz: "
              f"{datetime.now().astimezone().tzname()})")
        print(plistlib.dumps(build_plist()).decode())
        print(f"Would be written to: {PLIST}\nNothing has been installed.")
    elif a.cmd == "install":
        if not a.user_approved:
            raise SystemExit("Refusing: scheduling requires explicit user approval (--user-approved).")
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        PLIST.write_bytes(plistlib.dumps(build_plist()))
        subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
        subprocess.run(["launchctl", "load", str(PLIST)], check=True)
        write_private(private_path("schedule_state.json"), json.dumps(
            {"enabled": True, "approved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "plist": str(PLIST)}, indent=2))
        print(f"Installed and loaded {PLIST}")
    elif a.cmd == "uninstall":
        if PLIST.exists():
            subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
            PLIST.unlink()
        write_private(private_path("schedule_state.json"), json.dumps(
            {"enabled": False, "disabled_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=2))
        print("Scheduled searches disabled.")
    elif a.cmd == "status":
        loaded = subprocess.run(["launchctl", "list", LABEL], capture_output=True).returncode == 0
        print(json.dumps({"plist_installed": PLIST.exists(), "launchd_loaded": loaded}, indent=2))


if __name__ == "__main__":
    main()
