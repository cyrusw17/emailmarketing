"""Mark send_ready=yes on rows whose address passed verification.
Usage: python3 apply_verification.py <verifier-results.csv> [more.csv ...]
Reads any CSV with an email column and a status column (Reoon: "status"; MillionVerifier: "result" or "quality").
Only valid/safe/ok count. catch_all, unknown, risky, invalid and disposable stay send_ready=no (team lead rule)."""
import csv, glob, os, sys
WORK = os.path.expanduser(os.environ.get('GW_WORK', '~/gw-leads/campaigns'))
GOOD = {'valid', 'safe', 'ok', 'deliverable'}
status = {}
for f in sys.argv[1:]:
    for r in csv.DictReader(open(f, newline='', encoding='utf-8-sig')):
        low = {k.lower().strip(): (v or '').strip().lower() for k, v in r.items() if k}
        e = low.get('email') or low.get('email address')
        s = low.get('status') or low.get('result') or low.get('quality')
        if e and s:
            status[e] = s
counts = {'yes': 0, 'no': 0, 'not checked': 0}
for f in sorted(glob.glob(f'{WORK}/smartlead/*.csv')):
    rows = list(csv.DictReader(open(f, newline='')))
    if not rows:
        continue
    for r in rows:
        s = status.get(r['email'].lower())
        if s is None:
            counts['not checked'] += 1
            continue
        r['email_status'] = 'valid' if s in GOOD else s
        r['send_ready'] = 'yes' if s in GOOD and r.get('gap_confirmed') == 'yes' else 'no'
        counts[r['send_ready']] += 1
    w = csv.DictWriter(open(f, 'w', newline=''), list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(counts)
