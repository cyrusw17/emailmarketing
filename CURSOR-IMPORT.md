# Cursor task: merge the new leads and load them into Smartlead (paused)

Paste this whole file into Cursor as the task. Run it from a checkout of this repo (`cyrusw17/emailmarketing`, branch `claude/project-thread-4ke6l4`). Use the scripts in `tools/`; don't write new ones.

## 0. Hard rules
**Send rule (team lead, 2026-10-06): a lead is sent only when `gap_confirmed=yes` AND Reoon says `valid` (Reoon Power mode calls this `safe`; both count). Every other address, including any lead that was never gap-checked, is not sent. That means this file's merge, gap check and Reoon steps run before any more volume.**

1. **Nothing gets sent.** Never start, schedule, resume or "launch" a campaign, in the API or the UI. Campaigns stay draft or paused until Cyrus starts them himself.
2. Keys only in environment variables: `SMARTLEAD_API_KEY` (and a Reoon key if you use the API). Never print them, write them to a file or commit them.
3. **Never commit lead data.** All output goes to `~/gw-leads/campaigns/`, outside the repo.
4. Only rows with `gap_confirmed=yes` **and** `send_ready=yes` go into Smartlead. `send_ready` turns yes only after verification says `valid`. Catch-all, unknown and risky addresses stay out.
5. Plain-text copy only, no links, no HTML, open and link tracking off (see `SMARTLEAD-SETUP.md`).
6. Delete `~/gw-leads/campaigns/` and the Smartlead leads loaded from it by **2026-11-03** unless they are re-sourced (Google data rule).
7. If anything here would need a paid tool, a bigger cap or a send, stop and ask Cyrus.

## 1. Setup (once)
```sh
git pull origin claude/project-thread-4ke6l4
python3 -m pip install playwright
python3 -m playwright install chromium
export GW_WORK=~/gw-leads/campaigns
export GW_LEADS="$HOME/gw-leads/*-deduped.csv"            # the new scrape (both runs)
export GW_EXISTING="$PWD/leads/smartlead/*.csv"          # the 1,044 leads already built; they win duplicates
export GW_SUPPRESS="$HOME/gw-leads/do-not-contact*.csv"  # optional: any CSV with an email column (unsubscribes, bounces, "no thanks")
```
If Smartlead already has unsubscribes or bounces, export them (Settings > Global Block List, and each campaign's unsubscribed leads) to `~/gw-leads/do-not-contact-smartlead.csv` first.

## 2. Find each new lead's website gap
```sh
cd tools
python3 audit.py                    # opens every new lead's site; a few thousand sites can take an hour
NO_GATE=1 python3 build.py          # first pass: every gap the script found
python3 verify.py                   # re-checks each gap in a real phone-sized browser
python3 names.py                    # keeps a first name only if it also appears on the shop's own site
python3 build.py                    # final: confirmed gaps only, merged with the existing 1,044, deduped
```
The last command prints the lead count for each campaign plus what was removed and why (duplicate email, suppressed, no gap confirmed, chain location page, Canada). Output files: `~/gw-leads/campaigns/smartlead/<campaign>.csv`, one per Smartlead campaign, for example `exterior-prices`, `lawn-other-gaps` or `commercial-request-form`. A gap with 60 or more leads in a niche gets its own campaign; smaller ones go to `<niche>-other-gaps`.

Shops with no website, no email, or no confirmed gap are left out on purpose. They belong on the call list.

## 3. Verify the addresses
1. Make the upload list:
   ```sh
   python3 -c "import csv,glob,os;e=sorted({r['email'] for f in glob.glob(os.path.expanduser('~/gw-leads/campaigns/smartlead/*.csv')) for r in csv.DictReader(open(f))});open(os.path.expanduser('~/gw-leads/to-verify.csv'),'w').write('email\n'+'\n'.join(e)+'\n');print(len(e))"
   ```
2. Upload `~/gw-leads/to-verify.csv` to Reoon (Bulk Verify, Power mode). The first 600 a month are free. Download the results CSV.
3. Apply the results:
   ```sh
   python3 apply_verification.py ~/Downloads/<reoon-results>.csv
   ```
   It prints how many rows are now `send_ready=yes`. Stop and report if more than 3% are invalid.

## 4. Load into Smartlead (campaigns stay paused)
```sh
export SMARTLEAD_API_KEY=...        # terminal only
python3 smartlead_import.py         # dry run: shows send-ready counts per campaign, calls nothing
python3 smartlead_import.py --apply # creates any missing campaign as a draft, adds leads 100 at a time
```
The script:
- matches campaigns by name (= CSV file name) and creates missing ones as drafts
- skips any campaign that is already active, so it never adds leads to a live send
- keeps Smartlead's global block list, unsubscribe list and cross-campaign duplicate checks on
- sends these as custom fields: `short_name`, `city`, `service`, `gap_line`, `gap_subject`, `fix_line`, `second_gap_sentence`, `season_hook`, `niche`, `gap`, `campaign`

## 5. Finish each new campaign in the Smartlead UI
For every campaign the script created (existing ones already have this):
1. **Sequence:** paste the 4 steps from `sequences/gap-sequences.md` exactly. Delays: day 1, then +3, +5, +6 days. Steps 2 to 4 get a blank subject so they reply in the same thread. Step 1 A/B subjects: `{{short_name}} site` and `{{gap_subject}}`.
   - Commercial campaigns: in email 1, say "turns a visitor into a bid request". Real estate: "turns a visitor into a listing appointment".
2. **Footer** on every step (plain text): `Cyrus Wilburn, GroundWork-Web` / postal address / `This is a sales email. Reply "no thanks" and I won't email again.`
3. **Settings:** plain text, open tracking off, link tracking off, List-Unsubscribe header on (no unsubscribe link in the body), stop on reply, Mon to Fri 8 to 11 AM in the lead's time zone, 15 to 20 emails per inbox per day, spread across all warmed inboxes.
4. Preview 5 leads per campaign. Every `{{...}}` must fill in, with no blank "Hi ,". Open 2 of those sites and confirm the gap sentence is still true.
5. Send one test of each campaign to Cyrus's own address only.
6. **Apply the send rule to campaigns that already exist in Smartlead**, including any set up before this file. Export each campaign's leads and compare them with the `send_ready=yes` rows in `~/gw-leads/campaigns/smartlead/*.csv`. In a draft or paused campaign, pause every lead that isn't on that list (Smartlead's per-lead pause, which can be undone). In an active campaign, change nothing: list those leads and ask Cyrus whether to pause them.
7. **Leave it paused.** Report back the campaign names, lead counts per campaign, how many were removed and why, and the verification numbers.

## Marketing skills behind this campaign
- `marketing:campaign-plan`: segments, one campaign per niche and gap, success metric (positive replies per contact).
- `marketing:email-sequence`: the 4-step sequence, timing, exit and suppression rules in `sequences/gap-sequences.md`.
- `marketing:brand-review`: copy check against the brand voice, approved prices only, no unbacked claims.
- The cold email playbook (plain text, no links, CAN-SPAM footer) from the cold email specialist, then team lead review and the consultant's A+ grade.
