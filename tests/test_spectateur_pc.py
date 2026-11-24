"""9.1 côté PC (Tk sous Xvfb, faux serveur) : spectateurs et demandes pour regarder une partie en cours.
Les autres participants (hôte, joueurs) sont simulés par des requêtes REST. Usage : test_spectateur_pc.py <repo>"""
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
SV = {".sv": "timestamp"}
def req(m, chemin, uid, corps=None):
    r = urllib.request.Request(f"{B}/{chemin}.json?auth=tok-{uid}", method=m, data=json.dumps(corps).encode() if corps is not None else None)
    try: return urllib.request.urlopen(r).status
    except urllib.error.HTTPError as e: return e.code
def db(): return json.loads(urllib.request.urlopen(B + "/__admin.json").read() or b"null") or {}
def inscrire(): return json.loads(urllib.request.urlopen(urllib.request.Request(B + "/signup", method="POST", data=b"{}")).read())["localId"]
pm.confirmer = lambda *a, **k: True
alertes = []
def multi():  # (ré)ouvre le multijoueur : quitter une partie ramène à l'accueil principal
    global m, pr, lob, J
    app.ouvrir_multi(); pump(1)
    m = next(w for w in app.container.winfo_children() if hasattr(w, "frames"))
    m.frames["PageAccueil"].champ_pseudo.set("ZOE"); m.assurer_connexion()
    pr, lob, J = m.frames["PageRejoindre"], m.frames["PageLobby"], m.frames["PageJeu"]; pm.informer = lambda w, m, *a, **k: alertes.append(m)

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
m.frames["PageAccueil"].champ_pseudo.set("ZOE"); m.assurer_connexion(); moi = m.player_id
pr, lob, J = m.frames["PageRejoindre"], m.frames["PageLobby"], m.frames["PageJeu"]

# salon d'un hôte simulé, plein (8 joueurs)
import random; hote = inscrire(); code = str(random.randint(1000, 9999))
reglages = {"essais": 8, "min": 6, "max": 7, "rounds": 2, "timer": 120, "host_id": hote, "visible": True, "version": pm.VERSION_JEU, "game_mode": "CLASSIQUE", "rush_seed": 4242}
req("PUT", f"v7/lobbies/{code}", hote, {"status": "waiting", "maj": SV, "settings": reglages, "players": {hote: {"name": "HUGO", "score": 0, "last_seen": SV, "arrivee": SV}}})
autres = [inscrire() for _ in range(7)]
for i, u in enumerate(autres): req("PUT", f"v7/lobbies/{code}/players/{u}", u, {"name": f"J{i}", "score": 0, "last_seen": SV, "arrivee": SV})
def index(status="waiting"): req("PUT", f"v7/index/{code}", hote, {"owner": hote, "hote": "HUGO", "nb": len(db()["v7"]["lobbies"][code]["players"]), "prive": False, "visible": True, "status": status, "version": pm.VERSION_JEU, "maj": SV})
vivants = {"ok": True}
def battre():
    while vivants["ok"]:
        try:
            for u in [hote] + autres:
                if u in (db()["v7"]["lobbies"][code].get("players") or {}): req("PATCH", f"v7/lobbies/{code}/players/{u}", u, {"last_seen": SV})
            req("PATCH", f"v7/lobbies/{code}", hote, {"maj": SV}); index(db()["v7"]["lobbies"][code].get("status", "waiting"))
        except Exception: pass
        time.sleep(3)
index(); threading.Thread(target=battre, daemon=True).start()

ok("salon plein : on entre comme spectateur", pr.rejoindre(code, "") and m.spectateur and attendre(lambda: lob.active_sync, 8))
ok("compteur « 1 spectateur » dans le salon", attendre(lambda: "1 spectateur" in lob.lbl_spect.cget("text"), 8), lob.lbl_spect.cget("text"))
actions = lambda: [c.itemcget(i, "text") for c in lob.player_slots for i in c.find_withtag("action")]
ok("plein : pas de « Prendre la place »", attendre(lambda: "Prendre la place" not in actions(), 3))
req("DELETE", f"v7/lobbies/{code}/players/{autres[-1]}", autres[-1]); autres.pop()
ok("une place se libère : « Prendre la place »", attendre(lambda: "Prendre la place" in actions(), 8), actions())
lob.prendre_place(); pump(1)
s = db()["v7"]["lobbies"][code]
ok("« Prendre la place » : joueur", not m.spectateur and moi in s["players"] and moi not in (s.get("spectateurs") or {}))
ok("« Passer spectateur » sur sa propre ligne", attendre(lambda: "Passer spectateur" in actions(), 8), actions())
lob.passer_spectateur(); pump(1)
s = db()["v7"]["lobbies"][code]
ok("« Passer spectateur » : spectateur, place libérée", m.spectateur and moi not in s["players"] and moi in s["spectateurs"])

# l'hôte simulé lance la partie : vue spectateur
req("PATCH", f"v7/lobbies/{code}", hote, {"status": "playing", "settings": dict(reglages, current_round=1, start_time=time.time())})
ok("partie : vue spectateur (pas de grille à soi ni de clavier)", attendre(lambda: J.active_sync and J.lbl_spect.winfo_ismapped() and not J.zone_clavier.winfo_ismapped() and not J.moi_side.winfo_ismapped(), 15))
ok("partie : les grilles de tous les joueurs", len(J.adv_widgets) == len(db()["v7"]["lobbies"][code]["players"]), (len(J.adv_widgets), len(db()["v7"]["lobbies"][code]["players"])))
ok("partie : code du salon affiché", J.s_code.lbl.cget("text") == code, J.s_code.lbl.cget("text"))
ok("spectateur : aucune écriture dans la partie", m.fb_ok("put", f"lobbies/{code}/match_data/{moi}/0", {"c": ["B"], "l": ["A"]}) is False and moi not in (db()["v7"]["lobbies"][code].get("match_data") or {}))
J.quitter_jeu(); pump(1)
ok("le spectateur quitte : sa fiche est effacée", attendre(lambda: moi not in (db()["v7"]["lobbies"][code].get("spectateurs") or {}), 6))

# demande pendant la partie : refusée puis acceptée
multi(); m.show_frame("PageRejoindre"); pump(0.5)
ok("partie en cours : demande envoyée, fenêtre d'attente", pr.rejoindre(code, "") and attendre(lambda: moi in (db()["v7"].get("demandes", {}).get(code) or {}), 5) and pr.fen_attente.winfo_ismapped())
req("DELETE", f"v7/demandes/{code}/{moi}", hote)
ok("demande refusée : prévenu", attendre(lambda: any("refusé" in a for a in alertes), 8), alertes)
pr.rejoindre(code, ""); attendre(lambda: moi in (db()["v7"].get("demandes", {}).get(code) or {}), 5)
req("PUT", f"v7/lobbies/{code}/spectateurs/{moi}", hote, {"name": "ZOE", "last_seen": SV}); req("DELETE", f"v7/demandes/{code}/{moi}", hote)
ok("demande acceptée : on regarde la partie", attendre(lambda: m.spectateur and J.active_sync and J.lbl_spect.winfo_ismapped(), 15))
J.quitter_jeu(); pump(1)

# le PC hôte reçoit une demande : cloche, panneau, accepter
vivants["ok"] = False; pump(0.5)
multi()
m.settings_config.update({"password": "", "visible": True}); m.is_host, m.lobby_code = True, ""; m.show_frame("PageLobby"); pump(2)
code2 = m.lobby_code; u2 = inscrire()
req("PATCH", f"v7/lobbies/{code2}/players/{u2}", u2, {"name": "BOB", "score": 0, "last_seen": SV, "arrivee": SV}); pump(2)
lob.lancer(); pump(3)
ok("hôte PC : partie lancée", attendre(lambda: J.active_sync and not m.spectateur, 10))
d3 = inscrire(); req("PUT", f"v7/demandes/{code2}/{d3}", d3, {"name": "DAVID", "t": SV})
ok("hôte PC : la cloche montre « 1 »", attendre(lambda: J.badge.winfo_ismapped() and J.badge.cget("text") == "1", 8))
J.basculer_tiroir(); pump(0.5)
ok("hôte PC : panneau des demandes ouvert, le jeu reste visible", J.tiroir.winfo_ismapped() and J.zone_clavier.winfo_ismapped())
J.repondre(d3, {"name": "DAVID"}, True); pump(1)
s = db()["v7"]["lobbies"][code2]
ok("hôte PC : demande acceptée (spectateur, demande effacée)", d3 in (s.get("spectateurs") or {}) and d3 not in (db()["v7"].get("demandes", {}).get(code2) or {}))
print(f"{sum(res)}/{len(res)} conformes"); app.destroy()
