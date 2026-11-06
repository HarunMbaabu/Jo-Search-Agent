# Installation

[← Back to README](../README.md)

- [What you need](#what-you-need)
- [macOS](#macos)
- [Linux](#linux)
- [Windows](#windows)
- [Check that it works](#check-that-it-works)
- [Updating](#updating)
- [Troubleshooting](#troubleshooting)

---

## What you need

| Software | Why | Needed on |
|---|---|---|
| **Claude Code** | Runs the skill. You need a Claude subscription or an Anthropic API key. | All |
| **Python 3.9+** | Runs the helper scripts. No extra Python libraries are needed. | All |
| **Git** | Downloads and updates the skill | All |
| **pypdf** | Reads your CV PDF | Linux, Windows (built into macOS) |
| **pandoc** or **LibreOffice** | Creates Word (DOCX) files | Linux, Windows (built into macOS) |
| **Google Chrome** or **Microsoft Edge** | Creates PDF files | Recommended |
| **Claude in Chrome** extension | Fills in application forms. Without it, you get a copy-and-paste sheet. | Optional |

The skill folder must be named **`job_agents`** and sit in your Claude skills folder:

- macOS / Linux: `~/.claude/skills/job_agents`
- Windows: `C:\Users\<you>\.claude\skills\job_agents`

---

## macOS

```bash
# 1. Git and Python (Apple's developer tools)
xcode-select --install

# 2. Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# 3. The skill
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git ~/.claude/skills/job_agents

# 4. Optional: more accurate CV reading
python3 -m pip install --user pypdf
```

Install [Google Chrome](https://www.google.com/chrome/) for PDF output.

---

## Linux

Ubuntu / Debian. On Fedora or Arch, use `dnf` or `pacman` with the same package names.

```bash
# 1. Git, Python and a DOCX converter
sudo apt update
sudo apt install -y git python3 python3-pip pandoc

# 2. CV reader
python3 -m pip install --user pypdf
#   If pip says "externally-managed-environment":  sudo apt install python3-pypdf

# 3. Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# 4. The skill
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git ~/.claude/skills/job_agents
```

Install Google Chrome or Chromium for PDF output. If the skill can't find it, set
`CHROME_PATH=/path/to/chrome`.

---

## Windows

Windows 10 or 11. Run these commands in **PowerShell**:

```powershell
# 1. Git (Claude Code needs it), Python and a DOCX converter
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id JohnMacFarlane.Pandoc -e

# 2. Close PowerShell and open it again, then install the CV reader
py -m pip install --user pypdf

# 3. Claude Code
irm https://claude.ai/install.ps1 | iex

# 4. The skill
git clone https://github.com/HarunMbaabu/Jo-Search-Agent.git "$env:USERPROFILE\.claude\skills\job_agents"
```

### Make `python3` work on Windows

The skill runs its scripts with the command `python3`. Open **Git Bash** and run
`python3 --version`. If you see an error, or the Microsoft Store opens:

1. Open *Settings → Apps → Advanced app settings → App execution aliases*. Turn **off**
   `python.exe` and `python3.exe`.
2. In PowerShell, run:
   ```powershell
   $py = (Get-Command python).Source
   Copy-Item $py (Join-Path (Split-Path $py) "python3.exe")
   ```
3. Open a new Git Bash window and check `python3 --version` again.

**Prefer WSL?** You can run Claude Code inside WSL (Ubuntu) and follow the [Linux](#linux) steps
instead.

---

## Check that it works

1. Run the self-test. You should see `OK` at the end.
   ```bash
   python3 -m unittest discover -s ~/.claude/skills/job_agents/tests
   ```
   On Windows PowerShell:
   `py -m unittest discover -s "$env:USERPROFILE\.claude\skills\job_agents\tests"`
2. Start Claude Code with `claude` and type `/job_agents`. The skill should appear in the list.

---

## Updating

```bash
git -C ~/.claude/skills/job_agents pull                          # macOS / Linux
git -C "$env:USERPROFILE\.claude\skills\job_agents" pull         # Windows
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `/job_agents` doesn't appear | Check that the folder is named exactly `job_agents`, is inside `.claude/skills/`, and contains `SKILL.md`. Then restart Claude Code. |
| "No CVs found" | Make sure the CV is a PDF directly inside the `cvs` folder, not in a subfolder. Or run `/job_agents setup <path-to-cv.pdf>`. |
| "Install pypdf" | `python3 -m pip install --user pypdf` (Windows: `py -m pip install --user pypdf`) |
| The CV reads as empty | The PDF is a scanned image. Export it again from Word or Google Docs. |
| "no DOCX converter found" | Install pandoc or LibreOffice, then open a new terminal. |
| "Chrome not found - PDF skipped" | Install Chrome or Edge, or set `CHROME_PATH`. Your DOCX and TXT files are still created. |
| Windows: `python3` not found, or the Store opens | See [Make python3 work on Windows](#make-python3-work-on-windows). |
| Windows: Claude Code asks for Git Bash | `winget install --id Git.Git -e`, then restart the terminal. |
| `prepare` gives a copy sheet instead of filling the form | Install and connect the Claude in Chrome extension. |
| Scheduled searches don't run | See [Scheduled searches](CONFIGURATION.md#scheduled-searches). |
