# Crown Market Monitor v1.1 — Live MVP

Live MVP:
- Crown Now
- Cross-Asset
- State Explorer

## Data
- Yahoo market data through `yfinance` (research/MVP feed)
- FRED rates through the official FRED API
- Streamlit secret: `FRED_API_KEY`

## Deploy
Upload the contents of this folder to the existing GitHub repository, replacing the previous files.
Streamlit Community Cloud should automatically rebuild the app.

## Notes
The live state engine is intentionally conservative. Only a few high-confidence Crown rules are active.
Full Crown-v2.1 state integration is the next step.
