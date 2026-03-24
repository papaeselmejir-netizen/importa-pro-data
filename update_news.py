import feedparser
import json
import datetime

# Radares estratégicos para IMPORTA PRO
RADARS = {
    'GESTIÓN': "https://gestionalimentaria.com/feed/",
    'ANDINA': "https://andina.pe/agencia/rss/economia.aspx",
    'RPP ECON': "https://rpp.pe/feed/economia",
    'PORTAL PORTUARIO': "https://portalportuario.cl/feed/",
    'XATAKA': "https://www.xataka.com/index.xml"
}

KEYWORDS = ['ADUANA', 'SUNAT', 'VUCE', 'MTC', 'ARANCEL', 'CHANCAY', 'CALLAO', 'IMPORTA', 'DÓLAR', 'CHINA', 'FLETE']

def classify(title, desc):
    text = f"{title} {desc}".upper()
    if any(k in text for k in ['VUCE', 'MTC', 'DIGEMID', 'PERMISO']): return 'LEGAL'
    if any(k in text for k in ['SUNAT', 'IMPUESTO', 'ARANCEL', 'DÓLAR']): return 'TRIBUTARIO'
    if any(k in text for k in ['PUERTO', 'CHANCAY', 'LOGÍSTICA', 'FLETE']): return 'LOGÍSTICA'
    return 'MERCADO'

def scrape():
    all_news = []
    for source, url in RADARS.items():
        print(f"Escaneando {source}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.get('title', '')
            desc = entry.get('summary', '')
            if any(k in title.upper() or k in desc.upper() for k in KEYWORDS):
                all_news.append({
                    'id': entry.get('id', entry.link),
                    'title': title[:100],
                    'snippet': desc[:200].replace('<p>', '').replace('</p>', ''),
                    'date': datetime.datetime.now().isoformat(),
                    'source': source,
                    'url': entry.link,
                    'category': classify(title, desc)
                })
    
    # Guarda el botín en un JSON
    with open('news.json', 'w', encoding='utf-8') as f:
        json.dump(all_news[:50], f, ensure_ascii=False, indent=2)
    print("¡Bóveda actualizada!")

if __name__ == "__main__":
    scrape()