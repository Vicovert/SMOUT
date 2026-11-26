# SMOUT — feuille de route

Une entrée par version (la plus récente en haut). Voir `CLAUDE.md` pour la procédure de release.

## 9.13
- Panneau sur le côté (à droite) qui réunit le profil et les amis (version A validée par Victor : onglets « Profil » / « Amis »), ouvert par l'avatar seul : plus d'écran Amis ni de bouton Amis, plus de fenêtre « Ton pseudo ». S'ouvre sur « Amis » s'il y a des demandes ; pastille rouge des demandes sur l'avatar (accueil) ; multijoueur : le pseudo (site) ou l'avatar (PC) ouvre le panneau. PC et web (`panneauProfil` / `panneau_profil`). Sur PC, pas de voile assombri (Tk ne sait pas faire de transparence) : le panneau se ferme par la croix ou Échap.
- Tests adaptés : `amis_web.js` (17), `compte_web.js` (16), `test_amis_pc.py` (15).

- Série actuelle du mot du jour en petite pastille 🔥 à droite du pseudo : classement, fiche joueur, et posée sur mon avatar de l'accueil (dessinée dans le même canevas sur PC : pas de cadre) (pas dans « Ton pseudo », demandes de Victor). PC et web.
- Classement du mot du jour : en-têtes « Mots » (pastille bleue, couleur de la carte Mot du jour) et « Moyenne » ; plus de colonne « série ».
- Fiche joueur : Mots du jour, Moyenne, Record marathon.

- Classement du mot du jour (maquette validée par Victor sur pages complètes) : tri par nombre total de mots du jour trouvés, puis moyenne d'essais (pour ne pas « tout perdre » le jour où le mot est raté) ; colonnes « trouvés » · « moy. essais » · « série » (série actuelle, 🔥) ; « Aujourd'hui : 3 essais / raté / pas joué » sous le pseudo. PC et web. Base : `classements/mdj/<uid>/trouves` (règles publiées automatiquement). Un joueur encore sur une ancienne version n'apparaît qu'une fois passé en 9.11.
- Tests : règles 140/140, `classements_web.js` (14), `test_classements_pc.py` (7).

- Classement du marathon (maquette validée par Victor sur pages complètes) : 2 lignes par joueur (pseudo, puis réglages de la meilleure partie : essais, longueur des mots, difficile), colonnes « mots » (de cette partie) et « meilleur » ; PC et web. Nouvelle stat `marathon.meilleur_detail` ; base `classements/marathon/<uid>` : `mots`, `essais`, `lmin`, `lmax`, `difficile` (règles publiées automatiquement). Records antérieurs : « – » et pas de réglages jusqu'à la prochaine meilleure partie.
- Pseudos limités à 10 caractères partout (au lieu de 15) ; les plus longs sont coupés à 10.
- Tests : règles 138/138, `classements_web.js` (14), `solo_web.js` (pseudo de 10 caractères).

- Grand écran (site sur ordinateur et appli PC) : classements de l'accueil (mot du jour) et du menu Solo (marathon) centrés sous les cartes, 460 px de large (440 sur PC), comme sur téléphone (version « A moins large » validée par Victor). Le classement en direct du marathon en partie garde sa colonne à gauche.
- Numéro de version en haut à gauche de l'accueil (« v9.9 »), à la place de la ligne du bas.

- Classement du mot du jour (style C validé par Victor) : colonnes « série max » · « moy. essais » · « aujourd'hui » ; tri par meilleure série puis, à égalité, par moyenne d'essais la plus basse (raté = 8, calculée depuis les stats, donc aussi pour les parties passées ; pas de minimum de parties). Pastille de moyenne verte ≤ 3,5, jaune ≤ 4,5, rouge au-delà. Base : `classements/mdj/<uid>/moyenne` (règles publiées automatiquement).
- Tous les classements (mot du jour, marathon) : la liste entière, 5 lignes visibles, on fait défiler ; ma ligne reste collée en bas (ou en haut si on a défilé au-delà). Site : `position: sticky` ; PC : `Defilant` + ligne épinglée.
- Accueil : tableau plus large (site 420 px, PC 380 px), cartes un peu moins larges à côté sur grand écran ; colonnes resserrées sur téléphone.
- Tests : règles 136/136, `classements_web.js` (13).

- Nouveau calcul du score en solo et en marathon (option A validée par Victor), même formule PC (`design.score_mot`) et web (`scoreMot`) :
  - points = 100 par lettre × (1 + essais restants / essais permis) × réglages (8 essais ×1, 6 ×1,3, 4 ×1,6 ; difficile ×1,25) × rapidité (−10 % par minute, au plus −50 %) × (−5 % par mot inconnu) ;
  - le score affiché pendant la partie = les points si le mot est trouvé à cet essai.
- Classement du marathon en points (meilleur score d'une partie), repart de zéro : nouvelle stat `marathon.meilleur_points` ; base `classements/marathon/<uid>/score` (**règles à republier**) ; en direct « Encore N pts pour dépasser X » ; fiche joueur et menu Solo en points.
- Tests : règles 134/134, `classements_web.js`, `test_classements_pc.py`, `test_solo_base.py` (mot inconnu −5 %).

- Classement du mot du jour (maquette C validée par Victor) : deux colonnes, « série max » (pastille 🔥, ordre du classement) et « aujourd'hui » (pastille verte « 3 essais », rouge « raté », grise « pas joué ») ; « Ta série en cours » retirée (doublon). PC et web.
  - Le résultat du jour vient des stats (historique) : aussi pour une partie jouée avant la mise à jour. Base : `classements/mdj/<uid>/jour` (date) et `essais` (0 = raté) ; **règles à republier**.
- Mot du jour sans score (demande de Victor) : plus de score pendant la partie ni à la fin, « Mot inconnu » sans −100 points, partage sans « pts ». PC et web.
- Retours de Victor : 🔥 en couleur sur PC (image `fichiers/flamme14.png`, Tk n'affiche les émojis qu'en noir et blanc) ; « Ton record » retiré sous le classement marathon (doublon).
- Barre Temps / Score / Essai / Total (site) : ne passe plus sur 2 lignes, les chiffres rétrécissent si elle est trop large (`ajusterStats`).
- Tests : règles 132/132, `classements_web.js` (11).

- Version obsolète (demande de Victor : il fallait fermer et rouvrir le jeu) : au lancement et au retour sur l'appli, l'accueil affiche une fenêtre centrée « Version obsolète · la X.Y est disponible » avec « Plus tard » et « Mettre à jour » (une fois par lancement, jamais en pleine partie).
  - Site : lit `version.json` (généré par `export_web.py`, jamais en cache, ignoré par le service worker) ; « Mettre à jour » vide le cache hors ligne et recharge ; `index.html` appelle `smout.js`, `style.css` et `donnees.js` avec `?v=X.Y`.
  - PC (Windows seulement) : lit la dernière release GitHub ; « Mettre à jour » télécharge `SMOUT.X.Y.exe` à côté de l'actuel, le lance et se ferme (en cas d'échec : bouton vers la page des versions).
- Classement du mot du jour : la copine de Victor jouait sur PC ; un SMOUT.exe en 9.3 ou avant n'envoie rien au classement (il faut au moins la 9.4).

- Classements (maquettes validées par Victor ; top 5 + ma place, toucher une ligne ouvre la fiche), PC et web :
  - mot du jour (meilleure série, série en cours en note) sur l'accueil : colonne à droite sur grand écran, sous les cartes sinon ;
  - marathon (record de mots) dans le menu Solo (colonne à gauche sur grand écran) et en partie (« Classement : 4e · 15 mots pour dépasser X ») ;
  - seuls les comptes y apparaissent (« Crée un compte pour apparaître dans le classement ») ; le pseudo suit les changements.
- Fiche joueur : pseudo, « Joueur depuis <mois année> », meilleure série, record marathon, « Ajouter en ami » ; depuis les classements et la liste d'amis.
- Mot piégé sur téléphone : les lettres tapées s'affichent DANS les mini-grilles (lettres visibles dès 9 px, police plus grande) et les grilles des autres ont un peu plus de place (demande de Victor).
- Profil « Ton pseudo » (demande de Victor) : une croix pour fermer au lieu d'« Annuler », plus de bouton « Enregistrer » (enregistré à chaque frappe, « Enregistré ✓ »), pas de focus automatique (le clavier du téléphone ne s'ouvre plus tout seul) ; PC et web.
- Règles Firebase (**à republier**) : `classements/mdj/<uid>` (meilleure série : +1 par jour écoulé au plus, 365 au plus à la création) et `classements/marathon/<uid>` (record ≤ 500) ; chacun n'écrit que sa ligne.
- Tests : règles 130/130, `tests/web/classements_web.js` (10), `tests/test_classements_pc.py` (7).

## 9.3
- Retour de Victor (téléphone) : une fois son mot trouvé, on ne voyait pas ce que les autres tapent et valident. Corrigé :
  - frappe en direct dans tous les modes (sauf Rush/Chaîne, chacun son mot, et Coopératif, grille commune), visible seulement une fois SA manche finie (pas de triche) ; PC et web ;
  - téléphone : manche finie → ma grille et le clavier s'effacent, les grilles des autres s'agrandissent sur toute la place (comme la vue spectateur) ; les mini-cases réaffichent leurs lettres quand elles grandissent ;
  - le spectateur web voit aussi lettres et frappe dès le début (comme sur PC).
- Les classements (mot du jour, marathon) et la fiche joueur passent en 9.4.
- Tests : `tests/web/frappe_web.js` (6).

## 9.2
- Liste d'amis (comptes e-mail seulement ; maquettes validées par Victor), PC et web : écran Amis (icône sur l'accueil et dans le Multijoueur, pastille = demandes reçues) avec mon code ami (6 caractères, « Donne-le pour ajouter des amis. »), ajout par code, demandes reçues (Accepter / Refuser), liste avec statut (En ligne, Dans un salon · code, Hors ligne · il y a…), Inviter / Rejoindre / Retirer.
- Bandeau en haut de tous les écrans (pas en pleine partie) : « X t'invite dans son salon · Rejoindre / Ignorer » ou « X veut être ton ami · Voir / Ignorer ».
- « Inviter des amis » dans le salon (bouton à côté du code) et en partie (icône) : panneau latéral sans voile, amis en ligne d'abord, « Invité ✓ ».
- Rejoindre par invitation : sans taper le code ; le mot de passe du salon reste demandé ; partie en cours → spectateur directement (choix de Victor : toujours direct).
- Règles Firebase (**à republier**) : `codes_amis`, `profils`, `amis`, `amis_demandes`, `invitations`, et entrée en spectateur pendant une partie pour un invité. Signe de vie du profil toutes les 30 s (comptes seulement ; aucune connexion ouverte sans compte).
- Tests : règles 120/120, `tests/web/amis_web.js` (17), `tests/test_amis_pc.py` (15).

## 9.1
- Fenêtres du jeu à la place des fenêtres natives (confirm/alert du navigateur, messagebox du PC) : confirmations et messages dans la DA (titre, texte, boutons Annuler / action), PC et web (`dialogue`, `confirmer`, `informer`).
- Spectateurs (maquettes validées par Victor) : salon plein → on entre comme spectateur ; « x spectateurs » sous la liste des joueurs ; « Passer spectateur » sur sa propre ligne (pas pour l'hôte) ; « Prendre la place » sur une place libre. Le spectateur le reste pendant la partie : pas de grille ni de clavier, les grilles de tous les joueurs réparties sur toute la place, il voit tout (en Mot piégé aussi les mots à trouver), n'écrit rien dans la partie (bloqué dans le client et par les règles), peut quitter à tout moment.
- Rejoindre une partie EN COURS : demande à l'hôte (fenêtre « En attente de l'hôte », « Quitter » avec confirmation retire la demande). L'hôte a une cloche en haut à droite (pastille = nombre de demandes actives) qui ouvre un panneau latéral sans voile (le jeu reste utilisable) : Accepter (→ spectateur jusqu'au retour au salon) ou Refuser (le demandeur est prévenu). Partie terminée pendant l'attente : on entre directement dans le salon.
- Code du salon affiché pour tous en partie, dans la ligne Manche / Temps / Score.
- Règles Firebase (**à republier**) : `lobbies/<code>/spectateurs/<uid>` (lecture du salon par les spectateurs, entrée libre seulement avant la partie, avec la preuve du mot de passe), `demandes/<code>/<uid>` (écrite par le demandeur, lue et effacée par l'hôte), mots du Mot piégé lisibles par les spectateurs. `VERSION_JEU` 9.1 (un client plus ancien entrait en joueur dans une partie en cours).
- Tests : règles 100/100, `tests/web/spectateur_web.js` (17), `tests/test_spectateur_pc.py` (19), robots et tests adaptés aux fenêtres du jeu.

## 9.0
- Hôte : bouton « Lobby » (flèche de retour + « Lobby », contour jaune) en haut à gauche, à côté de la flèche, en pleine partie (aussi pendant le choix du Mot piégé) et sur l'écran de fin de partie, PC et web, téléphone compris. Il ramène tous les joueurs au salon après confirmation (« Ramener tous les joueurs au salon ? »). Remplace le petit lien « Retour au salon » de droite. Design validé par Victor.
- Moins de petits textes qui font doublon (PC et web) : plus de « mode · n lettres » ni de « Mot piégé · choisis le mot de … » en haut du jeu (il reste « Mot n° … » en Rush et « Mot choisi par … » pendant la devinette du Mot piégé), plus de ligne d'explication sous « Choisis le mot que … devra deviner », plus de « n sur m mots choisis », plus de « Salon de … · mode · Partie terminée » sur l'écran de fin.
- Écran de fin : « (hôte) » en gris à côté du nom de l'hôte, sur le podium et dans le tableau (la couronne reste réservée au gagnant), mis à jour si l'hôte change.
- Écran de fin, tous les modes : récapitulatif par manche, un bandeau par manche (option D validée par Victor), dans une zone qui défile quand la liste est longue (PC et téléphone). Classique, Blast, Précision, Mystère, Élimination, Coopératif : le mot de la manche en cases dans le bandeau, puis chaque joueur « trouvé en N » ou « pas trouvé » (l'hôte écrit `recap_manches/r<n>` = {mot, res} en passant à la suite, calculé depuis `match_data` ; pas de règle Firebase à republier, l'hôte peut écrire dans son salon). Rush et Chaîne : les mots de chaque manche en cases. Mot piégé : « Alice → Bob · mot en cases · trouvé en 3 / pas trouvé », « au hasard » signalé.
- Pseudo : lettres (accents compris), chiffres et espaces uniquement, 15 caractères au plus, espaces multiples fusionnés et retirés au début et à la fin (`nettoyer_pseudo` / `nettoyerPseudo`, mêmes résultats PC et web) ; les pseudos déjà enregistrés sont nettoyés à la lecture.
- Tests : « Lobby » visible en haut à gauche pour l'hôte seulement (web et PC, `hote_web.js`, `test_hote_pc.py`).

## 8.19
- Comptes : la création affichait « Les comptes ne sont pas encore activés sur le serveur » même avec E-mail/Mot de passe activé. Cause : la protection contre l'énumération des e-mails (activée par défaut sur le projet Firebase) refuse `accounts:update` (« Please verify the new email before changing email »). Le rattachement du joueur anonyme passe désormais par `accounts:signUp` avec son `idToken` (même identifiant), PC et web — vérifié sur le vrai projet avec un compte de test aussitôt supprimé.
- Tests : le faux serveur refuse maintenant `update` comme le vrai projet (les tests de comptes reçoivent l'opération appelée), ce qui aurait détecté le bug.

## 8.18
- Téléphone, page de jeu multijoueur (option « A » validée par Victor) : les mini-grilles des adversaires passent en haut (jusqu'à 4 par ligne, cadre avec nom et score), ma grille au milieu prend la hauteur qui reste, le clavier est en bas : tout tient sur un écran, sans défiler, de 2 à 8 joueurs (390×844 et 360×780 ; seul un très petit écran 360×640 à 8 joueurs défile encore un peu). Recalcul automatique quand la hauteur change (textes, Mot piégé). Ordinateur inchangé.
- Téléphone : plus de bascule « clavier du téléphone », seul le clavier du jeu sert à écrire.
- Téléphone : plus de zoom de la page au double appui ni au pincement (viewport non zoomable, `touch-action: manipulation`, gestes iOS bloqués ; un 2e appui rapide reste un clic).
- PC et web, solo et multijoueur : le réglage « taille » (− 100 % +) agrandit ou réduit aussi le clavier (`Clavier.set_zoom` / `--kz`).
- Tests : `tests/web/jeu_tel.js` (2, 4 et 8 joueurs sur téléphone : adversaires en haut, clavier visible, pas de défilement, zoom), `clavier_tel.js` revu (pas de clavier natif, pas de zoom au double appui, clavier qui suit la taille), clavier zoomé côté PC (solo et partie).

## 8.17
- Comptes SMOUT (e-mail + mot de passe, Firebase Authentication), PC et web : « Créer un compte » rattache le joueur de l'appareil à l'adresse (même identifiant, rien n'est perdu) ; « Se connecter » sur un autre PC ou téléphone reprend le même joueur et son avancement (pseudo, thème, thèmes perso, réglages, statistiques, série et mot du jour, partie multijoueur en cours). L'avancement est copié sous `/v7/comptes/<uid>` (lisible par son seul propriétaire), envoyé 2 s après chaque changement et relu au démarrage. On reste connecté tant qu'on ne se déconnecte pas. Mot de passe oublié par e-mail. Accès : fenêtre « Ton pseudo » → section Compte.
- Retour en pleine partie : fenêtre « Quitter la partie ? » avec Continuer / Quitter la partie / Mettre en pause. En pause, on garde sa place dans le salon et « Reprendre » (accueil du multijoueur) ramène dans la partie, aussi depuis un autre appareil connecté au même compte ; délai de reprise porté de 15 min à 2 h.
- Hôte : bouton « Donner l'hôte » sur la ligne de chaque joueur du salon ; si l'hôte part, le relais va au premier arrivé dans le salon (heure d'arrivée `arrivee`), et non plus au plus petit identifiant.
- Règles Firebase : `comptes/<uid>` ; **à republier**, et **activer E-mail/Mot de passe** dans Authentication (sans quoi la création de compte affiche « Les comptes ne sont pas encore activés sur le serveur »). `VERSION_JEU` inchangée (8.10).
- Tests : règles 83/83, comptes web 16/16 puis PC 20/20 (compte créé sur le web repris sur PC), salon et partie (donner l'hôte, pause, reprise, relais au premier arrivé) web 15/15 et PC 15/15.

## 8.16
- Mot piégé : on voit en permanence chez les autres joueurs (sauf soi) le mot qu'ils doivent trouver (« Mot à trouver : … » sous leur grille, dès que la devinette est lancée), ce qu'ils tapent en direct (ligne en cours, publiée au plus 5 fois par seconde) et les lettres de leurs essais. Avec « Cible cachée », la cible du mot qu'on a choisi n'est révélée qu'à partir de la devinette.
- Thème de chaque joueur : sa grille garde SES couleurs (bien placé, mal placé, absent, fond) chez tous les autres, dans tous les modes multijoueur, PC et web (`players/<uid>/theme`, publié au début de chaque manche).
- Mot du jour : la journée ne compte comme jouée que lorsque le mot a été vu (victoire, défaite ou abandon). En quittant avant, on reprend avec ses essais déjà faits, ses pénalités et son temps (`mdj_en_cours` dans la config), PC et web.
- Règles Firebase : `players/<uid>/frappe` (≤ 12 caractères) et `players/<uid>/theme` (couleurs ≤ 9 caractères) validés ; **à republier** (non bloquant : sans elles, tout fonctionne mais sans validation). `VERSION_JEU` inchangée (8.10).
- Tests : règles 77/77, mot du jour repris (PC et web), robots du Mot piégé : frappe publiée, mots et thèmes des autres affichés (PC et web, croisés).

## 8.15
- 8 joueurs par salon au lieu de 4 (PC et web) : liste des salons « n/8 », 8 places dans le salon (plus compactes), 2 couleurs d'avatar de plus. **Règles Firebase à republier** (`index/nb` ≤ 8) ; `VERSION_JEU` inchangée (8.10). Aucun mode n'est limité à 4 ; Blast garde ses points pour les 4 premiers (4, 3, 2, 1).
- Page de jeu : les grilles des adversaires s'adaptent au nombre de joueurs (calcul commun `disposition_adv` / `dispositionAdv`) : 1 à 3 adversaires = nom et score à droite de la grille ; au-delà, plusieurs colonnes et nom + score au-dessus de la grille si les cases sont plus grandes ainsi (jusqu'à 3 colonnes, 7 adversaires).
- Mot piégé : option du salon « Cible cachée » (on choisit son mot sans savoir pour qui ; « Ton mot » n'apparaît plus sous la grille de la cible). Les paires sont maintenant tirées au hasard à chaque manche (en évitant celles de la manche précédente quand c'est possible). La cible reste lisible dans la base (règles Firebase) : option de confort, pas de secret cryptographique.
- Menu Solo : bouton Paramètres clair (blanc cassé, texte sombre), bien distinct du fond.
- Tests : règles 72/72 (nb ≤ 8), 2 scénarios croisés « cible cachée » (x1, x2), `tests/web/captures_jeu.js` et `tests/capture_jeu_pc.py` (page de jeu de chaque mode, de 1 à 8 joueurs).

## 8.14
- Salon multijoueur repensé : sections « Mode de jeu » et « Réglages de la partie » ; cartes de mode avec leur description (masquée sur téléphone) ; les curseurs sont remplacés par des tuiles « − valeur + » (manches, temps, essais sur une ligne, lettres min/max dessous). Le temps avance par paliers (15 s … 1 min … 10 min). Les invités voient les mêmes tuiles, sans boutons, sous le bandeau du mode. Bouton « En attente d'un 2e joueur… » neutre tant qu'on est seul.
- Paramètres solo : page centrée, mêmes tuiles que le salon ; nouveau réglage « Taille de la grille » (60 à 160 %).
- Solo : boutons − / + de taille de grille dans la barre du haut (comme en multijoueur ; réglage commun au solo et au multi).
- Web, téléphone : panneau « Joueurs » du salon en pleine largeur.
- `VERSION_JEU` inchangée (8.10, protocole identique) : pas de règles Firebase à republier, compatible avec les joueurs en 8.10.

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
