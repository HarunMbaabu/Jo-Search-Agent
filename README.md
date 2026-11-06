# Jo Search Agent

An AI job-search assistant for data professionals, built as a **Claude Code skill**.

It finds data jobs, ranks them against your CV, writes tailored CVs and cover letters, and fills
in applications for you to review. **It never submits anything without your approval.**

**Roles covered:** Data Analyst / BI · Data Engineer / ETL · Data Scientist · ML / AI Engineer ·
Analytics Engineer · Python / SQL Developer

**Works on:** macOS · Linux · Windows

> Out of the box it's set up for job seekers based in **Kenya** (local jobs, remote roles open to
> Kenya, and international jobs with visa sponsorship). Anyone else can change this; see
> [Configuration](docs/CONFIGURATION.md#if-you-are-not-based-in-kenya).

---

## How it works

1. **Reads your CV** and builds a verified profile. You check and confirm it.
2. **Searches** job boards and company career pages, and drops scams, closed jobs and duplicates.
3. **Scores** each job against your profile, out of 100, and shows a ranked shortlist.
4. **Writes** a tailored CV and cover letter, using only facts from your CV. Nothing is invented.
5. **Fills in** the application in Chrome and stops before Submit. You review it and submit.

---

## Quick start

### Step 1: Install

You need **Claude Code** (with a Claude subscription or API key), **Python 3.9+** and **Git**.
Click your operating system:

<details>
<summary><b>macOS</b></summary>

```bash
xcode-select --install
curl -fsSL https://claude.ai/install.sh | bash
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git ~/.claude/skills/job_agents
```
</details>

<details>
<summary><b>Linux (Ubuntu / Debian)</b></summary>

```bash
sudo apt update && sudo apt install -y git python3 python3-pip pandoc
python3 -m pip install --user pypdf        # or: sudo apt install python3-pypdf
curl -fsSL https://claude.ai/install.sh | bash
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git ~/.claude/skills/job_agents
```
</details>

<details>
<summary><b>Windows 10 / 11</b></summary>

In **PowerShell**:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id JohnMacFarlane.Pandoc -e
# Close and reopen PowerShell, then:
py -m pip install --user pypdf
irm https://claude.ai/install.ps1 | iex
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git "$env:USERPROFILE\.claude\skills\job_agents"
```

Then open **Git Bash** and check that `python3 --version` works. If it doesn't, follow
[this fix](docs/INSTALL.md#make-python3-work-on-windows).
</details>

Also recommended: [Google Chrome](https://www.google.com/chrome/) and the **Claude in Chrome**
extension, which let the skill create PDFs and fill in application forms.

Full instructions, checks and fixes are in **[docs/INSTALL.md](docs/INSTALL.md)**.

### Step 2: Add your CV

Make a folder called **`cvs`** on your Desktop and put your CV in it **as a PDF**.

| macOS | Linux | Windows |
|---|---|---|
| `/Users/<you>/Desktop/cvs` | `/home/<you>/Desktop/cvs` | `C:\Users\<you>\Desktop\cvs` |

Already keep your CV somewhere else? You can skip the folder (see [step 3](#step-3-set-up-your-profile)).

### Step 3: Set up your profile

Open a terminal, start Claude Code, and run setup:

```
claude
/job_agents setup
```

To use a CV from another location, give its path:
`/job_agents setup ~/Documents/My_CV.pdf`

Claude reads your CV, shows you what it found, and asks you to confirm it.

### Step 4: Find jobs

```
/job_agents search
```

You get a ranked list of jobs with scores, matched skills, gaps, deadlines and links.

---

## Your CV: what to know

- **It must be a PDF.** In Word: *File → Save As → PDF*. In Google Docs: *File → Download → PDF*.
- **It must contain real text.** If you can't highlight words in the PDF, it's a scanned image
  and can't be read. Export it again from the original document.
- **Use your most complete CV.** The skill never adds anything that isn't in it.
- **Several CVs in the folder?** The skill asks which one to use.
- **Your CV file is never changed, moved or uploaded.**
- **Updated your CV?** Replace the PDF and run `/job_agents setup` again.
- **Don't put your CV inside the skill folder.** It's a Git repository, so the CV could be
  shared by accident.

More options, such as Windows OneDrive desktops or changing the default folder:
[docs/CONFIGURATION.md](docs/CONFIGURATION.md#cv-location).

---

## Commands

| Command | What it does |
|---|---|
| `/job_agents` | Shows your progress and suggests the next step |
| `/job_agents setup [path]` | Reads your CV and builds your profile. **Run this first.** |
| `/job_agents search` | Finds, checks and ranks new jobs |
| `/job_agents rank` | Scores any jobs that haven't been scored yet |
| `/job_agents tailor <id>` | Writes a tailored CV and cover letter for a job |
| `/job_agents prepare <id>` | Fills in the application in Chrome and stops before Submit |
| `/job_agents status` | Summary of your applications and upcoming deadlines |
| `/job_agents schedule ...` | Optional automatic searches ([setup](docs/CONFIGURATION.md#scheduled-searches)) |

You can also just ask in plain words, for example *"mark job 12 as interviewing"*.

---

## Safety and privacy

- **Never submits** an application without your approval for that specific job.
- **Never invents** skills, jobs, dates, degrees or results. Every claim is checked against your CV.
- **Never stores or types** passwords, one-time codes, or ID, passport or KRA PIN numbers. You
  sign in to sites yourself.
- **Skips scams** and uses only real company career pages and permitted job boards.
- **Keeps your data private** on your own computer, outside the skill folder
  ([details](docs/CONFIGURATION.md#where-your-data-is-stored)).

---

## More documentation

| Guide | What's in it |
|---|---|
| [docs/INSTALL.md](docs/INSTALL.md) | Detailed install for macOS, Linux and Windows, updating, troubleshooting |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | CV location, search settings, other countries, data folder, scheduled searches |
| [SKILL.md](SKILL.md) | The instructions Claude follows (for contributors) |
