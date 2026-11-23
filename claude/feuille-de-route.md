# SMOUT — feuille de route

Une entrée par version (la plus récente en haut). Voir `CLAUDE.md` pour la procédure de release.

## 8.13
- Menu Solo plus attrayant (design « C » validé par Victor), PC et web : titre « SOLO » en tuiles colorées, grand bouton « Jouer » en dégradé, puis Marathon (violet, record en sous-titre) et Paramètres (réglages en cours), chacun avec son icône (▶, ∞, engrenage). `CarteMenu` gagne `icone`, `degrade`, `rond`, `grand`.

## 8.12
- Mystère (multi) : un joueur qui a trouvé le mot n'apparaît plus « Pas trouvé » sous sa mini-grille chez les autres (la case de la lettre cachée était comptée comme ratée), PC et web.

## 8.11
- Podium de fin de partie : les joueurs ex aequo ont la même hauteur de marche (hauteur choisie selon le rang, plus selon la place), PC et web.

## 8.10
- Mot piégé : toutes les cases du mot à choisir sont affichées dès le départ ; celles au-delà de la longueur minimale sont en pointillé (« facultatives »), pour qu'on voie qu'on peut écrire 6 **ou** 7 lettres.
- Mot piégé : seul l'hôte voit le bouton « Forcer le démarrage » (mis à jour en continu, aussi après un changement d'hôte) ; plus de fenêtre de confirmation, retour visuel « c'est parti ! ». Un mot de secours refusé est retenté.
- Mot piégé : « Ton mot : … » s'affiche sous la mini-grille du joueur concerné (plus sous sa propre grille).
- Mini-grilles des adversaires plus grandes quand il y a peu de joueurs (jusqu'à 30 px avec 1 adversaire, 24 px avec 2, 18 px au-delà), PC et web.
- Plus de déconnexion pour inactivité : un joueur inactif n'est plus retiré du salon (il apparaît « Déconnecté ») ; s'il a été retiré quand même, il se réinscrit tout seul ; l'hôte inactif est relayé par un joueur actif ; un salon n'est supprimable qu'après 30 min sans signe de vie (au lieu de 2). Les paires du Mot piégé se font entre joueurs actifs.
- `VERSION_JEU` 8.10 ; **règles Firebase à republier** (délai d'abandon d'un salon : 30 min).
- Tests : 69/69 règles, robots mis à jour (clic réel sur « Forcer le démarrage », « Ton mot » sous la grille de la cible).

## 8.9
- Web : clavier du jeu « aplati » en multijoueur corrigé (régression de la 8.7 : le clavier s'écrasait en colonne étroite à côté des mini-grilles).
- Mot piégé : plus de limite de temps pour choisir son mot ; la devinette commence quand tous les mots sont choisis, ou quand l'hôte clique « Forcer le démarrage » (mot au hasard pour ceux qui n'ont rien choisi). Le temps de jeu ne court qu'à partir de là. Avancement « n sur m mots choisis ». Longueur libre dans la plage du salon (6 **ou** 7 lettres : une case de plus apparaît à chaque lettre).
- Mot piégé : verdicts plus rapides (rafraîchissement du salon toutes les 0,35 s au lieu de 0,8 s). Les mots choisis sont vérifiés dans le dictionnaire au moment du choix (PC et web) ; les mots tirés au hasard viennent de la liste de jeu.
- L'hôte peut ramener tout le monde au salon en cours de partie (bouton « Retour au salon » + confirmation), tous modes, PC et web.
- Bug « salon invisible » (liste et code) : (1) horloge locale décalée de plus de 30 s → le web comparait l'âge de l'annonce à sa propre heure ; il se synchronise maintenant sur le serveur (nouveau chemin `v7/horloge/$uid` dans les règles, **à republier**) ; (2) ancienne version du site gardée par le cache hors ligne → rechargement automatique à la mise à jour, et salons d'une autre version désormais signalés dans la liste au lieu d'être cachés.
- Salon : l'invité voit les réglages choisis par l'hôte (manches, temps, essais, lettres, choix du mot) en lecture seule, sans les curseurs (PC et web).
- Mot piégé : on voit le mot qu'on a choisi pour sa cible (jamais ceux des autres), pendant l'attente et la devinette.
- Mot piégé : barème simplifié, **1 point si on trouve son mot, 0 sinon** (le choisisseur ne marque pas ; remplace le barème équilibré de la 8.6).
- `VERSION_JEU` 8.9 (protocole : fin du choix infinie par défaut).
- Tests : `horloge_decalee.js`, 4 cas de règles (68/68), parties « retour au salon » (hôte web et hôte PC), démarrage forcé dans les parties Mot piégé ; robot PC à la taille réelle de fenêtre, longueur de mot alternée (mini/maxi).
- **Règles Firebase à republier** (`database.rules.json` : ajout de `horloge`).

## 8.8
- CI plus rapide : tests joués une seule fois, sur la branche `travail-*` (4 jobs parallèles : base, croisés a/b, Mot piégé ; ≈ 8 min au lieu de ≈ 20), plus de re-test sur `main`.
- Sur `main` : builds Windows/Mac/Linux + release directement (≈ 5 min) ; le site web est publié tout de suite par `pages.yml`.
- `tests/lancer_tests.sh` accepte `GROUPE=…` pour ne jouer qu'une partie de la suite.
- Web : le bouton « retour » du téléphone (ou Alt+←) revient à l'écran précédent comme la flèche de l'écran, ferme d'abord une fenêtre ouverte, demande confirmation en partie, et ne quitte la page que depuis l'accueil (`tests/web/retour_tel.js`). Non vérifié sur un vrai téléphone.

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
