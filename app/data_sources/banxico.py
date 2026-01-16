import os
from pathlib import Path
import datetime as dt

import requests
import pandas as pd
from dotenv import load_dotenv

# Ruta explícita al .env en la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parents[2]   # Economic_Dashboard/
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
BANXICO_TOKEN = os.getenv("BANXICO_TOKEN")

SERIES_IDS = {
    "tasa_objetivo": "SF61745",
    "tiie_fondeo": "SF331451",
    "tiie_28": "SF43783",
    "cetes_28": "SF60633",
    "fix": "SF43718",
    "reservas": "SF43707",
    # OJO: aquí deben estar tus quincenales correctas:
    "inflacion_general": "SP74833",
    "inflacion_subyacente": "SP74834",
    "udis": "SP68257",
}

_MESES = {
    1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN",
    7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC",
}


def _banxico_request(url: str):
    if not BANXICO_TOKEN:
        raise RuntimeError("No se encontró BANXICO_TOKEN. Revisa tu archivo .env.")
    headers = {"Bmx-Token": BANXICO_TOKEN}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data["bmx"]["series"]


def _parse_fecha_ddmmyyyy(fecha_str: str) -> dt.date | None:
    try:
        return dt.datetime.strptime(fecha_str, "%d/%m/%Y").date()
    except Exception:
        return None


def _format_fecha_portal(fecha: dt.date) -> str:
    # "18 - DIC - 2025"
    return f"{fecha.day:02d} - {_MESES[fecha.month]} - {fecha.year}"


def _format_rango_inflacion_portal(fecha: dt.date) -> str:
    # "1Q DIC - 2024 a 1Q DIC - 2025" (si día <= 15 -> 1Q, si no -> 2Q)
    q = "1Q" if fecha.day <= 15 else "2Q"
    mes = _MESES[fecha.month]
    return f"{q} {mes} - {fecha.year - 1} a {q} {mes} - {fecha.year}"


def get_latest_all() -> pd.DataFrame:
    """
    Trae el último dato DISPONIBLE (<= hoy) de todas las series en SERIES_IDS.
    Además devuelve 'fecha_label' para pintar debajo de la tarjeta (estilo portal).
    """

    from zoneinfo import ZoneInfo

    hoy = dt.datetime.now(ZoneInfo("America/Mexico_City")).date()

    def _ultimo_valido_desde_lista_datos(clave: str, datos: list[dict]) -> tuple[dt.date, float] | None:
        """Recibe serie_dict['datos'] y regresa (fecha, valor) del último dato válido <= hoy."""
        obs_validas = []
        for obs in datos or []:
            f = _parse_fecha_ddmmyyyy(obs.get("fecha", ""))
            if f is None or f > hoy:
                continue

            vraw = obs.get("dato", "")
            if vraw in ("N/E", "", None):
                continue

            try:
                v = float(str(vraw).replace(",", ""))
            except Exception:
                continue

            # Inflación quincenal: decimal -> porcentaje
            if clave in ("inflacion_general", "inflacion_subyacente") and v < 1.0:
                v = v * 100.0

            obs_validas.append((f, v))

        if not obs_validas:
            return None

        obs_validas.sort(key=lambda x: x[0])
        return obs_validas[-1]

    def _fallback_rango(clave: str, serie_id: str) -> tuple[dt.date, float] | None:
        """
        Si 'oportuno' no trae dato, intentamos con rango:
        tomamos el último dato disponible de los últimos 2 años.
        """
        start = (hoy.replace(year=hoy.year - 2)).strftime("%Y-%m-%d")
        end = hoy.strftime("%Y-%m-%d")
        url_rango = f"{BASE_URL}/{serie_id}/datos/{start}/{end}"
        raw = _banxico_request(url_rango)
        if not raw:
            return None
        return _ultimo_valido_desde_lista_datos(clave, raw[0].get("datos", []))

    # 1) Primero: oportuno para todas
    ids = ",".join(SERIES_IDS.values())
    url = f"{BASE_URL}/{ids}/datos/oportuno"
    raw_series = _banxico_request(url)
    series_by_id = {s["idSerie"]: s for s in raw_series}

    rows = []

    for clave, serie_id in SERIES_IDS.items():
        serie_dict = series_by_id.get(serie_id)

        nombre = (serie_dict or {}).get("titulo", clave)

        ultimo = None
        if serie_dict is not None:
            ultimo = _ultimo_valido_desde_lista_datos(clave, serie_dict.get("datos", []))

        # 2) Fallback si no hubo nada válido
        if ultimo is None:
            ultimo = _fallback_rango(clave, serie_id)

        if ultimo is None:
            rows.append(
                {
                    "clave": clave,
                    "serie_id": serie_id,
                    "nombre": nombre,
                    "fecha": None,
                    "valor": None,
                    "fecha_label": "",
                }
            )
            continue

        fecha_ult, valor_ult = ultimo

        if clave in ("inflacion_general", "inflacion_subyacente"):
            fecha_label = _format_rango_inflacion_portal(fecha_ult)
        else:
            fecha_label = _format_fecha_portal(fecha_ult)

        rows.append(
            {
                "clave": clave,
                "serie_id": serie_id,
                "nombre": nombre,
                "fecha": fecha_ult,
                "valor": valor_ult,
                "fecha_label": fecha_label,
            }
        )

    return pd.DataFrame(rows)


def get_series_history(clave: str, start: str = "2015-01-01", end: str | None = None) -> pd.DataFrame:
    """
    Devuelve serie de tiempo para una clave de SERIES_IDS entre start y end.
    Regresa DataFrame con columnas: fecha (datetime), valor (float)
    """
    if clave not in SERIES_IDS:
        raise KeyError(f"Clave no válida: {clave}")

    serie_id = SERIES_IDS[clave]
    if end is None:
        end = dt.date.today().strftime("%Y-%m-%d")

    url = f"{BASE_URL}/{serie_id}/datos/{start}/{end}"
    raw_series = _banxico_request(url)

    if not raw_series:
        return pd.DataFrame(columns=["fecha", "valor"])

    serie_dict = raw_series[0]
    rows = []

    for obs in serie_dict.get("datos", []):
        vraw = obs.get("dato", "")
        if vraw in ("N/E", "", None):
            continue

        try:
            v = float(str(vraw).replace(",", ""))
        except Exception:
            continue

        # inflación: decimal -> porcentaje
        if clave in ("inflacion_general", "inflacion_subyacente") and v < 1.0:
            v = v * 100.0

        rows.append((obs.get("fecha", ""), v))

    df = pd.DataFrame(rows, columns=["fecha", "valor"])
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"]).sort_values("fecha")
    return df
