#!/bin/bash
# Banc de test SMOUT : règles Firebase, solo PC, solo web (PC et téléphone, hors ligne) et parties croisées PC ↔ web.
# Tout tourne en local : faux serveur Firebase qui applique les vraies règles (tests/fb_regles.py), site web local, Chrome sans écran, Tk sous Xvfb.
# Variables : PY (python avec tkinter + requests), CHROME (chemin de Chrome). Code de sortie 1 si un test échoue.
ICI=$(cd "$(dirname "$0")" && pwd); DEPOT=$(dirname "$ICI"); export PY=${PY:-python3}
SITE=/tmp/smout_site; rm -rf $SITE; $PY "$DEPOT/outils/export_web.py" $SITE >/dev/null || exit 1
pkill -f "http.server 8000" 2>/dev/null; sleep 0.3; (cd $SITE && exec $PY -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1) & P1=$!
pkill -f "fb_regles.py 9000" 2>/dev/null; $PY "$ICI/fb_regles.py" 9000 >/tmp/fb_regles.log 2>&1 & P2=$!
trap "kill $P1 $P2 2>/dev/null" EXIT
sleep 1.5; [ -d "$ICI/web/node_modules" ] || (cd "$ICI/web" && npm install --silent >/dev/null 2>&1)
ECHECS=0
etape() { echo; echo "=== $1"; }
verifier() { if grep -qE "ÉCHEC|EXCEPTION|Traceback|: False|ok=False|sans rapport" "$1"; then echo "  >>> ÉCHEC"; ECHECS=$((ECHECS+1)); else echo "  >>> OK"; fi; }
xpy() { HOME=$(mktemp -d) xvfb-run -a -s "-screen 0 1200x860x24" $PY "$@"; }
etape "Règles Firebase v7"; $PY "$ICI/test_regles.py" 2>&1 | tee /tmp/t1.txt | tail -n 1; verifier /tmp/t1.txt
etape "Solo PC"; (xpy "$ICI/test_solo_base.py" "$DEPOT"; xpy "$ICI/test_solo_72.py" "$DEPOT") 2>&1 | tee /tmp/t2.txt | grep -E "ÉCHEC|False|conformes|Traceback"; verifier /tmp/t2.txt
for t in solo_web solo72_web hors_ligne captures_multi clavier_tel; do etape "Web : $t"; (cd "$ICI/web" && timeout 400 node $t.js) 2>&1 | tee /tmp/t_$t.txt | grep -E "ÉCHEC|conformes|EXCEPTION"; verifier /tmp/t_$t.txt; done
S="$ICI/scenario.sh"
etape "Croisé : Précision, hôte PC protégé, joueur web (mauvais puis bon mot de passe)"
DUREE=220 $S c1 'pc:{"nom":"ALICE","role":"host","mode":"PRECISION","manches":2,"mdp":"chat","nb":2}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"PRECISION","manches":2,"mdp":"chat","mdp_faux":"chien"}' 2>&1 | tee /tmp/t_c1.txt; $PY "$ICI/verif_scores.py" c1 | tee -a /tmp/t_c1.txt; verifier /tmp/t_c1.txt
etape "Croisé : Blast 3 joueurs, hôte web"
DUREE=260 PAUSE=6 $S c2 'web:{"nom":"BOB","role":"host","mode":"BLAST","manches":2,"nb":3}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"BLAST","manches":2}' 'web:{"nom":"DAVID","role":"join","hote":"BOB","mode":"BLAST","manches":2,"jeu":"perd"}' 2>&1 | tee /tmp/t_c2.txt; $PY "$ICI/verif_scores.py" c2 | tee -a /tmp/t_c2.txt; verifier /tmp/t_c2.txt
etape "Croisé : Rejouer dans ce salon, hôte web"
DUREE=300 $S c3 'web:{"nom":"BOB","role":"host","mode":"CLASSIQUE","manches":1,"nb":2,"parties":2}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"CLASSIQUE","manches":1,"parties":2}' 2>&1 | tee /tmp/t_c3.txt; $PY "$ICI/verif_scores.py" c3 | tee -a /tmp/t_c3.txt; verifier /tmp/t_c3.txt
etape "Croisé : Élimination à 3, hôte PC (le joueur web perd et devient spectateur)"
DUREE=320 PAUSE=5 $S c4 'pc:{"nom":"ALICE","role":"host","mode":"ELIMINATION","manches":3,"nb":3}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"ELIMINATION","manches":3,"jeu":"perd"}' 'pc:{"nom":"CHLOE","role":"join","hote":"ALICE","mode":"ELIMINATION","manches":3}' 2>&1 | tee /tmp/t_c4.txt; $PY "$ICI/verif_scores.py" c4 | tee -a /tmp/t_c4.txt; verifier /tmp/t_c4.txt
etape "Croisé : Coopératif, hôte web"
DUREE=220 $S c5 'web:{"nom":"BOB","role":"host","mode":"COOP","manches":2,"nb":2}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"COOP","manches":2,"jeu":"perd"}' 2>&1 | tee /tmp/t_c5.txt; $PY "$ICI/verif_scores.py" c5 | tee -a /tmp/t_c5.txt; verifier /tmp/t_c5.txt
etape "Croisé : Chaîne 30 s, hôte PC"
DUREE=220 $S c6 'pc:{"nom":"ALICE","role":"host","mode":"CHAINE","manches":1,"nb":2,"jeu":"rush","timer":30}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"CHAINE","manches":1,"jeu":"rush"}' 2>&1 | tee /tmp/t_c6.txt; $PY "$ICI/verif_scores.py" c6 | tee -a /tmp/t_c6.txt; verifier /tmp/t_c6.txt
etape "Croisé : le joueur web plante en manche 2 et reprend la partie"
DUREE=440 PAUSE=4 $S c8 'pc:{"nom":"ALICE","role":"host","mode":"CLASSIQUE","manches":3,"nb":2}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"CLASSIQUE","manches":3,"planter_manche":2}' 'web:{"nom":"BOB","role":"reprise","mode":"CLASSIQUE","manches":3,"config_depuis":"/tmp/sc/c8/r2.json","attente_reprise":3}' 2>&1 | tee /tmp/t_c8.txt; $PY "$ICI/verif_scores.py" c8 | tee -a /tmp/t_c8.txt; verifier /tmp/t_c8.txt
etape "Croisé : Mystère 3 joueurs, hôte web (le joueur web perd)"
DUREE=300 PAUSE=6 $S c9 'web:{"nom":"BOB","role":"host","mode":"MYSTERE","manches":2,"nb":3}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"MYSTERE","manches":2}' 'web:{"nom":"DAVID","role":"join","hote":"BOB","mode":"MYSTERE","manches":2,"jeu":"perd"}' 2>&1 | tee /tmp/t_c9.txt; $PY "$ICI/verif_scores.py" c9 | tee -a /tmp/t_c9.txt; verifier /tmp/t_c9.txt
etape "Croisé : Mystère, hôte PC (le joueur PC perd)"
DUREE=260 $S c10 'pc:{"nom":"ALICE","role":"host","mode":"MYSTERE","manches":2,"nb":2,"jeu":"perd"}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"MYSTERE","manches":2}' 2>&1 | tee /tmp/t_c10.txt; $PY "$ICI/verif_scores.py" c10 | tee -a /tmp/t_c10.txt; verifier /tmp/t_c10.txt
etape "Croisé : Rush 30 s, hôte PC"
DUREE=220 $S c11 'pc:{"nom":"ALICE","role":"host","mode":"RUSH","manches":1,"nb":2,"jeu":"rush","timer":30}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"RUSH","manches":1,"jeu":"rush"}' 2>&1 | tee /tmp/t_c11.txt; $PY "$ICI/verif_scores.py" c11 | tee -a /tmp/t_c11.txt; verifier /tmp/t_c11.txt
etape "Croisé : Rush 30 s, hôte web, 2 manches"
DUREE=300 $S c12 'web:{"nom":"BOB","role":"host","mode":"RUSH","manches":2,"nb":2,"jeu":"rush","timer":30}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"RUSH","manches":2,"jeu":"rush"}' 2>&1 | tee /tmp/t_c12.txt; $PY "$ICI/verif_scores.py" c12 | tee -a /tmp/t_c12.txt; verifier /tmp/t_c12.txt
etape "Croisé : Précision, hôte web (le joueur PC perd)"
DUREE=240 $S c13 'web:{"nom":"BOB","role":"host","mode":"PRECISION","manches":2,"nb":2}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"PRECISION","manches":2,"jeu":"perd"}' 2>&1 | tee /tmp/t_c13.txt; $PY "$ICI/verif_scores.py" c13 | tee -a /tmp/t_c13.txt; verifier /tmp/t_c13.txt
etape "Mot piégé PC : choix valide et invalide, devinette réussie et ratée"
DUREE=300 $S p1 'pc:{"nom":"ALICE","role":"host","mode":"PIEGE","manches":2,"nb":2}' 'pc:{"nom":"BOB","role":"join","hote":"ALICE","mode":"PIEGE","manches":2,"choix":"invalide","jeu":"perd"}' 2>&1 | tee /tmp/t_p1.txt; $PY "$ICI/verif_scores.py" p1 | tee -a /tmp/t_p1.txt; verifier /tmp/t_p1.txt
etape "Mot piégé PC : 3 joueurs, mot au hasard après 30 s, un joueur part (évaluation de secours)"
DUREE=330 PAUSE=5 $S p2 'pc:{"nom":"ALICE","role":"host","mode":"PIEGE","manches":2,"nb":3}' 'pc:{"nom":"BOB","role":"join","hote":"ALICE","mode":"PIEGE","manches":2,"choix":"rien"}' 'pc:{"nom":"CHLOE","role":"join","hote":"ALICE","mode":"PIEGE","manches":2,"planter_apres_choix":1}' 2>&1 | tee /tmp/t_p2.txt; $PY "$ICI/verif_scores.py" p2 | tee -a /tmp/t_p2.txt; verifier /tmp/t_p2.txt
etape "Croisé : Mot piégé, hôte PC, joueur web (choix invalide puis valide, devinette ratée)"
DUREE=300 $S q1 'pc:{"nom":"ALICE","role":"host","mode":"PIEGE","manches":2,"nb":2}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"PIEGE","manches":2,"choix":"invalide","jeu":"perd"}' 2>&1 | tee /tmp/t_q1.txt; $PY "$ICI/verif_scores.py" q1 | tee -a /tmp/t_q1.txt; verifier /tmp/t_q1.txt
etape "Croisé : Mot piégé, hôte web, joueur PC (mot au hasard après 30 s, devinette ratée côté PC)"
DUREE=330 $S q2 'web:{"nom":"BOB","role":"host","mode":"PIEGE","manches":2,"nb":2,"choix":"rien"}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"PIEGE","manches":2,"jeu":"perd"}' 2>&1 | tee /tmp/t_q2.txt; $PY "$ICI/verif_scores.py" q2 | tee -a /tmp/t_q2.txt; verifier /tmp/t_q2.txt
etape "Croisé : Mot piégé à 3, hôte PC, un joueur web part après son choix (évaluation de secours), mot au hasard"
DUREE=330 PAUSE=5 $S q3 'pc:{"nom":"ALICE","role":"host","mode":"PIEGE","manches":2,"nb":3}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"PIEGE","manches":2,"choix":"rien"}' 'web:{"nom":"CHLOE","role":"join","hote":"ALICE","mode":"PIEGE","manches":2,"planter_apres_choix":1}' 2>&1 | tee /tmp/t_q3.txt; $PY "$ICI/verif_scores.py" q3 | tee -a /tmp/t_q3.txt; verifier /tmp/t_q3.txt
etape "Mot piégé PC : le joueur plante après son choix et reprend la partie"
DUREE=400 $S p3 'pc:{"nom":"ALICE","role":"host","mode":"PIEGE","manches":2,"nb":2}' 'pc:{"nom":"BOB","role":"join","hote":"ALICE","mode":"PIEGE","manches":2,"jeu":"perd","planter_apres_choix":2}' 'pc:{"nom":"BOB","role":"reprise","mode":"PIEGE","manches":2,"jeu":"perd","home":"/tmp/hp32","apres_fichier":"/tmp/sc/p3/r2.json"}' 2>&1 | tee /tmp/t_p3.txt; $PY "$ICI/verif_scores.py" p3 | tee -a /tmp/t_p3.txt; verifier /tmp/t_p3.txt
echo; if [ $ECHECS -eq 0 ]; then echo "TOUS LES TESTS SONT PASSÉS"; else echo "$ECHECS ÉTAPE(S) EN ÉCHEC"; fi
exit $([ $ECHECS -eq 0 ] && echo 0 || echo 1)
