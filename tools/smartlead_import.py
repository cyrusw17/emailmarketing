"""Load send_ready=yes rows into Smartlead, one campaign per CSV. Never starts, schedules or resumes a campaign.
Dry run by default; add --apply to call the API. API key only from the SMARTLEAD_API_KEY environment variable.
Usage: python3 smartlead_import.py [--apply] [--only exterior-prices,lawn-prices]"""
import csv, glob, json, os, sys, time, urllib.parse, urllib.request
WORK = os.path.expanduser(os.environ.get('GW_WORK', '~/gw-leads/campaigns'))
BASE = 'https://server.smartlead.ai/api/v1'
STANDARD = {'email', 'first_name', 'last_name', 'company_name', 'website', 'location'}
CUSTOM = ['short_name', 'city', 'service', 'gap_line', 'gap_subject', 'fix_line', 'second_gap_sentence', 'season_hook', 'niche', 'gap', 'campaign']

def call(method, path, body=None):
    key = os.environ['SMARTLEAD_API_KEY']
    url = f"{BASE}{path}{'&' if '?' in path else '?'}api_key={urllib.parse.quote(key)}"
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or 'null')

def main():
    apply = '--apply' in sys.argv
    only = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
    existing = {c['name']: c for c in call('GET', '/campaigns')} if apply else {}
    for f in sorted(glob.glob(f'{WORK}/smartlead/*.csv')):
        name = os.path.basename(f)[:-4]
        if only and name not in only:
            continue
        rows = [r for r in csv.DictReader(open(f, newline='')) if r.get('send_ready') == 'yes' and r.get('gap_confirmed') == 'yes']
        print(f'{name}: {len(rows)} send-ready leads' + ('' if apply else ' (dry run)'))
        if not apply or not rows:
            continue
        camp = existing.get(name)
        if not camp:
            camp = call('POST', '/campaigns/create', {'name': name})  # new campaigns start as drafts
            existing[name] = camp
        if str(camp.get('status', 'DRAFTED')).upper() not in ('DRAFTED', 'PAUSED', 'STOPPED', ''):
            print(f'  skipped: campaign is {camp.get("status")}; this script only loads draft or paused campaigns')
            continue
        leads = [{**{k: r[k] for k in STANDARD if r.get(k)}, 'custom_fields': {k: r.get(k, '') for k in CUSTOM}} for r in rows]
        for i in range(0, len(leads), 100):  # API limit: 100 leads per call
            res = call('POST', f"/campaigns/{camp['id']}/leads", {
                'lead_list': leads[i:i + 100],
                'settings': {'ignore_global_block_list': False, 'ignore_unsubscribe_list': False,
                             'ignore_duplicate_leads_in_other_campaign': False}})
            print(f'  batch {i // 100 + 1}: {res}')
            time.sleep(1)

if __name__ == '__main__':
    main()
