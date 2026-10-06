# Confirm a name guessed from an email's local part actually appears as a word on the shop's site.
import csv, glob, json, os, re, subprocess
WORK = os.path.expanduser(os.environ.get('GW_WORK', '~/gw-leads/campaigns'))
from concurrent.futures import ThreadPoolExecutor
rows = [r for f in glob.glob(f'{WORK}/smartlead/*.csv') for r in csv.DictReader(open(f)) if r['name_guess']]
def chk(r):
    base = r['website'].rstrip('/')
    for u in (base + '/', base + '/about', base + '/about-us'):
        p = subprocess.run(['curl', '-sSL', '-m', '12', '--compressed', u], capture_output=True)
        t = re.sub(r'<[^>]+>', ' ', p.stdout.decode('utf-8', 'replace'))
        if re.search(r'\b' + re.escape(r['name_guess']) + r'\b', t):
            return r['email'], True
    return r['email'], False
with ThreadPoolExecutor(32) as ex:
    res = dict(ex.map(chk, rows))
json.dump(res, open(f'{WORK}/data/name-check.json', 'w'))
print(len(res), sum(res.values()))
