# faune-extreme-images

Carousels « Le saviez-vous ? » du compte @faune.extreme (Instagram, TikTok).

- `generer.py` : génère les slides PNG (1080×1350) à partir d'un fichier JSON. Prérequis : `pip install playwright` puis `playwright install chromium`.
- `faune_extreme/modele.json` : modèle de carousel (palette, logo, structure 5 slides : couverture, 3 faits, appel à l'action).
- `faune_extreme/historique.json` : animaux déjà publiés et réserve de faits.
- `posts/AAAA-MM-JJ/` : images de chaque carousel publié (liens publics utilisés par Metricool).
