"""Compte SMOUT côté PC (compte.py) sur le faux serveur : création (rattachement du joueur anonyme), erreurs,
connexion sur un 2e appareil, synchronisation de l'avancement dans les deux sens, mot de passe oublié, déconnexion.
Usage : test_compte.py <repo>"""
import sys, os, time, json, tempfile, urllib.request
repo = sys.argv[1]; os.chdir(repo); sys.path.insert(0, repo)
import requests
class Sess(requests.Session):
    def request(self, method, url, *a, **k):
        if "firebasedatabase.app" in url: url = "http://127.0.0.1:9000/" + url.split(".app/", 1)[1]
        elif "securetoken" in url: url = "http://127.0.0.1:9000/token"
        elif "identitytoolkit" in url: url = "http://127.0.0.1:9000/signup?op=" + url.split("accounts:")[1].split("?")[0]  # l'opération compte (update est refusé)
        return super().request(method, url, *a, **k)
requests.Session = Sess
import design, compte
res = []
def ok(nom, c, info=""): res.append(bool(c)); print(("OK    " if c else "ÉCHEC ") + nom + (f"  — {info}" if info and not c else ""), flush=True)
def appareil():  # un nouvel appareil = un nouveau dossier de configuration
    os.environ["HOME"] = tempfile.mkdtemp(); compte.auth().oublier()
def db(): return json.loads(urllib.request.urlopen("http://127.0.0.1:9000/__admin.json").read() or b"null") or {}
mel = f"alice{int(time.time())}@test.fr"

# appareil A : un joueur anonyme avec de l'avancement, puis création du compte
appareil()
design.maj_config(pseudo="ALICE", theme="AURORE", mdj_serie=3, stats={"solo": {"parties": 5, "victoires": 4}}, custom_themes={"Mon.thème #1": {"bg": "#101010", "accent1": "#ff0000", "accent2": "#00ff00"}})
uid_a = (compte.auth().jeton(), compte.auth().uid)[1]
ok("joueur anonyme créé", bool(uid_a))
ok("mot de passe trop court refusé", compte.creer(mel, "abc") == compte.ERREURS["WEAK_PASSWORD"], compte.creer(mel, "abc"))
ok("adresse invalide refusée", compte.creer("pas-une-adresse", "secret1") == compte.ERREURS["INVALID_EMAIL"])
ok("création du compte", compte.creer(mel, "secret1") is None)
ok("le joueur anonyme est rattaché au compte (même identifiant)", compte.auth().uid == uid_a)
c = (db().get("v7", {}).get("comptes") or {}).get(uid_a) or {}
d = json.loads(c.get("donnees") or "{}")
ok("avancement envoyé au compte (pseudo, statistiques, thème perso au nom spécial)", d.get("pseudo") == "ALICE" and d.get("stats", {}).get("solo", {}).get("parties") == 5 and "Mon.thème #1" in (d.get("custom_themes") or {}), str(d)[:200])

# appareil B : erreurs puis connexion
appareil()
design.maj_config(pseudo="BOBBY", mdj_serie=0)
ok("adresse déjà utilisée refusée à la création", compte.creer(mel, "autre12") == compte.ERREURS["EMAIL_EXISTS"])
ok("mauvais mot de passe refusé", compte.connecter(mel, "faux123") == compte.ERREURS["INVALID_LOGIN_CREDENTIALS"])
ok("connexion sur un 2e appareil", compte.connecter(mel, "secret1") is None)
cfg = design.lire_config()
ok("même joueur sur le 2e appareil", compte.auth().jeton() and compte.auth().uid == uid_a)
ok("l'avancement du compte remplace celui de l'appareil", cfg.get("pseudo") == "ALICE" and cfg.get("mdj_serie") == 3 and cfg.get("theme") == "AURORE" and (cfg.get("stats") or {}).get("solo", {}).get("victoires") == 4, str(cfg)[:200])
ok("on reste connecté (jeton gardé dans la configuration)", bool(cfg.get("auth_refresh")) and cfg.get("compte_email") == mel)

# changement sur B : envoyé automatiquement, relu par A
design.maj_config(mdj_serie=9)
time.sleep(3.5)
d = json.loads(((db().get("v7", {}).get("comptes") or {}).get(uid_a) or {}).get("donnees") or "{}")
ok("un changement est envoyé automatiquement au compte", d.get("mdj_serie") == 9, str(d.get("mdj_serie")))
home_b = os.environ["HOME"]
os.environ["HOME"] = tempfile.mkdtemp()  # A, simulé par une copie de sa configuration d'avant
design.maj_config(compte_email=mel, auth_refresh="r-" + uid_a, mdj_serie=3, compte_sync=1)
compte.auth().oublier()
ok("au démarrage, l'appareil relit l'avancement plus récent du compte", compte.tirer() and design.lire_config().get("mdj_serie") == 9)
ok("rien à relire quand l'appareil est à jour", compte.tirer() is False)

# mot de passe oublié, déconnexion
ok("mot de passe oublié : e-mail envoyé", compte.reinitialiser(mel) is None)
os.environ["HOME"] = home_b
compte.deconnecter(); cfg = design.lire_config()
ok("déconnexion : compte oublié sur l'appareil, avancement local gardé", not cfg.get("compte_email") and not cfg.get("auth_refresh") and cfg.get("pseudo") == "ALICE")
compte.auth().jeton()
ok("après déconnexion : un nouveau joueur anonyme", compte.auth().uid and compte.auth().uid != uid_a)
croise = os.environ.get("COMPTE_CROISE")  # compte créé sur le web par tests/web/compte_web.js (mot de passe « croise1 »)
if croise:
    appareil()
    ok("compte créé sur le web : connexion sur PC", compte.connecter(croise, "croise1") is None)
    cfg = design.lire_config()
    ok("compte créé sur le web : avancement retrouvé sur PC (pseudo, série, thème)", cfg.get("pseudo") == "ALICE" and cfg.get("mdj_serie") == 9 and cfg.get("theme") == "AURORE", str(cfg)[:160])
print(f"{sum(res)}/{len(res)} conformes")
