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


def fetch_page(page_num):
    """Descarga una página y devuelve la soup + artículos. None si falla."""
    url = f"https://www.chollometro.com/search/ofertas?merchant-id={MERCHANT_ID}&page={page_num}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return None, []
    except:
        return None, []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('article', class_=lambda c: c and 'thread' in c)
    return soup, articles


def get_page_first_date(page_num):
    """Obtiene la fecha del primer chollo de una página (la más reciente)."""
    _, articles = fetch_page(page_num)
    for article in articles:
        vue_div = article.find('div', attrs={'data-vue3': True})
        if not vue_div:
            continue
        try:
            vue_data = json.loads(vue_div['data-vue3'])
            thread = vue_data.get('props', {}).get('thread', {})
            pub_timestamp = thread.get('publishedAt', 0)
            if pub_timestamp:
                return datetime.utcfromtimestamp(int(pub_timestamp))
        except:
            continue
    return None


def find_start_page(fecha_fin, log):
    """
    Salto exponencial + búsqueda binaria para encontrar la página
    donde empiezan los chollos dentro del rango de fechas.
    """
    log.write("🔍 **Fase 1: Buscando página de inicio (salto exponencial)...**")

    # --- Paso 1: Salto exponencial (1, 2, 4, 8, 16, 32...) ---
    prev_page = 1
    page = 1
    while True:
        first_date = get_page_first_date(page)
        time.sleep(0.5)

        if first_date is None:
            log.write(f"   Pág {page}: sin datos → fin del merchant")
            return max(1, prev_page)

        log.write(f"   Pág {page}: primer chollo del {first_date.strftime('%d/%m/%Y')}")

        if first_date <= fecha_fin:
            break  # Esta página ya tiene chollos dentro del rango

        prev_page = page
        page *= 2  # Salto exponencial

    # --- Paso 2: Búsqueda binaria entre prev_page y page ---
    lo = prev_page
    hi = page
    log.write(f"🔍 **Fase 2: Búsqueda binaria entre pág {lo} y {hi}...**")

    while lo < hi:
        mid = (lo + hi) // 2
        first_date = get_page_first_date(mid)
        time.sleep(0.5)

        if first_date is None or first_date <= fecha_fin:
            hi = mid
            log.write(f"   Pág {mid}: {first_date.strftime('%d/%m/%Y') if first_date else 'sin datos'} → buscando antes")
        else:
            lo = mid + 1
            log.write(f"   Pág {mid}: {first_date.strftime('%d/%m/%Y')} → aún muy reciente")

    # Retrocedemos 1 página por seguridad (puede haber fechas mezcladas)
    start = max(1, lo - 1)
    log.write(f"✅ **Empezando recolección desde página {start}**")
    return start


def extract_deals_from_articles(articles, fecha_inicio, fecha_fin):
    """Extrae los chollos de los artículos de una página dentro del rango."""
    page_deals = []
    stop = False
    skipped = 0

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

        # Más reciente que FECHA_FIN → saltar
        if pub_date and pub_date > fecha_fin:
            skipped += 1
            continue

        # Más antiguo que FECHA_INICIO → parar
        if pub_date and pub_date < fecha_inicio:
            stop = True
            break

        # Dentro del rango → recoger
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

        page_deals.append({
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

    return page_deals, stop, skipped


# --- SCRAPING (solo cuando se pulsa el botón) ---
if iniciar:
    deals = []
    total_skipped = 0

    progress_bar = st.progress(0, text="Iniciando...")
    status_text = st.empty()
    log_container = st.expander("📋 Log de ejecución", expanded=True)

    # --- FASE 1+2: Encontrar página de inicio con salto exponencial + binaria ---
    status_text.info("🔍 Buscando la página correcta para tu rango de fechas...")
    start_page = find_start_page(FECHA_FIN, log_container)

    # --- FASE 3: Recolección página a página desde start_page ---
    log_container.write(f"📥 **Fase 3: Recolectando chollos desde página {start_page}...**")
    status_text.info(f"📥 Recolectando chollos desde página {start_page}...")

    page = start_page
    stop_scraping = False

    while not stop_scraping:
        progress_bar.progress(min(95, 30 + (page - start_page) * 3), text=f"Página {page}...")
        status_text.info(f"📄 Página {page}... ({len(deals)} chollos recogidos)")

        _, articles = fetch_page(page)

        if not articles:
            log_container.write(f"⚠️ Sin artículos en página {page}. Fin.")
            break

        page_deals, stop_scraping, skipped = extract_deals_from_articles(
            articles, FECHA_INICIO, FECHA_FIN
        )
        deals.extend(page_deals)
        total_skipped += skipped

        log_container.write(
            f"✅ Pág {page}: {len(page_deals)} chollos"
            + (f" | ⏭️ {skipped} saltados" if skipped else "")
            + (" | 🛑 Límite fecha alcanzado" if stop_scraping else "")
        )

        if stop_scraping:
            break

        page += 1
        time.sleep(1.5)

    progress_bar.progress(100, text="✅ Scraping completado!")
    status_text.empty()

    pages_searched = page - start_page + 1
    log_container.write(f"\n📊 **Resumen: {len(deals)} chollos en {pages_searched} páginas escaneadas**")
    if start_page > 1:
        log_container.write(f"⚡ **Optimización: se saltaron {start_page - 1} páginas gracias a la búsqueda binaria**")

    # Guardar en session_state
    if deals:
        st.session_state['df'] = pd.DataFrame(deals)
        st.session_state['fecha_inicio_str'] = FECHA_INICIO.strftime('%d/%m/%Y')
        st.session_state['fecha_fin_str'] = FECHA_FIN.strftime('%d/%m/%Y')
        st.session_state['merchant_id'] = MERCHANT_ID
        st.session_state['pages_skipped'] = start_page - 1
    else:
        st.warning("⚠️ No se encontraron chollos en ese rango de fechas.")


# --- MOSTRAR RESULTADOS (siempre que haya datos en session_state) ---
if 'df' in st.session_state and not st.session_state['df'].empty:
    df = st.session_state['df']
    f_inicio = st.session_state.get('fecha_inicio_str', '')
    f_fin = st.session_state.get('fecha_fin_str', '')
    m_id = st.session_state.get('merchant_id', '')
    pages_skipped = st.session_state.get('pages_skipped', 0)

    st.header(f"🎯 {len(df)} chollos encontrados")
    st.caption(
        f"Del {f_inicio} al {f_fin} | Merchant ID: {m_id}"
        + (f" | ⚡ {pages_skipped} páginas saltadas con búsqueda binaria" if pages_skipped > 0 else "")
    )

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
    """)
