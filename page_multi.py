import tkinter as tk
from tkinter import messagebox as tkm
import json, random, os, sys, time, requests, threading, webbrowser, queue, traceback, hashlib
import design

# --- CONFIGURATION DYNAMIQUE ---
FIREBASE_URL = "https://smout-multi-default-rtdb.europe-west1.firebasedatabase.app/"
FIREBASE_API_KEY = "AIzaSyCUliQiMhKmHZzxrMK6k35Gt0z7zBfZP3g"  # clé web publique (normal qu'elle soit dans le client)
RACINE = "v7"            # données du protocole 7 (PC et web) ; /v5 reste pour les 5.x/6.x
VERSION_JEU = "7.0"      # version du protocole multi : seuls les joueurs 7.x jouent ensemble (PC et navigateur)
DELAI_ABANDON_MS = 120000  # un salon dont plus personne ne donne signe de vie depuis 2 min peut être supprimé par n'importe qui

def preuve_salon(code, mot_de_passe):
    """Preuve de connaissance du mot de passe (le mot de passe lui-même n'est jamais envoyé)."""
    if not mot_de_passe: return None
    return hashlib.sha256(f"{code}:{mot_de_passe}".encode("utf-8")).hexdigest()[:32]

mot_graine = design.mot_graine

class AuthFirebase:
    """Connexion anonyme Firebase (jeton renouvelé automatiquement, sans compte à créer)."""
    def __init__(self, session):
        self.session, self.lock = session, threading.Lock()
        self.uid = self.id_token = self.refresh_token = None
        self.expire = 0

    def _appliquer(self, id_token, refresh_token, uid, expires_in):
        self.id_token, self.refresh_token, self.uid = id_token, refresh_token, uid
        self.expire = time.time() + int(expires_in)

    def jeton(self):
        with self.lock:
            if self.id_token and time.time() < self.expire - 120: return self.id_token
            try:
                if self.refresh_token:
                    r = self.session.post(f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}",
                                          data={"grant_type": "refresh_token", "refresh_token": self.refresh_token}, timeout=5)
                    if r.status_code == 200:
                        d = r.json(); self._appliquer(d["id_token"], d["refresh_token"], d["user_id"], d["expires_in"])
                        return self.id_token
                r = self.session.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}",
                                      json={"returnSecureToken": True}, timeout=5)
                if r.status_code == 200:
                    d = r.json(); self._appliquer(d["idToken"], d["refreshToken"], d["localId"], d["expiresIn"])
            except Exception: traceback.print_exc()
            return self.id_token



# ===================================================================== thème
import design
from design import (P, police, etiquette, espacer, Tuile, Bouton, Panneau, Icone, Avatar, Clavier, Stat, Chips, CarteChoix,
                    Champ, Interrupteur, Superposition, Stepper, CarteSalon, Defilant, arrondi, melanger, fenetre_aide)

BG = ACCENT1 = ACCENT2 = MUTED = KEY_BG = TXT1 = None
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

MODES = [
    ("CLASSIQUE", "Classique", "1 point par mot trouvé"),
    ("BLAST", "Blast", "Les plus rapides marquent"),
    ("PRECISION", "Précision", "Moins d'essais, + de points"),
    ("MYSTERE", "Mystère", "1re lettre cachée"),
    ("RUSH", "Rush", "Max de mots avant la fin"),
]
NOM_MODE = {m: n for m, n, _ in MODES}

def apply_theme_multi(theme_data):
    """Met à jour les couleurs globales du jeu"""
    global BG, ACCENT1, ACCENT2, MUTED, KEY_BG, TXT1
    if not P: design.appliquer_theme(theme_data)
    BG, ACCENT1, ACCENT2, MUTED, KEY_BG, TXT1 = P["fond"], P["bien"], P["mal"], P["absent"], P["tuile"], P["texte"]

def resource_path(relative_path):
    return design.resource_path(relative_path)

def get_txt_color(hex_color):
    return design.contraste(hex_color, "white", "#1a1a1a")

def en_codes(couleurs):
    """Couleurs locales -> états neutres envoyés aux autres joueurs (B = bien placé, M = mal placé, A = absent)."""
    return ["B" if c == ACCENT1 else "M" if c == ACCENT2 else "A" for c in couleurs]

def couleur_code(code):
    """État reçu -> couleur du thème de CE joueur."""
    return {"B": ACCENT1, "M": ACCENT2, "A": MUTED}.get(code, MUTED)

def nombre(n):
    return f"{int(n):,}".replace(",", " ")

def mm_ss(v):
    m, s = divmod(int(v), 60); return f"{m:02d}:{s:02d}"


class PageMulti(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        self.session = requests.Session() 
        self.auth = AuthFirebase(self.session)
        self.player_id = ""   # = identifiant Firebase, connu une fois connecté
        self.code_affiche = ""  # code à 4 chiffres montré aux joueurs (lobby_code = adresse réelle du salon)
        self.nb_joueurs, self.statut_salon = 1, "waiting"
        threading.Thread(target=self.assurer_connexion, daemon=True).start()
        self.pseudo = self.charger_pseudo_local()
        self.lobby_code, self.is_host, self.current_score = "", False, 0
        self.server_time_offset = 0 # Pour ajuster l'horloge
        self.settings_config = {"essais": 8, "min": 6, "max": 7, "round_num": 1, "timer": 180, "password": "", "visible": True, "game_mode": "CLASSIQUE"}
        self.charger_mots()
        self.dernier_mot = ""
        self.container = tk.Frame(self, bg=P["fond"])
        self.container.pack(side="left", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1); self.container.grid_columnconfigure(0, weight=1)
        self.frames = {F.__name__: F(parent=self.container, controller=self) for F in (PageAccueil, PageHostSetup, PageLobby, PageJeu, PageScoreFinal)}
        for f in self.frames.values(): f.grid(row=0, column=0, sticky="nsew")
        self.reponses_reseau = queue.Queue(); self.pomper_reponses()
        self.show_frame("PageAccueil"); self.controller.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.on_closing)
        self.heartbeat_active = True; self.start_heartbeat()

    def fb_get_async(self, path, callback):
        """Lit Firebase dans un thread puis appelle callback(data) dans le thread de l'interface (pas de gel de la fenêtre)."""
        def worker(): self.reponses_reseau.put((callback, self.fb_get(path)))
        threading.Thread(target=worker, daemon=True).start()

    def pomper_reponses(self):
        try:
            while True:
                callback, data = self.reponses_reseau.get_nowait()
                try: callback(data)
                except Exception: traceback.print_exc()
        except queue.Empty: pass
        self.after(50, self.pomper_reponses)

    def assurer_connexion(self):
        """Renvoie True si on est connecté à Firebase (connexion anonyme)."""
        if self.auth.jeton():
            self.player_id = self.auth.uid
            return True
        return False

    def start_heartbeat(self):
        if self.heartbeat_active and self.lobby_code:
            # signe de vie du joueur ET du salon (un salon sans signe de vie depuis 2 min est supprimable)
            uid = self.player_id
            self.fb_patch(f"lobbies/{self.lobby_code}", {"maj": {".sv": "timestamp"}, f"players/{uid}/last_seen": {".sv": "timestamp"},
                                                         f"players/{uid}/name": self.pseudo, f"players/{uid}/score": self.current_score})
            if self.is_host: self.maj_index()
        if self.heartbeat_active: self.after(5000, self.start_heartbeat)

    def maj_index(self):
        """Annonce le salon dans l'index (liste publique légère, sans mot de passe ni données de jeu)."""
        if not self.code_affiche: return
        sc = self.settings_config
        self.fb_patch(f"index/{self.code_affiche}", {"owner": self.player_id, "hote": self.pseudo[:20], "nb": self.nb_joueurs,
                      "prive": bool(sc.get("password")), "visible": bool(sc.get("visible", True)), "status": self.statut_salon,
                      "version": VERSION_JEU, "maj": {".sv": "timestamp"}})

    def on_closing(self):
        self.heartbeat_active = False; self.quitter_lobby_logic(True); self.controller.winfo_toplevel().destroy()

    def quitter_lobby_logic(self, exit_mode=False):
        if not self.lobby_code: return
        code_to_clean, self.lobby_code = self.lobby_code, ""
        code_index, self.code_affiche = self.code_affiche, ""
        def do_clean():
            try:
                data = self._requete("get", f"lobbies/{code_to_clean}")
                if data:
                    players = data.get("players", {})
                    hote = data.get("settings", {}).get("host_id") == self.player_id
                    if hote and len(players) > 1:  # on passe la main avant de partir
                        nouvel = sorted(pid for pid in players if pid != self.player_id)[0]
                        self._requete("patch", f"lobbies/{code_to_clean}/settings", {"host_id": nouvel})
                        self._requete("patch", f"index/{code_index}", {"owner": nouvel})
                    if self.player_id in players:
                        self._requete("delete", f"lobbies/{code_to_clean}/players/{self.player_id}")
                        del players[self.player_id]
                    if not players:  # dernier joueur : le salon vide est supprimé
                        self.supprimer_salon(code_to_clean)
            except Exception: traceback.print_exc()
        t = threading.Thread(target=do_clean); t.start()
        if exit_mode: t.join(1.0)

    def fb_ok(self, method, path, data=None, timeout=3):
        """Écriture/suppression synchrone : True si la base l'a acceptée."""
        try:
            jeton = self.auth.jeton()
            if not jeton: return False
            kw = {"params": {"auth": jeton}, "timeout": timeout}
            if method in ("put", "patch"): kw["json"] = data
            return getattr(self.session, method)(f"{FIREBASE_URL}{RACINE}/{path}.json", **kw).status_code == 200
        except Exception: return False

    def supprimer_salon(self, code):
        """Supprime un salon vide ou abandonné, son secret et son annonce (refusé par la base si le salon est encore actif)."""
        if self.fb_ok("delete", f"lobbies/{code}"):
            self.fb_ok("delete", f"secrets/{code}")
            self.fb_ok("delete", f"index/{code}")
            return True
        return False

    def charger_pseudo_local(self):
        return design.lire_config().get("pseudo", "") or "ANONYME"

    def sauver_pseudo_local(self, p):
        if not p: return
        self.pseudo = p.upper()
        design.maj_config(pseudo=self.pseudo)

    def charger_mots(self):
        def lire(nom):
            p = resource_path(os.path.join('fichiers', nom))
            if not os.path.exists(p): return []
            for enc in ['utf-8', 'latin-1']:
                try:
                    with open(p, 'r', encoding=enc) as f: return [l.strip().upper() for l in f if len(l.strip()) >= 4]
                except: continue
            return []
        self.liste_mots = lire('mots_trouver.txt'); self.banque_verif = set(self.liste_mots) | set(lire('banque_mots.txt'))

    def show_frame(self, name):
        for f in self.frames.values(): (setattr(f, "active_sync", False) if hasattr(f, "active_sync") else None)
        f = self.frames[name]; f.tkraise()
        f.focus_set()
        if name == "PageAccueil": f.charger_liste()
        elif name == "PageLobby": f.entrer_lobby()
        elif name == "PageJeu": f.initialiser_partie()
        elif name == "PageScoreFinal": f.afficher_vainqueur()

    def _requete(self, method, path, data=None, timeout=2):
        """Requête REST authentifiée sous /v7. Renvoie le JSON en cas de succès, sinon None."""
        try:
            jeton = self.auth.jeton()
            if not jeton: return None
            u = f"{FIREBASE_URL}{RACINE}/{path}.json"
            kw = {"params": {"auth": jeton}, "timeout": timeout}
            if method in ("put", "patch"): kw["json"] = data
            r = getattr(self.session, method)(u, **kw)
            if 'Date' in r.headers:
                import email.utils
                server_time = email.utils.parsedate_to_datetime(r.headers['Date']).timestamp()
                self.server_time_offset = server_time - time.time()
            if r.status_code != 200: return None  # ex. refus des règles de sécurité
            return r.json()
        except Exception: return None

    def fb_get(self, path): return self._requete("get", path, timeout=1.5)
    def fb_patch(self, path, data): threading.Thread(target=lambda: self._requete("patch", path, data), daemon=True).start()
    def fb_put(self, path, data): threading.Thread(target=lambda: self._requete("put", path, data), daemon=True).start()
    def fb_delete(self, path): threading.Thread(target=lambda: self._requete("delete", path), daemon=True).start()


# ===================================================================== écrans
def barre_haut(parent, on_retour, droite_texte=""):
    h = tk.Frame(parent, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
    Icone(h, "retour", on_retour, 46, cadre=True).pack(side="left")
    etiquette(h, "SMOUT", "titre", 24).pack(side="left", padx=18)
    lbl = etiquette(h, droite_texte, "texte", 16, P["texte2"]); lbl.pack(side="right")
    tk.Frame(parent, bg=P["bordure"], height=1).pack(fill="x", pady=(16, 0))
    return lbl


class PageAccueil(tk.Frame):
    """Multijoueur : pseudo, créer un salon, rejoindre par code, salons publics."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", lambda: self.controller.controller.creer_menu_accueil()).pack(side="left")
        c = tk.Frame(self, bg=P["fond"]); c.pack(pady=(0, 10))
        etiquette(c, "Multijoueur", "titre", 46).pack(anchor="w", pady=(14, 6))
        lp = tk.Frame(c, bg=P["fond"]); lp.pack(anchor="w", pady=(0, 22))
        etiquette(lp, "Ton pseudo", "texte", 16, P["texte2"]).pack(side="left", padx=(0, 12))
        self.champ_pseudo = Champ(lp, largeur=260, hauteur=44, mono=True, taille=17)
        self.champ_pseudo.set(self.controller.pseudo if self.controller.pseudo != "ANONYME" else "")
        self.champ_pseudo.var.trace_add("write", self.format_p); self.champ_pseudo.pack(side="left")
        self.sv_pseudo = self.champ_pseudo.var
        actions = tk.Frame(c, bg=P["fond"]); actions.pack(anchor="w")
        Bouton(actions, "Créer un salon", self.creer, largeur=270, hauteur=56, taille=17).pack(side="left")
        self.champ_code = Champ(actions, largeur=300, hauteur=56, texte_aide="CODE", mono=True, taille=22)
        self.champ_code.pack(side="left", padx=14); self.champ_code.bind_entree(self.valider)
        self.champ_code.var.trace_add("write", lambda *a: self._filtrer_code())
        self.e = self.champ_code.e
        Bouton(actions, "Rejoindre", self.valider, largeur=150, hauteur=56, variante="tuile", taille=17).pack(side="left")
        tete = tk.Frame(c, bg=P["fond"]); tete.pack(fill="x", pady=(34, 10))
        etiquette(tete, espacer("Salons publics"), "texte", 14, P["texte2"], True).pack(side="left")
        Icone(tete, "rafraichir", self.charger_liste, 34).pack(side="right")
        self.liste = Defilant(c, largeur=748, hauteur=430); self.liste.pack(fill="x")
        self.lf = self.liste.interieur
        # mot de passe
        self.pass_view = Superposition(self, largeur=460); i = self.pass_view.interieur
        etiquette(i, "Salon protégé", "titre", 28).pack(anchor="w")
        etiquette(i, "Entre le mot de passe donné par l'hôte.", "texte", 15, P["texte2"]).pack(anchor="w", pady=(4, 14))
        self.champ_pw = Champ(i, largeur=400, hauteur=52, masque=True); self.champ_pw.pack(anchor="w")
        self.e_pw = self.champ_pw.e; self.champ_pw.bind_entree(self.check_pw)
        self.lbl_pw = etiquette(i, "", "texte", 14, P["danger"], True); self.lbl_pw.pack(anchor="w", pady=(8, 0))
        bf = tk.Frame(i, bg=i["bg"]); bf.pack(anchor="e", pady=(12, 0))
        Bouton(bf, "Annuler", self.pass_view.cacher, largeur=130, variante="discret").pack(side="left", padx=10)
        Bouton(bf, "Rejoindre", self.check_pw, largeur=150).pack(side="left")

    def _filtrer_code(self):
        v = "".join(ch for ch in self.champ_code.get() if ch.isdigit())[:4]
        if v != self.champ_code.get(): self.champ_code.set(v)

    def format_p(self, *args):
        v = "".join([c.upper() for c in self.sv_pseudo.get() if c.isalnum()])[:15]
        if self.sv_pseudo.get() != v: self.sv_pseudo.set(v)
        self.controller.sauver_pseudo_local(v)

    def connecte(self):
        if self.controller.player_id or self.controller.assurer_connexion(): return True
        tkm.showwarning("SMOUT", "Connexion au serveur impossible. Vérifie ta connexion internet."); return False

    def pseudo_ok(self):
        if self.sv_pseudo.get().strip(): return True
        self.champ_pseudo.focus(); self.champ_pseudo.c.itemconfig(1, outline=P["danger"]); return False

    def creer(self):
        if self.pseudo_ok() and self.connecte(): self.controller.show_frame("PageHostSetup")

    def charger_liste(self):
        self.champ_code.set("")
        for w in self.lf.winfo_children(): w.destroy()
        etiquette(self.lf, "Chargement…", "texte", 15, P["texte2"]).pack(anchor="w", pady=10)
        if self.controller.player_id or self.controller.auth.id_token:
            self.controller.fb_get_async("index", self.afficher_liste)
        else:
            def apres_connexion():
                ok = self.controller.assurer_connexion()
                self.controller.reponses_reseau.put((lambda d: self.controller.fb_get_async("index", self.afficher_liste) if ok else self.afficher_liste(None), None))
            threading.Thread(target=apres_connexion, daemon=True).start()

    def maintenant_ms(self): return (time.time() + self.controller.server_time_offset) * 1000

    def afficher_liste(self, data):
        if not self.winfo_exists(): return
        for w in self.lf.winfo_children(): w.destroy()
        data = data or {}
        n = 0
        for code, val in sorted(data.items()):
            if not isinstance(val, dict): continue
            age = self.maintenant_ms() - (val.get("maj") or 0)
            if age > DELAI_ABANDON_MS + 10000:  # salon abandonné : n'importe quel joueur le supprime
                threading.Thread(target=self.controller.supprimer_salon, args=(code,), daemon=True).start(); continue
            if val.get("visible") and val.get("status") == "waiting" and val.get("version") == VERSION_JEU and age < 30000:
                titre = f"Salon de {val.get('hote', 'ANONYME').capitalize()}"
                sous = f"Code {code}" + ("  ·  protégé par mot de passe" if val.get("prive") else "")
                CarteSalon(self.lf, titre, sous, f"{val.get('nb', 1)}/4", lambda c=code: self.tenter_join(c)).pack(pady=(0, 12), anchor="w")
                n += 1
        if not n:
            etiquette(self.lf, "Aucun salon public pour le moment. Crée le tien !", "texte", 16, P["texte2"]).pack(anchor="w", pady=10)

    def tenter_join(self, code):
        if not self.pseudo_ok(): return
        if not self.controller.player_id and not self.controller.assurer_connexion():
            tkm.showwarning("SMOUT", "Connexion au serveur impossible."); return
        idx = self.controller.fb_get(f"index/{code}")
        if not idx or self.maintenant_ms() - (idx.get("maj") or 0) > 30000:
            tkm.showwarning("SMOUT", "Salon introuvable"); return
        if idx.get("version") != VERSION_JEU:
            tkm.showwarning("SMOUT", f"Ce salon utilise une autre version du jeu ({idx.get('version', '?')}). Mets SMOUT à jour."); return
        if idx.get("nb", 0) >= 4:
            tkm.showwarning("SMOUT", "Ce salon est déjà complet (maximum 4 joueurs)."); return
        self.t_c = code
        if idx.get("prive"):
            self.champ_pw.set(""); self.lbl_pw.config(text=""); self.pass_view.montrer(); self.champ_pw.focus()
        else: self.rejoindre(code, "")

    def check_pw(self):
        mdp = self.champ_pw.get().strip()
        if not self.rejoindre(self.t_c, mdp, silencieux=True):
            self.lbl_pw.config(text="Mot de passe incorrect")

    def valider(self):
        c = self.champ_code.get().strip()
        if c: self.tenter_join(c)

    def rejoindre(self, code, mdp, silencieux=False):
        uid = self.controller.player_id
        joueur = {"name": self.controller.pseudo, "score": 0, "last_seen": {".sv": "timestamp"}}
        preuve = preuve_salon(code, mdp)
        if preuve: joueur["preuve"] = preuve
        # la base n'accepte l'inscription qu'avec la bonne preuve de mot de passe
        if not self.controller.fb_ok("put", f"lobbies/{code}/players/{uid}", joueur):
            if not silencieux: tkm.showwarning("SMOUT", "Salon introuvable")
            return False
        d = self.controller.fb_get(f"lobbies/{code}") or {}
        self.pass_view.cacher(); self.controller.is_host = False
        if len(d.get("players", {})) > 4:
            self.controller.fb_ok("delete", f"lobbies/{code}/players/{uid}")
            tkm.showwarning("SMOUT", "Ce salon est déjà complet (maximum 4 joueurs)."); return True
        self.controller.lobby_code, self.controller.code_affiche, self.controller.current_score = code, code, 0
        self.controller.settings_config.update({"password": mdp, "visible": d.get("settings", {}).get("visible", True)})
        self.controller.show_frame("PageLobby")
        return True


class PageHostSetup(tk.Frame):
    """Création d'un salon : visibilité et mot de passe (ils déterminent l'adresse du salon)."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", lambda: controller.show_frame("PageAccueil")).pack(side="left")
        c = tk.Frame(self, bg=P["fond"]); c.pack()
        etiquette(c, "Créer un salon", "titre", 46).pack(anchor="w", pady=(14, 24))
        p = Panneau(c, padding=30, largeur=700); p.pack()
        i = p.interieur
        etiquette(i, "Visibilité", "texte", 18, gras=True).pack(anchor="w", pady=(0, 12))
        v = tk.Frame(i, bg=i["bg"]); v.pack(anchor="w")
        self.c_pub = CarteChoix(v, "Public", "Visible dans la liste des salons", lambda: self.set_vis(True), largeur=306, hauteur=74); self.c_pub.pack(side="left")
        self.c_pri = CarteChoix(v, "Privé", "Seulement avec le code", lambda: self.set_vis(False), largeur=306, hauteur=74); self.c_pri.pack(side="left", padx=12)
        self.inter = Interrupteur(i, "Protéger par un mot de passe", False, self._mdp, largeur=600); self.inter.pack(anchor="w", pady=(26, 10))
        self.champ_mdp = Champ(i, largeur=632, hauteur=52, texte_aide="Mot de passe")
        self.e_pass = self.champ_mdp.e
        self.note = etiquette(i, "Le mot de passe n'est jamais enregistré : il faut le transmettre aux autres joueurs.", "texte", 13, P["texte2"])
        self.btn = Bouton(i, "Créer le salon", self.valider, largeur=632, hauteur=56, taille=17); self.btn.pack(pady=(24, 0))
        self.set_vis(True)

    def _mdp(self, actif):
        if actif:
            self.champ_mdp.pack(anchor="w", before=self.btn); self.note.pack(anchor="w", pady=(8, 0), before=self.btn); self.champ_mdp.focus()
        else:
            self.champ_mdp.set(""); self.champ_mdp.pack_forget(); self.note.pack_forget()

    def set_vis(self, v):
        self.is_pub = v; self.c_pub.set_selection(v); self.c_pri.set_selection(not v)

    def valider(self):
        mdp = self.champ_mdp.get().strip() if self.inter.valeur else ""
        self.controller.settings_config.update({"password": mdp, "visible": self.is_pub})
        self.controller.is_host, self.controller.lobby_code = True, ""; self.controller.show_frame("PageLobby")


class PageLobby(tk.Frame):
    """Salle d'attente : joueurs, code, réglages de la partie (modifiables par l'hôte)."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller, self.active_sync = controller, False
        self.active_mode = "CLASSIQUE"
        self.lbl_role = barre_haut(self, self.quitter, "")
        zone = Defilant(self, hauteur=200); zone.pack(fill="both", expand=True)
        corps = tk.Frame(zone.interieur, bg=P["fond"]); corps.pack(fill="both", expand=True, padx=60, pady=(18, 20))
        tete = tk.Frame(corps, bg=P["fond"]); tete.pack(fill="x")
        tg = tk.Frame(tete, bg=P["fond"]); tg.pack(side="left", anchor="n")
        self.lbl_titre = etiquette(tg, "Salon", "titre", 42); self.lbl_titre.pack(anchor="w")
        self.lbl_status = etiquette(tg, "", "texte", 17, P["texte2"]); self.lbl_status.pack(anchor="w", pady=(4, 0))
        # code
        self.boite_code = Panneau(tete, padding=18, rayon=14, contour=P["mal"], tirets=True); self.boite_code.pack(side="right", anchor="n")
        bc = self.boite_code.interieur
        gauche = tk.Frame(bc, bg=bc["bg"]); gauche.pack(side="left")
        self.lbl_code_titre = etiquette(gauche, espacer("Code du salon"), "texte", 12, P["texte2"], True); self.lbl_code_titre.pack(anchor="w")
        self.lbl_code = etiquette(gauche, "----", "chiffres", 40, P["mal"]); self.lbl_code.pack(anchor="w")
        self.btn_copier = Icone(bc, "copier", self.copier, 46, cadre=True); self.btn_copier.pack(side="left", padx=(16, 0))
        # colonnes
        cols = tk.Frame(corps, bg=P["fond"]); cols.pack(fill="x", pady=(20, 0))
        pj = Panneau(cols, padding=24, largeur=340); pj.pack(side="left", anchor="n")
        etiquette(pj.interieur, "Joueurs", "texte", 18, gras=True).pack(anchor="w", pady=(0, 12))
        self.player_slots = []
        for i in range(4):
            c = tk.Canvas(pj.interieur, width=292, height=62, bg=P["panneau"], highlightthickness=0); c.pack(pady=4)
            self.player_slots.append(c)
        ps = Panneau(cols, padding=26); ps.pack(side="left", anchor="n", padx=(24, 0), fill="x", expand=True)
        i = ps.interieur
        self.lbl_param_badge = etiquette(i, "Paramètres de la partie", "texte", 18, gras=True); self.lbl_param_badge.pack(anchor="w")
        etiquette(i, "Mode", "texte", 15, P["texte2"], True).pack(anchor="w", pady=(12, 8))
        gm = tk.Frame(i, bg=i["bg"]); gm.pack(anchor="w")
        self.cartes_mode = {}
        for k, (m, nom, desc) in enumerate(MODES):
            cc = CarteChoix(gm, nom, desc, lambda m=m: self.set_mode(m), largeur=200, hauteur=66)
            cc.grid(row=k // 3, column=k % 3, padx=(0, 10), pady=(0, 10)); self.cartes_mode[m] = cc
        etiquette(i, "Longueur des mots", "texte", 15, P["texte2"], True).pack(anchor="w", pady=(6, 8))
        lg = tk.Frame(i, bg=i["bg"]); lg.pack(anchor="w")
        etiquette(lg, "de", "texte", 15, P["texte2"]).pack(side="left", padx=(0, 8))
        self.c_min = Chips(lg, range(6, 11), 6, self._min, largeur=44, hauteur=40); self.c_min.pack(side="left")
        etiquette(lg, "à", "texte", 15, P["texte2"]).pack(side="left", padx=(6, 8))
        self.c_max = Chips(lg, range(6, 11), 7, self._max, largeur=44, hauteur=40); self.c_max.pack(side="left")
        etiquette(i, "Nombre de manches", "texte", 15, P["texte2"], True).pack(anchor="w", pady=(16, 8))
        self.c_rounds = Chips(i, range(1, 11), 3, lambda v: self.sync_params(), largeur=44, hauteur=40); self.c_rounds.pack(anchor="w")
        st = tk.Frame(i, bg=i["bg"]); st.pack(anchor="w", pady=(16, 0))
        f1 = tk.Frame(st, bg=i["bg"]); f1.pack(side="left", padx=(0, 40))
        etiquette(f1, "Essais", "texte", 15, P["texte2"], True).pack(anchor="w", pady=(0, 8))
        self.s_essais = Stepper(f1, 4, 10, 8, 1, lambda v: self.sync_params(), largeur_valeur=60); self.s_essais.pack(anchor="w")
        f2 = tk.Frame(st, bg=i["bg"]); f2.pack(side="left")
        etiquette(f2, "Temps par manche", "texte", 15, P["texte2"], True).pack(anchor="w", pady=(0, 8))
        self.s_time = Stepper(f2, 15, 600, 180, 15, lambda v: self.sync_params(), formater=mm_ss, largeur_valeur=100); self.s_time.pack(anchor="w")
        self.btn_lancer = Bouton(i, "Lancer la partie", self.lancer, largeur=620, hauteur=56, taille=17); self.btn_lancer.pack(anchor="w", pady=(22, 0))

    # --- réglages ---
    def _min(self, v):
        if v > self.c_max.get(): self.c_max.set_valeur(v)
        self.sync_params()
    def _max(self, v):
        if v < self.c_min.get(): self.c_min.set_valeur(v)
        self.sync_params()

    def copier(self):
        try:
            self.clipboard_clear(); self.clipboard_append(self.controller.code_affiche)
            self.lbl_code_titre.config(text=espacer("Code copié ✓"))
            self.after(1500, lambda: self.lbl_code_titre.config(text=espacer("Code du salon")) if self.winfo_exists() else None)
        except tk.TclError: pass

    def set_mode(self, mode):
        if not self.controller.is_host: return
        if self.active_mode == mode: return
        self.active_mode = mode
        self.controller.settings_config["game_mode"] = mode
        # 8 essais et 6 à 7 lettres par défaut pour chaque mode
        self.s_essais.set_valeur(8); self.c_min.set_valeur(6); self.c_max.set_valeur(7)
        temps, manches = {"MYSTERE": (180, 3), "RUSH": (120, 1), "BLAST": (60, 3), "PRECISION": (180, 3), "CLASSIQUE": (180, 3)}[mode]
        self.s_time.set_valeur(temps); self.c_rounds.set_valeur(manches)
        self.update_mode_ui(mode)
        self.sync_params()

    def update_mode_ui(self, mode):
        for m, c in self.cartes_mode.items():
            if c.selection != (m == mode): c.set_selection(m == mode)

    def valeurs(self):
        return {"rounds": self.c_rounds.get(), "essais": self.s_essais.get(), "min": self.c_min.get(), "max": self.c_max.get(), "timer": self.s_time.get()}

    def sync_params(self):
        if self.controller.is_host and self.active_sync:
            sc = self.controller.settings_config
            mode = sc.get("game_mode", "CLASSIQUE")
            data = {"game_mode": mode, "host_id": self.controller.player_id, "visible": sc["visible"], "version": VERSION_JEU}
            data.update(self.valeurs())
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", data)

    # --- cycle de vie ---
    def entrer_lobby(self):
        self.active_sync = True; self.controller.current_score = 0
        self.btn_lancer.activer(False)
        if self.controller.is_host and not self.controller.lobby_code:
            sc, ctl = self.controller.settings_config, self.controller
            uid, preuve = ctl.player_id, None
            for _ in range(10):
                code = str(random.randint(1000, 9999))
                idx = ctl.fb_get(f"index/{code}")
                if idx and (time.time() + ctl.server_time_offset) * 1000 - (idx.get("maj") or 0) < 30000: continue  # code annoncé et actif
                # la suppression n'est acceptée que si le salon n'existe pas, est vide ou abandonné
                if not ctl.fb_ok("delete", f"lobbies/{code}"): continue
                preuve = preuve_salon(code, sc["password"])
                if not (ctl.fb_ok("put", f"secrets/{code}", preuve) if preuve else ctl.fb_ok("delete", f"secrets/{code}")): continue
                mode = sc.get("game_mode", "CLASSIQUE")
                hote = {"name": ctl.pseudo, "score": 0, "last_seen": {".sv": "timestamp"}}
                if preuve: hote["preuve"] = preuve
                if ctl.fb_ok("put", f"lobbies/{code}", {"status": "waiting", "maj": {".sv": "timestamp"},
                        "settings": {"game_mode": mode, "rounds": 3, "essais": 8, "min": 6, "max": 7, "timer": 180, "host_id": uid, "visible": sc["visible"], "version": VERSION_JEU},
                        "players": {uid: hote}}):
                    break
            else:
                tkm.showwarning("SMOUT", "Impossible de créer le salon. Vérifie ta connexion internet.")
                self.active_sync = False; self.controller.show_frame("PageAccueil"); return
            ctl.code_affiche, ctl.lobby_code = code, code
            ctl.nb_joueurs, ctl.statut_salon = 1, "waiting"
            ctl.maj_index()
        self.lobby_gen = getattr(self, "lobby_gen", 0) + 1
        self.lbl_code.config(text=self.controller.code_affiche)
        self.lbl_titre.config(text="Salon")
        self.ecouter_lobby(self.lobby_gen)

    def ecouter_lobby(self, gen):
        if not self.active_sync or gen != self.lobby_gen: return
        self.controller.fb_get_async(f"lobbies/{self.controller.lobby_code}", lambda d: self.traiter_lobby(d, gen))

    def dessiner_joueur(self, c, index, nom=None, hote=False, deco=False, moi=False):
        c.delete("all"); w, h = 292, 62
        if nom is None:
            c.create_oval(14, 13, 50, 49, fill=P["vide"], outline="")
            c.create_text(66, h / 2, text="Place libre", anchor="w", fill=P["texte_absent"], font=police("texte", 17, True))
            return
        arrondi(c, 0, 0, w, h, 12, fill=P["tuile"], outline="")
        coul = Avatar.COULEURS[index % len(Avatar.COULEURS)]
        c.create_oval(14, 13, 50, 49, fill=coul, outline="")
        c.create_text(32, 31, text=nom[:1].upper(), fill="#16130a", font=police("texte", 16, True))
        aff = nom.capitalize() + (" (vous)" if moi else "")
        c.create_text(64, h / 2, text=aff, anchor="w", fill=P["texte"], font=police("texte", 17, True), width=150)
        if deco: c.create_text(w - 14, h / 2, text="Déconnecté", anchor="e", fill=P["danger"], font=police("texte", 14))
        elif hote:
            c.create_text(w - 14, h / 2, text="Hôte", anchor="e", fill=P["mal"], font=police("texte", 15, True))
            x = w - 66; y = h / 2
            c.create_line(x - 9, y + 5, x - 9, y - 4, x - 4, y + 1, x, y - 6, x + 4, y + 1, x + 9, y - 4, x + 9, y + 5, x - 9, y + 5, fill=P["mal"], width=1.8, joinstyle="round")

    def traiter_lobby(self, d, gen):
        if not self.active_sync or gen != self.lobby_gen: return
        if d:
            s, p = d.get("settings", {}), d.get("players", {})
            server_now = max([pdat.get("last_seen", 0) for pdat in p.values()] + [0])
            for pid, pdat in list(p.items()):
                last_seen = pdat.get("last_seen", 0)
                diff_sec = (server_now - last_seen) / 1000
                if server_now > 0 and diff_sec > 25:
                    self.controller.fb_delete(f"lobbies/{self.controller.lobby_code}/players/{pid}"); del p[pid]
            if not p: self.quitter(); return

            hid = s.get("host_id")
            if hid not in p:
                hid = sorted(p.keys())[0]  # même choix chez tous les joueurs
                if hid == self.controller.player_id: self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", {"host_id": hid})
            self.controller.is_host = (s.get("host_id") == self.controller.player_id)
            self.controller.nb_joueurs, self.controller.statut_salon = len(p), d.get("status", "waiting")
            hote_nom = p.get(hid, {}).get("name", "")
            self.lbl_titre.config(text=f"Salon de {hote_nom.capitalize()}" if hote_nom else "Salon")
            self.lbl_role.config(text="Vous êtes l'hôte" if self.controller.is_host else "L'hôte règle la partie")

            mode = s.get("game_mode", "CLASSIQUE")
            if not self.controller.is_host:  # l'hôte garde ses propres réglages (la base peut avoir un temps de retard)
                self.active_mode = mode
                self.controller.settings_config["game_mode"] = mode
            self.update_mode_ui(self.active_mode)
            if not self.controller.is_host:
                self.c_rounds.set_valeur(s.get("rounds", 3)); self.s_essais.set_valeur(s.get("essais", 8))
                self.c_min.set_valeur(s.get("min", 6)); self.c_max.set_valeur(s.get("max", 7)); self.s_time.set_valeur(s.get("timer", 180))

            if d.get("status") == "playing":
                self.active_sync = False
                self.controller.settings_config.update(s)
                self.controller.settings_config["round_num"] = s.get("current_round", 1)
                self.controller.show_frame("PageJeu"); return

            pids = list(p.keys())
            for i, slot in enumerate(self.player_slots):
                if i < len(pids):
                    pid = pids[i]
                    deco = server_now > 0 and (server_now - p[pid].get("last_seen", 0)) / 1000 > 12
                    self.dessiner_joueur(slot, i, p[pid]["name"], pid == hid, deco, pid == self.controller.player_id)
                else: self.dessiner_joueur(slot, i)
            n = len(p)
            self.lbl_status.config(text=f"En attente des joueurs · {n} sur 4" + ("  ·  salon privé" if not self.controller.settings_config.get("visible", True) else ""))
            hote = self.controller.is_host
            for sw in [self.c_rounds, self.s_essais, self.c_min, self.c_max, self.s_time] + list(self.cartes_mode.values()): sw.activer(hote)
            if hote:
                self.btn_lancer.set_variante("principal")
                self.btn_lancer.set_text("Lancer la partie" if n > 1 else "Il faut au moins 2 joueurs")
                self.btn_lancer.activer(n > 1)
            else:
                self.btn_lancer.set_variante("discret"); self.btn_lancer.set_text("En attente du lancement par l'hôte…"); self.btn_lancer.activer(False)
        self.after(800, lambda: self.ecouter_lobby(gen))

    def quitter(self): self.active_sync = False; self.controller.quitter_lobby_logic(); self.controller.show_frame("PageAccueil")

    def lancer(self):
        v = self.valeurs()
        mi, ma = v["min"], v["max"]
        f = [m for m in self.controller.liste_mots if mi <= len(m) <= ma]
        f_sorted = sorted(f or self.controller.liste_mots)
        rush_seed = random.randint(1000, 999999)
        sc = self.controller.settings_config
        mode = sc.get("game_mode", "CLASSIQUE")
        new_settings = {
            "game_mode": mode, "rush_seed": rush_seed, "version": VERSION_JEU,
            "rounds": v["rounds"], "current_round": 1,
            "essais": v["essais"], "min": mi, "max": ma,
            "timer": v["timer"], "host_id": self.controller.player_id,
            "visible": sc.get("visible", True),
            "start_time": time.time() + self.controller.server_time_offset
        }
        self.controller.settings_config.update(new_settings)
        self.controller.statut_salon = "playing"; self.controller.maj_index()
        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"status": "playing", "settings": new_settings, "match_data": None, "fini_states": None, "round_wins": None, "rush_recap": None})


class Adversaire(tk.Frame):
    """Mini-grille d'un adversaire + nom, score et avancement."""
    def __init__(self, parent, nom, essais, longueur, taille=14, index=0):
        super().__init__(parent, bg=P["fond"])
        self.taille, self.index = taille, index
        self.zone = tk.Frame(self, bg=P["fond"]); self.zone.pack(side="left", anchor="n")
        self.grille = []
        self.construire(essais, longueur)
        info = tk.Frame(self, bg=P["fond"]); info.pack(side="left", anchor="n", padx=(16, 0))
        self.lbl_nom = etiquette(info, nom, "texte", 17, gras=True); self.lbl_nom.pack(anchor="w")
        self.lbl_score = etiquette(info, "0", "chiffres", 22, P["mal"]); self.lbl_score.pack(anchor="w")
        self.lbl_etat = etiquette(info, "", "texte", 14, P["texte2"]); self.lbl_etat.pack(anchor="w")
    def construire(self, essais, longueur):
        for w in self.zone.winfo_children(): w.destroy()
        self.grille = []
        for r in range(essais):
            ligne = []
            for c in range(longueur):
                t = Tuile(self.zone, self.taille, rayon=3, mini=True); t.config(bg=KEY_BG); t.grid(row=r, column=c, padx=1.5, pady=1.5); ligne.append(t)
            self.grille.append(ligne)


class PageJeu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller, self.active_sync = controller, False
        self.user_zoom = self.me_charger_zoom()
        self.sync_gen = 0
        # En-tête
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", self.quitter_jeu).pack(side="left")
        zf = tk.Frame(h, bg=P["fond"]); zf.pack(side="right")
        Icone(zf, "moins", lambda: self.adjust_zoom(-0.1), 32).pack(side="left")
        self.lbl_zoom = etiquette(zf, f"{int(self.user_zoom * 100)} %", "texte", 13, P["texte2"]); self.lbl_zoom.pack(side="left", padx=4)
        Icone(zf, "plus", lambda: self.adjust_zoom(0.1), 32).pack(side="left")
        self.lbl_info = etiquette(h, "", "texte", 16, P["texte2"]); self.lbl_info.pack(side="top", pady=8)
        # Corps : colonne de jeu + adversaires
        corps = tk.Frame(self, bg=P["fond"]); corps.pack(fill="both", expand=True)
        corps.grid_columnconfigure(0, weight=1)
        self.colonne = tk.Frame(corps, bg=P["fond"]); self.colonne.grid(row=0, column=0, sticky="n")
        self.adv_container = tk.Frame(corps, bg=P["fond"], width=300); self.adv_container.grid(row=0, column=1, sticky="ne", padx=(10, 40), pady=(20, 0))
        stats = tk.Frame(self.colonne, bg=P["fond"]); stats.pack(pady=(4, 0))
        self.s_manche = Stat(stats, "Manche", "1"); self.s_manche.pack(side="left", padx=34)
        self.s_temps = Stat(stats, "Temps", "00:00"); self.s_temps.pack(side="left", padx=34)
        self.s_score = Stat(stats, "Score", "0", P["mal"]); self.s_score.pack(side="left", padx=34)
        self.lbl_timer = self.s_temps.lbl
        self.moi_side = tk.Frame(self.colonne, bg=P["fond"]); self.moi_side.pack(pady=(16, 0))
        self.msg_c = tk.Frame(self.colonne, bg=P["fond"]); self.msg_c.pack(pady=(10, 6))
        self.lbl_msg = etiquette(self.msg_c, "", "texte", 15, P["texte"], True, justify="center"); self.lbl_msg.pack(side="left")
        self.btn_def = etiquette(self.msg_c, "  Définition ↗", "texte", 14, P["texte2"], cursor="hand2")
        self.btn_def.bind("<Button-1>", lambda e: webbrowser.open(f"https://www.google.com/search?q=D%C3%A9finition+du+mot+{self.mot}"))
        self.btn_next = Bouton(self.colonne, "Manche suivante", self.clic_suivant, largeur=300, hauteur=52, taille=16)
        self.zone_clavier = tk.Frame(self.colonne, bg=P["fond"]); self.zone_clavier.pack(pady=(4, 16))
        self.bind("<Configure>", self.on_resize)

    # --- zoom ---
    def me_charger_zoom(self):
        try: return float(design.lire_config().get("user_zoom", 1.0))
        except Exception: return 1.0
    def sauver_zoom_pref(self): design.maj_config(user_zoom=self.user_zoom)
    def adjust_zoom(self, delta):
        new_zoom = round(max(0.6, min(1.6, self.user_zoom + delta)), 2)
        if new_zoom != self.user_zoom:
            self.user_zoom = new_zoom
            self.lbl_zoom.config(text=f"{int(self.user_zoom * 100)} %")
            self.actualiser_tailles_grilles(); self.sauver_zoom_pref()
    def on_resize(self, e):
        if e.widget == self:
            if abs(e.height - getattr(self, "_last_h", 0)) > 30:
                self._last_h = e.height; self.actualiser_tailles_grilles()

    def quitter_jeu(self): self.active_sync, self.timer_actif = False, False; self.winfo_toplevel().unbind("<Key>"); self.controller.quitter_lobby_logic(); self.controller.controller.creer_menu_accueil()

    # --- construction d'une manche ---
    def initialiser_partie(self):
        self.sync_gen = getattr(self, "sync_gen", 0) + 1  # invalide les boucles du round précédent
        self.active_sync, self.last_sync_data, self.timer_actif = False, None, False; self.btn_next.pack_forget()
        [w.destroy() for w in self.moi_side.winfo_children() + self.adv_container.winfo_children() + self.zone_clavier.winfo_children()]
        self.lbl_msg.config(text=""); self.btn_def.pack_forget()

        dm = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if dm and "settings" in dm:
            self.controller.settings_config.update(dm["settings"])
        conf = self.controller.settings_config
        mode = conf.get("game_mode", "CLASSIQUE")
        self.controller.settings_config["game_mode"] = mode

        mi, ma = conf.get("min", 6), conf.get("max", 10)
        f_list = sorted([m for m in self.controller.liste_mots if mi <= len(m) <= ma] or self.controller.liste_mots)
        rush_seed = conf.get("rush_seed", 12345)
        self.rush_words = [mot_graine(f_list, rush_seed, i) for i in range(100)]  # même calcul sur PC et sur le web
        self.rush_index = 0
        if mode == "RUSH":
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"rush_index": 0})

        self.mot = self.rush_words[0]  # recalculé depuis la graine partagée (le mot n'est pas dans la base)
        self.controller.dernier_mot = self.mot
        self.round_actuel = conf.get("round_num", 1)
        self.start_time_round = conf.get("start_time", time.time())
        if int(self.round_actuel) == 1:
            self.controller.current_score = 0
            self.blast_scored_rounds = set()
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": 0})
        elif not hasattr(self, 'blast_scored_rounds'):
            self.blast_scored_rounds = set()

        self.ligne, self.fini_local, self.temps_restant = 0, False, conf.get("timer", 180)
        self.tape = [] if mode == "MYSTERE" else [self.mot[0]]
        self.statut_lettres = {l: None for l in ALPHABET}
        self.lbl_info.config(text=f"{NOM_MODE.get(mode, mode)} · {len(self.mot)} lettres")
        self.s_manche.set(str(self.round_actuel), suffixe=f" / {conf.get('rounds', 1)}")
        self.s_score.set(nombre(self.controller.current_score))

        self.labels_moi = self.creer_grille(self.moi_side, "", True)
        try: hf = self.winfo_toplevel().winfo_height()
        except Exception: hf = 860
        self.clavier = Clavier(self.zone_clavier, self.ajouter_lettre, self.effacer, self.valider, hauteur=50 if hf >= 760 or hf < 200 else 40); self.clavier.pack()

        hid = dm.get("settings", {}).get("host_id") if dm else None
        self.adv_widgets, self.adv_grids, self.adv_last_word_len = {}, {}, {}
        if dm:
            opponents = [item for item in dm.get("players", {}).items() if item[0] != self.controller.player_id]
            t_adv = self.taille_adv(len(opponents))
            for idx, (pid, p) in enumerate(opponents):
                a = Adversaire(self.adv_container, p["name"].capitalize(), conf.get("essais", 6), len(self.mot), t_adv, idx + 1)
                a.pack(anchor="w", pady=(0, 26))
                self.adv_widgets[pid] = a; self.adv_grids[pid] = a.grille; self.adv_last_word_len[pid] = len(self.mot)

        gen = self.sync_gen
        self.active_sync, self.timer_actif = True, True; self.update_timer(gen)
        threading.Thread(target=self.bg_sync, args=(gen,), daemon=True).start(); self.ui_loop(gen)
        self.winfo_toplevel().bind("<Key>", self.clavier_physique); self.maj_affichage()

    def recreer_grille_adv(self, pid, word_len):
        a = self.adv_widgets.get(pid)
        if a:
            a.construire(self.controller.settings_config.get("essais", 6), word_len)
            self.adv_grids[pid] = a.grille; self.adv_last_word_len[pid] = word_len

    def boucle_valide(self, gen):
        return self.active_sync and gen == getattr(self, "sync_gen", 0)

    def bg_sync(self, gen):
        while self.boucle_valide(gen):
            d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
            if d and gen == self.sync_gen: self.last_sync_data = d
            time.sleep(0.8)

    def ui_loop(self, gen):
        if not self.boucle_valide(gen): return
        if self.last_sync_data: self.traiter_match(self.last_sync_data)
        if self.boucle_valide(gen): self.after(200, lambda: self.ui_loop(gen))

    def points_blast(self, d):
        rw_all = d.get("round_wins") or {}
        rw_round = {}
        if isinstance(rw_all, dict): rw_round = rw_all.get(f"r{self.round_actuel}") or rw_all.get(str(self.round_actuel)) or {}
        elif isinstance(rw_all, list) and int(self.round_actuel) < len(rw_all): rw_round = rw_all[int(self.round_actuel)] or {}
        if isinstance(rw_round, dict) and rw_round:
            return sorted(rw_round.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0)
        return []

    def traiter_match(self, d):
        if d.get("status") == "waiting":  # l'hôte a ramené tout le monde au salon
            self.active_sync, self.timer_actif = False, False; self.winfo_toplevel().unbind("<Key>"); self.controller.show_frame("PageLobby"); return
        if d.get("status") == "finished": self.active_sync = False; self.winfo_toplevel().unbind("<Key>"); self.controller.show_frame("PageScoreFinal"); return
        s, p = d.get("settings", {}), d.get("players", {})
        server_now = max([pdat.get("last_seen", 0) for pdat in p.values()] + [0])

        if int(s.get("current_round", 1)) > int(self.round_actuel):
            self.active_sync = False
            self.controller.settings_config.update(s)
            self.controller.settings_config["round_num"] = int(s["current_round"])
            self.initialiser_partie(); return
        if s.get("rush_seed") and s.get("rush_seed") != self.controller.settings_config.get("rush_seed") and float(s.get("start_time", 0) or 0) > float(self.start_time_round) + 0.5:
            # un nouveau match a été lancé pendant qu'on était encore sur l'ancien
            # (une lecture plus ancienne que la manche en cours, arrivée en retard, est ignorée)
            self.active_sync = False
            self.controller.settings_config.update(s)
            self.controller.settings_config["round_num"] = int(s.get("current_round", 1))
            self.initialiser_partie(); return

        hid = s.get("host_id")
        active_pids = [pid for pid, pdat in p.items() if server_now == 0 or (server_now - pdat.get("last_seen", 0))/1000 <= 15]
        if not active_pids: active_pids = list(p.keys())
        # Réattribution de l'hôte s'il a quitté ou ne répond plus (sinon la partie reste bloquée)
        if active_pids and hid not in active_pids:
            nouvel_hote = sorted(active_pids)[0]  # même choix chez tous les joueurs
            if nouvel_hote == self.controller.player_id:
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", {"host_id": nouvel_hote})
            hid = nouvel_hote
        self.controller.is_host = (s.get("host_id") == self.controller.player_id)  # devient vrai dès que la base a validé la reprise
        self.controller.nb_joueurs = len(p)

        mode = s.get("game_mode", "CLASSIQUE")
        self.controller.settings_config["game_mode"] = mode
        self.s_manche.set(str(s.get("current_round", 1)), suffixe=f" / {s.get('rounds', 1)}")
        moi = p.get(self.controller.player_id, {})
        self.s_score.set(nombre(max(self.controller.current_score, moi.get("score", 0) if isinstance(moi.get("score", 0), (int, float)) else 0)))
        if mode == "RUSH":
            self.lbl_info.config(text=f"Rush · mot n° {self.rush_index + 1} · {len(self.mot)} lettres")

        fs = d.get("fini_states") or {}
        md = d.get("match_data", {}) or {}
        for pid, a in list(self.adv_widgets.items()):
            deco = not (pid in p and (server_now == 0 or (server_now - p[pid].get("last_seen", 0))/1000 <= 12))
            pdat = p.get(pid, {})
            nom = pdat.get("name", a.lbl_nom.cget("text")).capitalize() + (" ♛" if pid == hid else "")
            if a.lbl_nom.cget("text") != nom: a.lbl_nom.config(text=nom)
            a.lbl_score.config(text=nombre(pdat.get("score", 0) if isinstance(pdat.get("score", 0), (int, float)) else 0))
            # avancement
            lignes = md.get(pid) or {}
            items = list(enumerate(lignes)) if isinstance(lignes, list) else [(int(k), v) for k, v in lignes.items() if str(k).isdigit()] if isinstance(lignes, dict) else []
            items = [(i, v) for i, v in items if v]
            if mode == "RUSH":
                adv_idx = pdat.get("rush_index", pdat.get("score", 0)) or 0
                items = [(i, v) for i, v in items if v.get("w_idx") == adv_idx]
            trouve = any(all(c == "B" for c in v.get("c", [])) for _, v in items)
            if deco: etat, coul = "Déconnecté", P["danger"]
            elif mode == "RUSH":
                adv_idx = pdat.get("rush_index", pdat.get("score", 0)) or 0
                etat, coul = f"Mot n° {adv_idx + 1}", P["texte2"]
                if adv_idx < self.rush_index:
                    mot_adv = self.rush_words[adv_idx] if adv_idx < len(self.rush_words) else "?"
                    etat = f"Mot n° {adv_idx + 1} · {mot_adv}"
            elif fs.get(pid): etat, coul = (f"Trouvé en {len(items)}", P["succes"]) if trouve else ("Pas trouvé", P["texte2"]), None
            else: etat, coul = f"Essai {min(len(items) + 1, s.get('essais', 6))}", P["texte2"]
            if isinstance(etat, tuple): etat, coul = etat
            a.lbl_etat.config(text=etat, fg=coul or P["texte2"])

        round_over = (sum(1 for pid in active_pids if fs.get(pid)) >= len(active_pids)) or (self.temps_restant <= 0)
        fc = sum(1 for pid in active_pids if fs.get(pid))
        if round_over: self.timer_actif = False
        for pid in list(self.adv_grids.keys()):
            if mode == "RUSH" and hasattr(self, "rush_words"):
                adv_idx = p.get(pid, {}).get("rush_index", p.get(pid, {}).get("score", 0))
                if adv_idx < len(self.rush_words):
                    exp_len = len(self.rush_words[adv_idx])
                    if self.adv_last_word_len.get(pid) != exp_len:
                        self.recreer_grille_adv(pid, exp_len)
            grid = self.adv_grids[pid]
            cible = [[("", KEY_BG) for _ in row] for row in grid]
            if pid in md:
                data_p = md[pid]
                adv_idx = p.get(pid, {}).get("rush_index", p.get(pid, {}).get("score", 0))
                show_letters = (adv_idx < self.rush_index) if mode == "RUSH" else self.fini_local
                lignes = list(enumerate(data_p)) if isinstance(data_p, list) else list(data_p.items()) if isinstance(data_p, dict) else []
                for l_idx, content in lignes:
                    try: idx = int(l_idx)
                    except (ValueError, TypeError): continue
                    if not content or idx >= len(grid): continue
                    if mode == "RUSH" and content.get("w_idx") != adv_idx: continue
                    for c_idx, code in enumerate(content.get("c", [])):
                        if c_idx < len(grid[idx]): cible[idx][c_idx] = ("", couleur_code(code))
                    if show_letters:
                        for c_idx, char in enumerate(content.get("l", [])):
                            if c_idx < len(grid[idx]): cible[idx][c_idx] = (char, cible[idx][c_idx][1])
            for r, row in enumerate(grid):
                for c, t in enumerate(row):
                    txt, coul = cible[r][c]
                    if t.cget("text") != txt or t._fond != coul: t.config(text=txt, bg=coul)

        if mode == "BLAST":
            if not hasattr(self, 'blast_scored_rounds'): self.blast_scored_rounds = set()
            if self.round_actuel not in self.blast_scored_rounds:
                sorted_wins = self.points_blast(d)
                if sorted_wins:
                    pts_map = {0: 4, 1: 3, 2: 2, 3: 1}
                    my_rank = next((i for i, (pid, _) in enumerate(sorted_wins) if pid == self.controller.player_id), None)
                    if my_rank is not None and my_rank in pts_map:
                        self.controller.current_score += pts_map[my_rank]
                        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score})
                        self.blast_scored_rounds.add(self.round_actuel)
                elif round_over:
                    self.blast_scored_rounds.add(self.round_actuel)

        if self.fini_local:
            if not self.btn_def.winfo_ismapped(): self.btn_def.pack(side="left")
            if round_over:
                msg_text = f"Le mot était {self.mot}"
                if mode == "BLAST":
                    sorted_wins = self.points_blast(d)
                    pts_map = {0: 4, 1: 3, 2: 2, 3: 1}
                    parts = [f"{p.get(w_pid, {}).get('name', 'Joueur').capitalize()} +{pts_map.get(rank, 0)}" for rank, (w_pid, _) in enumerate(sorted_wins) if rank in pts_map]
                    if parts: msg_text += "\n" + "   ·   ".join(parts)
                if self.lbl_msg.cget("text") != msg_text: self.lbl_msg.config(text=msg_text, fg=P["mal"])
                if self.controller.is_host and not self.btn_next.winfo_ismapped():
                    self.btn_next.set_text("Voir les résultats" if int(s['current_round']) >= int(s['rounds']) else "Manche suivante")
                    self.btn_next.pack(pady=(4, 10), before=self.zone_clavier)
            else:
                t = f"En attente des autres joueurs ({fc}/{len(active_pids)})"
                if self.lbl_msg.cget("text") != t: self.lbl_msg.config(text=t, fg=P["texte2"])

    def update_timer(self, gen):
        if not self.timer_actif or gen != self.sync_gen: return
        self.temps_restant = max(0, int(int(self.controller.settings_config.get("timer", 180)) - ((time.time() + self.controller.server_time_offset) - self.start_time_round)))
        self.s_temps.set(mm_ss(self.temps_restant), P["texte"] if self.temps_restant > 30 else P["danger"])
        if self.temps_restant <= 0:
            if not self.fini_local: self.finir_round(False)
            self.timer_actif = False
        else: self.after(500, lambda: self.update_timer(gen))

    def message_temp(self, texte, couleur, duree=1200):
        self.lbl_msg.config(text=texte, fg=couleur)
        self.after(duree, lambda: self.lbl_msg.config(text="") if not self.fini_local and self.lbl_msg.cget("text") == texte else None)

    def valider(self):
        if self.fini_local: return
        mode = self.controller.settings_config.get("game_mode", "CLASSIQUE")
        req_len = len(self.mot) - 1 if mode == "MYSTERE" else len(self.mot)
        if len(self.tape) != req_len: return

        if mode == "MYSTERE":
            t_suffix = "".join(self.tape)
            target_suffix = self.mot[1:]
            is_valid = (t_suffix == target_suffix) or any((chr(code) + t_suffix) in self.controller.banque_verif for code in range(65, 91))
            if not is_valid:
                self.message_temp("Mot inconnu", P["danger"]); return
            res, secret = [MUTED]*len(target_suffix), list(self.mot)
            for i in range(len(target_suffix)):
                if self.tape[i] == target_suffix[i]: res[i], secret[i+1] = ACCENT1, None
            for i in range(len(target_suffix)):
                if res[i] != ACCENT1 and self.tape[i] in secret: res[i] = ACCENT2; secret[secret.index(self.tape[i])] = None
            self.maj_statuts(self.tape, res)
            for i, c in enumerate(res): self.labels_moi[self.ligne][i+1].config(bg=c)
            self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}/{self.ligne}", {"c": en_codes([MUTED]+res), "l": ["?"]+self.tape})
            for case in self.labels_moi[self.ligne]: case.set_curseur(False)
            if all(c == ACCENT1 for c in res):
                self.labels_moi[self.ligne][0].config(text=self.mot[0], bg=ACCENT1)
                self.finir_round(True)
            elif self.ligne >= self.controller.settings_config["essais"]-1:
                self.finir_round(False)
            else:
                self.ligne += 1; self.tape = []; self.maj_affichage()
        else:
            t = "".join(self.tape)
            if t not in self.controller.banque_verif and t != self.mot:
                self.message_temp("Mot inconnu", P["danger"]); return
            res, secret = [MUTED]*len(self.mot), list(self.mot)
            for i in range(len(self.mot)):
                if self.tape[i] == self.mot[i]: res[i], secret[i] = ACCENT1, None
            for i in range(len(self.mot)):
                if res[i] != ACCENT1 and self.tape[i] in secret: res[i] = ACCENT2; secret[secret.index(self.tape[i])] = None
            self.maj_statuts(self.tape, res)
            for i, c in enumerate(res): self.labels_moi[self.ligne][i].config(bg=c)
            for case in self.labels_moi[self.ligne]: case.set_curseur(False)
            payload = {"c": en_codes(res), "l": self.tape}
            if mode == "RUSH":
                payload["w_idx"] = self.rush_index
            if not (mode == "RUSH" and t == self.mot):
                self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}/{self.ligne}", payload)

            if t == self.mot:
                if mode == "RUSH":
                    self.controller.current_score += 1
                    self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score, "rush_index": self.rush_index + 1})
                    self.s_score.set(nombre(self.controller.current_score))
                    self.reinitialiser_grille_rush()
                    self.message_temp("+1 point · mot suivant !", P["succes"])
                else:
                    self.finir_round(True)
            elif self.ligne >= self.controller.settings_config["essais"]-1:
                if mode == "RUSH":
                    essais = self.controller.settings_config["essais"]
                    for r in range(0, essais - 1):
                        for c_idx in range(len(self.labels_moi[r])):
                            src = self.labels_moi[r+1][c_idx]
                            self.labels_moi[r][c_idx].config(text=src.cget("text"), bg=src._fond)
                    for c_idx in range(len(self.labels_moi[-1])):
                        self.labels_moi[-1][c_idx].config(text="", bg=BG)
                    self.ligne = essais - 1
                    self.tape = [self.mot[0]]
                    self.maj_affichage()
                else:
                    self.finir_round(False)
            else:
                self.ligne += 1
                self.tape = [self.mot[0]]
                self.maj_affichage()

    def maj_statuts(self, lettres, res):
        for i, char in enumerate(lettres):
            cur = self.statut_lettres.get(char)
            if res[i] == ACCENT1: self.statut_lettres[char] = ACCENT1
            elif res[i] == ACCENT2 and cur != ACCENT1: self.statut_lettres[char] = ACCENT2
            elif res[i] == MUTED and cur not in [ACCENT1, ACCENT2]: self.statut_lettres[char] = MUTED
        self.maj_clavier()

    def reinitialiser_grille_rush(self):
        self.rush_index += 1
        if hasattr(self, 'rush_words') and self.rush_index < len(self.rush_words):
            self.mot = self.rush_words[self.rush_index]
        else:
            mi, ma = self.controller.settings_config.get("min", 6), self.controller.settings_config.get("max", 10)
            f = [m for m in self.controller.liste_mots if mi <= len(m) <= ma]
            self.mot = random.choice(f or self.controller.liste_mots)
        self.controller.dernier_mot = self.mot
        self.ligne = 0
        self.tape = [self.mot[0]]
        self.statut_lettres = {l: None for l in ALPHABET}
        self.controller.fb_delete(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}")
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}", {})
        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"rush_index": self.rush_index, "score": self.controller.current_score})
        [w.destroy() for w in self.moi_side.winfo_children()]
        self.labels_moi = self.creer_grille(self.moi_side, "", True)
        self.maj_clavier()
        self.lbl_info.config(text=f"Rush · mot n° {self.rush_index + 1} · {len(self.mot)} lettres")
        self.maj_affichage()

    def get_max_tape(self):
        if hasattr(self, "labels_moi") and self.labels_moi and self.ligne < len(self.labels_moi):
            nb_cells = len(self.labels_moi[self.ligne])
            if self.controller.settings_config.get("game_mode") == "MYSTERE":
                return max(0, nb_cells - 1)
            return nb_cells
        mode = self.controller.settings_config.get("game_mode", "CLASSIQUE")
        return len(self.mot) - 1 if mode == "MYSTERE" else len(self.mot)

    def ajouter_lettre(self, char):
        if self.fini_local: return
        max_l = self.get_max_tape()
        if len(self.tape) > max_l: self.tape = self.tape[:max_l]
        if len(self.tape) < max_l: self.tape.append(char)
        self.maj_affichage()

    def effacer(self):
        if self.fini_local: return
        max_l = self.get_max_tape()
        if len(self.tape) > max_l: self.tape = self.tape[:max_l]
        min_len = 0 if self.controller.settings_config.get("game_mode") == "MYSTERE" else 1
        if len(self.tape) > min_len: self.tape.pop()
        self.maj_affichage()

    def finir_round(self, vic):
        self.fini_local = True
        for case in self.labels_moi[min(self.ligne, len(self.labels_moi) - 1)]: case.set_curseur(False)
        self.winfo_toplevel().unbind("<Key>")
        mode = self.controller.settings_config.get("game_mode", "CLASSIQUE")
        if vic:
            if mode in ["CLASSIQUE", "MYSTERE"]:
                self.controller.current_score += 1
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score})
            elif mode == "PRECISION":
                max_essais = self.controller.settings_config.get("essais", 6)
                base_pts = max(1, max_essais - self.ligne)
                pts = base_pts * 2 if self.ligne == 0 else base_pts
                self.controller.current_score += pts
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score})
            elif mode == "BLAST":
                self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/round_wins/r{self.round_actuel}/{self.controller.player_id}", {".sv": "timestamp"})
        self.s_score.set(nombre(self.controller.current_score))
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/fini_states/{self.controller.player_id}", True)
        self.lbl_msg.config(text="Bien joué !" if vic else "Manche terminée", fg=P["succes"] if vic else P["texte2"])
        if not self.btn_def.winfo_ismapped(): self.btn_def.pack(side="left")

    def clic_suivant(self):
        self.btn_next.pack_forget()
        d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if not d: return
        s = d["settings"]
        mode = s.get("game_mode", "CLASSIQUE")
        if mode == "RUSH" and hasattr(self, "rush_words"):
            p = d.get("players", {})
            max_idx = max([pdat.get("rush_index", 0) for pdat in p.values()] + [self.rush_index, 0])
            round_words = self.rush_words[:max_idx + 1]
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/rush_recap", {f"r{self.round_actuel}": round_words})
        if int(s["current_round"]) < int(s["rounds"]):
            s.update({
                "rush_seed": random.randint(1000, 999999),
                "current_round": int(s["current_round"]) + 1,
                "start_time": time.time() + self.controller.server_time_offset
            })
            self.controller.settings_config.update(s)
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"settings": s, "status": "playing", "match_data": None, "fini_states": None})
        else:
            self.controller.statut_salon = "finished"
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"status": "finished"})

    def clavier_physique(self, e):
        if self.fini_local: return
        k, c = e.keysym, e.char.upper()
        if c in ALPHABET and len(c) == 1: self.ajouter_lettre(c)
        elif k == "BackSpace": self.effacer()
        elif k in ("Return", "KP_Enter"): self.valider()

    def maj_affichage(self):
        if self.fini_local: return
        max_l = self.get_max_tape()
        if len(self.tape) > max_l: self.tape = self.tape[:max_l]
        mode = self.controller.settings_config.get("game_mode", "CLASSIQUE")
        ligne = self.labels_moi[self.ligne]
        if mode == "MYSTERE":
            if len(self.tape) > 0 and self.tape[0] == self.mot[0] and len(self.tape) == len(self.mot):
                self.tape = self.tape[1:]
            ligne[0].config(text="?", bg=KEY_BG)
            for i in range(1, len(ligne)):
                j = i - 1
                ligne[i].config(text=self.tape[j] if j < len(self.tape) else "", bg=BG)
            curseur = len(self.tape) + 1
        else:
            for i, case in enumerate(ligne):
                if i < len(self.tape): case.config(text=self.tape[i], bg=ACCENT1 if i == 0 else BG)
                else: case.config(text="", bg=BG)
            curseur = len(self.tape)
        for i, case in enumerate(ligne): case.set_curseur(i == curseur)

    # --- tailles ---
    def get_grid_sizes(self):
        try: win_h = self.winfo_toplevel().winfo_height()
        except Exception: win_h = 860
        if win_h <= 200: win_h = 860
        essais = self.controller.settings_config.get("essais", 6)
        longueur = len(getattr(self, "mot", "") or "x" * 7)
        dispo = win_h - 250 - 3 * ((50 if win_h >= 760 else 40) + 8)
        t = min(58, dispo / essais - 8, 600 / max(longueur, 5) - 8) * getattr(self, "user_zoom", 1.0)
        return int(max(24, min(70, t))), 14

    def taille_adv(self, nb):
        essais = self.controller.settings_config.get("essais", 6)
        try: win_h = self.winfo_toplevel().winfo_height()
        except Exception: win_h = 860
        if win_h <= 200: win_h = 860
        dispo = (win_h - 160) / max(1, nb) - 30
        return int(max(8, min(16, dispo / essais - 3)))

    def actualiser_tailles_grilles(self):
        main_size, _ = self.get_grid_sizes()
        if hasattr(self, "labels_moi") and self.labels_moi:
            for row in self.labels_moi:
                for t in row: t.set_taille(main_size)

    def creer_grille(self, parent, name, main):
        return self.creer_grille_sans_label(parent, main)

    def creer_grille_sans_label(self, parent, main=False):
        taille, _ = self.get_grid_sizes()
        essais = self.controller.settings_config.get("essais", 6)
        g, rows = tk.Frame(parent, bg=P["fond"]), []
        g.pack()
        for l in range(essais):
            line = [Tuile(g, taille) for _ in range(len(self.mot))]
            for c, t in enumerate(line): t.grid(row=l, column=c, padx=4, pady=4)
            rows.append(line)
        return rows

    def maj_clavier(self):
        for char, color in self.statut_lettres.items(): self.clavier.set_couleur(char, color)


class PageScoreFinal(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller, self.active_sync = controller, False
        self.lbl_haut = barre_haut(self, self.quitter_depuis_score, "Partie terminée")
        zone = Defilant(self, hauteur=200); zone.pack(fill="both", expand=True)
        self.corps = tk.Frame(zone.interieur, bg=P["fond"]); self.corps.pack(fill="both", expand=True, pady=(0, 20))
        self.lbl_rush_recap = tk.Label(self, text="")  # conservé pour la logique de récapitulatif

    def quitter_depuis_score(self): self.active_sync = False; self.controller.quitter_lobby_logic(); self.controller.controller.creer_menu_accueil()

    def recap_rush(self, d):
        recap_data = d.get("rush_recap")
        if d.get("settings", {}).get("game_mode") != "RUSH" or not recap_data: return []
        lignes = []
        if isinstance(recap_data, dict):
            for k in sorted(recap_data.keys(), key=lambda k: int(k.replace("r", "")) if k.replace("r", "").isdigit() else 0):
                if isinstance(recap_data[k], list) and recap_data[k]: lignes.append(f"Manche {k.replace('r', '')} : {', '.join(recap_data[k])}")
        elif isinstance(recap_data, list):
            for r, w in enumerate(recap_data):
                if w and isinstance(w, list): lignes.append(f"Manche {r} : {', '.join(w)}")
        return lignes

    def maj_rush_recap(self, d):
        lignes = self.recap_rush(d)
        self.lbl_rush_recap.config(text="\n".join(lignes))
        if lignes and hasattr(self, "zone_recap") and self.zone_recap.winfo_exists():
            for w in self.zone_recap.winfo_children(): w.destroy()
            etiquette(self.zone_recap, "\n".join(lignes), "texte", 14, P["texte2"], justify="center", wraplength=900).pack()

    def afficher_vainqueur(self):
        self.active_sync = True
        d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if not d: return
        p = d.get("players", {})
        if not p: return
        for w in self.corps.winfo_children(): w.destroy()
        hote = p.get(d.get("settings", {}).get("host_id"), {}).get("name", "")
        mode = d.get("settings", {}).get("game_mode", "CLASSIQUE")
        self.lbl_haut.config(text=(f"Salon de {hote.capitalize()} · " if hote else "") + f"{NOM_MODE.get(mode, mode)} · Partie terminée")
        c = tk.Frame(self.corps, bg=P["fond"]); c.pack(pady=(18, 0))
        mot = getattr(self.controller, "dernier_mot", "")
        if mot:
            etiquette(c, "Le dernier mot était", "texte", 17, P["texte2"]).pack()
            tl = tk.Frame(c, bg=P["fond"]); tl.pack(pady=(8, 12))
            for ch in mot:
                t = Tuile(tl, 46); t.config(text=ch, bg=P["bien"]); t.pack(side="left", padx=4)
        classement = sorted(p.items(), key=lambda x: x[1].get("score", 0), reverse=True)
        top = classement[0][1].get("score", 0)
        gagnants = [v["name"].capitalize() for _, v in classement if v.get("score", 0) == top]
        titre = f"{gagnants[0]} remporte la partie" if len(gagnants) == 1 else "Égalité : " + " et ".join(gagnants)
        etiquette(c, titre, "titre", 46).pack(pady=(0, 14))
        # podium
        pod = tk.Frame(c, bg=P["fond"]); pod.pack()
        ordre = [1, 0, 2] if len(classement) >= 3 else ([1, 0] if len(classement) == 2 else [0])
        hauteurs = {0: 150, 1: 110, 2: 84}
        rang_de = {}
        rang = 0
        for i, (pid, v) in enumerate(classement):
            if i > 0 and v.get("score", 0) < classement[i - 1][1].get("score", 0): rang = i
            rang_de[pid] = rang
        for k in ordre:
            if k >= len(classement): continue
            pid, v = classement[k]
            col = tk.Frame(pod, bg=P["fond"]); col.pack(side="left", anchor="s", padx=8)
            cv = tk.Canvas(col, width=190, height=hauteurs[k] + 64, bg=P["fond"], highlightthickness=0); cv.pack()
            hb = hauteurs[k]; H = hb + 64
            premier = rang_de[pid] == 0
            if premier:
                x, y = 95, H - hb - 50
                cv.create_line(x - 13, y + 7, x - 13, y - 6, x - 6, y + 1, x, y - 9, x + 6, y + 1, x + 13, y - 6, x + 13, y + 7, x - 13, y + 7, fill=P["mal"], width=2.2, joinstyle="round")
            cv.create_text(95, H - hb - 18, text=v["name"].capitalize(), fill=P["texte"], font=police("texte", 17, True))
            fill = P["mal"] if premier else P["tuile"]; fg = P["sur_mal"] if premier else P["texte"]
            arrondi(cv, 2, H - hb, 188, H + 16, 16, fill=fill, outline="")
            cv.create_text(95, H - hb + hb * 0.38, text=str(rang_de[pid] + 1), fill=fg, font=police("chiffres", 40))
            cv.create_text(95, H - hb + hb * 0.38 + 38, text=f"{nombre(v.get('score', 0))} pt" + ("s" if v.get("score", 0) > 1 else ""), fill=fg, font=police("texte", 16, True))
        # tableau
        tab = Panneau(c, padding=8, rayon=16, largeur=736, contour=P["bordure"]); tab.pack(pady=(18, 14))
        ti = tab.interieur
        def ligne(vals, entete=False, surligne=False):
            fr = tk.Frame(ti, bg=P["tuile"] if surligne else P["panneau"]); fr.pack(fill="x")
            cv = tk.Canvas(fr, width=720, height=40 if entete else 50, bg=fr["bg"], highlightthickness=0); cv.pack()
            y = 20 if entete else 25
            f = police("texte", 12, True) if entete else police("texte", 17, True)
            c1 = P["texte2"] if entete else P["texte"]
            cv.create_text(28, y, text=vals[0], anchor="w", fill=c1, font=f)
            cv.create_text(90, y, text=vals[1], anchor="w", fill=c1, font=f)
            cv.create_text(692, y, text=vals[2], anchor="e", fill=P["texte2"] if entete else P["mal"], font=f)
            if not entete: tk.Frame(ti, bg=P["bordure"], height=1).pack(fill="x")
        ligne(["#", espacer("Joueur"), espacer("Points")], entete=True)
        tk.Frame(ti, bg=P["bordure"], height=1).pack(fill="x")
        for pid, v in classement:
            moi = pid == self.controller.player_id
            ligne([str(rang_de[pid] + 1), v["name"].capitalize() + (" (vous)" if moi else ""), nombre(v.get("score", 0))], surligne=moi)
        self.zone_recap = tk.Frame(c, bg=P["fond"]); self.zone_recap.pack()
        self.maj_rush_recap(d)
        bf = tk.Frame(c, bg=P["fond"]); bf.pack(pady=(10, 0))
        self.btn_lobby = Bouton(bf, "Rejouer dans ce salon", self.retour_lobby_host, largeur=280, hauteur=56, taille=17)
        self.lbl_wait = Bouton(bf, "En attente de l'hôte…", lambda: None, largeur=280, hauteur=56, variante="discret", taille=16); self.lbl_wait.activer(False)
        (self.btn_lobby if self.controller.is_host else self.lbl_wait).pack(side="left", padx=8)
        Bouton(bf, "Retour à l'accueil", self.quitter_depuis_score, largeur=240, hauteur=56, variante="discret", taille=17).pack(side="left", padx=8)
        self.fin_gen = getattr(self, "fin_gen", 0) + 1
        self.ecouter_fin(self.fin_gen)

    def ecouter_fin(self, gen):
        if not self.active_sync or gen != self.fin_gen: return
        self.controller.fb_get_async(f"lobbies/{self.controller.lobby_code}", lambda d: self.traiter_fin(d, gen))

    def traiter_fin(self, d, gen):
        if not self.active_sync or gen != self.fin_gen: return
        if d and d.get("status") == "waiting": self.active_sync = False; self.controller.current_score = 0; self.controller.show_frame("PageLobby")
        else:
            if d and not self.lbl_rush_recap.cget("text"):
                self.maj_rush_recap(d)
            self.after(1000, lambda: self.ecouter_fin(gen))

    def retour_lobby_host(self):
        d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if d:
            self.controller.current_score = 0; p = d.get("players", {})
            for pid in p:
                p[pid]["score"] = 0
                p[pid]["rush_index"] = 0
            s = d.get("settings", {})
            s["rush_seed"] = random.randint(1000, 999999)
            self.controller.statut_salon = "waiting"
            self.controller.fb_put(f"lobbies/{self.controller.lobby_code}", {"status": "waiting", "maj": {".sv": "timestamp"}, "players": p, "settings": s, "match_data": None, "fini_states": None, "round_wins": None, "rush_recap": None})
