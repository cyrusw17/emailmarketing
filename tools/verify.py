"""Second pass: open each exported lead's site in a real browser (phone viewport), so content
drawn by JavaScript counts, and re-check the claimed gaps. Writes data/render-check.csv."""
import asyncio, csv, glob, re, sys, urllib.parse
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from audit import PRICE, BOOK_WIDGET, FORM_EMBED, REVIEWS, BEFORE_AFTER, SUBWANT
from playwright.async_api import async_playwright

import os
ROOT = os.path.expanduser(os.environ.get('GW_WORK', '~/gw-leads/campaigns'))
OUT = f'{ROOT}/data/render-check.csv'

def dom(u):
    return (urllib.parse.urlparse(u).hostname or '').lower().removeprefix('www.')

def prices(text):
    return sum(1 for m in PRICE.finditer(text) if not re.search(r'save|off|discount|up to|over|deposit|fee', text[max(0, m.start()-25):m.end()+12], re.I)) >= 2

async def grab(page, url):
    await page.goto(url, wait_until='domcontentloaded', timeout=25000)
    try:
        await page.wait_for_load_state('networkidle', timeout=8000)
    except Exception:
        pass
    await page.mouse.wheel(0, 4000)
    await page.wait_for_timeout(1500)
    html = await page.content()
    text = await page.evaluate('document.body ? document.body.innerText : ""')
    forms = await page.evaluate('''() => {
      const fs=[...document.querySelectorAll('form')].filter(f=>f.querySelectorAll('input,textarea,select').length>=3 && !/search/i.test(f.outerHTML.slice(0,300)));
      const ifr=[...document.querySelectorAll('iframe')].map(i=>i.src).join(' ');
      return {n:fs.length, ifr};
    }''')
    links = await page.evaluate('[...document.querySelectorAll("a[href]")].map(a=>a.href)')
    return html, text, forms, links

async def check(browser, row, sem):
    async with sem:
        ctx = await browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True,
                                        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')
        page = await ctx.new_page()
        res = dict(email=row['email'], website=row['website'], gap=row['gap'], second_gap=row['second_gap'])
        try:
            html, text, forms, links = await grab(page, row['website'])
            htmls, texts, nforms, ifr = [html], [text], forms['n'], forms['ifr']
            subs = [l for l in dict.fromkeys(links) if dom(l) == dom(page.url) and SUBWANT.search(urllib.parse.urlparse(l).path)][:2]
            for s in subs:
                try:
                    h2, t2, f2, _ = await grab(page, s)
                    htmls.append(h2); texts.append(t2); nforms += f2['n']; ifr += ' ' + f2['ifr']
                except Exception:
                    pass
            allh, allt = '\n'.join(htmls), '\n'.join(texts)
            sw = await page.evaluate('document.documentElement.scrollWidth')
            found = {
                'request_form': not (nforms > 0 or FORM_EMBED.search(allh + ifr) or BOOK_WIDGET.search(allh + ifr)),
                'reviews': not REVIEWS.search(allh),
                'prices': not prices(allt),
                'not_mobile': not re.search(r'<meta[^>]+name=["\']viewport', htmls[0], re.I),
                'before_after': not BEFORE_AFTER.search(allh),
                'tap_to_call': 'href="tel:' not in allh.lower() and "href='tel:" not in allh.lower(),
                'not_secure': not page.url.startswith('https://') if False else None,
            }
            res['status'] = 'ok'
            for g, v in found.items():
                res['c_' + g] = 'yes' if v in (True, None) else 'no'
            res['gap_confirmed'] = 'yes' if found.get(row['gap']) in (True, None) else 'no'
            res['second_confirmed'] = '' if not row['second_gap'] else ('yes' if found.get(row['second_gap']) in (True, None) else 'no')
            res['scroll_width'] = sw
        except Exception as e:
            res['status'] = 'error:' + type(e).__name__
        await ctx.close()
        return res

async def main():
    rows = [r for f in glob.glob(f'{ROOT}/smartlead/*.csv') for r in csv.DictReader(open(f))]
    sem = asyncio.Semaphore(10)
    async with async_playwright() as p:
        # GW_SPKI is only for a TLS-intercepting proxy (the cloud session); leave it unset on a normal machine.
        spki = os.environ.get('GW_SPKI')
        browser = await p.chromium.launch(executable_path=os.environ.get('GW_CHROME') or None, args=[f'--ignore-certificate-errors-spki-list={spki}'] if spki else [])
        out = []
        tasks = [check(browser, r, sem) for r in rows]
        for i, t in enumerate(asyncio.as_completed(tasks)):
            out.append(await t)
            if i % 100 == 0:
                print(i, flush=True)
        await browser.close()
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, ['email', 'website', 'gap', 'second_gap', 'status', 'gap_confirmed', 'second_confirmed', 'scroll_width'] + ['c_' + g for g in ['request_form', 'reviews', 'prices', 'not_mobile', 'before_after', 'tap_to_call', 'not_secure']])
        w.writeheader(); w.writerows(out)

asyncio.run(main())
