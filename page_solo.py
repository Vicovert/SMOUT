import tkinter as tk
from tkinter import messagebox as tkm
import json, random, os, sys, time, datetime

def get_data_path(filename):
    app_dir = os.path.join(os.getenv('APPDATA'), 'SMOUT_Game')
    if not os.path.exists(app_dir): os.makedirs(app_dir)
    return os.path.join(app_dir, filename)

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_txt_color(hex_color):
    """Calcule si le texte doit être blanc ou noir selon la luminosité du fond"""
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#1a1a1a" if luminance > 0.5 else "white"
    except: return "white"

# --- CONFIGURATION DYNAMIQUE ---
BLEU, ROUGE, JAUNE, BLEU_C, GRIS_LIGHT = '#0a4160', '#ef4444', '#eab308', '#0ea5e9', '#64748b'
GRILLE = "#1a1a1a"
FONT_MONO, FONT_UI = ("Courier", 24, "bold"), ("Helvetica", 12, "bold")
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def apply_theme_solo(theme_data):
    """Met à jour les couleurs globales pour le mode solo"""
    global BLEU, ROUGE, JAUNE, BLEU_C, GRIS_LIGHT, GRILLE
    BLEU = theme_data["bg"]
    ROUGE = theme_data["accent1"]
    JAUNE = theme_data["accent2"]
    BLEU_C = theme_data["highlight"]
    GRIS_LIGHT = theme_data["muted"]
    GRILLE = theme_data.get("grid", get_txt_color(BLEU))

class BoutonPro(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=45, color="#f5deb3", hover_color="#e2bc74"):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command, self.color, self.hover_color = command, color, hover_color
        self.rect = self.draw_round_rect(2, 2, width-2, height-2, 12, fill=color)
        self.txt = self.create_text(width/2, height/2, text=text, fill=get_txt_color(color), font=FONT_UI)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.color))
    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)
    def _on_release(self, e):
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height(): self.command()

class LogoSmout(tk.Canvas):
    def __init__(self, parent, tile_size=110):
        word = "SMOUT"
        gap = 18
        total_w = (tile_size + gap) * len(word)
        super().__init__(parent, width=total_w, height=tile_size + 50, bg=BLEU, highlightthickness=0)
        for i, char in enumerate(word):
            x = i * (tile_size + gap)
            p, s = 10, tile_size - 10
            bg = ROUGE if char == "U" else JAUNE
            dark = self._adjust_color(bg, 0.7)
            light = self._adjust_color(bg, 1.3)
            self.draw_round_rect(x+p+6, p+10, x+s+6, s+10, 20, fill="#042f48")
            self.draw_round_rect(x+p, p+5, x+s, s+5, 20, fill=dark)
            self.draw_round_rect(x+p, p, x+s, s, 20, fill=bg)
            self.draw_round_rect(x+p+5, p+5, x+s-5, p+(s/2.5), 15, fill=light)
            self.create_text(x+tile_size/2, tile_size/2, text=char, fill=get_txt_color(bg), font=("Verdana", int(tile_size*0.5), "bold"))
    
    def _adjust_color(self, hex_color, factor):
        try:
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            new_rgb = [min(255, max(0, int(c * factor))) for c in rgb]
            return '#{:02x}{:02x}{:02x}'.format(*new_rgb)
        except: return hex_color

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

class EcranFin(tk.Frame):
    def __init__(self, parent, controller, rejouer_cmd, menu_cmd):
        super().__init__(parent, bg=BLEU); self.rejouer_cmd, self.menu_cmd = rejouer_cmd, menu_cmd
        self.container = tk.Frame(self, bg="#052132", padx=40, pady=30, highlightbackground=BLEU_C, highlightthickness=2)
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_titre = tk.Label(self.container, text="", font=("Arial Black", 28), bg="#052132")
        self.lbl_stats = tk.Label(self.container, text="", font=FONT_UI, fg="white", bg="#052132")
        self.resume_frame = tk.Frame(self.container, bg="#052132"); self.lbl_mot = tk.Label(self.container, text="", font=("Courier", 18, "bold"), bg="#052132")
        self.btns_frame = tk.Frame(self.container, bg="#052132")
        self.btn_rejouer = BoutonPro(self.btns_frame, "REJOUER", self._on_rejouer, width=140, color="#22c55e")
        self.btn_rejouer.pack(side="left", padx=10)
        BoutonPro(self.btns_frame, "ACCUEIL", self._on_menu, width=140, color="#94a3b8").pack(side="left", padx=10)
    def _on_rejouer(self): self.place_forget(); self.rejouer_cmd()
    def _on_menu(self): self.place_forget(); self.menu_cmd()
    def afficher(self, victoire, mot, historique_donnees, score=0, temps="00:00", mdj=False):
        for widget in self.container.winfo_children(): widget.pack_forget()
        self.lbl_titre.config(text="VICTOIRE !" if victoire else "PERDU...", fg=JAUNE if victoire else ROUGE)
        self.lbl_stats.config(text=f"Score : {score}  |  Temps : {temps}" if victoire else "Dommage !")
        self.lbl_mot.config(text=f"Le mot était : {mot}", fg="white" if victoire else ROUGE)
        self.lbl_titre.pack(pady=(0, 5)); self.lbl_stats.pack(pady=10)
        for w in self.resume_frame.winfo_children(): w.destroy()
        if historique_donnees:
            self.resume_frame.pack(pady=15)
            for ligne in historique_donnees:
                row_f = tk.Frame(self.resume_frame, bg="#052132"); row_f.pack(pady=1)
                for char, coul in ligne: tk.Label(row_f, text=char, bg=coul, fg=get_txt_color(coul), font=("Courier", 11, "bold"), width=2, height=1).pack(side="left", padx=1)
        self.lbl_mot.pack(pady=10); self.btns_frame.pack(pady=(10, 0))
        if mdj: self.btn_rejouer.pack_forget() 
        else: self.btn_rejouer.pack(side="left", padx=10)
        self.place(relx=0, rely=0, relwidth=1, relheight=1); self.tkraise()

class PageSolo(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        self.charger_parametres(); self.charger_mots()
        self.container = tk.Frame(self, bg=BLEU); self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (PageAccueil, PageParametres, PageJeu):
            f = F(parent=self.container, controller=self); self.frames[F.__name__] = f; f.grid(row=0, column=0, sticky="nsew")
        self.show_frame("PageAccueil")
    def charger_parametres(self):
        self.config = {"nb_essais": 6, "nb_lettres_min": 6, "nb_lettres_max": 10, "mdj": False, "last_mdj": ""}
        path = get_data_path('config.json')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f: self.config.update(json.load(f))
            except: pass
    def sauver_parametres(self):
        with open(get_data_path('config.json'), 'w') as f:
            json.dump(self.config, f)
    def charger_mots(self):
        def lire(p):
            p = resource_path(p)
            if not os.path.exists(p): return []
            for enc in ['utf-8', 'latin-1']:
                try:
                    with open(p, 'r', encoding=enc) as f: return [l.strip().upper() for l in f if l.strip()]
                except: continue
            return []
        self.liste_mots = lire('fichiers/mots_trouver.txt'); self.banque_verif = set(lire('fichiers/banque_mots.txt')) or set(self.liste_mots)
    def show_frame(self, name):
        f = self.frames[name]; (f.initialiser_partie() if name == "PageJeu" else None); f.tkraise()

class PageAccueil(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU)
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.45, anchor="center")
        LogoSmout(c, 110).pack(pady=(0, 60))
        BoutonPro(c, text="JOUER", command=lambda: self.lancer(controller, False)).pack(pady=8)
        BoutonPro(c, text="MOT DU JOUR", command=lambda: self.lancer(controller, True)).pack(pady=8)
        BoutonPro(c, text="PARAMÈTRES", command=lambda: controller.show_frame("PageParametres"), color="#cbd5e1").pack(pady=8)
        BoutonPro(c, text="ACCUEIL", command=controller.controller.creer_menu_accueil, color="#94a3b8").pack(pady=8)
    def lancer(self, c, d): c.config.update({"mdj": d}); c.show_frame("PageJeu")

class PageJeu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller, self.timer_actif = controller, False
        self.game_zone = tk.Frame(self, bg=BLEU); self.game_zone.place(relx=0.5, rely=0.5, anchor="center")
    def initialiser_partie(self):
        self.timer_actif = False; [w.destroy() for w in self.game_zone.winfo_children()]
        conf, mots = self.controller.config, self.controller.liste_mots
        auj = datetime.datetime.now().strftime("%Y-%m-%d")
        
        if conf["mdj"]:
            if conf.get("last_mdj") == auj:
                tk.Label(self.game_zone, text="DÉJÀ JOUÉ AUJOURD'HUI !", font=FONT_MONO, fg=ROUGE, bg=BLEU).pack(pady=20)
                BoutonPro(self.game_zone, "RETOUR", lambda: self.controller.show_frame("PageAccueil")).pack()
                return
            mots_tries = sorted(mots); random.seed(auj.replace("-",""))
            self.mot = random.choice(mots_tries); random.seed(); self.nb_essais_partie = 7
        else:
            mi, ma = conf["nb_lettres_min"], conf["nb_lettres_max"]; filtre = [m for m in mots if mi <= len(m) <= ma]
            self.mot = random.choice(filtre if filtre else mots); self.nb_essais_partie = conf["nb_essais"]
            
        self.score_initial, self.penalite_dict, self.historique_complet, self.fini_local = (len(self.mot) * 100) * (13 - self.nb_essais_partie), 0, [], False
        self.statut_lettres, self.boutons_clavier = {l: BLEU for l in ALPHABET}, {}
        header = tk.Frame(self.game_zone, bg=BLEU); header.pack(fill="x")
        self.label_score = tk.Label(header, text="SCORE: 0", fg=JAUNE, bg=BLEU, font=FONT_UI); self.label_score.pack(side="right", padx=10)
        self.label_timer = tk.Label(header, text="00:00", fg=get_txt_color(BLEU), bg=BLEU, font=FONT_UI); self.label_timer.pack(side="right", padx=10)
        self.grid_frame = tk.Frame(self.game_zone, bg=BLEU); self.grid_frame.pack(pady=10)
        self.ligne_actuelle, self.mot_tape, self.grille_labels = 0, [self.mot[0]], []
        for l in range(self.nb_essais_partie):
            ligne = []
            for c in range(len(self.mot)):
                case = tk.Label(self.grid_frame, text="", font=FONT_MONO, width=2, height=1, fg=get_txt_color(BLEU), bg=BLEU, borderwidth=1, relief="solid", highlightbackground=GRILLE, highlightthickness=1)
                case.grid(row=l, column=c, padx=2, pady=2); ligne.append(case)
            self.grille_labels.append(ligne)
        self.creer_clavier(); actions = tk.Frame(self.game_zone, bg=BLEU); actions.pack(pady=20)
        BoutonPro(actions, "VALIDER", self.valider, width=130, color="#22c55e").pack(side="left", padx=10)
        BoutonPro(actions, "EFFACER", self.effacer, width=130, color="#94a3b8").pack(side="left", padx=10)
        BoutonPro(actions, "ABANDON", lambda: self.gestion_fin("PERDU"), width=130, color="#ef4444").pack(side="left", padx=10)
        self.overlay_fin = EcranFin(self, self.controller, self.initialiser_partie, lambda: self.controller.show_frame("PageAccueil"))
        self.debut_temps, self.timer_actif = time.time(), True; self.update_loop(); self.winfo_toplevel().bind("<Key>", self.clavier_physique); self.maj_affichage()
    def update_loop(self):
        if self.timer_actif:
            ecoule = int(time.time() - self.debut_temps); self.label_timer.config(text=f"{ecoule // 60:02d}:{ecoule % 60:02d}")
            self.label_score.config(text=f"SCORE: {max(0, self.score_initial - (ecoule * 2) - self.penalite_dict)}"); self.after(1000, self.update_loop)
    def valider(self):
        if len(self.mot_tape) != len(self.mot) or self.fini_local: return
        tentative = "".join(self.mot_tape)
        if tentative not in self.controller.banque_verif and tentative != self.mot: self.penalite_dict += 100; return
        res, secret = [GRIS_LIGHT]*len(self.mot), list(self.mot)
        for i in range(len(self.mot)):
            if self.mot_tape[i] == self.mot[i]: res[i], secret[i] = ROUGE, None
        for i in range(len(self.mot)):
            if res[i] != ROUGE and self.mot_tape[i] in secret: res[i] = JAUNE; secret[secret.index(self.mot_tape[i])] = None
        for i, char in enumerate(self.mot_tape):
            cur = self.statut_lettres.get(char, BLEU)
            if res[i] == ROUGE: self.statut_lettres[char] = ROUGE
            elif res[i] == JAUNE and cur != ROUGE: self.statut_lettres[char] = JAUNE
            elif res[i] == GRIS_LIGHT and cur not in [ROUGE, JAUNE]: self.statut_lettres[char] = GRIS_LIGHT
        self.maj_clavier(); self.historique_complet.append([(self.mot_tape[i], res[i]) for i in range(len(self.mot))])
        for i, color in enumerate(res): self.grille_labels[self.ligne_actuelle][i].config(bg=color, fg=get_txt_color(color))
        self.update_idletasks()
        if tentative == self.mot: self.fini_local = True; self.gestion_fin("VICTOIRE")
        elif self.ligne_actuelle + 1 >= self.nb_essais_partie: self.fini_local = True; self.gestion_fin("PERDU")
        else: self.ligne_actuelle += 1; self.mot_tape = [self.mot[0]]; self.maj_affichage()
    def gestion_fin(self, statut):
        self.timer_actif = False; self.winfo_toplevel().unbind("<Key>")
        if self.controller.config["mdj"]:
            self.controller.config["last_mdj"] = datetime.datetime.now().strftime("%Y-%m-%d")
            self.controller.sauver_parametres()
        self.overlay_fin.afficher(statut == "VICTOIRE", self.mot, self.historique_complet, self.label_score.cget("text").split(": ")[1], self.label_timer.cget("text"), self.controller.config["mdj"])
    def creer_clavier(self):
        f = tk.Frame(self.game_zone, bg=BLEU); f.pack(pady=10)
        for lettres in ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ"]:
            row = tk.Frame(f, bg=BLEU); row.pack()
            for c in lettres:
                btn = tk.Button(row, text=c, width=3, bg=BLEU, fg=get_txt_color(BLEU), font=("Helvetica", 10, "bold"), relief="raised", bd=2, command=lambda char=c: self.ajouter_lettre(char))
                btn.pack(side="left", padx=2, pady=2); self.boutons_clavier[c] = btn
    def maj_clavier(self):
        for char, color in self.statut_lettres.items():
            if char in self.boutons_clavier:
                if color == GRIS_LIGHT:
                    self.boutons_clavier[char].config(bg=color, fg="#6b7280", relief="flat", font=("Helvetica", 10, "bold overstrike"))
                else:
                    self.boutons_clavier[char].config(bg=color, fg=get_txt_color(color), relief="raised", font=("Helvetica", 10, "bold"))
    def clavier_physique(self, e):
        if not self.winfo_viewable() or self.fini_local: return
        c = e.char.upper()
        if c in ALPHABET: self.ajouter_lettre(c)
        elif e.keysym == "BackSpace": self.effacer()
        elif e.keysym == "Return": self.valider()
    def ajouter_lettre(self, c):
        if len(self.mot_tape) < len(self.mot) and not self.fini_local: self.mot_tape.append(c); self.maj_affichage()
    def effacer(self):
        if len(self.mot_tape) > 1 and not self.fini_local: self.mot_tape.pop(); self.maj_affichage()
    def maj_affichage(self):
        if self.fini_local: return
        for i, c in enumerate(self.mot_tape): 
            coul = ROUGE if i == 0 else BLEU
            self.grille_labels[self.ligne_actuelle][i].config(text=c, bg=coul, fg=get_txt_color(coul))
        for i in range(len(self.mot_tape), len(self.mot)): self.grille_labels[self.ligne_actuelle][i].config(text="", bg=BLEU)

class PageParametres(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="PARAMÈTRES", font=("Verdana", 24, "bold"), fg=get_txt_color(BLEU), bg=BLEU).pack(pady=20)
        tk.Label(c, text="NOMBRE D'ESSAIS", fg=get_txt_color(BLEU), bg=BLEU, font=FONT_UI).pack(pady=(10,0))
        self.s_essais = SingleSlider(c, 4, 8, controller.config["nb_essais"]); self.s_essais.pack(pady=10)
        self.s_len = RangeSlider(c, 6, 10, controller.config["nb_lettres_min"], controller.config["nb_lettres_max"]); self.s_len.pack(pady=10)
        BoutonPro(c, "ENREGISTRER", self.save, color="#cbd5e1").pack(pady=10); BoutonPro(c, text="RETOUR", command=lambda: controller.show_frame("PageAccueil"), color="#94a3b8").pack()
    def save(self):
        mi, ma = self.s_len.get_values()
        self.controller.config.update({"nb_essais": self.s_essais.get_value(), "nb_lettres_min": mi, "nb_lettres_max": ma})
        self.controller.sauver_parametres()
        self.controller.show_frame("PageAccueil")

class SingleSlider(tk.Canvas):
    def __init__(self, parent, min_val, max_val, init_val, width=350, height=80):
        super().__init__(parent, width=width, height=height, bg=BLEU, highlightthickness=0)
        self.min_val, self.max_val, self.v = min_val, max_val, init_val; self.margin, self.bw, self.h = 25, width - 50, height
        self.create_line(self.margin, height/2, width-self.margin, height/2, fill=get_txt_color(BLEU), width=4)
        self.handle = self.create_oval(0, 0, 24, 24, fill=BLEU_C, outline="white"); self.txt_val = self.create_text(0, 0, fill=get_txt_color(BLEU), font=FONT_UI); self.update_positions(); self.tag_bind(self.handle, "<B1-Motion>", self.move)
    def update_positions(self):
        ratio = (self.v - self.min_val) / (self.max_val - self.min_val); x = self.margin + ratio * self.bw
        self.coords(self.handle, x-12, self.h/2-12, x+12, self.h/2+12); self.coords(self.txt_val, x, self.h - 15); self.itemconfig(self.txt_val, text=str(int(self.v)))
    def move(self, event):
        ratio = (event.x - self.margin) / self.bw; self.v = max(self.min_val, min(self.max_val, int(self.min_val + ratio * (self.max_val - self.min_val)))); self.update_positions()
    def get_value(self): return int(self.v)

class RangeSlider(tk.Canvas):
    def __init__(self, parent, min_val, max_val, init_min, init_max, width=350, height=100):
        super().__init__(parent, width=width, height=height, bg=BLEU, highlightthickness=0)
        self.min_val, self.max_val, self.v_min, self.v_max = min_val, max_val, init_min, init_max; self.margin, self.bw, self.h = 25, width - 50, height
        self.create_text(width/2, 10, text="TAILLE DU MOT", fill=get_txt_color(BLEU), font=("Helvetica", 8, "bold"))
        self.create_line(self.margin, height/2, width-self.margin, height/2, fill=get_txt_color(BLEU), width=4)
        self.h_min = self.create_oval(0, 0, 24, 24, fill=JAUNE, outline="white"); self.h_max = self.create_oval(0, 0, 24, 24, fill=ROUGE, outline="white")
        self.txt = self.create_text(width/2, self.h - 15, fill=get_txt_color(BLEU), font=("Arial", 9, "bold"))
        self.update_positions(); self.tag_bind(self.h_min, "<B1-Motion>", lambda e: self.move(e, "min")); self.tag_bind(self.h_max, "<B1-Motion>", lambda e: self.move(e, "max"))
    def update_positions(self):
        y_mid = self.h / 2
        for side, val, handle in [("min", self.v_min, self.h_min), ("max", self.v_max, self.h_max)]:
            ratio = (val - self.min_val) / (self.max_val - self.min_val); x = self.margin + ratio * self.bw
            self.coords(handle, x-12, y_mid-12, x+12, y_mid+12)
        self.itemconfig(self.txt, text=f"{int(self.v_min)} à {int(self.v_max)} lettres")
    def move(self, event, side):
        ratio = (event.x - self.margin) / self.bw; new_v = max(self.min_val, min(self.max_val, int(self.min_val + ratio * (self.max_val - self.min_val))))
        if side == "min" and new_v <= self.v_max: self.v_min = new_v
        elif side == "max" and new_v >= self.v_min: self.v_max = new_v
        self.update_positions()
    def get_values(self): return int(self.v_min), int(self.v_max)
