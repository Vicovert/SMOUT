import tkinter as tk
from tkinter import messagebox as tkm
import json, random, os, sys, time, requests
from pathlib import Path

# --- CONFIGURATION ---
FIREBASE_URL = "https://smout-multi-default-rtdb.europe-west1.firebasedatabase.app/"
BLEU, ROUGE, JAUNE, BLEU_C, GRIS_LIGHT = '#0a4160', '#ef4444', '#eab308', '#0ea5e9', '#64748b'
FONT_MONO, FONT_UI = ("Courier", 24, "bold"), ("Helvetica", 12, "bold")
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- COMPOSANTS UI ---
class LogoSmout(tk.Canvas):
    def __init__(self, parent, tile_size=90):
        word = "SMOUT"
        gap = 12
        total_w = (tile_size + gap) * len(word)
        super().__init__(parent, width=total_w, height=tile_size + 40, bg=BLEU, highlightthickness=0)
        for i, char in enumerate(word):
            x = i * (tile_size + gap)
            p, s = 8, tile_size - 8
            bg, dark, light = (ROUGE, "#991b1b", "#f87171") if char == "U" else (JAUNE, "#a16207", "#fef08a")
            self.draw_round_rect(x+p+4, p+8, x+s+4, s+8, 15, fill="#042f48")
            self.draw_round_rect(x+p, p+4, x+s, s+4, 15, fill=dark)
            self.draw_round_rect(x+p, p, x+s, s, 15, fill=bg)
            self.draw_round_rect(x+p+4, p+4, x+s-4, p+(s/2.5), 12, fill=light)
            self.create_text(x+tile_size/2, tile_size/2, text=char, fill="white", font=("Verdana", int(tile_size*0.5), "bold"))
    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(p, **kwargs, smooth=True)

class BoutonPro(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=45, color="#f5deb3", hover_color="#e2bc74"):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command, self.color, self.hover_color = command, color, hover_color
        self.rect = self.draw_round_rect(2, 2, width-2, height-2, 12, fill=color)
        self.txt = self.create_text(width/2, height/2, text=text, fill=BLEU, font=FONT_UI)
        self.bind("<ButtonRelease-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.color))
    def set_text(self, new_text): self.itemconfig(self.txt, text=new_text)
    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(p, **kwargs, smooth=True)

class PageMulti(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        self.player_id = str(random.randint(100000, 999999))
        self.pseudo = self.charger_pseudo_local()
        self.lobby_code, self.is_host = "", False
        self.settings_config = {"nb_essais": 6, "nb_lettres_min": 6, "nb_lettres_max": 10, "round_num": 1}
        self.charger_mots()
        self.container = tk.Frame(self, bg=BLEU); self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (PageAccueil, PageLobby, PageCode, PageJeu, PageScoreFinal):
            f = F(parent=self.container, controller=self); self.frames[F.__name__] = f; f.grid(row=0, column=0, sticky="nsew")
        self.show_frame("PageAccueil")
        self.controller.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if self.lobby_code: self.quitter_lobby_logic()
        self.controller.winfo_toplevel().destroy()

    def quitter_lobby_logic(self):
        if not self.lobby_code: return
        data = self.fb_get(f"lobbies/{self.lobby_code}")
        if not data: return
        players = data.get("players", {})
        if self.player_id in players: del players[self.player_id]
        self.fb_delete(f"lobbies/{self.lobby_code}/players/{self.player_id}")
        if not players: self.fb_delete(f"lobbies/{self.lobby_code}")
        elif self.is_host:
            new_host_id = list(players.keys())[0]
            self.fb_patch(f"lobbies/{self.lobby_code}/settings", {"host_id": new_host_id})

    def charger_pseudo_local(self):
        d = os.path.join(os.getenv('APPDATA'), "SMOUT")
        p = os.path.join(d, "config.json")
        if os.path.exists(p):
            try:
                with open(p, 'r') as f: return json.load(f).get("pseudo", "ANONYME")
            except: pass
        return "ANONYME"

    def sauvegarder_pseudo_local(self, p):
        if not p: return
        self.pseudo = p.upper()
        d = os.path.join(os.getenv('APPDATA'), "SMOUT")
        os.makedirs(d, exist_ok=True)
        try:
            with open(os.path.join(d, "config.json"), 'w') as f: json.dump({"pseudo": self.pseudo}, f)
        except: pass

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
        for f in self.frames.values():
            if hasattr(f, "active_sync"): f.active_sync = False
        f = self.frames[name]; f.tkraise()
        if name == "PageCode": f.nettoyer()
        if name == "PageLobby": f.entrer_lobby()
        if name == "PageJeu": f.initialiser_partie()
        if name == "PageScoreFinal": f.afficher_vainqueur()

    def fb_get(self, path):
        try: return requests.get(f"{FIREBASE_URL}{path}.json", timeout=1.5).json()
        except: return None
    def fb_patch(self, path, data):
        try: requests.patch(f"{FIREBASE_URL}{path}.json", json=data, timeout=1.5)
        except: pass
    def fb_put(self, path, data):
        try: requests.put(f"{FIREBASE_URL}{path}.json", json=data, timeout=1.5)
        except: pass
    def fb_delete(self, path):
        try: requests.delete(f"{FIREBASE_URL}{path}.json", timeout=1.5)
        except: pass

class PageAccueil(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.5, anchor="center")
        LogoSmout(c, 110).pack(pady=(0, 30))
        tk.Label(c, text="TON PSEUDO", font=("Helvetica", 10, "bold"), fg=JAUNE, bg=BLEU).pack()
        self.sv_pseudo = tk.StringVar(value=self.controller.pseudo)
        self.sv_pseudo.trace_add("write", self.format_pseudo_input)
        tk.Entry(c, textvariable=self.sv_pseudo, font=("Courier", 18, "bold"), justify="center", bg="#052132", fg="white", width=15).pack(pady=(5, 20))
        BoutonPro(c, "CRÉER UN LOBBY", self.creer, color="#22c55e", width=250).pack(pady=8)
        BoutonPro(c, "REJOINDRE UN LOBBY", self.rejoindre, color=JAUNE, width=250).pack(pady=8)
        BoutonPro(c, "MENU", lambda: self.controller.controller.creer_menu_accueil(), color="#94a3b8", width=250).pack(pady=20)
    def format_pseudo_input(self, *args):
        val = self.sv_pseudo.get()
        formate = "".join([c.upper() for c in val if not c.isspace()])
        if val != formate: self.sv_pseudo.set(formate)
        self.controller.sauvegarder_pseudo_local(formate)
    def creer(self):
        if self.sv_pseudo.get().strip(): self.controller.is_host = True; self.controller.show_frame("PageLobby")
    def rejoindre(self):
        if self.sv_pseudo.get().strip(): self.controller.is_host = False; self.controller.show_frame("PageCode")

class PageCode(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="CODE DU LOBBY", font=("Helvetica", 25, "bold"), fg="white", bg=BLEU).pack(pady=20)
        vcmd = (self.register(self.validate_digits), '%P')
        self.e = tk.Entry(c, font=("Courier", 45, "bold"), justify="center", width=5, bg="#052132", fg=JAUNE, validate="key", validatecommand=vcmd)
        self.e.pack(pady=10); self.e.bind("<Return>", lambda e: self.valider())
        BoutonPro(c, "REJOINDRE", self.valider, color="#22c55e").pack(pady=20)
        BoutonPro(c, "RETOUR", lambda: controller.show_frame("PageAccueil"), color="#94a3b8").pack()
    def validate_digits(self, P): return P == "" or P.isdigit()
    def valider(self):
        code = self.e.get().strip()
        if code:
            data = self.controller.fb_get(f"lobbies/{code}")
            if data and len(data.get("players", {})) < 4:
                self.controller.lobby_code = code
                self.controller.fb_patch(f"lobbies/{code}/players/{self.controller.player_id}", {"name": self.controller.pseudo, "score": 0})
                self.controller.show_frame("PageLobby")
            else: tkm.showwarning("SMOUT", "Lobby plein ou introuvable")
    def nettoyer(self): self.e.delete(0, tk.END); self.e.focus_set()

class PageLobby(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller; self.active_sync = False
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="SALLE D'ATTENTE", font=("Arial Black", 20), fg="white", bg=BLEU).pack()
        self.lbl_code = tk.Label(c, text="----", font=("Courier", 55, "bold"), fg=JAUNE, bg="#052132", padx=25); self.lbl_code.pack(pady=15)
        self.grid_players = tk.Frame(c, bg=BLEU); self.grid_players.pack(pady=10)
        self.player_slots = []
        for i in range(4):
            f = tk.Frame(self.grid_players, bg="#052132", width=120, height=50, highlightbackground=BLEU_C, highlightthickness=1)
            f.grid_propagate(False); f.grid(row=i//2, column=i%2, padx=5, pady=5)
            lbl = tk.Label(f, text="VIDE", font=("Helvetica", 10, "bold"), fg=GRIS_LIGHT, bg="#052132")
            lbl.place(relx=0.5, rely=0.5, anchor="center"); self.player_slots.append(lbl)
        self.f_p = tk.Frame(c, bg=BLEU); self.f_p.pack()
        self.s_rounds = SingleSlider(self.f_p, 1, 10, 3, label="ROUNDS", callback=lambda v: self.sync_params())
        self.s_essais = SingleSlider(self.f_p, 4, 8, 6, label="ESSAIS", callback=lambda v: self.sync_params())
        self.s_len = RangeSlider(self.f_p, 6, 10, 6, 10, callback=lambda v1, v2: self.sync_params())
        [s.pack() for s in [self.s_rounds, self.s_essais, self.s_len]]
        self.lbl_status = tk.Label(c, text="EN ATTENTE D'UN AMI...", font=FONT_UI, fg=ROUGE, bg=BLEU); self.lbl_status.pack(pady=10)
        self.btn_lancer = BoutonPro(c, "LANCER LE MATCH", self.lancer, color="#22c55e", width=250)
        BoutonPro(c, "QUITTER LE LOBBY", self.quitter, color="#94a3b8", width=250).pack(pady=5)
    def sync_params(self):
        if self.controller.is_host and self.active_sync:
            mi, ma = self.s_len.get_values()
            d = {"rounds": self.s_rounds.get_value(), "essais": self.s_essais.get_value(), "min": mi, "max": ma, "host_id": self.controller.player_id}
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", d)
    def entrer_lobby(self):
        self.active_sync = True; self.btn_lancer.pack_forget()
        if self.controller.is_host:
            self.controller.lobby_code = str(random.randint(1000, 9999)); self.lbl_code.config(text=self.controller.lobby_code)
            init = {"status": "waiting", "settings": {"rounds":3, "essais":6, "min":6, "max":10, "host_id": self.controller.player_id}, "players": {self.controller.player_id: {"name": self.controller.pseudo, "score": 0}}}
            self.controller.fb_put(f"lobbies/{self.controller.lobby_code}", init)
        else: self.lbl_code.config(text=self.controller.lobby_code)
        self.ecouter_lobby()
    def ecouter_lobby(self):
        if not self.active_sync: return
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data:
            s, players = data.get("settings", {}), data.get("players", {})
            self.controller.is_host = (s.get("host_id") == self.controller.player_id)
            
            # --- MODIFICATION : Synchronisation visuelle pour les invités ---
            if not self.controller.is_host:
                self.s_rounds.set_val(s.get("rounds", 3))
                self.s_essais.set_val(s.get("essais", 6))
                self.s_len.set_vals(s.get("min", 6), s.get("max", 10))

            if not self.controller.is_host and data.get("status") == "playing":
                self.controller.settings_config.update({"target_word": s.get("target_word", "SMOUT"), "nb_essais": s.get("essais", 6), "round_num": 1, "rounds": s.get("rounds", 3)})
                self.controller.show_frame("PageJeu"); return
            for i, slot in enumerate(self.player_slots):
                if i < len(players): slot.config(text=list(players.values())[i]["name"], fg="white")
                else: slot.config(text="VIDE", fg=GRIS_LIGHT)
            if len(players) > 1:
                self.lbl_status.config(text=f"🟢 {len(players)} JOUEURS PRÊTS", fg="#22c55e")
                if self.controller.is_host: self.btn_lancer.pack(pady=5)
            else:
                self.lbl_status.config(text="🔴 EN ATTENTE D'UN AMI...", fg=ROUGE); self.btn_lancer.pack_forget()
            [s_ui.activer(self.controller.is_host) for s_ui in [self.s_rounds, self.s_essais, self.s_len]]
        self.after(800, self.ecouter_lobby)
    def quitter(self): self.active_sync = False; self.controller.quitter_lobby_logic(); self.controller.show_frame("PageAccueil")
    def lancer(self):
        mi, ma = self.s_len.get_values(); f = [m for m in self.controller.liste_mots if mi <= len(m) <= ma]
        mot = random.choice(f if f else self.controller.liste_mots)
        s = {"target_word": mot, "rounds": self.s_rounds.get_value(), "current_round": 1, "essais": self.s_essais.get_value(), "min": mi, "max": ma, "host_id": self.controller.player_id}
        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"status": "playing", "settings": s})
        self.controller.settings_config.update({"target_word": mot, "nb_essais": s["essais"], "round_num": 1, "rounds": s["rounds"]})
        self.controller.show_frame("PageJeu")

class PageJeu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller; self.active_sync = False
        self.timer_actif, self.temps_restant = False, 180
        self.main_c = tk.Frame(self, bg=BLEU); self.main_c.place(relx=0.5, rely=0.5, anchor="center")
        header = tk.Frame(self.main_c, bg=BLEU, pady=10); header.pack(fill="x")
        BoutonPro(header, "MENU", self.quitter_jeu, width=80, height=35, color="#94a3b8").pack(side="left", padx=10)
        self.lbl_info = tk.Label(header, text="ROUND", fg=JAUNE, bg=BLEU, font=("Helvetica", 16, "bold")); self.lbl_info.pack(side="left", padx=10)
        self.lbl_scores = tk.Label(header, text="", fg="white", bg=BLEU, font=("Helvetica", 10, "bold")); self.lbl_scores.pack(side="left", padx=20)
        self.lbl_timer = tk.Label(header, text="03:00", fg="white", bg=BLEU, font=("Courier", 22, "bold")); self.lbl_timer.pack(side="right", padx=10)
        game_area = tk.Frame(self.main_c, bg=BLEU); game_area.pack()
        self.moi_side = tk.Frame(game_area, bg=BLEU); self.moi_side.pack(side="left", padx=40)
        tk.Frame(game_area, width=3, bg=BLEU_C).pack(side="left", fill="y", padx=20, pady=20)
        self.adv_container = tk.Frame(game_area, bg=BLEU); self.adv_container.pack(side="left", padx=40, fill="y")
    def quitter_jeu(self): self.active_sync = False; self.timer_actif = False; self.controller.quitter_lobby_logic(); self.controller.controller.creer_menu_accueil()
    def initialiser_partie(self):
        self.active_sync = False; self.timer_actif = False; [w.destroy() for w in self.moi_side.winfo_children() + self.adv_container.winfo_children()]
        conf = self.controller.settings_config; self.mot, self.round_actuel = conf.get("target_word", "SMOUT"), conf.get("round_num", 1)
        self.ligne, self.tape, self.fini_local, self.temps_restant = 0, [self.mot[0]], False, 180
        self.statut_lettres = {l: "#052132" for l in ALPHABET}; self.boutons_clavier = {}
        self.labels_moi = self.creer_grille(self.moi_side, self.controller.pseudo, True)
        self.lbl_msg = tk.Label(self.moi_side, text="", font=("Helvetica", 11, "bold"), bg=BLEU, fg="white", height=2); self.lbl_msg.pack()
        self.creer_clavier(self.moi_side); btns = tk.Frame(self.moi_side, bg=BLEU); btns.pack(pady=10)
        BoutonPro(btns, "VALIDER", self.valider, width=100, color="#22c55e").pack(side="left", padx=5)
        BoutonPro(btns, "EFFACER", self.effacer, width=100, color="#94a3b8").pack(side="left", padx=5)
        self.adv_labels, self.adv_grids = {}, {}; data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data:
            players = data.get("players", {})
            for pid, p in players.items():
                if pid != self.controller.player_id:
                    f = tk.Frame(self.adv_container, bg=BLEU, pady=5); f.pack()
                    lbl = tk.Label(f, text=p["name"], font=("Helvetica", 11, "bold"), fg="white", bg=BLEU); lbl.pack(); self.adv_labels[pid] = lbl
                    self.adv_grids[pid] = self.creer_grille_sans_label(f)
        self.btn_next = BoutonPro(self.main_c, "ROUND SUIVANT", self.clic_suivant, color=JAUNE, width=250)
        self.active_sync, self.timer_actif = True, True; self.update_timer(); self.ecouter_match(); self.controller.focus_set(); self.controller.bind("<Key>", self.clavier_physique); self.maj_affichage()
    def update_timer(self):
        if self.temps_restant > 0 and self.timer_actif:
            self.temps_restant -= 1; m, s = divmod(self.temps_restant, 60); self.lbl_timer.config(text=f"{m:02d}:{s:02d}", fg="white" if self.temps_restant > 30 else ROUGE); self.after(1000, self.update_timer)
        elif self.temps_restant <= 0 and not self.fini_local: self.finir_round(False)
    def ecouter_match(self):
        if not self.active_sync: return
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data:
            if data.get("status") == "finished": self.controller.show_frame("PageScoreFinal"); return
            s, players = data.get("settings", {}), data.get("players", {})
            self.controller.is_host = (s.get("host_id") == self.controller.player_id)
            if int(s.get("current_round", 1)) > self.round_actuel: 
                self.controller.settings_config.update({"target_word": s.get("target_word"), "round_num": int(s["current_round"])})
                self.initialiser_partie(); return
            self.lbl_scores.config(text=" | ".join([f"{p['name']}: {p['score']}" for p in players.values()]))
            self.lbl_info.config(text=f"ROUND {s.get('current_round')} / {s.get('rounds')}")
            fini_raw = data.get("fini_states") or {}; fini_ids = [k for k,v in fini_raw.items() if v] if isinstance(fini_raw, dict) else []
            if len(fini_ids) >= len(players): self.timer_actif = False
            for pid, lbl in self.adv_labels.items():
                if pid not in players: lbl.config(text=f"{lbl.cget('text').split(' ')[0]} (DÉCONNECTÉ)", fg=GRIS_LIGHT)
            m_data = data.get("match_data", {})
            for pid, grid in self.adv_grids.items():
                if pid in players:
                    p_prog = m_data.get(pid, {})
                    it = enumerate(p_prog) if isinstance(p_prog, list) else p_prog.items() if isinstance(p_prog, dict) else []
                    for l_str, content in it:
                        if content:
                            l_idx = int(l_str)
                            if l_idx < len(grid):
                                for c_idx, coul in enumerate(content.get("c", [])): grid[l_idx][c_idx].config(bg=coul)
                                if self.fini_local: [grid[l_idx][c_idx].config(text=char) for c_idx, char in enumerate(content.get("l", []))]
            if self.fini_local:
                if len(fini_ids) >= len(players):
                    self.lbl_msg.config(text=f"LE MOT ÉTAIT : {self.mot}", fg=JAUNE)
                    if self.controller.is_host:
                        txt = "VOIR LES RÉSULTATS" if int(s['current_round']) == int(s['rounds']) else "ROUND SUIVANT"; self.btn_next.set_text(txt); self.btn_next.pack(pady=15)
                else: self.lbl_msg.config(text=f"EN ATTENTE DES AUTRES... ({len(fini_ids)}/{len(players)})", fg=BLEU_C)
        self.after(800, self.ecouter_match)
    def valider(self):
        if len(self.tape) != len(self.mot) or self.fini_local: return
        t = "".join(self.tape)
        if t not in self.controller.banque_verif and t != self.mot:
            self.lbl_msg.config(text="MOT INCONNU", fg=ROUGE); self.after(1000, lambda: self.lbl_msg.config(text="") if not self.fini_local else None); return
        res, secret = [GRIS_LIGHT]*len(self.mot), list(self.mot)
        for i in range(len(self.mot)):
            if self.tape[i] == self.mot[i]: res[i], secret[i] = ROUGE, None
        for i in range(len(self.mot)):
            if res[i] != ROUGE and self.tape[i] in secret: res[i] = JAUNE; secret[secret.index(self.tape[i])] = None
        for i, char in enumerate(self.tape):
            cur = self.statut_lettres.get(char, "#052132")
            if res[i] == ROUGE: self.statut_lettres[char] = ROUGE
            elif res[i] == JAUNE and cur != ROUGE: self.statut_lettres[char] = JAUNE
            elif res[i] == GRIS_LIGHT and cur not in [ROUGE, JAUNE]: self.statut_lettres[char] = GRIS_LIGHT
        self.maj_clavier()
        for i, c in enumerate(res): self.labels_moi[self.ligne][i].config(bg=c)
        self.update_idletasks()
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}/{self.ligne}", {"c": res, "l": self.tape})
        if t == self.mot: self.finir_round(True)
        elif self.ligne >= self.controller.settings_config["nb_essais"]-1: self.finir_round(False)
        else: self.ligne += 1; self.tape = [self.mot[0]]; self.maj_affichage()
    def effacer(self):
        if not self.fini_local and len(self.tape) > 1: self.tape.pop(); self.maj_affichage()
    def finir_round(self, vic):
        self.fini_local = True
        if vic:
            p = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}")
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": (p.get("score") or 0) + 1})
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/fini_states/{self.controller.player_id}", True)
    def clic_suivant(self):
        self.btn_next.pack_forget(); data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}"); s = data["settings"]
        if int(s["current_round"]) < int(s["rounds"]):
            self.controller.fb_delete(f"lobbies/{self.controller.lobby_code}/match_data"); self.controller.fb_delete(f"lobbies/{self.controller.lobby_code}/fini_states")
            f = [m for m in self.controller.liste_mots if s["min"] <= len(m) <= s["max"]]
            s.update({"target_word": random.choice(f if f else self.controller.liste_mots), "current_round": int(s["current_round"])+1})
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"settings": s, "status": "playing"})
        else: self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"status": "finished"})
    def clavier_physique(self, e):
        if self.fini_local: return
        k, c = e.keysym, e.char.upper()
        if c in ALPHABET and len(c) == 1:
            if len(self.tape) < len(self.mot): self.tape.append(c); self.maj_affichage()
        elif k == "BackSpace": self.effacer()
        elif k == "Return": self.valider()
    def maj_affichage(self):
        if self.fini_local: return
        for i, c in enumerate(self.tape): self.labels_moi[self.ligne][i].config(text=c, bg=ROUGE if i == 0 else BLEU)
        for i in range(len(self.tape), len(self.mot)): self.labels_moi[self.ligne][i].config(text="", bg=BLEU)
    def creer_grille(self, parent, name, main):
        tk.Label(parent, text=name, font=("Helvetica", 11, "bold"), fg="white", bg=BLEU).pack()
        return self.creer_grille_sans_label(parent, main)
    def creer_grille_sans_label(self, parent, main=False):
        g = tk.Frame(parent, bg=BLEU); g.pack(); rows = []
        size = 28 if main else 10
        for l in range(self.controller.settings_config["nb_essais"]):
            ligne = [tk.Label(g, text="", font=("Courier", size, "bold"), width=2, height=1, fg="white", bg="#052132", borderwidth=1, relief="solid") for _ in range(len(self.mot))]
            [lbl.grid(row=l, column=c, padx=1, pady=1) for c, lbl in enumerate(ligne)]; rows.append(ligne)
        return rows
    def creer_clavier(self, parent):
        f = tk.Frame(parent, bg=BLEU); f.pack(pady=5)
        for r in ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ"]:
            row = tk.Frame(f, bg=BLEU); row.pack()
            for c in r: 
                btn = tk.Button(row, text=c, width=2, font=("Arial", 8, "bold"), bg="#052132", fg="white", command=lambda x=c: (self.tape.append(x), self.maj_affichage()) if len(self.tape) < len(self.mot) and not self.fini_local else None)
                btn.pack(side="left", padx=1, pady=1); self.boutons_clavier[c] = btn
    def maj_clavier(self):
        for char, color in self.statut_lettres.items():
            if char in self.boutons_clavier: self.boutons_clavier[char].config(bg=color)

class PageScoreFinal(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        self.c = tk.Frame(self, bg=BLEU); self.c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(self.c, text="MATCH FINI", font=("Helvetica", 40, "bold"), fg=JAUNE, bg=BLEU).pack(pady=30)
        self.lbl_res = tk.Label(self.c, text="", font=("Helvetica", 22, "bold"), fg="white", bg=BLEU, justify="center"); self.lbl_res.pack(pady=30)
        BoutonPro(self.c, "RETOUR AU MENU", lambda: self.controller.controller.creer_menu_accueil(), color="#94a3b8", width=300).pack()
    def afficher_vainqueur(self):
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data:
            players = data.get("players", {})
            if not players: return
            items = sorted(players.values(), key=lambda x: x.get("score", 0), reverse=True)
            max_s = items[0].get("score", 0)
            winners = [p["name"] for p in items if p.get("score", 0) == max_s]
            titre = f"VAINQUEUR : {winners[0]}" if len(winners) == 1 else f"ÉGALITÉ : {', '.join(winners)}"
            score_txt = "\n".join([f"{p['name']} : {p.get('score') or 0} pts" for p in items])
            self.lbl_res.config(text=f"{titre}\n\n{score_txt}")

class SingleSlider(tk.Canvas):
    def __init__(self, parent, min_v, max_v, init_v, width=300, label="", callback=None):
        super().__init__(parent, width=width, height=70, bg=BLEU, highlightthickness=0)
        self.min_v, self.max_v, self.v, self.enabled, self.callback = min_v, max_v, init_v, True, callback; self.margin, self.bw = 30, width - 60
        self.create_text(width/2, 10, text=label, fill="white", font=("Helvetica", 10, "bold"))
        self.create_line(self.margin, 35, width-self.margin, 35, fill="white", width=4)
        self.h = self.create_oval(0, 0, 22, 22, fill=BLEU_C, outline="white"); self.txt = self.create_text(width/2, 60, fill="white", font=("Arial", 11, "bold"))
        self.update_pos(); self.tag_bind(self.h, "<B1-Motion>", self.move)
    def update_pos(self):
        x = self.margin + ((self.v - self.min_v) / (self.max_v - self.min_v)) * self.bw
        self.coords(self.h, x-11, 24, x+11, 46); self.itemconfig(self.txt, text=str(int(self.v)))
    def move(self, e):
        if self.enabled: self.v = max(self.min_v, min(self.max_v, int(self.min_v + ((e.x - self.margin) / self.bw) * (self.max_v - self.min_v)))); self.update_pos(); (self.callback(self.v) if self.callback else None)
    def activer(self, s): self.enabled = s; self.itemconfig(self.h, fill=BLEU_C if s else GRIS_LIGHT)
    def set_val(self, v): self.v = v; self.update_pos()
    def get_value(self): return int(self.v)

class RangeSlider(tk.Canvas):
    def __init__(self, parent, min_v, max_v, v1, v2, width=300, callback=None):
        super().__init__(parent, width=width, height=70, bg=BLEU, highlightthickness=0)
        self.min_v, self.max_v, self.v1, self.v2, self.enabled, self.callback = min_v, max_v, v1, v2, True, callback; self.margin, self.bw = 30, width - 60
        self.create_text(width/2, 10, text="TAILLE DU MOT", fill="white", font=("Helvetica", 10, "bold"))
        self.create_line(self.margin, 35, width-self.margin, 35, fill="white", width=4)
        self.h1, self.h2 = self.create_oval(0,0,22,22, fill=JAUNE, outline="white"), self.create_oval(0,0,22,22, fill=ROUGE, outline="white")
        self.txt = self.create_text(width/2, 60, fill="white", font=("Arial", 11, "bold"))
        self.update_pos(); self.tag_bind(self.h1, "<B1-Motion>", lambda e: self.move(e, 1)); self.tag_bind(self.h2, "<B1-Motion>", lambda e: self.move(e, 2))
    def update_pos(self):
        x1, x2 = self.margin+((self.v1-self.min_v)/(self.max_v-self.min_v))*self.bw, self.margin+((self.v2-self.min_v)/(self.max_v-self.min_v))*self.bw
        self.coords(self.h1, x1-11, 24, x1+11, 46); self.coords(self.h2, x2-11, 24, x2+11, 46); self.itemconfig(self.txt, text=f"{int(self.v1)} à {int(self.v2)} lettres")
    def move(self, e, h):
        if self.enabled:
            nv = max(self.min_v, min(self.max_v, int(self.min_v + ((e.x - self.margin) / self.bw) * (self.max_v - self.min_v))))
            if h == 1 and nv <= self.v2: self.v1 = nv
            elif h == 2 and nv >= self.v1: self.v2 = nv
            self.update_pos(); (self.callback(self.v1, self.v2) if self.callback else None)
    def activer(self, s): self.enabled = s; self.itemconfig(self.h1, fill=JAUNE if s else GRIS_LIGHT); self.itemconfig(self.h2, fill=ROUGE if s else GRIS_LIGHT)
    def set_vals(self, v1, v2): self.v1, self.v2 = v1, v2; self.update_pos()
    def get_values(self): return int(self.v1), int(self.v2)
