"""
Cherche une photo libre de droits d'un animal sur iNaturalist et l'enregistre dans faune_extreme/photos/.

Utilisation :
    python3 chercher_photo.py <cle> "<nom scientifique>" [rang]
    ex. : python3 chercher_photo.py hippopotame "Hippopotamus amphibius"
          python3 chercher_photo.py hippopotame "Hippopotamus amphibius" 2   (2e meilleure photo)

- Licences acceptées : CC BY, CC BY-SA, CC0 et domaine public (jamais de licence « NC » ni de photo sans licence).
- Ordre : observations « research grade » les plus votées, puis photo par défaut du taxon.
- Écrit faune_extreme/photos/<cle>.jpg et met à jour faune_extreme/photos/credits.json.
- Affiche la mention de crédit à recopier dans le champ "credit" de la slide.
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.inaturalist.org/v1"
LICENCES = {"cc-by": "CC BY", "cc-by-sa": "CC BY-SA", "cc0": "CC0", "pd": "domaine public"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "faune-extreme/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def candidats(nom):
    q = urllib.parse.quote(nom)
    obs = json.loads(get(f"{API}/observations?taxon_name={q}&photo_license=cc-by,cc-by-sa,cc0"
                         f"&quality_grade=research&per_page=15&order_by=votes"))
    for o in obs["results"]:
        for p in o["photos"]:
            if p.get("license_code") in LICENCES:
                yield {"url": p["url"].replace("square", "large"), "licence": LICENCES[p["license_code"]],
                       "attribution": p["attribution"], "source": o["uri"], "taxon": o["taxon"]["name"]}
                break
    taxa = json.loads(get(f"{API}/taxa?q={q}&per_page=3"))
    for t in taxa["results"]:
        dp = t.get("default_photo") or {}
        if dp.get("license_code") in LICENCES:
            yield {"url": dp["medium_url"].replace("medium", "large"), "licence": LICENCES[dp["license_code"]],
                   "attribution": dp["attribution"], "source": f"https://www.inaturalist.org/taxa/{t['id']}",
                   "taxon": t["name"]}


def auteur(attribution):
    a = attribution.replace("(c) ", "").split(",")[0].strip()
    return a if "no known copyright" not in attribution else attribution.split(",")[0].strip()


def main():
    cle, nom = sys.argv[1], sys.argv[2]
    rang = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    liste = list(candidats(nom))
    if len(liste) < rang:
        sys.exit(f"Aucune photo libre trouvée pour « {nom} » (rang {rang}). Essaie une espèce très proche.")
    c = liste[rang - 1]
    dossier = Path("faune_extreme/photos")
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{cle}.jpg").write_bytes(get(c["url"]))
    credit = f"Photo : {auteur(c['attribution'])} / iNaturalist ({c['licence']})"
    if c["taxon"].lower() != nom.lower():
        credit += f" – {c['taxon']}"
    fichier = dossier / "credits.json"
    credits = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {}
    credits[cle] = {"taxon": c["taxon"], "observation": c["source"], "attribution": c["attribution"],
                    "licence": c["licence"], "credit": credit}
    fichier.write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ faune_extreme/photos/{cle}.jpg  ({len(liste)} candidates)")
    print(f"credit: {credit}")


if __name__ == "__main__":
    main()
