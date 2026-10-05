# Smartlead setup instructions (for an agent with Smartlead access)

Read all of this before touching Smartlead.

## Hard rules
1. **Do not launch, start, schedule or resume any campaign.** Build everything as a draft (paused) campaign. Nothing is sent until Cyrus gives the go-ahead in writing in the project. That covers test sends to real leads too. Send test emails only to Cyrus's own address.
2. **Never import a row whose `send_ready` is not `yes`, and never one whose `gap_confirmed` is not `yes`.** `send_ready=yes` means the address passed verification (Reoon or MillionVerifier status `valid`). Every row today is `unverified`, so step 2 below comes first.
3. **No HTML, no images, no links** in any email (Cyrus, 2026-10-05). Plain text only.
4. **Never send from groundwork-web.com.** Only from the secondary sending domains Cyrus buys, each warmed for 3 to 4 weeks first.
5. Keep Smartlead's default import protections on: skip the global block list, unsubscribed leads and bounced leads.
6. **Purge by 2026-11-03.** The lead CSVs come partly from Google Places data and fall under its 30-day caching rule. Delete `leads/smartlead/` from this repo by 2026-11-03 unless the leads are re-sourced, and scrub it from git history too if the repo is ever made public.
7. Lead files contain business contact data. Don't copy them anywhere else, and delete them from any machine you downloaded them to when you're done.

## What's in this repo
| Path | What |
|---|---|
| `sequences/gap-sequences.md` | The 4-step sequence, every gap sentence, merge fields |
| `leads/smartlead/<campaign>.csv` | One file per Smartlead campaign. Google fields (phone, rating, review count, place ID) are left out on purpose |
| `leads/summary.md` | Lead counts by niche, segment and gap (added with the leads) |
| `templates/smartlead-import-example.csv` | Column layout with one invented row |

Campaign = niche + the main thing that lead's website lacks, for example `exterior-prices` or `lawn-other-gaps`. File name = campaign name.

## Before you start (Cyrus provides these; stop and ask the team lead if any is missing)
- 2 to 3 sending domains, 2 Google Workspace inboxes each, SPF, DKIM and DMARC set, connected to Smartlead with warmup on for 3 to 4 weeks.
- A postal address for the footer (a PO box or private mailbox is fine). **No address = no campaign can be finished.**
- A verification account (Reoon recommended; 600 free checks a month).

## Step 1. Connect and warm the inboxes
- Email Accounts > add each Workspace inbox (SMTP/IMAP or Google OAuth).
- Turn on warmup for every inbox. Leave it on during sending.
- Daily sending limit per inbox: **15 to 20 cold emails**. Week 1 of sending: 20 per domain per day total, then raise to 15 to 20 per inbox.

## Step 2. Verify addresses
- Run every `email` in `leads/smartlead/*.csv` through Reoon (or MillionVerifier).
- Keep only `valid`. Set `email_status=valid` and `send_ready=yes` on those rows; drop `invalid` and `disposable`; drop `catch_all` and `unknown` too (team lead decision).
- Stop and report if more than 3% come back invalid in one file.

## Step 3. Create one campaign per CSV
For each file in `leads/smartlead/`:
1. Campaigns > New campaign. Name it exactly like the file, for example `exterior-prices`.
2. Import CSV > upload the file (verified rows only).
3. Map the columns:

| CSV column | Map to |
|---|---|
| `email` | Email |
| `first_name` | First Name |
| `last_name` | Last Name |
| `company_name` | Company Name |
| `website` | Website |
| `location` | Location |
| `short_name`, `city`, `service`, `gap_line`, `gap_subject`, `fix_line`, `second_gap_sentence`, `season_hook`, `niche`, `gap`, `campaign` | Custom field, same name |
| `name_guess`, `state`, `second_gap`, `email_type`, `email_status`, `gap_confirmed`, `send_ready` | Do not import (or import as custom fields and never use them in copy) |

The custom field names must match the `{{...}}` variables in the copy exactly. Smartlead leaves a blank field empty with no fallback, which is why optional text (`second_gap_sentence`, `season_hook`) is a whole sentence or phrase.

4. `first_name` is a real first name only where it was confirmed on the shop's own site; otherwise `there`, so the greeting reads "Hi there,".

## Step 4. Sequence
Paste the copy from `sequences/gap-sequences.md` exactly.

| Step | Delay after previous | Subject |
|---|---|---|
| 1 | Day 1 | Variant A: `{{short_name}} site` / Variant B: `{{gap_subject}}` (50/50) |
| 2 | 3 days | Blank, so it sends as a reply in the same thread |
| 3 | 5 days | Blank (same thread) |
| 4 | 6 days | Blank (same thread) |

Every step ends with this footer, typed as plain text:
```
Cyrus Wilburn, GroundWork-Web
{postal address}
This is a sales email. Reply "no thanks" and I won't email again.
```
Wording swaps by niche (edit the copy in that campaign only):
- `commercial-*` campaigns: email 1 says "turns a visitor into a bid request" instead of "turns a visitor into a booked job".
- `realestate-*` campaigns: email 1 says "turns a visitor into a listing appointment".

## Step 5. Settings for every campaign
- Plain text. Open tracking **off**. Link tracking **off**.
- Unsubscribe: turn on Smartlead's List-Unsubscribe header only. Do **not** add an unsubscribe link in the body (no links rule); the footer's "no thanks" line covers CAN-SPAM. Treat any reply like "no thanks", "stop" or "remove" as an unsubscribe the same day.
- Stop sending to a lead on any reply. Out-of-office replies pause the lead, they don't count as replies.
- Schedule: Monday to Friday, 8:00 to 11:00 AM in the lead's time zone. Start new leads Tuesday to Thursday.
- Max new leads per day per campaign: split about 100 new leads a day across all campaigns (6 inboxes x 15 to 20).
- Lead order: as in the file (most Google reviews first).
- Exclude Canada (already removed from the files; don't add any back).
- Sending accounts: spread every campaign across all inboxes.

## Step 6. Check, then stop
- Preview the emails for 5 leads per campaign. Every `{{...}}` must fill in, no double spaces, no "Hi ,".
- Open 5 of those leads' websites and confirm the gap sentence is still true. If one is wrong, remove that lead and report it.
- Send one test of each campaign to Cyrus's own address only.
- **Leave every campaign paused/draft.** Report to the team lead: campaign names, lead counts after verification, and anything you removed.

## Timing (for when Cyrus says go)
| Niche | Best window |
|---|---|
| Exterior cleaning | October to February ("before the spring rush") |
| Lawn care | November to February |
| Detailing | Any time; backs up the call list |
| Commercial cleaning | Any time except the last two weeks of December |
| Real estate | January to March |

## Measuring
Judge by reply rate and positive replies, never opens. Kill an angle under 1% replies after 500 contacts. Bounces over 2%: pause and re-verify. Spam complaints must stay under 0.1%.

## When someone replies yes
Hand it to Cyrus. A mockup is built only for people who reply yes. Offer a short call only if they hesitate. Price, always in full: $99 to start (refunded if they don't want the site), $300 when they approve it, then from $99 a month once it's live.
