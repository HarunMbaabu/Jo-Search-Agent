# Configuration

[← Back to README](../README.md)

- [CV location](#cv-location)
- [Search settings](#search-settings)
- [If you are not based in Kenya](#if-you-are-not-based-in-kenya)
- [Where your data is stored](#where-your-data-is-stored)
- [Scheduled searches](#scheduled-searches)

All settings live in **`config/search_config.json`** inside the skill folder.

---

## CV location

You can give the skill your CV in any of three ways:

| Way | How |
|---|---|
| **Default folder** | Put the PDF in `Desktop/cvs` and run `/job_agents setup` |
| **Direct path** | `/job_agents setup ~/Documents/My_CV.pdf`. Put paths that contain spaces in quotes. |
| **Your own default folder** | Set `"cv_directory": "~/Documents/CVs"` in the config |

Notes:

- **Getting the path:** drag the file into the terminal window. On Windows you can also
  *Shift + right-click* the file and choose **Copy as path**.
- **Windows paths:** use forward slashes, for example `C:/Users/jane/Documents/CVs`.
- **Windows with OneDrive:** your Desktop may really be `C:\Users\<you>\OneDrive\Desktop`.
  Use `"cv_directory": "~/OneDrive/Desktop/cvs"`.
- **Which files are found:** only PDFs directly inside the folder. Subfolders aren't searched.

---

## Search settings

| Setting | What it controls | Default |
|---|---|---|
| `cv_directory` | Folder that holds your CV | `~/Desktop/cvs` |
| `timezone` | Your [time zone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) | `Africa/Nairobi` |
| `candidate_context` | Your citizenship, where you live, and whether you need visa sponsorship | Kenya, Kenya, yes |
| `role_families` | Job titles to search for. Add or remove titles freely. | 6 data role families |
| `seniority_filter` | Seniority levels to include | mid, senior, lead |
| `location_tiers` | Which locations count as eligible, and how they're scored | Kenya → remote-OK → sponsored |
| `ranking_weights` | How much each factor counts. The weights must add up to 1.0. | skills 35%, experience 25%, projects 15%, education 10%, preferred 10%, location 5% |
| `thresholds.shortlist_min_score` | Minimum score to shortlist a job | 60 |
| `thresholds.max_jobs_per_search` | Most new jobs per search | 25 |
| `excluded_keywords` | Postings containing these words are skipped | scam and fee phrases |

`config/tech_terms.txt` lists the tools and technologies the fact-checker knows about. Add any
from your field that are missing.

---

## If you are not based in Kenya

Update these four places:

1. **`config/search_config.json`:** `candidate_context`, `timezone`, and the labels in `location_tiers`.
2. **`SKILL.md`:** the `description` line, the "Candidate context" line, and the example search
   queries that mention Nairobi.
3. **`references/search_sources.md`:** the local job boards and scam warning signs.
4. **`references/document_guidelines.md`:** the example address line.

---

## Where your data is stored

Your CV text, profile, job tracker and generated documents are kept **on your computer only**,
in a private folder outside the skill:

| OS | Folder |
|---|---|
| macOS / Linux | `~/.job_agents/` (only your user account can read it) |
| Windows | `C:\Users\<you>\.job_agents\` |

What's inside:

| Item | Contents |
|---|---|
| `profile.json` | Verified facts from your CV |
| `tracker.db` | Every job, score and application |
| `applications/` | Your tailored CVs and cover letters |
| `logs/` | Logs from scheduled searches |

To use a different folder, set the `JOB_AGENTS_HOME` environment variable:

```bash
echo 'export JOB_AGENTS_HOME="$HOME/Documents/job_agents_data"' >> ~/.zshrc     # macOS
echo 'export JOB_AGENTS_HOME="$HOME/Documents/job_agents_data"' >> ~/.bashrc    # Linux
```
```powershell
setx JOB_AGENTS_HOME "$env:USERPROFILE\Documents\job_agents_data"             # Windows
```

If several people share one computer, each person should use their own user account. Their data
then stays separate.

---

## Scheduled searches

This is optional and off by default. Scheduled runs only **search and rank** jobs. They never
write documents or submit applications. Your computer must be on at the scheduled times. The
default times are 08:00, 11:00, 14:00, 17:00 and 20:00.

### macOS

```
/job_agents schedule preview     # shows the schedule; changes nothing
/job_agents schedule enable      # asks for your approval, then turns it on
/job_agents schedule disable     # turns it off
```

### Linux (cron)

Install zsh (`sudo apt install zsh`), run `crontab -e`, and add this line:

```cron
0 8,11,14,17,20 * * * PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin" zsh "$HOME/.claude/skills/job_agents/scripts/scheduled_search.sh"
```

The times use your computer's clock. To stop, remove the line with `crontab -e`.

### Windows (Task Scheduler)

1. Create a file named `C:\Users\<you>\.job_agents\scheduled_search.cmd` containing:
   ```bat
   @echo off
   if not exist "%USERPROFILE%\.job_agents\logs" mkdir "%USERPROFILE%\.job_agents\logs"
   cd /d "%USERPROFILE%\.claude\skills\job_agents"
   claude -p "/job_agents search --scheduled" --allowedTools "WebSearch" "WebFetch" "Read" "Write" "Bash(python3 *)" >> "%USERPROFILE%\.job_agents\logs\scheduled.log" 2>&1
   ```
2. In PowerShell, create the five daily tasks:
   ```powershell
   foreach ($t in '08:00','11:00','14:00','17:00','20:00') {
     schtasks /Create /F /SC DAILY /ST $t /TN "job_agents_search_$($t -replace ':','')" `
       /TR "`"$env:USERPROFILE\.job_agents\scheduled_search.cmd`""
   }
   ```
3. To stop, delete the tasks:
   ```powershell
   foreach ($t in '0800','1100','1400','1700','2000') { schtasks /Delete /F /TN "job_agents_search_$t" }
   ```

**If it doesn't run:** on macOS, run `python3 scripts/schedule.py status`. On Windows, check
*Last Run Result* in Task Scheduler. On any system, look in the `logs/` folder.
