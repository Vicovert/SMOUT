"""9.4 côté PC (Tk sous Xvfb, faux serveur) : classements (accueil, menu Solo, marathon en direct) et fiche joueur.
Usage : test_classements_pc.py <repo>"""
import sys, os, time, json, tempfile, urllib.request
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
import main as Mn, classements, compte, amis
res = []
def ok(nom, c, info=""): res.append(bool(c)); print(("OK    " if c else "ÉCHEC ") + nom + (f"  — {info}" if info and not c else ""), flush=True)
B = "http://127.0.0.1:9000"; SV = {".sv": "timestamp"}
def req(m, chemin, uid, corps=None):
    r = urllib.request.Request(f"{B}/{chemin}.json?auth=tok-{uid}", method=m, data=json.dumps(corps).encode() if corps is not None else None)
    try: return urllib.request.urlopen(r).status
    except urllib.error.HTTPError as e: return e.code
def db(): return json.loads(urllib.request.urlopen(B + "/__admin.json").read() or b"null") or {}
def inscrire(): return json.loads(urllib.request.urlopen(urllib.request.Request(B + "/signup", method="POST", data=b"{}")).read())["localId"]
uz = inscrire()
req("PUT", f"v7/classements/marathon/{uz}", uz, {"pseudo": "ZEBULON", "record": 58, "score": 58000, "maj": SV}); req("PUT", f"v7/classements/mdj/{uz}", uz, {"pseudo": "ZEBULON", "meilleure": 40, "maj": SV})
req("PUT", f"v7/profils/{uz}", uz, {"pseudo": "ZEBULON", "code": "", "vu": SV, "salon": "", "cree": 1790000000000})
design.maj_config(pseudo="ZOE", stats={"mdj": {"parties": 9, "victoires": 9, "repartition": {}, "serie": 0, "meilleure_serie": 6, "meilleur_score": 0}, "marathon": {"parties": 2, "record": 11, "record_score": 0, "mots": 20, "meilleur_points": 11000}})
ok("compte créé", compte.creer(f"zoe{int(time.time())}@test.fr", "secret1") is None)
classements.pousser(); moi = compte.auth().uid; d = db()["v7"]["classements"]
ok("envoyé à la base (mot du jour 6, marathon 11)", d["mdj"][moi]["meilleure"] == 6 and d["marathon"][moi]["record"] == 11 and d["marathon"][moi].get("score") == 11000)
l = classements.lire("marathon")
ok("lecture triée", [e["valeur"] for e in l] == sorted([e["valeur"] for e in l], reverse=True) and l[0]["valeur"] >= 58)
app = Mn.MenuPrincipal()
def pump(t):
    end = time.time() + t
    while time.time() < end: app.update(); time.sleep(0.01)
def attendre(c, t=15):
    end = time.time() + t
    while time.time() < end:
        pump(0.1)
        try:
            if c(): return True
        except Exception: pass
    return False
app.geometry("1200x840+0+0"); pump(1); app.creer_menu_accueil(); pump(0.5)  # le classement sur le côté demande ≥ 1180 px
def nb_lignes(p):  # 9.8 : lignes dans la zone qui défile
    z = [w for w in p.corps.winfo_children() if isinstance(w, design.Defilant)]
    return len(z[0].interieur.winfo_children()) if z else 0
def pan(racine):  # panneaux de classement, à toute profondeur
    l = []
    for w in racine.winfo_children(): l += [w] if isinstance(w, classements.PanneauClassement) else pan(w)
    return l
page = app.container.winfo_children()[0]
ok("accueil : classement du mot du jour à droite", attendre(lambda: pan(page) and pan(page)[0].fait.is_set() and nb_lignes(pan(page)[0]) >= 2))
app.ouvrir_menu_solo(); pump(0.5); ms = app.container.winfo_children()[0]
ok("menu Solo : classement du marathon", attendre(lambda: pan(ms) and pan(ms)[0].fait.is_set() and nb_lignes(pan(ms)[0]) >= 2))
app.ouvrir_marathon(); pump(1); ps = app.container.winfo_children()[0]
ok("marathon : classement en direct", attendre(lambda: pan(ps) and pan(ps)[0].fait.is_set() and "dépasser" in pan(ps)[0].note.cget("text"), 15), pan(ps)[0].note.cget("text") if pan(ps) else "")
f = classements.fiche_joueur(app, uz); pump(0.5)
txt = " ".join(w.cget("text") for w in f.interieur.winfo_children() if isinstance(w, tk.Label))
ok("fiche joueur : pseudo et ancienneté", "Zebulon" in txt and "Joueur depuis" in txt, txt)
print(f"{sum(res)}/{len(res)} conformes"); app.destroy()
