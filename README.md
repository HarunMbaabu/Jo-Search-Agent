# Jo Search Agent (`job_agents` skill for Claude Code)

A Claude Code skill that finds data jobs, ranks them against your CV, writes truthful
ATS-friendly CVs and cover letters, and prepares applications in Chrome for you to review.
**It never submits an application without your explicit approval for that specific job.**

It covers these role families: Data Analytics/BI, Data Engineering/ETL, Data Science, ML/AI,
Analytics Engineering and Python/SQL. Out of the box it is tuned for a candidate based in Kenya,
and you can change that (see [If you are not based in Kenya](#33-if-you-are-not-based-in-kenya)).

The skill only runs when you call it with `/job_agents`. Claude never triggers it on its own.

**Contents:**
[1. Requirements](#1-requirements) ·
[2. Install (macOS / Linux / Windows)](#2-install) ·
[3. Configure](#3-configure) ·
[4. Use](#4-use) ·
[5. Scheduled searches](#5-scheduled-searches-optional) ·
[6. Safety rules](#6-safety-rules-built-into-the-skill) ·
[7. Troubleshooting](#7-troubleshooting)

---

## 1. Requirements

### What works on each operating system

| Feature | macOS | Linux | Windows 10/11 |
|---|---|---|---|
| Search, rank, track jobs | ✅ | ✅ | ✅ |
| Read your CV PDF | ✅ built in | ✅ needs `pypdf` | ✅ needs `pypdf` |
| TXT output | ✅ | ✅ | ✅ |
| DOCX output | ✅ built in (`textutil`) | ✅ needs `pandoc` or LibreOffice | ✅ needs `pandoc` or LibreOffice |
| PDF output | ✅ Chrome or Edge | ✅ Chrome, Chromium or Edge | ✅ Chrome or Edge |
| Fill in applications in the browser | ✅ Claude in Chrome | ✅ Claude in Chrome | ✅ Claude in Chrome |
| Scheduled searches | ✅ built in (`launchd`) | ✅ manual `cron` setup | ✅ manual Task Scheduler setup |

### Software you need

| Software | Why | Required? |
|---|---|---|
| **Claude Code** | Runs the skill. You need a Claude subscription or an Anthropic API key. | Yes |
| **Python 3.9+** | All scripts. They use only the standard library. | Yes |
| **Git** | Downloading and updating the skill. Claude Code on Windows also needs Git for Windows. | Yes |
| **Google Chrome** (or Microsoft Edge) | PDF output, plus the Claude in Chrome extension | Recommended |
| **Claude in Chrome extension** | Lets Claude fill in application forms. Without it you get a copy-and-paste sheet. | Optional |
| **pypdf** | Reading your CV PDF | Linux/Windows: yes. macOS: optional. |
| **pandoc** *or* **LibreOffice** | Creating DOCX files | Linux/Windows: yes. macOS: no. |
| **Your CV as a PDF** | Setup | Yes. It must be a text PDF, not a scanned image. |

---

## 2. Install

The skill folder **must be named `job_agents`** and sit inside your Claude skills folder:

| OS | Skills folder |
|---|---|
| macOS / Linux | `~/.claude/skills/job_agents` |
| Windows | `%USERPROFILE%\.claude\skills\job_agents` (e.g. `C:\Users\you\.claude\skills\job_agents`) |

To install it for one project only, use `<your-project>/.claude/skills/job_agents` instead.

### 2A. macOS

```bash
# 1. Developer tools: git and python3
xcode-select --install          # or: brew install git python

# 2. Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# 3. The skill
mkdir -p ~/.claude/skills
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git ~/.claude/skills/job_agents

# 4. Optional: better PDF text extraction
python3 -m pip install --user pypdf

# 5. Check it works
python3 -m unittest discover -s ~/.claude/skills/job_agents/tests -v
```

Install [Google Chrome](https://www.google.com/chrome/) for PDF output.

### 2B. Linux (Ubuntu/Debian; use the equivalent packages on Fedora/Arch)

```bash
# 1. Base tools + DOCX converter
sudo apt update
sudo apt install -y git python3 python3-pip pandoc     # or: libreoffice-writer instead of pandoc

# 2. PDF reader for your CV
python3 -m pip install --user pypdf
#   If pip says "externally-managed-environment", use:  sudo apt install python3-pypdf

# 3. Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# 4. The skill
mkdir -p ~/.claude/skills
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git ~/.claude/skills/job_agents

# 5. Check it works
python3 -m unittest discover -s ~/.claude/skills/job_agents/tests -v
```

Install Google Chrome or Chromium for PDF output. If it's installed somewhere unusual, set
`CHROME_PATH=/path/to/chrome`.

### 2C. Windows 10/11

Run these in **PowerShell**:

```powershell
# 1. Git for Windows (Claude Code needs it), Python and pandoc
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id JohnMacFarlane.Pandoc -e        # or: winget install TheDocumentFoundation.LibreOffice

# Close and reopen PowerShell so the new PATH applies, then:

# 2. PDF reader for your CV
py -m pip install --user pypdf

# 3. Claude Code
irm https://claude.ai/install.ps1 | iex

# 4. The skill
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git "$env:USERPROFILE\.claude\skills\job_agents"

# 5. Check it works
py -m unittest discover -s "$env:USERPROFILE\.claude\skills\job_agents\tests" -v
```

**Make `python3` work.** The skill runs its scripts as `python3 ...`, through Git Bash. Open
**Git Bash** and run `python3 --version`. If you get an error, or the Microsoft Store opens:

1. Go to *Settings → Apps → Advanced app settings → App execution aliases* and switch **off**
   both `python.exe` and `python3.exe`.
2. Create a `python3` copy of Python (in PowerShell):
   ```powershell
   $py = (Get-Command python).Source
   Copy-Item $py (Join-Path (Split-Path $py) "python3.exe")
   ```
3. Open a new Git Bash window and check `python3 --version` again.

> **Alternative: WSL.** You can also run Claude Code inside WSL (Ubuntu) and follow the
> [Linux steps](#2b-linux-ubuntudebian-use-the-equivalent-packages-on-fedoraarch). In that case,
> keep your CV inside the Linux file system, or point `cv_directory` at `/mnt/c/Users/<you>/Desktop/cvs`.

### Confirm the skill is loaded (all systems)

Start Claude Code with `claude`, then type `/job_agents`. The skill should appear in the
slash-command list. If it doesn't, see [Troubleshooting](#7-troubleshooting).

### Updating

```bash
git -C ~/.claude/skills/job_agents pull                                # macOS / Linux
git -C "$env:USERPROFILE\.claude\skills\job_agents" pull               # Windows PowerShell
```

---

## 3. Configure

### 3.1 Put your CV where the skill can find it

By default the skill looks for PDF files in your **Desktop `cvs` folder**:

| OS | Default CV folder | Create it |
|---|---|---|
| macOS / Linux | `~/Desktop/cvs` | `mkdir -p ~/Desktop/cvs` |
| Windows | `C:\Users\<you>\Desktop\cvs` | `New-Item -ItemType Directory -Force "$env:USERPROFILE\Desktop\cvs"` |

Copy your CV PDF into that folder. If the folder has more than one CV, the skill asks you which
one to use. If your Desktop is somewhere else (for example, synced to OneDrive on Windows), set
`cv_directory` to the real path.

### 3.2 Edit `config/search_config.json`

| Setting | What it controls | Default |
|---|---|---|
| `cv_directory` | Folder that holds your CV PDFs. `~` works on every OS. On Windows you can also write `C:/Users/you/Desktop/cvs` (use forward slashes, or escape backslashes as `\\`). | `~/Desktop/cvs` |
| `timezone` | Your time zone, as an [IANA name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), for scheduled searches | `Africa/Nairobi` |
| `candidate_context` | Your citizenship, where you live, and whether you need visa sponsorship | Kenya, Kenya, `true` |
| `role_families` | Job titles to search for, grouped by family. Add or remove titles freely. | 6 data families |
| `seniority_filter` | Levels to include | `mid`, `senior`, `lead` |
| `location_tiers` | How eligible each location type is, and its score | Kenya, then remote-OK, then sponsored relocation |
| `ranking_weights` | Scoring weights. They must add up to 1.0. | skills .35, experience .25, projects .15, education .10, preferred .10, location .05 |
| `thresholds.shortlist_min_score` | Minimum score to shortlist a job | `60` |
| `thresholds.strong_match_score` | Score that counts as a "strong match" | `75` |
| `thresholds.max_jobs_per_search` | Cap on new jobs per search | `25` |
| `excluded_keywords` | Postings that contain these words are dropped | scam and fee phrases |
| `schedule.times_local` | Times for scheduled searches, in `timezone` | 08:00, 11:00, 14:00, 17:00, 20:00 |

`config/tech_terms.txt` lists the technologies the anti-fabrication checker watches for. Add any
tools from your field that are missing.

> **Windows users:** if `tzdata` errors appear when scheduling, run `py -m pip install --user tzdata`.

### 3.3 If you are not based in Kenya

The Kenyan focus is set in more than one place. Update all of these:

1. `config/search_config.json`: `candidate_context`, `timezone`, and the labels in `location_tiers`.
2. `SKILL.md`: the `description` line, the **Inputs → Candidate context** line, and the example
   search queries (for example, `Nairobi` and `site:careers.un.org`).
3. `references/search_sources.md`: the local job boards and scam signals.
4. `references/document_guidelines.md`: the example contact line (`Nairobi, Kenya`).

### 3.4 Where your private data lives

Your personal data is **never** stored in the skill folder. It goes to a private folder:

| OS | Default location | Protection |
|---|---|---|
| macOS / Linux | `~/.job_agents/` | Folder mode 700, files mode 600 (only you can read them) |
| Windows | `C:\Users\<you>\.job_agents\` | Protected by your Windows user account. Don't put it in a shared folder. |

```
profile.json      verified facts taken from your CV (the only source for any claim)
cv_text.txt       extracted CV text
tracker.db        SQLite record of every job, score, approval and submission
applications/     tailored CVs and cover letters (DOCX / PDF / TXT)
inbox/  logs/
```

To use a different location, set `JOB_AGENTS_HOME`:

```bash
echo 'export JOB_AGENTS_HOME="$HOME/Documents/job_agents_data"' >> ~/.zshrc    # macOS (zsh)
echo 'export JOB_AGENTS_HOME="$HOME/Documents/job_agents_data"' >> ~/.bashrc   # Linux (bash)
```
```powershell
setx JOB_AGENTS_HOME "$env:USERPROFILE\Documents\job_agents_data"            # Windows (new terminals)
```

> Don't commit your data folder or put your CV inside the skill folder if you fork this repo.

---

## 4. Use

Open a terminal in any folder (Terminal, PowerShell or Git Bash), run `claude`, then:

| Command | What it does |
|---|---|
| `/job_agents` | Shows the pipeline status and suggests the next step |
| `/job_agents setup` | Picks your CV, extracts it and builds `profile.json`. **Run this first.** You review and confirm the profile, including any inconsistencies it flags. |
| `/job_agents search` | Searches the web, checks each posting is real and open, removes duplicates, then scores and shortlists |
| `/job_agents rank` | Scores any jobs that haven't been scored yet |
| `/job_agents tailor 12` | Writes a CV and cover letter tailored to job 12, then checks every claim against your profile |
| `/job_agents prepare 12` | Fills in the application in Chrome and **stops before Submit**. You approve it, then submit. |
| `/job_agents status` | Summary of the pipeline and upcoming deadlines |
| `/job_agents schedule preview\|enable\|disable` | Automatic searches. Built in on macOS; see [section 5](#5-scheduled-searches-optional) for Linux and Windows. |

### A typical first run

1. `/job_agents setup`: confirm or correct the profile it extracts.
2. `/job_agents search`: you get a ranked table with score, matched skills, gaps, deadline and link.
3. `/job_agents tailor <id>`: review the documents in `<data folder>/applications/<id>-<company>/`.
4. `/job_agents prepare <id>`: sign in to the job site yourself, check the filled form, approve,
   then submit.
5. Later, record outcomes, for example: *"mark job 12 as interviewing"*.

---

## 5. Scheduled searches (optional)

Scheduled runs only **search, score and record** jobs. They never write documents, fill forms or
submit anything. They're off by default. Your computer must be on and awake at the scheduled
times.

### macOS: built in

```
/job_agents schedule preview     # shows the times and the LaunchAgent; changes nothing
/job_agents schedule enable      # asks for your approval, then installs it
/job_agents schedule disable     # removes it
```

### Linux: cron

The included runner script needs `zsh` (`sudo apt install zsh`). Open your crontab with
`crontab -e` and add this line. Cron uses your **system's local time**, so convert the times if
your system time zone isn't the one in the config.

```cron
0 8,11,14,17,20 * * * PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin" zsh "$HOME/.claude/skills/job_agents/scripts/scheduled_search.sh"
```

Logs go to `~/.job_agents/logs/`. To stop, delete the line with `crontab -e`.

### Windows: Task Scheduler

1. Create the file `%USERPROFILE%\.job_agents\scheduled_search.cmd` with this content:
   ```bat
   @echo off
   if not exist "%USERPROFILE%\.job_agents\logs" mkdir "%USERPROFILE%\.job_agents\logs"
   cd /d "%USERPROFILE%\.claude\skills\job_agents"
   claude -p "/job_agents search --scheduled" --allowedTools "WebSearch" "WebFetch" "Read" "Write" "Bash(python3 *)" >> "%USERPROFILE%\.job_agents\logs\scheduled.log" 2>&1
   ```
2. Register the five daily runs (PowerShell). The times use your **Windows clock**:
   ```powershell
   foreach ($t in '08:00','11:00','14:00','17:00','20:00') {
     schtasks /Create /F /SC DAILY /ST $t /TN "job_agents_search_$($t -replace ':','')" `
       /TR "`"$env:USERPROFILE\.job_agents\scheduled_search.cmd`""
   }
   ```
3. To stop, remove the tasks:
   ```powershell
   foreach ($t in '0800','1100','1400','1700','2000') { schtasks /Delete /F /TN "job_agents_search_$t" }
   ```

---

## 6. Safety rules built into the skill

- **Truthfulness:** documents contain only facts from your verified profile. `verify_claims.py`
  blocks any skill, metric, employer, degree or year count that isn't backed by the profile.
- **Consent:** nothing is submitted, sent or signed up for without your approval for that
  specific action.
- **Privacy:** passwords, OTPs, national ID, passport and KRA PIN numbers are never stored or
  typed. You sign in to sites yourself.
- **Legitimacy:** it uses employer career pages and permitted job boards only, and skips postings
  with scam signals.
- **No duplicates:** the tracker refuses to apply to the same job twice.

---

## 7. Troubleshooting

| Problem | OS | Fix |
|---|---|---|
| `/job_agents` doesn't appear | All | Make sure the folder is named exactly `job_agents`, is inside `.claude/skills/`, and contains `SKILL.md`. Then restart Claude Code. |
| "No CVs found" | All | Check `cv_directory` in the config and make sure the file ends in `.pdf`. On Windows, check whether your Desktop is inside OneDrive. |
| "Install pypdf ... to extract PDFs" | Linux / Windows | `python3 -m pip install --user pypdf` (Windows: `py -m pip install --user pypdf`). |
| The extracted CV text is empty | All | The PDF is probably a scanned image. Export a text PDF from Word or Google Docs. |
| "no DOCX converter found" | Linux / Windows | Install `pandoc` or LibreOffice (see the install steps), then open a new terminal. |
| "Chrome not found - PDF skipped" | All | Install Chrome or Edge, or set `CHROME_PATH` to the browser's executable. |
| `python3: command not found`, or the Microsoft Store opens | Windows | Follow [Make `python3` work](#2c-windows-1011). |
| Claude Code says it needs Git Bash | Windows | Install Git for Windows (`winget install Git.Git`) and restart the terminal. |
| `prepare` gives a copy sheet instead of filling the form | All | Install the Claude in Chrome extension and connect it. |
| The scheduled search doesn't run | All | macOS: `python3 scripts/schedule.py status`. Linux: `grep CRON /var/log/syslog`. Windows: open Task Scheduler and check *Last Run Result*. Also check the logs in your data folder. |

---

## Project layout

```
SKILL.md                      instructions Claude follows when you run /job_agents
config/search_config.json     role families, location tiers, ranking weights, thresholds, schedule
config/tech_terms.txt         vocabulary the anti-fabrication checker watches for
references/*.md               job sources and scam checks, scoring rubric, document rules, browser steps
scripts/cv_profile.py         discover / extract / validate / summary for the CV and profile
scripts/score.py              weighted ranking
scripts/tracker.py            SQLite tracker: duplicate checks, status lifecycle, approval gate
scripts/render_docs.py        Markdown -> DOCX + text PDF + TXT (textutil / pandoc / LibreOffice; Chrome or Edge)
scripts/verify_claims.py      flags unverified skills, metrics, years, degrees, employers
scripts/schedule.py           macOS launchd schedule (preview / install --user-approved / uninstall)
scripts/scheduled_search.sh   headless search-only run used by the schedule (macOS launchd, Linux cron)
tests/                        unittest suite (uses a synthetic profile; no personal data)
```
