# SMOUT — état du projet

_Mis à jour à la fin de chaque tâche (voir `CLAUDE.md`, « Méthode de travail »). Historique détaillé des versions : `claude/feuille-de-route.md`._

**Dernière mise à jour : 23/11/2026**

## En ligne
- Version : **8.15** (release Windows seule `SMOUT.8.15.exe`, 23/11/2026 ; site https://vicovert.github.io/SMOUT/ à jour). 8 joueurs max, Mot piégé « cible cachée », grilles adverses adaptées de 2 à 8 joueurs.
- Protocole multi : `VERSION_JEU` 8.10, données sous `/v7`

## À faire par Victor
- [ ] Republier `database.rules.json` dans la console Firebase (changements des 8.9, 8.10 et 8.15 : `horloge`, abandon d'un salon après 30 min, `nb ≤ 8` joueurs).
- [ ] Coller les instructions de projet (`claude/instructions-projet.md`) dans les réglages du projet.

## En cours
- 8.16 (branche `travail-8.16`, tests CI en cours) : Mot piégé (mot à trouver et frappe en direct des autres), thème propre à chaque grille adverse, mot du jour repris avec ses essais. **Victor : republier `database.rules.json` après la fusion.**
- Configuration de l'espace de travail : terminée (PR #1), Claude fusionne désormais lui-même les PR.

## Prochaines pistes (non commencées)
- Supprimer les branches inutiles : `travail-8.10`, `travail-8.11`, `travail-8.12`, `regles-etape3`, `v4.3`, `v5.0`, `v6.0`, `v7.0`.
- Corriger `tests/README.md` (dit encore que les tests tournent sur `main`).
- Test automatique d'équivalence PC ↔ web des constantes (`REGLES_MODES`, `RUSHS`, `COULEURS_MODES`).
- Règles Firebase : empêcher l'hôte d'écrire n'importe quel score.
- README public (lien du site et des releases).

## Points ouverts
- Les fils cloud poussent sur des branches `claude/...` alors que le CI ne teste que `travail-*` : à trancher.
