# GroundWork-Web email marketing

Cold email campaigns for GroundWork-Web, built for Smartlead. Each lead gets one sequence that names a real, checked gap on their website (no quote form, no prices, reviews not shown, not built for phones and so on).

- **Setting up Smartlead:** [SMARTLEAD-SETUP.md](SMARTLEAD-SETUP.md). Nothing launches without Cyrus's go-ahead.
- **Email copy:** [sequences/gap-sequences.md](sequences/gap-sequences.md)
- **Import format:** [templates/smartlead-import-example.csv](templates/smartlead-import-example.csv)
- **Lead files:** `leads/smartlead/` (keep this repo private)

## Importing new leads with Cursor
See [CURSOR-IMPORT.md](CURSOR-IMPORT.md): merges new scrapes with the existing leads, finds each gap, verifies, and loads Smartlead campaigns paused. Scripts are in `tools/`.
