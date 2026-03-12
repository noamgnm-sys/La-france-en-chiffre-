"""
pipeline.py — Extraction des stats via Claude API
La France en Chiffres
"""

import anthropic
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW_FILE = ROOT / "data" / "raw_articles.json"
STATS_FILE = ROOT / "site" / "data" / "stats.json"

SYSTEM_PROMPT = """Tu es le rédacteur en chef de "La France en Chiffres", le media de référence du data-journalism français.

Ta mission : extraire les statistiques les plus percutantes et révélatrices des documents officiels français.

Critères d'une bonne stat :
- Chiffre concret et vérifiable (%, montant €, nombre de personnes)
- Révèle une injustice, une tendance choquante ou un fait méconnu
- Facile à comprendre en 5 secondes
- Provoque une réaction émotionnelle (surprise, indignation, espoir)

Tu réponds UNIQUEMENT en JSON valide, sans markdown, sans commentaires."""

def extract_stats_from_articles(articles: list, api_key: str) -> list:
    if not articles:
        print("Aucun article à analyser.")
        return []

    client = anthropic.Anthropic(api_key=api_key)
    batches = [articles[i:i+5] for i in range(0, min(len(articles), 20), 5)]
    all_stats = []

    for batch_idx, batch in enumerate(batches):
        print(f"  🧠 Analyse du lot {batch_idx + 1}/{len(batches)}...")

        content = ""
        for a in batch:
            content += f"\n\n---\nSOURCE: {a['source']} | RUBRIQUE: {a['rubrique']}\nTITRE: {a['title']}\nRÉSUMÉ: {a['summary']}\nURL: {a['url']}\n"

        prompt = f"""Analyse ces {len(batch)} articles officiels français et extrait les statistiques les plus percutantes.

{content}

Retourne ce JSON exact :
{{
  "stats": [
    {{
      "chiffre": "valeur principale courte (ex: 9,1M ou 67 Mds€ ou 23%)",
      "unite": "unité si applicable",
      "rubrique": "Économie | Société | Politique | Entreprises | Santé | Logement | Environnement | Inégalités | Comparaisons",
      "titre": "stat en 8 mots max",
      "texte": "explication claire en 1 phrase (max 20 mots)",
      "angle_viral": "formulation choc pour les réseaux sociaux (max 25 mots)",
      "comparaison": "mise en perspective concrète ou null",
      "source_nom": "nom de la source officielle",
      "source_url": "URL de l'article source",
      "script_tiktok": "script 3 phrases pour vidéo 15s",
      "caption_insta": "caption Instagram avec emojis et hashtags (max 150 caractères)",
      "score_viralite": 1
    }}
  ]
}}

Ne génère une stat QUE si elle contient un chiffre réel et vérifiable. Maximum 3 stats par lot."""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            raw = message.content[0].text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)

            for stat in parsed.get("stats", []):
                stat["generated_at"] = datetime.now(timezone.utc).isoformat()
                stat["id"] = f"stat_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{len(all_stats) + 1:03d}"
                all_stats.append(stat)

        except Exception as e:
            print(f"  ⚠️  Erreur lot {batch_idx + 1}: {e}")
            continue

    return all_stats

def save_stats(new_stats: list):
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)

    existing = []
    if STATS_FILE.exists():
        try:
            data = json.loads(STATS_FILE.read_text())
            existing = data.get("stats", [])
        except:
            existing = []

    all_stats = new_stats + existing
    all_stats = all_stats[:200]
    all_stats.sort(key=lambda x: x.get("score_viralite", 0), reverse=True)

    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total": len(all_stats),
        "new_today": len(new_stats),
        "stats": all_stats
    }

    STATS_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"  💾 {len(all_stats)} stats sauvegardées ({len(new_stats)} nouvelles)")
    return all_stats

def run_pipeline(api_key: str = None):
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY manquante")

    print("\n🧠 Démarrage du pipeline Claude...\n")

    if not RAW_FILE.exists():
        print("Aucun article brut trouvé. Lance scraper.py d'abord.")
        return []

    articles = json.loads(RAW_FILE.read_text())
    print(f"  📄 {len(articles)} articles à analyser")

    if not articles:
        print("  Aucun nouvel article aujourd'hui.")
        return []

    stats = extract_stats_from_articles(articles, api_key)
    print(f"\n  ✨ {len(stats)} stats extraites")

    save_stats(stats)
    return stats

if __name__ == "__main__":
    stats = run_pipeline()
    for s in stats[:3]:
        print(f"  [{s['rubrique']}] {s['chiffre']} — {s['titre']}")
