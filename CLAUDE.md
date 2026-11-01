# Conventions du dépôt de recettes

- Source unique : `recettes/<slug>/recette.yaml` (voir `modele/recette.yaml`). Tout le reste est généré par `python3 outils/generer.py` ; ne jamais éditer `mealie.json`, `README.md` des recettes ni `docs/` à la main.
- Slug : minuscules, sans accents, tirets.
- Fiches familiales : transcription fidèle (orthographe corrigée seulement). Livres et sites : ingrédients repris, étapes reformulées, source citée.
- Unités : g, cl, c. à soupe / c. à café, °C. Une mesure ancienne (verre, noix…) est gardée et complétée par son équivalent entre parenthèses.
- Tout ajout absent de la source va dans `notes` ; tout doute non résolu va dans `questions` et le statut passe à « à compléter ».
- Le scan d'origine est conservé en `scan.jpg` (JPEG ~100 dpi, qualité 70, quelques centaines de Ko maximum).
- En l'absence de photo, une illustration SVG originale (`illustration.svg`, 800×500) sert de visuel provisoire.
