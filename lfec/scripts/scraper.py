"""
scraper.py — Surveillance automatique des sources officielles
La France en Chiffres
"""

import requests
import feedparser
import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# ── SOURCES À SURVEILLER ──────────────────────────────────────────────────────

SOURCES = [
    {
        "name": "INSEE",
        "type": "rss",
        "url": "https://www.insee.fr/fr/information/flux-rss-publications",
        "rubrique": "Économie"
    },
    {
        "name": "Eurostat",
        "type": "rss",
        "url": "https://ec.europa.eu/eurostat/rss/news",
        "rubrique": "Comparaisons"
    },
    {
        "name": "Cour des comptes",
        "type": "rss",
        "url": "https://www.ccomptes.fr/fr/flux-rss",
        "rubrique": "Politique"
    },
    {
        "name": "Sénat",
        "type": "rss",
        "url": "https://www.senat.fr/rss/actualites.xml",
        "rubrique": "Politique"
    },
    {
        "name": "Assemblée Nationale",
        "type": "rss",
        "url": "https://www.assemblee-nationale.fr/dyn/rss/actualites.rss",
        "rubrique": "Politique"
    },
    {
        "name": "Oxfam France",
        "type": "rss",
        "url": "https://www.oxfamfrance.org/feed/",
        "rubrique": "Inégalités"
    },
    {
        "name": "Fondation Abbé Pierre",
        "type": "rss",
        "url": "https://www.fondation-abbe-pierre.fr/feed",
        "rubrique": "Logement"
    },
    {
        "name": "Banque de France",
        "type": "rss",
        "url": "https://www.banque-france.fr/rss.xml",
        "rubrique": "Économie"
    },
    {
        "name": "DREES",
        "type": "rss",
        "url": "https://drees.solidarites-sante.gouv.fr/flux-rss",
        "rubrique": "Santé"
    },
    {
        "name": "Le Monde (Société)",
        "type": "rss",
        "url": "https://www.lemonde.fr/societe/rss_full.xml",
        "rubrique": "Société"
    }
]

# ── CHEMINS ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
SEEN_FILE = ROOT / "data" / "seen_articles.json"
RAW_FILE = ROOT / "data" / "raw_articles.json"

def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()

def save_seen(seen):
    SEEN_FILE.parent.mkdir(exist_ok=True)
    SEEN_FILE.write_text(json.dumps(list(seen), ensure_ascii=False, indent=2))

def article_id(url):
    return hashlib.md5(url.encode()).hexdigest()

def fetch_rss(source):
    """Récupère les articles d'un flux RSS."""
    articles = []
    try:
        headers = {"User-Agent": "LaFranceEnChiffres/1.0 (+https://lafranceenchiffres.fr)"}
        response = requests.get(source["url"], headers=headers, timeout=15)
        feed = feedparser.parse(response.content)

        for entry in feed.entries[:5]:  # Max 5 derniers par source
            url = entry.get("link", "")
            title = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))

            # Nettoyer le HTML du résumé
            import re
            summary = re.sub(r'<[^>]+>', ' ', summary).strip()
            summary = re.sub(r'\s+', ' ', summary)[:1000]

            if url and title:
                articles.append({
                    "id": article_id(url),
                    "source": source["name"],
                    "rubrique": source["rubrique"],
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "date": entry.get("published", datetime.now(timezone.utc).isoformat()),
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                })
    except Exception as e:
        print(f"  ⚠️  Erreur {source['name']}: {e}")
    return articles

def scrape_all():
    """Scrape toutes les sources et retourne les nouveaux articles."""
    print("🔍 Démarrage du scraping...")
    seen = load_seen()
    all_articles = []
    new_articles = []

    for source in SOURCES:
        print(f"  📡 {source['name']}...")
        articles = fetch_rss(source)
        all_articles.extend(articles)

        for article in articles:
            if article["id"] not in seen:
                new_articles.append(article)
                seen.add(article["id"])

    # Sauvegarder
    save_seen(seen)
    RAW_FILE.parent.mkdir(exist_ok=True)
    RAW_FILE.write_text(json.dumps(new_articles, ensure_ascii=False, indent=2))

    print(f"\n✅ {len(new_articles)} nouveaux articles trouvés sur {len(all_articles)} scannés")
    return new_articles

if __name__ == "__main__":
    articles = scrape_all()
    for a in articles[:3]:
        print(f"\n  → [{a['source']}] {a['title'][:80]}")
