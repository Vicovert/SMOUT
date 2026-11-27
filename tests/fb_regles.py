"""Faux serveur Firebase (REST + connexion anonyme) qui APPLIQUE les règles v7 de database.rules.json
(réécrites en Python, mêmes conditions). Journal des refus dans /tmp/fb_refus.log.
Admin : POST /__vieillir?ms=N recule tous les horodatages ; GET /__admin.json lit tout ; POST /__reset vide."""
import json, threading, time, sys, itertools, copy, re
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

DATA, LOCK, UIDS = {}, threading.Lock(), itertools.count(1)
COMPTES = {}  # comptes e-mail / mot de passe : e-mail -> [mot de passe, uid] (comme Firebase Authentication)
EMIS = set()  # jetons de rafraîchissement émis par CE serveur (comme Firebase : un jeton inconnu est refusé)
JOURNAL = open("/tmp/fb_refus.log", "a")
import os
TRACE = open("/tmp/fb_trace.log", "a") if os.environ.get("FB_TRACE") else None  # FB_TRACE=1 : journal de toutes les requêtes
maintenant = lambda: int(time.time() * 1000)

def resoudre(v):
    if isinstance(v, dict):
        if v == {".sv": "timestamp"}: return maintenant()
        return {k: resoudre(x) for k, x in v.items() if x is not None}
    return v

def lire(racine, parts):
    n = racine
    for k in parts:
        if not isinstance(n, dict) or k not in n: return None
        n = n[k]
    return n

def ecrire(racine, parts, val):
    if not parts: return val
    n = racine
    for k in parts[:-1]:
        if not isinstance(n.get(k), dict): n[k] = {}
        n = n[k]
    if val is None or val == {}: n.pop(parts[-1], None)
    else: n[parts[-1]] = val
    return racine

def nettoyer(n):
    if isinstance(n, dict):
        for k in list(n.keys()):
            nettoyer(n[k])
            if n[k] == {} or n[k] is None: del n[k]

existe = lambda v: v is not None and v != {}

# ---------------------------------------------------------------- règles v7 (traduction de database.rules.json)
def peut_lire(uid, p):
    if not uid: return False
    if p[:1] != ["v7"]: return False
    if p == ["v7", "index"] or (len(p) >= 3 and p[1] == "index"): return True
    if len(p) >= 3 and p[1] == "lobbies":  # joueurs et spectateurs (9.1) ; un spectateur peut toujours lire sa propre fiche
        if len(p) >= 5 and p[3] == "spectateurs" and p[4] == uid: return True
        return existe(lire(DATA, ["v7", "lobbies", p[2], "players", uid])) or existe(lire(DATA, ["v7", "lobbies", p[2], "spectateurs", uid]))
    if len(p) >= 3 and p[1] == "demandes":  # demandes pour regarder une partie en cours : l'hôte les lit toutes, chacun la sienne
        if len(p) >= 4 and p[3] == uid: return True
        return lire(DATA, ["v7", "lobbies", p[2], "settings", "host_id"]) == uid
    if len(p) >= 3 and p[1] == "comptes": return p[2] == uid  # compte : lisible par son seul propriétaire
    if p[1:2] in (["codes_amis"], ["classements"], ["pseudos"]) or (len(p) >= 3 and p[1] == "profils"): return True  # 9.4 : classements publics  # 9.2 : codes amis et profils publics
    if len(p) >= 3 and p[1] in ("amis", "amis_demandes", "invitations"): return p[2] == uid  # 9.2 : sa liste, ses demandes, ses invitations
    if len(p) >= 5 and p[1] == "pieges":  # mot piégé : lisible par les participants de la manche, sauf par celui qui doit le deviner
        return (uid != p[4] and participant(DATA, p[2], uid)) or existe(lire(DATA, ["v7", "lobbies", p[2], "spectateurs", uid]))  # les spectateurs voient tout
    return False

def participant(D, code, uid):
    return lire(D, ["v7", "lobbies", code, "settings", "piege_de", uid]) is not None

def regle_ecriture(uid, niveau, D, N):
    """niveau = chemin d'une règle .write ; D = données actuelles, N = nouvelles données (racine complète)."""
    if not uid or niveau[:1] != ["v7"]: return False
    if len(niveau) == 3 and niveau[1] == "comptes": return niveau[2] == uid  # compte : modifiable par son seul propriétaire
    if len(niveau) == 3 and niveau[1] == "index":
        d = lire(D, niveau)
        code = niveau[2]
        return (not existe(d) or d.get("owner") == uid or (d.get("maj") or 0) < maintenant() - 20000
                or lire(D, ["v7", "lobbies", code, "settings", "host_id"]) == uid  # l'hôte actuel (après une reprise d'hôte)
                or (not existe(lire(N, niveau)) and not existe(lire(D, ["v7", "lobbies", code]))))  # annonce d'un salon disparu
    if len(niveau) == 3 and niveau[1] == "horloge":  # synchronisation de l'horloge : chacun écrit l'heure du serveur sur son propre chemin
        return niveau[2] == uid
    if len(niveau) == 3 and niveau[1] == "secrets":
        code = niveau[2]
        if not re.fullmatch(r"[0-9]{4}", code): return False
        lob = lire(D, ["v7", "lobbies", code])
        return not existe(lob) or (lire(lob, ["settings", "host_id"]) == uid)
    if len(niveau) == 3 and niveau[1] == "codes_amis":  # 9.2 : code ami → joueur (créé ou effacé par son propriétaire)
        d, n = lire(D, niveau), lire(N, niveau)
        return (not existe(d) and n == uid) or (not existe(n) and d == uid)
    if len(niveau) == 3 and niveau[1] == "pseudos":  # 9.14 : pseudo réservé → joueur (pris par un seul, libéré par lui seul)
        d, n = lire(D, niveau), lire(N, niveau)
        return (not existe(d) and n == uid) or (not existe(n) and d == uid) or (d == uid and n == uid)
    if len(niveau) == 3 and niveau[1] == "profils": return niveau[2] == uid
    if len(niveau) == 4 and niveau[1] == "classements" and niveau[2] in ("mdj", "marathon"): return niveau[3] == uid  # 9.4
    if len(niveau) == 4 and niveau[1] == "amis":
        u, a = niveau[2], niveau[3]
        if uid == u: return True
        return uid == a and (not existe(lire(N, niveau)) or existe(lire(D, ["v7", "amis_demandes", a, u])))
    if len(niveau) == 4 and niveau[1] == "amis_demandes":
        cible, de = niveau[2], niveau[3]
        return (uid == de and de != cible) or (uid == cible and not existe(lire(N, niveau)))
    if len(niveau) == 4 and niveau[1] == "invitations":
        cible, code = niveau[2], niveau[3]; d, n = lire(D, niveau), lire(N, niveau)
        if uid == cible and not existe(n): return True
        if existe(n) and (n or {}).get("de") == uid and existe(lire(D, ["v7", "lobbies", code, "players", uid])) and existe(lire(D, ["v7", "amis", cible, uid])): return True
        return not existe(n) and (d or {}).get("de") == uid
    if len(niveau) == 4 and niveau[1] == "demandes":  # 9.1 : demande pour regarder une partie en cours
        code, pid = niveau[2], niveau[3]; d, n = lire(D, niveau), lire(N, niveau)
        if uid == pid:
            if not existe(n): return True
            if not existe(lire(D, ["v7", "lobbies", code, "settings"])): return False
            sec = lire(D, ["v7", "secrets", code])
            return existe(d) or sec is None or (n or {}).get("preuve") == sec
        return not existe(n) and lire(D, ["v7", "lobbies", code, "settings", "host_id"]) == uid
    if len(niveau) == 3 and niveau[1] == "pieges":  # nettoyage des mots d'un salon disparu
        return not existe(lire(N, niveau)) and not existe(lire(D, ["v7", "lobbies", niveau[2]]))
    if len(niveau) == 5 and niveau[1] == "pieges":
        code, pid, cible = niveau[2], niveau[3], niveau[4]
        reg = lire(D, ["v7", "lobbies", code, "settings"]) or {}
        if existe(lire(D, niveau)) or uid == cible or pid != reg.get("piege_id"): return False
        if uid == (reg.get("piege_de") or {}).get(cible): return True
        fin = reg.get("piege_fin_choix")
        return participant(D, code, uid) and isinstance(fin, (int, float)) and maintenant() > fin
    if len(niveau) >= 3 and niveau[1] == "lobbies":
        code = niveau[2]; d_lob = lire(D, ["v7", "lobbies", code]) or {}; n_lob = lire(N, ["v7", "lobbies", code]) or {}
        if len(niveau) == 3:
            if not re.fullmatch(r"[0-9]{4}", code): return False
            if not existe(d_lob) and lire(n_lob, ["settings", "host_id"]) == uid and existe(lire(n_lob, ["players", uid])): return True
            if lire(d_lob, ["settings", "host_id"]) == uid: return True
            if not existe(n_lob) and (not existe(d_lob.get("players")) or (d_lob.get("maj") or 0) < maintenant() - 1800000): return True
            return False
        sous = niveau[3:]
        if sous == ["maj"]: return existe(lire(d_lob, ["players", uid]))
        if sous == ["settings", "host_id"]:
            nv, av = lire(n_lob, ["settings", "host_id"]), lire(d_lob, ["settings", "host_id"])
            if nv != uid or not existe(lire(d_lob, ["players", uid])): return False
            ancien = lire(d_lob, ["players", av]) if av else None
            return not existe(ancien) or (ancien.get("last_seen") or 0) < maintenant() - 15000
        if len(sous) == 2 and sous[0] == "players":
            pid = sous[1]; d, n = lire(d_lob, ["players", pid]), lire(n_lob, ["players", pid])
            if uid == pid:
                if existe(d) or not existe(n): return True
                if not existe(d_lob.get("settings")): return False
                sec = lire(D, ["v7", "secrets", code])
                return sec is None or (n or {}).get("preuve") == sec
            return not existe(n) and existe(d) and (d.get("last_seen") or 0) < maintenant() - 25000
        if len(sous) == 2 and sous[0] == "spectateurs":  # 9.1 : spectateurs (entrée libre seulement dans le salon, avant la partie)
            pid = sous[1]; d, n = lire(d_lob, ["spectateurs", pid]), lire(n_lob, ["spectateurs", pid])
            if uid == pid:
                if existe(d) or not existe(n): return True
                if d_lob.get("status") != "waiting" and not existe(lire(D, ["v7", "invitations", pid, code])): return False  # 9.2 : invité par un ami
                sec = lire(D, ["v7", "secrets", code])
                return sec is None or (n or {}).get("preuve") == sec
            return not existe(n) and existe(d) and (d.get("last_seen") or 0) < maintenant() - 25000
        if len(sous) == 2 and sous[0] in ("match_data", "fini_states"): return uid == sous[1]
        if len(sous) == 3 and sous[0] == "round_wins": return uid == sous[2]
        if len(sous) == 2 and sous[0] == "piege_pret": return uid != sous[1] and participant(D, code, uid)
        if len(sous) == 3 and sous[0] == "piege_essais": return uid == sous[1] and not existe(lire(d_lob, sous))
        if len(sous) == 3 and sous[0] == "piege_verdicts": return uid != sous[1] and not existe(lire(d_lob, sous)) and participant(D, code, uid)
        if len(sous) == 3 and sous[0] == "piege_recap": return uid != sous[2] and not existe(lire(d_lob, sous)) and participant(D, code, uid)
    return False

def valider(N, cible):
    """Règles .validate touchées par l'écriture."""
    if len(cible) >= 3 and cible[1] == "pseudos":  # 9.14
        n = lire(N, cible[:3])
        if existe(n) and not (isinstance(n, str) and len(cible[2]) <= 10): return False
    if len(cible) >= 3 and cible[1] == "horloge" and not isinstance(lire(N, cible[:3]), (int, float)): return False
    if len(cible) >= 3 and cible[1] == "index":
        n = lire(N, cible[:3])
        if existe(n):
            if not re.fullmatch(r"[0-9]{4}", cible[2]) or not all(k in n for k in ("owner", "maj", "version")): return False
            if set(n) - {"owner", "hote", "nb", "prive", "visible", "status", "version", "maj"}: return False
            if "nb" in n and not (isinstance(n["nb"], (int, float)) and 0 <= n["nb"] <= 8): return False  # 8 joueurs au plus (database.rules.json)
    if len(cible) >= 3 and cible[1] == "lobbies":
        lob = lire(N, cible[:3])
        if existe(lob):
            s = lob.get("settings")
            if s is not None and not all(k in s for k in ("essais", "min", "max", "rounds", "host_id", "timer", "version")): return False
            for pid, p in (lob.get("players") or {}).items():
                if not isinstance(p, dict) or "name" not in p or "score" not in p: return False
                if "frappe" in p and not (isinstance(p["frappe"], str) and len(p["frappe"]) <= 12): return False  # frappe en direct (Mot piégé)
                if "theme" in p and not (isinstance(p["theme"], dict) and all(isinstance(c, str) and len(c) <= 9 for c in p["theme"].values())): return False  # couleurs du thème du joueur
            for pid, sp in (lob.get("spectateurs") or {}).items():
                if not isinstance(sp, dict) or not isinstance(sp.get("name"), str) or len(sp["name"]) > 30: return False
            for t, c in ((s or {}).get("piege_de") or {}).items():
                if not isinstance(c, str) or c == t: return False
            sous = cible[3:]
            v = lire(lob, sous) if sous else None
            if sous[:1] == ["piege_pret"] and len(sous) >= 2 and existe(lire(lob, sous[:2])) and not all(k in lire(lob, sous[:2]) for k in ("n", "p")): return False
            if sous[:1] == ["piege_essais"] and len(sous) == 3 and v is not None and not (isinstance(v, str) and re.fullmatch(r"[A-Z]+", v)): return False
            if sous[:1] == ["piege_verdicts"] and len(sous) == 3 and v is not None and not (isinstance(v, str) and re.fullmatch(r"[BMA]+", v)): return False
            if sous[:1] == ["piege_recap"] and len(sous) >= 3 and existe(lire(lob, sous[:3])) and not all(k in lire(lob, sous[:3]) for k in ("de", "mot")): return False
    if len(cible) >= 4 and cible[1] == "demandes":
        n = lire(N, cible[:4])
        if existe(n):
            if not isinstance(n, dict) or set(n) - {"name", "t", "preuve"} or not isinstance(n.get("name"), str) or len(n["name"]) > 30: return False
            if not isinstance(n.get("t"), (int, float)) or n["t"] > maintenant() + 5000: return False
    if len(cible) >= 3 and cible[1] == "codes_amis":
        n = lire(N, cible[:3])
        if existe(n) and (not re.fullmatch(r"[A-Z2-9]{6}", cible[2]) or not isinstance(n, str)): return False
    if len(cible) >= 3 and cible[1] == "profils":
        n = lire(N, cible[:3])
        if existe(n):
            if not isinstance(n, dict) or set(n) - {"pseudo", "code", "vu", "salon", "cree"}: return False
            if "pseudo" in n and not (isinstance(n["pseudo"], str) and len(n["pseudo"]) <= 30): return False
            if "vu" in n and not (isinstance(n["vu"], (int, float)) and n["vu"] <= maintenant() + 5000): return False
            if "salon" in n and not (isinstance(n["salon"], str) and len(n["salon"]) <= 4): return False
    if len(cible) >= 4 and cible[1] == "classements":  # 9.4
        n, d = lire(N, cible[:4]), lire(D := DATA, cible[:4])
        if existe(n):
            cles = {"mdj": ({"pseudo", "meilleure", "maj"}, {"actuelle", "jour", "essais", "moyenne", "trouves"}), "marathon": ({"pseudo", "record", "maj"}, {"score", "mots", "essais", "lmin", "lmax", "difficile"})}.get(cible[2])
            if not cles or not isinstance(n, dict) or not cles[0] <= set(n) or set(n) - cles[0] - cles[1]: return False
            if not isinstance(n["pseudo"], str) or len(n["pseudo"]) > 30 or not isinstance(n["maj"], (int, float)) or n["maj"] > maintenant() + 5000: return False
            if cible[2] == "marathon" and not (isinstance(n["record"], (int, float)) and 0 <= n["record"] <= 500): return False
            if cible[2] == "marathon" and "score" in n and not (isinstance(n["score"], (int, float)) and 0 <= n["score"] <= 10000000): return False  # 9.7
            if cible[2] == "marathon":  # 9.10 : mots et réglages de la meilleure partie
                for k, (a, b) in {"mots": (0, 500), "essais": (4, 8), "lmin": (6, 10), "lmax": (6, 10)}.items():
                    if k in n and not (isinstance(n[k], (int, float)) and not isinstance(n[k], bool) and a <= n[k] <= b): return False
                if "difficile" in n and not isinstance(n["difficile"], bool): return False
            if cible[2] == "mdj":
                m = n["meilleure"]
                if not isinstance(m, (int, float)) or m < 0: return False
                if existe(d): 
                    if m > d.get("meilleure", 0) + 1 + (maintenant() - (d.get("maj") or 0)) / 86400000: return False
                elif m > 365: return False
                if "actuelle" in n and not (isinstance(n["actuelle"], (int, float)) and 0 <= n["actuelle"] <= m): return False
                if "jour" in n and not (isinstance(n["jour"], str) and len(n["jour"]) <= 10): return False  # 9.6
                if "essais" in n and not (isinstance(n["essais"], (int, float)) and 0 <= n["essais"] <= 8): return False
                if "moyenne" in n and not (isinstance(n["moyenne"], (int, float)) and 1 <= n["moyenne"] <= 8): return False  # 9.8
                if "trouves" in n and not (isinstance(n["trouves"], (int, float)) and 0 <= n["trouves"] <= 100000): return False  # 9.11
    if len(cible) >= 4 and cible[1] == "amis":
        n = lire(N, cible[:4])
        if existe(n) and (n is not True or cible[2] == cible[3]): return False
    if len(cible) >= 4 and cible[1] in ("amis_demandes", "invitations"):
        n = lire(N, cible[:4])
        if existe(n):
            cles = {"pseudo", "t"} if cible[1] == "amis_demandes" else {"de", "pseudo", "t"}
            if not isinstance(n, dict) or set(n) != cles or not isinstance(n.get("pseudo"), str) or len(n["pseudo"]) > 30: return False
            if not isinstance(n.get("t"), (int, float)) or n["t"] > maintenant() + 5000: return False
    if len(cible) >= 3 and cible[1] == "comptes":
        n = lire(N, cible[:3])
        if existe(n) and not (isinstance(n, dict) and "maj" in n and isinstance(n.get("donnees"), str)): return False
    if len(cible) >= 5 and cible[1] == "pieges":
        n = lire(N, cible[:5])
        if existe(n):
            reg = lire(N, ["v7", "lobbies", cible[2], "settings"]) or {}
            if not isinstance(n, dict) or set(n) - {"mot", "de", "auto"} or "mot" not in n or "de" not in n: return False
            m = n["mot"]
            if not isinstance(m, str) or not re.fullmatch(r"[A-Z]+", m) or not isinstance(n["de"], str): return False
            if not (reg.get("min", 0) <= len(m) <= reg.get("max", 0)): return False
            if "auto" in n and not isinstance(n["auto"], bool): return False
    return True

def autorise(uid, ecritures):
    """ecritures = [(chemin, valeur)] appliquées ensemble (PATCH multi-chemins)."""
    N = copy.deepcopy(DATA)
    for p, v in ecritures: ecrire(N, p, resoudre(v))
    nettoyer(N)
    for p, v in ecritures:
        if not any(regle_ecriture(uid, p[:i], DATA, N) for i in range(1, len(p) + 1)): return None, p
        if not valider(N, p): return None, p
    return N, None

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def rep(self, code, obj):
        if TRACE and self.command != "OPTIONS":
            TRACE.write(f"{time.strftime('%H:%M:%S')}.{int(time.time()*1000)%1000:03d} {code} {self.command} {urlparse(self.path).path} {json.dumps(obj)[:120]}\n"); TRACE.flush()
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def corps(self):
        n = int(self.headers.get("Content-Length") or 0); return self.rfile.read(n).decode() if n else ""
    def chemin(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        tok = (q.get("auth") or [""])[0]
        uid = tok[4:] if tok.startswith("tok-") else None
        return [unquote(x) for x in u.path.rsplit(".json", 1)[0].split("/") if x], uid  # (comme Firebase : clés décodées)
    def refus(self, m, p, uid):
        JOURNAL.write(f"{time.strftime('%H:%M:%S')} REFUS {m} /{'/'.join(p)} uid={uid}\n"); JOURNAL.flush(); self.rep(401, {"error": "Permission denied"})
    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Methods", "*"); self.send_header("Access-Control-Allow-Headers", "*"); self.end_headers()
    def do_POST(self):
        global DATA
        b = self.corps(); u = urlparse(self.path)
        if u.path == "/__vieillir":
            ms = int(parse_qs(u.query)["ms"][0])
            def v(n):
                if isinstance(n, dict):
                    for k, x in n.items():
                        if k in ("maj", "last_seen") and isinstance(x, (int, float)): n[k] = x - ms
                        else: v(x)
            with LOCK: v(DATA)
            return self.rep(200, True)
        if u.path == "/__supprimer":  # admin : retire un nœud (ex. joueur exclu)
            ch = [x for x in parse_qs(u.query)["chemin"][0].split("/") if x]
            with LOCK:
                n = DATA
                for k in ch[:-1]: n = n.get(k, {})
                n.pop(ch[-1], None)
            return self.rep(200, True)
        if u.path == "/__reset":
            with LOCK: DATA = {}
            return self.rep(200, True)
        if "token" in self.path:  # renouvellement : même joueur (comme Firebase), à partir du jeton de rafraîchissement
            ancien = (parse_qs(b).get("refresh_token") or [""])[0]
            if ancien in EMIS: uid = ancien[2:]; return self.rep(200, {"id_token": "tok-" + uid, "refresh_token": ancien, "user_id": uid, "expires_in": "3600"})
            return self.rep(400, {"error": "INVALID_REFRESH_TOKEN"})
        try: corps = json.loads(b or "{}")
        except ValueError: corps = {}
        err = lambda m: self.rep(400, {"error": {"code": 400, "message": m}})
        jeton = lambda uid, **x: self.rep(200, dict({"idToken": "tok-" + uid, "refreshToken": "r-" + uid, "localId": uid, "expiresIn": "3600"}, **x))
        email = str(corps.get("email") or "").strip().lower()
        if corps.get("requestType") == "PASSWORD_RESET":  # mot de passe oublié (Firebase répond 200 même si l'adresse est inconnue)
            return self.rep(200, {"email": email}) if "@" in email else err("INVALID_EMAIL")
        if (parse_qs(u.query).get("op") or [""])[0] == "update" and corps.get("email"):  # comme le vrai projet (protection contre l'énumération des e-mails)
            return err("OPERATION_NOT_ALLOWED : Please verify the new email before changing email.")
        if corps.get("idToken") and "password" in corps:  # création du compte = rattachement du joueur anonyme (même uid)
            uid = str(corps["idToken"])[4:]
            if "@" not in email or "." not in email.split("@")[-1]: return err("INVALID_EMAIL")
            if len(str(corps["password"])) < 6: return err("WEAK_PASSWORD : Password should be at least 6 characters")
            if email in COMPTES and COMPTES[email][1] != uid: return err("EMAIL_EXISTS")
            COMPTES[email] = [str(corps["password"]), uid]; EMIS.add("r-" + uid)
            return jeton(uid, email=email)
        if "password" in corps:  # connexion à un compte existant
            c = COMPTES.get(email)
            if "@" not in email: return err("INVALID_EMAIL")
            if not c or c[0] != str(corps["password"]): return err("INVALID_LOGIN_CREDENTIALS")
            EMIS.add("r-" + c[1]); return jeton(c[1], email=email, registered=True)
        uid = f"uid{next(UIDS):03d}"; EMIS.add("r-" + uid)
        jeton(uid)
    def do_GET(self):
        p, uid = self.chemin()
        if p[:1] == ["__admin"] or (not p and not uid):
            with LOCK: return self.rep(200, copy.deepcopy(DATA))
        if not peut_lire(uid, p): return self.refus("GET", p, uid)
        with LOCK: self.rep(200, copy.deepcopy(lire(DATA, p)))
    def ecrire_req(self, m, ecritures, p, uid, reponse):
        global DATA
        with LOCK:
            N, bloque = autorise(uid, ecritures)
            if N is None: return self.refus(m, bloque, uid)
            DATA = N; self.rep(200, reponse)
    def do_PUT(self):
        p, uid = self.chemin(); v = json.loads(self.corps() or "null"); self.ecrire_req("PUT", [(p, v)], p, uid, resoudre(v))
    def do_PATCH(self):
        p, uid = self.chemin(); v = json.loads(self.corps() or "{}")
        self.ecrire_req("PATCH", [(p + [x for x in k.split("/") if x], x2) for k, x2 in v.items()], p, uid, resoudre(v))
    def do_DELETE(self):
        p, uid = self.chemin(); self.ecrire_req("DELETE", [(p, None)], p, uid, None)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
