import pandas as pd
import yfinance as yf


# Tickers
INDEX_TICKERS = ["^DJI", "^GSPC", "^IXIC", "^RUT"]    # Dow, S&P 500, Nasdaq, Russell 2000
CRYPTO_TICKERS = ["BTC-USD", "ETH-USD", "USDT-USD"]
COMMODITY_TICKERS = ["GC=F", "SI=F", "HG=F", "CL=F", "BZ=F", "NG=F"]
PRIVATE_COMPANY_TICKERS = ["SPAX.PVT", "OPAI.PVT", "ANTH.PVT", "XAAI.PVT", "DATB.PVT"]
MAG7_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]



TICKER_LABELS = {
    "^DJI": "Dow Jones",
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^RUT": "Russell 2000",
    "GC=F": "Gold",
    "SI=F": "Silver",
    "HG=F": "Copper",
    "CL=F": "Crude Oil (WTI)",
    "BZ=F": "Brent Crude",
    "NG=F": "Natural Gas",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "USDT-USD": "Tether",
    "SPAX.PVT": "SpaceX",
    "OPAI.PVT": "OpenAI",
    "ANTH.PVT": "Anthropic",
    "XAAI.PVT": "xAI",
    "DATB.PVT": "Databricks",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "NVDA": "Nvidia",
    "META": "Meta",
    "TSLA": "Tesla",
}

def get_private_companies_table():
    # Top 5 "highest valuation" (según los tickers disponibles en Yahoo/Finance)
    return _latest_price(PRIVATE_COMPANY_TICKERS)


# Helpers

def _safe_float(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _get_daily_close_and_prev(ticker: str):
    """
    Fallback robusto: último close diario y el anterior (para change%).
    """
    try:
        h = yf.Ticker(ticker).history(period="5d", interval="1d", auto_adjust=False)
        if h is None or h.empty or "Close" not in h.columns:
            return None, None
        closes = h["Close"].dropna()
        if closes.empty:
            return None, None
        last_close = float(closes.iloc[-1])
        prev_close = float(closes.iloc[-2]) if len(closes) >= 2 else None
        return last_close, prev_close
    except Exception:
        return None, None


def _pick_session_price(info: dict, ticker: str):
    """
    Regla A:
    - Si mercado abierto: regularMarketPrice y % vs regularMarketPreviousClose
    - Si cerrado: daily close y % vs close anterior
    - After-hours opcional: postMarketPrice en línea extra
    """
    market_state = (info.get("marketState") or "").upper().strip()

    reg_price = _safe_float(info.get("regularMarketPrice"))
    reg_prev_close = _safe_float(info.get("regularMarketPreviousClose"))

    post_price = _safe_float(info.get("postMarketPrice"))
    pre_price = _safe_float(info.get("preMarketPrice"))

    # Determina si "abierto" (REGULAR) o no.
    # Yahoo usa: PRE / REGULAR / POST / CLOSED (a veces "CLOSE" o vacío).
    is_regular = market_state == "REGULAR"

    if is_regular and reg_price is not None:
        price = reg_price
        base = reg_prev_close
        session = "Regular"
    else:
        # Cerrado (o Yahoo no dio regularMarketPrice): usamos close diario real
        last_close, prev_close = _get_daily_close_and_prev(ticker)
        price = last_close if last_close is not None else reg_price
        base = prev_close if prev_close is not None else reg_prev_close
        session = "Close"

    change_pct = None
    if price is not None and base not in (None, 0):
        change_pct = (price / base - 1.0) * 100.0

    # After-hours: solo si Yahoo lo da y es distinto a regular
    after_row = None
    if post_price is not None and reg_price is not None:
        # Evita duplicar si post == reg
        if abs(post_price - reg_price) > 1e-9:
            ah_change_pct = None
            if reg_price not in (None, 0):
                ah_change_pct = (post_price / reg_price - 1.0) * 100.0
            after_row = {
                "price": post_price,
                "change_pct": ah_change_pct,
                "session": "After-hours",
            }

    # (Opcional) Pre-market: si lo quisieras en el futuro, queda listo
    # if pre_price is not None and reg_prev_close is not None:
    #     ...

    return price, change_pct, session, after_row


def _latest_price(tickers):
    rows = []

    for t in tickers:
        name = TICKER_LABELS.get(t, t)
        try:
            tk = yf.Ticker(t)
            info = tk.info or {}
        except Exception:
            info = {}

        price, change_pct, session, after_row = _pick_session_price(info, t)

        if price is None:
            # Si no pudimos obtener nada, lo omitimos para no romper tablas
            continue

        rows.append(
            {
                "name": name,
                "ticker": t,
                "price": float(price),
                "change_pct": float(change_pct) if change_pct is not None else None,
                "session": session,
            }
        )

        # Línea extra After-hours si existe
        if after_row is not None:
            rows.append(
                {
                    "name": f"{name} (After-hours)",
                    "ticker": t,
                    "price": float(after_row["price"]),
                    "change_pct": float(after_row["change_pct"]) if after_row["change_pct"] is not None else None,
                    "session": after_row["session"],
                }
            )

    df = pd.DataFrame(rows)

    # Si quedó vacío, regresa columnas esperadas (evita errores en Streamlit)
    if df.empty:
        return pd.DataFrame(columns=["name", "ticker", "price", "change_pct", "session"])

    # Orden de columnas
    return df[["name", "ticker", "price", "change_pct", "session"]]


# -----------------------
# Public API
# -----------------------
def get_indices_table():
    return _latest_price(INDEX_TICKERS)


def get_crypto_table():
    return _latest_price(CRYPTO_TICKERS)


def get_commodities_table():
    return _latest_price(COMMODITY_TICKERS)

def get_mag7_table():
    return _latest_price(MAG7_TICKERS)

