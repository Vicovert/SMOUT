"""Compte SMOUT (e-mail + mot de passe, Firebase Authentication) : le même joueur et le même avancement sur tous les appareils.

- Sans compte, chaque appareil a son joueur anonyme Firebase (gardé d'un lancement à l'autre).
- « Créer un compte » rattache ce joueur anonyme à l'e-mail : même identifiant, rien n'est perdu.
- « Se connecter » sur un autre appareil reprend ce joueur et son avancement (le compte remplace les données de l'appareil).
- L'avancement (CLES_SYNCHRO) est copié sous /v7/comptes/<uid>, lisible et modifiable par son seul propriétaire,
  envoyé après chaque changement et relu au démarrage. On reste connecté tant qu'on ne se déconnecte pas.
Même logique que l'objet Compte de web/smout.js."""
import json, threading, time, traceback
import requests
import design

FIREBASE_URL = "https://smout-multi-default-rtdb.europe-west1.firebasedatabase.app/"
FIREBASE_API_KEY = "AIzaSyCUliQiMhKmHZzxrMK6k35Gt0z7zBfZP3g"  # clé web publique (normal qu'elle soit dans le client)
RACINE = "v7"
IDENTITE = "https://identitytoolkit.googleapis.com/v1/accounts:"
# avancement suivi d'un appareil à l'autre (mêmes clés que la configuration du site)
CLES_SYNCHRO = ("pseudo", "theme", "custom_themes", "daltonien", "user_zoom", "nb_essais", "nb_lettres_min", "nb_lettres_max", "difficile",
                "stats", "last_mdj", "mdj_serie", "mdj_dernier_gagne", "mdj_en_cours", "partie_en_cours")
ERREURS = {
    "EMAIL_EXISTS": "Cette adresse a déjà un compte : utilise « Se connecter ».",
    "INVALID_EMAIL": "Adresse e-mail invalide.",
    "MISSING_PASSWORD": "Entre un mot de passe.",
    "WEAK_PASSWORD": "Mot de passe trop court (6 caractères minimum).",
    "INVALID_LOGIN_CREDENTIALS": "E-mail ou mot de passe incorrect.",
    "INVALID_PASSWORD": "E-mail ou mot de passe incorrect.",
    "EMAIL_NOT_FOUND": "E-mail ou mot de passe incorrect.",
    "USER_DISABLED": "Ce compte est désactivé.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Trop d'essais : réessaie dans quelques minutes.",
    "OPERATION_NOT_ALLOWED": "Les comptes ne sont pas encore activés sur le serveur.",
    "CREDENTIAL_TOO_OLD_LOGIN_AGAIN": "Reconnecte-toi puis réessaie.",
}

_SESSION = None
def session():
    global _SESSION
    if _SESSION is None: _SESSION = requests.Session()  # créée au premier usage (les tests remplacent requests.Session avant)
    return _SESSION

def message_erreur(r):
    """Message en français pour une réponse d'erreur de Firebase Authentication."""
    try: code = str(r.json()["error"]["message"]).split(" ")[0]
    except Exception: return "Connexion au serveur impossible. Vérifie ta connexion internet."
    return ERREURS.get(code, "Erreur du serveur : " + code)


class AuthFirebase:
    """Connexion Firebase (joueur anonyme ou compte e-mail) : jeton renouvelé automatiquement, gardé d'un lancement à l'autre."""
    def __init__(self, sess=None):
        self.session, self.lock = sess or session(), threading.Lock()
        self.uid = self.id_token = None
        self.refresh_token = design.lire_config().get("auth_refresh")  # même joueur d'un lancement à l'autre (reprise de partie)
        self.expire = 0

    def _appliquer(self, id_token, refresh_token, uid, expires_in):
        if refresh_token != self.refresh_token: design.maj_config(auth_refresh=refresh_token)
        self.id_token, self.refresh_token, self.uid = id_token, refresh_token, uid
        self.expire = time.time() + int(expires_in)

    def oublier(self):
        with self.lock: self.uid = self.id_token = self.refresh_token = None; self.expire = 0

    def jeton(self):
        with self.lock:
            rt = design.lire_config().get("auth_refresh")
            if rt != self.refresh_token:  # connexion / déconnexion faite ailleurs (page Compte) : on suit
                self.refresh_token, self.id_token, self.expire = rt, None, 0
            if self.id_token and time.time() < self.expire - 120: return self.id_token
            try:
                if self.refresh_token:
                    r = self.session.post(f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}",
                                          data={"grant_type": "refresh_token", "refresh_token": self.refresh_token}, timeout=5)
                    if r.status_code == 200:
                        d = r.json(); self._appliquer(d["id_token"], d["refresh_token"], d["user_id"], d["expires_in"])
                        return self.id_token
                    if design.lire_config().get("compte_email"):  # session du compte refusée (mot de passe changé…) : on se déconnecte
                        design.maj_config(compte_email=None, compte_sync=None, compte_expire=True)
                r = self.session.post(f"{IDENTITE}signUp?key={FIREBASE_API_KEY}", json={"returnSecureToken": True}, timeout=5)
                if r.status_code == 200:
                    d = r.json(); self._appliquer(d["idToken"], d["refreshToken"], d["localId"], d["expiresIn"])
            except Exception: traceback.print_exc()
            return self.id_token


_AUTH = None
def auth():
    global _AUTH
    if _AUTH is None: _AUTH = AuthFirebase()
    return _AUTH

def email(): return design.lire_config().get("compte_email")

def _identite(op, corps):
    return session().post(f"{IDENTITE}{op}?key={FIREBASE_API_KEY}", json=corps, timeout=8)

def creer(adresse, mdp):
    """Crée le compte en y rattachant le joueur de cet appareil (même identifiant, avancement conservé). Renvoie None ou un message d'erreur."""
    adresse = (adresse or "").strip().lower()
    try:
        jeton = auth().jeton()
        if not jeton: return "Connexion au serveur impossible. Vérifie ta connexion internet."
        r = _identite("update", {"idToken": jeton, "email": adresse, "password": mdp or "", "returnSecureToken": True})
        if r.status_code != 200: return message_erreur(r)
        d = r.json()
        if d.get("idToken"): auth()._appliquer(d["idToken"], d["refreshToken"], d["localId"], d.get("expiresIn", 3600))
        design.maj_config(compte_email=adresse, compte_expire=None)
        pousser()
        return None
    except Exception:
        traceback.print_exc(); return "Connexion au serveur impossible. Vérifie ta connexion internet."

def connecter(adresse, mdp):
    """Connexion à un compte existant : l'avancement du compte remplace celui de cet appareil
    (s'il n'en a pas encore, c'est celui de l'appareil qui est envoyé). Renvoie None ou un message d'erreur."""
    adresse = (adresse or "").strip().lower()
    try:
        r = _identite("signInWithPassword", {"email": adresse, "password": mdp or "", "returnSecureToken": True})
        if r.status_code != 200: return message_erreur(r)
        d = r.json()
        auth()._appliquer(d["idToken"], d["refreshToken"], d["localId"], d.get("expiresIn", 3600))
        design.maj_config(compte_email=adresse, compte_sync=None, compte_expire=None)
        if not tirer(): pousser()
        return None
    except Exception:
        traceback.print_exc(); return "Connexion au serveur impossible. Vérifie ta connexion internet."

def reinitialiser(adresse):
    """Envoie l'e-mail de réinitialisation du mot de passe. Renvoie None ou un message d'erreur."""
    try:
        r = _identite("sendOobCode", {"requestType": "PASSWORD_RESET", "email": (adresse or "").strip().lower()})
        return None if r.status_code == 200 else message_erreur(r)
    except Exception:
        return "Connexion au serveur impossible. Vérifie ta connexion internet."

def deconnecter():
    """Quitte le compte sur cet appareil : l'avancement local reste, un nouveau joueur anonyme sera créé au besoin."""
    design.maj_config(compte_email=None, compte_sync=None, auth_refresh=None)
    auth().oublier()

def _db(methode, chemin, donnees=None):
    jeton = auth().jeton()
    if not jeton or not auth().uid: return None
    kw = {"params": {"auth": jeton}, "timeout": 6}
    if donnees is not None: kw["json"] = donnees
    r = getattr(session(), methode)(f"{FIREBASE_URL}{RACINE}/comptes/{auth().uid}{chemin}.json", **kw)
    return r.json() if r.status_code == 200 else None

def pousser():
    """Envoie l'avancement de cet appareil vers le compte."""
    if not email(): return False
    cfg = design.lire_config()
    donnees = {k: cfg[k] for k in CLES_SYNCHRO if k in cfg}
    try:
        if _db("put", "", {"maj": {".sv": "timestamp"}, "donnees": json.dumps(donnees)}) is None: return False
        maj = _db("get", "/maj")
        if isinstance(maj, (int, float)): design.maj_config(compte_sync=maj)
        return True
    except Exception:
        traceback.print_exc(); return False

def tirer():
    """Relit l'avancement du compte ; s'il est plus récent que la dernière synchronisation, il remplace celui de l'appareil.
    Renvoie True si des données ont été appliquées."""
    if not email(): return False
    try:
        d = _db("get", "")
        if not isinstance(d, dict) or not isinstance(d.get("maj"), (int, float)): return False
        if d["maj"] <= (design.lire_config().get("compte_sync") or 0): return False
        donnees = json.loads(d.get("donnees") or "{}")
        maj = {k: donnees.get(k) for k in CLES_SYNCHRO}  # une clé absente du compte est effacée sur l'appareil
        maj["compte_sync"] = d["maj"]
        _ENVOI["bloque"] = True
        try: design.maj_config(**maj)
        finally: _ENVOI["bloque"] = False
        return True
    except Exception:
        traceback.print_exc(); return False


# envoi automatique après chaque changement de l'avancement (regroupé : au plus un envoi toutes les 2 s)
_ENVOI = {"minuteur": None, "bloque": False}
def _apres_maj(cles):
    if _ENVOI["bloque"] or not email() or not (set(cles) & set(CLES_SYNCHRO)): return
    if _ENVOI["minuteur"] is None:
        def envoyer():
            _ENVOI["minuteur"] = None; pousser()
        t = threading.Timer(2.0, envoyer); t.daemon = True; _ENVOI["minuteur"] = t; t.start()
design.APRES_MAJ_CONFIG.append(_apres_maj)
