"""Audit each lead's website for gaps. Fetches the home page plus up to 2 relevant
internal pages (pricing/services/booking/quote/contact) with curl, extracts signals.
Output: $GW_WORK/data/site-audit.csv (one row per domain)."""
import csv, glob, json, re, subprocess, sys, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor

import os, glob as _g
WORK = os.path.expanduser(os.environ.get('GW_WORK', '~/gw-leads/campaigns'))
def lead_files():
    pats = os.environ.get('GW_LEADS', '~/gw-leads/*-deduped.csv').split(';')
    return sorted({f for p in pats for f in _g.glob(os.path.expanduser(p.strip()))})
OUT = f'{WORK}/data/site-audit.csv'
os.makedirs(f'{WORK}/data', exist_ok=True)
UA = 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36'

def dom(u):
    try:
        h = urllib.parse.urlparse(u).hostname or ''
    except Exception:
        return ''
    return h.lower().removeprefix('www.')

def fetch(url):
    t = time.time()
    p = subprocess.run(['curl', '-sS', '-L', '--max-redirs', '5', '-m', '15', '-A', UA, '--compressed',
                        '-w', '\n__META__%{http_code} %{url_effective} %{time_starttransfer} %{time_total} %{size_download}', url],
                       capture_output=True, timeout=25)
    body = p.stdout.decode('utf-8', 'replace')
    if '__META__' not in body:
        return None
    body, meta = body.rsplit('\n__META__', 1)
    code, eff, ttfb, tot, size = meta.split(' ')
    return dict(code=int(code), url=eff, ttfb=float(ttfb), total=float(tot), size=int(float(size)), html=body)

PRICE = re.compile(r'\$\s?\d{2,4}(?:\.\d\d)?(?!\d)(?!\s*(?:k|m|million|billion|off|discount))', re.I)
BOOK_WIDGET = re.compile(r'calendly\.com|squareup\.com/appointments|square\.site/book|acuityscheduling|as\.me/|setmore\.com|booksy\.com|vagaro\.com|schedulicity|clienthub\.getjobber|getjobber\.com/(?:client|work_request)|housecallpro\.com|book\.housecallpro|urable\.com|mobile-tech-rx|mobiletechrx|servicetitan|workiz\.com|markate\.com|gorilladesk|fieldpulse|booking\.|/book-online|/booking|/book-now|/schedule|bookingkoala|launch27|zenmaid|youcanbook\.me|tidycal|simplybook|book now|book online|schedule (?:now|online|service)|request (?:an )?appointment|showingtime', re.I)
QUOTE_WORDS = re.compile(r'(free )?(quote|estimate|bid|proposal)', re.I)
FORM_EMBED = re.compile(r'jotform|typeform|wufoo|formstack|cognitoforms|hsforms|hubspot.*form|wpforms|gravityforms|gform_|contact-form-7|wpcf7|elementor-form|forminator|ninja-forms|fluentform|squarespace-form|wixforms|wix-forms|form-builder|getjobber\.com/client_hubs|work_request|housecallpro|google\.com/forms|docs\.google\.com/forms|123formbuilder|formsite|leadconnector|msgsndr|gohighlevel', re.I)
REVIEWS = re.compile(r'testimonial|what (?:our )?(?:customers|clients) say|google reviews|reviews?\b.*\b(?:stars?|★)|★★★|elfsight|trustindex|birdeye|podium|nicejob|reviewsonmywebsite|grade\.us|sociablekit|embedsocial|reviewwave|5[- ]star', re.I)
BEFORE_AFTER = re.compile(r'before\s*(?:&amp;|&|and|/|-)\s*after|before-after|beforeafter|twentytwenty|image-compare|juxtapose', re.I)
PLATFORM = [('wix', r'wixstatic|wix\.com'), ('squarespace', r'squarespace'), ('godaddy', r'godaddy|secureserver|img1\.wsimg'),
            ('weebly', r'weebly'), ('wordpress', r'wp-content'), ('shopify', r'cdn\.shopify'), ('duda', r'dudaone|multiscreensite'),
            ('webflow', r'webflow'), ('gohighlevel', r'leadconnector|msgsndr'), ('yelp-site', r'yelp\.com/biz')]
SUBLINK = re.compile(r'href=["\']([^"\'#]+)["\']', re.I)
SUBWANT = re.compile(r'pric|rate|package|menu|cost|service|book|schedul|quote|estimate|contact|appoint', re.I)

def forms_real(html):
    n = 0
    for f in re.findall(r'<form\b.*?</form>', html, re.I | re.S):
        low = f.lower()
        if 'search' in low and 'textarea' not in low:
            continue
        inputs = len(re.findall(r'<(?:input|textarea|select)\b', low))
        if inputs >= 3 and ('textarea' in low or 'tel' in low or 'phone' in low or 'message' in low):
            n += 1
    return n

def audit(site):
    url = site if site.startswith('http') else 'http://' + site
    r = None
    for u in (url, url.replace('http://', 'https://') if url.startswith('http://') else None):
        if not u:
            continue
        try:
            r = fetch(u)
        except Exception:
            r = None
        if r and r['code'] and r['code'] < 500 and r['html'].strip():
            break
    row = dict(website=site, domain=dom(site))
    if not r or not r['html'].strip() or r['code'] >= 400:
        row.update(status='unreachable', http_code=(r or {}).get('code', 0))
        return row
    h = r['html']
    low = h.lower()
    pages = [h]
    # follow up to 2 relevant internal links
    base = r['url']
    seen = set()
    for href in SUBLINK.findall(h):
        full = urllib.parse.urljoin(base, href)
        if dom(full) != dom(base) or full in seen or not SUBWANT.search(urllib.parse.urlparse(full).path):
            continue
        if re.search(r'\.(jpg|png|pdf|webp|css|js)$', full, re.I):
            continue
        seen.add(full)
        if len(seen) > 2:
            break
        try:
            s = fetch(full)
            if s and s['code'] < 400:
                pages.append(s['html'])
        except Exception:
            pass
    allh = '\n'.join(pages)
    text = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', allh, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    years = [int(y) for y in re.findall(r'(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})', h, re.I) if 1995 < int(y) < 2030]
    platform = next((n for n, p in PLATFORM if re.search(p, low)), 'other')
    booking = bool(BOOK_WIDGET.search(allh))
    real_forms = forms_real(allh)
    form_embed = bool(FORM_EMBED.search(allh))
    has_form = real_forms > 0 or form_embed
    row.update(
        status='ok', http_code=r['code'], final_url=r['url'], https=r['url'].startswith('https://'),
        platform=platform,
        viewport=bool(re.search(r'<meta[^>]+name=["\']viewport', h, re.I)),
        tel_link='href="tel:' in low or "href='tel:" in low,
        sms_link='href="sms:' in low,
        prices_shown=sum(1 for m in PRICE.finditer(text) if not re.search(r'save|off|discount|up to|over|deposit|fee', text[max(0, m.start()-25):m.end()+12], re.I)) >= 2,
        booking=booking,
        quote_form=has_form,
        quote_cta=bool(QUOTE_WORDS.search(text)),
        reviews_shown=bool(REVIEWS.search(allh)),
        before_after=bool(BEFORE_AFTER.search(allh)),
        img_count=len(re.findall(r'<img\b', h, re.I)),
        html_kb=round(r['size'] / 1024),
        scripts=len(re.findall(r'<script\b', h, re.I)),
        ttfb=round(r['ttfb'], 2), load_s=round(r['total'], 2),
        copyright_year=max(years) if years else '',
        word_count=len(text.split()),
        pages_checked=len(pages),
    )
    return row

def safe(s):
    try:
        return audit(s)
    except Exception as e:
        return dict(website=s, domain=dom(s), status='error:' + type(e).__name__)

def main():
    sites = {}
    for f in lead_files():
        for x in csv.DictReader(open(f)):
            if x['segment'] == 'has_site' and x['website']:
                d = dom(x['website'])
                if d and d not in sites:
                    sites[d] = x['website']
    items = list(sites.values())
    if len(sys.argv) > 1:
        items = items[:int(sys.argv[1])]
    print(len(items), 'sites', flush=True)
    fields = ['website', 'domain', 'status', 'http_code', 'final_url', 'https', 'platform', 'viewport', 'tel_link', 'sms_link',
              'prices_shown', 'booking', 'quote_form', 'quote_cta', 'reviews_shown', 'before_after', 'img_count', 'html_kb',
              'scripts', 'ttfb', 'load_s', 'copyright_year', 'word_count', 'pages_checked']
    done = 0
    with open(OUT, 'w', newline='') as fh, ThreadPoolExecutor(48) as ex:
        w = csv.DictWriter(fh, fields)
        w.writeheader()
        for row in ex.map(safe, items):
            w.writerow(row)
            done += 1
            if done % 250 == 0:
                print(done, flush=True); fh.flush()

if __name__ == '__main__':
    main()
