#!/usr/bin/env python3
"""Anti-fabrication check for generated CVs and cover letters.

Compares a document (.md, .txt, .html or .docx) against the verified profile and reports:
  * unverified_terms  - tools/technologies/credentials from config/tech_terms.txt that appear in
                        the document but nowhere in the verified profile;
  * unverified_metrics - percentages or numbers-with-% not present in the profile's highlights;
  * years_claims       - "N years"/"N+ years" claims above profile.max_years_claim;
  * unknown_employers  - lines formatted like 'Title | Employer' whose employer isn't in the profile.

Exit code 0 = clean, 1 = issues found (do NOT present the document for approval until fixed).
Output never echoes document text beyond the offending term.
"""
from __future__ import annotations

import argparse
import json
import re
import html
import shutil
import subprocess
import zipfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SKILL_DIR, load_profile, norm  # noqa: E402
from score import canon, profile_skill_set  # noqa: E402

TERMS_PATH = SKILL_DIR / "config" / "tech_terms.txt"


def load_terms() -> list[str]:
    out = []
    for line in TERMS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            out.append(line)
    return out


def read_doc(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        if shutil.which("textutil"):
            res = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(path)],
                                 capture_output=True, text=True, check=True)
            return res.stdout
        # Cross-platform fallback: read the paragraphs straight out of the DOCX zip.
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:tab/>", "\t", xml)
        return html.unescape(re.sub(r"<[^>]+>", "", xml))
    text = path.read_text(encoding="utf-8")
    if suffix in (".html", ".htm"):
        text = re.sub(r"<[^>]+>", " ", text)
    return text


def term_present(term: str, text: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def check(doc_text: str, profile: dict, terms: list[str] | None = None) -> dict:
    terms = terms or load_terms()
    doc = doc_text.lower()
    # 'flags'/'notes' describe gaps and caveats - they are NOT evidence, so exclude them.
    evidence = {k: v for k, v in profile.items() if k not in ("flags", "notes")}
    corpus = json.dumps(evidence, ensure_ascii=False).lower()
    corpus_norm = norm(corpus)
    skills = profile_skill_set(profile)

    unverified_terms = []
    for t in terms:
        if term_present(t, doc):
            if term_present(t, corpus) or canon(t) in skills or term_present(canon(t), corpus_norm):
                continue
            unverified_terms.append(t)

    profile_metrics = set(re.findall(r"\d+(?:\.\d+)?\s?%", corpus))
    profile_metrics = {m.replace(" ", "") for m in profile_metrics}
    unverified_metrics = sorted({m.replace(" ", "") for m in re.findall(r"\d+(?:\.\d+)?\s?%", doc)}
                                - profile_metrics)

    max_years = profile.get("max_years_claim")
    years_claims = []
    for m in re.finditer(r"(\d+)\s*\+?\s*(?:years|yrs)", doc):
        n = int(m.group(1))
        if max_years is not None and n > max_years:
            years_claims.append(f"{m.group(0).strip()} (max verified: {max_years})")

    employers = {norm(e["employer"]) for e in profile.get("experience", [])}
    unknown_employers = []
    for line in doc_text.splitlines():
        if "|" in line and not line.strip().startswith(("-", "*")):
            parts = [norm(p) for p in line.split("|")]
            if len(parts) >= 2 and parts[1] and len(parts[1].split()) <= 6:
                emp = parts[1]
                if not any(emp in e or e in emp for e in employers) and not any(
                        emp in norm(ed["institution"]) for ed in profile.get("education", [])):
                    # header/contact lines contain '@' or digits-heavy phone numbers - ignore those
                    if "@" not in line and not re.search(r"\d{6,}", line.replace(" ", "")):
                        unknown_employers.append(parts[1])

    issues = {k: v for k, v in {
        "unverified_terms": unverified_terms,
        "unverified_metrics": unverified_metrics,
        "years_claims": years_claims,
        "unknown_employers": unknown_employers,
    }.items() if v}
    return {"clean": not issues, "issues": issues}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("documents", nargs="+")
    a = ap.parse_args()
    profile = load_profile()
    terms = load_terms()
    all_clean = True
    for d in a.documents:
        res = check(read_doc(Path(d).expanduser()), profile, terms)
        all_clean &= res["clean"]
        print(json.dumps({"document": Path(d).name, **res}, indent=2))
    sys.exit(0 if all_clean else 1)


if __name__ == "__main__":
    main()
