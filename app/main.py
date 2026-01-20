from pathlib import Path
import sys

#  raíz del proyecto en el path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.data_sources import news
import streamlit as st
import pandas as pd
import plotly.express as px

from app.data_sources.banxico import get_latest_all as banxico_latest, get_series_history
from app.data_sources.fred_api import get_latest_all as fred_latest, get_time_series
from app.data_sources import markets


st.set_page_config(page_title="Economic Dashboard", layout="wide")
st.markdown(
    """
    <style>
      .metric-card{
        background:#ffffff;
        border:1px solid #e6e6e6;
        border-radius:12px;
        padding:14px 16px;
        box-shadow:0 1px 2px rgba(0,0,0,.04);
        height: 100%;
      }
      .metric-title{
        font-size:14px;
        font-weight:600;
        color:#111827;
        margin:0 0 6px 0;
      }
      .metric-value{
        font-size:32px;
        font-weight:700;
        color:#0b1220;
        margin:0;
        line-height:1.1;
      }
      .metric-sub{
        font-size:12px;
        color:#6b7280;
        margin-top:8px;
      }
      .section-title{
        font-size:18px;
        font-weight:700;
        margin: 8px 0 2px 0;
      }
      .section-sub{
        color:#6b7280;
        font-size:13px;
        margin:0 0 14px 0;
      }
      .divider{
        margin: 18px 0;
        border-top:1px solid #efefef;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Layout Banxico ----------
from pathlib import Path
import base64
import streamlit as st

def layout_banxico():
    # CSS banner Banxico
    st.markdown(
        """
        <style>
        /* Reduce el espacio superior del contenido principal */
        section.main > div.block-container{
            padding-top: 0.25rem;
        }

        /* Banner: estilo tipo "hero" */
        .banxico-banner{
            margin-top: -1.25rem;   /* sube el banner */
            margin-bottom: 1.25rem;
        }
        .banxico-banner img{
            width: 100%;
            height: 180px;          /* ajusta alto */
            object-fit: cover;
            border-radius: 18px;
            display: block;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Banner 
    banner_path = Path(__file__).resolve().parent / "museo.jpg"  # app/museo.jpg

    if banner_path.exists():
        img_bytes = banner_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        st.markdown(
            f"""
            <div class="banxico-banner">
              <img src="data:image/jpeg;base64,{img_b64}" alt="Banxico banner" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Contenido principal
    st.title("México")
    st.write(
        "Dato oportuno de los principales indicadores de Banco de México, "
        "obtenidos vía API SIE."
    )

    try:
        df = banxico_latest()

        order = [
            "tasa_objetivo",
            "tiie_fondeo",
            "tiie_28",
            "cetes_28",
            "fix",
            "reservas",
            "inflacion_general",
            "inflacion_subyacente",
            "udis",
        ]

        labels = {
            "tasa_objetivo": "Tasa objetivo",
            "tiie_fondeo": "TIIE Fondeo",
            "tiie_28": "TIIE 28",
            "cetes_28": "Cetes 28",
            "fix": "Tipo de cambio FIX",
            "reservas": "Reservas intl. (mill. dls.)",
            "inflacion_general": "Inflación anual (quincenal)",
            "inflacion_subyacente": "Inflación subyacente anual (quincenal)",
            "udis": "UDIS",
        }

        # Validación mínima
        for c in ["clave", "serie_id", "fecha", "valor"]:
            if c not in df.columns:
                raise ValueError(f"Banxico: falta columna requerida '{c}' en el DataFrame.")

        # Ordenar
        df = df.set_index("clave").reindex(order).reset_index()

        st.subheader("Indicadores")
        st.caption(
            "Las cifras de inflación corresponden a variación anual del INPC "
            "con datos quincenales."
        )

        # Tarjetas (3 por fila) 
        cards_per_row = 3
        for i in range(0, len(df), cards_per_row):
            cols = st.columns(cards_per_row)

            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(df):
                    break

                row = df.iloc[idx]
                clave = row["clave"]
                serie_id = row.get("serie_id")
                valor = row.get("valor")
                fecha_raw = row.get("fecha")
                fecha_label = row.get("fecha_label", "")  # viene desde banxico.py

                # Valor formateado"
                if pd.isna(valor):
                    value_str = "N/E"
                else:
                    v = float(valor)

                    if clave in ("inflacion_general", "inflacion_subyacente", "tasa_objetivo", "tiie_fondeo", "cetes_28"):
                        value_str = f"{v:.2f}"
                    elif clave == "tiie_28":
                        value_str = f"{v:.4f}"          
                    elif clave == "reservas":
                        value_str = f"{v:,.1f}".replace(",", "")
                    elif clave == "udis":
                        value_str = f"{v:.6f}"
                    else:
                        value_str = f"{v:.4f}"

                with col:
                    titulo = labels.get(clave, clave)
                    sub = row.get("fecha_label", "") or ""

                    st.markdown(
                  f"""
                  <div class="metric-card">
                 <div class="metric-title">{titulo}</div>
                  <div class="metric-value">{value_str}</div>
                 <div class="metric-sub">{sub}</div>
                 </div>
                  """,
                 unsafe_allow_html=True,
                )

        # Gráfica interactiva
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown("### Serie seleccionada")

        opciones = {
            "Tasa objetivo": "tasa_objetivo",
            "TIIE Fondeo": "tiie_fondeo",
            "TIIE 28": "tiie_28",
            "Cetes 28": "cetes_28",
            "Tipo de cambio FIX": "fix",
            "Reservas internacionales": "reservas",
            "Inflación anual (quincenal)": "inflacion_general",
            "Inflación subyacente anual (quincenal)": "inflacion_subyacente",
            "UDIS": "udis",
        }

        nombre_sel = st.selectbox(
            "Selecciona un indicador para graficar",
            list(opciones.keys()),
            key="banxico_sel_graph",
        )
        clave_sel = opciones[nombre_sel]

        col_a, col_b = st.columns(2)
        with col_a:
            fecha_inicio = st.date_input(
                "Fecha inicial",
                value=pd.to_datetime("2015-01-01").date(),
                key="banxico_start_graph",
            )
        with col_b:
            fecha_fin = st.date_input(
                "Fecha final",
                value=pd.Timestamp.today().date(),
                key="banxico_end_graph",
            )

        if fecha_fin < fecha_inicio:
            st.warning("La fecha final no puede ser menor que la fecha inicial.")
            return

        ts = get_series_history(
            clave_sel,
            start=fecha_inicio.strftime("%Y-%m-%d"),
            end=fecha_fin.strftime("%Y-%m-%d"),
        )

        if ts is None or ts.empty:
            st.info("No hay datos para el periodo seleccionado.")
        else:
            if "fecha" not in ts.columns or "valor" not in ts.columns:
                raise ValueError("Banxico: la serie histórica debe traer columnas ['fecha','valor'].")

            fig = px.line(ts, x="fecha", y="valor", title=nombre_sel)
            fig.update_layout(xaxis_title="Fecha", yaxis_title="Valor")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al cargar datos de Banxico: {e}")

#  ---------- Layout United States (Fed) ----------
def layout_fed():
        # --- CSS banner FED ---
    st.markdown("""
    <style>
    .fed-banner img {
        width: 100%;
        height: 180px;
        object-fit: cover;
        border-radius: 16px;
        margin-bottom: 1.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Banner 
    banner_path = Path(__file__).resolve().parent / "fed_bn.jpg"
    if banner_path.exists():
        st.markdown('<div class="fed-banner">', unsafe_allow_html=True)
        st.image(str(banner_path), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.title("United States")

    st.write(
        "Macroeconomic indicators for the United States obtained from FRED"
        "(St. Louis Fed): policy rate, PCE inflation, unemployment, and real GDP."
    )

    try:
        # Tarjetas principales 
        df = fred_latest()

        order = ["policy_range", "inflation_pce", "unemployment", "gdp_growth"]
        labels = {
            "policy_range": "Fed Funds Target Range",
            "inflation_pce": "Inflation (PCE)",
            "unemployment": "Unemployment Rate",
            "gdp_growth": "Gross Domestic Product (GDP)",
        }

        df = df.set_index("clave").loc[order].reset_index()

        st.subheader("Key indicators – latest available data")
        st.caption("Source: FRED (St. Louis Fed) / Board of Governors / BEA.")

        cols = st.columns(4)
        for i, col in enumerate(cols):
            row = df.iloc[i]
            clave = row["clave"]
            label = labels.get(clave, clave)

            fecha_dt = pd.to_datetime(row["fecha"])

            # Texto de periodo según el tipo de serie
            if clave == "gdp_growth":
                # Real GDP trimestral
                period_str = f"Q{fecha_dt.quarter} {fecha_dt.year}"   # ej. Q2 2025
            elif clave in ("inflation_pce", "unemployment"):
                # Series mensuales
                period_str = fecha_dt.strftime("%B %Y")               # ej. September 2025
            else:
                # Fed funds target range: dejamos fecha exacta
                period_str = fecha_dt.strftime("%Y-%m-%d")

            value_str = row.get("valor_str", f"{row['valor']:.2f}%")

            # Mostrar tarjeta con valor y subtítulo de periodo
            with col:
             st.markdown(
               f"""
             <div class="metric-card">
              <div class="metric-title">{label}</div>
              <div class="metric-value">{value_str}</div>
              <div class="metric-sub">{period_str}</div>
             </div>
              """,
               unsafe_allow_html=True,
             )



        #  Serie seleccionada (gráfica con rango) 
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown("### Serie seleccionada")

        series_options = {
            "Policy rate": "policy_rate",
            "Inflation (PCE)": "inflation_pce",
            "Unemployment Rate": "unemployment",
            "Gross Domestic Product": "gdp_growth",
        }

        nombre_sel = st.selectbox(
            "Selecciona una serie para graficar",
            list(series_options.keys()),
        )
        clave_sel = series_options[nombre_sel]

        col_a, col_b = st.columns(2)
        with col_a:
            start_date = st.date_input(
                "Fecha inicial",
                value=pd.to_datetime("2015-01-01").date(),
            )
        with col_b:
            end_date = st.date_input(
                "Fecha final",
                value=pd.to_datetime("today").date(),
            )

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        ts = get_time_series(clave_sel, start=start_str, end=end_str)

        if ts.empty:
            st.warning("No se encontraron datos para el periodo seleccionado.")
        else:
            fig = px.line(
                ts,
                x="fecha",        # usamos la columna 'fecha'
                y="valor",
                labels={"fecha": "Fecha", "valor": "Valor"},
                title=nombre_sel,
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al cargar datos del FRED: {e}")

def layout_markets():
    st.title("Mercados financieros")
    
    st.info(
    "Nota: Los precios provienen de Yahoo Finance vía yfinance. "
    "Dependiendo del activo y la sesión (Regular / Cierre / After-hours), "
    "pueden existir diferencias pequeñas o un desfase de minutos respecto a la web de Yahoo Finance."
    )

    st.write(
        "Precios y variaciones recientes de índices, criptomonedas,commodities y empresas privadas de alta valoración."
        )

    def _format_table(df):
        if df is None or df.empty:
            return df

        df = df.copy()

        # Renombra session a algo legible en español
        session_map = {
            "Regular": "Regular",
            "Close": "Cierre",
            "After-hours": "After-hours",
        }
        if "session" in df.columns:
            df["session"] = df["session"].astype(str).map(session_map).fillna(df["session"])

        # Formato de números
        if "price" in df.columns:
            # Redondeo inteligente:
            # - crypto/stablecoins: más decimales
            # - commodities: 2-4
            # - índices: 2
            # (sin depender del tipo: usamos heurística por nivel de precio)
            def _fmt_price(x):
                try:
                    x = float(x)
                except Exception:
                    return x
                if x < 5:
                    return round(x, 4)
                if x < 100:
                    return round(x, 2)
                return round(x, 2)

            df["price"] = df["price"].apply(_fmt_price)

        if "change_pct" in df.columns:
            df["change_pct"] = pd.to_numeric(df["change_pct"], errors="coerce").round(2)

        # Orden de columnas si existen
        cols = [c for c in ["name", "ticker", "price", "change_pct", "session"] if c in df.columns]
        df = df[cols]

        # Renombres finales
        rename = {
            "name": "name",
            "ticker": "ticker",
            "price": "price",
            "change_pct": "change_pct",
            "session": "session",
        }
        df = df.rename(columns=rename)

        return df

    def _render(df):
        if df is None or df.empty:
            st.info("No hay datos disponibles por el momento.")
            return

        df_show = _format_table(df)

        # Mostrar con formateo visual (sin cambiar colores)
        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "price": st.column_config.NumberColumn("price"),
                "change_pct": st.column_config.NumberColumn("change_pct", format="%.2f%%"),
                "session": st.column_config.TextColumn("session"),
            },
        )

    col1, col2 = st.columns(2)

    # Columna izquierda: índices y cripto
    with col1:
        st.subheader("Magníficas 7")
        st.caption("Alphabet, Amazon, Apple, Meta, Microsoft, Nvidia y Tesla.")
        try:
            mag7 = markets.get_mag7_table()
            st.dataframe(mag7, width="stretch")
        except Exception as e:
            st.error(f"Error al cargar Magníficas 7: {e}")

        st.subheader("Índices")
        st.caption("Dow Jones, S&P 500, Nasdaq.")
        try:
            indices = markets.get_indices_table()
            _render(indices)
        except Exception as e:
            st.error(f"Error al cargar índices: {e}")

        st.subheader("Criptomonedas")
        st.caption("Bitcoin, Ethereum, Tether.")
        try:
            cryptos = markets.get_crypto_table()
            _render(cryptos)
        except Exception as e:
            st.error(f"Error al cargar criptomonedas: {e}")

    # Columna derecha: commodities
    with col2:
        st.subheader("Commodities")
        st.caption("Oro, Plata, Cobre, Petróleo (WTI/Brent) y Gas natural.")
        try:
            comm = markets.get_commodities_table()
            _render(comm)
        except Exception as e:
            st.error(f"Error al cargar commodities: {e}")
            
        st.subheader("Empresas privadas de alta valoración")
        st.caption("Top 5 (tickers tipo .PVT disponibles en Yahoo Finance).")
        try:
            priv = markets.get_private_companies_table()
            _render(priv)
        except Exception as e:
            st.error(f"Error al cargar private companies: {e}")

def layout_news():
    import streamlit as st

    st.title("Noticias Económicas")
    st.write("Selección de fuentes oficiales para monitoreo en tiempo real.")
    
    # Estilo CSS personalizado para mejorar la apariencia de los hipervínculos
    st.markdown("""
        <style>
        .news-card {
            border-radius: 10px;
            padding: 15px;
            background-color: #f0f2f6;
            margin-bottom: 10px;
            border: 1px solid #e6e9ef;
        }
        .source-title {
            color: #1c3d5a;
            font-weight: bold;
            font-size: 1.2rem;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- FILA 1: REUTERS & BLOOMBERG LÍNEA ---
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("<div class='source-title'> Reuters</div>", unsafe_allow_html=True)
            st.markdown("- [Global Economy](https://www.reuters.com/markets/econ-world/)")
            st.markdown("- [Markets](https://www.reuters.com/markets/)")
            st.markdown("- [Technology](https://www.reuters.com/technology/)")

    with col2:
        with st.container(border=True):
            st.markdown("<div class='source-title'> Bloomberg Línea</div>", unsafe_allow_html=True)
            st.markdown("- [México](https://www.bloomberglinea.com/latinoamerica/mexico/)")
            st.markdown("- [Mercados](https://www.bloomberglinea.com/mercados/)")
            st.markdown("- [Tecnología](https://www.bloomberglinea.com/tecnologia/)")
            st.markdown("- [Latinoamérica](https://www.bloomberglinea.com/latinoamerica/)")
            st.markdown("- [Estados Unidos](https://www.bloomberglinea.com/mundo/estados-unidos/)")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- FILA 2: CNBC & YAHOO FINANCE ---
    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.markdown("<div class='source-title'> CNBC</div>", unsafe_allow_html=True)
            st.markdown("- [Technology](https://www.cnbc.com/technology/)")
            st.markdown("- [Markets](https://www.cnbc.com/markets/)")
            st.markdown("- [Politics](https://www.cnbc.com/politics/)")
            st.markdown("- [Economy](https://www.cnbc.com/economy/)")

    with col4:
        with st.container(border=True):
            st.markdown("<div class='source-title'> Yahoo Finance</div>", unsafe_allow_html=True)
            st.markdown("- [Economy](https://finance.yahoo.com/topic/economic-news/)")
            st.markdown("- [Technology](https://finance.yahoo.com/tech/)")

    st.markdown("<br>", unsafe_allow_html=True)

# --- FILA 3: ING THINK (RESEARCH) ---
col5, col6 = st.columns(2)

with col5:
    with st.container(border=True):
        st.markdown("<div class='source-title'> ING Think)</div>", unsafe_allow_html=True)
        st.markdown("- [Commodities](https://think.ing.com/market/commodities/)")
        st.markdown("- [Commodities, Food & Agri](https://think.ing.com/sector/commodities-food-agri/)")
        st.markdown("- [Energy](https://think.ing.com/sector/energy/)")

    # --- PIE DE PÁGINA O HERRAMIENTAS EXTRAS ---
    st.divider()
    st.caption("Nota: Los enlaces se abren en una nueva pestaña del navegador.")
        
def main():
    import streamlit as st

    st.sidebar.title("Indicadores Económicos")

    page = st.sidebar.radio(
        label="",
        options=("Banxico", "Fed", "Mercados", "Noticias"),
    )

    if page == "Banxico":
        layout_banxico()
    elif page == "Fed":
        layout_fed()
    elif page == "Mercados":
        layout_markets()
    else:
        layout_news()


if __name__ == "__main__":
    main()
