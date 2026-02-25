import tkinter as tk
from tkinter import messagebox as tkm
import json, random, os, sys, time, requests, threading, webbrowser
from pathlib import Path

# --- CONFIGURATION DYNAMIQUE ---
FIREBASE_URL = "https://smout-multi-default-rtdb.europe-west1.firebasedatabase.app/"
BLEU, ROUGE, JAUNE, BLEU_C, GRIS_LIGHT = '#0a4160', '#ef4444', '#eab308', '#0ea5e9', '#64748b'
GRILLE = "#1a1a1a"
FONT_MONO, FONT_UI = ("Courier", 24, "bold"), ("Helvetica", 12, "bold")
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def apply_theme_multi(theme_data):
    """Met à jour les couleurs globales du jeu"""
    global BLEU, ROUGE, JAUNE, BLEU_C, GRIS_LIGHT, GRILLE
    BLEU = theme_data["bg"]
    ROUGE = theme_data["accent1"]
    JAUNE = theme_data["accent2"]
    BLEU_C = theme_data["highlight"]
    GRIS_LIGHT = theme_data["muted"]
    GRILLE = theme_data.get("grid", get_txt_color(BLEU))

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
            bg = ROUGE if char == "U" else JAUNE
            dark = self._adjust_color(bg, 0.7)
            light = self._adjust_color(bg, 1.3)
            
            self.draw_round_rect(x+p+4, p+8, x+s+4, s+8, 15, fill="#042f48")
            self.draw_round_rect(x+p, p+4, x+s, s+4, 15, fill=dark)
            self.draw_round_rect(x+p, p, x+s, s, 15, fill=bg)
            self.draw_round_rect(x+p+4, p+4, x+s-4, p+(s/2.5), 12, fill=light)
            self.create_text(x+tile_size/2, tile_size/2, text=char, fill=get_txt_color(bg), font=("Verdana", int(tile_size*0.5), "bold"))
    
    def _adjust_color(self, hex_color, factor):
        try:
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            new_rgb = [min(255, max(0, int(c * factor))) for c in rgb]
            return '#{:02x}{:02x}{:02x}'.format(*new_rgb)
        except: return hex_color

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(p, **kwargs, smooth=True)

class BoutonPro(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=45, color="#f5deb3", hover_color="#e2bc74"):
        super().__init__(parent, width=width, height=height+4, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command, self.color, self.hover_color = command, color, hover_color
        self.draw_round_rect(2, 6, width-2, height+2, 12, fill="#042f48", tags="shadow")
        self.rect = self.draw_round_rect(2, 2, width-2, height-2, 12, fill=color, tags="face")
        self.txt = self.create_text(width/2, height/2, text=text, fill=get_txt_color(color), font=FONT_UI, tags="face")
        
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.color))

    def _on_press(self, e):
        self.move("face", 0, 2)
        
    def _on_release(self, e):
        self.move("face", 0, -2)
        self.command()

    def set_text(self, new_text): self.itemconfig(self.txt, text=new_text)
    def set_color(self, c, hc): self.color, self.hover_color = c, hc; self.itemconfig(self.rect, fill=c); self.itemconfig(self.txt, fill=get_txt_color(c))

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(p, **kwargs, smooth=True)

class TimeSelector(tk.Canvas):
    def __init__(self, parent, init_v, callback=None):
        super().__init__(parent, width=320, height=90, bg=BLEU, highlightthickness=0, cursor="hand2")
        self.v, self.callback, self.enabled = init_v, callback, True
        
        self.create_text(160, 15, text="TEMPS PAR ROUND", fill=get_txt_color(BLEU), font=("Helvetica", 9, "bold"))
        self.draw_round_rect(100, 35, 220, 75, 10, fill="#042f48")
        self.txt_time = self.create_text(160, 55, text="00:00", fill="white", font=("Courier", 18, "bold"))
        
        self.btn_m = self.create_oval(60, 40, 90, 70, fill=ROUGE, outline="white", width=2, tags="btn_m")
        self.create_text(75, 55, text="-", fill="white", font=("Arial", 16, "bold"), state="disabled")
        
        self.btn_p = self.create_oval(230, 40, 260, 70, fill="#22c55e", outline="white", width=2, tags="btn_p")
        self.create_text(245, 55, text="+", fill="white", font=("Arial", 16, "bold"), state="disabled")

        self.tag_bind("btn_m", "<Button-1>", lambda e: self._change(-30))
        self.tag_bind("btn_p", "<Button-1>", lambda e: self._change(30))
        self.update_display()

    def _change(self, delta):
        if not self.enabled: return
        self.v = max(30, min(600, self.v + delta))
        self.update_display()
        if self.callback: self.callback(self.v)
        
        tag = "btn_m" if delta < 0 else "btn_p"
        old_col = ROUGE if delta < 0 else "#22c55e"
        self.itemconfig(tag, fill="white")
        self.after(50, lambda: self.itemconfig(tag, fill=old_col))

    def update_display(self):
        m, s = divmod(self.v, 60); self.itemconfig(self.txt_time, text=f"{m:02d}:{s:02d}")
    def activer(self, s): self.enabled = s; self.itemconfig("btn_m", fill=ROUGE if s else GRIS_LIGHT); self.itemconfig("btn_p", fill="#22c55e" if s else GRIS_LIGHT)
    def set_val(self, v): self.v = v; self.update_display()

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(p, **kwargs, smooth=True)

class SingleSlider(tk.Canvas):
    def __init__(self, parent, min_v, max_v, init_v, width=300, label="", callback=None):
        super().__init__(parent, width=width, height=75, bg=BLEU, highlightthickness=0, cursor="hand2")
        self.min_v, self.max_v, self.v = min_v, max_v, init_v
        self.callback, self.enabled = callback, True
        self.margin, self.bw = 40, width - 80

        self.create_text(width/2, 12, text=label, fill=get_txt_color(BLEU), font=("Helvetica", 9, "bold"))
        self.create_line(self.margin, 40, width-self.margin, 40, fill="#042f48", width=6, capstyle="round")
        for i in range(max_v - min_v + 1):
            x = self.margin + (i / (max_v - min_v)) * self.bw
            self.create_oval(x-1, 39, x+1, 41, fill="white")

        self.h = self.create_oval(0, 0, 24, 24, fill=BLEU_C, outline="white", width=2)
        self.txt_val = self.create_text(width/2, 65, fill=get_txt_color(BLEU), font=("Arial", 11, "bold"))
        
        self.update_pos()
        self.bind("<B1-Motion>", self._move)
        self.bind("<Button-1>", self._move)

    def _move(self, e):
        if not self.enabled: return
        raw_v = (e.x - self.margin) / self.bw
        new_v = max(self.min_v, min(self.max_v, round(self.min_v + raw_v * (self.max_v - self.min_v))))
        if new_v != self.v:
            self.v = new_v
            self.update_pos()
            if self.callback: self.callback(self.v)

    def update_pos(self):
        x = self.margin + ((self.v - self.min_v) / (self.max_v - self.min_v)) * self.bw
        self.coords(self.h, x-12, 28, x+12, 52)
        self.itemconfig(self.txt_val, text=str(self.v))

    def activer(self, s): self.enabled = s; self.itemconfig(self.h, fill=BLEU_C if s else GRIS_LIGHT)
    def set_val(self, v): self.v = v; self.update_pos()
    def get_value(self): return int(self.v)

class RangeSlider(tk.Canvas):
    def __init__(self, parent, min_v, max_v, v1, v2, width=300, callback=None):
        super().__init__(parent, width=width, height=80, bg=BLEU, highlightthickness=0, cursor="hand2")
        self.min_v, self.max_v, self.v1, self.v2 = min_v, max_v, v1, v2
        self.callback, self.enabled = callback, True
        self.margin, self.bw = 40, width - 80
        self.active_handle = None

        self.create_text(width/2, 12, text="TAILLE DU MOT", fill=get_txt_color(BLEU), font=("Helvetica", 9, "bold"))
        self.create_line(self.margin, 42, width-self.margin, 42, fill="#042f48", width=6, capstyle="round")
        for i in range(max_v - min_v + 1):
            x = self.margin + (i / (max_v - min_v)) * self.bw
            self.create_oval(x-1, 41, x+1, 43, fill="white")

        self.h1 = self.create_oval(0, 0, 24, 24, fill=JAUNE, outline="white", width=2)
        self.h2 = self.create_oval(0, 0, 24, 24, fill=ROUGE, outline="white", width=2)
        self.txt = self.create_text(width/2, 68, fill=get_txt_color(BLEU), font=("Arial", 11, "bold"))
        
        self.update_pos()
        self.bind("<Button-1>", self._start_move)
        self.bind("<B1-Motion>", self._move)

    def _start_move(self, e):
        if not self.enabled: return
        raw_v = (e.x - self.margin) / self.bw
        nv = max(self.min_v, min(self.max_v, round(self.min_v + raw_v * (self.max_v - self.min_v))))
        
        if self.v1 == self.v2:
            if nv > self.v1: self.active_handle = "h2"
            else: self.active_handle = "h1"
        else:
            if abs(nv - self.v1) < abs(nv - self.v2): self.active_handle = "h1"
            else: self.active_handle = "h2"
        self._move(e)

    def _move(self, e):
        if not self.enabled or not self.active_handle: return
        raw_v = (e.x - self.margin) / self.bw
        nv = max(self.min_v, min(self.max_v, round(self.min_v + raw_v * (self.max_v - self.min_v))))
        
        changed = False
        if self.active_handle == "h1":
            nv = min(nv, self.v2)
            if nv != self.v1: self.v1 = nv; changed = True
        else:
            nv = max(nv, self.v1)
            if nv != self.v2: self.v2 = nv; changed = True

        if changed:
            self.update_pos()
            if self.callback: self.callback(self.v1, self.v2)

    def update_pos(self):
        x1 = self.margin + ((self.v1 - self.min_v) / (self.max_v - self.min_v)) * self.bw
        x2 = self.margin + ((self.v2 - self.min_v) / (self.max_v - self.min_v)) * self.bw
        self.coords(self.h1, x1-12, 30, x1+12, 54)
        self.coords(self.h2, x2-12, 30, x2+12, 54)
        self.itemconfig(self.txt, text=f"{int(self.v1)} à {int(self.v2)} lettres")

    def activer(self, s): self.enabled = s; self.itemconfig(self.h1, fill=JAUNE if s else GRIS_LIGHT); self.itemconfig(self.h2, fill=ROUGE if s else GRIS_LIGHT)
    def set_vals(self, v1, v2): self.v1, self.v2 = v1, v2; self.update_pos()
    def get_values(self): return int(self.v1), int(self.v2)

# --- PAGES DU JEU ---

class PageMulti(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        self.player_id = str(random.randint(100000, 999999))
        self.pseudo = self.charger_pseudo_local()
        self.lobby_code, self.is_host = "", False
        self.settings_config = {"essais": 6, "min": 6, "max": 10, "round_num": 1, "timer": 180, "password": "", "visible": True}
        self.charger_mots()
        self.container = tk.Frame(self, bg=BLEU); self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (PageAccueil, PageHostSetup, PageCode, PageLobby, PageJeu, PageScoreFinal):
            f = F(parent=self.container, controller=self); self.frames[F.__name__] = f; f.grid(row=0, column=0, sticky="nsew")
        self.show_frame("PageAccueil")
        self.controller.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.quitter_lobby_logic(exit_mode=True)
        self.controller.winfo_toplevel().destroy()

    def quitter_lobby_logic(self, exit_mode=False):
        if not self.lobby_code: return
        try:
            url = f"{FIREBASE_URL}lobbies/{self.lobby_code}.json"
            resp = requests.get(url, timeout=2); data = resp.json() if resp.status_code == 200 else None
            if data:
                players = data.get("players", {})
                if self.player_id in players: del players[self.player_id]
                if not players: requests.delete(url, timeout=2)
                else:
                    requests.delete(f"{FIREBASE_URL}lobbies/{self.lobby_code}/players/{self.player_id}.json", timeout=2)
                    if self.is_host:
                        new_host_id = list(players.keys())[0]
                        requests.patch(f"{FIREBASE_URL}lobbies/{self.lobby_code}/settings.json", json={"host_id": new_host_id}, timeout=2)
        except: pass

    def charger_pseudo_local(self):
        d = os.path.join(os.getenv('APPDATA'), "SMOUT"); p = os.path.join(d, "config.json")
        if os.path.exists(p):
            try:
                with open(p, 'r') as f: return json.load(f).get("pseudo", "ANONYME")
            except: pass
        return "ANONYME"

    def sauvegarder_pseudo_local(self, p):
        if not p: return
        self.pseudo = p.upper(); d = os.path.join(os.getenv('APPDATA'), "SMOUT"); os.makedirs(d, exist_ok=True)
        try:
            data = {}
            if os.path.exists(os.path.join(d, "config.json")):
                with open(os.path.join(d, "config.json"), 'r') as f: data = json.load(f)
            data["pseudo"] = self.pseudo
            with open(os.path.join(d, "config.json"), 'w') as f: json.dump(data, f)
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
        if name == "PageCode": f.charger_liste()
        if name == "PageLobby": f.entrer_lobby()
        if name == "PageJeu": f.initialiser_partie()
        if name == "PageScoreFinal": f.afficher_vainqueur()

    def fb_get(self, path):
        try: return requests.get(f"{FIREBASE_URL}{path}.json", timeout=1.5).json()
        except: return None
    
    def fb_patch(self, path, data):
        threading.Thread(target=lambda: self._exec_request("patch", path, data), daemon=True).start()

    def fb_put(self, path, data):
        threading.Thread(target=lambda: self._exec_request("put", path, data), daemon=True).start()

    def fb_delete(self, path):
        threading.Thread(target=lambda: self._exec_request("delete", path), daemon=True).start()

    def _exec_request(self, method, path, data=None):
        try:
            url = f"{FIREBASE_URL}lobbies/{path}.json" if not path.startswith("lobbies") else f"{FIREBASE_URL}{path}.json"
            if method == "patch": requests.patch(url, json=data, timeout=2)
            elif method == "put": requests.put(url, json=data, timeout=2)
            elif method == "delete": requests.delete(url, timeout=2)
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
        val = self.sv_pseudo.get(); formate = "".join([c.upper() for c in val if c.isalnum()])
        if val != formate: self.sv_pseudo.set(formate)
        self.controller.sauvegarder_pseudo_local(formate)
    def creer(self):
        if self.sv_pseudo.get().strip(): self.controller.show_frame("PageHostSetup")
    def rejoindre(self):
        if self.sv_pseudo.get().strip(): self.controller.show_frame("PageCode")

class PageHostSetup(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        c = tk.Frame(self, bg=BLEU); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="CONFIGURATION DU SALON", font=FONT_UI, fg="white", bg=BLEU).pack(pady=20)
        tk.Label(c, text="MOT DE PASSE (Optionnel)", font=("Helvetica", 10), fg=GRIS_LIGHT, bg=BLEU).pack()
        self.e_pass = tk.Entry(c, font=FONT_UI, justify="center", bg="#052132", fg="white", width=20); self.e_pass.pack(pady=10)
        self.is_pub = True; btn_f = tk.Frame(c, bg=BLEU); btn_f.pack(pady=10)
        self.b_pub = BoutonPro(btn_f, "PUBLIC", lambda: self.set_vis(True), width=120, color=BLEU_C)
        self.b_pri = BoutonPro(btn_f, "PRIVÉ", lambda: self.set_vis(False), width=120, color="#475569")
        self.b_pub.pack(side="left", padx=5); self.b_pri.pack(side="left", padx=5)
        BoutonPro(c, "CRÉER", self.valider, color="#22c55e").pack(pady=20)
        BoutonPro(c, "RETOUR", lambda: controller.show_frame("PageAccueil"), color="#94a3b8").pack()
    def set_vis(self, v):
        self.is_pub = v; self.b_pub.set_color(BLEU_C if v else "#475569", BLEU_C if v else "#64748b")
        self.b_pri.set_color("#475569" if v else JAUNE, "#64748b" if v else "#fbbf24")
    def valider(self):
        self.controller.settings_config.update({"password": self.e_pass.get().strip(), "visible": self.is_pub})
        self.controller.is_host = True; self.controller.lobby_code = ""; self.controller.show_frame("PageLobby")

class PageCode(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller
        self.c = tk.Frame(self, bg=BLEU); self.c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(self.c, text="CODE DU LOBBY", font=("Helvetica", 25, "bold"), fg="white", bg=BLEU).pack(pady=20)
        self.e = tk.Entry(self.c, font=("Courier", 45, "bold"), justify="center", width=5, bg="#052132", fg=JAUNE)
        self.e.pack(pady=10); self.e.bind("<Return>", lambda e: self.valider())
        BoutonPro(self.c, "REJOINDRE", self.valider, color="#22c55e").pack(pady=20)
        tk.Frame(self.c, height=2, bg=BLEU_C, width=350).pack(pady=15)
        tk.Label(self.c, text="SALONS PUBLICS", font=FONT_UI, fg="white", bg=BLEU).pack(pady=5)
        self.cl = tk.Frame(self.c, bg=BLEU); self.cl.pack()
        self.canvas = tk.Canvas(self.cl, width=420, height=220, bg="#052132", highlightthickness=0)
        self.scroll = tk.Scrollbar(self.cl, orient="vertical", command=self.canvas.yview)
        self.lf = tk.Frame(self.canvas, bg="#052132"); self.canvas.create_window((0,0), window=self.lf, anchor="nw", width=420)
        self.canvas.configure(yscrollcommand=self.scroll.set); self.canvas.pack(side="left"); self.scroll.pack(side="right", fill="y")
        self.lf.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.pass_view = tk.Frame(self, bg=BLEU, highlightthickness=2, highlightbackground=JAUNE)
        tk.Label(self.pass_view, text="MOT DE PASSE REQUIS", fg="white", bg=BLEU, font=FONT_UI).pack(pady=10)
        self.e_pw = tk.Entry(self.pass_view, show="*", font=FONT_UI, justify="center"); self.e_pw.pack(pady=5, padx=20)
        pb = tk.Frame(self.pass_view, bg=BLEU); pb.pack(pady=10)
        BoutonPro(pb, "VALIDER", self.check_pw, width=100, height=30, color="#22c55e").pack(side="left", padx=5)
        BoutonPro(pb, "ANNULER", lambda: self.pass_view.place_forget(), width=100, height=30, color=ROUGE).pack(side="left", padx=5)
        BoutonPro(self.c, "RAFRAÎCHIR", self.charger_liste, color=BLEU_C, width=250).pack(pady=10)
        BoutonPro(self.c, "RETOUR", lambda: controller.show_frame("PageAccueil"), color="#94a3b8").pack()
    def flash_error(self, count=0):
        if count < 6: self.pass_view.config(bg=ROUGE if count%2==0 else BLEU); self.after(100, lambda: self.flash_error(count+1))
    def charger_liste(self):
        for w in self.lf.winfo_children(): w.destroy()
        data = self.controller.fb_get("lobbies") or {}
        for code, val in data.items():
            s = val.get("settings", {}); players = val.get("players", {})
            if s.get("visible") and val.get("status") == "waiting":
                host_id = s.get("host_id"); host_name = players.get(host_id, {}).get("name", "ANONYME")
                f = tk.Frame(self.lf, bg=BLEU, pady=8, padx=10, highlightthickness=1, highlightbackground=BLEU_C); f.pack(fill="x", pady=2)
                tk.Label(f, text=f"#{code} | Hôte: {host_name} | {len(players)}/4" + (" 🔒" if s.get("password") else ""), fg="white", bg=BLEU, font=("Helvetica", 9, "bold")).pack(side="left")
                BoutonPro(f, "REJOINDRE", lambda c=code: self.tenter_join(c), width=130, height=30, color="#22c55e").pack(side="right")
    def tenter_join(self, code):
        data = self.controller.fb_get(f"lobbies/{code}")
        if not data: return
        self.t_c, self.t_p = code, data.get("settings", {}).get("password")
        if self.t_p: self.pass_view.place(relx=0.5, rely=0.5, anchor="center"); self.e_pw.delete(0, tk.END); self.e_pw.focus_set()
        else: self.rejoindre(code)
    def check_pw(self):
        if self.e_pw.get() == self.t_p: self.pass_view.place_forget(); self.rejoindre(self.t_c)
        else: self.flash_error()
    def valider(self):
        code = self.e.get().strip()
        if code:
            if self.controller.fb_get(f"lobbies/{code}"): self.tenter_join(code)
            else: tkm.showwarning("SMOUT", "Lobby plein ou introuvable")
    def rejoindre(self, code):
        self.controller.is_host = False; data = self.controller.fb_get(f"lobbies/{code}")
        if data and len(data.get("players", {})) < 4:
            self.controller.lobby_code = code
            self.controller.fb_patch(f"lobbies/{code}/players/{self.controller.player_id}", {"name": self.controller.pseudo, "score": 0})
            self.controller.show_frame("PageLobby")

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
        self.s_essais = SingleSlider(self.f_p, 4, 10, 6, label="ESSAIS", callback=lambda v: self.sync_params())
        self.s_len = RangeSlider(self.f_p, 6, 10, 6, 10, callback=lambda v1, v2: self.sync_params())
        self.s_time = TimeSelector(self.f_p, 180, callback=lambda v: self.sync_params())
        [s.pack() for s in [self.s_rounds, self.s_essais, self.s_len, self.s_time]]
        self.lbl_status = tk.Label(c, text="EN ATTENTE D'UN AMI...", font=FONT_UI, fg=ROUGE, bg=BLEU); self.lbl_status.pack(pady=10)
        self.btn_lancer = BoutonPro(c, "LANCER LE MATCH", self.lancer, color="#22c55e", width=250)
        BoutonPro(c, "QUITTER LE LOBBY", self.quitter, color="#94a3b8", width=250).pack(pady=5)
    
    def sync_params(self):
        if self.controller.is_host and self.active_sync:
            mi, ma = self.s_len.get_values(); sc = self.controller.settings_config
            d = {"rounds": self.s_rounds.get_value(), "essais": self.s_essais.get_value(), 
                 "min": mi, "max": ma, "timer": self.s_time.v, 
                 "host_id": self.controller.player_id, "password": sc["password"], "visible": sc["visible"]}
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", d)
    
    def entrer_lobby(self):
        self.active_sync = True; self.btn_lancer.pack_forget()
        if self.controller.is_host:
            if not self.controller.lobby_code: 
                self.controller.lobby_code = str(random.randint(1000, 9999))
                sc = self.controller.settings_config
                init = {"status": "waiting", "settings": {"rounds":3, "essais":6, "min":6, "max":10, "timer": 180, "host_id": self.controller.player_id, "password": sc["password"], "visible": sc["visible"]}, "players": {self.controller.player_id: {"name": self.controller.pseudo, "score": 0}}}
                self.controller.fb_put(f"lobbies/{self.controller.lobby_code}", init)
            self.lbl_code.config(text=self.controller.lobby_code)
        else: self.lbl_code.config(text=self.controller.lobby_code)
        self.ecouter_lobby()
    
    def ecouter_lobby(self):
        if not self.active_sync: return
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data:
            s, players = data.get("settings", {}), data.get("players", {})
            host_id = s.get("host_id")
            self.controller.is_host = (host_id == self.controller.player_id)
            
            if not self.controller.is_host:
                self.s_rounds.set_val(s.get("rounds", 3))
                self.s_essais.set_val(s.get("essais", 6))
                self.s_len.set_vals(s.get("min", 6), s.get("max", 10))
                self.s_time.set_val(s.get("timer", 180))
            
            if data.get("status") == "playing":
                self.active_sync = False
                self.controller.settings_config.update({
                    "target_word": s.get("target_word"), 
                    "essais": s.get("essais"), 
                    "round_num": s.get("current_round", 1), 
                    "rounds": s.get("rounds"), 
                    "timer": s.get("timer"),
                    "start_time": s.get("start_time")
                })
                self.controller.show_frame("PageJeu"); return
            
            p_ids = list(players.keys())
            for i, slot in enumerate(self.player_slots):
                if i < len(p_ids):
                    p_id = p_ids[i]
                    p_name = players[p_id]["name"]
                    if p_id == host_id: p_name += " 👑"
                    slot.config(text=p_name, fg="white")
                else: slot.config(text="VIDE", fg=GRIS_LIGHT)
            
            if len(players) > 1:
                self.lbl_status.config(text=f"🟢 {len(players)} JOUEURS PRÊTS", fg="#22c55e")
                if self.controller.is_host: self.btn_lancer.pack(pady=5)
            else:
                self.lbl_status.config(text="🔴 EN ATTENTE D'UN AMI...", fg=ROUGE); self.btn_lancer.pack_forget()
            [s_ui.activer(self.controller.is_host) for s_ui in [self.s_rounds, self.s_essais, self.s_len, self.s_time]]
        self.after(800, self.ecouter_lobby)

    def quitter(self): self.active_sync = False; self.controller.quitter_lobby_logic(); self.controller.show_frame("PageAccueil")

    def lancer(self):
        mi, ma = self.s_len.get_values()
        f = [m for m in self.controller.liste_mots if mi <= len(m) <= ma]
        mot = random.choice(f if f else self.controller.liste_mots)
        sc = self.controller.settings_config
        
        s = {"target_word": mot, "rounds": self.s_rounds.get_value(), "current_round": 1, 
             "essais": self.s_essais.get_value(), "min": mi, "max": ma, 
             "timer": self.s_time.v, "host_id": self.controller.player_id, 
             "password": sc["password"], "visible": sc["visible"],
             "start_time": time.time()}
        
        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {
            "status": "playing", 
            "settings": s,
            "match_data": None,
            "fini_states": None
        })

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
        conf = self.controller.settings_config
        self.mot = conf.get("target_word", "SMOUT")
        self.round_actuel = conf.get("round_num", 1)
        self.start_time_round = conf.get("start_time", time.time())
        self.ligne, self.tape, self.fini_local, self.temps_restant = 0, [self.mot[0]], False, conf.get("timer", 180)
        self.statut_lettres = {l: "#052132" for l in ALPHABET}; self.boutons_clavier = {}
        
        mon_nom = self.controller.pseudo
        data_match = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        host_id = data_match.get("settings", {}).get("host_id") if data_match else None
        if self.controller.player_id == host_id: mon_nom += " 👑"
        
        self.labels_moi = self.creer_grille(self.moi_side, mon_nom, True)
        
        self.msg_container = tk.Frame(self.moi_side, bg=BLEU, height=40); self.msg_container.pack()
        self.lbl_msg = tk.Label(self.msg_container, text="", font=("Helvetica", 11, "bold"), bg=BLEU, fg="white")
        self.lbl_msg.pack(side="left")
        self.btn_def = tk.Label(self.msg_container, text="?", font=("Helvetica", 10, "bold", "underline"), bg=BLEU, fg=BLEU_C, cursor="hand2")
        self.btn_def.bind("<Button-1>", lambda e: webbrowser.open(f"https://www.google.com/search?q=D%C3%A9finition+du+mot+{self.mot}"))
        
        self.creer_clavier(self.moi_side)
        self.btns_frame = tk.Frame(self.moi_side, bg=BLEU); self.btns_frame.pack(pady=10)
        # On sauvegarde les références des boutons pour pouvoir les masquer plus tard
        self.btn_valider = BoutonPro(self.btns_frame, "VALIDER", self.valider, width=100, color="#22c55e")
        self.btn_valider.pack(side="left", padx=5)
        self.btn_effacer = BoutonPro(self.btns_frame, "EFFACER", self.effacer, width=100, color="#94a3b8")
        self.btn_effacer.pack(side="left", padx=5)
        
        self.adv_labels, self.adv_grids = {}, {}
        if data_match:
            players = data_match.get("players", {})
            for pid, p in players.items():
                if pid != self.controller.player_id:
                    adv_nom = p["name"]
                    if pid == host_id: adv_nom += " 👑"
                    f = tk.Frame(self.adv_container, bg=BLEU, pady=5); f.pack()
                    lbl = tk.Label(f, text=adv_nom, font=("Helvetica", 11, "bold"), fg="white", bg=BLEU); lbl.pack(); self.adv_labels[pid] = lbl
                    self.adv_grids[pid] = self.creer_grille_sans_label(f)
                    
        self.btn_next = BoutonPro(self.main_c, "ROUND SUIVANT", self.clic_suivant, color=JAUNE, width=250)
        self.active_sync, self.timer_actif = True, True; self.update_timer(); self.ecouter_match(); self.controller.focus_set(); self.controller.bind("<Key>", self.clavier_physique); self.maj_affichage()
    
    def update_timer(self):
        if not self.timer_actif: return
        conf = self.controller.settings_config
        duree_totale = int(conf.get("timer", 180))
        maintenant = time.time()
        ecoule = maintenant - self.start_time_round
        self.temps_restant = max(0, int(duree_totale - ecoule))
        m, s = divmod(self.temps_restant, 60)
        self.lbl_timer.config(text=f"{m:02d}:{s:02d}", fg="white" if self.temps_restant > 30 else ROUGE)
        if self.temps_restant <= 0:
            if not self.fini_local: self.finir_round(False)
        else:
            self.after(500, self.update_timer)
    
    def ecouter_match(self):
        if not self.active_sync: return
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data:
            if data.get("status") == "finished": 
                self.active_sync = False
                self.controller.show_frame("PageScoreFinal"); return
            s, players = data.get("settings", {}), data.get("players", {})
            self.controller.is_host = (s.get("host_id") == self.controller.player_id)
            if int(s.get("current_round", 1)) > int(self.round_actuel): 
                self.active_sync = False
                self.controller.settings_config.update({
                    "target_word": s.get("target_word"), 
                    "round_num": int(s["current_round"]),
                    "start_time": s.get("start_time")
                })
                self.initialiser_partie(); return
            self.lbl_scores.config(text=" | ".join([f"{p['name']}: {p['score']}" for p in players.values()]))
            self.lbl_info.config(text=f"ROUND {s.get('current_round')} / {s.get('rounds')}")
            fini_raw = data.get("fini_states") or {}
            fini_ids = [k for k,v in fini_raw.items() if v] if isinstance(fini_raw, dict) else []
            if len(fini_ids) >= len(players): self.timer_actif = False
            m_data = data.get("match_data", {})
            for pid, grid in self.adv_grids.items():
                if pid in players:
                    p_prog = m_data.get(pid, {})
                    it = enumerate(p_prog) if isinstance(p_prog, list) else p_prog.items() if isinstance(p_prog, dict) else []
                    for l_str, content in it:
                        if content:
                            l_idx = int(l_str)
                            if l_idx < len(grid):
                                for c_idx, coul in enumerate(content.get("c", [])): grid[l_idx][c_idx].config(bg=coul, fg=get_txt_color(coul), highlightbackground=GRILLE)
                                if self.fini_local: [grid[l_idx][c_idx].config(text=char) for c_idx, char in enumerate(content.get("l", []))]
                else:
                    self.adv_labels[pid].config(text=f"{self.adv_labels[pid].cget('text').split(' ')[0]} (PARTI)", fg=GRIS_LIGHT)
            if self.fini_local:
                if len(fini_ids) >= len(players):
                    self.lbl_msg.config(text=f"LE MOT ÉTAIT : {self.mot} ", fg=JAUNE)
                    self.btn_def.pack(side="left")
                    if self.controller.is_host:
                        txt = "VOIR LES RÉSULTATS" if int(s['current_round']) >= int(s['rounds']) else "ROUND SUIVANT"; self.btn_next.set_text(txt); self.btn_next.pack(pady=15)
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
        for i, c in enumerate(res): self.labels_moi[self.ligne][i].config(bg=c, fg=get_txt_color(c))
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}/{self.ligne}", {"c": res, "l": self.tape})
        if t == self.mot: self.finir_round(True)
        elif self.ligne >= self.controller.settings_config["essais"]-1: self.finir_round(False)
        else: self.ligne += 1; self.tape = [self.mot[0]]; self.maj_affichage()
    
    def effacer(self):
        if not self.fini_local and len(self.tape) > 1: self.tape.pop(); self.maj_affichage()
    
    def finir_round(self, vic):
        self.fini_local = True
        # On fait disparaître les boutons d'action
        self.btn_valider.pack_forget()
        self.btn_effacer.pack_forget()
        if vic:
            p = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}")
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": (p.get("score") or 0) + 1})
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/fini_states/{self.controller.player_id}", True)
    
    def clic_suivant(self):
        self.btn_next.pack_forget()
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if not data: return
        s = data["settings"]
        if int(s["current_round"]) < int(s["rounds"]):
            f = [m for m in self.controller.liste_mots if int(s["min"]) <= len(m) <= int(s["max"])]
            n_mot = random.choice(f if f else self.controller.liste_mots)
            s.update({
                "target_word": n_mot, 
                "current_round": int(s["current_round"])+1,
                "start_time": time.time()
            })
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {
                "settings": s, 
                "status": "playing",
                "match_data": None,
                "fini_states": None
            })
        else:
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"status": "finished"})
    
    def clavier_physique(self, e):
        if self.fini_local: return
        k, c = e.keysym, e.char.upper()
        if c in ALPHABET and len(c) == 1:
            if len(self.tape) < len(self.mot): self.tape.append(c); self.maj_affichage()
        elif k == "BackSpace": self.effacer()
        elif k == "Return": self.valider()
    
    def maj_affichage(self):
        if self.fini_local: return
        for i, c in enumerate(self.tape): 
            coul = ROUGE if i == 0 else BLEU
            self.labels_moi[self.ligne][i].config(text=c, bg=coul, fg=get_txt_color(coul))
        for i in range(len(self.tape), len(self.mot)): self.labels_moi[self.ligne][i].config(text="", bg=BLEU)
    
    def creer_grille(self, parent, name, main):
        tk.Label(parent, text=name, font=("Helvetica", 11, "bold"), fg="white", bg=BLEU).pack()
        return self.creer_grille_sans_label(parent, main)
    
    def creer_grille_sans_label(self, parent, main=False):
        g = tk.Frame(parent, bg=BLEU); g.pack(); rows = []
        size = 28 if main else 10
        for l in range(self.controller.settings_config["essais"]):
            ligne = [tk.Label(g, text="", font=("Courier", size, "bold"), width=2, height=1, fg="white", bg="#052132", borderwidth=1, relief="solid", highlightbackground=GRILLE, highlightthickness=1) for _ in range(len(self.mot))]
            [lbl.grid(row=l, column=c, padx=1, pady=1) for c, lbl in enumerate(ligne)]; rows.append(ligne)
        return rows
    
    def creer_clavier(self, parent):
        f = tk.Frame(parent, bg=BLEU); f.pack(pady=5)
        for r in ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ"]:
            row = tk.Frame(f, bg=BLEU); row.pack()
            for c in r: 
                btn = tk.Button(row, text=c, width=2, font=("Arial", 8, "bold"), bg="#052132", fg="white", relief="raised", bd=2, command=lambda x=c: (self.tape.append(x), self.maj_affichage()) if len(self.tape) < len(self.mot) and not self.fini_local else None)
                btn.pack(side="left", padx=1, pady=1); self.boutons_clavier[c] = btn
    def maj_clavier(self):
        for char, color in self.statut_lettres.items():
            if char in self.boutons_clavier:
                if color == GRIS_LIGHT:
                    self.boutons_clavier[char].config(bg=color, fg="#6b7280", relief="flat", font=("Arial", 8, "bold overstrike"))
                else:
                    self.boutons_clavier[char].config(bg=color, fg=get_txt_color(color), relief="raised", font=("Arial", 8, "bold"))

class PageScoreFinal(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BLEU); self.controller = controller; self.active_sync = False
        self.c = tk.Frame(self, bg=BLEU); self.c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(self.c, text="MATCH FINI", font=("Helvetica", 40, "bold"), fg=JAUNE, bg=BLEU).pack(pady=30)
        self.lbl_res = tk.Label(self.c, text="", font=("Helvetica", 22, "bold"), fg="white", bg=BLEU, justify="center"); self.lbl_res.pack(pady=30)
        self.btn_f = tk.Frame(self.c, bg=BLEU); self.btn_f.pack()
        self.btn_lobby = BoutonPro(self.btn_f, "RETOUR AU SALON", self.retour_lobby_host, color="#22c55e", width=300)
        BoutonPro(self.c, "RETOUR AU MENU", lambda: self.controller.controller.creer_menu_accueil(), color="#94a3b8", width=300).pack(pady=10)
        self.lbl_wait = tk.Label(self.c, text="ATTENTE DE L'HÔTE...", font=FONT_UI, fg=GRIS_LIGHT, bg=BLEU)

    def afficher_vainqueur(self):
        self.active_sync = True; self.btn_lobby.pack_forget(); self.lbl_wait.pack_forget()
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data:
            players = data.get("players", {})
            if not players: return
            items = sorted(players.values(), key=lambda x: x.get("score", 0), reverse=True)
            winners = [p["name"] for p in items if p.get("score", 0) == items[0].get("score", 0)]
            titre = f"VAINQUEUR : {winners[0]}" if len(winners) == 1 else f"ÉGALITÉ : {', '.join(winners)}"
            score_txt = "\n".join([f"{p['name']} : {p.get('score') or 0} pts" for p in items])
            self.lbl_res.config(text=f"{titre}\n\n{score_txt}")
            if self.controller.is_host: self.btn_lobby.pack(pady=10)
            else: self.lbl_wait.pack(pady=10)
            self.ecouter_fin()

    def ecouter_fin(self):
        if not self.active_sync: return
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data and data.get("status") == "waiting":
            self.active_sync = False; self.controller.show_frame("PageLobby"); return
        self.after(1000, self.ecouter_fin)

    def retour_lobby_host(self):
        data = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if data:
            players = data.get("players", {})
            for pid in players: players[pid]["score"] = 0
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {
                "status": "waiting", 
                "players": players,
                "match_data": None,
                "fini_states": None
            })
