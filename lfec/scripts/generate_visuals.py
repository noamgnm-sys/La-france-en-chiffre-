"""
generate_visuals.py — Génération automatique des visuels PNG
La France en Chiffres
Formats : carré (1080×1080), story (1080×1920), paysage (1920×1080)
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Pillow non installé. Install: pip install Pillow")

ROOT = Path(__file__).parent.parent
STATS_FILE = ROOT / "site" / "data" / "stats.json"
VISUALS_DIR = ROOT / "site" / "visuals"
FONTS_DIR = ROOT / "assets" / "fonts"

# ── PALETTE ───────────────────────────────────────────────────────────────────
BG_DARK      = (8, 17, 31)
BG_CARD      = (13, 27, 46)
RED          = (232, 0, 61)
RED_LIGHT    = (255, 107, 53)
WHITE        = (240, 237, 232)
MUTED        = (107, 122, 141)
GREEN_ACCENT = (0, 212, 255)

RUBRIQUES_COLORS = {
    "Économie":      (232, 0, 61),
    "Société":       (0, 150, 255),
    "Politique":     (180, 0, 200),
    "Entreprises":   (255, 140, 0),
    "Santé":         (0, 200, 120),
    "Logement":      (255, 200, 0),
    "Environnement": (50, 200, 100),
    "Inégalités":    (255, 60, 60),
    "Comparaisons":  (0, 180, 255),
}

def get_font(size, bold=False):
    """Charge une fonte système."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def draw_gradient_bar(draw, x, y, w, h, color1, color2):
    """Dessine une barre de dégradé horizontal."""
    for i in range(w):
        r = int(color1[0] + (color2[0] - color1[0]) * i / w)
        g = int(color1[1] + (color2[1] - color1[1]) * i / w)
        b = int(color1[2] + (color2[2] - color1[2]) * i / w)
        draw.rectangle([x + i, y, x + i + 1, y + h], fill=(r, g, b))

def wrap_text(text, font, max_width, draw):
    """Découpe le texte pour tenir dans max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def generate_square(stat, output_path):
    """Format carré 1080×1080 pour Instagram."""
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    rubrique = stat.get("rubrique", "France")
    color = RUBRIQUES_COLORS.get(rubrique, RED)

    # Barre supérieure colorée
    draw_gradient_bar(draw, 0, 0, W, 6, color, RED_LIGHT)

    # Fond carte centrale
    draw.rectangle([60, 80, W-60, H-80], fill=BG_CARD, outline=(30, 47, 70), width=1)

    # Rubrique
    font_cat = get_font(28, bold=True)
    draw.text((120, 130), rubrique.upper(), font=font_cat, fill=color)

    # Chiffre principal
    chiffre = stat.get("chiffre", "")
    font_num = get_font(180, bold=True)
    bbox = draw.textbbox((0, 0), chiffre, font=font_num)
    num_w = bbox[2] - bbox[0]
    x_num = max(120, min((W - num_w) // 2, W - num_w - 120))
    draw.text((x_num, 200), chiffre, font=font_num, fill=WHITE)

    # Ligne rouge sous le chiffre
    draw.rectangle([120, 420, W-120, 424], fill=color)

    # Titre
    font_titre = get_font(52, bold=True)
    titre = stat.get("titre", "")
    lines = wrap_text(titre, font_titre, W - 280, draw)
    y = 460
    for line in lines[:2]:
        draw.text((120, y), line, font=font_titre, fill=WHITE)
        y += 70

    # Texte explication
    font_body = get_font(38)
    texte = stat.get("texte", "")
    lines_body = wrap_text(texte, font_body, W - 280, draw)
    y = max(y + 20, 640)
    for line in lines_body[:3]:
        draw.text((120, y), line, font=font_body, fill=(*MUTED,))
        y += 55

    # Comparaison
    comparaison = stat.get("comparaison")
    if comparaison:
        font_comp = get_font(34, bold=True)
        draw.rectangle([120, y + 20, 128, y + 70], fill=color)
        lines_comp = wrap_text(comparaison, font_comp, W - 310, draw)
        yc = y + 20
        for line in lines_comp[:2]:
            draw.text((148, yc), line, font=font_comp, fill=(*GREEN_ACCENT,))
            yc += 48

    # Source
    font_source = get_font(28)
    source = f"Source : {stat.get('source_nom', 'Source officielle')}"
    draw.text((120, H - 160), source, font=font_source, fill=(*MUTED,))

    # Branding
    font_brand = get_font(32, bold=True)
    brand = "lafranceenchiffres.fr"
    bbox = draw.textbbox((0, 0), brand, font=font_brand)
    draw.text((W - bbox[2] - bbox[0] - 120, H - 160), brand, font=font_brand, fill=color)

    img.save(output_path, "PNG", quality=95)

def generate_story(stat, output_path):
    """Format story/reel 1080×1920."""
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    rubrique = stat.get("rubrique", "France")
    color = RUBRIQUES_COLORS.get(rubrique, RED)

    # Fond dégradé vertical
    for y in range(H):
        alpha = y / H
        r = int(BG_DARK[0] * (1 - alpha * 0.3))
        g = int(BG_DARK[1] * (1 - alpha * 0.2))
        b = int(BG_DARK[2] + (20 * alpha))
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Barre latérale colorée
    draw.rectangle([0, 0, 8, H], fill=color)

    # Tag rubrique
    font_cat = get_font(36, bold=True)
    draw.text((80, 200), f"◼  {rubrique.upper()}", font=font_cat, fill=color)

    # Accroche
    font_hook = get_font(48)
    draw.text((80, 300), "Le chiffre que vous", font=font_hook, fill=(*MUTED,))
    draw.text((80, 360), "devez connaître.", font=font_hook, fill=(*MUTED,))

    # Ligne séparatrice
    draw.rectangle([80, 460, W-80, 464], fill=(30, 47, 70))

    # Chiffre ÉNORME
    font_num = get_font(240, bold=True)
    chiffre = stat.get("chiffre", "")
    bbox = draw.textbbox((0, 0), chiffre, font=font_num)
    x_c = (W - (bbox[2] - bbox[0])) // 2
    draw.text((max(80, x_c), 520), chiffre, font=font_num, fill=WHITE)

    # Titre
    font_titre = get_font(68, bold=True)
    titre = stat.get("titre", "")
    lines = wrap_text(titre, font_titre, W - 160, draw)
    y = 860
    for line in lines[:2]:
        draw.text((80, y), line, font=font_titre, fill=WHITE)
        y += 90

    # Ligne colorée
    draw.rectangle([80, y + 20, 200, y + 26], fill=color)

    # Explication
    font_body = get_font(46)
    texte = stat.get("texte", "")
    lines_body = wrap_text(texte, font_body, W - 160, draw)
    y = y + 60
    for line in lines_body[:3]:
        draw.text((80, y), line, font=font_body, fill=(*MUTED,))
        y += 65

    # Angle viral
    font_angle = get_font(42, bold=True)
    angle = stat.get("angle_viral", "")
    lines_angle = wrap_text(f'"{angle}"', font_angle, W - 160, draw)
    y = max(y + 40, 1300)
    for line in lines_angle[:3]:
        draw.text((80, y), line, font=font_angle, fill=WHITE)
        y += 58

    # Script TikTok (petit)
    script = stat.get("script_tiktok", "")
    if script:
        font_script = get_font(30)
        lines_script = wrap_text(script, font_script, W - 200, draw)
        y = max(y + 40, 1580)
        for line in lines_script[:3]:
            draw.text((80, y), line, font=font_script, fill=(*MUTED,))
            y += 42

    # Branding bas
    draw_gradient_bar(draw, 0, H-100, W, 100, (0,0,0,0), (*color, 60))
    font_brand = get_font(36, bold=True)
    draw.text((80, H - 70), "lafranceenchiffres.fr", font=font_brand, fill=color)
    font_src = get_font(28)
    src_text = f"Source : {stat.get('source_nom', '')}"
    bbox = draw.textbbox((0, 0), src_text, font=font_src)
    draw.text((W - bbox[2] - 80, H - 65), src_text, font=font_src, fill=(*MUTED,))

    img.save(output_path, "PNG", quality=95)

def generate_all_visuals(stats: list = None, max_stats: int = 10):
    """Génère tous les formats pour les N meilleures stats."""
    if not PIL_AVAILABLE:
        print("❌ Pillow requis. Installe avec: pip install Pillow")
        return

    if stats is None:
        if not STATS_FILE.exists():
            print("Aucun fichier stats trouvé.")
            return
        data = json.loads(STATS_FILE.read_text())
        stats = data.get("stats", [])[:max_stats]

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_dir = VISUALS_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🎨 Génération des visuels pour {len(stats)} stats...")

    for i, stat in enumerate(stats):
        stat_id = stat.get("id", f"stat_{i+1:03d}")
        rubrique = stat.get("rubrique", "general").lower().replace(" ", "_")
        base_name = f"{stat_id}_{rubrique}"

        print(f"  [{i+1}/{len(stats)}] {stat.get('chiffre')} — {stat.get('titre', '')[:40]}...")

        try:
            # Carré Instagram
            generate_square(stat, out_dir / f"{base_name}_square.png")
            # Story/Reel
            generate_story(stat, out_dir / f"{base_name}_story.png")
        except Exception as e:
            print(f"  ⚠️  Erreur visuel {stat_id}: {e}")

    # Index des visuels générés
    visuals_index = []
    for png in sorted(out_dir.glob("*.png")):
        visuals_index.append({
            "file": str(png.relative_to(ROOT / "site")),
            "format": "story" if "story" in png.name else "square",
            "date": today
        })

    index_file = VISUALS_DIR / "index.json"
    existing_index = []
    if index_file.exists():
        try:
            existing_index = json.loads(index_file.read_text())
        except:
            pass

    index_file.write_text(json.dumps(visuals_index + existing_index, ensure_ascii=False, indent=2))
    print(f"\n✅ {len(visuals_index)} visuels générés dans {out_dir}")

if __name__ == "__main__":
    generate_all_visuals(max_stats=5)
