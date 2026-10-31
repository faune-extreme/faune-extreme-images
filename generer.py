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
.centre {{ flex:1; min-height:0; overflow:hidden; display:flex; flex-direction:column; justify-content:center; }}
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
.photo {{ position:absolute; left:0; top:0; width:100%; height:660px; background-size:cover; background-repeat:no-repeat; }}
.photo::after {{ content:""; position:absolute; inset:0;
   background:linear-gradient(to bottom, rgba(0,0,0,.35) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 55%, {FOND} 100%); }}
.couv .photo {{ height:100%; }}
.couv .photo::after {{ background:linear-gradient(to bottom, rgba(0,0,0,.45) 0%, rgba(0,0,0,.05) 25%, rgba(0,0,0,.15) 45%, {FOND}F2 72%, {FOND} 100%); }}
.credit {{ position:absolute; right:40px; top:612px; font-size:19px; color:#fff; opacity:.75; text-shadow:0 1px 3px #000; max-width:900px; text-align:right; z-index:2; }}
.couv .credit {{ top:auto; bottom:190px; }}
.haut, .centre, .bas {{ position:relative; z-index:1; }}
.avec-photo .haut span:last-child {{ color:#fff; text-shadow:0 1px 6px rgba(0,0,0,.8); }}
.avec-photo .centre {{ justify-content:flex-start; padding-top:520px; }}
.avec-photo h2 {{ font-size:66px; margin-bottom:30px; }}
.avec-photo p {{ font-size:40px; line-height:1.38; }}
.mosaique {{ position:absolute; left:0; top:0; width:100%; height:780px; display:grid; gap:6px; background:{FOND}; }}
.mosaique.n3 {{ grid-template-columns:58fr 42fr; grid-template-rows:1fr 1fr; }}
.mosaique.n3 div:first-child {{ grid-row:1 / 3; }}
.mosaique.n2 {{ grid-template-columns:1fr 1fr; }}
.mosaique div {{ background-size:cover; background-repeat:no-repeat; }}
.mosaique .case-emoji {{ display:flex; align-items:center; justify-content:center; font-size:230px; background:#16392B; }}
.mosaique::after {{ content:""; position:absolute; inset:0;
   background:linear-gradient(to bottom, rgba(0,0,0,.4) 0%, rgba(0,0,0,0) 20%, rgba(0,0,0,0) 55%, {FOND} 100%); }}
.couv-mosaique .centre {{ justify-content:flex-end; padding-bottom:30px; }}
.couv-mosaique .credit {{ top:auto; bottom:170px; left:96px; right:96px; text-align:left; font-size:18px; }}
.couv .centre {{ justify-content:flex-end; padding-bottom:40px; }}
.couv h1 {{ text-shadow:0 2px 18px rgba(0,0,0,.35); }}
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
    if t == "fait" and s.get("photo"):
        return f"""<h2>{mettre_en_valeur(s['titre'])}</h2>
            <p>{esc(s['texte'])}</p>"""
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


def data_uri(chemin):
    import base64, mimetypes
    p = Path(chemin)
    return f"data:{mimetypes.guess_type(p.name)[0] or 'image/jpeg'};base64," + base64.b64encode(p.read_bytes()).decode()


def bloc_photo(s):
    """Couverture : "photos" = liste de {photo, cadrage} (mosaïque de 2 ou 3), "credit" = mention commune.
    Photo optionnelle : "photo" (chemin local), "credit" (auteur/licence), "cadrage" (CSS background-position)."""
    if s.get("photos"):
        cases = "".join(
            f'<div class="case-emoji">{esc(p["emoji"])}</div>' if p.get("emoji") else
            f'<div style="background-image:url({data_uri(p["photo"])});background-position:{esc(p.get("cadrage", "center"))}"></div>'
            for p in s["photos"])
        credit = f'<div class="credit">{esc(s.get("credit"))}</div>' if s.get("credit") else ""
        return f'<div class="mosaique n{len(s["photos"])}">{cases}</div>{credit}'
    if not s.get("photo"):
        return ""
    import base64, mimetypes
    p = Path(s["photo"])
    uri = f"data:{mimetypes.guess_type(p.name)[0] or 'image/jpeg'};base64," + base64.b64encode(p.read_bytes()).decode()
    credit = f'<div class="credit">{esc(s.get("credit"))}</div>' if s.get("credit") else ""
    return f'<div class="photo" style="background-image:url({uri});background-position:{esc(s.get("cadrage","center"))}"></div>{credit}'


def classes(s):
    if s.get("photos"):
        return "slide couv-mosaique"
    if not s.get("photo"):
        return "slide"
    return "slide couv" if s["type"] == "cover" else "slide avec-photo"


def page_html(data, i):
    total = len(data["slides"])
    s = data["slides"][i]
    points = "".join(f'<span class="{"actif" if k == i else ""}"></span>' for k in range(total))
    numero = "" if s["type"] in ("cover", "cta") else f"{i}/{total - 2}"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{make_css()}</style></head>
    <body><div class="{classes(s)}">
      {bloc_photo(s) or '<div class="rond r1"></div><div class="rond r2"></div>'}
      <div class="haut"><span class="badge">{esc(data['serie'])}</span><span>{numero}</span></div>
      <div class="centre">{corps_slide(s)}</div>
      <div class="bas"><span class="compte">{logo_svg(data)}{esc(data['compte'])}</span><div class="points">{points}</div></div>
    </div></body></html>"""


def main():
    fichier = Path(sys.argv[1] if len(sys.argv) > 1 else "contenu.json")
    data = json.loads(fichier.read_text(encoding="utf-8"))
    appliquer_style(data)
    sortie = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("sortie") / fichier.stem
    sortie.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        page = nav.new_page(viewport={"width": LARGEUR, "height": HAUTEUR})
        for i in range(len(data["slides"])):
            page.set_content(page_html(data, i), wait_until="networkidle")
            # Sécurité : si le texte déborde, on réduit la taille des polices jusqu'à ce qu'il tienne
            reduit = page.evaluate("""() => {
                const c = document.querySelector('.centre'); let n = 0;
                while (c.scrollHeight > c.clientHeight + 1 && n < 12) {
                    c.querySelectorAll('h1,h2,p').forEach(e => {
                        e.style.fontSize = (parseFloat(getComputedStyle(e).fontSize) * 0.95) + 'px'; });
                    n++; }
                return n; }""")
            if reduit:
                print(f"  (texte réduit {reduit}x pour tenir sur la slide {i + 1})")
            chemin = sortie / f"slide_{i + 1:02d}.png"
            page.screenshot(path=str(chemin))
            print("✓", chemin)
        nav.close()


if __name__ == "__main__":
    main()
