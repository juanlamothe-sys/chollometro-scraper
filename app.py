import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
import json
import time
import re
import io

# --- CONFIGURACION DE PAGINA ---
st.set_page_config(
    page_title="🔥 Chollometro Dashboard",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Chollometro Dashboard")
st.markdown(
    "Extrae y analiza chollos de cualquier merchant "
    "o busqueda en Chollometro"
)

# --- MERCHANTS PREDEFINIDOS ---
MERCHANTS = {
    "Todos (sin filtro)": 0,
    "MediaMarkt (171)": 171,
    "Amazon (173)": 173,
    "PcComponentes (202)": 202,
    "El Corte Ingles (170)": 170,
    "Carrefour (211)": 211,
    "Fnac (192)": 192,
    "Worten (205)": 205,
    "AliExpress (165)": 165,
    "Miravia (7530)": 7530,
    "Temu (7537)": 7537,
    "LG (1857)": 1857,
    "Samsung (256)": 256,
    "Apple (342)": 342,
    "Xiaomi (259)": 259,
    "Otro (manual)": -1,
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuracion")

    modo = st.radio(
        "🔎 Modo de busqueda",
        ["Por Merchant", "Por Keyword / Marca"],
        horizontal=True
    )

    if modo == "Por Merchant":
        merchant_sel = st.selectbox(
            "🏪 Merchant",
            options=[
                k for k in MERCHANTS.keys()
                if k != "Todos (sin filtro)"
            ]
        )
        if MERCHANTS[merchant_sel] == -1:
            MERCHANT_ID = st.number_input(
                "ID manual", min_value=1, value=171
            )
        else:
            MERCHANT_ID = MERCHANTS[merchant_sel]
        SEARCH_QUERY = None

    else:
        SEARCH_QUERY = st.text_input(
            "🔍 Keyword o marca",
            placeholder="Ej: LG, Samsung, iPhone, PS5..."
        )
        merchant_sel = st.selectbox(
            "🏪 Filtrar por retailer (opcional)",
            options=list(MERCHANTS.keys())
        )
        if MERCHANTS[merchant_sel] == -1:
            MERCHANT_ID = st.number_input(
                "ID manual", min_value=1, value=171
            )
        elif MERCHANTS[merchant_sel] == 0:
            MERCHANT_ID = None
        else:
            MERCHANT_ID = MERCHANTS[merchant_sel]

    st.subheader("📅 Rango de fechas")
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input(
            "Desde",
            value=date(2026, 1, 1),
            format="DD/MM/YYYY"
        )
    with col2:
        fecha_fin = st.date_input(
            "Hasta",
            value=date.today(),
            format="DD/MM/YYYY"
        )

    if fecha_fin < fecha_inicio:
        st.error(
            "❌ La fecha FIN no puede ser anterior a INICIO"
        )
        st.stop()

    FECHA_INICIO = datetime.combine(
        fecha_inicio, datetime.min.time()
    )
    FECHA_FIN = datetime.combine(
        fecha_fin, datetime.max.time()
    )

    can_start = False
    if modo == "Por Merchant":
        can_start = True
    elif modo == "Por Keyword / Marca" and SEARCH_QUERY:
        can_start = True

    iniciar = st.button(
        "🚀 Iniciar Scraping",
        type="primary",
        use_container_width=True,
        disabled=not can_start
    )

# --- LISTA DE MARCAS ---
MARCAS = [
    'LG', 'Samsung', 'Sony', 'Xiaomi', 'Cecotec', 'Philips',
    'Bosch', 'Siemens', 'Bose', 'JBL', 'Apple', 'HP', 'Lenovo',
    'Asus', 'ASUS', 'Acer', 'Dell', 'MSI', 'Huawei', 'OnePlus',
    'OPPO', 'Realme', 'Google', 'Microsoft', 'Nintendo',
    'PlayStation', 'Xbox', 'Dyson', 'Rowenta', 'Tefal',
    'Moulinex', 'Braun', "Oral-B", 'iRobot', 'Roomba', 'Conga',
    'Dreame', 'Roborock', 'Garmin', 'Fitbit', 'GoPro', 'Canon',
    'Nikon', 'Panasonic', 'Hisense', 'TCL', 'Haier', 'Whirlpool',
    'Electrolux', 'AEG', 'Miele', 'Toshiba', 'Sharp', 'Marshall',
    'Sennheiser', 'HyperX', 'Logitech', 'Razer', 'SteelSeries',
    'Corsair', 'TP-Link', 'Netgear', 'Amazon', 'Echo', 'Kindle',
    'Ring', 'Sonos', 'Bang & Olufsen', 'B&O', 'DeWalt', 'Makita',
    'Karcher', 'Kärcher', 'Weber', 'WMF', 'Zwilling',
    'KitchenAid', 'Nespresso', "De'Longhi", 'DeLonghi', 'Krups',
    'Tassimo', 'SanDisk', 'Western Digital', 'WD', 'Seagate',
    'Kingston', 'Crucial', 'Intel', 'AMD', 'Nvidia',
    'Beats', 'Nothing', 'Motorola', 'Honor', 'Amazfit', 'Polar',
    'Suunto', 'Lego', 'Playmobil', 'Barbie', 'Hot Wheels',
    'Cricut', 'Brother', 'Epson', 'Roidmi', 'Tineco', 'Creality',
    'AnkerMake', 'Anker', 'Soundcore', 'Eufy', 'Jackery',
    'Singer', 'EcoFlow', 'Bluetti', 'Worx', 'Gardena',
    'Husqvarna', 'Remington', 'Babyliss', 'GHD', 'Revlon',
    'Shark', 'Ninja', 'Russell Hobbs', 'Fujitsu', 'Polti',
    'Taurus', 'Jata', 'Daitsu', 'Ufesa', 'Funko', 'Sherwood',
    'Gigabyte', 'Teka', 'Paladone', 'Balay', 'AOC', 'KOENIC',
    'Midea', 'Pokémon', 'PS5', 'PS4', 'Smeg', 'Instant Pot',
    'Cosori', 'Vitamix', 'hp', 'Beko', 'Candy', 'Infiniton',
    'Magefesa', 'Ariete', 'Kenwood', 'Princess', 'Jocel', 'Cata',
    'Bissell', 'MELLERWARE', 'Laurastar', 'LUMAN', 'Sage',
    'Breville', 'Nutribullet', 'DJI', 'Insta360', 'Polaroid',
    'Fujifilm', 'Nokia', 'Harman Kardon', 'Ultimate Ears',
    'Vieta', 'Shokz', 'PEAQ', 'Newskill', 'Krom', 'Nilox',
    'Evercade', 'MyArcade', 'My Arcade', 'Pocophone', 'POCO',
    'Belkin', 'Baseus', 'Ugreen', 'CellularLine', 'StarTech',
    'Meta', 'Ray-Ban', 'Oakley', 'Renpho', 'Geske', 'Segway',
    'smartGyro', 'Tado', 'ZIPRO', 'Wahl', 'Duracell', 'Targus',
    'Case Logic', 'Hama', 'ISY', 'BRITA', 'BELSON', 'Pyramid',
    'InnoGIO',
]

MARCAS_CANONICAL = {
    'asus': 'Asus',
    'hp': 'HP',
    "de'longhi": "De'Longhi",
    'delonghi': "De'Longhi",
    'karcher': 'Kärcher',
    'kärcher': 'Kärcher',
}

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36'
    ),
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
            mejor_marca = MARCAS_CANONICAL.get(
                marca.lower(), marca
            )
    return mejor_marca


def build_url(page_num):
    """Construye la URL segun el modo de busqueda."""
    if SEARCH_QUERY:
        query_encoded = SEARCH_QUERY.replace(" ", "+")
        url = (
            "https://www.chollometro.com/search"
            "?q=" + query_encoded
        )
        if MERCHANT_ID:
            url = url + "&merchant-id=" + str(MERCHANT_ID)
        url = url + "&page=" + str(page_num)
        return url
    else:
        return (
            "https://www.chollometro.com/search/ofertas"
            "?merchant-id=" + str(MERCHANT_ID)
            + "&page=" + str(page_num)
        )


def fetch_page(page_num):
    """Descarga una pagina y devuelve los articulos."""
    url = build_url(page_num)
    try:
        response = requests.get(
            url, headers=HEADERS, timeout=15
        )
        if response.status_code != 200:
            return []
    except Exception:
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.find_all(
        'article', class_=lambda c: c and 'thread' in c
    )


def get_page_dates(page_num):
    """Devuelve (primera_fecha, ultima_fecha) de una pagina."""
    articles = fetch_page(page_num)
    dates = []
    for article in articles:
        vue_div = article.find(
            'div', attrs={'data-vue3': True}
        )
        if not vue_div:
            continue
        try:
            vue_data = json.loads(vue_div['data-vue3'])
            thread = vue_data.get('props', {}).get(
                'thread', {}
            )
            ts = thread.get('publishedAt', 0)
            if ts:
                dates.append(
                    datetime.utcfromtimestamp(int(ts))
                )
        except Exception:
            continue
    if not dates:
        return None, None
    return max(dates), min(dates)


def find_page_boundary(target_date, direction, max_page, log):
    """Salto exponencial + busqueda binaria."""
    label = "inicio" if direction == "start" else "final"
    target_str = target_date.strftime('%d/%m/%Y')
    log.write(
        "🔍 Buscando pagina **" + label
        + "** (fecha objetivo: " + target_str + ")..."
    )

    prev = 1
    page = 1
    while page <= max_page:
        first_date, last_date = get_page_dates(page)
        time.sleep(0.5)

        if first_date is None:
            log.write("   Pag " + str(page) + ": sin datos")
            break

        first_str = first_date.strftime('%d/%m')
        last_str = last_date.strftime('%d/%m')
        log.write(
            "   Pag " + str(page) + ": "
            + first_str + " -> " + last_str
        )

        if direction == 'start':
            if first_date <= target_date:
                break
        else:
            if last_date < target_date:
                break

        prev = page
        page = min(page * 2, max_page + 1)

    if page > max_page:
        page = max_page

    lo = prev
    hi = page
    log.write(
        "   🔎 Binaria entre pag "
        + str(lo) + " y " + str(hi) + "..."
    )

    while lo < hi:
        mid = (lo + hi) // 2
        first_date, last_date = get_page_dates(mid)
        time.sleep(0.5)

        if first_date is None:
            hi = mid
            continue

        if direction == 'start':
            if first_date <= target_date:
                hi = mid
            else:
                lo = mid + 1
        else:
            if last_date >= target_date:
                lo = mid + 1
            else:
                hi = mid

    if direction == 'start':
        result = max(1, lo - 1)
    else:
        result = lo

    log.write(
        "   ✅ Pagina " + label + ": **" + str(result) + "**"
    )
    return result


def extract_deals_from_articles(articles, fecha_inicio, fecha_fin):
    """Extrae los chollos dentro del rango de una pagina."""
    page_deals = []
    stop = False
    skipped = 0

    for article in articles:
        vue_div = article.find(
            'div', attrs={'data-vue3': True}
        )
        if not vue_div:
            continue
        try:
            vue_data = json.loads(vue_div['data-vue3'])
            thread = vue_data.get('props', {}).get(
                'thread', {}
            )
        except (json.JSONDecodeError, KeyError):
            continue

        title = thread.get('title', 'Sin titulo')
        brand = detectar_marca(title)
        degrees = thread.get('temperature', 0)
        try:
            degrees = round(float(degrees), 1)
        except Exception:
            degrees = 0
        comments = thread.get('commentCount', 0)

        pub_timestamp = thread.get('publishedAt', 0)
        pub_date = None
        if pub_timestamp:
            try:
                pub_date = datetime.utcfromtimestamp(
                    int(pub_timestamp)
                )
            except Exception:
                pass

        if pub_date and pub_date > fecha_fin:
            skipped += 1
            continue

        if pub_date and pub_date < fecha_inicio:
            stop = True
            break

        link = thread.get('shareableLink', '')
        if not link:
            slug = thread.get('titleSlug', '')
            thread_id = thread.get('threadId', '')
            if slug:
                link = (
                    "https://www.chollometro.com/ofertas/"
                    + slug + "-" + str(thread_id)
                )

        author = thread.get('user', {}).get('username', '')
        status = thread.get('status', '')
        is_expired = thread.get('isExpired', False)
        price = thread.get('price', '')
        next_best_price = thread.get('nextBestPrice', '')
        category_data = thread.get('mainGroup', {})
        category = category_data.get('threadGroupName', '')
        merchant_data = thread.get('merchant', {})
        merchant_name = merchant_data.get('merchantName', '')

        if pub_date:
            fecha_str = pub_date.strftime('%Y-%m-%d %H:%M')
        else:
            fecha_str = 'N/A'

        if is_expired:
            estado = 'Expirado'
        else:
            estado = status

        page_deals.append({
            'Titulo': title,
            'Marca': brand,
            'Retailer': merchant_name,
            'Fecha': fecha_str,
            'Autor': author,
            'Grados': degrees,
            'Comentarios': comments,
            'Precio': price,
            'Precio ref.': next_best_price,
            'Categoria': category,
            'Estado': estado,
            'URL': link,
        })

    return page_deals, stop, skipped


# --- SCRAPING ---
if iniciar:
    deals = []

    progress_bar = st.progress(0, text="Iniciando...")
    status_text = st.empty()
    log_container = st.expander(
        "📋 Log de ejecucion", expanded=True
    )

    # Mostrar que estamos buscando
    if SEARCH_QUERY:
        search_desc = "Keyword: " + SEARCH_QUERY
        if MERCHANT_ID:
            search_desc = (
                search_desc + " | Retailer ID: "
                + str(MERCHANT_ID)
            )
    else:
        search_desc = "Merchant ID: " + str(MERCHANT_ID)

    log_container.write("🔎 **" + search_desc + "**")

    MAX_PAGE_LIMIT = 500

    status_text.info(
        "🔍 Fase 1/3: Buscando pagina de inicio..."
    )
    progress_bar.progress(5, text="Buscando pagina de inicio...")
    start_page = find_page_boundary(
        FECHA_FIN, 'start', MAX_PAGE_LIMIT, log_container
    )

    status_text.info(
        "🔍 Fase 2/3: Buscando pagina final..."
    )
    progress_bar.progress(15, text="Buscando pagina final...")
    end_page = find_page_boundary(
        FECHA_INICIO, 'end', MAX_PAGE_LIMIT, log_container
    )

    end_page = max(end_page, start_page)
    end_page = min(end_page + 2, MAX_PAGE_LIMIT)

    total_pages = end_page - start_page + 1
    log_container.write(
        "\n📐 **Rango: pag " + str(start_page)
        + " -> " + str(end_page)
        + " (" + str(total_pages) + " paginas)**"
    )

    status_text.info(
        "📥 Fase 3/3: Recolectando chollos..."
    )
    log_container.write("📥 **Fase 3: Recolectando...**")

    for i, page in enumerate(range(start_page, end_page + 1)):
        pct = 20 + int(75 * (i / total_pages))
        pct = min(pct, 95)
        progress_bar.progress(
            pct,
            text=(
                "Pagina " + str(page) + "/" + str(end_page)
                + " (" + str(len(deals)) + " chollos)"
            )
        )
        status_text.info(
            "📄 Pagina " + str(page) + "/" + str(end_page)
            + "... (" + str(len(deals)) + " chollos)"
        )

        articles = fetch_page(page)

        if not articles:
            log_container.write(
                "⚠️ Pag " + str(page) + ": sin articulos"
            )
            continue

        page_deals, should_stop, skipped = (
            extract_deals_from_articles(
                articles, FECHA_INICIO, FECHA_FIN
            )
        )
        deals.extend(page_deals)

        msg = (
            "✅ Pag " + str(page) + ": "
            + str(len(page_deals)) + " chollos"
        )
        if skipped:
            msg = msg + " | ⏭️ " + str(skipped) + " saltados"
        if should_stop:
            msg = msg + " | 🛑 Limite fecha"
        log_container.write(msg)

        if should_stop:
            break

        time.sleep(1.5)

    progress_bar.progress(100, text="✅ Scraping completado!")
    status_text.empty()

    log_container.write("=" * 50)
    log_container.write(
        "📊 **Resultado: " + str(len(deals)) + " chollos**"
    )

    if deals:
        st.session_state['df'] = pd.DataFrame(deals)
        st.session_state['fecha_inicio_str'] = (
            FECHA_INICIO.strftime('%d/%m/%Y')
        )
        st.session_state['fecha_fin_str'] = (
            FECHA_FIN.strftime('%d/%m/%Y')
        )
        st.session_state['merchant_id'] = MERCHANT_ID
        st.session_state['search_query'] = SEARCH_QUERY
        st.session_state['start_page'] = start_page
        st.session_state['end_page'] = end_page
    else:
        st.warning(
            "⚠️ No se encontraron chollos en ese rango."
        )


# --- MOSTRAR RESULTADOS ---
if 'df' in st.session_state and not st.session_state['df'].empty:
    df = st.session_state['df']
    f_inicio = st.session_state.get('fecha_inicio_str', '')
    f_fin = st.session_state.get('fecha_fin_str', '')
    m_id = st.session_state.get('merchant_id', '')
    s_query = st.session_state.get('search_query', '')
    s_page = st.session_state.get('start_page', 1)
    e_page = st.session_state.get('end_page', 1)

    if s_query:
        search_label = "Busqueda: " + s_query
        if m_id:
            search_label = (
                search_label + " | Retailer: " + str(m_id)
            )
    else:
        search_label = "Merchant: " + str(m_id)

    st.header("🎯 " + str(len(df)) + " chollos encontrados")
    st.caption(
        "Del " + f_inicio + " al " + f_fin + " | "
        + search_label + " | "
        + "Pags " + str(s_page) + " -> " + str(e_page)
    )

    # --- FILTROS ---
    st.header("🔎 Filtros")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        marca_filter = st.multiselect(
            "Filtrar por marca",
            sorted(df['Marca'].unique())
        )
    with col_f2:
        cat_filter = st.multiselect(
            "Filtrar por categoria",
            sorted(df['Categoria'].unique())
        )
    with col_f3:
        estado_filter = st.multiselect(
            "Filtrar por estado",
            sorted(df['Estado'].unique())
        )
    with col_f4:
        retailer_filter = st.multiselect(
            "Filtrar por retailer",
            sorted(df['Retailer'].unique())
        )

    df_filtered = df.copy()
    if marca_filter:
        df_filtered = df_filtered[
            df_filtered['Marca'].isin(marca_filter)
        ]
    if cat_filter:
        df_filtered = df_filtered[
            df_filtered['Categoria'].isin(cat_filter)
        ]
    if estado_filter:
        df_filtered = df_filtered[
            df_filtered['Estado'].isin(estado_filter)
        ]
    if retailer_filter:
        df_filtered = df_filtered[
            df_filtered['Retailer'].isin(retailer_filter)
        ]

    any_filter = (
        marca_filter or cat_filter
        or estado_filter or retailer_filter
    )
    if any_filter:
        st.caption(
            "📌 Mostrando " + str(len(df_filtered))
            + " de " + str(len(df)) + " chollos"
        )

    # --- METRICAS ---
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(
        "🔥 Grados medio",
        str(round(df_filtered['Grados'].mean(), 1)) + "°"
    )
    col2.metric(
        "🏆 Grados maximo",
        str(df_filtered['Grados'].max()) + "°"
    )
    col3.metric(
        "💬 Comentarios",
        str(df_filtered['Comentarios'].sum())
    )
    col4.metric(
        "✅ Activos",
        len(df_filtered[df_filtered['Estado'] != 'Expirado'])
    )
    col5.metric(
        "⏰ Expirados",
        len(df_filtered[df_filtered['Estado'] == 'Expirado'])
    )

    # --- GRAFICOS ---
    st.header("📊 Analisis")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🏷️ Marcas", "📅 Evolucion",
         "📂 Categorias", "🏪 Retailers"]
    )

    with tab1:
        marca_counts = (
            df_filtered['Marca'].value_counts().head(20)
        )
        st.bar_chart(marca_counts)

    with tab2:
        df_temp = df_filtered.copy()
        df_temp['Fecha_dt'] = pd.to_datetime(
            df_temp['Fecha'], errors='coerce'
        )
        df_temp['Semana'] = (
            df_temp['Fecha_dt'].dt.to_period('W').astype(str)
        )
        evolucion = df_temp.groupby('Semana').size()
        st.line_chart(evolucion)

    with tab3:
        cat_counts = (
            df_filtered['Categoria'].value_counts().head(15)
        )
        st.bar_chart(cat_counts)

    with tab4:
        retailer_counts = (
            df_filtered['Retailer'].value_counts().head(15)
        )
        st.bar_chart(retailer_counts)

    # --- TABLA ---
    st.header("📋 Todos los chollos")
    st.dataframe(
        df_filtered,
        use_container_width=True,
        column_config={
            "URL": st.column_config.LinkColumn("URL"),
            "Grados": st.column_config.NumberColumn(
                format="%.1f°"
            ),
        }
    )

    # --- DESCARGA ---
    st.header("💾 Descargar")

    safe_inicio = f_inicio.replace('/', '')
    safe_fin = f_fin.replace('/', '')
    if s_query:
        safe_query = s_query.replace(' ', '_')
        base_filename = (
            "chollos_" + safe_query
            + "_" + safe_inicio
            + "_a_" + safe_fin
        )
    else:
        base_filename = (
            "chollos_" + str(m_id)
            + "_" + safe_inicio
            + "_a_" + safe_fin
        )

    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        buffer = io.BytesIO()
        df_filtered.to_excel(
            buffer, index=False, sheet_name='Chollos'
        )
        st.download_button(
            "📥 Descargar Excel",
            data=buffer.getvalue(),
            file_name=base_filename + ".xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True
        )

    with col_dl2:
        csv_data = df_filtered.to_csv(
            index=False
        ).encode('utf-8')
        st.download_button(
            "📥 Descargar CSV",
            data=csv_data,
            file_name=base_filename + ".csv",
            mime="text/csv",
            use_container_width=True
        )

elif 'df' not in st.session_state:
    st.markdown(
        """
        ### 👋 Bienvenido!

        **Como usar:**
        1. 🔎 Elige modo: **Por Merchant** o **Por Keyword/Marca**
        2. 🏪 Opcionalmente filtra por retailer
        3. 📅 Selecciona fechas
        4. 🚀 Pulsa **Iniciar Scraping**
        5. 📥 Descarga en Excel o CSV

        **Merchants populares:**
        | Merchant |
        |---|---|
        | MediaMarkt |
        | Amazon | 
        | PcComponentes |
        | El Corte Ingles |
        | Carrefour |
        | Fnac | 

        **Busquedas de ejemplo:**
        | Keyword | Que busca |
        |---|---|
        | LG | Todos los chollos de LG |
        | iPhone | Ofertas de iPhone |
        | PS5 | Chollos de PlayStation 5 |
        | portatil | Ofertas de portatiles |
        | LG + MediaMarkt | Chollos LG solo en MediaMarkt |
        """
    )
