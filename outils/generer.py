#!/usr/bin/env python3
"""Génère toutes les sorties à partir des fichiers recettes/<slug>/recette.yaml.

Pour chaque recette :
  recettes/<slug>/mealie.json     JSON schema.org/Recipe, à importer dans Mealie
  recettes/<slug>/README.md       fiche lisible directement sur GitHub
  recettes/<slug>/illustration.png  (si illustration.svg existe) image à téléverser dans Mealie
  docs/<slug>.html                fiche HTML autonome (illustration + scan intégrés), pour l'archive
Et globalement :
  docs/index.html                 sommaire du site
  README.md                       tableau de suivi (entre les marqueurs INDEX)

Usage : python3 outils/generer.py   (dépendance : pyyaml ; rsvg-convert facultatif)
"""
import base64
import html
import json
import pathlib
import re
import shutil
import subprocess

import yaml

RACINE = pathlib.Path(__file__).resolve().parent.parent
RECETTES = RACINE / "recettes"
DOCS = RACINE / "docs"

STATUTS = {
    "à relire": ("À relire", "#b45309"),
    "à compléter": ("À compléter", "#a16207"),
    "validée": ("Validée", "#15803d"),
    "testée": ("Testée en cuisine", "#1d4ed8"),
}
ORDRE_STATUT = list(STATUTS)


# ---------------------------------------------------------------- chargement
def charger():
    recettes = []
    for f in sorted(RECETTES.glob("*/recette.yaml")):
        try:
            r = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError as err:
            raise SystemExit(f"{f}: YAML invalide (penser à mettre entre guillemets un texte contenant « : »)\n{err}")
        r["slug"] = f.parent.name
        r["dossier"] = f.parent
        r.setdefault("notes", [])
        r["questions"] = r.get("questions") or []
        r["notes"] = r.get("notes") or []
        r["mots_cles"] = r.get("mots_cles") or []
        r.setdefault("statut", "à relire")
        if r["statut"] not in STATUTS:
            raise SystemExit(f"{f}: statut inconnu « {r['statut']} »")
        recettes.append(r)
    return recettes


def minutes(n):
    return f"PT{int(n)}M" if n else None


# ---------------------------------------------------------------- schema.org
def schema_org(r):
    d = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r["nom"],
        "description": r.get("description") or "",
        "recipeCategory": r.get("categorie") or "",
        "keywords": ", ".join(r["mots_cles"]),
        "recipeIngredient": r["ingredients"],
        "recipeInstructions": [{"@type": "HowToStep", "text": e} for e in r["etapes"]],
    }
    if r.get("auteur"):
        d["author"] = {"@type": "Person", "name": r["auteur"]}
    if est_url(r.get("source")):
        d["isBasedOn"] = r["source"]
    if r.get("portions"):
        d["recipeYield"] = str(r["portions"])
    if minutes(r.get("preparation")):
        d["prepTime"] = minutes(r["preparation"])
    if minutes(r.get("cuisson")):
        d["cookTime"] = minutes(r["cuisson"])
    if r.get("preparation") and r.get("cuisson"):
        d["totalTime"] = minutes(int(r["preparation"]) + int(r["cuisson"]))
    return d


# ---------------------------------------------------------------- source
def est_url(s):
    return isinstance(s, str) and s.startswith(("http://", "https://"))


def nom_source(r):
    """Libellé de la source : `source_nom` si présent, sinon le domaine de l'URL."""
    if r.get("source_nom"):
        return r["source_nom"]
    return r["source"].split("/")[2].removeprefix("www.")


# ---------------------------------------------------------------- GitHub (Markdown)
def meta_ligne(r):
    m = []
    if r.get("portions"):
        m.append(f"Pour {r['portions']}")
    if r.get("preparation"):
        m.append(f"Préparation {r['preparation']} min")
    if r.get("cuisson"):
        m.append(f"Cuisson {r['cuisson']} min")
    if r.get("categorie"):
        m.append(r["categorie"])
    return m


def markdown(r):
    d = r["dossier"]
    L = [f"# {r['nom']}", ""]
    if (d / "photo.jpg").exists():
        L += ["![Photo du plat](photo.jpg)", ""]
    elif (d / "illustration.svg").exists():
        L += ["![Illustration](illustration.svg)", ""]
    L += [f"**Statut : {STATUTS[r['statut']][0]}** · " + " · ".join(meta_ligne(r)), ""]
    if r.get("auteur") or r.get("source"):
        if est_url(r.get("source")):
            src = f"[{nom_source(r)}]({r['source']})"
        else:
            src = r.get("source") or ""
        qui = f"Recette de {r['auteur']}" if r.get("auteur") else ""
        L += ["*" + " — ".join(x for x in (qui, src) if x) + "*", ""]
    if r.get("description"):
        L += [r["description"], ""]
    L += ["## Ingrédients", ""] + [f"- {i}" for i in r["ingredients"]] + [""]
    L += ["## Préparation", ""] + [f"{n}. {e}" for n, e in enumerate(r["etapes"], 1)] + [""]
    if r["notes"]:
        L += ["## Notes", "", "*Précisions ajoutées lors de la transcription.*", ""]
        L += [f"- {n}" for n in r["notes"]] + [""]
    if r["questions"]:
        L += ["## À compléter", ""] + [f"- [ ] {q}" for q in r["questions"]] + [""]
    if (d / "scan.jpg").exists():
        L += ["## Fiche d'origine", "", "<details><summary>Afficher le scan</summary>", "",
              '<img src="scan.jpg" alt="Fiche d\'origine" width="700">', "", "</details>", ""]
    L += ["---", "", "Import Mealie : [`mealie.json`](mealie.json)"]
    if r.get("transcrit_le"):
        L += ["", f"<sub>Transcrite le {r['transcrit_le']}. Fichier source : `recette.yaml`.</sub>"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- HTML autonome
CSS = """
:root{--bg:#fbf8f3;--fg:#2b2622;--muted:#7a6f66;--accent:#b5562c;--card:#fff;--line:#e8e0d6}
@media (prefers-color-scheme:dark){:root{--bg:#1d1a17;--fg:#ece6df;--muted:#a89d92;--accent:#e08a5c;--card:#27231f;--line:#3a342e}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:18px/1.6 Georgia,"Times New Roman",serif}
main{max-width:760px;margin:0 auto;padding:24px 16px 64px}
a{color:var(--accent)}
.retour{font:15px system-ui,sans-serif;text-decoration:none}
.visuel{width:100%;aspect-ratio:8/5;border-radius:14px;overflow:hidden;margin:14px 0 22px;border:1px solid var(--line)}
.visuel img{width:100%;height:100%;object-fit:cover;display:block}
h1{font-size:2.1rem;line-height:1.2;margin:0 0 6px}
.auteur{color:var(--muted);font-style:italic;margin:0 0 6px}
.meta{color:var(--muted);font:15px/1.5 system-ui,sans-serif;display:flex;flex-wrap:wrap;gap:6px 18px;margin-bottom:8px}
.badge{display:inline-block;font:600 12px/1 system-ui,sans-serif;color:#fff;padding:5px 9px;border-radius:99px}
h2{font:600 14px/1 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin:30px 0 12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px}
ul.ing{margin:0;padding-left:1.1em} ul.ing li{margin:4px 0}
ol.steps{margin:0;padding-left:1.4em} ol.steps li{margin:0 0 12px;padding-left:4px}
.notes p{margin:0 0 10px;font-size:16px} .notes p:last-child{margin:0}
details summary{cursor:pointer;color:var(--muted);font:15px system-ui,sans-serif}
details img{width:100%;margin-top:12px;border:1px solid var(--line);border-radius:6px}
footer{margin-top:40px;color:var(--muted);font:13px system-ui,sans-serif}
@media print{body{background:#fff;color:#000;font-size:12pt}.card{border:none;padding:0}details,.retour,.badge{display:none}main{padding:0}.visuel{max-height:6cm}}
"""


def data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def visuel(r):
    d = r["dossier"]
    if (d / "photo.jpg").exists():
        return data_uri(d / "photo.jpg", "image/jpeg"), "Photo du plat"
    if (d / "illustration.svg").exists():
        return data_uri(d / "illustration.svg", "image/svg+xml"), "Illustration"
    return None, None


def badge(r):
    lib, coul = STATUTS[r["statut"]]
    return f'<span class="badge" style="background:{coul}">{lib}</span>'


def page(r):
    e = html.escape
    src, alt = visuel(r)
    bloc_visuel = f'<div class="visuel"><img src="{src}" alt="{alt}"></div>' if src else ""
    meta = "".join(f"<span>{e(m)}</span>" for m in meta_ligne(r))
    morceaux = []
    if r.get("auteur"):
        morceaux.append(f'Recette de {e(r["auteur"])}')
    if est_url(r.get("source")):
        morceaux.append(f'<a href="{e(r["source"])}" target="_blank" rel="noopener">{e(nom_source(r))}</a>')
    auteur = f'<p class="auteur">{" — ".join(morceaux)}</p>' if morceaux else ""
    ing = "\n".join(f"<li>{e(i)}</li>" for i in r["ingredients"])
    eta = "\n".join(f"<li>{e(x)}</li>" for x in r["etapes"])
    notes = ""
    if r["notes"]:
        notes = '<h2>Notes</h2><div class="card notes">' + "".join(f"<p>{e(n)}</p>" for n in r["notes"]) + "</div>"
    quest = ""
    if r["questions"]:
        quest = '<h2>À compléter</h2><div class="card notes">' + "".join(f"<p>☐ {e(q)}</p>" for q in r["questions"]) + "</div>"
    scan = ""
    if (r["dossier"] / "scan.jpg").exists():
        scan = ('<h2>Fiche d\'origine</h2><details><summary>Afficher le scan manuscrit</summary>'
                f'<img src="{data_uri(r["dossier"] / "scan.jpg", "image/jpeg")}" alt="Fiche manuscrite d\'origine"></details>')
    ld = json.dumps(schema_org(r), ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(r['nom'])}</title>
<style>{CSS}</style>
<script type="application/ld+json">
{ld}
</script>
</head><body><main>
<a class="retour" href="index.html">← Toutes les recettes</a>
{bloc_visuel}
<h1>{e(r['nom'])}</h1>
{auteur}
<div class="meta">{meta}</div>
{badge(r)}
<h2>Ingrédients</h2>
<div class="card"><ul class="ing">
{ing}
</ul></div>
<h2>Préparation</h2>
<div class="card"><ol class="steps">
{eta}
</ol></div>
{notes}
{quest}
{scan}
<footer>Transcrite le {e(str(r.get('transcrit_le', '')))}</footer>
</main></body></html>
"""


def sommaire(recettes):
    e = html.escape
    cartes = []
    for r in sorted(recettes, key=lambda r: r["nom"].lower()):
        src, alt = visuel(r)
        img = f'<img src="{src}" alt="">' if src else '<div class="vide"></div>'
        cherche = " ".join([r["nom"], r.get("categorie") or "", *r["mots_cles"]]).lower()
        cartes.append(
            f'<a class="carte" href="{r["slug"]}.html" data-cherche="{e(cherche)}" data-statut="{e(r["statut"])}">'
            f'{img}<div class="txt"><strong>{e(r["nom"])}</strong>'
            f'<span>{e(r.get("categorie") or "")}{" · " + e(r["auteur"]) if r.get("auteur") else ""}</span>'
            f'{badge(r)}</div></a>')
    options = "".join(f'<option value="{e(k)}">{e(v[0])}</option>' for k, v in STATUTS.items())
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mes recettes</title>
<style>{CSS}
main{{max-width:1000px}}
.outils{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 24px}}
.outils input,.outils select{{font:16px system-ui,sans-serif;padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--fg)}}
.outils input{{flex:1;min-width:200px}}
.grille{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px}}
.carte{{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;text-decoration:none;color:var(--fg);display:flex;flex-direction:column}}
.carte img,.carte .vide{{width:100%;aspect-ratio:8/5;object-fit:cover;background:var(--line)}}
.carte .txt{{padding:12px 14px 16px;display:flex;flex-direction:column;gap:6px;align-items:flex-start}}
.carte strong{{font-size:1.1rem;line-height:1.3}}
.carte span:not(.badge){{color:var(--muted);font:14px system-ui,sans-serif}}
</style></head><body><main>
<h1>Mes recettes</h1>
<div class="outils">
<input id="q" type="search" placeholder="Rechercher une recette, un ingrédient, une catégorie…">
<select id="s"><option value="">Tous les statuts</option>{options}</select>
</div>
<div class="grille" id="g">
{chr(10).join(cartes)}
</div>
</main>
<script>
const q=document.getElementById('q'),s=document.getElementById('s');
function f(){{const t=q.value.toLowerCase().trim(),st=s.value;
document.querySelectorAll('.carte').forEach(c=>{{c.style.display=(!t||c.dataset.cherche.includes(t))&&(!st||c.dataset.statut===st)?'':'none'}})}}
q.addEventListener('input',f);s.addEventListener('change',f);
</script>
</body></html>
"""


# ---------------------------------------------------------------- README racine
def index_readme(recettes):
    L = ["| Recette | Catégorie | Auteur | Statut | Reste à faire |", "|---|---|---|---|---|"]
    for r in sorted(recettes, key=lambda r: (ORDRE_STATUT.index(r["statut"]), r["nom"].lower())):
        L.append(f"| [{r['nom']}](recettes/{r['slug']}/README.md) | {r.get('categorie') or ''} | "
                 f"{r.get('auteur') or ''} | {STATUTS[r['statut']][0]} | {len(r['questions']) or '—'} |")
    return "\n".join(L)


def maj_readme(recettes):
    f = RACINE / "README.md"
    txt = f.read_text(encoding="utf-8")
    bloc = f"<!-- INDEX:DEBUT -->\n{index_readme(recettes)}\n<!-- INDEX:FIN -->"
    txt = re.sub(r"<!-- INDEX:DEBUT -->.*?<!-- INDEX:FIN -->", lambda m: bloc, txt, flags=re.S)
    f.write_text(txt, encoding="utf-8")


# ---------------------------------------------------------------- main
def main():
    recettes = charger()
    DOCS.mkdir(exist_ok=True)
    rsvg = shutil.which("rsvg-convert")
    for r in recettes:
        d = r["dossier"]
        (d / "mealie.json").write_text(json.dumps(schema_org(r), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "README.md").write_text(markdown(r), encoding="utf-8")
        svg, png = d / "illustration.svg", d / "illustration.png"
        if rsvg and svg.exists() and (not png.exists() or png.stat().st_mtime < svg.stat().st_mtime):
            subprocess.run([rsvg, "-w", "1200", str(svg), "-o", str(png)], check=True)
        (DOCS / f"{r['slug']}.html").write_text(page(r), encoding="utf-8")
        print(f"✓ {r['slug']}  ({STATUTS[r['statut']][0]})")
    (DOCS / "index.html").write_text(sommaire(recettes), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    maj_readme(recettes)
    print(f"{len(recettes)} recette(s) générée(s).")


if __name__ == "__main__":
    main()
