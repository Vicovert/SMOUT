#!/bin/bash
# scenario.sh <nom> '<json pc ou web>' ... : chaque argument = "pc|web:json"
ICI=$(cd "$(dirname "$0")" && pwd); DEPOT=$(dirname "$ICI")
nom=$1; shift; mkdir -p /tmp/sc/$nom; rm -f /tmp/sc/$nom/*; : > /tmp/fb_refus.log
curl -s -X POST http://127.0.0.1:9000/__reset >/dev/null
i=0; pids=()
for a in "$@"; do
  sup=${a%%:*}; js=${a#*:}; i=$((i+1)); out=/tmp/sc/$nom/r$i.json
  js=$(python3 -c "import json,sys;d=json.loads(sys.argv[1]);d['sortie']=sys.argv[2];print(json.dumps(d))" "$js" "$out")
  if [ $sup = pc ]; then
    (HOME=/tmp/h$nom$i; rm -rf $HOME; mkdir -p $HOME; timeout ${DUREE:-400} xvfb-run -a -s "-screen 0 ${ECRAN:-1200x860}x24" ${PY:-python3} "$ICI/robot_pc.py" "$DEPOT" "$js" > /tmp/sc/$nom/log$i.txt 2>&1) &
  else
    (cd "$ICI/web" && timeout ${DUREE:-400} node robot_web.js "$js" > /tmp/sc/$nom/log$i.txt 2>&1) &
  fi
  pids+=($!); sleep ${PAUSE:-4}
done
wait "${pids[@]}"
python3 - "$nom" <<'PY'
import json,glob,sys,os
nom=sys.argv[1]; d=f"/tmp/sc/{nom}"
for f in sorted(glob.glob(d+"/r*.json")):
    r=json.load(open(f)); print(f"  {r['support']:3} {r['nom']:6} ok={r.get('ok')} mots={r.get('mots')} res={r.get('resultats')} {('rush='+str(r['rush_trouves'])) if r.get('rush_trouves') else ''} {('podium='+r['texte_podium']) if r.get('texte_podium') else ''}")
    for e in r.get("erreurs",[]): print("     ERREUR:", e.strip()[-400:])
n=len(glob.glob(d+"/log*.txt")); m=len(glob.glob(d+"/r*.json"))
if m<n: print(f"  !! {n-m} robot(s) sans rapport")
ref=open("/tmp/fb_refus.log").read().strip()
print("  refus règles:", ref.count("\n")+1 if ref else 0)
if ref: print("   ", "\n    ".join(ref.splitlines()[:8]))
PY
