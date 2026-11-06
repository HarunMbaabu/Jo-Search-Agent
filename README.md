# job_agents: data-role job search and application assistant

A Claude Code skill that runs only when you call it (`disable-model-invocation: true`). It finds
data jobs suited to a Kenya-based candidate, scores them against a verified CV, writes truthful
ATS-ready documents and prepares applications. **It never submits without your approval for
each application.**

## Layout
```
SKILL.md                      instructions loaded when you run /job_agents
config/search_config.json     role families, location tiers, ranking weights, thresholds, schedule
config/tech_terms.txt         vocabulary the anti-fabrication checker watches for
references/*.md               sources and scam checks, scoring rubric, document rules, browser procedure
scripts/cv_profile.py         discover / extract / validate / summary for the CV and profile
scripts/score.py              weighted ranking (35/25/15/10/10/5)
scripts/tracker.py            SQLite tracker: duplicate checks, status lifecycle, approval gate
scripts/render_docs.py        Markdown -> DOCX + text PDF + TXT (ATS-safe)
scripts/verify_claims.py      flags unverified skills, metrics, years, degrees, employers
scripts/schedule.py           optional launchd schedule (preview / install --user-approved / uninstall)
scripts/scheduled_search.sh   headless search-only run used by the schedule
tests/                        unittest suite (uses a synthetic profile)
```

## Private data (not in this folder)
Everything personal lives in `~/.job_agents/`. The folder is mode 700 and each file is 600:
`profile.json`, `cv_text.txt`, `selected_cv.json`, `tracker.db`, `inbox/`, `applications/` and
`logs/`. To keep it somewhere else, set the `JOB_AGENTS_HOME` environment variable.

## Usage
```
/job_agents                 # status + next step
/job_agents setup           # (re)select CV and rebuild the verified profile
/job_agents search          # find, verify, de-duplicate, score, shortlist
/job_agents rank            # score any unscored jobs
/job_agents tailor 12       # tailored CV and cover letter for job 12, claim-checked
/job_agents prepare 12      # fill the form in Chrome, stop before Submit, ask for approval
/job_agents status          # pipeline summary
/job_agents schedule preview|enable|disable
```

## Tests
```
python3 -m unittest discover -s ~/.claude/skills/job_agents/tests -v
```
