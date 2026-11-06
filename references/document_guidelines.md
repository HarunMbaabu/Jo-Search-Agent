# Tailored CV and cover letter guidelines

## Truthfulness rules (hard constraints)
- Every skill, tool, employer, title, date, metric, degree and responsibility must appear in
  `~/.job_agents/profile.json`. Rephrasing and reordering are fine; adding is not.
- Keep metrics exactly as written in the profile highlights. Do not round up, combine or re-attribute
  them to a different role.
- Years of experience: do not state more than `max_years_claim` unless the user confirms otherwise.
- Do not claim certifications, degrees, languages, clearances, citizenships or work rights not in
  the profile. For sponsorship roles, state truthfully that the candidate is Kenya-based and would
  require visa sponsorship.
- If the job needs a skill the candidate lacks, leave it out of the CV; the cover letter may say the
  candidate is keen to learn it - only if the user agrees.
- Run `scripts/verify_claims.py` on every output; fix every issue before showing the user.

## ATS format
- File: DOCX (primary) + text-based PDF; filename `Firstname_Lastname_CV_<Company>.docx`.
- Single column; no tables, columns, text boxes, headers/footers, images, icons, skill bars.
- Standard headings: SUMMARY, SKILLS, EXPERIENCE, EDUCATION (add PROJECTS / CERTIFICATIONS only if
  verified content exists).
- Contact line in body text: name, email, phone, city/country, LinkedIn, GitHub URLs written out.
- Role line: `### Title | Employer | City, Country (Mode) | Mon YYYY – Mon YYYY`.
- 1-2 pages. 3-6 bullets per recent role, strongest and most job-relevant first.
- Mirror the posting's exact keywords **only where the profile supports them** (e.g. if the ad says
  "ELT" and the profile shows ELT work, use "ELT").
- Plain bullets ("-"), standard fonts, 10.5-11pt, dates consistently formatted.

## Tailoring procedure
1. Extract from the posting: required skills, preferred skills, responsibilities, keywords, seniority.
2. Map each to profile evidence (skill list, role highlight). Unmapped items = gaps (report to user).
3. Summary (3 lines): target title + verified strengths matching the top 3 requirements.
4. Skills: reorder groups so required skills appear first; omit irrelevant ones if space-limited.
5. Experience: reorder bullets by relevance; light rewording for keywords; keep every number intact.
6. Write `cv.md` and `cover_letter.md` in the application folder, render, verify claims.

## Cover letter (250-400 words)
- Addressed to the hiring manager/team by name if the posting gives one; otherwise "Dear Hiring Team".
- P1: role applied for, where found, one-line value proposition.
- P2-3: two or three requirement → verified-evidence pairs with metrics.
- P4: location/eligibility truthfully (Nairobi-based; available for remote/onsite; requires visa
  sponsorship for relocation roles), availability, thanks.
- No clichés stacking, no flattery, no claims beyond the profile.

## Markdown template (render with scripts/render_docs.py)
```markdown
# Full Name
Email · Phone · Nairobi, Kenya · linkedin.com/in/... · github.com/...

## Summary
...

## Skills
- **Languages:** Python, SQL, Scala, R
- **Data Engineering:** ...

## Experience
### Data Engineer | Employer | Nairobi, Kenya (Onsite) | Mar 2023 – Present
- ...

## Education
### Degree | Institution | YYYY – YYYY
- GPA: x.x (only if in the profile)
```
