"""Salon et partie côté PC (Tk sous Xvfb, faux serveur) : « Donner l'hôte », pause en pleine partie puis « Reprendre »,
départ définitif de l'hôte avec relais au PREMIER ARRIVÉ (CHLOE a l'identifiant le plus petit mais arrive après BOB).
Usage : test_hote_pc.py <repo>"""
import sys, os, time, json, tempfile, threading, urllib.request
repo = sys.argv[1]; os.environ["HOME"] = tempfile.mkdtemp(); os.chdir(repo); sys.path.insert(0, repo)
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
res = []
def ok(nom, c, info=""): res.append(bool(c)); print(("OK    " if c else "ÉCHEC ") + nom + (f"  — {info}" if info and not c else ""), flush=True)
B = "http://127.0.0.1:9000"
def req(m, chemin, uid, corps=None):
    r = urllib.request.Request(f"{B}/{chemin}.json?auth=tok-{uid}", method=m, data=json.dumps(corps).encode() if corps is not None else None)
    return urllib.request.urlopen(r).read()
def db(): return json.loads(urllib.request.urlopen(B + "/__admin.json").read() or b"null") or {}
def inscrire(): return json.loads(urllib.request.urlopen(urllib.request.Request(B + "/signup", method="POST", data=b"{}")).read())["localId"]
pm.tkm.askyesno = lambda *a, **k: True

# successeur : le premier arrivé, pas le plus petit identifiant
ok("successeur : premier arrivé", pm.successeur({"u1": {"arrivee": 30}, "u2": {"arrivee": 10}, "u3": {"arrivee": 20}}, exclu="u2") == "u3")
ok("successeur : parmi les joueurs actifs seulement", pm.successeur({"u1": {"arrivee": 30}, "u2": {"arrivee": 10}}, actifs=["u1"]) == "u1")

app = Mn.MenuPrincipal()
def pump(t):
    end = time.time() + t
    while time.time() < end: app.update(); time.sleep(0.01)
def attendre(c, t=20):
    end = time.time() + t
    while time.time() < end:
        pump(0.1)
        try:
            if c(): return True
        except Exception: pass
    return False
pump(0.5); app.ouvrir_multi(); pump(1)
m = next(w for w in app.container.winfo_children() if hasattr(w, "frames"))
m.frames["PageAccueil"].champ_pseudo.set("ALICE"); m.assurer_connexion()
m.settings_config.update({"password": "", "visible": True}); m.is_host, m.lobby_code = True, ""; m.show_frame("PageLobby"); pump(2)
lob, code, moi = m.frames["PageLobby"], m.lobby_code, m.player_id
uc = inscrire(); ub = inscrire()  # CHLOE a un identifiant plus petit que BOB…
vivants = {"ok": True}
def battre(uid):
    while vivants["ok"]:
        try: req("PATCH", f"v7/lobbies/{code}/players/{uid}", uid, {"last_seen": {".sv": "timestamp"}})
        except Exception: pass
        time.sleep(3)
for uid, nom in ((ub, "BOB"), (uc, "CHLOE")):  # … mais BOB arrive avant CHLOE
    req("PATCH", f"v7/lobbies/{code}/players/{uid}", uid, {"name": nom, "score": 0, "last_seen": {".sv": "timestamp"}, "arrivee": {".sv": "timestamp"}}); time.sleep(0.05)
    threading.Thread(target=battre, args=(uid,), daemon=True).start()
ok("3 joueurs dans le salon", attendre(lambda: m.nb_joueurs >= 3))
ok("heure d'arrivée enregistrée pour l'hôte", isinstance(db()["v7"]["lobbies"][code]["players"][moi].get("arrivee"), (int, float)))
nb_donner = lambda: sum(1 for c in lob.player_slots if c.find_withtag("donner"))
ok("l'hôte voit « Donner l'hôte » sur la ligne des deux autres joueurs", attendre(lambda: nb_donner() == 2, 5), nb_donner())

lob.donner_hote(ub, "BOB")
ok("« Donner l'hôte » : BOB devient l'hôte", db()["v7"]["lobbies"][code]["settings"]["host_id"] == ub)
ok("l'ancien hôte n'a plus la main (plus de « Donner l'hôte »)", attendre(lambda: not m.is_host and nb_donner() == 0, 5))
req("PATCH", f"v7/lobbies/{code}/settings", ub, {"host_id": moi})  # BOB rend la main (l'hôte peut écrire dans tout le salon)
ok("l'hôte rendu par BOB : ALICE a de nouveau la main", attendre(lambda: m.is_host, 5))

# partie : pause puis reprise
pump(1); lob.lancer(); pump(3)
J = m.frames["PageJeu"]
J.quitter_jeu(); pump(0.5)
ok("retour en partie : fenêtre « Quitter la partie ? »", J.fen_quitter.winfo_ismapped())
J.fen_quitter.cacher(); J.mettre_en_pause(); pump(1.5)
ok("en pause : ALICE garde sa place dans le salon", moi in db()["v7"]["lobbies"][code]["players"])
ok("en pause : partie mémorisée pour « Reprendre »", (design.lire_config().get("partie_en_cours") or {}).get("code") == code and not m.lobby_code)
acc = m.frames["PageAccueil"]
ok("en pause : « Reprendre » proposé sur l'accueil du multijoueur", bool(acc.zone_reprise.winfo_children()))
acc.reprendre(design.lire_config()["partie_en_cours"]); pump(3)
ok("« Reprendre » ramène dans la partie en cours", m.lobby_code == code and J.active_sync)
k0 = int(J.clavier.canvas["A"]["height"]); J.adjust_zoom(0.2); pump(0.3); k1 = int(J.clavier.canvas["A"]["height"]); J.adjust_zoom(-0.2); pump(0.3)
ok("en partie : « + » agrandit aussi le clavier", k1 > k0 and int(J.clavier.canvas["A"]["height"]) == k0, (k0, k1))

# départ définitif de l'hôte : relais au premier arrivé (BOB), pas au plus petit identifiant (CHLOE)
J.quitter_definitif(); time.sleep(2.5)
s = db()["v7"]["lobbies"][code]
ok("départ définitif : ALICE n'est plus dans le salon", moi not in s["players"])
ok("relais au premier arrivé (BOB), et non au plus petit identifiant (CHLOE)", s["settings"]["host_id"] == ub, s["settings"]["host_id"])
vivants["ok"] = False
print(f"{sum(res)}/{len(res)} conformes"); app.destroy()
