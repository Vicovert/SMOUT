"""Robot joueur PC (vrai code Tkinter de SMOUT, sans écran) sur le faux serveur à règles.
Usage : robot_pc.py <repo> '<json scénario>'"""
import sys, os, time, json, urllib.request, traceback, random
repo, S = sys.argv[1], json.loads(sys.argv[2])
if S.get("home"): os.environ["HOME"] = S["home"]  # reprise : même dossier de configuration que le robot qui a planté
if S.get("attente_reprise"): time.sleep(S["attente_reprise"])
os.chdir(repo); sys.path.insert(0, repo)
import requests
class Sess(requests.Session):
    def request(self, method, url, *a, **k):
        if "firebasedatabase.app" in url: url = "http://127.0.0.1:9000/" + url.split(".app/", 1)[1]
        elif "securetoken" in url: url = "http://127.0.0.1:9000/token"
        elif "identitytoolkit" in url: url = "http://127.0.0.1:9000/signup"
        return super().request(method, url, *a, **k)
requests.Session = Sess
import tkinter as tk, design; design.charger_polices()
erreurs = []
import page_multi as pm, main as Mn
_tb = traceback.print_exc
def capte(*a, **k): erreurs.append(traceback.format_exc()); _tb(*a, **k)
pm.traceback.print_exc = capte
design.appliquer_theme(Mn.THEMES["PLATEAU DE NUIT"]); pm.apply_theme_multi(Mn.THEMES["PLATEAU DE NUIT"])
root = tk.Tk(); root.geometry("1200x860")
root.report_callback_exception = lambda *a: erreurs.append("".join(traceback.format_exception(*a)))
class Ctrl:
    def winfo_toplevel(self): return root
    def creer_menu_accueil(self): pass
fr = tk.Frame(root); fr.pack(fill="both", expand=True)
A = pm.PageMulti(fr, Ctrl()); A.pack(fill="both", expand=True)
nom = S["nom"]; A.frames["PageAccueil"].champ_pseudo.set(nom); A.assurer_connexion()
R = {"nom": nom, "support": "PC", "mots": [], "evenements": [], "erreurs": erreurs}
def log(*a): print(f"[PC {nom}]", *a, flush=True); R["evenements"].append(" ".join(map(str, a)))
def pump(t):
    end = time.time() + t
    while time.time() < end: root.update(); time.sleep(0.01)
def db(): return json.loads(urllib.request.urlopen("http://127.0.0.1:9000/__admin.json").read() or b"null") or {}
def attendre(c, t=60):
    end = time.time() + t
    while time.time() < end:
        pump(0.1)
        try:
            if c(): return True
        except Exception: pass
    return False
def fin(ok=True):
    R["ok"] = ok and not erreurs
    try: R["scores_base"] = {v["name"]: v.get("score") for v in db()["v7"]["lobbies"][A.lobby_code]["players"].values()}
    except Exception: pass
    json.dump(R, open(S["sortie"], "w"), ensure_ascii=False, indent=1); log("fin", "OK" if R["ok"] else "ÉCHEC")
    try: A.quitter_lobby_logic(True); pump(1.5)
    except Exception: pass
    sys.exit(0)
J, lob = A.frames["PageJeu"], A.frames["PageLobby"]
try:
    if S["role"] == "rapide":
        A.frames["PageAccueil"].partie_rapide(); pump(1.5)
        if not A.lobby_code: log("ÉCHEC partie rapide"); fin(False)
        S["role"] = "host" if A.is_host else "join"; R["code"] = A.lobby_code; log("partie rapide :", "salon créé" if A.is_host else "a rejoint", A.lobby_code)
    elif S["role"] == "reprise":
        pe = design.lire_config().get("partie_en_cours")
        if not pe or not A.frames["PageAccueil"].zone_reprise.winfo_children(): log("ÉCHEC pas de proposition de reprise"); fin(False)
        A.frames["PageAccueil"].reprendre(pe); pump(1)
        if not A.lobby_code: log("ÉCHEC reprise"); fin(False)
        log("partie reprise", A.lobby_code, "score", A.current_score); R["code"] = A.lobby_code
    elif S["role"] == "host":
        A.show_frame("PageHostSetup"); hs = A.frames["PageHostSetup"]
        if S.get("mdp"): hs.inter.basculer(); hs.champ_mdp.set(S["mdp"])
        if S.get("prive"): hs.set_vis(False)
        hs.valider(); pump(1)
        if not A.lobby_code: log("ÉCHEC création"); fin(False)
        log("salon créé", A.lobby_code); R["code"] = A.lobby_code
    else:
        cible = S.get("hote")
        def trouver():
            idx = (db().get("v7", {}).get("index") or {})
            c = [(v.get("maj", 0), k) for k, v in idx.items() if v.get("status") == "waiting" and v.get("hote") == cible]
            return max(c)[1] if c else None
        if not attendre(lambda: trouver(), 90): log("ÉCHEC salon introuvable"); fin(False)
        code = trouver(); pa = A.frames["PageAccueil"]
        if S.get("mdp_faux"):
            refus = not pa.rejoindre(code, S["mdp_faux"], silencieux=True)
            log("mauvais mot de passe refusé" if refus else "BUG: mauvais mot de passe accepté"); R["mdp_faux_refuse"] = refus
            if not refus: fin(False)
        pm.tkm.showwarning = lambda t, m, *a, **k: log("alerte:", m)
        if S.get("via_ui"):
            pa.tenter_join(code); pump(1)
            if not A.lobby_code: log("ÉCHEC rejoindre"); fin(S.get("attendu_refus", False))
        elif not pa.rejoindre(code, S.get("mdp", ""), silencieux=True): log("ÉCHEC rejoindre"); fin(False)
        log("a rejoint", code); R["code"] = code
    for partie in range(1, S.get("parties", 1) + 1):
        if S["role"] == "host":
            if not attendre(lambda: lob.active_sync and A.nb_joueurs >= S.get("nb", 2), 120): log("ÉCHEC joueurs manquants", A.nb_joueurs); fin(False)
            if partie == 1:
                lob.set_mode(S["mode"]) if S["mode"] != "CLASSIQUE" else None
                lob.c_rounds.set_valeur(S.get("manches", 1))
                if S.get("timer"): lob.s_time.set_valeur(S["timer"])
                if S.get("essais"): lob.s_essais.set_valeur(S["essais"])
                lob.sync_params()
            pump(1.5); lob.lancer(); log("partie lancée", partie)
        debut = 1
        if S["role"] == "reprise":
            attendre(lambda: J.active_sync, 90); debut = int(J.round_actuel); log("reprend à la manche", debut)
        for manche in range(debut, S.get("manches", 1) + 1):
            if manche > 1 and A.frames["PageScoreFinal"].active_sync: log("partie terminée avant la manche", manche); break
            if not attendre(lambda: J.active_sync and int(J.round_actuel) == manche and J.controller.settings_config.get("game_mode") == S["mode"], 90):
                log("ÉCHEC manche pas commencée", manche); fin(False)
            pump(1.2); R["mots"].append(J.mot); log(f"partie {partie} manche {manche} mot {J.mot}")
            if getattr(J, "elimine", False):
                log(f"manche {manche} : éliminé, spectateur"); R["elimine"] = manche
                attendre(lambda: (J.active_sync and int(J.round_actuel) > manche) or A.frames["PageScoreFinal"].active_sync, 300); continue
            if S.get("planter_manche") == manche:
                log("PLANTAGE simulé"); json.dump(dict(R, ok=True, plante=True), open(S["sortie"], "w"), ensure_ascii=False); os._exit(0)
            jeu = S.get("jeu", "gagne")
            if jeu == "gagne":
                J.tape = list(J.mot[1:]) if S["mode"] == "MYSTERE" else list(J.mot); J.valider()
            elif jeu == "perd":
                faux = [m for m in sorted(A.banque_verif) if len(m) == len(J.mot) and m != J.mot and (S["mode"] == "MYSTERE" or m[0] == J.mot[0])]
                for k in range(int(J.controller.settings_config.get("essais", 6))):
                    w = faux[k]; J.tape = list(w[1:]) if S["mode"] == "MYSTERE" else list(w); J.valider(); pump(0.2)
            elif jeu == "rush":
                trouves = 0
                while J.timer_actif and not J.fini_local and J.temps_restant > 2:
                    J.tape = list(J.mot); J.valider(); trouves += 1; pump(0.6)
                R.setdefault("rush_trouves", []).append(trouves); log("rush trouvés", trouves)
            pump(1)
            # attendre la manche suivante ou les résultats ; si on est (ou devient) l'hôte, cliquer sur le bouton
            clic = [False]
            def suite():
                if (J.active_sync and int(J.round_actuel) > manche) or A.frames["PageScoreFinal"].active_sync: return True
                if not clic[0] and J.btn_next.winfo_manager() != "" and A.is_host: clic[0] = True; J.clic_suivant()
                return False
            if not attendre(suite, 300): log("ÉCHEC manche suivante / résultats"); fin(False)
        if not attendre(lambda: A.frames["PageScoreFinal"].active_sync, 90): log("ÉCHEC pas de résultats"); fin(False)
        pump(2.5)
        R.setdefault("resultats", []).append({v["name"]: v.get("score") for v in db()["v7"]["lobbies"][A.lobby_code]["players"].values()})
        log("résultats", R["resultats"][-1])
        if partie < S.get("parties", 1):
            if A.is_host: A.frames["PageScoreFinal"].retour_lobby_host()
            if not attendre(lambda: lob.active_sync, 60): log("ÉCHEC retour au salon"); fin(False)
            log("retour au salon")
    pump(S.get("rester", 6))
    fin(True)
except SystemExit: raise
except Exception:
    erreurs.append(traceback.format_exc()); log("EXCEPTION"); fin(False)
