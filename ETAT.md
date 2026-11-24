# SMOUT — état du projet

_Mis à jour à la fin de chaque tâche (voir `CLAUDE.md`, « Méthode de travail »). Historique détaillé des versions : `claude/feuille-de-route.md`._

**Dernière mise à jour : 24/11/2026**

## En ligne
- Version : **9.1** (release Windows seule `SMOUT.9.1.exe`, 24/11/2026 ; site https://vicovert.github.io/SMOUT/ à jour). Fenêtres du jeu, spectateurs, demandes pour regarder une partie en cours (cloche de l'hôte), code du salon en partie.
- Protocole multi : `VERSION_JEU` 9.1, données sous `/v7` (spectateurs, demandes)

## À faire par Victor
- [x] E-mail/Mot de passe activé et règles Firebase republiées (fait par Victor le 24/11/2026).
- [x] 8.19 testée par Victor (comptes, téléphone).
- [x] Idées 9.1 à 9.3 décrites et décisions prises : voir `claude/passations/2026-11-24-plan-9.1-9.3.md`.
- [ ] **Republier `database.rules.json`** (9.1 : spectateurs, demandes) : sans cela, spectateurs et demandes échouent en ligne.
- [ ] Tester la 9.1 à plusieurs (salon plein → spectateur, demande pendant une partie, cloche de l'hôte).
- [x] Branches inutiles supprimées (24/11/2026).

## En cours
- Configuration de l'espace de travail : terminée (PR #1), Claude fusionne désormais lui-même les PR.

## Prochaines pistes (non commencées)
- 9.2 : amis (code ami) et invitations ; 9.3 : classements mot du jour et marathon + fiche joueur (ancienneté). Détails : `claude/passations/2026-11-24-plan-9.1-9.3.md`.
- Corriger `tests/README.md` (dit encore que les tests tournent sur `main`).
- Test automatique d'équivalence PC ↔ web des constantes (`REGLES_MODES`, `RUSHS`, `COULEURS_MODES`).
- Règles Firebase : empêcher l'hôte d'écrire n'importe quel score.
- README public (lien du site et des releases).

## Points ouverts
- CI : 8 jobs de tests (base PC, base web, 6 tranches de parties), environ 4 min ; objectif 10 min au plus entre validation et release.
- GitHub Pages doit rester sur la source « GitHub Actions » (incident du 24/11 : passée en « Deploy from a branch », site cassé puis rétabli).
- Zoom au double appui : bloqué et testé dans Chrome sans écran ; à confirmer sur un vrai iPhone et un vrai Android.
- Téléphone très petit (360×640) à 8 joueurs : la page de jeu dépasse encore d'environ 60 px.
- Les fils cloud poussent sur des branches `claude/...` alors que le CI ne teste que `travail-*` : à trancher.

## Notes techniques
- Tests PC : `tests/test_solo_base.py` et `tests/test_solo_72.py` affichent « RAPPEL TK EN ECHEC » (fonction, arguments, pile) si un rappel Tkinter plante. `design.py` ignore les appels Tk sans événement (parasites, vus sur le CI quand une fenêtre sous le pointeur est recréée).
