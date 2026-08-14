# Crown Market Monitor v1.2 — Crown Integrated

Cloud-only Streamlit monitor.

## Changes from v1.1
- Daily market changes now compare current price with the previous official daily close.
- FRED Treasury yields are explicitly labelled DAILY.
- Sidebar uploader accepts a Crown results ZIP.
- If the ZIP contains Event-Aware outputs, Crown Now displays the actual strategic gate, deployment percentage, tactical multiplier, event phase, strategic score, and condition states.
- Live market data refresh independently of the uploaded Crown run.

## Streamlit Cloud
Replace the files in the existing GitHub repository with the contents of this folder.
Do not change your existing FRED_API_KEY secret.
