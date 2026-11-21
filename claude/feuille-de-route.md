# SMOUT — feuille de route

Une entrée par version (la plus récente en haut). Voir `CLAUDE.md` pour la procédure de release.

## 8.7
- Accueil (PC et web) : Solo et Multijoueur côte à côte, chacun de sa couleur (rouge « bien placé » / jaune « mal placé » du thème) ; le Mot du jour, à part en dessous, en bleu clair.
- Web, téléphone : clavier du jeu refait (touches plus larges et hautes, pleine largeur, appui immédiat sans délai ni zoom, vibration légère, ⌫ et ↵).
- Web, téléphone : bouton « ⌨ Clavier du téléphone » en jeu (solo et multi) pour taper avec le clavier natif (champ invisible : lettres, accents ramenés à la lettre, effacer, entrée), préférence mémorisée ; absent sur ordinateur, qui utilise déjà le clavier physique.
- Tests : nouveau `tests/web/clavier_tel.js` (accueil, taille des touches, saisie native).

## 8.6
- Nouveau mode multijoueur « Mot piégé » (bleu `#5B7CFA`) : chacun choisit en secret (30 s, mot au hasard sinon) le mot que son voisin devra deviner, puis devine celui qu'on lui a choisi. Paires tirées au lancement, décalage différent à chaque manche, 2 joueurs minimum.
- Barème : chaque paire distribue autant de points que d'essais ; le devineur a le barème Précision, le choisisseur les essais ratés (0 si mot au hasard).
- Confidentialité par les règles Firebase (`v7/pieges`, mot jamais lisible par sa cible) : les essais sont évalués par le choisisseur, ou par un autre joueur s'il est parti, qui révèle le mot en fin de paire. **Règles à republier dans la console** (compatibles 8.5).
- `VERSION_JEU` passe à 8.6 : les clients 8.5 ne jouent plus avec les 8.6.
- Web : portage strictement équivalent (`smout.js`) ; PC : `page_multi.py`.
- Tests : 33 cas de règles, 3 parties PC, 3 parties croisées PC ↔ web (choix invalide, mot au hasard, joueur parti, évaluation de secours), robot web étendu. Suite complète 24/24.
- Limites connues : l'hôte peut déjà écrire n'importe quel score ; à 2 joueurs, si l'un part, la paire de l'autre est annulée.

## 8.5
- Reprend les 8.3 et 8.4 (jamais publiées : leur CI a échoué sur les nouvelles vérifications de scores) avec les correctifs.
- Élimination : le contrôle de score accepte les deux ordres (BOB = 0, les autres = 1 et 2), car le plus lent est éliminé au hasard des temps.
- CI : le journal de la 1re tentative est conservé (`/tmp/essai1`) avant la relance, pour diagnostiquer les échecs ponctuels (un `Traceback` isolé à l'étape « Solo PC » a été vu une fois, non reproductible).

## 8.4 (non publiée, incluse dans la 8.5)
- Reprend la 8.3 (jamais publiée : son CI a échoué sur la nouvelle vérification des scores) avec le correctif.
- Vérification des scores : référence = scores relevés par l'hôte (avant « Rejouer », qui remet les scores à 0) ; cohérence entre joueurs contrôlée sur les scores finaux seulement.

## 8.3 (non publiée, incluse dans la 8.4)
- Banc de tests : 5 parties croisées PC ↔ web ajoutées (Mystère ×2, Rush ×2, Précision avec défaite), de sorte que les 8 modes multijoueur sont couverts.
- Vérification automatique des scores (`tests/verif_scores.py`) : chaque partie croisée est contrôlée selon la règle de son mode, et tous les joueurs doivent voir les mêmes scores.
- CI : délai maximal du workflow de release porté à 75 min (suite plus longue).

## 8.2
- Multijoueur : « Créer un salon » / « Rejoindre un salon » (code ou liste), plus de Partie rapide.
- Salon privé : cadenas, couleurs public/privé, champ « Mot de passe ».
- Curseurs (plage de lettres, manches, temps, essais) dans le salon et les Paramètres solo.
- Salon épuré : modes en pastilles, règle sur une ligne, invités avec simple bandeau.
- Thèmes : aperçu fixe pendant le défilement, plus de retour en haut de page (PC et web).
- Logo SMOUT aux couleurs de MOTUS.
- Correctif : thème personnalisé incomplet. Banc de tests fiabilisé.

## Pistes
- (à compléter)
