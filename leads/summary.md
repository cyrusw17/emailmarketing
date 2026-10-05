# Segments: what each lead's website lacks

Campaigns thread, 2026-10-05. Source: the project's site audit (kept in the project files). Nothing sent.

## All leads by segment
| Niche | Site has a gap | No gap found | No site | Social page only | Site unreachable |
|---|---|---|---|---|---|
| Exterior cleaning | 947 | 35 | 350 | 30 | 217 |
| Lawn care | 637 | 68 | 61 | 17 | 75 |
| Detailing | 436 | 171 | 520 | 104 | 241 |
| Commercial cleaning | 237 | 432 | 131 | 7 | 162 |
| Real estate | 142 | 150 | 21 | 39 | 109 |

The "has a gap" counts come from the script check only; the browser re-check ran on the emailable leads. No-site and social-only shops have almost no findable email, so they stay on the call list (playbook section 7). No-gap sites get no email: we never invent a flaw.

## How common each gap is (sites that have it, any priority)
| Gap | Exterior cleaning | Lawn care | Detailing | Commercial cleaning | Real estate |
|---|---|---|---|---|---|
| No booking/quote form | 222 | 152 | 199 | 119 | 73 |
| Google reviews not shown (10+ at 4.5+) | 209 | 154 | 96 | 81 | 67 |
| No prices | 883 | 610 | 311 | - | - |
| Not built for phones | 86 | 47 | 85 | 42 | 29 |
| No before/after photos | 701 | - | - | - | - |
| No tap-to-call | 221 | 176 | 261 | 158 | 93 |
| Not secure (no https) | 43 | 28 | 28 | 26 | 13 |

## Smartlead campaigns (emailable, gap confirmed in a real phone browser)
| Campaign | Leads |
|---|---|
| lawn-prices | 254 |
| exterior-before-after | 233 |
| exterior-prices | 139 |
| exterior-other-gaps | 92 |
| lawn-other-gaps | 90 |
| commercial-other-gaps | 82 |
| detailing-prices | 68 |
| detailing-other-gaps | 51 |
| realestate-other-gaps | 35 |
| **Total** | **1044** |

Removed before export: no gap confirmed in browser 39, chain location page 19, site did not load in browser 6. All addresses are still unverified, so `send_ready` is `no` on every row until Reoon runs.

Gap checks are from our script (home page plus up to 2 pricing/booking/contact pages), then confirmed in a phone-sized browser. Gap order follows the marketing review (form, phones, reviews, then the rest). Slow speed is not used as a gap.
