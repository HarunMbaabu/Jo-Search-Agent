#!/usr/bin/env python3
"""Render a tailored CV or cover letter from simple Markdown into ATS-readable files.

ATS rules applied: single column, no tables/images/text boxes/icons, standard section headings,
real text (not images), common font, bullets as plain list items, contact details in body text.

Supported Markdown subset:
  # Name            -> document title (H1)
  ## Section        -> section heading (H2)
  ### Role line     -> sub-heading (H3), e.g. "Data Engineer | Employer | Mon YYYY – Present"
  - bullet          -> list item
  **bold**          -> bold
  blank line        -> paragraph break

Usage:
  render_docs.py INPUT.md --out-dir DIR [--basename NAME] [--formats docx,pdf,txt]

Outputs are written with 0600 permissions. DOCX via macOS textutil, pandoc or LibreOffice;
PDF via headless Chrome/Edge (set CHROME_PATH to override). Missing tools are skipped with a warning. Run verify_claims.py on the output afterwards.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def _chrome_candidates() -> list[str]:
    names = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
             "chrome", "msedge", "microsoft-edge"]
    fixed = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    for env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            fixed += [os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                      os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")]
    return [os.environ.get("CHROME_PATH", "")] + fixed + [shutil.which(n) or "" for n in names]


CHROME_CANDIDATES = _chrome_candidates()


def html_to_docx(html_path: Path, out: Path) -> bool:
    """macOS textutil, else pandoc, else LibreOffice. Returns False if none is available."""
    if shutil.which("textutil"):
        subprocess.run(["textutil", "-convert", "docx", str(html_path), "-output", str(out)],
                       check=True, capture_output=True)
        return True
    if shutil.which("pandoc"):
        subprocess.run(["pandoc", str(html_path), "-f", "html", "-o", str(out)],
                       check=True, capture_output=True)
        return True
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice and os.environ.get("PROGRAMFILES"):
        cand = Path(os.environ["PROGRAMFILES"]) / "LibreOffice" / "program" / "soffice.exe"
        soffice = str(cand) if cand.exists() else None
    if soffice:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([soffice, "--headless", "--convert-to", "docx:MS Word 2007 XML",
                            "--outdir", tmp, str(html_path)], check=True, capture_output=True,
                           timeout=180)
            shutil.move(str(Path(tmp) / f"{html_path.stem}.docx"), str(out))
        return True
    return False

CSS = """
body { font-family: Calibri, Arial, Helvetica, sans-serif; font-size: 11pt; line-height: 1.3;
       color: #000; margin: 0.6in 0.7in; }
h1 { font-size: 18pt; margin: 0 0 4pt 0; }
h2 { font-size: 12pt; text-transform: uppercase; border-bottom: 1px solid #000;
     margin: 12pt 0 4pt 0; padding-bottom: 1pt; }
h3 { font-size: 11pt; margin: 8pt 0 2pt 0; }
p { margin: 0 0 6pt 0; }
ul { margin: 0 0 6pt 18pt; padding: 0; }
li { margin: 0 0 2pt 0; }
"""


def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a> (\2)', s)
    return s


def md_to_html(md: str, title: str) -> str:
    out, in_list, para = [], False, []

    def flush_para():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if re.match(r"^\s*[-*]\s+", line):
            flush_para()
            if not in_list:
                out.append("<ul>"); in_list = True
            item = re.sub(r"^\s*[-*]\s+", "", line)
            out.append(f"<li>{inline(item)}</li>")
            continue
        if in_list:
            out.append("</ul>"); in_list = False
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            flush_para()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
        elif not line.strip():
            flush_para()
        else:
            para.append(line.strip())
    flush_para()
    if in_list:
        out.append("</ul>")
    return (f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            f"<style>{CSS}</style></head><body>\n" + "\n".join(out) + "\n</body></html>")


def md_to_text(md: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", md)
    text = re.sub(r"^#{1,3}\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*]\s+", "• ", text, flags=re.M)
    return text


def chmod_private(p: Path) -> None:
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def render(md_path: Path, out_dir: Path, basename: str, formats: set[str]) -> list[Path]:
    md = md_path.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(out_dir, 0o700)
    produced: list[Path] = []
    page = md_to_html(md, basename)
    html_path = out_dir / f"{basename}.html"
    html_path.write_text(page, encoding="utf-8"); chmod_private(html_path)
    if "txt" in formats:
        t = out_dir / f"{basename}.txt"
        t.write_text(md_to_text(md), encoding="utf-8"); chmod_private(t); produced.append(t)
    if "docx" in formats:
        d = out_dir / f"{basename}.docx"
        if html_to_docx(html_path, d):
            chmod_private(d); produced.append(d)
        else:
            print("WARNING: no DOCX converter found (macOS textutil, pandoc or LibreOffice) - "
                  "DOCX skipped.", file=sys.stderr)
    if "pdf" in formats:
        chrome = next((c for c in CHROME_CANDIDATES if c and Path(c).exists()), None)
        if not chrome:
            print("WARNING: Chrome not found - PDF skipped (DOCX is ATS-safe).", file=sys.stderr)
        else:
            pdf = out_dir / f"{basename}.pdf"
            with tempfile.TemporaryDirectory() as prof:
                subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                                f"--user-data-dir={prof}", f"--print-to-pdf={pdf}", html_path.as_uri()],
                               capture_output=True, timeout=120)
            if pdf.exists() and pdf.stat().st_size > 0:
                chmod_private(pdf); produced.append(pdf)
            else:
                print("WARNING: PDF generation failed - DOCX still available.", file=sys.stderr)
    html_path.unlink()
    return produced


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_md")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--basename")
    ap.add_argument("--formats", default="docx,pdf,txt")
    a = ap.parse_args()
    src = Path(a.input_md).expanduser()
    produced = render(src, Path(a.out_dir).expanduser(), a.basename or src.stem,
                      {f.strip() for f in a.formats.split(",") if f.strip()})
    for p in produced:
        print(p)


if __name__ == "__main__":
    main()
