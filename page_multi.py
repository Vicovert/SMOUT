import tkinter as tk
from tkinter import messagebox as tkm
import json, random, os, sys, time, requests, threading, webbrowser, queue, traceback, hashlib
import design
import tkinter.font as tkfont

# --- CONFIGURATION DYNAMIQUE ---
FIREBASE_URL = "https://smout-multi-default-rtdb.europe-west1.firebasedatabase.app/"
FIREBASE_API_KEY = "AIzaSyCUliQiMhKmHZzxrMK6k35Gt0z7zBfZP3g"  # clé web publique (normal qu'elle soit dans le client)
RACINE = "v7"            # données du protocole 7 (PC et web) ; /v5 reste pour les 5.x/6.x
VERSION_JEU = "8.10"     # version du protocole multi : 8.10 = plus d'exclusion des joueurs inactifs ; seuls les joueurs 8.10+ jouent ensemble (PC et navigateur)
DELAI_ABANDON_MS = 1800000  # un salon dont plus personne ne donne signe de vie depuis 30 min peut être supprimé par n'importe qui (pas de déconnexion pour simple inactivité)

def preuve_salon(code, mot_de_passe):
    """Preuve de connaissance du mot de passe (le mot de passe lui-même n'est jamais envoyé)."""
    if not mot_de_passe: return None
    return hashlib.sha256(f"{code}:{mot_de_passe}".encode("utf-8")).hexdigest()[:32]

mot_graine = design.mot_graine

from compte import AuthFirebase  # connexion Firebase partagée avec le compte (même joueur sur tous les appareils une fois connecté)


# ===================================================================== thème
import design
from design import (Curseur, P, police, etiquette, espacer, Tuile, Bouton, BoutonLobby, Panneau, Icone, Avatar, Clavier, Stat, Chips, CarteChoix,
                    Champ, TuileAction, Interrupteur, Superposition, Stepper, TuileReglage, CarteSalon, Defilant, arrondi, melanger, fenetre_aide)

BG = ACCENT1 = ACCENT2 = MUTED = KEY_BG = TXT1 = None
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

MODES = [
    ("CLASSIQUE", "Classique", "1 point par mot trouvé"),
    ("BLAST", "Blast", "Les rapides marquent"),
    ("PRECISION", "Précision", "Peu d'essais, + de pts"),
    ("MYSTERE", "Mystère", "1re lettre cachée"),
    ("RUSH", "Rush", "Max de mots avant la fin"),
    ("ELIMINATION", "Élimination", "Le dernier est éliminé"),
    ("CHAINE", "Chaîne", "Les mots s'enchaînent"),
    ("COOP", "Coopératif", "Une grille pour tous"),
    ("PIEGE", "Mot piégé", "Choisis le mot d'un autre"),
]
NOM_MODE = {m: n for m, n, _ in MODES}
RUSHS = ("RUSH", "CHAINE")  # modes « un maximum de mots avant la fin du temps »
DELAI_REPRISE = 7200  # « Reprendre » est proposé pendant 2 h après la pause ou l'interruption (tant que le salon existe)
MAX_JOUEURS = 8  # joueurs par salon (identique au web et aux règles Firebase : index/nb ≤ 8)
TEMPS_POSSIBLES = (15, 30, 45, 60, 90, 120, 150, 180, 240, 300, 360, 420, 480, 540, 600)  # pas du réglage du temps (s)
LARGEUR_REGLAGES = 628  # largeur des réglages du salon (3 cartes de mode de 204 px)
# chaque mode a sa couleur (identique à COULEURS_MODES de smout.js) et une règle en une phrase
COULEURS_MODES = {"CLASSIQUE": "#F5B83D", "BLAST": "#FF6B6B", "PRECISION": "#4CC9F0", "MYSTERE": "#A78BFA", "RUSH": "#FF8FC7", "ELIMINATION": "#FF9F43", "CHAINE": "#2DD4BF", "COOP": "#7ED957", "PIEGE": "#5B7CFA"}
REGLES_MODES = {
    "CLASSIQUE": "Chacun cherche le mot : 1 point par mot trouvé.", "BLAST": "Les plus rapides marquent le plus de points à chaque manche.",
    "PRECISION": "Moins tu utilises d'essais, plus tu marques.", "MYSTERE": "Même la première lettre est cachée.",
    "RUSH": "Un maximum de mots avant la fin du temps.", "ELIMINATION": "Qui ne trouve pas, ou le plus lent, est éliminé. Le dernier gagne.",
    "CHAINE": "Chaque mot commence par la dernière lettre du précédent.", "COOP": "Une seule grille pour l'équipe, essais partagés.",
    "PIEGE": "Choisis en secret le mot qu'un autre joueur devra deviner. 1 point si tu trouves le tien."}
SOMBRE = "#14182A"  # texte sur les couleurs de mode


def calcul_elimination(d, manche):
    """Élimination : (éliminés de cette manche, joueurs encore en lice après la manche). Même calcul chez tous les joueurs.
    Qui n'a pas trouvé est éliminé ; si tout le monde a trouvé, le plus lent est éliminé ; si personne n'a trouvé, personne."""
    p = d.get("players") or {}; s = d.get("settings") or {}
    deja = set(s.get("elimines") or [])
    vivants = sorted(pid for pid in p if pid not in deja)
    rw = d.get("round_wins") or {}
    r = (rw.get(f"r{manche}") or {}) if isinstance(rw, dict) else {}
    trouves = {pid: t for pid, t in r.items() if pid in vivants and isinstance(t, (int, float))}
    if not trouves or len(vivants) <= 1: elim = []
    elif len(trouves) < len(vivants): elim = [pid for pid in vivants if pid not in trouves]
    else: elim = [max(trouves, key=lambda k: (trouves[k], k))]
    return elim, [pid for pid in vivants if pid not in elim]


def fusion_coop(md, essais):
    """Coopératif : propositions de tous les joueurs, dans l'ordre d'arrivée sur le serveur, limitées au nombre d'essais."""
    tout = []
    for pid, lignes in (md or {}).items():
        items = list(enumerate(lignes)) if isinstance(lignes, list) else list(lignes.items()) if isinstance(lignes, dict) else []
        for k, v in items:
            if isinstance(v, dict) and v.get("c"): tout.append((v.get("t") if isinstance(v.get("t"), (int, float)) else 9e15, pid, int(k), v))
    tout.sort(key=lambda x: (x[0], x[1], x[2]))
    return tout[:essais]

PIEGE_FIN_INFINIE = 32503680000000  # Mot piégé : fin du choix (ms, an 3000) tant que l'hôte ne l'a pas fixée : on choisit sans limite de temps


def successeur(joueurs, exclu=None, actifs=None):
    """Joueur qui reprend le rôle d'hôte : le premier arrivé dans le salon (heure d'arrivée « arrivee »), hors « exclu ».
    Même choix chez tous les joueurs (même calcul que successeur() de web/smout.js) ; None s'il n'y a personne."""
    c = [pid for pid in (actifs if actifs is not None else list(joueurs)) if pid != exclu and pid in joueurs]
    if not c: return None
    return min(c, key=lambda pid: ((joueurs.get(pid) or {}).get("arrivee") or 9e15, pid))


def disposition_adv(nb, essais, longueur, larg, haut):
    """Adversaires (mini-grilles) : (colonnes, taille de case, dense) qui remplissent au mieux la zone larg x haut (px).
    Même calcul sur PC et sur le web : 1 à 3 adversaires = nom et score à droite de la grille ; à partir de 3, le nom et le
    score passent au-dessus de la grille (« dense ») si cela permet des cases plus grandes, avec plusieurs colonnes."""
    if nb <= 0: return 1, 14, False
    plafond = {1: 30, 2: 24}.get(nb, 20)
    meilleur = None
    for dense in ((False, True) if nb >= 3 else (False,)):
        for cols in range(1, min(nb, 4) + 1):
            rangs = -(-nb // cols)
            for t in range(plafond, 5, -1):
                lb = longueur * (t + 3) + (8 if dense else 124)  # grille (+ nom / score à droite)
                hb = max(essais * (t + 3) + (52 if dense else 0), 66)
                if cols * lb + (cols - 1) * 18 <= larg and rangs * hb + (rangs - 1) * 14 <= haut:
                    if meilleur is None or t > meilleur[1]: meilleur = (cols, t, dense)
                    break
    return meilleur or (min(nb, 2), 6, nb >= 3)


def piege_paires(ordre, joueurs, manche):
    """Mot piégé : {cible: choisisseur} pour la manche (même calcul sur PC et sur le web).
    Ordre circulaire tiré au lancement ; le décalage change à chaque manche pour varier les adversaires."""
    part = [u for u in (ordre or []) if u in joueurs] + sorted(u for u in joueurs if u not in (ordre or []))
    n = len(part)
    if n < 2: return {}
    d = 1 + (int(manche) - 1) % (n - 1)
    return {part[i]: part[(i - d) % n] for i in range(n)}


def piege_reglages(ordre, joueurs, manche, graine, debut, precedent=None):
    """Réglages d'une manche de Mot piégé (écrits par l'hôte) : paires tirées au hasard à chaque manche (en évitant celles de la manche
    précédente quand c'est possible), identifiant de manche, fin du choix (infinie : l'hôte la fixe quand tous ont choisi, ou en forçant).
    Les paires sont écrites dans le salon : chaque client les lit, le tirage n'a donc pas à être identique sur PC et sur le web."""
    part = [u for u in (ordre or []) if u in joueurs] + sorted(u for u in joueurs if u not in (ordre or []))
    essais, meilleur = 0, None
    while essais < 30 and len(part) > 1:
        essais += 1
        mel = part[:]; random.shuffle(mel)
        paires = piege_paires(mel, joueurs, 1)
        meilleur = (mel, paires)
        if not precedent or len(part) < 3 or all(precedent.get(c) != ch for c, ch in paires.items()): break
    mel, paires = meilleur if meilleur else (part, {})
    return {"piege_ordre": list(mel), "piege_de": paires, "piege_id": f"p{graine}", "piege_fin_choix": PIEGE_FIN_INFINIE}


def piege_points_paire(essais_max, k):
    """(points du devineur, points du choisisseur) pour une paire : k = essai gagnant (1…), 0 si le mot n'est pas trouvé.
    Barème simple : 1 point à celui qui trouve son mot, 0 sinon ; le choisisseur ne marque rien."""
    return (1 if k > 0 else 0), 0


def piege_points(recap, uid, essais_max):
    """Total d'un joueur sur toutes les manches, recalculé à partir du récapitulatif (aucun point compté deux fois)."""
    total = 0
    for r in (recap or {}).values():
        for cible, x in (r or {}).items() if isinstance(r, dict) else []:
            if not isinstance(x, dict): continue
            dev, cho = piege_points_paire(int(essais_max), int(x.get("essais") or 0))
            if cible == uid: total += dev
            if x.get("de") == uid and not x.get("auto"): total += cho
    return total


def piege_lignes_recap(recap_manche, de_map, noms):
    """Lignes « Alice → Bob : MOT · trouvé en 3 » d'une manche (récap de fin de manche et écran final)."""
    lignes = []
    if de_map is None: de_map = {c: x.get("de") for c, x in (recap_manche or {}).items() if isinstance(x, dict)}
    for cible, cho in sorted(de_map.items(), key=lambda x: noms.get(x[1], "")):
        x = (recap_manche or {}).get(cible)
        a, b = noms.get(cho, "?").capitalize(), noms.get(cible, "?").capitalize()
        if not isinstance(x, dict): lignes.append(f"{a} → {b} : paire annulée"); continue
        k = int(x.get("essais") or 0)
        res = f"trouvé en {k}" if k else "pas trouvé"
        lignes.append(f"{a} → {b} : {x.get('mot', '?')} · {res}" + (" (mot au hasard)" if x.get("auto") else ""))
    return lignes


def apply_theme_multi(theme_data):
    """Met à jour les couleurs globales du jeu"""
    global BG, ACCENT1, ACCENT2, MUTED, KEY_BG, TXT1
    if not P: design.appliquer_theme(theme_data)
    BG, ACCENT1, ACCENT2, MUTED, KEY_BG, TXT1 = P["fond"], P["bien"], P["mal"], P["absent"], P["tuile"], P["texte"]

def resource_path(relative_path):
    return design.resource_path(relative_path)

def get_txt_color(hex_color):
    return design.contraste(hex_color, "white", "#1a1a1a")

# Thème de chaque joueur : ses couleurs sont publiées avec son pseudo (players/<uid>/theme) et dessinent SA grille chez les autres.
CLES_THEME = {"f": "fond", "v": "vide", "t": "tuile", "b": "bien", "m": "mal", "a": "absent", "x": "texte", "y": "texte_absent", "s": "sur_bien", "u": "sur_mal"}

def palette_publique():
    """Couleurs de ce thème, sous la forme compacte envoyée aux autres joueurs."""
    return {k: P[v] for k, v in CLES_THEME.items() if isinstance(P.get(v), str)}

def palette_depuis(th):
    """Palette complète d'un autre joueur à partir de ce qu'il a publié (les couleurs manquantes ou invalides gardent celles de cet appareil)."""
    pal = dict(P)
    if isinstance(th, dict):
        for k, v in CLES_THEME.items():
            c = th.get(k)
            if isinstance(c, str) and len(c) == 7 and c[0] == "#": pal[v] = c
    pal["ombre_bien"], pal["ombre_mal"] = pal["bien"], pal["mal"]
    pal["sombre"] = design.luminance(pal["fond"]) < 0.5
    return pal


def en_codes(etats):
    """États ("bien"/"mal"/"absent") -> codes neutres envoyés aux autres joueurs (B = bien placé, M = mal placé, A = absent).
    On ne déduit jamais l'état d'une couleur : un thème perso peut avoir deux couleurs identiques."""
    return [{"bien": "B", "mal": "M"}.get(e, "A") for e in etats]

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
        self.frames = {F.__name__: F(parent=self.container, controller=self) for F in (PageAccueil, PageRejoindre, PageHostSetup, PageLobby, PageJeu, PageScoreFinal)}
        for f in self.frames.values(): f.grid(row=0, column=0, sticky="nsew")
        self.vu_ok, self.salon_perdu = 0, False
        self.reponses_reseau = queue.Queue(); self.pomper_reponses()
        self.show_frame("PageAccueil"); self.controller.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.on_closing)
        self.heartbeat_active = True; self.start_heartbeat()

    def fb_get_async(self, path, callback):
        """Lit Firebase dans un thread puis appelle callback(data) dans le thread de l'interface (pas de gel de la fenêtre)."""
        def worker(): self.reponses_reseau.put((callback, self.fb_get(path)))
        threading.Thread(target=worker, daemon=True).start()

    def lire_salon(self):
        """Lit le salon courant. Si on n'y figure plus pendant 10 s (exclu après une coupure, salon fermé), on le signale."""
        code = self.lobby_code
        if not code: return None
        if not self.vu_ok: self.vu_ok = time.time()
        d = self.fb_get(f"lobbies/{code}")
        if code != self.lobby_code: return None
        if d and self.player_id in (d.get("players") or {}): self.vu_ok = time.time(); return d
        # retiré du salon (ancien client, longue mise en veille) : on s'y réinscrit tout seul, sans déconnexion
        if time.time() - getattr(self, "dernier_retour", 0) > 3:
            self.dernier_retour = time.time()
            moi = {"name": self.pseudo, "score": self.current_score, "last_seen": {".sv": "timestamp"}, "arrivee": {".sv": "timestamp"}}
            preuve = preuve_salon(code, self.settings_config.get("password", ""))
            if preuve: moi["preuve"] = preuve
            if self.fb_ok("put", f"lobbies/{code}/players/{self.player_id}", moi):
                d = self.fb_get(f"lobbies/{code}")
                if d and self.player_id in (d.get("players") or {}): self.vu_ok = time.time(); return d
        if time.time() - self.vu_ok > 10: self.salon_perdu = True  # le salon n'existe plus (ou le mot de passe a changé)
        return d

    def lire_salon_async(self, callback):
        def worker(): self.reponses_reseau.put((callback, self.lire_salon()))
        threading.Thread(target=worker, daemon=True).start()

    def pomper_reponses(self):
        if self.salon_perdu:
            self.salon_perdu, self.vu_ok, self.is_host = False, 0, False
            self.lobby_code, self.code_affiche = "", ""
            self.show_frame("PageAccueil")
            tkm.showwarning("SMOUT", "Ce salon n'existe plus.")
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

    def memoriser_partie(self):
        """Garde le salon en mémoire : si le jeu se ferme ou plante, « Reprendre la partie » permet d'y revenir."""
        if self.lobby_code:
            design.maj_config(partie_en_cours={"code": self.lobby_code, "mdp": self.settings_config.get("password", ""), "t": time.time(), "score": self.current_score})

    def oublier_partie(self): design.maj_config(partie_en_cours=None)

    def pause_partie(self):
        """Mise en pause : on garde sa place dans le salon (rien n'est supprimé) ; « Reprendre » y ramène, depuis n'importe quel
        appareil connecté au même compte. Un hôte en pause est relayé par le premier arrivé, comme un hôte inactif."""
        if not self.lobby_code: return
        self.memoriser_partie()
        self.lobby_code, self.code_affiche, self.vu_ok = "", "", 0

    def start_heartbeat(self):
        if self.heartbeat_active and self.lobby_code: self.memoriser_partie()
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
        self.vu_ok = 0; self.oublier_partie()  # départ volontaire
        code_index, self.code_affiche = self.code_affiche, ""
        def do_clean():
            try:
                data = self._requete("get", f"lobbies/{code_to_clean}")
                if data:
                    players = data.get("players", {})
                    hote = data.get("settings", {}).get("host_id") == self.player_id
                    if hote and len(players) > 1:  # on passe la main avant de partir
                        nouvel = successeur(players, self.player_id)
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
        if not path or path.endswith("/") or "//" in path: return False
        try:
            jeton = self.auth.jeton()
            if not jeton: return False
            kw = {"params": {"auth": jeton}, "timeout": timeout}
            if method in ("put", "patch"): kw["json"] = data
            return getattr(self.session, method)(f"{FIREBASE_URL}{RACINE}/{path}.json", **kw).status_code == 200
        except Exception: return False

    def ramener_au_salon(self):
        """Hôte : tout le monde retourne au salon (partie annulée, scores remis à zéro) ; les clients le voient au prochain rafraîchissement."""
        d = self.lire_salon()
        if not d: return
        self.current_score = 0; p = d.get("players", {})
        for pid in p:
            p[pid]["score"] = 0
            p[pid]["rush_index"] = 0
        s = d.get("settings", {})
        s["rush_seed"] = random.randint(1000, 999999)
        self.statut_salon = "waiting"
        self.fb_put(f"lobbies/{self.lobby_code}", {"status": "waiting", "maj": {".sv": "timestamp"}, "players": p, "settings": s, "match_data": None, "fini_states": None, "round_wins": None, "rush_recap": None,
                                                    "piege_pret": None, "piege_essais": None, "piege_verdicts": None, "piege_recap": None})

    def supprimer_salon(self, code):
        """Supprime un salon vide ou abandonné, son secret et son annonce (refusé par la base si le salon est encore actif)."""
        if self.fb_ok("delete", f"lobbies/{code}"):
            self.fb_ok("delete", f"secrets/{code}")
            self.fb_ok("delete", f"pieges/{code}")
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
        if name == "PageAccueil": f.afficher_reprise()
        elif name == "PageRejoindre": f.charger_liste()
        elif name == "PageLobby": f.entrer_lobby()
        elif name == "PageJeu": f.initialiser_partie()
        elif name == "PageScoreFinal": f.afficher_vainqueur()

    def _requete(self, method, path, data=None, timeout=2):
        """Requête REST authentifiée sous /v7. Renvoie le JSON en cas de succès, sinon None."""
        if not path or path.endswith("/") or "//" in path: return None  # salon déjà quitté : rien à lire
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
    """Multijoueur : pseudo, puis « Créer un salon » ou « Rejoindre un salon »."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", lambda: self.controller.controller.creer_menu_accueil()).pack(side="left")
        etiquette(h, "Multijoueur", "texte", 19, gras=True).pack(side="left", padx=16)
        lp = tk.Frame(h, bg=P["fond"]); lp.pack(side="right")
        etiquette(lp, "Pseudo", "texte", 14, P["texte2"]).pack(side="left", padx=(0, 10))
        self.champ_pseudo = Champ(lp, largeur=200, hauteur=42, mono=True, taille=16)
        self.champ_pseudo.set(self.controller.pseudo if self.controller.pseudo != "ANONYME" else "")
        self.champ_pseudo.var.trace_add("write", self.format_p); self.champ_pseudo.pack(side="left")
        self.sv_pseudo = self.champ_pseudo.var
        c = tk.Frame(self, bg=P["fond"]); c.place(relx=0.5, rely=0.46, anchor="center")
        self.zone_reprise = tk.Frame(c, bg=P["fond"]); self.zone_reprise.pack(fill="x")
        actions = tk.Frame(c, bg=P["fond"]); actions.pack()
        TuileAction(actions, "Créer un salon", "Choisis le mode et invite tes amis", self.creer, P["mal"], P["sur_mal"], largeur=390, hauteur=170).pack(side="left", padx=(0, 16))
        TuileAction(actions, "Rejoindre un salon", "Avec un code ou depuis la liste", self.rejoindre_page, P["bien"], P["sur_bien"], largeur=390, hauteur=170).pack(side="left")

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

    def rejoindre_page(self):
        if self.pseudo_ok(): self.controller.show_frame("PageRejoindre")

    def afficher_reprise(self):
        for w in self.zone_reprise.winfo_children(): w.destroy()
        pe = design.lire_config().get("partie_en_cours")
        if not pe or time.time() - pe.get("t", 0) > DELAI_REPRISE: return
        p = Panneau(self.zone_reprise, padding=14, largeur=796, contour=P["mal"]); p.pack(pady=(0, 18))
        i = p.interieur
        etiquette(i, f"Partie interrompue · salon {pe['code']}", "texte", 16, gras=True).pack(side="left", padx=(4, 0))
        Bouton(i, "Ignorer", lambda: (self.controller.oublier_partie(), self.afficher_reprise()), largeur=110, hauteur=44, variante="discret").pack(side="right")
        Bouton(i, "Reprendre", lambda: self.reprendre(pe), largeur=150, hauteur=44).pack(side="right", padx=10)

    def reprendre(self, pe):
        if not self.connecte(): return
        if not self.controller.frames["PageRejoindre"].rejoindre(pe["code"], pe.get("mdp", ""), silencieux=True, score=int(pe.get("score", 0) or 0)):
            self.controller.oublier_partie(); self.afficher_reprise()
            tkm.showwarning("SMOUT", "Cette partie est terminée ou le salon n'existe plus.")


class PageRejoindre(tk.Frame):
    """Rejoindre un salon : code à 4 chiffres ou liste des salons publics."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", lambda: controller.show_frame("PageAccueil")).pack(side="left")
        c = tk.Frame(self, bg=P["fond"]); c.pack(pady=(6, 0))
        etiquette(c, "Rejoindre un salon", "titre", 46).pack(anchor="w", pady=(8, 20))
        rj = Panneau(c, padding=14, largeur=748); rj.pack(anchor="w"); ri = rj.interieur
        etiquette(ri, "Code du salon", "texte", 16, gras=True).pack(side="left", padx=(6, 14))
        self.champ_code = Champ(ri, largeur=300, hauteur=50, texte_aide="CODE", mono=True, taille=22)
        self.champ_code.pack(side="left", padx=(0, 12)); self.champ_code.bind_entree(self.valider)
        self.champ_code.var.trace_add("write", lambda *a: self._filtrer_code())
        self.e = self.champ_code.e
        Bouton(ri, "Rejoindre", self.valider, largeur=150, hauteur=50, variante="tuile", taille=16).pack(side="left")
        tete = tk.Frame(c, bg=P["fond"]); tete.pack(fill="x", pady=(28, 10))
        etiquette(tete, espacer("Salons publics"), "texte", 14, P["texte2"], True).pack(side="left")
        Icone(tete, "rafraichir", self.charger_liste, 34).pack(side="right")
        self.liste = Defilant(c, largeur=748, hauteur=400); self.liste.pack(fill="x")
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

    def pseudo_ok(self): return self.controller.frames["PageAccueil"].pseudo_ok()

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
                sous = f"Code {code}" + ("  ·  mot de passe" if val.get("prive") else "")
                CarteSalon(self.lf, titre, sous, f"{val.get('nb', 1)}/{MAX_JOUEURS}", lambda c=code: self.tenter_join(c)).pack(pady=(0, 12), anchor="w")
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
        if idx.get("nb", 0) >= MAX_JOUEURS:
            tkm.showwarning("SMOUT", f"Ce salon est déjà complet (maximum {MAX_JOUEURS} joueurs)."); return
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

    def rejoindre(self, code, mdp, silencieux=False, score=None):
        uid = self.controller.player_id
        joueur = {"name": self.controller.pseudo, "score": score or 0, "last_seen": {".sv": "timestamp"}, "arrivee": {".sv": "timestamp"}}
        preuve = preuve_salon(code, mdp)
        if preuve: joueur["preuve"] = preuve
        # la base n'accepte l'inscription qu'avec la bonne preuve de mot de passe
        if not self.controller.fb_ok("put", f"lobbies/{code}/players/{uid}", joueur):
            if not silencieux: tkm.showwarning("SMOUT", "Salon introuvable")
            return False
        d = self.controller.fb_get(f"lobbies/{code}") or {}
        self.pass_view.cacher(); self.controller.is_host = False
        if len(d.get("players", {})) > MAX_JOUEURS:
            self.controller.fb_ok("delete", f"lobbies/{code}/players/{uid}")
            tkm.showwarning("SMOUT", f"Ce salon est déjà complet (maximum {MAX_JOUEURS} joueurs)."); return True
        self.controller.lobby_code, self.controller.code_affiche, self.controller.current_score = code, code, score or 0
        self.controller.reprise = score is not None  # garde ses points en revenant dans une partie en cours
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
        self.c_pub = CarteChoix(v, "Public", "Visible dans la liste des salons", lambda: self.set_vis(True), largeur=306, hauteur=74, couleur=P["succes"]); self.c_pub.pack(side="left")
        self.c_pri = CarteChoix(v, "Privé", "Seulement avec le code", lambda: self.set_vis(False), largeur=306, hauteur=74, couleur=P["mal"], icone="cadenas"); self.c_pri.pack(side="left", padx=12)
        self.inter = Interrupteur(i, "Mot de passe", False, self._mdp, largeur=600); self.inter.pack(anchor="w", pady=(26, 10))
        self.champ_mdp = Champ(i, largeur=632, hauteur=52, texte_aide="Mot de passe")
        self.e_pass = self.champ_mdp.e
        self.btn = Bouton(i, "Créer le salon", self.valider, largeur=632, hauteur=56, taille=17); self.btn.pack(pady=(24, 0))
        self.set_vis(True)

    def _mdp(self, actif):
        if actif:
            self.champ_mdp.pack(anchor="w", before=self.btn); self.champ_mdp.focus()
        else:
            self.champ_mdp.set(""); self.champ_mdp.pack_forget()

    def set_vis(self, v):
        self.is_pub = v; self.c_pub.set_selection(v); self.c_pri.set_selection(not v)

    def valider(self):
        mdp = self.champ_mdp.get().strip() if self.inter.valeur else ""
        self.controller.settings_config.update({"password": mdp, "visible": self.is_pub})
        self.controller.is_host, self.controller.lobby_code = True, ""; self.controller.show_frame("PageLobby")


class PageLobby(tk.Frame):
    """Salle d'attente : joueurs, code, mode et réglages de la partie (modifiables par l'hôte)."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller, self.active_sync = controller, False
        self.active_mode = "CLASSIQUE"
        self.lbl_role = barre_haut(self, self.quitter, "")
        zone = Defilant(self, hauteur=200); zone.pack(fill="both", expand=True)
        corps = tk.Frame(zone.interieur, bg=P["fond"]); corps.pack(fill="both", expand=True, padx=60, pady=(6, 16))
        tete = tk.Frame(corps, bg=P["fond"]); tete.pack(fill="x")
        tg = tk.Frame(tete, bg=P["fond"]); tg.pack(side="left", anchor="n")
        self.lbl_titre = etiquette(tg, "Salon", "titre", 34); self.lbl_titre.pack(anchor="w")
        self.lbl_status = etiquette(tg, "", "texte", 15, P["texte2"]); self.lbl_status.pack(anchor="w", pady=(2, 0))
        # code
        self.boite_code = Panneau(tete, padding=14, rayon=14, contour=P["mal"], tirets=True); self.boite_code.pack(side="right", anchor="n")
        bc = self.boite_code.interieur
        gauche = tk.Frame(bc, bg=bc["bg"]); gauche.pack(side="left")
        self.lbl_code_titre = etiquette(gauche, espacer("Code du salon"), "texte", 11, P["texte2"], True); self.lbl_code_titre.pack(anchor="w")
        self.lbl_code = etiquette(gauche, "----", "chiffres", 32, P["mal"]); self.lbl_code.pack(anchor="w")
        self.btn_copier = Icone(bc, "copier", self.copier, 42, cadre=True); self.btn_copier.pack(side="left", padx=(14, 0))
        # colonnes
        cols = tk.Frame(corps, bg=P["fond"]); cols.pack(fill="x", pady=(14, 0))
        pj = Panneau(cols, padding=20, largeur=332); pj.pack(side="left", anchor="n")
        etiquette(pj.interieur, "Joueurs", "texte", 17, gras=True).pack(anchor="w", pady=(0, 6))
        self.player_slots = []
        for i in range(MAX_JOUEURS):
            c = tk.Canvas(pj.interieur, width=292, height=48, bg=P["panneau"], highlightthickness=0); c.pack(pady=2)
            self.player_slots.append(c)
        ps = Panneau(cols, padding=24); ps.pack(side="left", anchor="n", padx=(22, 0), fill="x", expand=True)
        i = ps.interieur; self.panneau_partie = i
        # --- hôte : choix du mode (cartes nom + description), règle du mode choisi
        self.zone_hote = tk.Frame(i, bg=i["bg"]); zh = self.zone_hote
        etiquette(zh, espacer("Mode de jeu"), "texte", 11, P["texte2"], True).pack(anchor="w", pady=(0, 8))
        gm = tk.Frame(zh, bg=i["bg"]); gm.pack(anchor="w")
        self.cartes_mode = {}
        for k, (m, nom, desc) in enumerate(MODES):
            cc = CarteChoix(gm, nom, desc, lambda m=m: self.set_mode(m), largeur=204, hauteur=56, couleur=COULEURS_MODES[m])
            cc.grid(row=k // 3, column=k % 3, padx=(0 if k % 3 == 0 else 8, 0), pady=(0, 6)); self.cartes_mode[m] = cc
        self.lbl_regle = etiquette(zh, "", "texte", 14, COULEURS_MODES["CLASSIQUE"], True, wraplength=620, justify="left"); self.lbl_regle.pack(anchor="w", pady=(2, 0))
        # --- invité : bandeau du mode choisi par l'hôte
        self.zone_invite = tk.Frame(i, bg=i["bg"])
        self.bandeau = tk.Canvas(self.zone_invite, width=LARGEUR_REGLAGES, height=86, bg=i["bg"], highlightthickness=0); self.bandeau.pack(anchor="w")
        # --- réglages, communs : tuiles « − valeur + » pour l'hôte, les mêmes en lecture seule (sans boutons) pour les invités
        self.zone_reglages = tk.Frame(i, bg=i["bg"]); zr = self.zone_reglages; zr.pack(anchor="w", pady=(14, 0))
        etiquette(zr, espacer("Réglages de la partie"), "texte", 11, P["texte2"], True).pack(anchor="w", pady=(0, 8))
        self.grille_reglages = tk.Frame(zr, bg=i["bg"]); self.grille_reglages.pack(anchor="w")
        def tuile(lib, *a, **k): return TuileReglage(self.grille_reglages, lib, *a, commande=lambda v: self.sync_params(), **k)
        self.c_rounds = tuile("Manches", 1, 10, 3)
        self.s_time = tuile("Temps par manche", 15, 600, 180, formater=mm_ss, valeurs=TEMPS_POSSIBLES)
        self.s_essais = tuile("Essais", 4, 10, 8)
        self.c_lettres = tuile("Lettres par mot", 6, 10, (6, 7), plage=True, largeur=LARGEUR_REGLAGES)
        self.i_cache = Interrupteur(zr, "Cible cachée : on choisit son mot sans savoir pour qui", False, lambda v: self.sync_params(), largeur=LARGEUR_REGLAGES)
        self.lbl_choix = etiquette(zr, "", "texte", 14, P["texte2"], wraplength=LARGEUR_REGLAGES, justify="left")
        self.note_invite = etiquette(i, "L'hôte choisit le mode et les réglages.", "texte", 14, P["texte2"])
        self.btn_lancer = Bouton(i, "Lancer la partie", self.lancer, largeur=LARGEUR_REGLAGES, hauteur=54, taille=17); self.btn_lancer.pack(anchor="w", pady=(14, 0))
        self._placer_tuiles(False)
        self._maj_bandeau()

    # --- réglages ---
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
        self.s_essais.set_valeur(8); self.c_lettres.set_valeur(6, 7)
        temps, manches = {"MYSTERE": (180, 3), "RUSH": (120, 1), "BLAST": (60, 3), "PRECISION": (180, 3), "CLASSIQUE": (180, 3),
                          "ELIMINATION": (90, 10), "CHAINE": (150, 1), "COOP": (180, 3), "PIEGE": (180, 3)}[mode]
        self.s_time.set_valeur(temps); self.c_rounds.set_valeur(manches)
        self.update_mode_ui(mode)
        self.sync_params()

    def update_mode_ui(self, mode):
        for m, c in self.cartes_mode.items():
            if c.selection != (m == mode): c.set_selection(m == mode)
        self._maj_bandeau()

    def _maj_bandeau(self):
        """Couleur du mode partout (pastille, curseurs, bouton), règle en une ligne ; bandeau + résumé pour les invités."""
        mode = self.active_mode; mc = COULEURS_MODES.get(mode, COULEURS_MODES["CLASSIQUE"]); v = self.valeurs()
        sig = (mode, tuple(sorted(v.items())), self.controller.is_host)
        if getattr(self, "_sig_bandeau", None) == sig: return
        self._sig_bandeau = sig
        rush = mode in RUSHS
        self.lbl_regle.config(text=REGLES_MODES.get(mode, ""), fg=mc)
        self._placer_tuiles(rush)
        self.s_time.set_libelle("Temps de jeu" if rush else "Temps pour deviner" if mode == "PIEGE" else "Temps par manche")
        self.c_rounds.set_libelle("Manches max" if mode == "ELIMINATION" else "Manches")
        for w in (self.c_rounds, self.s_time, self.s_essais, self.c_lettres): w.set_couleur(mc)
        if mode == "PIEGE":
            hote = self.controller.is_host
            self.lbl_choix.config(text="Choix du mot : sans limite de temps (l'hôte peut forcer le départ)." + ("" if hote else
                (" La cible est cachée : tu ne sauras pas pour qui tu choisis." if v.get("piege_cache") else " La cible est visible : tu sais pour qui tu choisis.")))
            self.lbl_choix.pack_forget(); self.i_cache.pack_forget()
            if hote: self.i_cache.pack(anchor="w", pady=(10, 0))
            self.lbl_choix.pack(anchor="w", pady=(6 if hote else 10, 0))
        else: self.lbl_choix.pack_forget(); self.i_cache.pack_forget()
        self.btn_lancer.set_couleur(mc)
        b = self.bandeau; b.delete("all"); W, H = LARGEUR_REGLAGES, 86
        arrondi(b, 0, 0, W, H, 14, fill=mc, outline="")
        b.create_text(18, 18, text=espacer("Mode de jeu"), anchor="w", fill=melanger(SOMBRE, mc, 0.35), font=police("texte", 10, True))
        b.create_text(18, 44, text=NOM_MODE.get(mode, mode), anchor="w", fill=SOMBRE, font=police("titre", 26))
        b.create_text(18, 70, text=REGLES_MODES.get(mode, ""), anchor="w", fill=SOMBRE, font=police("texte", 13))
        if self.controller.is_host: self.btn_lancer.set_text(f"Lancer · {NOM_MODE.get(mode, mode)}" if self.controller.nb_joueurs > 1 else "En attente d'un 2e joueur…")

    def _placer_tuiles(self, rush):
        """Manches (sauf modes rush), temps et essais sur une ligne ; les lettres dessous, sur toute la largeur."""
        if getattr(self, "_rush_place", None) == rush: return
        self._rush_place = rush
        haut = [self.s_time, self.s_essais] if rush else [self.c_rounds, self.s_time, self.s_essais]
        for w in (self.c_rounds, self.s_time, self.s_essais, self.c_lettres): w.grid_forget()
        n = len(haut); lw = (LARGEUR_REGLAGES - 10 * (n - 1)) // n
        for k, w in enumerate(haut): w.set_largeur(lw); w.grid(row=0, column=k, padx=(0 if k == 0 else 10, 0), pady=(0, 10))
        self.c_lettres.grid(row=1, column=0, columnspan=n, sticky="w")

    def valeurs(self):
        mi, ma = self.c_lettres.get()
        return {"rounds": self.c_rounds.get(), "essais": self.s_essais.get(), "min": mi, "max": ma, "timer": self.s_time.get(),
                "piege_cache": bool(self.i_cache.valeur) and self.active_mode == "PIEGE"}

    def sync_params(self):
        if hasattr(self, "bandeau"): self._maj_bandeau()
        if self.controller.is_host and self.active_sync:
            sc = self.controller.settings_config
            mode = sc.get("game_mode", "CLASSIQUE")
            data = {"game_mode": mode, "host_id": self.controller.player_id, "visible": sc["visible"], "version": VERSION_JEU}
            data.update(self.valeurs())
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", data)

    # --- cycle de vie ---
    def entrer_lobby(self):
        self.active_sync = True
        if not getattr(self.controller, "reprise", False): self.controller.current_score = 0
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
                hote = {"name": ctl.pseudo, "score": 0, "last_seen": {".sv": "timestamp"}, "arrivee": {".sv": "timestamp"}}
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
        self.controller.lire_salon_async(lambda d: self.traiter_lobby(d, gen))

    def dessiner_joueur(self, c, index, nom=None, hote=False, deco=False, moi=False, donner=None):
        """donner : fonction appelée par « Donner l'hôte » (affiché pour l'hôte sur la ligne des autres joueurs)."""
        c.delete("all"); w, h = 292, 48
        if nom is None:
            c.create_oval(12, 6, 42, 42, fill=P["vide"], outline="")
            c.create_text(56, h / 2, text="Place libre", anchor="w", fill=P["texte_absent"], font=police("texte", 16, True))
            return
        coul = Avatar.COULEURS[index % len(Avatar.COULEURS)]
        arrondi(c, 0, 0, w, h, 12, fill=melanger(P["tuile"], coul, 0.16), outline="")
        arrondi(c, 0, 8, 5, h - 8, 2, fill=coul, outline="")
        c.create_oval(12, 6, 42, 42, fill=coul, outline="")
        c.create_text(27, 24, text=nom[:1].upper(), fill="#16130a", font=police("texte", 15, True))
        aff = nom.capitalize() + (" (vous)" if moi else "")
        c.create_text(56, h / 2, text=aff, anchor="w", fill=P["texte"], font=police("texte", 16, True), width=110 if donner else 160)
        if donner:  # l'hôte peut passer la main à ce joueur
            c.create_text(w - 12, h / 2, text="Donner l'hôte", anchor="e", fill=P["mal"], font=police("texte", 13, True), tags="donner")
            c.tag_bind("donner", "<ButtonRelease-1>", lambda e=None: donner())
            c.tag_bind("donner", "<Enter>", lambda e=None: c.config(cursor="hand2")); c.tag_bind("donner", "<Leave>", lambda e=None: c.config(cursor=""))
        if deco and not donner: c.create_text(w - 14, h / 2, text="Déconnecté", anchor="e", fill=P["danger"], font=police("texte", 14))
        elif hote:
            c.create_text(w - 14, h / 2, text="Hôte", anchor="e", fill=P["mal"], font=police("texte", 15, True))
            x = w - 66; y = h / 2
            c.create_line(x - 9, y + 5, x - 9, y - 4, x - 4, y + 1, x, y - 6, x + 4, y + 1, x + 9, y - 4, x + 9, y + 5, x - 9, y + 5, fill=P["mal"], width=1.8, joinstyle="round")

    def donner_hote(self, pid, nom):
        """L'hôte passe son rôle à un autre joueur du salon (après confirmation)."""
        if not self.controller.is_host: return
        if not tkm.askyesno("SMOUT", f"Donner le rôle d'hôte à {nom.capitalize()} ?\nC'est lui qui choisira le mode et lancera la partie."): return
        ctl = self.controller
        if ctl.fb_ok("patch", f"lobbies/{ctl.lobby_code}/settings", {"host_id": pid}):
            ctl.is_host = False; ctl.fb_patch(f"index/{ctl.code_affiche}", {"owner": pid})
            self._vue_hote = None; self._sig_bandeau = None

    def traiter_lobby(self, d, gen):
        if not self.active_sync or gen != self.lobby_gen: return
        if d:
            s, p = d.get("settings", {}), d.get("players", {})
            server_now = max([pdat.get("last_seen", 0) for pdat in p.values()] + [0])
            if not p: self.quitter(); return
            # un joueur inactif reste dans le salon (affiché « Déconnecté ») : pas d'exclusion pour inactivité
            actifs = [pid for pid, pdat in p.items() if not server_now or server_now - pdat.get("last_seen", 0) <= 25000] or list(p)
            hid = s.get("host_id")
            if hid not in actifs:  # hôte parti ou inactif : le premier arrivé des joueurs actifs prend le relais (même choix chez tous)
                hid = successeur(p, None, actifs)
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
                self.c_lettres.set_valeur(s.get("min", 6), s.get("max", 7)); self.s_time.set_valeur(s.get("timer", 180))
                self.i_cache.valeur = bool(s.get("piege_cache")); self.i_cache._dessiner()

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
                    moi = pid == self.controller.player_id
                    donner = (lambda pid=pid, n=p[pid]["name"]: self.donner_hote(pid, n)) if (self.controller.is_host and not moi and pid != hid) else None
                    self.dessiner_joueur(slot, i, p[pid]["name"], pid == hid, deco, moi, donner)
                else: self.dessiner_joueur(slot, i)
            n = len(p)
            self.lbl_status.config(text=f"En attente des joueurs · {n} sur {MAX_JOUEURS}" + ("  ·  salon privé" if not self.controller.settings_config.get("visible", True) else ""))
            hote = self.controller.is_host
            for sw in [self.c_rounds, self.s_essais, self.c_lettres, self.s_time] + list(self.cartes_mode.values()): sw.activer(hote)
            self._maj_bandeau()
            if hote != getattr(self, "_vue_hote", None):  # l'hôte règle la partie, les invités voient le résumé
                self._vue_hote = hote
                if hote:
                    self.zone_invite.pack_forget(); self.note_invite.pack_forget(); self.zone_hote.pack(anchor="w", before=self.zone_reglages)
                else:
                    self.zone_hote.pack_forget(); self.zone_invite.pack(anchor="w", before=self.zone_reglages)
                    self.note_invite.pack(anchor="w", pady=(12, 0), before=self.btn_lancer)
            if hote:
                self.btn_lancer.set_variante("principal" if n > 1 else "tuile"); self._sig_bandeau = None; self._maj_bandeau()
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
            "visible": sc.get("visible", True), "piege_cache": bool(v.get("piege_cache")),
            "start_time": time.time() + self.controller.server_time_offset
        }
        if mode == "PIEGE":  # ordre circulaire tiré au hasard, puis paires « qui choisit pour qui » de la 1re manche
            d = self.controller.lire_salon() or {}
            pl = d.get("players") or {}; now_ms = max([v.get("last_seen", 0) for v in pl.values()] + [0])
            joueurs = [pid for pid, v in pl.items() if now_ms - v.get("last_seen", 0) <= 25000] or [self.controller.player_id]
            ordre = random.sample(joueurs, len(joueurs))
            new_settings.update(piege_reglages(ordre, joueurs, 1, rush_seed, new_settings["start_time"]))
        self.controller.settings_config.update(new_settings)
        self.controller.statut_salon = "playing"; self.controller.maj_index()
        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"status": "playing", "settings": new_settings, "match_data": None, "fini_states": None, "round_wins": None, "rush_recap": None,
                                                                           "piege_pret": None, "piege_essais": None, "piege_verdicts": None, "piege_recap": None})


class Adversaire(tk.Frame):
    """Mini-grille d'un adversaire + nom, score et avancement (dense : nom et score au-dessus de la grille, pour les salons nombreux)."""
    def __init__(self, parent, nom, essais, longueur, taille=14, index=0, dense=False):
        super().__init__(parent, bg=P["fond"])
        self.taille, self.index, self.dense, self.pal, self._th = taille, index, dense, None, None
        if dense:
            info = tk.Frame(self, bg=P["fond"]); info.pack(side="top", anchor="w", pady=(0, 3))
            self.zone = tk.Frame(self, bg=P["fond"]); self.zone.pack(side="top", anchor="w")
            self.grille = []
            self.construire(essais, longueur)
            self.lbl_nom = etiquette(info, nom, "texte", 14, gras=True); self.lbl_nom.pack(side="left")
            self.lbl_score = etiquette(info, "0", "chiffres", 15, P["mal"]); self.lbl_score.pack(side="left", padx=(8, 0))
            self.lbl_etat = etiquette(self, "", "texte", 12, P["texte2"]); self.lbl_etat.pack(side="top", anchor="w")
            self.lbl_mot = etiquette(self, "", "texte", 12, P["mal"], True); self.lbl_mot.pack(side="top", anchor="w")
            return
        self.zone = tk.Frame(self, bg=P["fond"]); self.zone.pack(side="left", anchor="n")
        self.grille = []
        self.construire(essais, longueur)
        info = tk.Frame(self, bg=P["fond"]); info.pack(side="left", anchor="n", padx=(16, 0))
        self.lbl_nom = etiquette(info, nom, "texte", 17, gras=True); self.lbl_nom.pack(anchor="w")
        self.lbl_score = etiquette(info, "0", "chiffres", 22, P["mal"]); self.lbl_score.pack(anchor="w")
        self.lbl_etat = etiquette(info, "", "texte", 14, P["texte2"]); self.lbl_etat.pack(anchor="w")
        self.lbl_mot = etiquette(info, "", "texte", 14, P["mal"], True); self.lbl_mot.pack(anchor="w", pady=(4, 0))  # Mot piégé : le mot qu'on lui a choisi
    def construire(self, essais, longueur):
        for w in self.zone.winfo_children(): w.destroy()
        self.grille = []
        for r in range(essais):
            ligne = []
            for c in range(longueur):
                t = Tuile(self.zone, self.taille, rayon=3, mini=True); t.config(bg=KEY_BG); t.grid(row=r, column=c, padx=1.5, pady=1.5); ligne.append(t)
                if self.pal: tk.Canvas.configure(t, bg=self.pal["fond"]); t.set_palette(self.pal); t.config(bg=self.pal["tuile"])
            self.grille.append(ligne)

    def set_theme(self, th):
        """Dessine cette grille avec le thème du joueur (th = ce qu'il a publié)."""
        if th == self._th: return
        self._th = th; self.pal = palette_depuis(th)
        self.zone.config(bg=self.pal["fond"], padx=4, pady=4)
        for ligne in self.grille:
            for t in ligne: tk.Canvas.configure(t, bg=self.pal["fond"]); t.set_palette(self.pal); t.config(bg=self.pal["tuile"])


class PageJeu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller, self.active_sync = controller, False
        self.user_zoom = self.me_charger_zoom()
        self.sync_gen = 0
        self._frappe_prog, self._frappe_env, self._frappe_voulue = None, None, ""  # frappe en direct (Mot piégé)
        # En-tête
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        gf = tk.Frame(h, bg=P["fond"]); gf.pack(side="left")
        Icone(gf, "retour", self.quitter_jeu).pack(side="left")
        # 9.0 : bouton de l'hôte « Lobby » en haut à gauche (ramène tous les joueurs au salon, après confirmation)
        self.btn_salon = BoutonLobby(gf, self.retour_salon_hote); self.btn_salon_visible = False
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
            if getattr(self, "clavier", None) and self.clavier.winfo_exists(): self.clavier.set_zoom(self.user_zoom)  # le clavier suit la taille de la grille
    def on_resize(self, e):
        if e.widget == self:
            if abs(e.height - getattr(self, "_last_h", 0)) > 30:
                self._last_h = e.height; self.actualiser_tailles_grilles()

    def maj_bouton_salon(self):
        """L'hôte peut ramener tout le monde au salon en cours de partie (avec confirmation)."""
        if self.controller.is_host != self.btn_salon_visible:
            self.btn_salon_visible = self.controller.is_host
            if self.btn_salon_visible: self.btn_salon.pack(side="left", padx=(8, 0))
            else: self.btn_salon.pack_forget()

    def retour_salon_hote(self):
        if not self.controller.is_host: return
        if not tkm.askyesno("Retour au salon", "Ramener tous les joueurs au salon ?\nLa partie en cours sera annulée."): return
        self.controller.ramener_au_salon()

    def quitter_jeu(self):
        """Retour pendant la partie : mettre en pause (on garde sa place et on revient par « Reprendre ») ou quitter définitivement."""
        if getattr(self, "fen_quitter", None) is not None and self.fen_quitter.winfo_exists() and self.fen_quitter.winfo_ismapped(): return
        o = Superposition(self, largeur=500); i = o.interieur; self.fen_quitter = o
        etiquette(i, "Quitter la partie ?", "titre", 26).pack(anchor="w")
        etiquette(i, "En pause, tu gardes ta place dans le salon : « Reprendre » (accueil du multijoueur) te ramène dans la partie, "
                     "aussi depuis un autre appareil connecté à ton compte.", "texte", 14, P["texte2"], wraplength=440, justify="left").pack(anchor="w", pady=(6, 18))
        bf = tk.Frame(i, bg=i["bg"]); bf.pack(anchor="e")
        Bouton(bf, "Continuer", o.cacher, largeur=120, variante="discret").pack(side="left", padx=(0, 8))
        Bouton(bf, "Quitter la partie", lambda: (o.cacher(), self.quitter_definitif()), largeur=170, variante="secondaire").pack(side="left", padx=(0, 8))
        Bouton(bf, "Mettre en pause", lambda: (o.cacher(), self.mettre_en_pause()), largeur=170).pack(side="left")
        o.montrer()

    def quitter_definitif(self): self.active_sync, self.timer_actif = False, False; self.winfo_toplevel().unbind("<Key>"); self.controller.quitter_lobby_logic(); self.controller.controller.creer_menu_accueil()

    def mettre_en_pause(self):
        self.active_sync, self.timer_actif = False, False; self.winfo_toplevel().unbind("<Key>")
        self.controller.pause_partie(); self.controller.show_frame("PageAccueil")

    # --- construction d'une manche ---
    def initialiser_partie(self):
        self.sync_gen = getattr(self, "sync_gen", 0) + 1  # invalide les boucles du round précédent
        self.active_sync, self.last_sync_data, self.timer_actif = False, None, False; self.btn_next.pack_forget()
        [w.destroy() for w in self.moi_side.winfo_children() + self.adv_container.winfo_children() + self.zone_clavier.winfo_children()]
        self.lbl_msg.config(text=""); self.btn_def.pack_forget()

        dm = self.controller.lire_salon()
        if dm and "settings" in dm:
            self.controller.settings_config.update(dm["settings"])
        conf = self.controller.settings_config
        mode = conf.get("game_mode", "CLASSIQUE")
        self.controller.settings_config["game_mode"] = mode

        mi, ma = conf.get("min", 6), conf.get("max", 10)
        f_list = sorted([m for m in self.controller.liste_mots if mi <= len(m) <= ma] or self.controller.liste_mots)
        rush_seed = conf.get("rush_seed", 12345)
        if mode == "CHAINE": self.rush_words = design.mots_chaine(f_list, rush_seed)  # même calcul sur PC et sur le web
        else: self.rush_words = [mot_graine(f_list, rush_seed, i) for i in range(100)]
        self.rush_index = 0
        if mode in RUSHS:
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"rush_index": 0})

        self.mot = self.rush_words[0]  # recalculé depuis la graine partagée (le mot n'est pas dans la base)
        self.controller.dernier_mot = self.mot
        self.round_actuel = conf.get("round_num", 1)
        self.start_time_round = conf.get("start_time", time.time())
        reprise = getattr(self.controller, "reprise", False); self.controller.reprise = False
        if int(self.round_actuel) == 1 and not reprise:
            self.controller.current_score = 0
            self.blast_scored_rounds = set()
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": 0})
        elif not hasattr(self, 'blast_scored_rounds'):
            self.blast_scored_rounds = set()
        self.elimine = False
        if mode == "ELIMINATION":  # 1 point par manche survécue
            self.elimine = self.controller.player_id in (conf.get("elimines") or [])
            if int(self.round_actuel) > 1 and not self.elimine:
                self.controller.current_score = int(self.round_actuel) - 1
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score})
        self.coop_n, self.coop_attente, self.coop_md, self.coop_sig = 0, [], {}, None
        self.piege = mode == "PIEGE"
        if self.piege: self.piege_init(conf)

        self.ligne, self.fini_local, self.temps_restant = 0, False, conf.get("timer", 180)
        self.tape = [] if mode == "MYSTERE" else [self.mot[0]]
        self.statut_lettres = {l: None for l in ALPHABET}
        self.lbl_info.config(text=f"{NOM_MODE.get(mode, mode)} · {len(self.mot)} lettres")
        self.s_manche.set(str(self.round_actuel), suffixe=f" / {conf.get('rounds', 1)}")
        self.s_score.set(nombre(self.controller.current_score))

        self.labels_moi = self.creer_grille(self.moi_side, "", True)
        try: hf = self.winfo_toplevel().winfo_height()
        except Exception: hf = 860
        self.clavier = Clavier(self.zone_clavier, self.ajouter_lettre, self.effacer, self.valider, hauteur=50 if hf >= 760 or hf < 200 else 40, zoom=self.user_zoom); self.clavier.pack()

        hid = dm.get("settings", {}).get("host_id") if dm else None
        self.adv_widgets, self.adv_grids, self.adv_last_word_len = {}, {}, {}
        if dm:
            opponents = [item for item in dm.get("players", {}).items() if item[0] != self.controller.player_id]
            cols, t_adv, dense = self.taille_adv(len(opponents))
            for idx, (pid, p) in enumerate(opponents):
                a = Adversaire(self.adv_container, p["name"].capitalize(), conf.get("essais", 6), len(self.mot), t_adv, idx + 1, dense)
                a.grid(row=idx // cols, column=idx % cols, sticky="nw", padx=(0 if idx % cols == 0 else 18, 0), pady=(0, 14 if len(opponents) > 2 else 26))
                self.adv_widgets[pid] = a; self.adv_grids[pid] = a.grille; self.adv_last_word_len[pid] = len(self.mot)
                if isinstance(p.get("theme"), dict): a.set_theme(p["theme"])
        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"theme": palette_publique(), "frappe": None})  # mon thème, pour les autres joueurs
        self._frappe_env, self._frappe_voulue = None, ""

        if self.piege: self.piege_demarrer(dm)
        gen = self.sync_gen
        self.active_sync, self.timer_actif = True, True; self.update_timer(gen)
        threading.Thread(target=self.bg_sync, args=(gen,), daemon=True).start(); self.ui_loop(gen)
        self.winfo_toplevel().bind("<Key>", self.clavier_physique); self.maj_affichage()
        if self.elimine:  # spectateur jusqu'à la fin de la partie
            self.fini_local = True; self.winfo_toplevel().unbind("<Key>")
            for case in self.labels_moi[0]: case.set_curseur(False)
            for w in self.zone_clavier.winfo_children(): w.destroy()
            self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/fini_states/{self.controller.player_id}", True)
            self.lbl_msg.config(text="Tu es éliminé : tu regardes la fin de la partie", fg=P["texte2"])

    def recreer_grille_adv(self, pid, word_len):
        a = self.adv_widgets.get(pid)
        if a:
            a.construire(self.controller.settings_config.get("essais", 6), word_len)
            self.adv_grids[pid] = a.grille; self.adv_last_word_len[pid] = word_len

    def boucle_valide(self, gen):
        return self.active_sync and gen == getattr(self, "sync_gen", 0)

    def bg_sync(self, gen):
        while self.boucle_valide(gen):
            d = self.controller.lire_salon()
            if d and gen == self.sync_gen: self.last_sync_data = d
            time.sleep(0.35 if getattr(self, "piege", False) else 0.8)  # Mot piégé : le verdict d'un essai passe par un autre joueur, on rafraîchit plus vite

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
        self.maj_bouton_salon()
        if d.get("status") == "waiting":  # l'hôte a ramené tout le monde au salon
            self.active_sync, self.timer_actif = False, False; self.winfo_toplevel().unbind("<Key>"); self.controller.show_frame("PageLobby"); return
        if d.get("status") == "finished":
            sf = d.get("settings", {})
            if sf.get("game_mode") == "ELIMINATION" and self.controller.player_id not in (sf.get("elimines") or []):
                self.controller.current_score = int(sf.get("current_round", 1))  # a survécu jusqu'au bout
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score})
            self.active_sync = False; self.winfo_toplevel().unbind("<Key>"); self.controller.show_frame("PageScoreFinal"); return
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
            nouvel_hote = successeur(p, None, active_pids)  # le premier arrivé, même choix chez tous les joueurs
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
        if mode in RUSHS:
            self.lbl_info.config(text=f"{NOM_MODE[mode]} · mot n° {self.rush_index + 1} · {len(self.mot)} lettres")

        fs = d.get("fini_states") or {}
        md = d.get("match_data", {}) or {}
        for pid, a in list(self.adv_widgets.items()):
            deco = not (pid in p and (server_now == 0 or (server_now - p[pid].get("last_seen", 0))/1000 <= 12))
            pdat = p.get(pid, {})
            nom = pdat.get("name", a.lbl_nom.cget("text")).capitalize() + (" ♛" if pid == hid else "")
            if a.lbl_nom.cget("text") != nom: a.lbl_nom.config(text=nom)
            if isinstance(pdat.get("theme"), dict): a.set_theme(pdat["theme"])  # sa grille garde SES couleurs
            a.lbl_score.config(text=nombre(pdat.get("score", 0) if isinstance(pdat.get("score", 0), (int, float)) else 0))
            # avancement
            lignes = md.get(pid) or {}
            items = list(enumerate(lignes)) if isinstance(lignes, list) else [(int(k), v) for k, v in lignes.items() if str(k).isdigit()] if isinstance(lignes, dict) else []
            items = [(i, v) for i, v in items if v]
            if mode in RUSHS:
                adv_idx = pdat.get("rush_index", pdat.get("score", 0)) or 0
                items = [(i, v) for i, v in items if v.get("w_idx") == adv_idx]
            trouve = any(c and all(x == "B" for x in c) for c in ((v.get("c") or [])[1 if mode == "MYSTERE" else 0:] for _, v in items))  # Mystère : la case 0 (lettre cachée) est toujours "A"
            if deco: etat, coul = "Déconnecté", P["danger"]
            elif mode == "ELIMINATION" and pid in (s.get("elimines") or []): etat, coul = "Éliminé", P["texte2"]
            elif mode == "COOP": etat, coul = f"{len(items)} proposition" + ("s" if len(items) > 1 else ""), P["texte2"]
            elif mode == "PIEGE" and not fs.get(pid): etat, coul = self.piege_etat_adv(pid, d, len(items)), P["texte2"]
            elif mode in RUSHS:
                adv_idx = pdat.get("rush_index", pdat.get("score", 0)) or 0
                etat, coul = f"Mot n° {adv_idx + 1}", P["texte2"]
                if adv_idx < self.rush_index:
                    mot_adv = self.rush_words[adv_idx] if adv_idx < len(self.rush_words) else "?"
                    etat = f"Mot n° {adv_idx + 1} · {mot_adv}"
            elif fs.get(pid): etat, coul = (f"Trouvé en {len(items)}", P["succes"]) if trouve else ("Pas trouvé", P["texte2"]), None
            else: etat, coul = f"Essai {min(len(items) + 1, s.get('essais', 6))}", P["texte2"]
            if isinstance(etat, tuple): etat, coul = etat
            a.lbl_etat.config(text=etat, fg=coul or P["texte2"])

        if mode == "COOP": self.coop_md = md; self.rendre_coop()
        if self.piege: self.piege_tick(d, s, p, active_pids, fs)
        round_over = (sum(1 for pid in active_pids if fs.get(pid)) >= len(active_pids)) or (self.temps_restant <= 0)
        if self.piege and round_over and not self.piege_recaps_complets(d, active_pids): round_over = False
        fc = sum(1 for pid in active_pids if fs.get(pid))
        if round_over: self.timer_actif = False
        for pid in list(self.adv_grids.keys()):
            if self.piege:  # chaque joueur devine un mot de longueur différente
                n_adv = ((d.get("piege_pret") or {}).get(pid) or {}).get("n")
                if isinstance(n_adv, int) and self.adv_last_word_len.get(pid) != n_adv: self.recreer_grille_adv(pid, n_adv)
            if mode in RUSHS and hasattr(self, "rush_words"):
                adv_idx = p.get(pid, {}).get("rush_index", p.get(pid, {}).get("score", 0))
                if adv_idx < len(self.rush_words):
                    exp_len = len(self.rush_words[adv_idx])
                    if self.adv_last_word_len.get(pid) != exp_len:
                        self.recreer_grille_adv(pid, exp_len)
            grid = self.adv_grids[pid]
            pal = getattr(self.adv_widgets.get(pid), "pal", None)
            vide = pal["tuile"] if pal else KEY_BG
            code_coul = (lambda c: {"B": pal["bien"], "M": pal["mal"]}.get(c, pal["absent"])) if pal else couleur_code
            cible = [[("", vide) for _ in row] for row in grid]
            nb_lignes = 0
            if pid in md:
                data_p = md[pid]
                adv_idx = p.get(pid, {}).get("rush_index", p.get(pid, {}).get("score", 0))
                show_letters = (adv_idx < self.rush_index) if mode in RUSHS else (self.fini_local or mode in ("COOP", "PIEGE"))  # Mot piégé : on voit les lettres de tout le monde
                lignes = list(enumerate(data_p)) if isinstance(data_p, list) else list(data_p.items()) if isinstance(data_p, dict) else []
                for l_idx, content in lignes:
                    try: idx = int(l_idx)
                    except (ValueError, TypeError): continue
                    if not content or idx >= len(grid): continue
                    if mode in RUSHS and content.get("w_idx") != adv_idx: continue
                    nb_lignes = max(nb_lignes, idx + 1)
                    for c_idx, code in enumerate(content.get("c", [])):
                        if c_idx < len(grid[idx]): cible[idx][c_idx] = ("", code_coul(code))
                    if show_letters:
                        for c_idx, char in enumerate(content.get("l", [])):
                            if c_idx < len(grid[idx]): cible[idx][c_idx] = (char, cible[idx][c_idx][1])
            if mode == "PIEGE" and not fs.get(pid) and nb_lignes < len(grid):  # frappe en direct : la ligne qu'il est en train de remplir
                frappe = p.get(pid, {}).get("frappe")
                if isinstance(frappe, str):
                    for c_idx, char in enumerate(frappe[:len(grid[nb_lignes])]): cible[nb_lignes][c_idx] = (char, code_coul("B") if c_idx == 0 else vide)
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
                if self.piege:
                    noms = {pid: v.get("name", "?") for pid, v in p.items()}
                    msg_text = "\n".join(piege_lignes_recap(((d.get("piege_recap") or {}).get(f"r{self.round_actuel}") or {}), self.piege_de, noms))
                if mode == "BLAST":
                    sorted_wins = self.points_blast(d)
                    pts_map = {0: 4, 1: 3, 2: 2, 3: 1}
                    parts = [f"{p.get(w_pid, {}).get('name', 'Joueur').capitalize()} +{pts_map.get(rank, 0)}" for rank, (w_pid, _) in enumerate(sorted_wins) if rank in pts_map]
                    if parts: msg_text += "\n" + "   ·   ".join(parts)
                derniere = int(s['current_round']) >= int(s['rounds'])
                if mode == "ELIMINATION":
                    elim, vivants = calcul_elimination(d, int(s.get("current_round", 1)))
                    noms = ", ".join(p.get(x, {}).get("name", "?").capitalize() for x in elim)
                    msg_text += f"\nÉliminé{'s' if len(elim) > 1 else ''} : {noms}" if elim else "\nPersonne n'est éliminé"
                    derniere = derniere or len(vivants) <= 1
                if self.lbl_msg.cget("text") != msg_text: self.lbl_msg.config(text=msg_text, fg=P["mal"])
                if self.controller.is_host and not self.btn_next.winfo_ismapped():
                    self.btn_next.set_text("Voir les résultats" if derniere else "Manche suivante")
                    self.btn_next.pack(pady=(4, 10), before=self.zone_clavier)
            else:
                t = ("Tu es éliminé : tu regardes la fin de la partie\n" if self.elimine else "") + f"En attente des autres joueurs ({fc}/{len(active_pids)})"
                if self.lbl_msg.cget("text") != t: self.lbl_msg.config(text=t, fg=P["texte2"])

    # --- Mot piégé : chaque joueur choisit le mot de sa cible, puis devine celui qu'on lui a choisi ---------------------
    # Le mot n'est jamais lisible par celui qui le devine (règles Firebase) : ses essais sont évalués par son
    # choisisseur, ou, s'il est parti, par le premier autre joueur présent, qui révèle aussi le mot en fin de paire.
    def piege_fin_connue(self): return self.piege_fin < 3e10  # la fin du choix est fixée (tous ont choisi, ou l'hôte a forcé)

    def piege_init(self, conf):
        me = self.controller.player_id
        self.piege_de = dict(conf.get("piege_de") or {})
        self.piege_id = conf.get("piege_id", "")
        self.piege_fin = float(conf.get("piege_fin_choix") or PIEGE_FIN_INFINIE) / 1000
        self.lbl_piege_etat = None
        self.piege_cible = next((t for t, c in self.piege_de.items() if c == me), None)
        self.piege_mots, self.piege_lectures, self.piege_envoyes, self.piege_recaps = {}, {}, set(), set()
        self.piege_secours, self.piege_essais_txt, self.piege_pret_envoye = set(), {}, {}
        self.choix, self.choix_envoi, self.attente_verdict, self.mot_reel = [], False, None, ""
        self.piege_premiere, self.piege_n, self.piege_attente_recap = "", 0, None
        self.piege_mon_mot, self.lbl_mon_mot = "", None  # le mot qu'on a choisi pour sa cible (on ne voit jamais ceux des autres)
        self.phase = "choix" if (self.piege_cible and me in self.piege_de) else "spectateur"
        self.mot = "?" * int(conf.get("max", 7)); self.controller.dernier_mot = ""

    def piege_noms(self, d=None):
        d = d or self.last_sync_data or self.controller.lire_salon() or {}
        return {pid: v.get("name", "?") for pid, v in (d.get("players") or {}).items()}

    def piege_vider(self):
        for w in self.moi_side.winfo_children(): w.destroy()
        self.labels_moi = []

    def piege_demarrer(self, d):
        me, d = self.controller.player_id, d or {}
        if self.phase == "spectateur":
            self.piege_vider(); self.fini_local = True
            self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/fini_states/{me}", True)
            self.lbl_msg.config(text="Tu regardes cette manche", fg=P["texte2"]); return
        pret = d.get("piege_pret") or {}
        if pret.get(self.piege_cible): self.phase = "attente"  # reprise : le mot de notre cible est déjà choisi
        if self.phase == "attente" and isinstance(pret.get(me), dict) and self.piege_fin_connue(): self.piege_devine(pret[me], d)
        elif self.phase == "attente": self.piege_construire_attente()
        else: self.piege_construire_choix(d)

    def piege_construire_choix(self, d=None):
        self.piege_vider()
        conf = self.controller.settings_config; mi, ma = int(conf.get("min", 6)), int(conf.get("max", 7))
        cache = bool(conf.get("piege_cache"))  # option du salon : on ne sait pas pour qui on choisit
        nom = "un autre joueur" if cache else self.piege_noms(d).get(self.piege_cible, "?").capitalize()
        self.lbl_info.config(text=f"{NOM_MODE['PIEGE']} · choisis le mot de {nom}" if not cache else f"{NOM_MODE['PIEGE']} · choisis un mot pour un autre joueur")
        etiquette(self.moi_side, f"Choisis le mot que {nom} devra deviner" if not cache else "Choisis le mot que devra deviner un autre joueur (tu ne sais pas qui)", "texte", 19, gras=True).pack()
        aide = self.piege_texte_longueur(mi, ma) + (" (cases en pointillé facultatives)" if ma > mi else "")
        etiquette(self.moi_side, aide + " · un mot du dictionnaire · gardé secret · pas de limite de temps", "texte", 14, P["texte2"], wraplength=520, justify="center").pack(pady=(2, 10))
        rg = tk.Frame(self.moi_side, bg=P["fond"]); rg.pack()
        taille, _ = self.get_grid_sizes()
        self.labels_choix = [Tuile(rg, taille) for _ in range(ma)]
        self.labels_moi, self.ligne = [self.labels_choix], 0
        self.piege_rendre_choix()
        self.piege_zone_hote()

    def piege_texte_longueur(self, mi, ma):
        return f"{mi} lettres" if mi == ma else f"{mi} ou {ma} lettres" if ma == mi + 1 else f"de {mi} à {ma} lettres"

    def piege_rendre_choix(self):
        mi, ma = int(self.controller.settings_config.get("min", 6)), int(self.controller.settings_config.get("max", 7))
        for i, t in enumerate(getattr(self, "labels_choix", [])):  # cases au-delà du minimum : facultatives (en pointillé)
            t.grid(row=0, column=i, padx=4, pady=4)
            txt = self.choix[i] if i < len(self.choix) else ""
            if t.cget("text") != txt: t.config(text=txt, bg=BG)
            t.set_pointilles(i >= mi)
            t.set_curseur(i == len(self.choix) and not self.choix_envoi)

    def piege_construire_attente(self, texte="Mot envoyé ✓"):
        self.piege_vider()
        etiquette(self.moi_side, texte, "titre", 26).pack(pady=(30, 6))
        etiquette(self.moi_side, "En attente des autres joueurs…", "texte", 15, P["texte2"]).pack()
        self.piege_maj_mon_mot()
        self.piege_zone_hote()

    def piege_zone_hote(self):
        """Avancement du choix des mots, et pour l'hôte le bouton qui force le démarrage (mot au hasard pour ceux qui n'ont pas choisi)."""
        self.lbl_piege_etat = etiquette(self.moi_side, "", "texte", 14, P["texte2"]); self.lbl_piege_etat.pack(pady=(14, 0))
        self.btn_forcer = Bouton(self.moi_side, "Forcer le démarrage", self.piege_forcer, largeur=240, hauteur=44, variante="discret")
        self.btn_forcer_visible = False
        self.piege_maj_etat()

    def piege_maj_etat(self, d=None):
        if not getattr(self, "lbl_piege_etat", None) or not self.lbl_piege_etat.winfo_exists(): return
        pret = ((d or self.last_sync_data or {}).get("piege_pret")) or {}
        txt = f"{sum(1 for t in self.piege_de if t in pret)} sur {len(self.piege_de)} mots choisis"
        if self.piege_fin_connue(): txt += " · c'est parti !"
        self.lbl_piege_etat.config(text=txt)
        voir = self.controller.is_host and not self.piege_fin_connue()  # seul l'hôte peut forcer le démarrage
        if voir != self.btn_forcer_visible:
            self.btn_forcer_visible = voir
            if voir: self.btn_forcer.pack(pady=(10, 0))
            else: self.btn_forcer.pack_forget()

    def piege_frappe(self):
        """Mot piégé, devinette : publie (au plus 5 fois par seconde) la ligne en cours de frappe, pour que les autres la voient en direct."""
        if not (self.piege and getattr(self, "phase", "") == "devine"): return
        txt = "".join(self.tape) if (self.attente_verdict is None and not self.fini_local) else ""
        self._frappe_voulue = txt
        if self._frappe_prog is None and txt != self._frappe_env:
            try: self._frappe_prog = self.after(200, self._frappe_envoyer)
            except tk.TclError: pass

    def _frappe_envoyer(self):
        self._frappe_prog = None
        if self._frappe_voulue != self._frappe_env and self.active_sync:
            self._frappe_env = self._frappe_voulue
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"frappe": self._frappe_voulue or None})

    def piege_maj_mots_autres(self, d):
        """Une fois la devinette lancée, le mot à trouver de chaque autre joueur s'affiche sous sa grille (jamais le nôtre : la base le refuse)."""
        if not self.piege_fin_connue(): return
        cache, pret = bool(self.controller.settings_config.get("piege_cache")), d.get("piege_pret") or {}
        for pid, a in self.adv_widgets.items():
            if pid not in pret or not a.winfo_exists(): continue
            if pid == self.piege_cible and not cache and self.piege_mon_mot: continue  # « Ton mot : … » est déjà affiché sous sa grille
            sec = self.piege_mot(pid)
            if sec:
                txt = ("Mot : " if a.dense else "Mot à trouver : ") + sec["mot"]
                if a.lbl_mot.cget("text") != txt: a.lbl_mot.config(text=txt)

    def piege_maj_mon_mot(self, d=None):
        """Affiche le mot qu'on a choisi pour sa cible (jamais ceux choisis par ou pour les autres)."""
        if not self.piege_mon_mot and self.piege_cible and ((d or self.last_sync_data or {}).get("piege_pret") or {}).get(self.piege_cible):
            sec = self.piege_mots.get(self.piege_cible) or self.piege_mot(self.piege_cible)  # reprise : relu en arrière-plan (autorisé : on est son choisisseur)
            if sec and sec.get("de") == self.controller.player_id: self.piege_mon_mot = sec["mot"]
        a = None if self.controller.settings_config.get("piege_cache") else getattr(self, "adv_widgets", {}).get(self.piege_cible)  # affiché sous la mini-grille du joueur concerné (sauf cible cachée)
        if self.piege_mon_mot and a is not None and a.winfo_exists() and a.lbl_mot.cget("text") != f"Ton mot : {self.piege_mon_mot}":
            a.lbl_mot.config(text=f"Ton mot : {self.piege_mon_mot}")

    def piege_poser_fin(self):
        """Hôte : fixe la fin du choix à maintenant ; chacun passe à la devinette, ceux qui n'ont rien choisi ont un mot au hasard."""
        ms = int((time.time() + self.controller.server_time_offset) * 1000)
        self.piege_fin = ms / 1000; self.controller.settings_config["piege_fin_choix"] = ms
        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", {"piege_fin_choix": ms})

    def piege_forcer(self):
        """Hôte : démarre la devinette tout de suite ; ceux qui n'ont pas encore choisi reçoivent un mot au hasard."""
        if not self.controller.is_host or self.piege_fin_connue(): return
        self.piege_poser_fin(); self.piege_maj_etat()

    def piege_mot_hasard(self):
        conf = self.controller.settings_config; mi, ma = int(conf.get("min", 6)), int(conf.get("max", 7))
        return random.choice([m for m in self.controller.liste_mots if mi <= len(m) <= ma and m.isalpha() and m.isascii()] or self.controller.liste_mots)

    def valider_choix(self):
        if self.choix_envoi: return
        conf = self.controller.settings_config; mi, ma = int(conf.get("min", 6)), int(conf.get("max", 7))
        mot = "".join(self.choix)
        if not mi <= len(mot) <= ma:
            self.message_temp(f"Le mot doit faire {self.piege_texte_longueur(mi, ma)}", P["danger"], 1800); return
        if mot not in self.controller.banque_verif: self.message_temp("Mot inconnu", P["danger"]); return
        self.piege_envoyer(self.piege_cible, mot, self.controller.player_id, False)

    def piege_envoyer(self, cible, mot, de, auto):
        """Enregistre le mot secret de « cible » puis annonce sa longueur et sa 1re lettre (comme dans les autres modes)."""
        ctl, code, pid, gen = self.controller, self.controller.lobby_code, self.piege_id, self.sync_gen
        moi_choix = cible == self.piege_cible and de == ctl.player_id
        if moi_choix: self.choix_envoi = True; self.piege_rendre_choix()
        def worker():
            ok = ctl.fb_ok("put", f"pieges/{code}/{pid}/{cible}", {"mot": mot, "de": de, "auto": auto})
            if ok: ctl.fb_ok("put", f"lobbies/{code}/piege_pret/{cible}", {"n": len(mot), "p": mot[0]})
            ctl.reponses_reseau.put((lambda r: self.piege_envoye(r, cible, mot, de, auto, moi_choix, gen), ok))
        threading.Thread(target=worker, daemon=True).start()

    def piege_envoye(self, ok, cible, mot, de, auto, moi_choix, gen):
        if gen != self.sync_gen: return
        if ok: self.piege_mots[cible] = {"mot": mot, "de": de, "auto": auto}
        elif not moi_choix: self.piege_secours.discard(cible)  # mot de secours refusé (horloge) : on réessaiera
        if ok and cible == self.piege_cible and de == self.controller.player_id: self.piege_mon_mot = mot
        if not moi_choix or self.phase != "choix": return
        maintenant = time.time() + self.controller.server_time_offset
        if ok or maintenant > self.piege_fin:  # refusé après la fin du décompte : un mot au hasard a déjà été attribué
            self.phase = "attente"
            self.piege_construire_attente("Mot tiré au hasard" if (auto or not ok) else "Mot envoyé ✓")
        else:
            self.choix_envoi = False; self.piege_rendre_choix(); self.message_temp("Envoi impossible, réessaie", P["danger"], 1800)

    def piege_devine(self, info, d):
        me, conf = self.controller.player_id, self.controller.settings_config
        n, prem = int(info.get("n") or 0), str(info.get("p") or "?")[:1]
        self.piege_vider(); self.phase = "devine"; self.piege_n, self.piege_premiere = n, prem
        self.mot = prem + "?" * (n - 1)
        self.ligne, self.tape, self.attente_verdict = 0, [prem], None
        self.statut_lettres = {l: None for l in ALPHABET}
        self.labels_moi = self.creer_grille(self.moi_side, "", True)
        nom = self.piege_noms(d).get(self.piege_de.get(me), "?").capitalize()
        self.lbl_info.config(text=f"{NOM_MODE['PIEGE']} · mot choisi par {nom} · {n} lettres")
        essais = ((d.get("piege_essais") or {}).get(me)) or {}
        for k in range(int(conf.get("essais", 8))):  # reprise : on rejoue les essais déjà envoyés
            t = essais.get(f"e{k}") if isinstance(essais, dict) else None
            if not isinstance(t, str): break
            self.piege_essais_txt[k] = t; self.ligne, self.tape, self.attente_verdict = k, list(t), k
            if not self.piege_appliquer_verdict(d) or self.fini_local: break
        self.maj_clavier(); self.maj_affichage(); self.piege_maj_mon_mot(d)
        if self.attente_verdict is not None:
            for case in self.labels_moi[self.attente_verdict]: case.set_curseur(False)
            self.lbl_msg.config(text="Vérification…", fg=P["texte2"])

    def valider_piege(self):
        if self.attente_verdict is not None or len(self.tape) != self.piege_n: return
        t = "".join(self.tape)
        if t not in self.controller.banque_verif: self.message_temp("Mot inconnu", P["danger"]); return
        k, me = self.ligne, self.controller.player_id
        self.piege_essais_txt[k], self.attente_verdict = t, k
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/piege_essais/{me}/e{k}", t)
        for case in self.labels_moi[k]: case.set_curseur(False)
        self.lbl_msg.config(text="Vérification…", fg=P["texte2"])

    def piege_appliquer_verdict(self, d):
        """Applique le verdict (couleurs) de l'essai en attente, s'il est arrivé. Renvoie True s'il a été appliqué."""
        k, me = self.attente_verdict, self.controller.player_id
        if k is None: return False
        v = (((d.get("piege_verdicts") or {}).get(me)) or {}).get(f"e{k}")
        t = list(self.piege_essais_txt.get(k, ""))
        if not isinstance(v, str) or len(v) != self.piege_n or len(t) != self.piege_n: return False
        res = [{"B": "bien", "M": "mal"}.get(c, "absent") for c in v]
        self.attente_verdict = None
        self.maj_statuts(t, res)
        for i, e in enumerate(res): self.labels_moi[k][i].config(text=t[i], bg=P[e])
        for case in self.labels_moi[k]: case.set_curseur(False)
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{me}/{k}", {"c": list(v), "l": t})
        if self.lbl_msg.cget("text") == "Vérification…": self.lbl_msg.config(text="")
        if set(v) == {"B"}:
            self.mot_reel = self.mot = self.controller.dernier_mot = "".join(t); self.finir_round(True)
        elif k >= int(self.controller.settings_config.get("essais", 8)) - 1: self.finir_round(False)
        else: self.ligne, self.tape = k + 1, [self.piege_premiere]; self.maj_affichage()
        return True

    def piege_mot(self, cible):
        """Mot secret de « cible » (pour l'évaluer) : en cache, sinon lu en arrière-plan (refusé par la base si c'est le nôtre)."""
        if cible in self.piege_mots: return self.piege_mots[cible]
        if time.time() - self.piege_lectures.get(cible, 0) > 1.5:
            self.piege_lectures[cible] = time.time(); gen = self.sync_gen
            def recu(x):
                if gen == self.sync_gen and isinstance(x, dict) and isinstance(x.get("mot"), str): self.piege_mots[cible] = x
            self.controller.fb_get_async(f"pieges/{self.controller.lobby_code}/{self.piege_id}/{cible}", recu)
        return None

    def piege_evaluateur(self, cible, actifs):
        """Qui évalue les essais de « cible » : son choisisseur s'il est là, sinon le premier autre participant présent."""
        c = self.piege_de.get(cible)
        if c in actifs: return c
        return next(iter(sorted(u for u in actifs if u != cible and u in self.piege_de)), None)

    def piege_tick(self, d, s, p, actifs, fs):
        me, code = self.controller.player_id, self.controller.lobby_code
        essais_max = int(s.get("essais", 8))
        maintenant = time.time() + self.controller.server_time_offset
        pret = d.get("piege_pret") or {}
        recap_r = ((d.get("piege_recap") or {}).get(f"r{self.round_actuel}")) or {}
        fin = float(s.get("piege_fin_choix") or PIEGE_FIN_INFINIE) / 1000  # fixée par l'hôte (tous ont choisi, ou démarrage forcé)
        if fin != self.piege_fin: self.piege_fin = fin
        # 0. hôte : tous les mots (des joueurs présents) sont choisis → la devinette commence
        if self.controller.is_host and not self.piege_fin_connue():
            attendus = [t for t, c in self.piege_de.items() if t in actifs and c in actifs]
            if attendus and all(t in pret for t in attendus): self.piege_poser_fin()
        self.piege_maj_etat(d); self.piege_maj_mon_mot(d); self.piege_maj_mots_autres(d); self.piege_frappe()
        # 1. notre choix : mot au hasard si l'hôte a forcé le démarrage
        if self.phase == "choix" and not self.choix_envoi and self.piege_fin_connue() and maintenant > self.piege_fin:
            if pret.get(self.piege_cible): self.phase = "attente"; self.piege_construire_attente("Mot tiré au hasard")
            else: self.piege_envoyer(self.piege_cible, self.piege_mot_hasard(), me, True)
        # 2. notre mot est prêt, la fin du choix est fixée : place à la devinette
        if self.phase == "attente" and isinstance(pret.get(me), dict) and self.piege_fin_connue(): self.piege_devine(pret[me], d)
        # 3. verdict de notre dernier essai
        if self.phase == "devine" and self.attente_verdict is not None and not self.fini_local: self.piege_appliquer_verdict(d)
        # 4. mot au hasard pour un choisisseur parti avant d'avoir choisi
        if self.piege_fin_connue() and maintenant > self.piege_fin + 5:
            for t, c in self.piege_de.items():
                if t in pret or t not in actifs or t in self.piege_secours: continue
                if self.piege_evaluateur(t, [u for u in actifs if u != c]) == me:
                    self.piege_secours.add(t); self.piege_envoyer(t, self.piege_mot_hasard(), c, True)
        # 5. évaluation des essais des cibles dont on a la charge, puis révélation du mot en fin de paire
        tous_essais, tous_verdicts = d.get("piege_essais") or {}, d.get("piege_verdicts") or {}
        num = lambda k: int(str(k)[1:]) if str(k)[1:].isdigit() else 99
        for t, c in self.piege_de.items():
            if t == me or t not in p or t in recap_r or t in self.piege_recaps: continue
            if self.piege_evaluateur(t, actifs) != me: continue
            sec = self.piege_mot(t)
            if not sec: continue
            mot = sec["mot"]
            if t not in pret and time.time() - self.piege_pret_envoye.get(t, 0) > 3:  # annonce perdue : on la renvoie
                self.piege_pret_envoye[t] = time.time()
                self.controller.fb_put(f"lobbies/{code}/piege_pret/{t}", {"n": len(mot), "p": mot[0]})
            et = tous_essais.get(t) if isinstance(tous_essais.get(t), dict) else {}
            vt = dict(tous_verdicts.get(t) or {}) if isinstance(tous_verdicts.get(t), dict) else {}
            for k in sorted(et, key=num):
                g = et[k]
                if k in vt or (t, k) in self.piege_envoyes or not isinstance(g, str) or len(g) != len(mot): continue
                v = "".join(en_codes(design.evaluer(list(g), mot)))
                self.controller.fb_put(f"lobbies/{code}/piege_verdicts/{t}/{k}", v); self.piege_envoyes.add((t, k)); vt[k] = v
            gagne = next((num(k) + 1 for k in sorted(vt, key=num) if set(vt[k]) == {"B"}), 0)
            if gagne or len(vt) >= essais_max or fs.get(t) or self.temps_restant <= 0:
                self.piege_recaps.add(t)
                self.controller.fb_put(f"lobbies/{code}/piege_recap/r{self.round_actuel}/{t}", {"de": c, "mot": mot, "essais": gagne, "auto": bool(sec.get("auto"))})
        # 6. notre mot révélé et notre score (recalculé à partir du récapitulatif de toutes les manches)
        mien = recap_r.get(me)
        if isinstance(mien, dict) and isinstance(mien.get("mot"), str) and not self.mot_reel:
            self.mot_reel = self.mot = self.controller.dernier_mot = mien["mot"]
        total = piege_points(d.get("piege_recap"), me, essais_max)
        if total != self.controller.current_score:
            self.controller.current_score = total; self.s_score.set(nombre(total))
            self.controller.fb_patch(f"lobbies/{code}/players/{me}", {"score": total})

    def piege_recaps_complets(self, d, actifs):
        """La manche ne se clôt qu'une fois chaque mot révélé (8 s de délai au plus, si un évaluateur manque)."""
        recap_r = ((d.get("piege_recap") or {}).get(f"r{self.round_actuel}")) or {}
        attendus = [t for t in self.piege_de if t in actifs and self.piege_evaluateur(t, actifs) and t not in recap_r]
        if not attendus: return True
        if self.piege_attente_recap is None: self.piege_attente_recap = time.time()
        return time.time() - self.piege_attente_recap > 8

    def piege_etat_adv(self, pid, d, nb_essais):
        """État d'un adversaire pendant une manche de Mot piégé."""
        pret = d.get("piege_pret") or {}
        if pid not in self.piege_de: return "Spectateur"
        sa_cible = next((t for t, c in self.piege_de.items() if c == pid), None)
        if sa_cible and sa_cible not in pret: return "Choisit un mot…"
        if pid not in pret: return "Attend son mot…"
        return f"Essai {min(nb_essais + 1, int(self.controller.settings_config.get('essais', 8)))}"

    def update_timer(self, gen):
        if not self.timer_actif or gen != self.sync_gen: return
        maintenant = time.time() + self.controller.server_time_offset
        duree = int(self.controller.settings_config.get("timer", 180))
        if self.piege:  # le temps ne court qu'une fois le choix des mots terminé
            self.temps_restant = max(0, int(duree - (maintenant - self.piege_fin))) if self.piege_fin_connue() else duree
            if not self.piege_fin_connue(): self.s_temps.set("--:--", P["texte"])
            else: self.s_temps.set(mm_ss(self.temps_restant), P["texte"] if self.temps_restant > 30 else P["danger"])
        else:
            self.temps_restant = max(0, int(duree - (maintenant - self.start_time_round)))
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
        if self.piege:
            if self.phase == "choix": self.valider_choix()
            elif self.phase == "devine": self.valider_piege()
            return
        mode = self.controller.settings_config.get("game_mode", "CLASSIQUE")
        req_len = len(self.mot) - 1 if mode == "MYSTERE" else len(self.mot)
        if len(self.tape) != req_len: return

        if mode == "MYSTERE":
            t_suffix = "".join(self.tape)
            target_suffix = self.mot[1:]
            is_valid = (t_suffix == target_suffix) or any((chr(code) + t_suffix) in self.controller.banque_verif for code in range(65, 91))
            if not is_valid:
                self.message_temp("Mot inconnu", P["danger"]); return
            res, secret = ["absent"]*len(target_suffix), list(self.mot)
            for i in range(len(target_suffix)):
                if self.tape[i] == target_suffix[i]: res[i], secret[i+1] = "bien", None
            for i in range(len(target_suffix)):
                if res[i] != "bien" and self.tape[i] in secret: res[i] = "mal"; secret[secret.index(self.tape[i])] = None
            self.maj_statuts(self.tape, res)
            for i, e in enumerate(res): self.labels_moi[self.ligne][i+1].config(bg=P[e])
            self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}/{self.ligne}", {"c": en_codes(["absent"]+res), "l": ["?"]+self.tape})
            for case in self.labels_moi[self.ligne]: case.set_curseur(False)
            if all(e == "bien" for e in res):
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
            if mode == "COOP": return self.valider_coop()
            res = design.evaluer(self.tape, self.mot)
            self.maj_statuts(self.tape, res)
            for i, e in enumerate(res): self.labels_moi[self.ligne][i].config(bg=P[e])
            for case in self.labels_moi[self.ligne]: case.set_curseur(False)
            payload = {"c": en_codes(res), "l": self.tape}
            if mode in RUSHS:
                payload["w_idx"] = self.rush_index
            if not (mode in RUSHS and t == self.mot):
                self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}/{self.ligne}", payload)

            if t == self.mot:
                if mode in RUSHS:
                    self.controller.current_score += 1
                    self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score, "rush_index": self.rush_index + 1})
                    self.s_score.set(nombre(self.controller.current_score))
                    self.reinitialiser_grille_rush()
                    self.message_temp("+1 point · mot suivant !", P["succes"])
                else:
                    self.finir_round(True)
            elif self.ligne >= self.controller.settings_config["essais"]-1:
                if mode in RUSHS:
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

    # --- mode coopératif : une grille commune remplie par tous les joueurs ---
    def valider_coop(self):
        uid, k = self.controller.player_id, self.coop_n
        res = design.evaluer(self.tape, self.mot)
        v = {"c": en_codes(res), "l": list(self.tape), "t": {".sv": "timestamp"}}
        self.coop_n += 1
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{uid}/{k}", v)
        self.coop_attente.append((uid, k, dict(v, t=None)))  # affiché tout de suite, en attendant le serveur
        self.tape = [self.mot[0]]
        self.rendre_coop()

    def rendre_coop(self):
        essais = int(self.controller.settings_config.get("essais", 6))
        serveur = fusion_coop(self.coop_md, essais)
        connus = {(pid, k) for _, pid, k, _ in serveur}
        self.coop_attente = [x for x in self.coop_attente if (x[0], x[1]) not in connus]
        lignes = (serveur + [(9e15, pid, k, v) for pid, k, v in self.coop_attente])[:essais]
        sig = tuple((pid, k) for _, pid, k, _ in lignes)
        if sig != self.coop_sig:
            self.coop_sig = sig
            self.statut_lettres = {l: None for l in ALPHABET}
            etats = {"B": "bien", "M": "mal", "A": "absent"}
            for r, row in enumerate(self.labels_moi):
                if r < len(lignes):
                    v = lignes[r][3]
                    for c, case in enumerate(row):
                        code = (v.get("c") or [])[c] if c < len(v.get("c") or []) else "A"
                        case.config(text=(v.get("l") or [""] * len(row))[c] if c < len(v.get("l") or []) else "", bg=couleur_code(code)); case.set_curseur(False)
                    self.maj_statuts(list(v.get("l") or []), [etats.get(x, "absent") for x in v.get("c") or []])
                elif not (self.fini_local and r == self.ligne):
                    for case in row: case.config(text="", bg=BG); case.set_curseur(False)
            self.maj_clavier()
        if self.fini_local: return
        self.ligne = min(len(lignes), essais - 1)
        trouve = any(all(x == "B" for x in (v.get("c") or ["A"])) for _, _, _, v in lignes)
        if trouve: self.finir_round(True)
        elif len(lignes) >= essais: self.finir_round(False)
        else: self.maj_affichage()

    def maj_statuts(self, lettres, res):
        for i, char in enumerate(lettres):
            cur = self.statut_lettres.get(char)
            if res[i] == "bien": self.statut_lettres[char] = "bien"
            elif res[i] == "mal" and cur != "bien": self.statut_lettres[char] = "mal"
            elif res[i] == "absent" and cur not in ("bien", "mal"): self.statut_lettres[char] = "absent"
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
        self.lbl_info.config(text=f"{NOM_MODE.get(self.controller.settings_config.get('game_mode'), 'Rush')} · mot n° {self.rush_index + 1} · {len(self.mot)} lettres")
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
        if self.piege and self.phase != "devine":
            if self.phase == "choix" and not self.choix_envoi and len(self.choix) < int(self.controller.settings_config.get("max", 7)):
                self.choix.append(char); self.piege_rendre_choix()
            return
        if self.piege and self.attente_verdict is not None: return
        max_l = self.get_max_tape()
        if len(self.tape) > max_l: self.tape = self.tape[:max_l]
        if len(self.tape) < max_l: self.tape.append(char)
        self.maj_affichage()

    def effacer(self):
        if self.fini_local: return
        if self.piege and self.phase != "devine":
            if self.phase == "choix" and not self.choix_envoi and self.choix: self.choix.pop(); self.piege_rendre_choix()
            return
        if self.piege and self.attente_verdict is not None: return
        max_l = self.get_max_tape()
        if len(self.tape) > max_l: self.tape = self.tape[:max_l]
        min_len = 0 if self.controller.settings_config.get("game_mode") == "MYSTERE" else 1
        if len(self.tape) > min_len: self.tape.pop()
        self.maj_affichage()

    def finir_round(self, vic):
        self.fini_local = True
        if self.labels_moi:
            for case in self.labels_moi[min(self.ligne, len(self.labels_moi) - 1)]: case.set_curseur(False)
        self.winfo_toplevel().unbind("<Key>")
        mode = self.controller.settings_config.get("game_mode", "CLASSIQUE")
        if vic:
            if mode in ["CLASSIQUE", "MYSTERE", "COOP"]:
                self.controller.current_score += 1
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score})
            elif mode == "PRECISION":
                max_essais = self.controller.settings_config.get("essais", 6)
                base_pts = max(1, max_essais - self.ligne)
                pts = base_pts * 2 if self.ligne == 0 else base_pts
                self.controller.current_score += pts
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score})
            elif mode in ("BLAST", "ELIMINATION"):
                self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/round_wins/r{self.round_actuel}/{self.controller.player_id}", {".sv": "timestamp"})
        self.s_score.set(nombre(self.controller.current_score))
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/fini_states/{self.controller.player_id}", True)
        self.lbl_msg.config(text="Bien joué !" if vic else "Manche terminée", fg=P["succes"] if vic else P["texte2"])
        if not self.btn_def.winfo_ismapped(): self.btn_def.pack(side="left")

    def clic_suivant(self):
        self.btn_next.pack_forget()
        d = self.controller.lire_salon()
        if not d: return
        s = d["settings"]
        mode = s.get("game_mode", "CLASSIQUE")
        if mode in RUSHS and hasattr(self, "rush_words"):
            p = d.get("players", {})
            max_idx = max([pdat.get("rush_index", 0) for pdat in p.values()] + [self.rush_index, 0])
            round_words = self.rush_words[:max_idx + 1]
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/rush_recap", {f"r{self.round_actuel}": round_words})
        fin = {"status": "finished"}
        if mode == "ELIMINATION":
            elim, vivants = calcul_elimination(d, int(s["current_round"]))
            s["elimines"] = list(s.get("elimines") or []) + elim
            # scores finaux écrits avec la fin de partie : 1 point par manche survécue (les survivants ont survécu à toutes)
            fin.update({"settings/elimines": s["elimines"], **{f"players/{v}/score": int(s["current_round"]) for v in vivants}})
            if len(vivants) <= 1:
                self.controller.statut_salon = "finished"
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", fin); return
        if mode == "PIEGE" and int(s["current_round"]) < int(s["rounds"]):
            p = d.get("players") or {}; now_ms = max([v.get("last_seen", 0) for v in p.values()] + [0])
            actifs = [pid for pid, v in p.items() if now_ms - v.get("last_seen", 0) <= 15000]
            if len(actifs) < 2:  # plus assez de joueurs pour former des paires
                self.controller.statut_salon = "finished"
                self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", fin); return
        if int(s["current_round"]) < int(s["rounds"]):
            s.update({
                "rush_seed": random.randint(1000, 999999),
                "current_round": int(s["current_round"]) + 1,
                "start_time": time.time() + self.controller.server_time_offset
            })
            maj = {"settings": s, "status": "playing", "match_data": None, "fini_states": None}
            if mode == "PIEGE":
                s.update(piege_reglages(s.get("piege_ordre") or [], actifs, s["current_round"], s["rush_seed"], s["start_time"], s.get("piege_de")))
                maj.update({"piege_pret": None, "piege_essais": None, "piege_verdicts": None})
            self.controller.settings_config.update(s)
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", maj)
        else:
            self.controller.statut_salon = "finished"
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", fin)

    def clavier_physique(self, e):
        if self.fini_local: return
        k, c = e.keysym, e.char.upper()
        if c in ALPHABET and len(c) == 1: self.ajouter_lettre(c)
        elif k == "BackSpace": self.effacer()
        elif k in ("Return", "KP_Enter"): self.valider()

    def maj_affichage(self):
        self.piege_frappe()
        if self.fini_local: return
        if getattr(self, "piege", False) and self.phase != "devine":
            if self.phase == "choix": self.piege_rendre_choix()
            return
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
        """(colonnes, taille de case, dense) des grilles adverses selon le nombre d'adversaires et la fenêtre."""
        conf = self.controller.settings_config
        try: win_h, win_w = self.winfo_toplevel().winfo_height(), self.winfo_toplevel().winfo_width()
        except Exception: win_h, win_w = 860, 1200
        if win_h <= 200: win_h = 860
        if win_w <= 200: win_w = 1200
        longueur = max(len(getattr(self, "mot", "") or "x" * 7), int(conf.get("max", 7) or 7))
        return disposition_adv(nb, conf.get("essais", 6), longueur, max(300, win_w - 640), win_h - 140)

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
        for char, etat in self.statut_lettres.items(): self.clavier.set_couleur(char, P[etat] if etat else None)


class PageScoreFinal(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller, self.active_sync = controller, False
        self.lbl_haut = barre_haut(self, self.quitter_depuis_score, "Partie terminée")
        hb = self.lbl_haut.master  # 9.0 : bouton de l'hôte « Lobby » à côté de la flèche
        self.btn_lobby_haut = BoutonLobby(hb, self.retour_lobby_confirme); self.lobby_haut_visible = None
        zone = Defilant(self, hauteur=200); zone.pack(fill="both", expand=True)
        self.corps = tk.Frame(zone.interieur, bg=P["fond"]); self.corps.pack(fill="both", expand=True, pady=(0, 20))
        self.lbl_rush_recap = tk.Label(self, text="")  # conservé pour la logique de récapitulatif

    def quitter_depuis_score(self): self.active_sync = False; self.controller.quitter_lobby_logic(); self.controller.controller.creer_menu_accueil()

    def recap_rush(self, d):
        if d.get("settings", {}).get("game_mode") == "PIEGE":
            rec, lignes = d.get("piege_recap") or {}, []
            noms = {pid: v.get("name", "?") for pid, v in (d.get("players") or {}).items()}
            for k in sorted(rec, key=lambda k: int(k[1:]) if k[1:].isdigit() else 0):
                lignes += [f"Manche {k[1:]}"] + piege_lignes_recap(rec[k], None, noms)
            return lignes
        recap_data = d.get("rush_recap")
        if d.get("settings", {}).get("game_mode") not in RUSHS or not recap_data: return []
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
        d = self.controller.lire_salon()
        if not d: return
        p = d.get("players", {})
        if not p: return
        for w in self.corps.winfo_children(): w.destroy()
        hote = p.get(d.get("settings", {}).get("host_id"), {}).get("name", "")
        mode = d.get("settings", {}).get("game_mode", "CLASSIQUE")
        self.lbl_haut.config(text=(f"Salon de {hote.capitalize()} · " if hote else "") + f"{NOM_MODE.get(mode, mode)} · Partie terminée")
        c = tk.Frame(self.corps, bg=P["fond"]); c.pack(pady=(18, 0))
        mot = getattr(self.controller, "dernier_mot", "") if mode != "PIEGE" else ""
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
            cv = tk.Canvas(col, width=190, height=hauteurs[rang_de[pid]] + 64, bg=P["fond"], highlightthickness=0); cv.pack()
            hb = hauteurs[rang_de[pid]]; H = hb + 64  # ex aequo : même marche
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
        self.maj_lobby_haut()
        self.fin_gen = getattr(self, "fin_gen", 0) + 1
        self.ecouter_fin(self.fin_gen)

    def ecouter_fin(self, gen):
        if not self.active_sync or gen != self.fin_gen: return
        self.controller.lire_salon_async(lambda d: self.traiter_fin(d, gen))

    def traiter_fin(self, d, gen):
        if not self.active_sync or gen != self.fin_gen: return
        if d and d.get("status") == "waiting": self.active_sync = False; self.controller.current_score = 0; self.controller.show_frame("PageLobby")
        else:
            if d and d.get("settings", {}).get("host_id"):  # l'hôte a pu changer
                self.controller.is_host = d["settings"]["host_id"] == self.controller.player_id; self.maj_lobby_haut()
            if d and self.lbl_rush_recap.cget("text") != "\n".join(self.recap_rush(d)):
                self.maj_rush_recap(d)
            if d and d.get("settings", {}).get("game_mode") == "PIEGE":  # dernier mot révélé après la fin : score à jour
                total = piege_points(d.get("piege_recap"), self.controller.player_id, int(d["settings"].get("essais", 8)))
                if total != self.controller.current_score:
                    self.controller.current_score = total
                    self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": total})
            self.after(1000, lambda: self.ecouter_fin(gen))

    def retour_lobby_host(self): self.controller.ramener_au_salon()
    def retour_lobby_confirme(self):
        if self.controller.is_host and tkm.askyesno("Lobby", "Ramener tous les joueurs au salon ?"): self.controller.ramener_au_salon()
    def maj_lobby_haut(self):
        v = bool(self.controller.is_host)
        if v == self.lobby_haut_visible: return
        self.lobby_haut_visible = v
        if v: self.btn_lobby_haut.pack(side="left", padx=(12, 0), after=self.btn_lobby_haut.master.winfo_children()[0])
        else: self.btn_lobby_haut.pack_forget()