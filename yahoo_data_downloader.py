from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import yfinance as yf

OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def _find_col(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    lookup = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().lower().replace(" ", "_")
        if key in lookup:
            return lookup[key]
    return None


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    try:
        if pd.isna(value):
            return False
    except Exception:
        pass
    return str(value).strip().lower() in {"1", "true", "yes", "y", "include", "included"}


def normalize_yahoo_ticker(value: str, symbol: str | None = None, suffix: str = ".NS") -> str:
    ticker = str(value or "").strip().upper()
    sym = str(symbol or "").strip().upper()
    if ticker and ticker not in {"NAN", "NONE"}:
        if ticker.startswith("^") or "." in ticker:
            return ticker
        return f"{ticker}{suffix}"
    if sym and sym not in {"NAN", "NONE"}:
        if sym.startswith("^") or "." in sym:
            return sym
        return f"{sym}{suffix}"
    return ""


def load_universe_tickers(universe_path: Path, ticker_suffix: str = ".NS") -> List[str]:
    df = pd.read_csv(universe_path, sep=None, engine="python")
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]

    include_col = _find_col(df, ["Include", "include", "include_signal", "include signal"])
    if include_col is not None:
        before = len(df)
        df = df[df[include_col].apply(_truthy)].copy()
        print(f"Universe Include filter: {before:,} -> {len(df):,}")

    series_col = _find_col(df, ["Series", "series"])
    if series_col is not None:
        df = df[df[series_col].astype(str).str.upper().str.strip().eq("EQ")].copy()

    ticker_col = _find_col(df, ["ticker", "Ticker", "Yahoo Ticker"])
    symbol_col = _find_col(df, ["symbol", "Symbol", "SYMBOL"])
    if ticker_col is None and symbol_col is None:
        raise ValueError(f"Universe must contain ticker or symbol column. Found: {list(df.columns)}")

    tickers = []
    for _, row in df.iterrows():
        ticker = normalize_yahoo_ticker(row.get(ticker_col, "") if ticker_col else "", row.get(symbol_col, "") if symbol_col else "", suffix=ticker_suffix)
        if ticker:
            tickers.append(ticker)
    return list(dict.fromkeys(tickers))


def flatten_yfinance_download(raw: pd.DataFrame, tickers: List[str]) -> dict[str, pd.DataFrame]:
    parsed: dict[str, pd.DataFrame] = {}
    if raw.empty:
        return parsed

    if isinstance(raw.columns, pd.MultiIndex):
        # yfinance can return either first level=ticker or first level=field.
        level0 = list(raw.columns.get_level_values(0).unique())
        level1 = list(raw.columns.get_level_values(1).unique())
        if any(t in level0 for t in tickers):
            for t in tickers:
                if t in level0:
                    df = raw[t].copy()
                    if not df.dropna(how="all").empty:
                        parsed[t] = df.rename(columns=str.title)
        elif any(t in level1 for t in tickers):
            for t in tickers:
                if t in level1:
                    df = raw.xs(t, axis=1, level=1).copy()
                    if not df.dropna(how="all").empty:
                        parsed[t] = df.rename(columns=str.title)
    else:
        if len(tickers) == 1:
            parsed[tickers[0]] = raw.copy().rename(columns=str.title)
    return parsed


def download_prices(tickers: List[str], period: str, interval: str, batch_size: int) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    failed: list[str] = []
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        print(f"Downloading batch {i // batch_size + 1}: {len(batch)} tickers")
        try:
            raw = yf.download(
                batch,
                period=period,
                interval=interval,
                auto_adjust=True,
                group_by="ticker",
                threads=False,
                progress=False,
            )
            parsed = flatten_yfinance_download(raw, batch)
            out.update(parsed)
            failed.extend([t for t in batch if t not in parsed])
        except Exception as exc:
            print(f"Batch failed: {exc}")
            failed.extend(batch)

    # Fallback one-by-one. Slower but improves reliability.
    for t in list(dict.fromkeys(failed)):
        if t in out:
            continue
        try:
            df = yf.Ticker(t).history(period=period, interval=interval, auto_adjust=True)
            df = df.rename(columns=str.title).dropna(how="all")
            if not df.empty:
                out[t] = df
                print(f"Recovered {t}")
        except Exception as exc:
            print(f"Failed {t}: {exc}")
    return out


def write_wide_csv(price_data: dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_dates = sorted(set().union(*[set(df.index.tz_localize(None).normalize()) if getattr(df.index, 'tz', None) is not None else set(pd.to_datetime(df.index).tz_localize(None).normalize()) for df in price_data.values()]))
    if not all_dates:
        raise RuntimeError("No price dates downloaded.")

    for field in OHLCV:
        wide = pd.DataFrame(index=pd.DatetimeIndex(all_dates, name="date"))
        for ticker, df in price_data.items():
            if field not in df.columns:
                continue
            s = df[field].copy()
            s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
            wide[ticker.upper()] = pd.to_numeric(s, errors="coerce")
        wide = wide.sort_index().reset_index()
        wide.to_csv(output_dir / f"wide_{field.lower()}.csv", index=False)
        print(f"Saved {output_dir / f'wide_{field.lower()}.csv'}: {wide.shape[0]:,} rows x {wide.shape[1]-1:,} tickers")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Yahoo prices into wide CSV files for the VCP engine.")
    parser.add_argument("--universe", default="data/universe_2026.csv", help="Universe CSV path.")
    parser.add_argument("--outdir", default="data/yahoo_prices", help="Output folder for wide_open/high/low/close/volume CSVs.")
    parser.add_argument("--period", default="24mo", help="Yahoo period, e.g. 24mo, 5y, max.")
    parser.add_argument("--interval", default="1d", help="Yahoo interval. Default: 1d")
    parser.add_argument("--market-index", default="^NSEI", help="Benchmark ticker to include. Default: ^NSEI")
    parser.add_argument("--batch-size", type=int, default=40, help="Download batch size.")
    parser.add_argument("--ticker-suffix", default=".NS", help="Suffix added when universe has plain NSE symbols.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    universe_path = Path(args.universe)
    if not universe_path.exists():
        raise FileNotFoundError(f"Universe file not found: {universe_path}. Put universe_2026.csv in data/ or pass --universe.")

    tickers = load_universe_tickers(universe_path, ticker_suffix=args.ticker_suffix)
    if args.market_index:
        tickers = list(dict.fromkeys(tickers + [args.market_index.upper()]))
    print(f"Downloading {len(tickers):,} total series including benchmark.")

    price_data = download_prices(tickers, args.period, args.interval, args.batch_size)
    print(f"Downloaded usable data for {len(price_data):,}/{len(tickers):,} series.")
    if args.market_index.upper() not in {t.upper() for t in price_data}:
        raise RuntimeError(f"Benchmark {args.market_index} was not downloaded. Engine needs it in the wide price folder.")

    write_wide_csv(price_data, Path(args.outdir))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
