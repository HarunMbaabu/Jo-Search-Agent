#!/usr/bin/env python3
"""Persistent SQLite application tracker for the job_agents skill.

DB: $JOB_AGENTS_HOME/tracker.db (default ~/.job_agents/tracker.db, mode 0600).
Stores job metadata, scores, document *paths* and status history only - never CV text,
national ID numbers, passwords or credentials.

Status lifecycle (enforced):
  discovered -> shortlisted | skipped | closed
  shortlisted -> drafted | skipped | closed
  drafted -> ready_for_review | skipped | closed
  ready_for_review -> approved | drafted | skipped | closed
  approved -> submitted | ready_for_review | withdrawn | closed
  submitted -> interviewing | rejected | offer | withdrawn | closed
  interviewing -> offer | rejected | withdrawn | closed
  (skipped/closed may be reopened to shortlisted)

Safety gates:
  * duplicates are detected by canonical URL and by company+title+location key;
  * 'approve' needs: ready_for_review, verified link, claim-checked documents, and the user's
    own approval statement for THIS job;
  * 'submitted' can only follow 'approved', and a job can be submitted once only.

Usage examples
  tracker.py init
  echo '{"title":..,"company":..,"apply_url":..}' | tracker.py add -
  tracker.py check --url URL --company C --title T --location L
  tracker.py list [--status shortlisted] [--min-score 60]
  tracker.py show ID
  tracker.py set-score ID score.json
  tracker.py verify-link ID --ok|--failed --note "..."
  tracker.py set-status ID STATUS --note "..."
  tracker.py attach-docs ID --cv PATH --cover PATH --claims-verified
  tracker.py approve ID --user-statement "Yes, submit application 12"
  tracker.py mark-submitted ID --note "confirmation #"
  tracker.py log-search --mode manual --queries "..." --found N --new N
  tracker.py stats | export-csv PATH
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm, private_path  # noqa: E402

STATUSES = ["discovered", "shortlisted", "skipped", "drafted", "ready_for_review", "approved",
            "submitted", "interviewing", "offer", "rejected", "withdrawn", "closed"]
TRANSITIONS = {
    "discovered": {"shortlisted", "skipped", "closed"},
    "shortlisted": {"drafted", "skipped", "closed"},
    "drafted": {"ready_for_review", "skipped", "closed"},
    "ready_for_review": {"approved", "drafted", "skipped", "closed"},
    "approved": {"submitted", "ready_for_review", "withdrawn", "closed"},
    "submitted": {"interviewing", "rejected", "offer", "withdrawn", "closed"},
    "interviewing": {"offer", "rejected", "withdrawn", "closed"},
    "offer": {"withdrawn", "closed"},
    "rejected": {"closed"},
    "withdrawn": {"closed"},
    "skipped": {"shortlisted", "closed"},
    "closed": {"shortlisted"},
}
TRACKING_PARAMS = {"ref", "source", "src", "gh_src", "trk", "trackingid", "refid", "lipi", "fbclid",
                   "gclid", "mc_cid", "mc_eid", "from", "utm"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dedupe_key TEXT NOT NULL UNIQUE,
  canonical_url TEXT UNIQUE,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  location TEXT,
  location_tier TEXT,
  role_family TEXT,
  source TEXT,
  apply_url TEXT,
  posted_date TEXT,
  deadline TEXT,
  salary TEXT,
  eligibility_notes TEXT,
  link_verified INTEGER NOT NULL DEFAULT 0,
  link_verified_at TEXT,
  score REAL,
  band TEXT,
  score_json TEXT,
  status TEXT NOT NULL DEFAULT 'discovered',
  discovered_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  notes TEXT
);
CREATE TABLE IF NOT EXISTS applications (
  job_id INTEGER PRIMARY KEY REFERENCES jobs(id),
  cv_path TEXT,
  cover_letter_path TEXT,
  claims_verified INTEGER NOT NULL DEFAULT 0,
  approved_at TEXT,
  approval_statement TEXT,
  submitted_at TEXT,
  submission_note TEXT
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER REFERENCES jobs(id),
  at TEXT NOT NULL,
  from_status TEXT,
  to_status TEXT,
  note TEXT
);
CREATE TABLE IF NOT EXISTS searches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  mode TEXT NOT NULL,
  queries TEXT,
  found INTEGER,
  new INTEGER
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db_path() -> Path:
    return private_path("tracker.db")


def connect() -> sqlite3.Connection:
    p = db_path()
    new = not p.exists()
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    if new:
        os.chmod(p, 0o600)
    return con


def canonical_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS]
    path = parts.path.rstrip("/") or "/"
    host = parts.netloc.lower().removeprefix("www.")
    return urlunsplit(("https", host, path, urlencode(sorted(query)), ""))


def dedupe_key(company: str, title: str, location: str | None) -> str:
    return f"{norm(company)}|{norm(title)}|{norm(location)}"


def find_duplicates(con, url=None, company=None, title=None, location=None, loose=True) -> list[sqlite3.Row]:
    """Strict: same canonical URL or same company+title+location. Loose adds same company+title anywhere."""
    rows = []
    cu = canonical_url(url)
    if cu:
        rows += con.execute("SELECT * FROM jobs WHERE canonical_url = ?", (cu,)).fetchall()
    if company and title:
        rows += con.execute("SELECT * FROM jobs WHERE dedupe_key = ?",
                            (dedupe_key(company, title, location),)).fetchall()
    if company and title and loose:
        # same company + title anywhere (e.g. reposted with a different location string)
        rows += con.execute("SELECT * FROM jobs WHERE dedupe_key LIKE ?",
                            (f"{norm(company)}|{norm(title)}|%",)).fetchall()
    seen, out = set(), []
    for r in rows:
        if r["id"] not in seen:
            seen.add(r["id"])
            out.append(r)
    return out


def log_event(con, job_id, frm, to, note=None):
    con.execute("INSERT INTO events(job_id, at, from_status, to_status, note) VALUES (?,?,?,?,?)",
                (job_id, now(), frm, to, note))


def get_job(con, job_id: int) -> sqlite3.Row:
    row = con.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise SystemExit(f"job {job_id} not found")
    return row


def transition(con, job_id: int, to: str, note: str | None = None) -> None:
    if to not in STATUSES:
        raise SystemExit(f"unknown status {to!r}; choose from {STATUSES}")
    job = get_job(con, job_id)
    frm = job["status"]
    if to == frm:
        return
    if to not in TRANSITIONS[frm]:
        raise SystemExit(f"illegal transition {frm} -> {to} for job {job_id}")
    if to in ("approved", "submitted"):
        raise SystemExit(f"use the '{'approve' if to == 'approved' else 'mark-submitted'}' command for {to}")
    con.execute("UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?", (to, now(), job_id))
    log_event(con, job_id, frm, to, note)


def add_job(con, job: dict) -> tuple[int, bool, list[int]]:
    for f in ("title", "company"):
        if not job.get(f):
            raise SystemExit(f"job is missing required field '{f}'")
    dups = find_duplicates(con, job.get("apply_url") or job.get("url"), job["company"], job["title"],
                           job.get("location"), loose=False)
    if dups:
        return dups[0]["id"], False, [d["id"] for d in dups]
    ts = now()
    cur = con.execute(
        """INSERT INTO jobs(dedupe_key, canonical_url, title, company, location, location_tier, role_family,
           source, apply_url, posted_date, deadline, salary, eligibility_notes, discovered_at, updated_at, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (dedupe_key(job["company"], job["title"], job.get("location")),
         canonical_url(job.get("apply_url") or job.get("url")), job["title"], job["company"],
         job.get("location"), job.get("location_tier"), job.get("role_family"), job.get("source"),
         job.get("apply_url") or job.get("url"), job.get("posted_date"), job.get("deadline"),
         job.get("salary"), job.get("eligibility_notes"), ts, ts, job.get("notes")))
    log_event(con, cur.lastrowid, None, "discovered", job.get("source"))
    return cur.lastrowid, True, []


def row_dict(r) -> dict:
    return {k: r[k] for k in r.keys()}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("add"); p.add_argument("job_json", help="file or - for stdin (object or list)")
    p = sub.add_parser("check")
    p.add_argument("--url"); p.add_argument("--company"); p.add_argument("--title"); p.add_argument("--location")
    p = sub.add_parser("list"); p.add_argument("--status"); p.add_argument("--min-score", type=float)
    p.add_argument("--limit", type=int, default=50)
    p = sub.add_parser("show"); p.add_argument("id", type=int)
    p = sub.add_parser("set-score"); p.add_argument("id", type=int); p.add_argument("score_json")
    p = sub.add_parser("verify-link"); p.add_argument("id", type=int)
    g = p.add_mutually_exclusive_group(required=True); g.add_argument("--ok", action="store_true")
    g.add_argument("--failed", action="store_true"); p.add_argument("--note")
    p = sub.add_parser("set-status"); p.add_argument("id", type=int); p.add_argument("status")
    p.add_argument("--note")
    p = sub.add_parser("attach-docs"); p.add_argument("id", type=int); p.add_argument("--cv")
    p.add_argument("--cover"); p.add_argument("--claims-verified", action="store_true")
    p = sub.add_parser("approve"); p.add_argument("id", type=int)
    p.add_argument("--user-statement", required=True, help="the user's own words approving THIS application")
    p = sub.add_parser("mark-submitted"); p.add_argument("id", type=int); p.add_argument("--note")
    p = sub.add_parser("log-search"); p.add_argument("--mode", choices=["manual", "scheduled"], required=True)
    p.add_argument("--queries"); p.add_argument("--found", type=int, default=0); p.add_argument("--new", type=int, default=0)
    sub.add_parser("stats")
    p = sub.add_parser("export-csv"); p.add_argument("path")
    a = ap.parse_args(argv)

    con = connect()
    with con:
        if a.cmd == "init":
            print(f"tracker ready: {db_path()}")
        elif a.cmd == "add":
            raw = sys.stdin.read() if a.job_json == "-" else Path(a.job_json).read_text(encoding="utf-8")
            data = json.loads(raw)
            results = []
            for job in (data if isinstance(data, list) else [data]):
                jid, created, dups = add_job(con, job)
                results.append({"id": jid, "created": created, "duplicate_of": dups or None,
                                "title": job["title"], "company": job["company"]})
            print(json.dumps(results, indent=2))
        elif a.cmd == "check":
            dups = find_duplicates(con, a.url, a.company, a.title, a.location)
            applied = [d for d in dups if d["status"] in ("approved", "submitted", "interviewing", "offer", "rejected")]
            strict = {d["id"] for d in find_duplicates(con, a.url, a.company, a.title, a.location, loose=False)}
            print(json.dumps({"duplicate": bool(strict), "similar": bool(dups), "already_applied_or_approved": bool(applied),
                              "matches": [{"id": d["id"], "title": d["title"], "company": d["company"],
                                           "status": d["status"], "exact": d["id"] in strict} for d in dups]}, indent=2))
        elif a.cmd == "list":
            q, params = "SELECT id, score, band, status, title, company, location, location_tier, link_verified FROM jobs WHERE 1=1", []
            if a.status:
                q += " AND status = ?"; params.append(a.status)
            if a.min_score is not None:
                q += " AND score >= ?"; params.append(a.min_score)
            q += " ORDER BY score IS NULL, score DESC, id DESC LIMIT ?"; params.append(a.limit)
            rows = con.execute(q, params).fetchall()
            print(json.dumps([row_dict(r) for r in rows], indent=2))
        elif a.cmd == "show":
            job = row_dict(get_job(con, a.id))
            app = con.execute("SELECT * FROM applications WHERE job_id = ?", (a.id,)).fetchone()
            ev = con.execute("SELECT at, from_status, to_status, note FROM events WHERE job_id = ? ORDER BY id", (a.id,)).fetchall()
            print(json.dumps({"job": job, "application": row_dict(app) if app else None,
                              "history": [row_dict(e) for e in ev]}, indent=2))
        elif a.cmd == "set-score":
            raw = sys.stdin.read() if a.score_json == "-" else Path(a.score_json).read_text(encoding="utf-8")
            s = json.loads(raw)
            get_job(con, a.id)
            con.execute("UPDATE jobs SET score = ?, band = ?, score_json = ?, updated_at = ? WHERE id = ?",
                        (s["score"], s.get("band"), json.dumps(s), now(), a.id))
            print(f"job {a.id} score={s['score']} band={s.get('band')}")
        elif a.cmd == "verify-link":
            get_job(con, a.id)
            con.execute("UPDATE jobs SET link_verified = ?, link_verified_at = ?, updated_at = ? WHERE id = ?",
                        (1 if a.ok else 0, now(), now(), a.id))
            log_event(con, a.id, None, None, f"link {'verified' if a.ok else 'FAILED'}: {a.note or ''}")
            print(f"job {a.id} link_verified={1 if a.ok else 0}")
        elif a.cmd == "set-status":
            transition(con, a.id, a.status, a.note)
            print(f"job {a.id} -> {a.status}")
        elif a.cmd == "attach-docs":
            get_job(con, a.id)
            for pth in (a.cv, a.cover):
                if pth and not Path(pth).expanduser().exists():
                    raise SystemExit(f"document not found: {pth}")
            con.execute("INSERT OR IGNORE INTO applications(job_id) VALUES (?)", (a.id,))
            if a.cv:
                con.execute("UPDATE applications SET cv_path = ? WHERE job_id = ?", (a.cv, a.id))
            if a.cover:
                con.execute("UPDATE applications SET cover_letter_path = ? WHERE job_id = ?", (a.cover, a.id))
            if a.claims_verified:
                con.execute("UPDATE applications SET claims_verified = 1 WHERE job_id = ?", (a.id,))
            print(f"job {a.id} documents attached (claims_verified={int(a.claims_verified)})")
        elif a.cmd == "approve":
            job = get_job(con, a.id)
            app = con.execute("SELECT * FROM applications WHERE job_id = ?", (a.id,)).fetchone()
            problems = []
            if job["status"] != "ready_for_review":
                problems.append(f"status is {job['status']}, must be ready_for_review")
            if not job["link_verified"]:
                problems.append("application link not verified")
            if not app or not app["claims_verified"]:
                problems.append("documents not claim-verified (run verify_claims.py, then attach-docs --claims-verified)")
            if not a.user_statement.strip():
                problems.append("empty user approval statement")
            active = ("approved", "submitted", "interviewing", "offer", "rejected")
            for loose in (False, True):
                others = [d for d in find_duplicates(con, job["apply_url"], job["company"], job["title"],
                                                     job["location"], loose=loose)
                          if d["id"] != a.id and d["status"] in active]
                if others and not loose:
                    problems.append(f"already applied/approved for this role as job {[o['id'] for o in others]}")
                    break
                if others and loose:
                    print(f"WARNING: same company+title already applied as job {[o['id'] for o in others]} "
                          "(different location) - confirm with the user this is a distinct vacancy.", file=sys.stderr)
            if problems:
                raise SystemExit("cannot approve:\n- " + "\n- ".join(problems))
            con.execute("UPDATE applications SET approved_at = ?, approval_statement = ? WHERE job_id = ?",
                        (now(), a.user_statement.strip(), a.id))
            con.execute("UPDATE jobs SET status = 'approved', updated_at = ? WHERE id = ?", (now(), a.id))
            log_event(con, a.id, "ready_for_review", "approved", "user approval recorded")
            print(f"job {a.id} approved by user")
        elif a.cmd == "mark-submitted":
            job = get_job(con, a.id)
            app = con.execute("SELECT * FROM applications WHERE job_id = ?", (a.id,)).fetchone()
            if job["status"] != "approved" or not app or not app["approved_at"]:
                raise SystemExit(f"job {a.id} is not approved (status={job['status']}); refusing to mark submitted")
            if app["submitted_at"]:
                raise SystemExit(f"job {a.id} was already submitted at {app['submitted_at']}")
            con.execute("UPDATE applications SET submitted_at = ?, submission_note = ? WHERE job_id = ?",
                        (now(), a.note, a.id))
            con.execute("UPDATE jobs SET status = 'submitted', updated_at = ? WHERE id = ?", (now(), a.id))
            log_event(con, a.id, "approved", "submitted", a.note)
            print(f"job {a.id} marked submitted")
        elif a.cmd == "log-search":
            con.execute("INSERT INTO searches(at, mode, queries, found, new) VALUES (?,?,?,?,?)",
                        (now(), a.mode, a.queries, a.found, a.new))
            print("search logged")
        elif a.cmd == "stats":
            by = con.execute("SELECT status, COUNT(*) n FROM jobs GROUP BY status ORDER BY n DESC").fetchall()
            last = con.execute("SELECT at, mode, found, new FROM searches ORDER BY id DESC LIMIT 1").fetchone()
            print(json.dumps({"by_status": {r["status"]: r["n"] for r in by},
                              "total": sum(r["n"] for r in by),
                              "last_search": row_dict(last) if last else None}, indent=2))
        elif a.cmd == "export-csv":
            rows = con.execute("""SELECT j.id, j.score, j.band, j.status, j.title, j.company, j.location,
                                  j.location_tier, j.apply_url, j.deadline, j.discovered_at, a.approved_at, a.submitted_at
                                  FROM jobs j LEFT JOIN applications a ON a.job_id = j.id ORDER BY j.id""").fetchall()
            with open(a.path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if rows:
                    w.writerow(rows[0].keys())
                w.writerows([tuple(r) for r in rows])
            print(f"exported {len(rows)} rows -> {a.path}")


if __name__ == "__main__":
    main()
