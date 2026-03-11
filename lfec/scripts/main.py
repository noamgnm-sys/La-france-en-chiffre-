"""
main.py — Orchestrateur du pipeline complet
La France en Chiffres

Usage:
  python scripts/main.py              # Pipeline complet
  python scripts/main.py --no-visuals # Sans génération d'images
  python scripts/main.py --test       # Test avec données mockées
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

def run(args):
    start = datetime.now()
    print(f"""
╔═══════════════════════════════════════════╗
║   LA FRANCE EN CHIFFRES — Pipeline Daily  ║
║   {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}                      ║
╚═══════════════════════════════════════════╝
""")

    api_key = os.environ.get("ANTHROPIC_API_KEY") or args.api_key
    if not api_key and not args.test:
        print("❌ ANTHROPIC_API_KEY manquante.")
        print("   Définis la variable d'environnement ou passe --api-key sk-ant-...")
        sys.exit(1)

    # ── ÉTAPE 1 : SCRAPING ────────────────────────────────────────────────────
    print("=" * 50)
    print("ÉTAPE 1/3 — Scraping des sources")
    print("=" * 50)

    if args.test:
        print("  [MODE TEST] Utilisation de données mockées")
        mock_articles = [
            {
                "id": "test001",
                "source": "INSEE",
                "rubrique": "Économie",
                "title": "En 2023, 9,1 millions de personnes vivent sous le seuil de pauvreté",
                "summary": "Le taux de pauvreté s'établit à 14,4% de la population française en 2023. Les jeunes de 18-29 ans sont particulièrement touchés avec un taux de 21%. Le seuil de pauvreté est fixé à 1 158€ par mois pour une personne seule.",
                "url": "https://www.insee.fr/test",
                "date": datetime.now(timezone.utc).isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "test002",
                "source": "Oxfam France",
                "rubrique": "Inégalités",
                "title": "Les dividendes du CAC40 atteignent un nouveau record en 2023",
                "summary": "Les 40 plus grandes entreprises françaises ont versé 67,4 milliards d'euros de dividendes en 2023, soit une augmentation de 12% par rapport à 2022. Dans le même temps, 200 000 emplois ont été supprimés en France.",
                "url": "https://www.oxfamfrance.org/test",
                "date": datetime.now(timezone.utc).isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        # Sauvegarder les articles mockés
        raw_file = ROOT / "data" / "raw_articles.json"
        raw_file.parent.mkdir(exist_ok=True)
        raw_file.write_text(json.dumps(mock_articles, ensure_ascii=False, indent=2))
        articles = mock_articles
    else:
        from scraper import scrape_all
        articles = scrape_all()

    if not articles:
        print("\n  Aucun nouvel article aujourd'hui. Pipeline terminé.")
        _write_summary(0, 0, start)
        return

    # ── ÉTAPE 2 : ANALYSE CLAUDE ──────────────────────────────────────────────
    print(f"\n{'=' * 50}")
    print("ÉTAPE 2/3 — Analyse Claude & extraction stats")
    print("=" * 50)

    from pipeline import run_pipeline
    stats = run_pipeline(api_key=api_key)

    if not stats:
        print("\n  Aucune stat générée.")
        _write_summary(len(articles), 0, start)
        return

    # ── ÉTAPE 3 : VISUELS ─────────────────────────────────────────────────────
    if not args.no_visuals:
        print(f"\n{'=' * 50}")
        print("ÉTAPE 3/3 — Génération des visuels")
        print("=" * 50)
        try:
            from generate_visuals import generate_all_visuals
            generate_all_visuals(stats=stats[:8])
        except Exception as e:
            print(f"  ⚠️  Visuels ignorés: {e}")
    else:
        print("\n  [Visuels ignorés --no-visuals]")

    # ── RÉSUMÉ ────────────────────────────────────────────────────────────────
    _write_summary(len(articles), len(stats), start)

def _write_summary(articles_count, stats_count, start):
    elapsed = (datetime.now() - start).total_seconds()
    summary = {
        "date": datetime.now(timezone.utc).isoformat(),
        "articles_scraped": articles_count,
        "stats_generated": stats_count,
        "duration_seconds": round(elapsed, 1),
        "status": "success" if stats_count > 0 else "no_new_content"
    }

    log_file = ROOT / "data" / "pipeline_log.json"
    log_file.parent.mkdir(exist_ok=True)
    existing_logs = []
    if log_file.exists():
        try:
            existing_logs = json.loads(log_file.read_text())
        except:
            pass
    log_file.write_text(json.dumps([summary] + existing_logs[:29], ensure_ascii=False, indent=2))

    print(f"""
╔═══════════════════════════════════════════╗
║   ✅ Pipeline terminé                     ║
║   Articles scannés : {articles_count:<4}                  ║
║   Stats générées   : {stats_count:<4}                  ║
║   Durée            : {elapsed:.1f}s                  ║
╚═══════════════════════════════════════════╝
""")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline La France en Chiffres")
    parser.add_argument("--no-visuals", action="store_true", help="Ne pas générer les visuels PNG")
    parser.add_argument("--test", action="store_true", help="Mode test avec données mockées")
    parser.add_argument("--api-key", type=str, help="Clé API Anthropic (optionnel si var env définie)")
    args = parser.parse_args()
    run(args)
