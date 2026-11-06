# Scoring rubric (0-100 per component)

Final score = 0.35·technical + 0.25·experience + 0.15·projects + 0.10·education
            + 0.10·preferred + 0.05·location. Computed by `scripts/score.py`; ineligible jobs capped at 40.
Bands: **strong** ≥ 75, **shortlist** ≥ 60, **low** < 60.

Judge ONLY against `~/.job_agents/profile.json`. Never credit a skill the profile lacks.

## technical_skills (35%)
Prefer the deterministic route: list the posting's *required* technical skills in
`required_skills` and let score.py compute coverage. Use canonical names (python, sql, airflow,
spark, dbt, snowflake, aws, power bi ...). If you must judge manually:
100 all required present · 75 one minor gap · 50 half · 25 few · 0 none.

## experience (25%)
Compare required years and domain with dated roles in the profile.
- Years: use `max_years_claim` (conservative) unless the user confirmed a higher figure.
- 100: meets years AND same function (e.g. data engineering for a DE role) AND relevant domain
  (use the industries of the employers listed in the profile).
- 75: meets years, adjacent function. 50: 1-2 years short or adjacent domain. 25: >2 years short.
- Senior/lead/manager titles: credit lead roles only if a profile highlight evidences leading a
  team; do not credit "Head of"/director roles requiring formal people-management years unless stated.

## projects (15%)
Use `profile.projects` first. If it is empty, credit delivered outcomes from experience highlights
that match the job, and public GitHub/blog work only if the user points to specific repos/posts and
they are added to the profile as verified projects.
100 directly analogous delivered work · 60 related · 30 tangential · 0 none.

## education (10%)
Compare with `profile.education`.
100 meets/exceeds requirement (BSc in CS/Maths/Stats/related) · 60 "Master's preferred" ·
30 "Master's/PhD required" · 0 unrelated mandatory degree.

## preferred_qualifications (10%)
Nice-to-haves: certifications, specific tools, domain, languages. Share present in the profile.
If `profile.certifications` is empty, any required certification counts as a gap.

## location_eligibility (5%)
Set `location_tier` instead of a number: kenya 100 · remote_kenya_ok 90 · relocation_sponsored 70 ·
unclear 30 · ineligible 0 (also caps total at 40).

## Example job JSON
```json
{"title": "Senior Data Engineer", "company": "Example Ltd", "location": "Nairobi",
 "location_tier": "kenya",
 "required_skills": ["python", "sql", "airflow", "spark", "aws", "terraform"],
 "components": {"experience": 80, "projects": 75, "education": 100, "preferred_qualifications": 50},
 "evidence": {"experience": "Requires 4+ yrs DE; profile shows matching dated DE roles"}}
```
