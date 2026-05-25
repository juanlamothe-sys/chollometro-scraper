import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
import json
import time
import re
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="🔥 Chollometro Scraper",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Chollometro Scraper")
st.markdown("Extrae y analiza chollos de cualquier merchant en Chollometro")

# --- MERCHANTS PREDEFINIDOS ---
MERCHANTS = {
    "MediaMarkt (171)": 171,
    "Amazon (11)": 11,
    "PcComponentes (389)": 389,
    "El Corte Inglés (456)": 456,
    "LG (1857)": 1857,
    "Otro (manual)": 0,
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")

    merchant_sel = st.selectbox("🏪 Merchant", options=list(MERCHANTS.keys()))
    if MERCHANTS[merchant_sel] == 0:
        MERCHANT_ID = st.number_input("ID manual", min_value=1, value=171)
    else:
        MERCHANT_ID = MERCHANTS[merchant_sel]

    st.subheader("📅 Rango de fechas")
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Desde", value=date(2026, 1, 1), format="DD/MM/YYYY")
    with col2:
        fecha_fin = st.date_input("Hasta", value=date.today(), format="DD/MM/YYYY")

    if fecha_fin < fecha_inicio:
        st.error("❌ La fecha FIN no puede ser anterior a INICIO")
        st.stop()

    FECHA_INICIO = datetime.combine(fecha_inicio, datetime.min.time())
    FECHA_FIN = datetime.combine(fecha_fin, datetime.max.time())

    iniciar = st.button("🚀 Iniciar Scraping", type="primary", use_container_width=True)

# --- LISTA DE MARCAS ---
MARCAS = [
    'LG', 'Samsung', 'Sony', 'Xiaomi', 'Cecotec', 'Philips', 'Bosch', 'Siemens',
    'Bose', 'JBL', 'Apple', 'HP', 'Lenovo', 'Asus', 'ASUS', 'Acer', 'Dell', 'MSI',
    'Huawei', 'OnePlus', 'OPPO', 'Realme', 'Google', 'Microsoft', 'Nintendo',
    'PlayStation', 'Xbox', 'Dyson', 'Rowenta', 'Tefal', 'Moulinex', 'Braun',
    "Oral-B", 'iRobot', 'Roomba', 'Conga', 'Dreame', 'Roborock', 'Garmin',
    'Fitbit', 'GoPro', 'Canon', 'Nikon', 'Panasonic', 'Hisense', 'TCL',
    'Haier', 'Whirlpool', 'Electrolux', 'AEG', 'Miele', 'Toshiba', 'Sharp',
    'Marshall', 'Sennheiser', 'HyperX', 'Logitech', 'Razer', 'SteelSeries',
    'Corsair', 'TP-Link', 'Netgear', 'Amazon', 'Echo', 'Kindle', 'Ring',
    'Sonos', 'Bang & Olufsen', 'B&O', 'DeWalt', 'Makita', 'Karcher', 'Kärcher',
    'Weber', 'WMF', 'Zwilling', 'KitchenAid', 'Nespresso', "De'Longhi", 'DeLonghi',
    'Krups', 'Tassimo', 'SanDisk', 'Western Digital', 'WD', 'Seagate',
    'Kingston', 'Crucial', 'Intel', 'AMD', 'Nvidia',
    'NanoCell', 'Beats', 'Nothing', 'Motorola', 'Honor',
    'Amazfit', 'Polar', 'Suunto', 'Lego', 'Playmobil', 'Barbie',
    'Hot Wheels', 'Cricut', 'Brother', 'Epson', 'Roidmi', 'Tineco',
    'Creality', 'AnkerMake', 'Anker', 'Soundcore', 'Eufy', 'Jackery', 'Singer',
    'EcoFlow', 'Bluetti', 'Worx', 'Gardena', 'Husqvarna', 'Remington',
    'Babyliss', 'GHD', 'Revlon', 'Shark', 'Ninja', 'Russell Hobbs', 'Fujitsu', 'Polti', 'Taurus',
    'Jata', 'Daitsu', 'Ufesa', 'Funko', 'Sherwood', 'Gigabyte', 'Teka', 'Paladone', 'Balay',
    'AOC', 'KOENIC', 'Midea', 'Pokémon', 'PS5', 'PS4',
    'Smeg', 'Instant Pot', 'Cosori', 'Vitamix', 'hp',
    'Beko', 'Candy', 'Infiniton', 'Magefesa', 'Ariete', 'Kenwood', 'Princess',
    'Jocel', 'Cata', 'Bissell', 'MELLERWARE', 'Laurastar', 'LUMAN',
    'Sage', 'Breville', 'Nutribullet',
    'DJI', 'Insta360', 'Polaroid', 'Fujifilm', 'Nokia',
    'Harman Kardon', 'Ultimate Ears', 'Vieta', 'Shokz', 'PEAQ',
    'Newskill', 'Krom', 'Nilox', 'Evercade', 'MyArcade', 'My Arcade',
    'Pocophone', 'POCO',
    'Belkin', 'Baseus', 'Ugreen', 'CellularLine', 'StarTech',
    'Meta', 'Ray-Ban', 'Oakley', 'Renpho', 'Geske',
    'Segway', 'smartGyro', 'Tado', 'ZIPRO',
    'Wahl', 'Duracell',
    'Targus', 'Case Logic', 'Hama', 'ISY',
    'BRITA', 'BELSON', 'Pyramid', 'InnoGIO',
]

MARCAS_CANONICAL = {
    'asus': 'Asus', 'hp': 'HP',
    "de'longhi": "De'Longhi", 'delonghi': "De'Longhi",
    'karcher': 'Kärcher', 'kärcher': 'Kärcher',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
}


def detectar_marca(titulo):
    mejor_marca = 'Desconocida'
    mejor_pos = len(titulo)
    for marca in MARCAS:
        pattern = r'(?<!\w)' + re.escape(marca) + r'(?!\w)'
        match = re.search(pattern, titulo, re.IGNORECASE)
        if match and match.start() < mejor_pos:
            mejor_pos = match.start()
            mejor_marca = MARCAS_CANONICAL.get(marca.lower(), marca)
    return mejor_marca


# --- SCRAPING (solo cuando se pulsa el botón) ---
if iniciar:
    deals = []
    stop_scraping = False
    skipped_newer = 0
    page = 0

    progress_bar = st.progress(0, text="Iniciando scraping...")
    status_text = st.empty()
    log_container = st.expander("📋 Log de ejecución", expanded=False)

    while not stop_scraping:
        page += 1
        url = f"https://www.chollometro.com/search/ofertas?merchant-id={MERCHANT_ID}&page={page}"
        status_text.info(f"📄 Página {page}... ({len(deals)} chollos recogidos)")
        progress_bar.progress(min(page * 2, 99), text=f"Escaneando página {page}...")

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                log_container.write(f"❌ HTTP {response.status_code} en página {page}. Parando.")
                break
        except Exception as e:
            log_container.write(f"❌ Error en página {page}: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article', class_=lambda c: c and 'thread' in c)

        if not articles:
            log_container.write(f"⚠️ Sin artículos en página {page}. Fin.")
            break

        count = 0
        for article in articles:
            vue_div = article.find('div', attrs={'data-vue3': True})
            if not vue_div:
                continue
            try:
                vue_data = json.loads(vue_div['data-vue3'])
                thread = vue_data.get('props', {}).get('thread', {})
            except (json.JSONDecodeError, KeyError):
                continue

            title = thread.get('title', 'Sin título')
            brand = detectar_marca(title)
            degrees = thread.get('temperature', 0)
            try:
                degrees = round(float(degrees), 1)
            except:
                degrees = 0
            comments = thread.get('commentCount', 0)

            pub_timestamp = thread.get('publishedAt', 0)
            pub_date = None
            if pub_timestamp:
                try:
                    pub_date = datetime.utcfromtimestamp(int(pub_timestamp))
                except:
                    pass

            if pub_date and pub_date > FECHA_FIN:
                skipped_newer += 1
                continue

            if pub_date and pub_date < FECHA_INICIO:
                log_container.write(
                    f"🛑 Chollo del {pub_date.strftime('%d/%m/%Y')} → "
                    f"anterior a {FECHA_INICIO.strftime('%d/%m/%Y')}. Parando."
                )
                stop_scraping = True
                break

            link = thread.get('shareableLink', '')
            if not link:
                slug = thread.get('titleSlug', '')
                thread_id = thread.get('threadId', '')
                link = f"https://www.chollometro.com/ofertas/{slug}-{thread_id}" if slug else ''

            author = thread.get('user', {}).get('username', '')
            status = thread.get('status', '')
            is_expired = thread.get('isExpired', False)
            price = thread.get('price', '')
            next_best_price = thread.get('nextBestPrice', '')
            category = thread.get('mainGroup', {}).get('threadGroupName', '')

            deals.append({
                'Título': title,
                'Marca': brand,
                'Fecha': pub_date.strftime('%Y-%m-%d %H:%M') if pub_date else 'N/A',
                'Autor': author,
                'Grados (°)': degrees,
                'Comentarios': comments,
                'Precio (€)': price,
                'Precio ref. (€)': next_best_price,
                'Categoría': category,
                'Estado': 'Expirado' if is_expired else status,
                'URL': link,
            })
            count += 1

        log_container.write(f"✅ Página {page}: {count} chollos recogidos")
        time.sleep(1.5)

    progress_bar.progress(100, text="✅ Scraping completado!")
    status_text.empty()

    # Guardar en session_state para que sobreviva a los re-renders
    if deals:
        st.session_state['df'] = pd.DataFrame(deals)
        st.session_state['fecha_inicio_str'] = FECHA_INICIO.strftime('%d/%m/%Y')
        st.session_state['fecha_fin_str'] = FECHA_FIN.strftime('%d/%m/%Y')
        st.session_state['merchant_id'] = MERCHANT_ID
    else:
        st.warning("⚠️ No se encontraron chollos en ese rango de fechas.")


# --- MOSTRAR RESULTADOS (siempre que haya datos en session_state) ---
if 'df' in st.session_state and not st.session_state['df'].empty:
    df = st.session_state['df']
    f_inicio = st.session_state.get('fecha_inicio_str', '')
    f_fin = st.session_state.get('fecha_fin_str', '')
    m_id = st.session_state.get('merchant_id', '')

    st.header(f"🎯 {len(df)} chollos encontrados")
    st.caption(f"Del {f_inicio} al {f_fin} | Merchant ID: {m_id}")

    # --- MÉTRICAS ---
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🔥 Grados medio", f"{df['Grados (°)'].mean():.1f}°")
    col2.metric("🏆 Grados máximo", f"{df['Grados (°)'].max()}°")
    col3.metric("💬 Comentarios", f"{df['Comentarios'].sum():,}")
    col4.metric("✅ Activos", len(df[df['Estado'] != 'Expirado']))
    col5.metric("⏰ Expirados", len(df[df['Estado'] == 'Expirado']))

    # --- GRÁFICOS ---
    st.header("📊 Análisis")
    tab1, tab2, tab3 = st.tabs(["🏷️ Marcas", "📅 Evolución", "📂 Categorías"])

    with tab1:
        marca_counts = df['Marca'].value_counts().head(20)
        st.bar_chart(marca_counts)

    with tab2:
        df_temp = df.copy()
        df_temp['Fecha_dt'] = pd.to_datetime(df_temp['Fecha'], errors='coerce')
        df_temp['Semana'] = df_temp['Fecha_dt'].dt.to_period('W').astype(str)
        evolucion = df_temp.groupby('Semana').size()
        st.line_chart(evolucion)

    with tab3:
        cat_counts = df['Categoría'].value_counts().head(15)
        st.bar_chart(cat_counts)

    # --- TABLA CON FILTROS ---
    st.header("📋 Todos los chollos")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        marca_filter = st.multiselect("Filtrar por marca", sorted(df['Marca'].unique()))
    with col_f2:
        cat_filter = st.multiselect("Filtrar por categoría", sorted(df['Categoría'].unique()))
    with col_f3:
        estado_filter = st.multiselect("Filtrar por estado", sorted(df['Estado'].unique()))

    df_filtered = df.copy()
    if marca_filter:
        df_filtered = df_filtered[df_filtered['Marca'].isin(marca_filter)]
    if cat_filter:
        df_filtered = df_filtered[df_filtered['Categoría'].isin(cat_filter)]
    if estado_filter:
        df_filtered = df_filtered[df_filtered['Estado'].isin(estado_filter)]

    st.dataframe(
        df_filtered,
        use_container_width=True,
        column_config={
            "URL": st.column_config.LinkColumn("URL"),
            "Grados (°)": st.column_config.NumberColumn(format="%.1f°"),
        }
    )

    # --- DESCARGA ---
    st.header("💾 Descargar")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        buffer = io.BytesIO()
        df_filtered.to_excel(buffer, index=False, sheet_name='Chollos')
        st.download_button(
            "📥 Descargar Excel",
            data=buffer.getvalue(),
            file_name=f"chollos_{m_id}_{f_inicio.replace('/', '')}_a_{f_fin.replace('/', '')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_dl2:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar CSV",
            data=csv_data,
            file_name=f"chollos_{m_id}_{f_inicio.replace('/', '')}_a_{f_fin.replace('/', '')}.csv",
            mime="text/csv",
            use_container_width=True
        )

elif 'df' not in st.session_state:
    st.markdown("""
    ### 👋 ¡Bienvenido!

    **Cómo usar:**
    1. 🏪 Elige el merchant en el sidebar izquierdo
    2. 📅 Selecciona las fechas de inicio y fin
    3. 🚀 Pulsa **Iniciar Scraping**
    4. 📥 Descarga los resultados en Excel o CSV

    **Merchants populares:**
    | Merchant | ID |
    |---|---|
    | MediaMarkt | 171 |
    | Amazon | 11 |
    | PcComponentes | 389 |
    | El Corte Inglés | 456 |
    | LG | 1857 |
    """)
