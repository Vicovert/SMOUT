# SMOUT — consignes pour Claude Code

Jeu de mots type Motus, SOLO ou multijoueur, plusieurs modes de jeu.
Deux clients à logique identique : **bureau (Python/Tkinter)** et **web (JS vanille)**, multijoueur via **Firebase Realtime Database (REST, auth anonyme)**.
Site : https://vicovert.github.io/SMOUT/ — Dépôt : Vicovert/SMOUT. **Toujours répondre en français.**

## Structure
- `main.py`, `page_solo.py`, `page_multi.py`, `design.py` : appli bureau (composants UI dans `design.py`, `VERSION_APP` y est définie)
- `web/` : `smout.js`, `style.css`, `index.html` ; `outils/export_web.py` génère `donnees.js` (dont la version) pour le site
- `database.rules.json` : règles Firebase (chemin `/v7`, `VERSION_JEU`). **Je ne publie jamais les règles dans la console Firebase : c'est l'utilisateur qui le fait.**
- `tests/` : banc de test (faux serveur Firebase `fb_regles.py`, robots PC/web, scénarios croisés)
- `.github/workflows/release.yml` (push sur `travail-*` → tests en 4 jobs parallèles ; push sur `main` → build Windows + release, sans retester) et `pages.yml` (site, publié dès le push sur `main`)

## Règle d'équivalence
Toute règle ou logique de jeu modifiée côté PC doit l'être à l'identique côté web (modes, `COULEURS_MODES`, `REGLES_MODES`, `RUSHS`, composants `Curseur`/`curseur`, etc.) et inversement.

## Versions et releases (OBLIGATOIRE à chaque mise à jour)
- Chaque mise à jour du code : incrémenter le **second chiffre** (8.2 → 8.3). Grosse mise à jour : premier chiffre +1, second remis à 0.
- Mettre à jour `VERSION_APP` dans `design.py` (le web la lit via `export_web.py`).
- Une release à chaque fois, avec **un seul fichier `SMOUT.X.Y.exe` (Windows)** ; plus de builds Mac ni Linux. On travaille sur une branche `travail-X.Y`, PR vers `main`, puis **Claude squash-merge lui-même** une fois les tests verts → le workflow publie la release.
- **Sauvegarde avant chaque fusion dans `main`** (obligatoire, c'est ce qui dispense du feu vert de Victor) : créer une branche `sauvegarde/AAAAMMJJ-HHMM` (heure de Paris) depuis `main`, avec l'outil GitHub `create_branch` (le push de tags est refusé depuis les fils cloud). Elle ne déclenche aucun workflow. Retour arrière possible depuis cette branche.
- Message du commit sur `main` : ligne de résumé = **tag** (ex. `8.2`), corps = notes de version au format `-élément`, un par bloc séparé d'une ligne vide, puis les lignes d'attribution.
- Vérifier ensuite l'asset `SMOUT.X.Y.exe` : `gh api repos/Vicovert/SMOUT/releases/tags/X.Y` (dans les fils cloud, outil GitHub `get_release_by_tag`).
- Mettre à jour le doc de projet `claude/feuille-de-route.md` (entrée de la version) et `ETAT.md`.
- Après chaque mise à jour : **lister clairement et brièvement les modifications**.

## Modèle et effort
Pour chaque tâche, **indiquer le modèle et l'effort conseillés** (ex. « Sonnet, effort moyen ») et pourquoi, pour économiser le quota. **Quand Victor doit changer de modèle (ou d'effort) pour la suite, s'arrêter** : le dire clairement (modèle et effort à choisir) et attendre qu'il ait changé avant de continuer. Les sous-agents d'un modèle inférieur restent possibles s'ils sont rentables pour le quota.

## Méthode de travail (fils du projet)
- **Honnêteté** : dire ce qui a été vérifié, ce qui ne l'a pas été, et ce qui a échoué. Poser autant de questions que nécessaire avant de coder quand la demande est ambiguë.
- **Plan validé par Claude** : pour une demande de code, le fil rédige un plan, le relit et le valide lui-même (ou le coordinateur le fait) ; Victor n'est sollicité que pour les choix qui changent le but et les règles Firebase (qu'il publie lui-même).
- **Fusion des PR par Claude** : Victor ne fusionne jamais lui-même. Claude squash-merge ses PR dans `main` dès que les tests sont verts (CI ou local, voir « Tests »), sans demander, **après avoir créé la sauvegarde** (voir « Versions et releases »), puis vérifie la release et le site. Une PR de documentation seule qui modifie aussi un workflow se fusionne avec `[skip ci]` dans le titre, sinon une fausse release est créée.
- **Instruction répétée** : quand Victor donne **2 fois** la même instruction (dans un même fil ou d'un fil à l'autre), l'ajouter à ce `CLAUDE.md` dans la section qui convient, dans le même fil.
- **État du projet** : tenir `ETAT.md` à jour à la fin de chaque tâche (version en ligne, travail en cours, à faire par Victor).
- **Contexte trop gros** : quand un fil devient long (réponses qui ralentissent, nombreux fichiers relus, plusieurs résumés de contexte), le clore avec la procédure `claude/PASSATION.md` et demander au coordinateur d'ouvrir un nouveau fil.
- **Leçons apprises** : les noter dans `claude/lecons.md` (une ligne par leçon, la plus récente en haut) à la clôture d'un fil.
- Les changements de documentation seule (`*.md`, `claude/`) ne changent pas la version et ne déclenchent ni tests ni release.

## Tests (une seule fois : **soit** dans le CI, **soit** en local, jamais les deux)
Par défaut : le CI, en poussant `travail-X.Y`. En local seulement si le CI est indisponible ; dans ce cas, mettre `[skip ci]` dans le dernier commit poussé sur `travail-X.Y` pour ne pas retester une seconde fois.
Local (sans navigateur cloud, uniquement Chrome headless via puppeteer-core et Tk sous Xvfb) :
- Faux Firebase : `(setsid nohup python3 tests/fb_regles.py 9000 >/dev/null 2>&1 &)`
- Site local : `python3 outils/export_web.py /tmp/site` puis `(cd /tmp/site && setsid nohup python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1 &)`
- **Ne pas lancer la suite complète en local** (25 min, séquentielle) : le CI la fait en ~8 min en parallèle dès qu'on pousse `travail-X.Y`. Si on teste par le CI, aucun test local en plus. Avant le squash-merge : attendre que les 4 jobs « Tests » de la branche soient verts (`actions_list`), puis squash-merger (la release de `main` ne retestant pas, l'arbre doit être celui de la branche testée).
- Suite complète en local (secours) : `PY=python3 tests/lancer_tests.sh` ; une partie seulement : `GROUPE=base|croise-a|croise-b|piege`
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
