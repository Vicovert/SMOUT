"""9.2 côté PC (Tk sous Xvfb, faux serveur) : amis. Les autres joueurs sont simulés par des requêtes REST.
Usage : test_amis_pc.py <repo>"""
import sys, os, time, json, tempfile, random, urllib.request
repo = sys.argv[1]; os.environ["HOME"] = tempfile.mkdtemp(); os.chdir(repo); sys.path.insert(0, repo)
import requests
class Sess(requests.Session):
    def request(self, method, url, *a, **k):
        if "firebasedatabase.app" in url: url = "http://127.0.0.1:9000/" + url.split(".app/", 1)[1]
        elif "securetoken" in url: url = "http://127.0.0.1:9000/token"
        elif "identitytoolkit" in url: url = "http://127.0.0.1:9000/signup?op=" + url.split("accounts:")[1].split("?")[0]
        return super().request(method, url, *a, **k)
requests.Session = Sess
import tkinter as tk, design; design.charger_polices()
import main as Mn, page_multi as pm, amis, compte
res = []
def ok(nom, c, info=""): res.append(bool(c)); print(("OK    " if c else "ÉCHEC ") + nom + (f"  — {info}" if info and not c else ""), flush=True)
B = "http://127.0.0.1:9000"; SV = {".sv": "timestamp"}
def req(m, chemin, uid, corps=None):
    r = urllib.request.Request(f"{B}/{chemin}.json?auth=tok-{uid}", method=m, data=json.dumps(corps).encode() if corps is not None else None)
    try: return urllib.request.urlopen(r).status
    except urllib.error.HTTPError as e: return e.code
def db(): return json.loads(urllib.request.urlopen(B + "/__admin.json").read() or b"null") or {}
def inscrire(): return json.loads(urllib.request.urlopen(urllib.request.Request(B + "/signup", method="POST", data=b"{}")).read())["localId"]
alertes = []; design.informer = lambda w, m, *a, **k: alertes.append(m); pm.informer = design.informer
mdp_saisi = {"v": "chat"}; design.demander_texte = lambda *a, **k: mdp_saisi["v"]

design.maj_config(pseudo="ZOE")
ok("compte créé", compte.creer(f"zoe{int(time.time())}@test.fr", "secret1") is None)
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
moi = compte.auth().uid
app.ecran_amis(); pump(1.5)
ok("écran Amis : mon code ami", attendre(lambda: len(amis.E["code"]) == 6 and app.lbl_code_ami.cget("text") == amis.E["code"], 10), amis.E["code"])
ok("profil public (pseudo, code)", (db()["v7"]["profils"][moi] or {}).get("code") == amis.E["code"])
# B demande à devenir ami : bandeau sur l'accueil, puis acceptation
ub = inscrire(); req("PUT", f"v7/profils/{ub}", ub, {"pseudo": "BOB", "code": "", "vu": SV, "salon": ""})
req("PUT", f"v7/amis_demandes/{moi}/{ub}", ub, {"pseudo": "BOB", "t": SV})
app.creer_menu_accueil(); app.boucle_amis()
ok("bandeau partout : « veut être ton ami »", attendre(lambda: app.bandeau is not None and app.bandeau.winfo_ismapped(), 15))
amis.accepter(ub); pump(0.5)
d = db()["v7"]
ok("acceptée : amis des deux côtés", d["amis"][moi][ub] and d["amis"][ub][moi] and ub not in (d.get("amis_demandes", {}).get(moi) or {}))
amis.charger()
ok("statut : Bob « En ligne »", amis.statut(amis.E["profils"][ub])[0] == "En ligne", amis.statut(amis.E["profils"][ub]))
# ajouter C par son code
uc = inscrire(); cc = "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6)); req("PUT", f"v7/codes_amis/{cc}", uc, uc)
ok("ajouter par code : demande envoyée", amis.ajouter(cc.lower()) is None and moi in (db()["v7"]["amis_demandes"].get(uc) or {}))
ok("ajouter son propre code refusé", amis.ajouter(amis.E["code"]) == "C'est ton propre code.")
# invitation de Bob dans une partie en cours, salon protégé : spectateur direct, mot de passe demandé
code = str(random.randint(1000, 9999))
reg = {"essais": 8, "min": 6, "max": 7, "rounds": 2, "timer": 120, "host_id": ub, "visible": True, "version": pm.VERSION_JEU, "game_mode": "CLASSIQUE", "rush_seed": 99, "current_round": 1, "start_time": time.time()}
req("PUT", f"v7/secrets/{code}", ub, pm.preuve_salon(code, "chat"))
req("PUT", f"v7/lobbies/{code}", ub, {"status": "playing", "maj": SV, "settings": reg, "players": {ub: {"name": "BOB", "score": 0, "last_seen": SV, "arrivee": SV}}})
req("PUT", f"v7/index/{code}", ub, {"owner": ub, "hote": "BOB", "nb": 1, "prive": True, "visible": True, "status": "playing", "version": pm.VERSION_JEU, "maj": SV})
ok("invitation envoyée par l'ami", req("PUT", f"v7/invitations/{moi}/{code}", ub, {"de": ub, "pseudo": "BOB", "t": SV}) == 200)
amis.E["vues"].clear(); app.creer_menu_accueil(); app.boucle_amis()
ok("bandeau : « t'invite dans son salon »", attendre(lambda: app.bandeau is not None and str(app.bandeau.cle).startswith("i"), 15))
app.rejoindre_invitation(code); pump(2)
m = app._multi
ok("invitation pendant une partie : spectateur direct (mot de passe fourni)", attendre(lambda: m.spectateur and moi in (db()["v7"]["lobbies"][code].get("spectateurs") or {}), 15))
ok("invitation effacée après usage", attendre(lambda: code not in (db()["v7"].get("invitations", {}).get(moi) or {}), 5))
# inviter depuis son propre salon
m.quitter_lobby_logic(); pump(1); app.creer_menu_accueil(); m = app.ouvrir_multi(); pump(1)
m.frames["PageAccueil"].champ_pseudo.set("ZOE"); m.assurer_connexion()
m.settings_config.update({"password": "", "visible": True}); m.is_host, m.lobby_code = True, ""; m.show_frame("PageLobby"); pump(2.5)
lob = m.frames["PageLobby"]
ok("salon : bouton « Inviter des amis »", lob.btn_inviter.winfo_ismapped())
lob.panneau_inviter.ouvrir(); ok("panneau : Bob avec « Inviter »", attendre(lambda: any(isinstance(w, design.Bouton) and w.texte == "Inviter" for w in lob.panneau_inviter.liste.winfo_children() for w in w.interieur.winfo_children() if hasattr(w, "texte")) if False else
   any(getattr(x, "texte", "") == "Inviter" for p_ in lob.panneau_inviter.liste.winfo_children() for x in getattr(p_, "interieur", p_).winfo_children()), 10))
ok("invitation envoyée depuis le salon", amis.inviter(ub, m.lobby_code) and m.lobby_code in (db()["v7"]["invitations"].get(ub) or {}))
print(f"{sum(res)}/{len(res)} conformes"); app.destroy()
