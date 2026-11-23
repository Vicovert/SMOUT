"""Captures PC de la page de jeu pour chaque mode avec 2 à 8 joueurs (Tk sous Xvfb, faux serveur).
Usage : capture_jeu_pc.py <repo> <dossier> [modes] [nombres de joueurs]   (ex. CLASSIQUE,PIEGE 2,5,8)"""
import sys, os, time, subprocess, tempfile, json, threading, urllib.request
repo, out = sys.argv[1], sys.argv[2]
MODES = (sys.argv[3] if len(sys.argv) > 3 else "CLASSIQUE,BLAST,PRECISION,MYSTERE,RUSH,ELIMINATION,CHAINE,COOP,PIEGE").split(",")
NS = [int(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "2,3,4,5,6,7,8").split(",")]
os.environ["HOME"] = tempfile.mkdtemp(); os.chdir(repo); sys.path.insert(0, repo)
import requests
class Sess(requests.Session):
    def request(self, method, url, *a, **k):
        if "firebasedatabase.app" in url: url = "http://127.0.0.1:9000/" + url.split(".app/", 1)[1]
        elif "securetoken" in url: url = "http://127.0.0.1:9000/token"
        elif "identitytoolkit" in url: url = "http://127.0.0.1:9000/signup"
        return super().request(method, url, *a, **k)
requests.Session = Sess
import tkinter as tk, design; design.charger_polices()
import main as Mn, page_multi as pm
NOMS = ["BOB", "CHLOE", "DAVID", "EMMA", "FELIX", "GABY", "HUGO"]
B = "http://127.0.0.1:9000"
def req(m, chemin, uid, corps=None):
    r = urllib.request.Request(f"{B}/{chemin}.json?auth=tok-{uid}", method=m, data=json.dumps(corps).encode() if corps is not None else None)
    return urllib.request.urlopen(r).read()
def faux(code, n):
    ids = []
    for i in range(n):
        uid = json.loads(urllib.request.urlopen(urllib.request.Request(B + "/signup", method="POST", data=b"{}")).read())["localId"]
        ids.append((uid, NOMS[i])); req("PATCH", f"v7/lobbies/{code}/players/{uid}", uid, {"name": NOMS[i], "score": 0, "last_seen": {".sv": "timestamp"}})
    vivant = [True]
    def battre():
        while vivant[0]:
            for uid, nom in ids:
                try: req("PATCH", f"v7/lobbies/{code}/players/{uid}", uid, {"last_seen": {".sv": "timestamp"}})
                except Exception: pass
            time.sleep(4)
    threading.Thread(target=battre, daemon=True).start()
    return lambda: vivant.__setitem__(0, False)
app = Mn.MenuPrincipal()
def pump(t):
    end = time.time() + t
    while time.time() < end: app.update(); time.sleep(0.01)
def cap(nom): pump(1.0); subprocess.run(["import", "-window", "root", os.path.join(out, f"{nom}.png")])
pump(1)
for mode in MODES:
    for n in NS:
        app.ouvrir_multi(); pump(1)
        pump(0.5); m = next(w for w in app.container.winfo_children() if hasattr(w, "frames"))
        m.frames["PageAccueil"].champ_pseudo.set("ALICE"); m.assurer_connexion()
        m.settings_config.update({"password": "", "visible": True}); m.is_host, m.lobby_code = True, ""; m.show_frame("PageLobby"); pump(2)
        lob = m.frames["PageLobby"]; code = m.lobby_code
        arret = faux(code, n - 1)
        for _ in range(100):
            pump(0.2)
            if m.nb_joueurs >= n: break
        if mode != "CLASSIQUE": lob.set_mode(mode)
        pump(1.5); lob.lancer(); pump(3)
        cap(f"pc_{mode}_{n}")
        arret(); m.quitter_lobby_logic(True); pump(1)
app.destroy()
