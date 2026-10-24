"""
Générateur de carousel "Le saviez-vous ?"
Lit contenu.json et produit une image PNG par slide (1080x1350, format Instagram/TikTok portrait).

Prérequis (une seule fois) :
    pip install playwright
    playwright install chromium

Utilisation :
    python generer.py                 # lit contenu.json, écrit dans ./sortie
    python generer.py themes/x.json    # autre fichier de contenu (images dans sortie/x)
"""
import json
import sys
import html
from pathlib import Path
from playwright.sync_api import sync_playwright

LARGEUR, HAUTEUR = 1080, 1350

# Couleurs : changer ici pour un autre style
FOND = "#0F1B2D"        # bleu nuit
ACCENT = "#FFC94D"      # jaune
TEXTE = "#F4F1EA"       # blanc cassé
TEXTE_DOUX = "#9FB0C8"  # gris bleuté

def make_css():
    return f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:{LARGEUR}px; height:{HAUTEUR}px; overflow:hidden;
  background:{FOND}; color:{TEXTE};
  font-family:'Inter','Inter Display',sans-serif;
}}
.slide {{ position:relative; width:100%; height:100%; padding:110px 96px; display:flex; flex-direction:column; }}
.rond {{ position:absolute; border-radius:50%; background:{ACCENT}; opacity:.08; }}
.r1 {{ width:620px; height:620px; right:-220px; top:-200px; }}
.r2 {{ width:380px; height:380px; left:-160px; bottom:-140px; }}
.haut {{ display:flex; justify-content:space-between; align-items:center; font-size:30px; font-weight:600; color:{TEXTE_DOUX}; }}
.badge {{ background:{ACCENT}; color:{FOND}; padding:12px 26px; border-radius:40px; font-weight:800; letter-spacing:.5px; }}
.centre {{ flex:1; display:flex; flex-direction:column; justify-content:center; }}
.emoji {{ font-size:150px; line-height:1; margin-bottom:56px; }}
h1 {{ font-size:96px; line-height:1.05; font-weight:800; letter-spacing:-2px; }}
h2 {{ font-size:76px; line-height:1.08; font-weight:800; letter-spacing:-1.5px; margin-bottom:44px; }}
h1 em, h2 em {{ font-style:normal; color:{ACCENT}; }}
p {{ font-size:44px; line-height:1.4; color:{TEXTE}; opacity:.88; font-weight:400; }}
.sous {{ margin-top:56px; font-size:40px; color:{ACCENT}; font-weight:600; }}
.barre {{ width:120px; height:10px; background:{ACCENT}; border-radius:5px; margin-bottom:56px; }}
.compte {{ display:flex; align-items:center; gap:18px; }}
.compte svg {{ width:64px; height:64px; }}
.bas {{ display:flex; justify-content:space-between; align-items:center; font-size:30px; color:{TEXTE_DOUX}; font-weight:500; }}
.points {{ display:flex; gap:12px; }}
.points span {{ width:14px; height:14px; border-radius:50%; background:{TEXTE_DOUX}; opacity:.35; }}
.points span.actif {{ background:{ACCENT}; opacity:1; width:40px; border-radius:7px; }}
.action {{ margin-top:70px; display:inline-block; align-self:flex-start; background:{ACCENT}; color:{FOND};
           font-size:42px; font-weight:800; padding:30px 48px; border-radius:24px; }}
"""


def esc(t):
    return html.escape(t or "")


def mettre_en_valeur(titre):
    """Met le dernier mot du titre en couleur d'accent."""
    mots = esc(titre).split(" ")
    # En français, "?" ou "!" est précédé d'une espace : on garde le mot avec
    n = 2 if len(mots) > 2 and mots[-1] in ("?", "!", ":") else 1
    if len(mots) <= n:
        return " ".join(mots)
    return " ".join(mots[:-n]) + " <em>" + " ".join(mots[-n:]) + "</em>"


def corps_slide(s):
    t = s["type"]
    if t == "cover":
        return f"""<div class="barre"></div>
            <h1>{mettre_en_valeur(s['titre'])}</h1>
            <div class="sous">{esc(s.get('sous_titre'))}</div>"""
    if t == "fait":
        return f"""<div class="emoji">{esc(s.get('emoji'))}</div>
            <h2>{mettre_en_valeur(s['titre'])}</h2>
            <p>{esc(s['texte'])}</p>"""
    if t == "cta":
        return f"""<h1>{mettre_en_valeur(s['titre'])}</h1>
            <p class="sous" style="color:{TEXTE}">{esc(s.get('texte'))}</p>
            <div class="action">{esc(s.get('action'))}</div>"""
    raise ValueError(f"Type de slide inconnu : {t}")


def logo_svg(data):
    """Logo optionnel (fichier SVG indiqué dans "logo"), affiché à côté du nom du compte."""
    chemin = data.get("logo")
    return Path(chemin).read_text(encoding="utf-8") if chemin else ""


def appliquer_style(data):
    """Le bloc "style" du JSON remplace les couleurs par défaut (une palette par compte)."""
    global FOND, ACCENT, TEXTE, TEXTE_DOUX
    st = data.get("style", {})
    FOND = st.get("fond", FOND)
    ACCENT = st.get("accent", ACCENT)
    TEXTE = st.get("texte", TEXTE)
    TEXTE_DOUX = st.get("texte_doux", TEXTE_DOUX)


def page_html(data, i):
    total = len(data["slides"])
    s = data["slides"][i]
    points = "".join(f'<span class="{"actif" if k == i else ""}"></span>' for k in range(total))
    numero = "" if s["type"] in ("cover", "cta") else f"{i}/{total - 2}"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{make_css()}</style></head>
    <body><div class="slide">
      <div class="rond r1"></div><div class="rond r2"></div>
      <div class="haut"><span class="badge">{esc(data['serie'])}</span><span>{numero}</span></div>
      <div class="centre">{corps_slide(s)}</div>
      <div class="bas"><span class="compte">{logo_svg(data)}{esc(data['compte'])}</span><div class="points">{points}</div></div>
    </div></body></html>"""


def main():
    fichier = Path(sys.argv[1] if len(sys.argv) > 1 else "contenu.json")
    data = json.loads(fichier.read_text(encoding="utf-8"))
    appliquer_style(data)
    sortie = Path("sortie") / fichier.stem
    sortie.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        page = nav.new_page(viewport={"width": LARGEUR, "height": HAUTEUR})
        for i in range(len(data["slides"])):
            page.set_content(page_html(data, i), wait_until="networkidle")
            chemin = sortie / f"slide_{i + 1:02d}.png"
            page.screenshot(path=str(chemin))
            print("✓", chemin)
        nav.close()


if __name__ == "__main__":
    main()
