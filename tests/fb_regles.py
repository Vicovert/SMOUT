"""Faux serveur Firebase (REST + connexion anonyme) qui APPLIQUE les règles v7 de database.rules.json
(réécrites en Python, mêmes conditions). Journal des refus dans /tmp/fb_refus.log.
Admin : POST /__vieillir?ms=N recule tous les horodatages ; GET /__admin.json lit tout ; POST /__reset vide."""
import json, threading, time, sys, itertools, copy, re
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DATA, LOCK, UIDS = {}, threading.Lock(), itertools.count(1)
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
    if len(p) >= 3 and p[1] == "lobbies":
        return existe(lire(DATA, ["v7", "lobbies", p[2], "players", uid]))
    return False

def regle_ecriture(uid, niveau, D, N):
    """niveau = chemin d'une règle .write ; D = données actuelles, N = nouvelles données (racine complète)."""
    if not uid or niveau[:1] != ["v7"]: return False
    if len(niveau) == 3 and niveau[1] == "index":
        d = lire(D, niveau)
        code = niveau[2]
        return (not existe(d) or d.get("owner") == uid or (d.get("maj") or 0) < maintenant() - 20000
                or lire(D, ["v7", "lobbies", code, "settings", "host_id"]) == uid  # l'hôte actuel (après une reprise d'hôte)
                or (not existe(lire(N, niveau)) and not existe(lire(D, ["v7", "lobbies", code]))))  # annonce d'un salon disparu
    if len(niveau) == 3 and niveau[1] == "secrets":
        code = niveau[2]
        if not re.fullmatch(r"[0-9]{4}", code): return False
        lob = lire(D, ["v7", "lobbies", code])
        return not existe(lob) or (lire(lob, ["settings", "host_id"]) == uid)
    if len(niveau) >= 3 and niveau[1] == "lobbies":
        code = niveau[2]; d_lob = lire(D, ["v7", "lobbies", code]) or {}; n_lob = lire(N, ["v7", "lobbies", code]) or {}
        if len(niveau) == 3:
            if not re.fullmatch(r"[0-9]{4}", code): return False
            if not existe(d_lob) and lire(n_lob, ["settings", "host_id"]) == uid and existe(lire(n_lob, ["players", uid])): return True
            if lire(d_lob, ["settings", "host_id"]) == uid: return True
            if not existe(n_lob) and (not existe(d_lob.get("players")) or (d_lob.get("maj") or 0) < maintenant() - 120000): return True
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
        if len(sous) == 2 and sous[0] in ("match_data", "fini_states"): return uid == sous[1]
        if len(sous) == 3 and sous[0] == "round_wins": return uid == sous[2]
    return False

def valider(N, cible):
    """Règles .validate touchées par l'écriture."""
    if len(cible) >= 3 and cible[1] == "index":
        n = lire(N, cible[:3])
        if existe(n):
            if not re.fullmatch(r"[0-9]{4}", cible[2]) or not all(k in n for k in ("owner", "maj", "version")): return False
            if set(n) - {"owner", "hote", "nb", "prive", "visible", "status", "version", "maj"}: return False
    if len(cible) >= 3 and cible[1] == "lobbies":
        lob = lire(N, cible[:3])
        if existe(lob):
            s = lob.get("settings")
            if s is not None and not all(k in s for k in ("essais", "min", "max", "rounds", "host_id", "timer", "version")): return False
            for pid, p in (lob.get("players") or {}).items():
                if not isinstance(p, dict) or "name" not in p or "score" not in p: return False
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
        return [x for x in u.path.rsplit(".json", 1)[0].split("/") if x], uid
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
        uid = f"uid{next(UIDS):03d}"; EMIS.add("r-" + uid)
        self.rep(200, {"idToken": "tok-" + uid, "refreshToken": "r-" + uid, "localId": uid, "expiresIn": "3600"})
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
