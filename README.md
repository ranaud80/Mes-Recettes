# Mes recettes

Recettes familiales et favorites, numérisées dans un format ouvert et durable, compatibles avec [Mealie](https://mealie.io).

**Consulter en ligne : https://ranaud80.github.io/Mes-Recettes/**

## Suivi des recettes

<!-- INDEX:DEBUT -->
| Recette | Catégorie | Auteur | Statut | Reste à faire |
|---|---|---|---|---|
| [Flamiche aux poireaux picarde](recettes/flamiche-poireaux/README.md) | Plat | Mme Seminet | À relire | 2 |
| [Gâteau à l'ananas extra moelleux](recettes/gateau-ananas-moelleux/README.md) | Dessert | Amélie Martin | À relire | 2 |
| [Gaufres (recette huile Lesieur)](recettes/gaufres-huile-lesieur/README.md) | Dessert | Maman | À compléter | 2 |
| [Potage aux champignons](recettes/potage-champignons/README.md) | Soupe | Maman | À compléter | 1 |
| [Potage d'hiver](recettes/potage-hiver/README.md) | Soupe | Maman | À compléter | 1 |
| [Potage tomates-carottes](recettes/potage-tomates-carottes/README.md) | Soupe | Maman | Validée | — |
| [Welsh](recettes/welsh/README.md) | Plat | Maman | Validée | — |
<!-- INDEX:FIN -->

## Organisation

```
recettes/<nom-de-la-recette>/
  recette.yaml       ← source : c'est le seul fichier à modifier
  scan.jpg           ← fiche d'origine (manuscrite, page de livre…)
  photo.jpg          ← photo du plat (facultatif, remplace l'illustration)
  illustration.svg   ← illustration provisoire en attendant la photo
  illustration.png   ← (généré) version image à téléverser dans Mealie
  mealie.json        ← (généré) à importer dans Mealie
  README.md          ← (généré) fiche lisible sur GitHub
docs/                ← (généré) site : une page HTML autonome par recette + sommaire
outils/generer.py    ← régénère tous les fichiers marqués (généré)
CLAUDE.md            ← conventions de transcription
modele/recette.yaml  ← modèle pour une nouvelle recette
```

Après toute modification d'un `recette.yaml` : `python3 outils/generer.py`.

## Cycle de relecture

Chaque recette porte un `statut` dans son `recette.yaml` :

| Statut | Signification |
|---|---|
| à relire | transcrite, pas encore relue |
| à compléter | relue, mais des informations manquent (liste `questions`) |
| validée | relue, rien ne manque |
| testée | réalisée en cuisine avec cette fiche, quantités confirmées |

Les points ouverts se notent dans `questions` ; ils apparaissent en cases à cocher sur la fiche GitHub et dans la colonne « Reste à faire » ci-dessus. Les précisions ajoutées à la transcription vont dans `notes`, pour toujours distinguer le texte d'origine des ajouts.

## Import dans Mealie

Dans Mealie : *Créer → Importer depuis HTML ou JSON*, coller le contenu de `mealie.json`, puis téléverser `photo.jpg` (ou `illustration.png`) comme image et `scan.jpg` en pièce jointe.

## Consultation hors ligne

Chaque page de `docs/` est autonome (illustration et scan intégrés) : elle s'ouvre dans n'importe quel navigateur, même hors ligne, et s'imprime proprement. `docs/index.html` sert de sommaire avec recherche.
