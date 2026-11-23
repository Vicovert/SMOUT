# SMOUT — état du projet

_Mis à jour à la fin de chaque tâche (voir `CLAUDE.md`, « Méthode de travail »). Historique détaillé des versions : `claude/feuille-de-route.md`._

**Dernière mise à jour : 23/11/2026**

## En ligne
- Version : **8.16** (release Windows seule `SMOUT.8.16.exe`, 24/11/2026 ; site https://vicovert.github.io/SMOUT/ à jour). Mot piégé en direct (mot à trouver et frappe des autres), thème propre à chaque grille adverse, mot du jour repris avec ses essais.
- Protocole multi : `VERSION_JEU` 8.10, données sous `/v7`

## À faire par Victor
- [ ] Republier `database.rules.json` dans la console Firebase (changements des 8.9, 8.10, 8.15 et 8.16 : `horloge`, abandon d'un salon après 30 min, `nb ≤ 8` joueurs, `frappe` et `theme` des joueurs).
- [ ] Coller les instructions de projet (`claude/instructions-projet.md`) dans les réglages du projet.

## En cours
- Configuration de l'espace de travail : terminée (PR #1), Claude fusionne désormais lui-même les PR.

## Prochaines pistes (non commencées)
- Supprimer les branches inutiles (dont `travail-8.14`, `travail-8.15`, `travail-8.16`, `doc-etat-8.14`, `doc-etat-8.15`, `doc-etat-8.16`) : `travail-8.10`, `travail-8.11`, `travail-8.12`, `regles-etape3`, `v4.3`, `v5.0`, `v6.0`, `v7.0`.
- Corriger `tests/README.md` (dit encore que les tests tournent sur `main`).
- Test automatique d'équivalence PC ↔ web des constantes (`REGLES_MODES`, `RUSHS`, `COULEURS_MODES`).
- Règles Firebase : empêcher l'hôte d'écrire n'importe quel score.
- README public (lien du site et des releases).

## Points ouverts
- Les fils cloud poussent sur des branches `claude/...` alors que le CI ne teste que `travail-*` : à trancher.

## Notes techniques
- Tests PC : `tests/test_solo_base.py` et `tests/test_solo_72.py` affichent « RAPPEL TK EN ECHEC » (fonction, arguments, pile) si un rappel Tkinter plante. `design.py` ignore les appels Tk sans événement (parasites, vus sur le CI quand une fenêtre sous le pointeur est recréée).
