# Job search sources and legitimacy checks

Use only legitimate employer career pages and recruitment platforms whose terms permit viewing.
Do **not** bulk-scrape sites that prohibit automation (e.g. LinkedIn, Glassdoor). For those, use web
search results that link to the posting, or ask the user to open the page in their own Chrome
session and read it with Claude in Chrome at human pace. Never bypass logins, CAPTCHAs or paywalls.

## Tier 1 - Jobs in Kenya
| Source | Notes |
|---|---|
| Employer career pages | Safaricom, M-PESA Africa, KCB, Equity Bank, NCBA, Absa Kenya, Stanbic, I&M, Co-op Bank, Britam, Jubilee, CIC, Old Mutual, M-KOPA, Cellulant, Twiga Foods, Sendy, Wasoko, Kopo Kopo, Pezesha, Moniepoint Kenya, Copia, Apollo Agriculture, Bolt, Glovo, Microsoft ADC (Nairobi), Google Kenya, Visa (Nairobi), IBM Research Africa, Andela, Turing, Kenya Airways, KenGen, KPLC, EABL, Unilever, Safaricom Spark, Sanergy, One Acre Fund, IDinsight, Living Goods |
| International orgs in Nairobi | UN Careers (careers.un.org - UNON, UNEP, UN-Habitat), UNICEF, WFP, UNHCR, World Bank, IFC, AfDB, ILRI, ICRAF/CIFOR, KEMRI-Wellcome, Gates Foundation, Mastercard Foundation, IRC, Save the Children (via ReliefWeb jobs) |
| Kenyan public sector | Public Service Commission (psckjobs.go.ke), County PSBs, Central Bank of Kenya, KRA, KNBS, ICT Authority - official .go.ke sites only |
| Job boards | BrighterMonday Kenya, MyJobMag Kenya, Fuzu, Corporate Staffing Services, Opportunities for Young Kenyans (verify each to an employer page), ReliefWeb (NGO), LinkedIn (via search results only) |

## Tier 2 - Remote roles accepting Kenya-based applicants
Accept only if the posting **explicitly** says one of: Kenya, Africa, EMEA (incl. Africa), "anywhere",
"worldwide", "any timezone", or names an Employer-of-Record arrangement covering Kenya
(Deel, Remote.com, Oyster, Rippling).

Sources: Greenhouse / Lever / Ashby / Workable / SmartRecruiters / Teamtailor boards found via web
search (e.g. `site:boards.greenhouse.io "data engineer" remote Africa`), We Work Remotely, Remotive,
Remote OK, Working Nomads, Himalayas, Arc.dev, Turing, Andela, Toptal (vetting-based), EU Remote Jobs
(only EMEA-incl.-Africa roles), Pangian, Jobgether (check "location: worldwide").

Reject "remote" roles limited to US/UK/EU/Canada residents, or requiring existing local work rights.

## Tier 3 - International with relocation AND visa sponsorship
Require explicit wording: "visa sponsorship", "relocation package", "we sponsor work permits", Skilled
Worker sponsor, Blue Card support, etc. Sources: Relocate.me, Landing.jobs, Otta / Welcome to the
Jungle (sponsorship filter), Make it in Germany, Workpermit-friendly employer pages (Booking.com,
Adyen, Zalando, Spotify, Klarna, Delivery Hero, Revolut, Wise, Amazon, Microsoft, Google), UK
Register of Licensed Sponsors (gov.uk) to confirm UK sponsors, IND public register (NL recognised
sponsors), UAE/Saudi/Qatar employer pages (confirm employer-provided visa).

## Verification checklist (every job, before scoring above "unclear")
1. The application URL resolves (HTTP 200) on the employer's domain or a known ATS
   (greenhouse.io, lever.co, ashbyhq.com, workable.com, smartrecruiters.com, myworkdayjobs.com,
   successfactors, taleo, icims, bamboohr, teamtailor, recruitee, breezy, jobvite, oraclecloud).
2. The posting is open (not "no longer accepting", past deadline, or 404/redirect to listing).
3. The employer exists (own website, LinkedIn page, KRA/company registry or press coverage).
4. Eligibility wording matches the location tier assigned.
5. Record the result: `tracker.py verify-link ID --ok|--failed --note "..."`.

## Scam / red-flag signals - skip and tell the user
- Any fee: application, training, "medical", visa processing, registration, "refundable deposit".
- Contact only via WhatsApp/Telegram/Gmail/Yahoo, or interview via chat only.
- Requests for national ID, passport, KRA PIN, bank or M-PESA details **before** an offer.
- Salary wildly above market for the level, vague duties, urgent "start tomorrow".
- Domain mismatch (e.g. `safaricom-careers.net`), copy-pasted descriptions with a different company.
- "Overseas jobs" agencies not on the NEA (National Employment Authority) accredited list.
