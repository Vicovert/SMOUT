#!/bin/bash
# Banc de test SMOUT : règles Firebase, solo PC, solo web (PC et téléphone, hors ligne) et parties croisées PC ↔ web.
# Tout tourne en local : faux serveur Firebase qui applique les vraies règles (tests/fb_regles.py), site web local, Chrome sans écran, Tk sous Xvfb.
# Variables : PY (python avec tkinter + requests), CHROME (chemin de Chrome). Code de sortie 1 si un test échoue.
ICI=$(cd "$(dirname "$0")" && pwd); DEPOT=$(dirname "$ICI"); export PY=${PY:-python3}
SITE=/tmp/smout_site; rm -rf $SITE; $PY "$DEPOT/outils/export_web.py" $SITE >/dev/null || exit 1
(cd $SITE && exec $PY -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1) & P1=$!
$PY "$ICI/fb_regles.py" 9000 >/tmp/fb_regles.log 2>&1 & P2=$!
trap "kill $P1 $P2 2>/dev/null" EXIT
sleep 1.5; [ -d "$ICI/web/node_modules" ] || (cd "$ICI/web" && npm install --silent >/dev/null 2>&1)
ECHECS=0
etape() { echo; echo "=== $1"; }
verifier() { if grep -qE "ÉCHEC|EXCEPTION|Traceback|: False|ok=False|sans rapport" "$1"; then echo "  >>> ÉCHEC"; ECHECS=$((ECHECS+1)); else echo "  >>> OK"; fi; }
xpy() { HOME=$(mktemp -d) xvfb-run -a -s "-screen 0 1200x860x24" $PY "$@"; }
etape "Règles Firebase v7"; $PY "$ICI/test_regles.py" 2>&1 | tee /tmp/t1.txt | tail -n 1; verifier /tmp/t1.txt
etape "Solo PC"; (xpy "$ICI/test_solo_base.py" "$DEPOT"; xpy "$ICI/test_solo_72.py" "$DEPOT") 2>&1 | tee /tmp/t2.txt | grep -E "ÉCHEC|False|conformes|Traceback"; verifier /tmp/t2.txt
for t in solo_web solo72_web hors_ligne; do etape "Web : $t"; (cd "$ICI/web" && timeout 400 node $t.js) 2>&1 | tee /tmp/t_$t.txt | grep -E "ÉCHEC|conformes|EXCEPTION"; verifier /tmp/t_$t.txt; done
S="$ICI/scenario.sh"
etape "Croisé : Précision, hôte PC protégé, joueur web (mauvais puis bon mot de passe)"
DUREE=220 $S c1 'pc:{"nom":"ALICE","role":"host","mode":"PRECISION","manches":2,"mdp":"chat","nb":2}' 'web:{"nom":"BOB","role":"join","hote":"ALICE","mode":"PRECISION","manches":2,"mdp":"chat","mdp_faux":"chien"}' 2>&1 | tee /tmp/t_c1.txt; verifier /tmp/t_c1.txt
etape "Croisé : Blast 3 joueurs, hôte web"
DUREE=260 PAUSE=6 $S c2 'web:{"nom":"BOB","role":"host","mode":"BLAST","manches":2,"nb":3}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"BLAST","manches":2}' 'web:{"nom":"DAVID","role":"join","hote":"BOB","mode":"BLAST","manches":2,"jeu":"perd"}' 2>&1 | tee /tmp/t_c2.txt; verifier /tmp/t_c2.txt
etape "Croisé : Rejouer dans ce salon, hôte web"
DUREE=300 $S c3 'web:{"nom":"BOB","role":"host","mode":"CLASSIQUE","manches":1,"nb":2,"parties":2}' 'pc:{"nom":"ALICE","role":"join","hote":"BOB","mode":"CLASSIQUE","manches":1,"parties":2}' 2>&1 | tee /tmp/t_c3.txt; verifier /tmp/t_c3.txt
echo; if [ $ECHECS -eq 0 ]; then echo "TOUS LES TESTS SONT PASSÉS"; else echo "$ECHECS ÉTAPE(S) EN ÉCHEC"; fi
exit $([ $ECHECS -eq 0 ] && echo 0 || echo 1)
