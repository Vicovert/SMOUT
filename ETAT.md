# SMOUT — état du projet

_Mis à jour à la fin de chaque tâche (voir `CLAUDE.md`, « Méthode de travail »). Historique détaillé des versions : `claude/feuille-de-route.md`._

**Dernière mise à jour : 24/11/2026**

## En ligne
- Version : **8.19** (release Windows seule `SMOUT.8.19.exe`, 24/11/2026 ; site https://vicovert.github.io/SMOUT/ à jour). Création de compte corrigée (protection contre l'énumération des e-mails). 8.18 : téléphone sur un écran (adversaires en haut), clavier du jeu seul, pas de zoom au double appui, clavier qui suit la taille. 8.17 : comptes e-mail, pause/reprise, « Donner l'hôte ».
- Protocole multi : `VERSION_JEU` 8.10, données sous `/v7`

## À faire par Victor
- [x] E-mail/Mot de passe activé et règles Firebase republiées (fait par Victor le 24/11/2026).
- [ ] Tester la 8.19 : création de compte, connexion sur un 2e appareil, partie multijoueur sur téléphone (pas de défilement, pas de zoom au double appui, « + » agrandit le clavier).
- [ ] Supprimer les branches inutiles : `claude/project-thread-y6lqmp`, `doc-etat-8.17`, `regles-etape3`, `travail-8.10` à `travail-8.13`, `v4.3`, `v5.0`, `v6.0`, `v7.0` (et, facultatif, les sauvegardes d'avant le 24/11).

## En cours
- Configuration de l'espace de travail : terminée (PR #1), Claude fusionne désormais lui-même les PR.

## Prochaines pistes (non commencées)
- Corriger `tests/README.md` (dit encore que les tests tournent sur `main`).
- Test automatique d'équivalence PC ↔ web des constantes (`REGLES_MODES`, `RUSHS`, `COULEURS_MODES`).
- Règles Firebase : empêcher l'hôte d'écrire n'importe quel score.
- README public (lien du site et des releases).

## Points ouverts
- Zoom au double appui : bloqué et testé dans Chrome sans écran ; à confirmer sur un vrai iPhone et un vrai Android.
- Téléphone très petit (360×640) à 8 joueurs : la page de jeu dépasse encore d'environ 60 px.
- Les fils cloud poussent sur des branches `claude/...` alors que le CI ne teste que `travail-*` : à trancher.

## Notes techniques
- Tests PC : `tests/test_solo_base.py` et `tests/test_solo_72.py` affichent « RAPPEL TK EN ECHEC » (fonction, arguments, pile) si un rappel Tkinter plante. `design.py` ignore les appels Tk sans événement (parasites, vus sur le CI quand une fenêtre sous le pointeur est recréée).
