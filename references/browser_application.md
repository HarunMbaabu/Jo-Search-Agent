# Preparing applications with Claude in Chrome

## Pre-conditions (all required)
- Job status `ready_for_review`, `link_verified = 1`, documents attached with `--claims-verified`.
- The user has reviewed the tailored CV + cover letter for this specific job.
- `tracker.py check` shows no prior application for the same role.

## Procedure
1. Load the browser tools in one ToolSearch call:
   `select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__file_upload,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__get_page_text`
   If unavailable or no browser is connected, skip to "Manual fallback".
2. `tabs_context_mcp`, then open a NEW tab and navigate to the verified `apply_url`.
3. Confirm the page is the employer/ATS domain recorded in the tracker. If it redirects elsewhere,
   stop and tell the user.
4. Fill only fields backed by the profile: name, email, phone, location, LinkedIn, GitHub,
   employment history, education. Upload the tailored DOCX/PDF CV and cover letter with
   `file_upload`.
5. Questions you cannot answer from the profile (salary expectations, notice period, start date,
   right-to-work, demographic/EEO, referral source, custom essays) -> leave blank and list them for
   the user. Never guess. Never tick consent/declaration boxes on the user's behalf.
6. If the site requires login/account creation: stop and ask the user to sign in themselves.
   Never type, store or ask for passwords; never handle CAPTCHAs or 2FA.
7. **STOP before the final Submit/Apply button.** Do not click it. Take a screenshot, then show
   the user: job, URL, every field filled, files attached, unanswered questions.
8. Ask: "Do you approve submitting application #ID to <Company> – <Title>?" Only an explicit yes
   for that specific application counts. Approval of one application never carries to another.
9. After approval: `tracker.py approve ID --user-statement "<user's words>"`, then the user clicks
   Submit (preferred) or explicitly tells you to click it. Then `tracker.py mark-submitted ID --note
   "<confirmation text/number>"`.

## Never enter
National ID number, passport number, KRA PIN, NHIF/SHA/NSSF numbers, bank/M-PESA details, date of
birth, passwords or one-time codes. If a form requires any of these, stop and hand over to the user.

## Manual fallback
Give the user the verified apply link, the document paths, a field-by-field copy sheet and the list
of open questions. The user submits; record approval/submission in the tracker afterwards.
