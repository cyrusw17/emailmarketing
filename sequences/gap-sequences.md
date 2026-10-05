# Gap sequences (Smartlead copy)

Status: **draft, nothing sent, nothing loaded.** Built on the GroundWork-Web cold email playbook (sections 4, 5, 9). Owner of final copy: Cold email specialist thread. Prices are the approved price list only.

One sequence skeleton, one gap per lead. The gap is checked by script for that exact shop (site audit kept in the project files, not in this repo) and the full sentence lives in the CSV (`{{gap_line}}`), because Smartlead has no if/else and leaves blank fields empty. So every merge field is either always filled or is a whole optional sentence.

## Merge fields (all in the CSV)
| Field | Example | Notes |
|---|---|---|
| `{{first_name}}` | there | We have no owner names yet; "there" until a name is found. Never guess from the address. |
| `{{company_name}}` | Example Pressure Washing | Google name, LLC/Inc and taglines stripped |
| `{{city}}` | Pasadena | |
| `{{service}}` | pressure washing | From name and category: window/gutter/roof cleaning, soft washing, landscaping, mobile detailing |
| `{{gap_line}}` | there's no way to ask for a quote on your site, so homeowners have to call and catch you between jobs | One per lead, the highest-priority gap found |
| `{{gap_subject}}` | quote requests | Subject B |
| `{{fix_line}}` | a short quote request form near the top that works on a phone and sends straight to you | Email 2 |
| `{{second_gap_sentence}}` | While I was there I'd also show starting prices. | Empty when only one gap was found |
| `{{season_hook}}` | " before the spring rush" | Exterior, lawn, real estate; empty for detailing and commercial |
| `{{rating}}`, `{{review_count}}` | 5.0, 130 | Only used inside gap lines |

## Gap lines (exact text, by niche)
Priority decides which one leads: request form, then reviews, then the niche's next gaps (detailing: prices, phones, before/after; exterior: before/after, prices, phones; lawn: phones, prices). "Reviews" counts only when the shop has 10+ Google reviews at 4.5+ stars.

| Gap | Line |
|---|---|
| request_form, detailing | there's no way to book or request a time on your site, so people have to call and hope you pick up |
| request_form, exterior | there's no way to ask for a quote on your site, so homeowners have to call and catch you between jobs |
| request_form, lawn | ...so homeowners have to call and catch you between yards |
| request_form, commercial | there's no way to request a walkthrough or a bid on your site, so a facility manager comparing companies has to call just to get started |
| request_form, real estate | there's no way for a seller to ask for a home value on your site, so they have to call or email you cold |
| reviews | you have {rating} stars from {count} Google reviews, and none of them show on your site, which is the first thing a {homeowner / car owner / facility manager / seller} looks for |
| prices, detailing | your site doesn't list prices, so people who want a number have to call or message first |
| prices, exterior | your site doesn't show a single starting price, so people who want a number for a house wash may call someone who does |
| prices, lawn | your site doesn't give even a starting price, so people who want a ballpark for mowing tend to move on to the next company |
| not_mobile | your site isn't set up for phones, so it shows up shrunk down and hard to tap, and most people looking you up are on a phone |
| before_after | your before-and-after photos are the best sales pitch you have, and I couldn't find any on your site |
| tap_to_call | on a phone there's no button to tap and call you, so people have to copy your number by hand |
| not_secure | browsers show "Not secure" next to your site's address, and that makes some people back out before they call |

Never used as a lead gap: slow pages (our check can't match PageSpeed; the old "slow" line needs a PageSpeed score under 50 checked per shop) and old copyright years (not something a customer sees).

---

## Email 1 (day 1), about 60 words, no links

Subject A: `{{company_name}} site`
Subject B: `{{gap_subject}}`

> Hi {{first_name}},
>
> I was looking at {{service}} companies in {{city}} and checked out {{company_name}}'s site. One thing stood out: {{gap_line}}.
>
> That's an easy fix, and it's the kind of thing that turns a visitor into a booked job. Want me to mock it up and send it over? No cost to look.

## Email 2 (day 4, same thread), about 45 words

> Hi {{first_name}}, to be specific, I'd add {{fix_line}}. {{second_gap_sentence}}
>
> Should I put a mockup together for {{company_name}}?

## Email 3 (day 9, same thread), live offer only

> Hi {{first_name}}, here's how it works: $99 to start, I build the new site, you see it before paying the $300, and if you don't like it you get the $99 back. Monthly plans start at $99, only once it's live.
>
> Worth a look for {{company_name}}{{season_hook}}?

No links and no HTML in any step (Cyrus, 2026-10-05). Mockups are built only for people who reply yes, so no email says one already exists.

## Email 4 (day 15, breakup), about 30 words

> Hi {{first_name}}, I'll leave it here. If you ever want a second set of eyes on {{company_name}}'s site, just reply and I'll send over a free check.

## Footer on every email
```
Cyrus Wilburn, GroundWork-Web
{postal address, chosen by Cyrus}
This is a sales email. Reply "no thanks" and I won't email again.
```
Plus Smartlead's unsubscribe link/header on.

## Commercial cleaning and real estate wording
Email 1 swaps "turns a visitor into a booked job" for "turns a visitor into a bid request" (commercial) or "turns a visitor into a listing appointment" (real estate). Email 3 is the same offer. Load them as separate Smartlead campaigns so the swap is plain text, not a merge field.
