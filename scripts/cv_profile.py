#!/usr/bin/env python3
"""Discover, extract and validate the candidate CV / verified profile.

Subcommands
  discover [DIR]          List PDF CVs in DIR (default from config), de-duplicated by hash.
  extract PDF             Extract text + hyperlinks into the private data dir (never printed
                          unless --print is given). Records the selected CV path.
  validate                Validate ~/.job_agents/profile.json against the required schema.
  summary                 Print a non-sensitive summary (counts only, no contact details).

Text extraction uses pypdf if installed, otherwise macOS PDFKit via osascript (no install needed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config, private_path, profile_path, write_private  # noqa: E402

JXA_TEXT = """
ObjC.import('PDFKit');
function run(argv){
  var d=$.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  if(!d || d.isNil()) throw new Error('cannot open PDF');
  var links=[];
  for(var i=0;i<d.pageCount;i++){
    var a=d.pageAtIndex(i).annotations;
    for(var j=0;j<a.count;j++){var u=a.objectAtIndex(j).URL;
      if(u && !u.isNil()) links.push(ObjC.unwrap(u.absoluteString));}
  }
  return JSON.stringify({text: ObjC.unwrap(d.string), links: links, pages: d.pageCount});
}
"""

REQUIRED_KEYS = {
    "source_cv": str,
    "verified_at": str,
    "name": str,
    "location": dict,
    "headline": str,
    "skills": dict,
    "experience": list,
    "education": list,
    "projects": list,
    "certifications": list,
    "links": dict,
    "flags": list,
}
SKILL_GROUPS = {"languages", "data_engineering", "cloud_and_storage", "analytics_and_bi", "ml_ai"}
EXP_KEYS = {"title", "employer", "location", "work_mode", "start", "end", "highlights", "tools"}
EDU_KEYS = {"institution", "qualification", "start", "end"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def discover(directory: Path) -> list[dict]:
    seen: dict[str, dict] = {}
    for p in sorted(directory.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True):
        digest = sha256(p)
        entry = seen.setdefault(digest, {"sha256": digest[:16], "path": str(p), "duplicates": [],
                                         "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes")})
        if entry["path"] != str(p):
            entry["duplicates"].append(str(p))
    return list(seen.values())


def extract_pdf(pdf: Path) -> dict:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(pdf))
        text = "\n".join((pg.extract_text() or "") for pg in reader.pages)
        links = []
        for pg in reader.pages:
            for annot in pg.get("/Annots") or []:
                a = annot.get_object().get("/A") or {}
                if a.get("/URI"):
                    links.append(str(a["/URI"]))
        return {"text": text, "links": links, "pages": len(reader.pages)}
    except ImportError:
        pass
    if sys.platform != "darwin":
        raise SystemExit("Install pypdf (pip install pypdf) to extract PDFs on this platform.")
    out = subprocess.run(["osascript", "-l", "JavaScript", "-e", JXA_TEXT, str(pdf)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def validate_profile(profile: dict) -> list[str]:
    errors = []
    for key, typ in REQUIRED_KEYS.items():
        if key not in profile:
            errors.append(f"missing key: {key}")
        elif not isinstance(profile[key], typ):
            errors.append(f"{key} must be {typ.__name__}")
    if isinstance(profile.get("skills"), dict):
        missing = SKILL_GROUPS - set(profile["skills"])
        if missing:
            errors.append(f"skills missing groups: {sorted(missing)}")
        for g, items in profile["skills"].items():
            if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
                errors.append(f"skills.{g} must be a list of strings")
    for i, e in enumerate(profile.get("experience") or []):
        miss = EXP_KEYS - set(e)
        if miss:
            errors.append(f"experience[{i}] missing {sorted(miss)}")
    for i, e in enumerate(profile.get("education") or []):
        miss = EDU_KEYS - set(e)
        if miss:
            errors.append(f"education[{i}] missing {sorted(miss)}")
    for forbidden in ("national_id", "id_number", "passport_number", "password", "kra_pin"):
        if forbidden in json.dumps(profile).lower():
            errors.append(f"profile must not contain '{forbidden}'")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover")
    d.add_argument("directory", nargs="?")
    e = sub.add_parser("extract")
    e.add_argument("pdf")
    e.add_argument("--print", action="store_true", help="print extracted text to stdout (for Claude to read)")
    sub.add_parser("validate")
    sub.add_parser("summary")
    a = ap.parse_args()

    if a.cmd == "discover":
        directory = Path(a.directory or load_config()["cv_directory"]).expanduser()
        if not directory.is_dir():
            raise SystemExit(f"CV directory not found: {directory}")
        found = discover(directory)
        print(json.dumps({"directory": str(directory), "unique_pdfs": len(found), "cvs": found}, indent=2))
        if len(found) > 1:
            print("\nMULTIPLE DISTINCT CVs FOUND - ask the user which one to use.", file=sys.stderr)
    elif a.cmd == "extract":
        pdf = Path(a.pdf).expanduser().resolve()
        data = extract_pdf(pdf)
        write_private(private_path("cv_text.txt"), data["text"])
        write_private(private_path("selected_cv.json"), json.dumps({
            "path": str(pdf), "sha256": sha256(pdf), "pages": data["pages"], "links": data["links"],
            "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=2))
        if a.print:
            print(data["text"])
            print("\nLINKS:\n" + "\n".join(data["links"]))
        else:
            print(f"Extracted {len(data['text'])} chars, {len(data['links'])} links, {data['pages']} page(s) "
                  f"-> {private_path('cv_text.txt')}")
    elif a.cmd == "validate":
        p = profile_path()
        if not p.exists():
            raise SystemExit(f"profile not found: {p}")
        errors = validate_profile(json.loads(p.read_text(encoding="utf-8")))
        if errors:
            print("INVALID profile:\n- " + "\n- ".join(errors))
            sys.exit(1)
        print(f"profile OK: {p}")
    elif a.cmd == "summary":
        prof = json.loads(profile_path().read_text(encoding="utf-8"))
        print(json.dumps({
            "source_cv": Path(prof["source_cv"]).name,
            "headline": prof["headline"],
            "skills": {k: len(v) for k, v in prof["skills"].items()},
            "roles": [f"{e['title']} @ {e['employer']} ({e['start']}–{e['end']})" for e in prof["experience"]],
            "education": [f"{e['qualification']}, {e['institution']}" for e in prof["education"]],
            "projects": len(prof["projects"]),
            "flags": prof["flags"],
        }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
