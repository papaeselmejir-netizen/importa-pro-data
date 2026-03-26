import feedparser
import json
import datetime
import re
import os
from time import mktime

# --- EL RADAR MASIVO DE 15 FUENTES ---
RADARS = {
    'GESTIÓN': "https://gestionalimentaria.com/feed/",
    'EL COMERCIO': "https://elcomercio.pe/arc/outboundfeeds/rss/category/economia/",
    'ANDINA': "https://andina.pe/agencia/rss/economia.aspx",
    'RPP ECON': "https://rpp.pe/feed/economia",
    'PORTAL PORTUARIO': "https://portalportuario.cl/feed/",
    'BLOOMBERG': "https://www.bloomberglinea.com/index.xml",
    'SCMP CHINA': "https://www.scmp.com/rss/318206/feed",
    'REUTERS': "https://www.reutersagency.com/feed/?best-topics=world-news&post_type=best",
    'CNN TRADE': "http://rss.cnn.com/rss/money_news_international.rss",
    'BBC BIZ': "https://feeds.bbci.co.uk/news/business/rss.xml",
    'XATAKA': "https://www.xataka.com/index.xml",
    'TECHCRUNCH': "https://techcrunch.com/feed/",
    'CNET': "https://www.cnet.com/rss/news/",
    'ENGADGET': "https://www.engadget.com/rss.xml",
    'WIRED': "https://www.wired.com/feed/category/business/latest/rss",
    'SUNAT' : "https://news.google.com/rss/search?q=site:gob.pe+SUNAT+Aduanas&hl=es-419&gl=PE&ceid=PE:es-419",
}

# --- DICCIONARIO MAESTRO LUX ---
KEYWORDS = [
    'ADUANA', 'SUNAT', 'VUCE', 'DIGEMID', 'DIGESA', 'SENASA', 'MTC', 'TLC', 
    'HOMOLOGACIÓN', 'PERMISO', 'DÓLAR', 'ARANCEL', 'AD-VALOREM', 'IGV', 'IPM', 
    'PERCEPCIÓN', 'FOB', 'CIF', 'FLETE', 'ROI', 'TAX', 'PUERTO', 'CHANCAY', 
    'CALLAO', 'LOGÍSTICA', 'NAVIERA', 'CONTENEDOR', 'ALMACÉN', 'VISTO BUENO', 
    'HANDLING', 'XIAOMI', 'IPHONE', 'SAMSUNG', 'DRONE', 'SMARTWATCH', 'CELULAR', 
    'TABLET', 'MAQUILLAJE', 'COSMÉTICO', 'VITAMINA', 'SUPLEMENTO', 'JUGUETE', 
    'FUNKO', 'LEGO', 'ZAPATILLAS', 'ROPA', 'TEXTIL', 'CALZADO', 'CHINA', 'USA', 
    'ALIEXPRESS', 'ALIBABA', 'AMAZON', 'SHEIN', 'COURIER', 'SERPOST', 'DHL', 'FEDEX'
]

def clean_text(text):
    if not text: return ""
    # Limpia etiquetas HTML y espacios extra
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    return text.replace('&nbsp;', ' ').replace('&quot;', '"').strip()

def classify(title, desc):
    text = f"{title} {desc}".upper()
    if any(k in text for k in ['VUCE', 'MTC', 'DIGEMID', 'DIGESA', 'SENASA', 'PERMISO', 'HOMOLOGACIÓN']):
        return 'LEGAL'
    if any(k in text for k in ['SUNAT', 'IMPUESTO', 'ARANCEL', 'DÓLAR', 'IGV', 'TAX', 'PERCEPCIÓN']):
        return 'TRIBUTARIO'
    if any(k in text for k in ['PUERTO', 'CHANCAY', 'CALLAO', 'FLETE', 'LOGÍSTICA', 'CONTENEDOR', 'NAVIERA']):
        return 'LOGÍSTICA'
    return 'MERCADO'

def scrape():
    file_path = 'news.json'
    all_news = []
    seen_titles = set()
    
    # --- CONFIGURACIÓN DE TIEMPO (VENTANA DE 3 DÍAS) ---
    ahora = datetime.datetime.now()
    limite_temporal = ahora - datetime.timedelta(days=3)

    # 1. CARGAR NOTICIAS EXISTENTES (Para acumular lo de días anteriores)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                news_archivo = json.load(f)
                # Solo mantenemos las que aún están dentro del límite de 3 días
                for n in news_archivo:
                    fecha_n = datetime.datetime.fromisoformat(n['date'])
                    if fecha_n > limite_temporal:
                        all_news.append(n)
                        seen_titles.add(n['title'])
        except Exception as e:
            print(f"⚠️ No se pudo leer el archivo previo: {e}")

    # 2. ESCANEO DE FUENTES NUEVAS
    for source, url in RADARS.items():
        try:
            print(f"📡 Escaneando: {source}")
            feed = feedparser.parse(url)
            
            # Control de errores en el feed
            if feed.bozo:
                print(f"⚠️ Aviso: Problemas técnicos con {source}, saltando...")
                continue

            for entry in feed.entries[:20]:
                title = entry.get('title', '')
                desc = entry.get('summary', entry.get('description', ''))
                
                # Obtener fecha real de publicación
                if 'published_parsed' in entry:
                    dt_pub = datetime.datetime.fromtimestamp(mktime(entry.published_parsed))
                else:
                    dt_pub = ahora # Si no hay fecha, usamos el momento actual

                # FILTRO 1: ¿Está dentro de la ventana de 3 días?
                if dt_pub < limite_temporal:
                    continue

                # FILTRO 2: Filtro de Palabras Clave (Keywords Lux)
                if any(k in title.upper() or k in desc.upper() for k in KEYWORDS):
                    clean_title = clean_text(title)
                    
                    # FILTRO 3: Evitar Duplicados (por título)
                    if clean_title not in seen_titles:
                        all_news.append({
                            'id': entry.get('id', entry.link),
                            'title': clean_title,
                            'snippet': clean_text(desc)[:220] + "...",
                            'date': dt_pub.isoformat(),
                            'source': source,
                            'url': entry.link,
                            'category': classify(title, desc)
                        })
                        seen_titles.add(clean_title)

        except Exception as e:
            print(f"❌ Error crítico en {source}: {e}")
            continue

    # 3. ORDENAMIENTO Y CIERRE
    # Ordenamos por fecha para que las más recientes aparezcan primero en el JSON
    all_news.sort(key=lambda x: x['date'], reverse=True)

    # Guardamos el resultado (Limitamos a 150 noticias para que la app no sea pesada)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_news[:150], f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Bóveda de Inteligencia actualizada.")
    print(f"📊 Noticias activas (últimas 72h): {len(all_news[:150])}")

if __name__ == "__main__":
    scrape()
