# StockGita — Post-Close Market Reset

Private Streamlit dashboard for reviewing market structure after close. It is designed as a **data/education dashboard**, not buy/sell advice.

## What is included

- `streamlit_app.py` — Streamlit dashboard.
- `vcp_engine.py` — VCP/trending/market-structure engine.
- `yahoo_data_downloader.py` — downloads Yahoo OHLCV data into wide CSV files.
- `run_post_close_pipeline.py` — one command to download data and run the engine.
- `.github/workflows/post_close_market_reset.yml` — optional GitHub Actions cron at **4:00 PM IST** on weekdays.
- `data/` — put your `universe_2026.csv` here.
- `outputs/` — engine output CSVs/charts used by the Streamlit app.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Add your universe file:

```text
data/universe_2026.csv
```

Expected columns can follow your current format:

```text
company_name, industry, symbol, Series, sector, ticker, f&o, Include
```

Rows with `Include != 1` are ignored. Plain NSE symbols are converted to `.NS` tickers by the downloader.

## Run the post-close pipeline manually

```bash
python run_post_close_pipeline.py \
  --universe data/universe_2026.csv \
  --price-dir data/yahoo_prices \
  --outputs outputs \
  --period 24mo \
  --chart-scope dashboard
```

This does two things:

1. Downloads Yahoo data into:
   - `data/yahoo_prices/wide_open.csv`
   - `data/yahoo_prices/wide_high.csv`
   - `data/yahoo_prices/wide_low.csv`
   - `data/yahoo_prices/wide_close.csv`
   - `data/yahoo_prices/wide_volume.csv`
2. Runs the engine and writes dashboard files into `outputs/`.

## Run Streamlit

```bash
streamlit run streamlit_app.py
```

## GitHub upload flow

Create a private GitHub repository, then upload these project files.

Recommended: keep `outputs/` committed after every daily run because Streamlit Cloud reads those files directly.

```bash
git init
git add .
git commit -m "Initial private StockGita Streamlit dashboard"
git branch -M main
git remote add origin https://github.com/<user>/<private-repo>.git
git push -u origin main
```

## Automated 4 PM India run

The workflow file is already included:

```text
.github/workflows/post_close_market_reset.yml
```

It runs at:

```text
30 10 * * 1-5 UTC = 4:00 PM IST, Monday-Friday
```

It will:

1. Checkout the repo.
2. Install dependencies.
3. Download Yahoo data.
4. Run the engine.
5. Commit refreshed `data/yahoo_prices/` and `outputs/` back to the repo.

Important GitHub setting:

```text
Repo Settings → Actions → General → Workflow permissions → Read and write permissions
```

Without write permission, the workflow can run but cannot commit updated outputs.

## NSE holiday note

The cron is weekday-based. It does not know NSE holidays. On a holiday, Yahoo may return unchanged/partial data. That is acceptable for a private testing build, but later you can add an NSE holiday calendar check.

## Streamlit Cloud private sharing

1. Keep the GitHub repo private.
2. Deploy from Streamlit Community Cloud or your preferred host.
3. Share the private app link only with selected people.

The top “Today’s Market Story” is deliberately SEBI-safe: it describes market structure and breadth, without giving buy/sell/hold recommendations.
