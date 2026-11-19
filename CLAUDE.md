# SMOUT — consignes pour Claude Code

Jeu de mots type Motus, SOLO ou multijoueur, plusieurs modes de jeu.
Deux clients à logique identique : **bureau (Python/Tkinter)** et **web (JS vanille)**, multijoueur via **Firebase Realtime Database (REST, auth anonyme)**.
Site : https://vicovert.github.io/SMOUT/ — Dépôt : Vicovert/SMOUT. **Toujours répondre en français.**

## Structure
- `main.py`, `page_solo.py`, `page_multi.py`, `design.py` : appli bureau (composants UI dans `design.py`, `VERSION_APP` y est définie)
- `web/` : `smout.js`, `style.css`, `index.html` ; `outils/export_web.py` génère `donnees.js` (dont la version) pour le site
- `database.rules.json` : règles Firebase (chemin `/v7`, `VERSION_JEU`). **Je ne publie jamais les règles dans la console Firebase : c'est l'utilisateur qui le fait.**
- `tests/` : banc de test (faux serveur Firebase `fb_regles.py`, robots PC/web, scénarios croisés)
- `.github/workflows/release.yml` (push sur `main` → tests + release Windows/Mac/Linux) et `pages.yml` (site)

## Règle d'équivalence
Toute règle ou logique de jeu modifiée côté PC doit l'être à l'identique côté web (modes, `COULEURS_MODES`, `REGLES_MODES`, `RUSHS`, composants `Curseur`/`curseur`, etc.) et inversement.

## Versions et releases (OBLIGATOIRE à chaque mise à jour)
- Chaque mise à jour du code : incrémenter le **second chiffre** (8.2 → 8.3). Grosse mise à jour : premier chiffre +1, second remis à 0.
- Mettre à jour `VERSION_APP` dans `design.py` (le web la lit via `export_web.py`).
- Une release à chaque fois, avec builds **Windows, Mac et Linux** : on travaille sur une branche `travail-X.Y`, puis squash-merge dans `main` et push → le workflow publie la release.
- Message du commit sur `main` : ligne de résumé = **tag** (ex. `8.2`), corps = notes de version au format `-élément`, un par bloc séparé d'une ligne vide, puis les lignes d'attribution.
- Vérifier ensuite les assets `SMOUT.X.Y_{LINUX.tar.gz,MACOS.zip,WINDOWS.exe}` : `gh api repos/Vicovert/SMOUT/releases/tags/X.Y`.
- Mettre à jour le doc de projet `claude/feuille-de-route.md` (entrée de la version).
- Après chaque mise à jour : **lister clairement et brièvement les modifications**.

## Modèle et effort
Pour chaque tâche, **indiquer le modèle et l'effort à utiliser**. Si des tâches peuvent être découpées pour des modèles inférieurs, **s'arrêter** et attendre que l'utilisateur change de modèle avant de continuer.

## Tests (à lancer avant toute release)
Local (sans navigateur cloud, uniquement Chrome headless via puppeteer-core et Tk sous Xvfb) :
- Faux Firebase : `(setsid nohup python3 tests/fb_regles.py 9000 >/dev/null 2>&1 &)`
- Site local : `python3 outils/export_web.py /tmp/site` puis `(cd /tmp/site && setsid nohup python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1 &)`
- Suite complète (~10 min, la lancer en arrière-plan et la surveiller) : `PY=python3 tests/lancer_tests.sh`
  (la suite coupe le serveur http à la fin : le relancer avant un test isolé)
- Scénario croisé isolé : `DUREE=150 tests/scenario.sh c1 'pc:{...}' 'web:{...}'`
- Dépendances : `xvfb`, `python3-tk`, `pip install requests`, `cd tests/web && npm install`
- Les tests d'une étape "Croisé" peuvent échouer ponctuellement (le CI relance une fois) ; relancer l'étape seule avant de conclure à une régression.

## Pièges connus
- Ne pas passer une fonction à paramètre optionnel directement en `onclick` (l'événement devient le 1er argument).
- Les thèmes personnalisés peuvent être incomplets : fusionner avec le thème par défaut.
- Jetons de rafraîchissement du faux serveur : nettoyer `$HOME` des robots avant chaque scénario (déjà fait dans `scenario.sh`).

## Interdits
- Ne pas utiliser de navigateur distant/cloud pour tester.
- Ne pas toucher à la console Firebase ni aux secrets.
