# SMOUT — état du projet

_Mis à jour à la fin de chaque tâche (voir `CLAUDE.md`, « Méthode de travail »). Historique détaillé des versions : `claude/feuille-de-route.md`._

**Dernière mise à jour : 23/11/2026**

## En ligne
- Version : **8.13** (release Windows seule `SMOUT.8.13.exe`, 23/11/2026 ; site https://vicovert.github.io/SMOUT/). 8.10 était la dernière avec Mac / Linux.
- Protocole multi : `VERSION_JEU` 8.10, données sous `/v7`

## À faire par Victor
- [ ] Republier `database.rules.json` dans la console Firebase (changements des 8.9 et 8.10 : `horloge`, abandon d'un salon après 30 min).
- [ ] Coller les instructions de projet (`claude/instructions-projet.md`) dans les réglages du projet.

## En cours
- Configuration de l'espace de travail : terminée (PR #1), Claude fusionne désormais lui-même les PR.

## Prochaines pistes (non commencées)
- Supprimer les branches inutiles : `travail-8.10`, `travail-8.11`, `travail-8.12`, `regles-etape3`, `v4.3`, `v5.0`, `v6.0`, `v7.0`.
- Corriger `tests/README.md` (dit encore que les tests tournent sur `main`).
- Test automatique d'équivalence PC ↔ web des constantes (`REGLES_MODES`, `RUSHS`, `COULEURS_MODES`).
- Règles Firebase : empêcher l'hôte d'écrire n'importe quel score.
- README public (lien du site et des releases).

## Points ouverts
- Les fils cloud poussent sur des branches `claude/...` alors que le CI ne teste que `travail-*` : à trancher.
