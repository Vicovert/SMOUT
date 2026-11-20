# Banc de test SMOUT

`tests/lancer_tests.sh` lance tous les tests en local, sans toucher à la vraie base Firebase :

- `fb_regles.py` : faux serveur Firebase qui applique les règles v7 (`database.rules.json`) — `test_regles.py` vérifie 31 cas ;
- `robot_pc.py` : joueur PC (vrai code Tkinter, sous Xvfb) ; `web/robot_web.js` : joueur web (vraie page, Chrome sans écran) ;
- `scenario.sh` : parties croisées PC ↔ web (les 8 modes, mot de passe, plusieurs joueurs, plantage, « Rejouer ») dont `verif_scores.py` contrôle les scores selon la règle de chaque mode ;
- `test_solo_base.py`, `test_solo_72.py` : solo PC ; `web/solo_web.js`, `web/solo72_web.js`, `web/hors_ligne.js` : solo web, téléphone et hors ligne.

Ils tournent automatiquement sur GitHub à chaque push sur `main` : la release (Windows, Mac, Linux) et le site ne sont publiés que s'ils passent.
Prérequis en local : Python avec tkinter et `requests`, `xvfb-run`, Node.js, Chrome (`CHROME=…`), puis `cd tests/web && npm install`.
