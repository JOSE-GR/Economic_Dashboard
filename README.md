# Economic Dashboard 

Dashboard interactivo de indicadores macroeconómicos de México y Estados Unidos, construido con **Streamlit** y alimentado por datos en tiempo real de la API SIE de Banxico, FRED (Federal Reserve Economic Data) y Yahoo Finance.

🔗 **Link de consulta:** [economic-dashboard-mx.streamlit.app](https://economic-dashboard-mx.streamlit.app/)

---

## Secciones del dashboard

### 🇲🇽 México (Banxico)
Datos obtenidos vía API SIE del Banco de México. Muestra el dato oportuno y series históricas interactivas de:

| Indicador | Serie SIE |
|---|---|
| Tasa objetivo | SF61745 |
| TIIE Fondeo | SF331451 |
| TIIE 28 días | SF43783 |
| Cetes 28 días | SF60633 |
| Tipo de cambio FIX | SF43718 |
| Reservas internacionales | SF43707 |
| Inflación general (quincenal) | SP74833 |
| Inflación subyacente (quincenal) | SP74834 |
| UDIS | SP68257 |

### 🇺🇸 United States (FRED)
Datos de la Reserva Federal vía FRED API:

| Indicador | Serie FRED |
|---|---|
| Fed Funds Target Range | DFEDTARL / DFEDTARU |
| Inflación PCE | PCEPI |
| Tasa de desempleo | UNRATE |
| PIB real (q/q SAAR) | A191RL1Q225SBEA |

### 📈 Mercados financieros (Yahoo Finance)
Precios y variación porcentual en tiempo real de:
- **Magníficas 7:** Apple, Microsoft, Alphabet, Amazon, Nvidia, Meta, Tesla
- **Índices:** Dow Jones, S&P 500, Nasdaq, Russell 2000
- **Criptomonedas:** Bitcoin, Ethereum, Tether
- **Commodities:** Oro, Plata, Cobre, Petróleo WTI, Brent, Gas Natural
- **Empresas privadas:** SpaceX, OpenAI, Anthropic, xAI, Databricks (tickers `.PVT`)

### Noticias Económicas
Acceso directo a secciones de economía y mercados de Reuters, Bloomberg Línea, CNBC, Yahoo Finance e ING Think.

---

## Estructura del proyecto

```
Economic_Dashboard/
├── app/
│   ├── data_sources/
│   │   ├── __init__.py
│   │   ├── banxico.py      # Conexión y parseo de API SIE Banxico
│   │   ├── fred_api.py     # Conexión y parseo de FRED API
│   │   ├── markets.py      # Datos de Yahoo Finance (yfinance)
│   │   └── news.py         # Fuentes de noticias
│   ├── __init__.py
│   ├── main.py             # App principal de Streamlit
│   ├── museo.jpg           # Banner sección México
│   └── fed_bn.jpg          # Banner sección Estados Unidos
├── .vscode/
│   └── settings.json
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Tecnologías

| Librería | Uso |
|---|---|
| `streamlit` | Framework del dashboard |
| `requests` | Llamadas HTTP a Banxico y FRED |
| `pandas` | Manipulación de datos |
| `plotly` | Gráficas interactivas de series históricas |
| `yfinance` | Precios de mercados (Yahoo Finance) |
| `python-dotenv` | Manejo de variables de entorno (API keys) |

---

## Cómo ejecutar localmente

### 1. Clonar el repositorio

```bash
git clone https://github.com/JOSE-GR/Economic_Dashboard.git
cd Economic_Dashboard
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar las API Keys

Crea un archivo `.env` en la **raíz del proyecto** (junto a `requirements.txt`):

```env
BANXICO_TOKEN=tu_token_de_banxico
FRED_API_KEY=tu_api_key_de_fred
```

**¿Cómo obtener cada key?**
- **Banxico SIE:** Regístrate en [https://www.banxico.org.mx/SieAPIRest](https://www.banxico.org.mx/SieAPIRest/service/v1/token) — es gratuita
- **FRED:** Regístrate en [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html) — es gratuita

> ⚠️ El archivo `.env` ya está en `.gitignore`. Nunca lo subas al repositorio.

### 4. Ejecutar la app

```bash
streamlit run app/main.py
```

La app abrirá en `http://localhost:8501`

---

## Ejecutar en GitHub Codespaces

Puedes abrir y editar el proyecto directamente en el navegador sin instalar nada:

1. En la página del repositorio, haz clic en **`<> Code`** → pestaña **Codespaces**
2. Haz clic en **"Create codespace on main"**
3. Una vez que cargue el entorno, en la terminal integrada ejecuta:

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

## APIs utilizadas

| API | Datos | Documentación |
|---|---|---|
| Banxico SIE | Tasas, inflación, FIX, reservas, UDIS | [docs](https://www.banxico.org.mx/SieAPIRest/service/v1/) |
| FRED (St. Louis Fed) | Tasas Fed, PCE, desempleo, PIB | [docs](https://fred.stlouisfed.org/docs/api/fred/) |
| Yahoo Finance (`yfinance`) | Índices, crypto, commodities, acciones | [docs](https://github.com/ranaroussi/yfinance) |

---

## Autor 👤

**JOSE-GR** — [@JOSE-GR](https://github.com/JOSE-GR)

---

Si este proyecto te resulta útil, considera darle una estrella al repositorio.