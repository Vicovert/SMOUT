"""Amis (9.2) côté PC : même logique que l'objet Amis de web/smout.js.
Réservé aux comptes e-mail (même joueur sur tous les appareils). Code ami (codes_amis/<CODE> → uid), profil public
(profils/<uid> : pseudo, code, vu, salon), liste (amis/<uid>/<ami>), demandes (amis_demandes/<cible>/<de>),
invitations (invitations/<cible>/<code du salon>) : on rejoint sans taper le code, le mot de passe reste demandé."""
import random, time, traceback, email.utils
import design, compte

ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SV = {".sv": "timestamp"}
E = {"code": "", "uid_code": None, "liste": {}, "profils": {}, "demandes": {}, "invitations": {}, "vues": set(), "n": 0, "decalage": 0.0}


def _req(methode, chemin, donnees=None):
    """(ok, json) d'une requête REST sous /v7 avec la connexion du compte."""
    try:
        jeton = compte.auth().jeton()
        if not jeton: return False, None
        kw = {"params": {"auth": jeton}, "timeout": 5}
        if donnees is not None: kw["json"] = donnees
        r = getattr(compte.session(), methode)(f"{compte.FIREBASE_URL}{compte.RACINE}/{chemin}.json", **kw)
        if "Date" in r.headers:
            try: E["decalage"] = email.utils.parsedate_to_datetime(r.headers["Date"]).timestamp() - time.time()
            except Exception: pass
        try: j = r.json()
        except Exception: j = None
        return r.status_code == 200, j
    except Exception:
        traceback.print_exc(); return False, None

def lire(chemin): return _req("get", chemin)[1]
def ok(methode, chemin, donnees=None): return _req(methode, chemin, donnees)[0]
def maintenant_ms(): return (time.time() + E["decalage"]) * 1000
def uid(): return compte.auth().uid
def pseudo(): return design.nettoyer_pseudo(design.lire_config().get("pseudo", "")).strip() or "ANONYME"
def actif(): return bool(compte.email()) and bool(uid())


# 9.14 : pseudos uniques (comme l'objet Pseudos du site). pseudos/<PSEUDO> = uid de celui qui l'a réservé en l'enregistrant dans son profil
PAS_DE_RESEAU = "Connexion au serveur impossible. Vérifie ta connexion internet."


def _cle_pseudo(p):
    from urllib.parse import quote
    return quote(design.nettoyer_pseudo(p).strip(), safe="")


def pseudo_libre(p):
    """True si personne d'autre n'a réservé ce pseudo (hors ligne : on ne bloque pas)."""
    k = design.nettoyer_pseudo(p).strip()
    if not k or k == "ANONYME" or not compte.auth().jeton(): return True
    v = lire(f"pseudos/{_cle_pseudo(k)}")
    return not v or v == uid()


def reserver_pseudo(p):
    """Réserve le pseudo pour ce joueur et libère l'ancien ; renvoie un message d'erreur ou None."""
    k = design.nettoyer_pseudo(p).strip()
    if not k: return "Choisis un pseudo."
    if not compte.auth().jeton(): return PAS_DE_RESEAU
    okl, v = _req("get", f"pseudos/{_cle_pseudo(k)}")
    if not okl: return PAS_DE_RESEAU
    if v and v != uid(): return "Ce pseudo est déjà pris."
    if not ok("put", f"pseudos/{_cle_pseudo(k)}", uid()): return "Ce pseudo est déjà pris."
    ancien = design.lire_config().get("pseudo_reserve")
    if ancien and ancien != k: ok("delete", f"pseudos/{_cle_pseudo(ancien)}")
    design.maj_config(pseudo=k, pseudo_reserve=k); return None


def assurer_profil(salon=""):
    u = uid(); pr = lire(f"profils/{u}") or {}
    code = pr.get("code") or ""
    if not code or lire(f"codes_amis/{code}") != u:
        code = ""
        for _ in range(8):
            c = "".join(random.choice(ALPHA) for _ in range(6))
            if ok("put", f"codes_amis/{c}", u): code = c; break
    E["code"], E["uid_code"] = code, u
    maj = {"pseudo": pseudo(), "code": code, "vu": SV, "salon": salon or ""}
    if not pr.get("cree"): maj["cree"] = SV
    ok("patch", f"profils/{u}", maj)


def tic(salon=""):
    """Signe de vie (toutes les 30 s) et relève des demandes et invitations (appelé toutes les 10 s, dans un fil)."""
    if not compte.email(): E["code"] = ""; return
    if not compte.auth().jeton(): return
    u = uid()
    if not E["code"] or E["uid_code"] != u: assurer_profil(salon)  # (autre compte : autre code)
    elif E["n"] % 3 == 0: ok("patch", f"profils/{u}", {"pseudo": pseudo(), "vu": SV, "salon": salon or ""})
    E["n"] += 1
    E["demandes"] = lire(f"amis_demandes/{u}") or {}
    inv, now = lire(f"invitations/{u}") or {}, maintenant_ms()
    E["invitations"] = {c: v for c, v in inv.items() if isinstance(v, dict) and now - (v.get("t") or 0) < 10 * 60000}


def ajouter(code_brut):
    """None ou un message d'erreur."""
    code = "".join(c for c in str(code_brut or "").upper() if c.isalnum())
    if len(code) != 6: return "Un code ami fait 6 caractères."
    cible = lire(f"codes_amis/{code}")
    if not cible: return "Aucun joueur avec ce code."
    if cible == uid(): return "C'est ton propre code."
    if cible in E["liste"]: return "Vous êtes déjà amis."
    if cible in E["demandes"]: accepter(cible); return None  # il m'avait déjà demandé : on devient amis
    return None if ok("put", f"amis_demandes/{cible}/{uid()}", {"pseudo": pseudo(), "t": SV}) else "Connexion au serveur impossible. Vérifie ta connexion internet."

def accepter(de):
    u = uid(); ok("put", f"amis/{u}/{de}", True); ok("put", f"amis/{de}/{u}", True); ok("delete", f"amis_demandes/{u}/{de}")
    E["demandes"].pop(de, None); E["liste"][de] = True

def refuser(de): ok("delete", f"amis_demandes/{uid()}/{de}"); E["demandes"].pop(de, None)

def retirer(ami):
    u = uid(); ok("delete", f"amis/{u}/{ami}"); ok("delete", f"amis/{ami}/{u}"); E["liste"].pop(ami, None)

def charger():
    E["liste"] = lire(f"amis/{uid()}") or {}
    for a in list(E["liste"]): E["profils"][a] = lire(f"profils/{a}") or {}
    E["demandes"] = lire(f"amis_demandes/{uid()}") or {}

def statut(p):
    """(texte, état : on | jeu | off, en ligne ?)"""
    p = p or {}; age = maintenant_ms() - (p.get("vu") or 0)
    if age < 75000: return (f"Dans un salon · {p['salon']}", "jeu", True) if p.get("salon") else ("En ligne", "on", True)
    j, h, mn = int(age // 86400000), int(age // 3600000), max(1, int(age // 60000))
    return (f"Hors ligne · il y a {f'{j} j' if j else f'{h} h' if h else f'{mn} min'}" if p.get("vu") else "Hors ligne"), "off", False

def amis_tries():
    return sorted(E["liste"], key=lambda a: not statut(E["profils"].get(a))[2])

def inviter(ami, code): return bool(code) and ok("put", f"invitations/{ami}/{code}", {"de": uid(), "pseudo": pseudo(), "t": SV})
def effacer_invitation(code): ok("delete", f"invitations/{uid()}/{code}")
