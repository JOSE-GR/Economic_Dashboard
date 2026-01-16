import os
import datetime as dt
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# Cargamos .env desde la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

FRED_SERIES = {
    # Para gráficos / series de tiempo:
    "policy_rate": "FEDFUNDS",              # Federal Funds Effective Rate
    "inflation_pce": "PCEPI",               # PCE price index (lo convertimos a % anual)
    "unemployment": "UNRATE",               # Unemployment rate
    "gdp_growth": "A191RL1Q225SBEA",        # Real GDP, % change from preceding period (quarterly, SAAR)
}


def _fred_series(serie_id: str, start: str = "2015-01-01") -> pd.DataFrame:
    """
    Descarga una serie de FRED desde 'start' hasta hoy.
    Devuelve un DataFrame con índice fecha y columna 'valor'.
    """
    if not FRED_API_KEY:
        raise RuntimeError("No se encontró FRED_API_KEY. Revisa tu archivo .env.")

    params = {
        "series_id": serie_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start,
    }

    resp = requests.get(FRED_BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json().get("observations", [])

    if not data:
        return pd.DataFrame(columns=["fecha", "valor"]).set_index("fecha")

    df = pd.DataFrame(
        [(row["date"], row["value"]) for row in data],
        columns=["fecha", "valor"],
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    # Algunos valores pueden ser "." cuando no hay dato
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df.set_index("fecha", inplace=True)
    return df.sort_index()


def get_latest_all() -> pd.DataFrame:
    """
    Devuelve un DataFrame con los valores más recientes de:
    - Fed funds target range (inferior y superior) en texto
    - Inflación PCE (% anual)
    - Tasa de desempleo (%)
    - PIB real (% variación trimestral anualizada)
    """

    rows = []

    # 1) Fed funds target range (DFEDTARL / DFEDTARU)
    low = _fred_series("DFEDTARL", "2015-01-01")
    up = _fred_series("DFEDTARU", "2015-01-01")
    if not low.empty and not up.empty:
        date = min(low.index.max(), up.index.max())
        low_val = float(low.loc[date, "valor"])
        up_val = float(up.loc[date, "valor"])
        rows.append(
            {
                "clave": "policy_range",
                "nombre": "Fed Funds Target Range",
                "fecha": date.date(),
                "valor": (low_val + up_val) / 2.0,   # valor numérico de referencia
                "valor_str": f"{low_val:.2f}% to {up_val:.2f}%",
            }
        )

    # 2) Inflación PCE (% anual, calculada desde el índice PCEPI)
    pce = _fred_series(FRED_SERIES["inflation_pce"], "2010-01-01")
    if len(pce) >= 13:
        pce = pce.sort_index()
        last_date = pce.index.max()
        last_val = pce.loc[last_date, "valor"]
        prev_series = pce[pce.index <= (last_date - pd.DateOffset(years=1))]
        if not prev_series.empty:
            prev_val = prev_series.iloc[-1]["valor"]
            yoy = (last_val / prev_val - 1.0) * 100.0
            rows.append(
                {
                    "clave": "inflation_pce",
                    "nombre": "Inflation (PCE)",
                    "fecha": last_date.date(),
                    "valor": float(yoy),
                    "valor_str": f"{yoy:.1f}%",
                }
            )

    # 3) Desempleo (%)
    unemp = _fred_series(FRED_SERIES["unemployment"], "2010-01-01")
    if not unemp.empty:
        last_date = unemp.index.max()
        val = float(unemp.loc[last_date, "valor"])
        rows.append(
            {
                "clave": "unemployment",
                "nombre": "Unemployment Rate",
                "fecha": last_date.date(),
                "valor": val,
                "valor_str": f"{val:.2f}%",
            }
        )

    # 4) PIB real – % cambio trimestral anualizado (Real GDP, q/q SAAR)
    gdp = get_time_series("gdp_growth", start="2015-01-01")
    if not gdp.empty:
        last_row = gdp.iloc[-1]
        last_date = last_row["fecha"]
        val = float(last_row["valor"])

        rows.append(
            {
                "clave": "gdp_growth",
                "nombre": "Real GDP (q/q SAAR)",
                "fecha": last_date.date(),
                "valor": val,
                "valor_str": f"{val:.1f}%",
            }
        )

    return pd.DataFrame(rows)

def get_time_series(
    clave: str,
    start: str = "2015-01-01",
    end: str | None = None,
) -> pd.DataFrame:
    """
    Devuelve una serie de tiempo FRED para una clave de FRED_SERIES
    entre 'start' y 'end' (YYYY-MM-DD).
    Retorna un DataFrame con columnas:
    - fecha (datetime)
    - valor (float)
    """
    series_id = FRED_SERIES[clave]

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start,
    }
    if end is not None:
        params["observation_end"] = end

    resp = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()["observations"]

    rows = []
    for obs in data:
        val_raw = obs["value"]
        if val_raw in (".", ""):
            continue
        rows.append((obs["date"], float(val_raw)))

    df = pd.DataFrame(rows, columns=["fecha", "valor"])

    # IMPORTANTÍSIMO: NO poner set_index("fecha") aquí;
    # dejamos 'fecha' como columna para poder usar x="fecha".
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha")

    return df
