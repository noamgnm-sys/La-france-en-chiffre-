# 🇫🇷 La France en Chiffres — Pipeline Automatique

Data-journalism automatisé. Chaque matin, le pipeline scrape les sources officielles, extrait les stats les plus percutantes via Claude, génère les visuels et met à jour le site.

---

## ⚡ Mise en route (15 minutes)

### 1. Fork & Clone

```bash
git clone https://github.com/TON_USERNAME/la-france-en-chiffres.git
cd la-france-en-chiffres
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Tester en local

```bash
# Test complet avec données mockées (sans clé API)
python scripts/main.py --test --no-visuals

# Pipeline réel (nécessite clé API)
export ANTHROPIC_API_KEY=sk-ant-api03-...
python scripts/main.py
```

### 4. Configurer GitHub Actions

Dans ton repo GitHub → **Settings → Secrets and variables → Actions** :

| Secret | Valeur |
|--------|--------|
| `ANTHROPIC_API_KEY` | Ta clé API Anthropic (sk-ant-api03-...) |
| `NETLIFY_BUILD_HOOK` | URL du build hook Netlify (optionnel) |

Le pipeline tournera automatiquement **chaque matin à 8h00** (heure de Paris).

Pour lancer manuellement : **Actions → Pipeline Daily → Run workflow**

### 5. Déployer sur Netlify

1. Va sur [netlify.com](https://netlify.com)
2. "Add new site" → "Import from Git"
3. Sélectionne ton repo
4. Publish directory : `site`
5. Déploie

---

## 📁 Structure du projet

```
├── .github/
│   └── workflows/
│       └── daily.yml          # Pipeline automatique 8h/jour
├── scripts/
│   ├── main.py                # Orchestrateur principal
│   ├── scraper.py             # Scraping des sources officielles
│   ├── pipeline.py            # Extraction stats via Claude API
│   └── generate_visuals.py    # Génération PNG (carré + story)
├── site/
│   ├── index.html             # Site web public
│   ├── data/
│   │   └── stats.json         # Stats générées (auto-mis à jour)
│   └── visuals/               # Visuels PNG générés
│       └── YYYYMMDD/
│           ├── stat_XXX_square.png
│           └── stat_XXX_story.png
├── data/
│   ├── raw_articles.json      # Articles bruts scrapés
│   ├── seen_articles.json     # Articles déjà traités
│   └── pipeline_log.json      # Logs d'exécution
├── requirements.txt
└── netlify.toml
```

---

## 🔧 Sources surveillées

| Source | Type | Rubrique |
|--------|------|----------|
| INSEE | RSS | Économie |
| Eurostat | RSS | Comparaisons |
| Cour des comptes | RSS | Politique |
| Sénat | RSS | Politique |
| Assemblée Nationale | RSS | Politique |
| Oxfam France | RSS | Inégalités |
| Fondation Abbé Pierre | RSS | Logement |
| Banque de France | RSS | Économie |
| DREES | RSS | Santé |

### Ajouter une source

Dans `scripts/scraper.py`, ajoute à la liste `SOURCES` :

```python
{
    "name": "Nom de la source",
    "type": "rss",
    "url": "https://exemple.fr/feed.xml",
    "rubrique": "Économie"  # ou Société, Politique, etc.
}
```

---

## 📱 Visuels générés

Pour chaque stat, le pipeline génère automatiquement :
- **Carré 1080×1080** → Instagram feed, Facebook, X
- **Story 1080×1920** → Instagram Story, TikTok, Reels

Les visuels sont sauvegardés dans `site/visuals/YYYYMMDD/`

---

## 💰 Coût estimé

| Service | Coût |
|---------|------|
| GitHub Actions | Gratuit (2000 min/mois) |
| Netlify | Gratuit |
| Claude API | ~0,05-0,20€/jour selon le volume |

**Budget mensuel : ~3-6€/mois maximum.**

---

## 🚀 Évolutions possibles

- [ ] Newsletter automatique (Mailchimp API)
- [ ] Post automatique sur X/Twitter
- [ ] Page stat individuelle avec SEO
- [ ] Comparaison historique des stats
- [ ] API publique des données
