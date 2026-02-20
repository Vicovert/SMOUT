import tkinter as tk
from tkinter import messagebox as tkm
from tkinter import simpledialog
import json
import random
import os
import sys
import time
import requests 
from datetime import datetime
from functools import partial

# --- CONFIGURATION DES CHEMINS ---

def get_data_path(filename):
    app_dir = os.path.join(os.getenv('APPDATA'), 'SMOUT_Game')
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    return os.path.join(app_dir, filename)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CONFIGURATION VISUELLE ---
BLEU, ROUGE, JAUNE, BLEU_C, GRIS_LIGHT = '#0a4160', '#ef4444', '#eab308', '#0ea5e9', '#64748b'
FONT_MONO, FONT_UI = ("Courier", 24, "bold"), ("Helvetica", 12, "bold")
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# --- COMPOSANTS UI ---

class BoutonPro(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=45, color="#f5deb3", hover_color="#e2bc74"):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command, self.color, self.hover_color = command, color, hover_color
        self.rect = self.draw_round_rect(2, 2, width-2, height-2, 12, fill=color)
        self.txt = self.create_text(width/2, height/2, text=text, fill=BLEU, font=FONT_UI)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_release(self, e):
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            self.command()

    def on_enter(self, e): self.itemconfig(self.rect, fill=self.hover_color)
    def on_leave(self, e): self.itemconfig(self.rect, fill=self.color)

class LogoSmout(tk.Canvas):
    def __init__(self, parent, tile_size=110):
        word = "SMOUT"
        gap = 18
        total_w = (tile_size + gap) * len(word)
        super().__init__(parent, width=total_w, height=tile_size + 50, bg=BLEU, highlightthickness=0)
        for i, char in enumerate(word):
            x = i * (tile_size + gap)
            p, s = 10, tile_size - 10
            bg, dark, light = (ROUGE, "#991b1b", "#f87171") if char == "U" else (JAUNE, "#a16207", "#fef08a")
            self.draw_round_rect(x+p+6, p+10, x+s+6, s+10, 20, fill="#042f48")
            self.draw_round_rect(x+p, p+5, x+s, s+5, 20, fill=dark)
            self.draw_round_rect(x+p, p, x+s, s, 20, fill=bg)
            self.draw_round_rect(x+p+5, p+5, x+s-5, p+(s/2.5), 15, fill=light)
            self.create_text(x+tile_size/2, tile_size/2, text=char, fill="white", font=("Verdana", int(tile_size*0.5), "bold"))

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

# --- OVERLAY DE FIN ---

class EcranFin(tk.Frame):
    def __init__(self, parent, controller, rejouer_cmd, menu_cmd):
        super().__init__(parent, bg=BLEU)
        self.rejouer_cmd, self.menu_cmd = rejouer_cmd, menu_cmd
        self.container = tk.Frame(self, bg="#052132", padx=40, pady=30, highlightbackground=BLEU_C, highlightthickness=2)
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_titre = tk.Label(self.container, text="", font=("Arial Black", 28), bg="#052132")
        self.lbl_deja_joue = tk.Label(self.container, text="", font=("Helvetica", 10, "bold"), bg="#052132")
        self.lbl_stats = tk.Label(self.container, text="", font=FONT_UI, fg="white", bg="#052132")
        self.resume_frame = tk.Frame(self.container, bg="#052132")
        self.lbl_mot = tk.Label(self.container, text="", font=("Courier", 18, "bold"), bg="#052132")
        self.btns_frame = tk.Frame(self.container, bg="#052132")
        BoutonPro(self.btns_frame, "REJOUER", self._on_rejouer, width=140, color="#22c55e", hover_color="#16a34a").pack(side="left", padx=10)
        BoutonPro(self.btns_frame, "MENU", self._on_menu, width=140, color="#94a3b8", hover_color="#64748b").pack(side="left", padx=10)

    def _on_rejouer(self): self.place_forget(); self.rejouer_cmd()
    def _on_menu(self): self.place_forget(); self.menu_cmd()

    def afficher(self, victoire, mot, deja_joue, historique_donnees, score=0, temps="00:00"):
        for widget in self.container.winfo_children(): widget.pack_forget()
        self.lbl_titre.config(text="VICTOIRE !" if victoire else "PERDU...", fg=JAUNE if victoire else ROUGE)
        self.lbl_deja_joue.config(text="● DÉJÀ JOUÉ AUJOURD'HUI" if deja_joue else "", fg=GRIS_LIGHT)
        self.lbl_stats.config(text=f"Score : {score}  |  Temps : {temps}" if victoire else "Dommage, retente ta chance !")
        self.lbl_mot.config(text=f"Le mot était : {mot}", fg="white" if victoire else ROUGE)
        self.lbl_titre.pack(pady=(0, 5))
        if deja_joue: self.lbl_deja_joue.pack(pady=2)
        self.lbl_stats.pack(pady=10)
        for w in self.resume_frame.winfo_children(): w.destroy()
        if historique_donnees:
            self.resume_frame.pack(pady=15)
            for ligne in historique_donnees:
                row_f = tk.Frame(self.resume_frame, bg="#052132")
                row_f.pack(pady=1)
                for char, coul in ligne:
                    tk.Label(row_f, text=char, bg=coul, fg="white", font=("Courier", 11, "bold"), width=2, height=1).pack(side="left", padx=1)
            self.lbl_mot.pack(pady=10)
        else: self.lbl_mot.pack(pady=(40, 20))
        self.btns_frame.pack(pady=(10, 0))
        self.place(relx=0, rely=0, relwidth=1, relheight=1); self.tkraise()

# --- APPLICATION PRINCIPALE ---

class MotusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SMOUT")
        self.geometry("1100x850")
        self.configure(bg=BLEU)
        
        main_icon = resource_path('icones/logo.ico')
        if os.path.exists(main_icon):
            try: self.iconbitmap(main_icon)
            except: pass

        self.charger_parametres(); self.charger_mots(); self.charger_historique()
        self.container = tk.Frame(self, bg=BLEU); self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1); self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (PageAccueil, PageParametres, PageJeu, PageCode):
            f = F(parent=self.container, controller=self); self.frames[F.__name__] = f; f.grid(row=0, column=0, sticky="nsew")
        self.show_frame("PageAccueil")

    def charger_parametres(self):
        def_config = {"nb_essais": 6, "nb_lettres_min": 6, "nb_lettres_max": 10, "multi": False, "mdj": False}
        path = get_data_path('config.json')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f: self.config = {**def_config, **json.load(f)}
            except: self.config = def_config
        else: self.config = def_config

    def sauver_parametres(self):
        path = get_data_path('config.json')
        with open(path, 'w') as f: json.dump(self.config, f)

    def charger_mots(self):
        def lire(p):
            p = resource_path(p)
            if not os.path.exists(p): return []
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(p, 'r', encoding=enc) as f: return [l.strip().split()[0].upper() for l in f if l.strip()]
                except: continue
            return []
        self.liste_mots = lire('fichiers/mots_trouver.txt')
        self.banque_verif = set(lire('fichiers/banque_mots.txt')) or set(self.liste_mots)
        if not self.liste_mots: self.liste_mots = ["PYTHON", "MOTUS", "SMOUT"]

    def charger_historique(self):
        self.historique = set()
        jour_actuel = datetime.now().strftime("%d")
        pd, pm = get_data_path('date_triche.txt'), get_data_path('numeros_joues.txt')
        if os.path.exists(pd):
            with open(pd, 'r') as f:
                if f.read().strip() != jour_actuel:
                    if os.path.exists(pm): open(pm, 'w').close()
        with open(pd, 'w') as f: f.write(jour_actuel)
        if os.path.exists(pm):
            with open(pm, 'r') as f: self.historique = {l.strip() for l in f if l.strip()}

    def ajouter_a_historique(self, index):
        if str(index) not in self.historique:
            self.historique.add(str(index))
            with open(get_data_path('numeros_joues.txt'), 'a') as f: f.write(f"{index}\n")

    def changer_icone(self, page_name):
        icon_mapping = {"PageAccueil": "icones/icon_a.ico", "PageJeu": "icones/icon_j.ico", "PageParametres": "icones/icon_s.ico", "PageCode": "icones/icon_n.ico"}
        path = resource_path(icon_mapping.get(page_name, 'icones/logo.ico'))
        if os.path.exists(path):
            try:
                img = tk.PhotoImage(file=path)
                self.tk.call('wm', 'iconphoto', self._w, img)
            except: pass

    def show_frame(self, name):
        f = self.frames[name]
        self.changer_icone(name)
        if name == "PageCode": f.nettoyer()
        if name == "PageJeu": f.initialiser_partie()
        f.tkraise()

class PageAccueil(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU)
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.45, anchor="center")
        LogoSmout(c, 110).pack(pady=(0, 60))
        for t, m, d in [("JOUER", False, False), ("REJOINDRE", True, False), ("MOT DU JOUR", False, True)]:
            cmd = partial(self.lancer, controller, m, d) if t != "REJOINDRE" else (lambda: controller.show_frame("PageCode"))
            BoutonPro(c, text=t, command=cmd).pack(pady=8)
        BoutonPro(c, text="PARAMÈTRES", command=lambda: controller.show_frame("PageParametres"), color="#cbd5e1").pack(pady=8)
        BoutonPro(c, text="QUITTER", command=controller.destroy, color="#f87171").pack(pady=8)
    def lancer(self, c, m, d): c.config.update({"multi": m, "mdj": d}); c.show_frame("PageJeu")

class PageJeu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU)
        self.controller, self.timer_actif = controller, False
        self.game_zone = tk.Frame(self, bg=BLEU); self.game_zone.place(relx=0.5, rely=0.5, anchor="center")

    def initialiser_partie(self):
        self.timer_actif = False
        for w in self.game_zone.winfo_children(): w.destroy()
        conf, mots = self.controller.config, self.controller.liste_mots
        if conf["mdj"]:
            random.seed(datetime.now().strftime("%Y%m%d"))
            self.idx_mot = random.randint(0, len(mots)-1); self.mot = mots[self.idx_mot]; random.seed(); self.nb_essais_partie = 7
        elif conf["multi"]:
            self.idx_mot = max(0, min(conf.get("code_partie", 0), len(mots)-1)); self.mot = mots[self.idx_mot]; self.nb_essais_partie = conf["nb_essais"]
        else:
            random.seed(time.time()); mi, ma = conf["nb_lettres_min"], conf["nb_lettres_max"]
            filtre = [m for m in mots if mi <= len(m) <= ma]; self.mot = random.choice(filtre if filtre else mots); self.idx_mot, self.nb_essais_partie = mots.index(self.mot), conf["nb_essais"]
        
        self.deja_joue_partie = str(self.idx_mot) in self.controller.historique
        self.historique_complet = []
        self.score_initial, self.penalite_dict = (len(self.mot) * 100) * (13 - self.nb_essais_partie), 0
        self.statut_lettres, self.boutons_clavier = {l: BLEU for l in ALPHABET}, {}
        
        header = tk.Frame(self.game_zone, bg=BLEU); header.pack(fill="x")
        mode_txt = ("MOT DU JOUR" if conf["mdj"] else f"CODE: {self.idx_mot}") + (" | DÉJÀ JOUÉ" if self.deja_joue_partie else "")
        tk.Label(header, text=mode_txt, fg="white", bg=BLEU, font=("Helvetica", 10, "bold")).pack(side="left", padx=10)
        self.label_score = tk.Label(header, text="SCORE: 0", fg=JAUNE, bg=BLEU, font=FONT_UI); self.label_score.pack(side="right", padx=10)
        self.label_timer = tk.Label(header, text="00:00", fg="white", bg=BLEU, font=FONT_UI); self.label_timer.pack(side="right", padx=10)
        
        self.grid_frame = tk.Frame(self.game_zone, bg=BLEU); self.grid_frame.pack(pady=10)
        self.ligne_actuelle, self.mot_tape, self.grille_labels = 0, [self.mot[0]], []
        for l in range(self.nb_essais_partie):
            ligne = []
            for c in range(len(self.mot)):
                case = tk.Label(self.grid_frame, text="", font=FONT_MONO, width=2, height=1, fg="white", bg=BLEU, borderwidth=2, relief="solid")
                case.grid(row=l, column=c, padx=2, pady=2); ligne.append(case)
            self.grille_labels.append(ligne)
        
        self.creer_clavier()
        actions = tk.Frame(self.game_zone, bg=BLEU); actions.pack(pady=20)
        BoutonPro(actions, "VALIDER", self.valider, width=130, color="#22c55e").pack(side="left", padx=10)
        BoutonPro(actions, "EFFACER", self.effacer, width=130, color="#94a3b8").pack(side="left", padx=10)
        BoutonPro(actions, "ABANDON", self.abandon, width=130, color="#ef4444").pack(side="left", padx=10)
        
        self.overlay_fin = EcranFin(self, self.controller, self.initialiser_partie, lambda: self.controller.show_frame("PageAccueil"))
        self.debut_temps, self.timer_actif = time.time(), True
        self.controller.ajouter_a_historique(self.idx_mot)
        self.update_loop(); self.controller.bind("<Key>", self.clavier_physique); self.maj_affichage()

    def update_loop(self):
        if self.timer_actif:
            ecoule = int(time.time() - self.debut_temps)
            self.label_timer.config(text=f"{ecoule // 60:02d}:{ecoule % 60:02d}")
            score = max(0, self.score_initial - (ecoule * 2) - self.penalite_dict)
            self.label_score.config(text=f"SCORE: {score}")
            self.after(1000, self.update_loop)

    def valider(self):
        if len(self.mot_tape) != len(self.mot): return
        tentative = "".join(self.mot_tape)
        if tentative not in self.controller.banque_verif and tentative != self.mot:
            self.penalite_dict += 100; self.label_score.config(fg=ROUGE); self.after(500, lambda: self.label_score.config(fg=JAUNE)); return
        
        res, secret = [GRIS_LIGHT]*len(self.mot), list(self.mot)
        for i in range(len(self.mot)):
            if self.mot_tape[i] == self.mot[i]: res[i], secret[i] = ROUGE, None
        for i in range(len(self.mot)):
            if res[i] != ROUGE and self.mot_tape[i] in secret: 
                res[i] = JAUNE; secret[secret.index(self.mot_tape[i])] = None
        
        ligne_donnees = []
        for i in range(len(self.mot)): ligne_donnees.append((self.mot_tape[i], res[i]))
        self.historique_complet.append(ligne_donnees)
        
        for i, color in enumerate(res):
            self.grille_labels[self.ligne_actuelle][i].config(bg=color)
            char = self.mot_tape[i]
            if color == ROUGE: self.statut_lettres[char] = ROUGE
            elif color == JAUNE and self.statut_lettres[char] != ROUGE: self.statut_lettres[char] = JAUNE
            elif color == GRIS_LIGHT and self.statut_lettres[char] == BLEU: self.statut_lettres[char] = GRIS_LIGHT
            self.boutons_clavier[char].config(bg=self.statut_lettres[char])
            
        if tentative == self.mot: self.gestion_fin("VICTOIRE")
        elif self.ligne_actuelle + 1 >= self.nb_essais_partie: self.gestion_fin("PERDU")
        else: self.ligne_actuelle += 1; self.mot_tape = [self.mot[0]]; self.maj_affichage()

    def gestion_fin(self, statut):
        self.timer_actif = False; self.controller.unbind("<Key>")
        score = self.label_score.cget("text").split(": ")[1]
        self.overlay_fin.afficher(statut == "VICTOIRE", self.mot, self.deja_joue_partie, self.historique_complet, score, self.label_timer.cget("text"))

    def abandon(self): self.gestion_fin("PERDU")
    def creer_clavier(self):
        f = tk.Frame(self.game_zone, bg=BLEU); f.pack(pady=10)
        for lettres in ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ"]:
            row = tk.Frame(f, bg=BLEU); row.pack()
            for c in lettres:
                btn = tk.Button(row, text=c, width=3, bg=BLEU, fg="white", font=("Helvetica", 10, "bold"), command=lambda char=c: self.ajouter_lettre(char))
                btn.pack(side="left", padx=2, pady=2); self.boutons_clavier[c] = btn
    def clavier_physique(self, e):
        if not self.winfo_viewable(): return
        sym, c = e.keysym, e.char.upper()
        if len(c) == 1 and c in ALPHABET: self.ajouter_lettre(c)
        elif sym == "BackSpace": self.effacer()
        elif sym == "Return": self.valider()
    def ajouter_lettre(self, c):
        if len(self.mot_tape) < len(self.mot): self.mot_tape.append(c); self.maj_affichage()
    def effacer(self):
        if len(self.mot_tape) > 1: self.mot_tape.pop(); self.maj_affichage()
    def maj_affichage(self):
        for i, c in enumerate(self.mot_tape): self.grille_labels[self.ligne_actuelle][i].config(text=c, bg=ROUGE if i == 0 else BLEU)
        for i in range(len(self.mot_tape), len(self.mot)): self.grille_labels[self.ligne_actuelle][i].config(text="", bg=BLEU)

class PageCode(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="CODE PARTIE", font=("Helvetica", 20, "bold"), fg="white", bg=BLEU).pack(pady=20)
        self.e = tk.Entry(c, font=("Helvetica", 18), justify="center"); self.e.pack(pady=10)
        BoutonPro(c, text="VALIDER", command=self.valider, color="#22c55e").pack(pady=10)
        BoutonPro(c, text="RETOUR", command=lambda: controller.show_frame("PageAccueil"), color="#94a3b8").pack(pady=5)
    
    def nettoyer(self):
        """ Vide le champ et donne le focus automatiquement """
        self.e.delete(0, tk.END)
        self.e.focus_set() # <--- FOCUS AUTOMATIQUE ICI

    def valider(self):
        if self.e.get().isdigit():
            self.controller.config.update({"multi": True, "mdj": False, "code_partie": int(self.e.get())})
            self.controller.show_frame("PageJeu")

class PageParametres(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="PARAMÈTRES", font=("Verdana", 24, "bold"), fg="white", bg=BLEU).pack(pady=20)
        tk.Label(c, text="NOMBRE D'ESSAIS", fg='white', bg=BLEU, font=FONT_UI).pack(pady=(10,0))
        self.s_essais = SingleSlider(c, 4, 12, controller.config["nb_essais"]); self.s_essais.pack(pady=10)
        tk.Label(c, text="LONGUEUR MOT", fg='white', bg=BLEU, font=FONT_UI).pack(pady=(20,0))
        self.s_len = RangeSlider(c, 6, 12, controller.config["nb_lettres_min"], controller.config["nb_lettres_max"]); self.s_len.pack(pady=10)
        BoutonPro(c, text="ENREGISTRER", command=self.save, color="#cbd5e1").pack(pady=30)
    def save(self):
        mi, ma = self.s_len.get_values()
        self.controller.config.update({"nb_essais": self.s_essais.get_value(), "nb_lettres_min": mi, "nb_lettres_max": ma})
        self.controller.sauver_parametres(); self.controller.show_frame("PageAccueil")

# Sliders
class SingleSlider(tk.Canvas):
    def __init__(self, parent, min_val, max_val, init_val, width=350, height=80):
        super().__init__(parent, width=width, height=height, bg=BLEU, highlightthickness=0)
        self.min_val, self.max_val, self.v = min_val, max_val, init_val
        self.margin, self.bw, self.h = 25, width - 50, height
        self.create_line(self.margin, height/2, width-self.margin, height/2, fill="white", width=4)
        self.handle = self.create_oval(0, 0, 24, 24, fill=BLEU_C, outline="white")
        self.txt_val = self.create_text(0, 0, fill="white", font=FONT_UI); self.update_positions(); self.tag_bind(self.handle, "<B1-Motion>", self.move)
    def update_positions(self):
        ratio = (self.v - self.min_val) / (self.max_val - self.min_val); x = self.margin + ratio * self.bw
        self.coords(self.handle, x-12, self.h/2-12, x+12, self.h/2+12); self.coords(self.txt_val, x, self.h - 15); self.itemconfig(self.txt_val, text=str(int(self.v)))
    def move(self, event):
        ratio = (event.x - self.margin) / self.bw; self.v = max(self.min_val, min(self.max_val, int(self.min_val + ratio * (self.max_val - self.min_val)))); self.update_positions()
    def get_value(self): return int(self.v)

class RangeSlider(tk.Canvas):
    def __init__(self, parent, min_val, max_val, init_min, init_max, width=350, height=100):
        super().__init__(parent, width=width, height=height, bg=BLEU, highlightthickness=0)
        self.min_val, self.max_val, self.v_min, self.v_max = min_val, max_val, init_min, init_max
        self.margin, self.bw, self.h = 25, width - 50, height
        self.create_line(self.margin, height/2, width-self.margin, height/2, fill="white", width=4)
        self.h_min = self.create_oval(0, 0, 24, 24, fill=JAUNE, outline="white"); self.h_max = self.create_oval(0, 0, 24, 24, fill=ROUGE, outline="white")
        self.lbl_min = self.create_text(0, 15, text="MIN", fill="white", font=("Helvetica", 9, "bold")); self.lbl_max = self.create_text(0, 15, text="MAX", fill="white", font=("Helvetica", 9, "bold"))
        self.txt_min = self.create_text(0, 0, fill="white", font=FONT_UI); self.txt_max = self.create_text(0, 0, fill="white", font=FONT_UI)
        self.update_positions(); self.tag_bind(self.h_min, "<B1-Motion>", lambda e: self.move(e, "min")); self.tag_bind(self.h_max, "<B1-Motion>", lambda e: self.move(e, "max"))
    def update_positions(self):
        y_mid = self.h / 2
        for side, val, handle, txt, lbl in [("min", self.v_min, self.h_min, self.txt_min, self.lbl_min), ("max", self.v_max, self.h_max, self.txt_max, self.lbl_max)]:
            ratio = (val - self.min_val) / (self.max_val - self.min_val); x = self.margin + ratio * self.bw
            self.coords(handle, x-12, y_mid-12, x+12, y_mid+12); self.coords(txt, x, self.h - 15); self.coords(lbl, x, 15); self.itemconfig(txt, text=str(int(val)))
    def move(self, event, side):
        ratio = (event.x - self.margin) / self.bw; new_v = max(self.min_val, min(self.max_val, int(self.min_val + ratio * (self.max_val - self.min_val))))
        if side == "min" and new_v <= self.v_max: self.v_min = new_v
        elif side == "max" and new_v >= self.v_min: self.v_max = new_v
        self.update_positions()
    def get_values(self): return int(self.v_min), int(self.v_max)

if __name__ == "__main__":
    app = MotusApp(); app.mainloop()
