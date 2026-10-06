"""Join lead lists with the site audit, assign each lead its website gaps, and write
Smartlead-ready CSVs (one per campaign) plus segment counts.
Inputs: $GW_LEADS (prospect CSVs), $GW_WORK/data/site-audit.csv, render-check.csv, name-check.json,
optional $GW_EXISTING (already-built Smartlead CSVs, kept as they are), $GW_SUPPRESS (CSVs with an email column)
and $GW_PIPELINE (anything not 'new' is suppressed). Outputs under $GW_WORK."""
import csv, glob, json, re, collections, urllib.parse, os

ROOT = os.path.expanduser(os.environ.get('GW_WORK', '~/gw-leads/campaigns'))
GATE = os.environ.get('NO_GATE') != '1'  # NO_GATE=1 exports every static gap for the browser re-check
NICHE_KEY = {'auto-detailers': 'detailing', 'exterior-cleaning': 'exterior', 'lawn-care': 'lawn',
             'commercial-cleaning': 'commercial', 'real-estate-agents': 'realestate'}
NICHE_OF = {'auto-detailing': 'detailing', 'exterior-cleaning': 'exterior', 'landscaping-lawn-care': 'lawn',
            'commercial-cleaning': 'commercial', 'real-estate-agents': 'realestate'}
CANADA = {'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'}
FREE = re.compile(r'@(gmail|yahoo|hotmail|outlook|aol|icloud|live|msn|comcast|att|sbcglobal|bellsouth|ymail|me)\.', re.I)

# Words per niche: who visits the site, what they ask for, the season hook for email 3.
N = {
    'detailing': dict(visitor='car owner', request='booking request', season='', campaign_word='detailing'),
    'exterior': dict(visitor='homeowner', request='quote request', season=' before the spring rush', campaign_word='exterior'),
    'lawn': dict(visitor='homeowner', request='quote request', season=' before spring sign-ups start', campaign_word='lawn'),
    'commercial': dict(visitor='facility manager', request='walkthrough request', season='', campaign_word='commercial'),
    'realestate': dict(visitor='seller', request='home value request', season=' before the spring market', campaign_word='realestate'),
}

# Gap priority per niche (first true gap is the one email 1 leads with; second feeds email 2).
PRIORITY = {
    # Marketing review 2026-10-05: phones second everywhere, reviews before prices, before/after before prices (exterior).
    'detailing': ['request_form', 'not_mobile', 'reviews', 'prices', 'tap_to_call', 'not_secure'],
    'exterior': ['request_form', 'not_mobile', 'reviews', 'before_after', 'prices', 'tap_to_call', 'not_secure'],
    'lawn': ['request_form', 'not_mobile', 'reviews', 'prices', 'tap_to_call', 'not_secure'],
    'commercial': ['request_form', 'not_mobile', 'reviews', 'tap_to_call', 'not_secure'],
    'realestate': ['request_form', 'not_mobile', 'reviews', 'tap_to_call', 'not_secure'],
}

def gap_line(g, n, x):
    v = N[n]['visitor']
    if g == 'request_form':
        return {
            'detailing': "there's no way to book or request a time on your site, so people have to call and hope you pick up",
            'exterior': "there's no way to ask for a quote on your site, so homeowners have to call and catch you between jobs",
            'lawn': "there's no way to ask for a quote on your site, so homeowners have to call and catch you between yards",
            'commercial': "there's no way to request a walkthrough or a bid on your site, so a facility manager comparing companies has to call just to get started",
            'realestate': "there's no way for a seller to ask for a home value on your site, so they have to call or email you cold",
        }[n]
    if g == 'reviews':
        return f"you've got plenty of strong Google reviews, but none of them show on your site, and reviews are one of the first things a {v} checks"
    if g == 'prices':
        return {
            'detailing': "your site doesn't list prices, so people who want a number have to call or message first",
            'exterior': "your site doesn't show a single starting price, so people who want a number for a house wash may call someone who does",
            'lawn': "your site doesn't give even a starting price, so people who want a ballpark for mowing tend to move on to the next company",
        }[n]
    if g == 'not_mobile':
        return f"your site isn't set up for phones, so it shows up shrunk down and hard to tap, and most people looking you up are on a phone"
    if g == 'before_after':
        return "your before-and-after photos are the best sales pitch you have, and I couldn't find any on your site"
    if g == 'tap_to_call':
        return "on a phone there's no button to tap and call you, so people have to copy your number by hand"
    if g == 'not_secure':
        return "browsers show \"Not secure\" next to your site's address, and that makes some people back out before they call"

def fix_line(g, n, x):
    r = N[n]['request']
    return {
        'request_form': f"a short {r} form near the top that works on a phone and sends straight to you",
        'reviews': "your best Google reviews right under the headline, next to your phone number",
        'prices': "starting prices for your main services, so people see a number before they call",
        'not_mobile': f"a page built for phones first, with your number and a {r} button you can hit with a thumb",
        'before_after': "your before-and-after photos right up top, where they sell the job",
        'tap_to_call': "a call button and a text button that stay at the bottom of the screen on phones",
        'not_secure': "a secure address, so no browser warns people away",
    }[g]

SUBJECT = {'request_form': {'detailing': 'booking on your site', 'commercial': 'bid requests', 'realestate': 'seller requests'},
           'reviews': 'your google reviews', 'prices': 'prices on your site', 'not_mobile': 'your site on phones',
           'before_after': 'before and afters', 'tap_to_call': 'call button', 'not_secure': 'not secure warning'}

SHORT = {'request_form': 'add a {req} form', 'reviews': 'put your Google reviews on the page',
         'prices': 'show starting prices', 'not_mobile': 'make it work on phones', 'before_after': 'put your before-and-afters up top',
         'tap_to_call': 'add a tap-to-call button', 'not_secure': 'fix the "Not secure" warning'}

def subject(g, n):
    s = SUBJECT[g]
    if isinstance(s, dict):
        return s.get(n, 'quote requests')
    return s

def service_word(n, name, cat):
    t = (name + ' ' + cat).lower()
    if n == 'exterior':
        for k, w in [('window', 'window cleaning'), ('gutter', 'gutter cleaning'), ('roof', 'roof cleaning'), ('soft', 'soft washing')]:
            if k in t:
                return w
        return 'pressure washing'
    if n == 'lawn':
        return 'landscaping' if 'landscap' in t else 'lawn care'
    if n == 'detailing':
        return 'mobile detailing' if 'mobile' in t else 'detailing'
    return {'commercial': 'commercial cleaning', 'realestate': 'real estate'}[n]

def clean_name(s):
    s = re.split(r'\s+[|–—]\s+|\s+-\s+(?=[A-Z][a-z]+ (?:TX|FL|GA|NC|SC|AL|TN|in|of)\b)', s)[0]
    s = re.sub(r',?\s+(LLC|L\.L\.C\.|Inc\.?|Co\.|Corp\.?|Ltd\.?)$', '', s.strip(), flags=re.I)
    return s.strip(' ,')

def short_name(n):
    # Conservative: drop a " - location/tagline" or ", tagline" suffix, then a trailing "And Detail"-style tail.
    s = re.split(r'\s+-\s+|,\s+|\s+\|\s+', n)[0].strip()
    t = re.sub(r'\s+(and|&)\s+\S+(\s+\S+)?$', '', s, flags=re.I).strip()
    return t if len(t.split()) >= 2 else s

def dom(u):
    try:
        return (urllib.parse.urlparse(u).hostname or '').lower().removeprefix('www.')
    except Exception:
        return ''

ROLEWORDS = re.compile(r'info|contact|admin|office|sales|support|hello|team|service|book|quote|detail|wash|clean|lawn|mail|help|owner|estimat|schedul|realty|homes|group', re.I)

NOT_NAMES = {'care', 'serve', 'guzman', 'blue', 'claims', 'design', 'gutters', 'horticare', 'quality', 'ramirez', 'rentals',
             'tucson', 'window', 'davis', 'lewis', 'marshall', 'parker'}  # words, places and surnames (consultant round 1)

def name_guess(e, etype):
    # For a human to confirm before it replaces "there"; never used automatically.
    local = e.split('@')[0]
    if etype == 'personal' and re.fullmatch(r'[a-z]{3,9}', local) and not ROLEWORDS.search(local) and local not in NOT_NAMES:
        return local.capitalize()
    return ''

def truthy(v):
    return v == 'True'

def gaps_for(n, a, x):
    found = []
    has_phone = bool(x['phone'])
    try:
        rating, reviews = float(x['rating'] or 0), int(x['review_count'] or 0)
    except ValueError:
        rating, reviews = 0, 0
    checks = {
        'request_form': not truthy(a['booking']) and not truthy(a['quote_form']) if n == 'detailing' else not truthy(a['quote_form']) and not truthy(a['booking']),
        'reviews': not truthy(a['reviews_shown']) and reviews >= 10 and rating >= 4.5,
        'prices': not truthy(a['prices_shown']),
        'not_mobile': not truthy(a['viewport']),
        'before_after': not truthy(a['before_after']),
        'tap_to_call': has_phone and not truthy(a['tel_link']),
        'not_secure': not truthy(a['https']),
    }
    for g in PRIORITY[n]:
        if checks.get(g):
            found.append(g)
    return found

def main():
    audit = {r['domain']: r for r in csv.DictReader(open(f'{ROOT}/data/site-audit.csv'))}
    render = {r['email']: r for r in csv.DictReader(open(f'{ROOT}/data/render-check.csv'))} if os.path.exists(f'{ROOT}/data/render-check.csv') else {}
    names_ok = json.load(open(f'{ROOT}/data/name-check.json')) if os.path.exists(f'{ROOT}/data/name-check.json') else {}
    suppressed = set()
    for f in [x for p in os.environ.get('GW_SUPPRESS', '').split(';') if p.strip() for x in glob.glob(os.path.expanduser(p.strip()))]:
        for r in csv.DictReader(open(f)):
            if r.get('email'):
                suppressed.add(r['email'].strip().lower())
    pipeline = os.path.expanduser(os.environ.get('GW_PIPELINE', ''))
    for p in (csv.DictReader(open(pipeline)) if pipeline and os.path.exists(pipeline) else []):
        if p['status'] != 'new':
            for v in (p['contact_email'], p['shop']):
                if v:
                    suppressed.add(v.lower())
    leads = {}
    for f in sorted({f for p in os.environ.get('GW_LEADS', '~/gw-leads/*-deduped.csv').split(';') for f in glob.glob(os.path.expanduser(p.strip()))}):
        for x in csv.DictReader(open(f)):
            k = (x['place_id'], x['niche'])
            if k not in leads or (x['email'] and not leads[k]['email']):
                leads[k] = x
    seg = collections.Counter()
    gapcount = collections.Counter()
    rows_out = collections.defaultdict(list)
    seen_email = set()
    excl = collections.Counter()
    # Already-built, already-graded rows (e.g. the repo's leads/smartlead/*.csv) are kept as they are and win any duplicate.
    if GATE:
        for f in [x for p in os.environ.get('GW_EXISTING', '').split(';') if p.strip() for x in sorted(glob.glob(os.path.expanduser(p.strip())))]:
            for r in csv.DictReader(open(f)):
                e = r['email'].strip().lower()
                if e in seen_email:
                    continue
                if e in suppressed:
                    excl['existing row suppressed'] += 1; continue
                seen_email.add(e)
                rows_out[r['niche']].append(dict(r))
    audit_rows = []
    for x in leads.values():
        n = NICHE_OF.get(x['niche'])
        if not n:
            excl['unknown niche ' + x['niche']] += 1
            continue
        a = audit.get(dom(x['website'])) if x['segment'] == 'has_site' else None
        if x['segment'] != 'has_site':
            s = x['segment']
            gaps = []
        elif not a or a.get('status') != 'ok':
            s = 'site_unreachable'
            gaps = []
        else:
            gaps = gaps_for(n, a, x)
            s = 'gap' if gaps else 'no_gap_found'
        seg[(n, s)] += 1
        for g in gaps:
            gapcount[(n, g)] += 1
        if gaps:
            gapcount[(n, 'primary:' + gaps[0])] += 1
        audit_rows.append(dict(niche=n, place_id=x['place_id'], name=x['name'], segment=s, primary_gap=gaps[0] if gaps else '',
                               all_gaps=' '.join(gaps), has_email='yes' if x['email'] else 'no', website=x['website']))
        # Campaign export: has a gap, has an email, US, not suppressed, one row per address.
        if not gaps or not x['email']:
            continue
        e = x['email'].strip().lower()
        if x['state'] in CANADA:
            excl['canada'] += 1; continue
        if e in suppressed or x['name'].lower() in suppressed:
            excl['pipeline status not new'] += 1; continue
        if FREE.search(e) and x['email_source_url'] and dom(x['email_source_url']) != dom(x['website']):
            excl['webmail found on another site'] += 1; continue
        if re.search(r'/locations?/', urllib.parse.urlparse(x['website']).path, re.I):
            excl['chain location page'] += 1; continue
        if e in seen_email:
            excl['duplicate email'] += 1; continue
        rc = render.get(e)
        if GATE:
            if not rc or rc['status'] != 'ok':
                excl['site did not load in browser'] += 1; continue
            if 'c_request_form' in rc:
                gaps = [g for g in gaps if rc.get('c_' + g) == 'yes']
            else:  # older check: only the then-primary and second gap were tested
                ok = {rc['gap']} if rc['gap_confirmed'] == 'yes' else set()
                if rc['second_confirmed'] == 'yes':
                    ok.add(rc['second_gap'])
                gaps = [g for g in gaps if g in ok]
            if not gaps:
                excl['no gap confirmed in browser'] += 1; continue
        seen_email.add(e)
        g1 = gaps[0]
        g2 = gaps[1] if len(gaps) > 1 else ''
        ng = name_guess(e, x['email_type'])
        second = (f"While I was there I'd also {SHORT[g2].format(req=N[n]['request'])}." if g2 else '')
        rows_out[n].append({
            'email': e, 'first_name': ng if ng and names_ok.get(e) else 'there', 'short_name': short_name(clean_name(x['name'])), 'last_name': '', 'company_name': clean_name(x['name']),
            'website': x['website'].split('?')[0], 'name_guess': ng, 'phone_number': x['phone'], 'location': f"{x['city']}, {x['state']}",
            'city': x['city'], 'state': x['state'], 'niche': n, 'service': service_word(n, x['name'], x.get('category', '')),
            'rating': x['rating'], 'review_count': x['review_count'],
            'gap': g1, 'gap_line': gap_line(g1, n, x), 'gap_subject': subject(g1, n), 'fix_line': fix_line(g1, n, x),
            'second_gap': g2, 'second_gap_sentence': second, 'season_hook': N[n]['season'],
            'email_type': x['email_type'], 'email_status': x['email_status'] or 'unverified',
            'gap_confirmed': 'yes', 'send_ready': 'yes' if x['email_status'] == 'valid' else 'no', 'place_id': x['place_id'],
        })
    os.makedirs(f'{ROOT}/smartlead', exist_ok=True)
    for f in glob.glob(f'{ROOT}/smartlead/*.csv'):
        os.remove(f)
    camp_counts = collections.Counter()
    MIN = 60
    for n, rows in rows_out.items():
        by = collections.Counter(r['gap'] for r in rows)
        for r in rows:
            r['campaign'] = f"{n}-{r['gap'].replace('_', '-')}" if by[r['gap']] >= MIN else f"{n}-other-gaps"
            camp_counts[r['campaign']] += 1
    # No Google Places values (phone, rating, review count, place ID) in the Smartlead files.
    fields = ['email', 'first_name', 'name_guess', 'last_name', 'company_name', 'short_name', 'website', 'location', 'city', 'state', 'niche',
              'service', 'gap', 'gap_line', 'gap_subject', 'fix_line', 'second_gap', 'second_gap_sentence',
              'season_hook', 'campaign', 'email_type', 'email_status', 'gap_confirmed', 'send_ready']
    allrows = [r for rows in rows_out.values() for r in rows]
    for c in camp_counts:
        with open(f'{ROOT}/smartlead/{c}.csv', 'w', newline='') as fh:
            w = csv.DictWriter(fh, fields, extrasaction='ignore'); w.writeheader()
            w.writerows(sorted((r for r in allrows if r['campaign'] == c), key=lambda r: -int(r.get('review_count') or 0)))
    with open(f'{ROOT}/data/lead-gaps.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, list(audit_rows[0].keys())); w.writeheader(); w.writerows(audit_rows)
    json.dump(dict(segments={f'{a}|{b}': c for (a, b), c in seg.items()}, gaps={f'{a}|{b}': c for (a, b), c in gapcount.items()},
                   campaigns=camp_counts, excluded=excl, exported=len(allrows)),
              open(f'{ROOT}/data/summary.json', 'w'), indent=1)
    print(json.dumps(dict(campaigns=camp_counts, excluded=excl, exported=len(allrows)), indent=1))

if __name__ == '__main__':
    main()
