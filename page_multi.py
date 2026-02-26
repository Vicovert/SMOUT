import tkinter as tk
from tkinter import messagebox as tkm
import json, random, os, sys, time, requests, threading, webbrowser
from pathlib import Path

# --- CONFIGURATION DYNAMIQUE ---
FIREBASE_URL = "https://smout-multi-default-rtdb.europe-west1.firebasedatabase.app/"
BG, ACCENT1, ACCENT2, MUTED = '#0a4160', '#ef4444', '#eab308', '#64748b'
BTN1, BTN2, BTN3 = '#0ea5e9', '#ef4444', '#eab308'
TXT1, TXT2, TXT3 = 'white', 'black', 'white'
GRILLE = "#1a1a1a"
FONT_MONO, FONT_UI = ("Courier", 24, "bold"), ("Helvetica", 12, "bold")
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def apply_theme_multi(theme_data):
    """Met à jour les couleurs globales du jeu"""
    global BG, ACCENT1, ACCENT2, MUTED, BTN1, BTN2, BTN3, TXT1, TXT2, TXT3, GRILLE
    BG, ACCENT1, ACCENT2, MUTED = theme_data["bg"], theme_data["accent1"], theme_data["accent2"], theme_data["muted"]
    BTN1, BTN2, BTN3 = theme_data["btn1"], theme_data["btn2"], theme_data["btn3"]
    TXT1, TXT2, TXT3 = theme_data["txt1"], theme_data["txt2"], theme_data["txt3"]
    GRILLE = TXT3

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_txt_color(hex_color):
    """Calcule si le texte doit être blanc ou noir selon la luminosité du fond"""
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return "#1a1a1a" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.5 else "white"
    except: return "white"

def adjust_color(hex_color, factor):
    """Utilitaire de couleur partagé"""
    try:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return '#{:02x}{:02x}{:02x}'.format(*[min(255, max(0, int(c * factor))) for c in rgb])
    except: return hex_color

def draw_round_rect_static(canvas, x1, y1, x2, y2, r, **kwargs):
    p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
    return canvas.create_polygon(p, **kwargs, smooth=True)

# --- COMPOSANTS UI ---

class LogoSmout(tk.Canvas):
    def __init__(self, parent, tile_size=90):
        word, gap = "SMOUT", 12
        total_w = (tile_size + gap) * len(word)
        super().__init__(parent, width=total_w, height=tile_size + 40, bg=parent["bg"], highlightthickness=0)
        for i, char in enumerate(word):
            x = i * (tile_size + gap)
            p, s, bg = 8, tile_size - 8, (ACCENT1 if char == "U" else ACCENT2)
            draw_round_rect_static(self, x+p+4, p+8, x+s+4, s+8, 15, fill="#042f48")
            draw_round_rect_static(self, x+p, p+4, x+s+4, s+4, 15, fill=adjust_color(bg, 0.7))
            draw_round_rect_static(self, x+p, p, x+s, s, 15, fill=bg)
            draw_round_rect_static(self, x+p+4, p+4, x+s-4, p+(s/2.5), 12, fill=adjust_color(bg, 1.3))
            self.create_text(x+tile_size/2, tile_size/2, text=char, fill=get_txt_color(bg), font=("Verdana", int(tile_size*0.5), "bold"))

class BoutonPro(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=45, color="#f5deb3", hover_color=None):
        super().__init__(parent, width=width, height=height+4, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command, self.color = command, color
        self.hover_color = hover_color or adjust_color(color, 1.2)
        draw_round_rect_static(self, 2, 6, width-2, height+2, 12, fill="#042f48", tags="shadow")
        self.rect = draw_round_rect_static(self, 2, 2, width-2, height-2, 12, fill=color, tags="face")
        self.txt = self.create_text(width/2, height/2, text=text, fill=get_txt_color(color), font=FONT_UI, tags="face")
        self.bind("<Button-1>", lambda e: self.move("face", 0, 2))
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.color))

    def _on_release(self, e):
        self.move("face", 0, -2); self.command()
    def set_text(self, new_text): self.itemconfig(self.txt, text=new_text)
    def set_color(self, c, hc): 
        self.color, self.hover_color = c, (hc or adjust_color(c, 1.2))
        self.itemconfig(self.rect, fill=c); self.itemconfig(self.txt, fill=get_txt_color(c))

class TimeSelector(tk.Canvas):
    def __init__(self, parent, init_v, callback=None):
        super().__init__(parent, width=320, height=90, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.v, self.callback, self.enabled = init_v, callback, True
        self.create_text(160, 15, text="TEMPS PAR ROUND", fill=TXT1, font=("Helvetica", 9, "bold"))
        draw_round_rect_static(self, 100, 35, 220, 75, 10, fill="#042f48")
        self.txt_time = self.create_text(160, 55, text="00:00", fill="white", font=("Courier", 18, "bold"))
        self.btn_m = self.create_oval(60, 40, 90, 70, fill=ACCENT1, outline="white", width=2, tags="btn_m")
        self.create_text(75, 55, text="-", fill=get_txt_color(ACCENT1), font=("Arial", 16, "bold"), state="disabled")
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
        tag, old_col = ("btn_m", ACCENT1) if delta < 0 else ("btn_p", "#22c55e")
        self.itemconfig(tag, fill="white"); self.after(50, lambda: self.itemconfig(tag, fill=old_col))

    def update_display(self):
        m, s = divmod(self.v, 60); self.itemconfig(self.txt_time, text=f"{m:02d}:{s:02d}")
    def activer(self, s): self.enabled = s; self.itemconfig("btn_m", fill=ACCENT1 if s else MUTED); self.itemconfig("btn_p", fill="#22c55e" if s else MUTED)
    def set_val(self, v): self.v = v; self.update_display()

class SingleSlider(tk.Canvas):
    def __init__(self, parent, min_v, max_v, init_v, width=300, label="", callback=None):
        super().__init__(parent, width=width, height=75, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.min_v, self.max_v, self.v, self.callback, self.enabled = min_v, max_v, init_v, callback, True
        self.margin, self.bw = 40, width - 80
        self.create_text(width/2, 12, text=label, fill=TXT1, font=("Helvetica", 9, "bold"))
        self.create_line(self.margin, 40, width-self.margin, 40, fill="#042f48", width=6, capstyle="round")
        for i in range(max_v - min_v + 1):
            x = self.margin + (i / (max_v - min_v)) * self.bw
            self.create_oval(x-1, 39, x+1, 41, fill=TXT1)
        self.h = self.create_oval(0, 0, 24, 24, fill=BTN1, outline="white", width=2)
        self.txt_val = self.create_text(width/2, 65, fill=TXT1, font=("Arial", 11, "bold"))
        self.update_pos()
        self.bind("<B1-Motion>", self._move); self.bind("<Button-1>", self._move)

    def _move(self, e):
        if not self.enabled: return
        nv = max(self.min_v, min(self.max_v, round(self.min_v + ((e.x - self.margin) / self.bw) * (self.max_v - self.min_v))))
        if nv != self.v: self.v = nv; self.update_pos(); (self.callback(self.v) if self.callback else None)

    def update_pos(self):
        x = self.margin + ((self.v - self.min_v) / (self.max_v - self.min_v)) * self.bw
        self.coords(self.h, x-12, 28, x+12, 52); self.itemconfig(self.txt_val, text=str(self.v))
    def activer(self, s): self.enabled = s; self.itemconfig(self.h, fill=BTN1 if s else MUTED)
    def set_val(self, v): self.v = v; self.update_pos()
    def get_value(self): return int(self.v)

class RangeSlider(tk.Canvas):
    def __init__(self, parent, min_v, max_v, v1, v2, width=300, callback=None):
        super().__init__(parent, width=width, height=80, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.min_v, self.max_v, self.v1, self.v2, self.callback, self.enabled = min_v, max_v, v1, v2, callback, True
        self.margin, self.bw, self.active_handle = 40, width - 80, None
        self.create_text(width/2, 12, text="TAILLE DU MOT", fill=TXT1, font=("Helvetica", 9, "bold"))
        self.create_line(self.margin, 42, width-self.margin, 42, fill="#042f48", width=6, capstyle="round")
        for i in range(max_v - min_v + 1):
            x = self.margin + (i / (max_v - min_v)) * self.bw
            self.create_oval(x-1, 41, x+1, 43, fill=TXT1)
        self.h1, self.h2 = self.create_oval(0,0,0,0, fill=ACCENT2, outline="white", width=2), self.create_oval(0,0,0,0, fill=ACCENT1, outline="white", width=2)
        self.txt = self.create_text(width/2, 68, fill=TXT1, font=("Arial", 11, "bold"))
        self.update_pos(); self.bind("<Button-1>", self._start_move); self.bind("<B1-Motion>", self._move)

    def _start_move(self, e):
        if not self.enabled: return
        nv = max(self.min_v, min(self.max_v, round(self.min_v + ((e.x-self.margin)/self.bw) * (self.max_v-self.min_v))))
        d1, d2 = abs(nv-self.v1), abs(nv-self.v2)
        if d1 < d2: self.active_handle = "h1"
        elif d2 < d1: self.active_handle = "h2"
        else: self.active_handle = "h2" if nv >= self.v2 else "h1"
        self._move(e)

    def _move(self, e):
        if not self.enabled or not self.active_handle: return
        nv = max(self.min_v, min(self.max_v, round(self.min_v + ((e.x-self.margin)/self.bw) * (self.max_v-self.min_v))))
        if self.active_handle == "h1":
            nv = min(nv, self.v2)
            if nv != self.v1: self.v1 = nv; self.update_pos(); (self.callback(self.v1, self.v2) if self.callback else None)
        else:
            nv = max(nv, self.v1)
            if nv != self.v2: self.v2 = nv; self.update_pos(); (self.callback(self.v1, self.v2) if self.callback else None)

    def update_pos(self):
        x1, x2 = [self.margin + ((v - self.min_v) / (self.max_v - self.min_v)) * self.bw for v in (self.v1, self.v2)]
        self.coords(self.h1, x1-12, 30, x1+12, 54); self.coords(self.h2, x2-12, 30, x2+12, 54)
        self.itemconfig(self.txt, text=f"{int(self.v1)} à {int(self.v2)} lettres")
    def activer(self, s): self.enabled = s; self.itemconfig(self.h1, fill=ACCENT2 if s else MUTED); self.itemconfig(self.h2, fill=ACCENT1 if s else MUTED)
    def set_vals(self, v1, v2): self.v1, self.v2 = v1, v2; self.update_pos()
    def get_values(self): return int(self.v1), int(self.v2)

# --- PAGES DU JEU ---

class PageMulti(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG); self.controller = controller
        self.session = requests.Session() 
        self.player_id = str(random.randint(100000, 999999))
        self.pseudo = self.charger_pseudo_local()
        self.lobby_code, self.is_host, self.current_score = "", False, 0
        self.settings_config = {"essais": 6, "min": 6, "max": 10, "round_num": 1, "timer": 180, "password": "", "visible": True}
        self.charger_mots()
        self.container = tk.Frame(self, bg=BG); self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1); self.container.grid_columnconfigure(0, weight=1)
        self.frames = {F.__name__: F(parent=self.container, controller=self) for F in (PageAccueil, PageHostSetup, PageCode, PageLobby, PageJeu, PageScoreFinal)}
        for f in self.frames.values(): f.grid(row=0, column=0, sticky="nsew")
        self.show_frame("PageAccueil"); self.controller.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.on_closing)
        self.heartbeat_active = True; self.start_heartbeat()

    def start_heartbeat(self):
        if self.heartbeat_active and self.lobby_code:
            self.fb_patch(f"lobbies/{self.lobby_code}/players/{self.player_id}", {"last_seen": time.time(), "name": self.pseudo, "score": self.current_score})
        if self.heartbeat_active: self.after(5000, self.start_heartbeat)

    def on_closing(self):
        self.heartbeat_active = False; self.quitter_lobby_logic(True); self.controller.winfo_toplevel().destroy()

    def quitter_lobby_logic(self, exit_mode=False):
        if not self.lobby_code: return
        code_to_clean, self.lobby_code = self.lobby_code, ""
        def do_clean():
            try:
                url = f"{FIREBASE_URL}lobbies/{code_to_clean}.json"
                data = self.session.get(url, timeout=2).json()
                if data:
                    players = data.get("players", {})
                    if self.player_id in players:
                        self.session.delete(f"{FIREBASE_URL}lobbies/{code_to_clean}/players/{self.player_id}.json", timeout=2)
                        del players[self.player_id]
                    if not players: self.session.delete(url, timeout=2)
                    elif self.is_host: self.session.patch(f"{FIREBASE_URL}lobbies/{code_to_clean}/settings.json", json={"host_id": list(players.keys())[0]}, timeout=2)
            except: pass
        t = threading.Thread(target=do_clean); t.start()
        if exit_mode: t.join(1.0)

    def charger_pseudo_local(self):
        p = os.path.join(os.getenv('APPDATA'), "SMOUT", "config.json")
        try:
            with open(p, 'r') as f: return json.load(f).get("pseudo", "ANONYME")
        except: return "ANONYME"

    def sauver_pseudo_local(self, p):
        if not p: return
        self.pseudo = p.upper(); d = os.path.join(os.getenv('APPDATA'), "SMOUT"); os.makedirs(d, exist_ok=True)
        try:
            cfg = {}
            if os.path.exists(os.path.join(d, "config.json")):
                with open(os.path.join(d, "config.json"), 'r') as f: cfg = json.load(f)
            cfg["pseudo"] = self.pseudo
            with open(os.path.join(d, "config.json"), 'w') as f: json.dump(cfg, f)
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
        for f in self.frames.values(): (setattr(f, "active_sync", False) if hasattr(f, "active_sync") else None)
        f = self.frames[name]; f.tkraise()
        if name == "PageCode": f.charger_liste()
        elif name == "PageLobby": f.entrer_lobby()
        elif name == "PageJeu": f.initialiser_partie()
        elif name == "PageScoreFinal": f.afficher_vainqueur()

    def fb_get(self, path):
        try: return self.session.get(f"{FIREBASE_URL}{path}.json", timeout=1.5).json()
        except: return None
    
    def fb_patch(self, path, data): threading.Thread(target=lambda: self._exec_req("patch", path, data), daemon=True).start()
    def fb_put(self, path, data): threading.Thread(target=lambda: self._exec_req("put", path, data), daemon=True).start()
    def fb_delete(self, path): threading.Thread(target=lambda: self._exec_req("delete", path), daemon=True).start()

    def _exec_req(self, method, path, data=None):
        try:
            u = f"{FIREBASE_URL}{path}.json" if path.startswith("lobbies") else f"{FIREBASE_URL}lobbies/{path}.json"
            getattr(self.session, method)(u, json=data, timeout=2)
        except: pass

class PageAccueil(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG); self.controller = controller
        c = tk.Frame(self, bg=BG); c.place(relx=0.5, rely=0.5, anchor="center")
        LogoSmout(c, 110).pack(pady=(0, 30))
        tk.Label(c, text="TON PSEUDO", font=("Helvetica", 10, "bold"), fg=ACCENT2, bg=BG).pack()
        self.sv_pseudo = tk.StringVar(value=self.controller.pseudo); self.sv_pseudo.trace_add("write", self.format_p)
        tk.Entry(c, textvariable=self.sv_pseudo, font=("Courier", 18, "bold"), justify="center", bg="#052132", fg="white", width=15).pack(pady=(5, 20))
        BoutonPro(c, "CRÉER UN LOBBY", self.creer, color="#22c55e", width=250).pack(pady=8)
        BoutonPro(c, "REJOINDRE UN LOBBY", lambda: self.controller.show_frame("PageCode"), color=BTN1, width=250).pack(pady=8)
        BoutonPro(c, "MENU", lambda: self.controller.controller.creer_menu_accueil(), color=BTN3, width=250).pack(pady=20)
    
    def format_p(self, *args):
        v = "".join([c.upper() for c in self.sv_pseudo.get() if c.isalnum()])
        if self.sv_pseudo.get() != v: self.sv_pseudo.set(v)
        self.controller.sauver_pseudo_local(v)
        
    def creer(self): (self.controller.show_frame("PageHostSetup") if self.sv_pseudo.get().strip() else None)

class PageHostSetup(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG); self.controller = controller
        c = tk.Frame(self, bg=BG); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="CONFIGURATION DU SALON", font=FONT_UI, fg=TXT1, bg=BG).pack(pady=20)
        tk.Label(c, text="MOT DE PASSE (Optionnel)", font=("Helvetica", 10), fg=TXT3, bg=BG).pack()
        self.e_pass = tk.Entry(c, font=FONT_UI, justify="center", bg="#052132", fg="white", width=20); self.e_pass.pack(pady=10)
        self.is_pub, btn_f = True, tk.Frame(c, bg=BG); btn_f.pack(pady=10)
        self.b_pub = BoutonPro(btn_f, "PUBLIC", lambda: self.set_vis(True), width=120, color=BTN1)
        self.b_pri = BoutonPro(btn_f, "PRIVÉ", lambda: self.set_vis(False), width=120, color="#475569")
        self.b_pub.pack(side="left", padx=5); self.b_pri.pack(side="left", padx=5)
        BoutonPro(c, "CRÉER", self.valider, color="#22c55e").pack(pady=20)
        BoutonPro(c, "RETOUR", lambda: controller.show_frame("PageAccueil"), color=BTN3).pack()
    def set_vis(self, v):
        self.is_pub = v; self.b_pub.set_color(BTN1 if v else "#475569", None); self.b_pri.set_color("#475569" if v else ACCENT2, None)
    def valider(self):
        self.controller.settings_config.update({"password": self.e_pass.get().strip(), "visible": self.is_pub})
        self.controller.is_host, self.controller.lobby_code = True, ""; self.controller.show_frame("PageLobby")

class PageCode(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG); self.controller = controller
        self.c = tk.Frame(self, bg=BG); self.c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(self.c, text="CODE DU LOBBY", font=("Helvetica", 25, "bold"), fg=TXT1, bg=BG).pack(pady=20)
        self.e = tk.Entry(self.c, font=("Courier", 45, "bold"), justify="center", width=5, bg="#052132", fg=ACCENT2)
        self.e.pack(pady=10); self.e.bind("<Return>", lambda e: self.valider())
        BoutonPro(self.c, "REJOINDRE", self.valider, color="#22c55e").pack(pady=20)
        tk.Frame(self.c, height=2, bg=BTN1, width=350).pack(pady=15); self.cl = tk.Frame(self.c, bg=BG); self.cl.pack()
        self.canvas = tk.Canvas(self.cl, width=420, height=220, bg="#052132", highlightthickness=0)
        self.scroll = tk.Scrollbar(self.cl, orient="vertical", command=self.canvas.yview)
        self.lf = tk.Frame(self.canvas, bg="#052132"); self.canvas.create_window((0,0), window=self.lf, anchor="nw", width=420)
        self.canvas.configure(yscrollcommand=self.scroll.set); self.canvas.pack(side="left"); self.scroll.pack(side="right", fill="y")
        self.lf.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.pass_view = tk.Frame(self, bg=BG, highlightthickness=2, highlightbackground=ACCENT2)
        tk.Label(self.pass_view, text="MOT DE PASSE REQUIS", fg=TXT1, bg=BG, font=FONT_UI).pack(pady=10)
        self.e_pw = tk.Entry(self.pass_view, show="*", font=FONT_UI, justify="center"); self.e_pw.pack(pady=5, padx=20)
        self.e_pw.bind("<Return>", lambda e: self.check_pw()) # Validation par touche Entrée ajoutée
        pb = tk.Frame(self.pass_view, bg=BG); pb.pack(pady=10)
        BoutonPro(pb, "VALIDER", self.check_pw, width=100, height=30, color="#22c55e").pack(side="left", padx=5)
        BoutonPro(pb, "ANNULER", lambda: self.pass_view.place_forget(), width=100, height=30, color=ACCENT1).pack(side="left", padx=5)
        BoutonPro(self.c, "RAFRAÎCHIR", self.charger_liste, color=BTN1, width=250).pack(pady=10)
        BoutonPro(self.c, "RETOUR", lambda: controller.show_frame("PageAccueil"), color=BTN3).pack()
    def charger_liste(self):
        for w in self.lf.winfo_children(): w.destroy()
        data = self.controller.fb_get("lobbies") or {}
        for code, val in data.items():
            s, p = val.get("settings", {}), val.get("players", {})
            if s.get("visible") and val.get("status") == "waiting":
                f = tk.Frame(self.lf, bg=BG, pady=8, padx=10, highlightthickness=1, highlightbackground=BTN1); f.pack(fill="x", pady=2)
                tk.Label(f, text=f"#{code} | Hôte: {p.get(s.get('host_id'), {}).get('name', 'ANONYME')} | {len(p)}/4" + (" 🔒" if s.get("password") else ""), fg="white", bg=BG, font=("Helvetica", 9, "bold")).pack(side="left")
                BoutonPro(f, "REJOINDRE", lambda c=code: self.tenter_join(c), width=130, height=30, color="#22c55e").pack(side="right")
    def tenter_join(self, code):
        data = self.controller.fb_get(f"lobbies/{code}")
        if not data: return
        self.t_c, self.t_p = code, data.get("settings", {}).get("password")
        if self.t_p: self.pass_view.place(relx=0.5, rely=0.5, anchor="center"); self.e_pw.delete(0, tk.END); self.e_pw.focus_set()
        else: self.rejoindre(code)
    def check_pw(self): (self.rejoindre(self.t_c) if self.e_pw.get() == self.t_p else [self.pass_view.config(bg=ACCENT1), self.after(200, lambda: self.pass_view.config(bg=BG))])
    def valider(self):
        c = self.e.get().strip()
        if c: (self.tenter_join(c) if self.controller.fb_get(f"lobbies/{c}") else tkm.showwarning("SMOUT", "Lobby introuvable"))
    def rejoindre(self, code):
        self.pass_view.place_forget(); self.controller.is_host = False; d = self.controller.fb_get(f"lobbies/{code}")
        if d and len(d.get("players", {})) < 4:
            self.controller.lobby_code, self.controller.current_score = code, 0
            self.controller.fb_patch(f"lobbies/{code}/players/{self.controller.player_id}", {"name": self.controller.pseudo, "score": 0, "last_seen": time.time()})
            self.controller.show_frame("PageLobby")

class PageLobby(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG); self.controller, self.active_sync = controller, False
        c = tk.Frame(self, bg=BG); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="SALLE D'ATTENTE", font=("Arial Black", 20), fg=TXT1, bg=BG).pack()
        self.lbl_code = tk.Label(c, text="----", font=("Courier", 55, "bold"), fg=ACCENT2, bg="#052132", padx=25); self.lbl_code.pack(pady=15)
        self.grid_p = tk.Frame(c, bg=BG); self.grid_p.pack(pady=10); self.player_slots = []
        for i in range(4):
            f = tk.Frame(self.grid_p, bg="#052132", width=120, height=50, highlightbackground=BTN1, highlightthickness=1); f.grid_propagate(False); f.grid(row=i//2, column=i%2, padx=5, pady=5)
            l = tk.Label(f, text="VIDE", font=("Helvetica", 10, "bold"), fg=TXT3, bg="#052132"); l.place(relx=0.5, rely=0.5, anchor="center"); self.player_slots.append(l)
        fp = tk.Frame(c, bg=BG); fp.pack()
        self.s_rounds, self.s_essais = SingleSlider(fp, 1, 10, 3, label="ROUNDS", callback=lambda v: self.sync_params()), SingleSlider(fp, 4, 10, 6, label="ESSAIS", callback=lambda v: self.sync_params())
        self.s_len, self.s_time = RangeSlider(fp, 6, 10, 6, 10, callback=lambda v1, v2: self.sync_params()), TimeSelector(fp, 180, callback=lambda v: self.sync_params())
        [s.pack() for s in [self.s_rounds, self.s_essais, self.s_len, self.s_time]]
        self.lbl_status = tk.Label(c, text="EN ATTENTE...", font=FONT_UI, fg=ACCENT1, bg=BG); self.lbl_status.pack(pady=10)
        self.btn_lancer = BoutonPro(c, "LANCER LE MATCH", self.lancer, color="#22c55e", width=250)
        BoutonPro(c, "QUITTER LE LOBBY", self.quitter, color=BTN3, width=250).pack(pady=5)
    
    def sync_params(self):
        if self.controller.is_host and self.active_sync:
            mi, ma = self.s_len.get_values(); sc = self.controller.settings_config
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", {"rounds": self.s_rounds.get_value(), "essais": self.s_essais.get_value(), "min": mi, "max": ma, "timer": self.s_time.v, "host_id": self.controller.player_id, "password": sc["password"], "visible": sc["visible"]})
    
    def entrer_lobby(self):
        self.active_sync = True; self.btn_lancer.pack_forget()
        if self.controller.is_host and not self.controller.lobby_code:
            self.controller.lobby_code = str(random.randint(1000, 9999)); sc = self.controller.settings_config
            self.controller.fb_put(f"lobbies/{self.controller.lobby_code}", {"status": "waiting", "settings": {"rounds":3, "essais":6, "min":6, "max":10, "timer": 180, "host_id": self.controller.player_id, "password": sc["password"], "visible": sc["visible"]}, "players": {self.controller.player_id: {"name": self.controller.pseudo, "score": 0, "last_seen": time.time()}}})
        self.lbl_code.config(text=self.controller.lobby_code); self.ecouter_lobby()
    
    def ecouter_lobby(self):
        if not self.active_sync: return
        d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if d:
            s, p, now = d.get("settings", {}), d.get("players", {}), time.time()
            for pid, pdat in list(p.items()):
                # On marque "DÉCONNECTÉ" après 8s sans signal, on supprime après 15s
                if now - pdat.get("last_seen", 0) > 15: self.controller.fb_delete(f"lobbies/{self.controller.lobby_code}/players/{pid}"); del p[pid]
            if not p: self.controller.fb_delete(f"lobbies/{self.controller.lobby_code}"); self.quitter(); return
            hid = s.get("host_id")
            if hid not in p: hid = list(p.keys())[0]; self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/settings", {"host_id": hid})
            self.controller.is_host = (hid == self.controller.player_id)
            if not self.controller.is_host:
                self.s_rounds.set_val(s.get("rounds", 3)); self.s_essais.set_val(s.get("essais", 6)); self.s_len.set_vals(s.get("min", 6), s.get("max", 10)); self.s_time.set_val(s.get("timer", 180))
            if d.get("status") == "playing":
                self.active_sync = False; self.controller.settings_config.update({"target_word": s.get("target_word"), "essais": s.get("essais"), "round_num": s.get("current_round", 1), "rounds": s.get("rounds"), "timer": s.get("timer"), "start_time": s.get("start_time")})
                self.controller.show_frame("PageJeu"); return
            pids = list(p.keys())
            for i, slot in enumerate(self.player_slots):
                if i < len(pids):
                    pid = pids[i]; n = p[pid]["name"]
                    if pid == hid: n += " 👑"
                    # Ajout de la mention déconnecté si le heartbeat est vieux
                    if now - p[pid].get("last_seen", 0) > 8: n += " (DÉCONNECTÉ)"
                    slot.config(text=n, fg=(TXT1 if "(DÉCONNECTÉ)" not in n else ACCENT1))
                else: slot.config(text="VIDE", fg=TXT3)
            if len(p) > 1:
                self.lbl_status.config(text=f"🟢 {len(p)} JOUEURS", fg="#22c55e"); (self.btn_lancer.pack(pady=5) if self.controller.is_host else None)
            else: self.lbl_status.config(text="🔴 EN ATTENTE...", fg=ACCENT1); self.btn_lancer.pack_forget()
            [sw.activer(self.controller.is_host) for sw in [self.s_rounds, self.s_essais, self.s_len, self.s_time]]
        self.after(800, self.ecouter_lobby)

    def quitter(self): self.active_sync = False; self.controller.quitter_lobby_logic(); self.controller.show_frame("PageAccueil")

    def lancer(self):
        mi, ma = self.s_len.get_values(); f = [m for m in self.controller.liste_mots if mi <= len(m) <= ma]
        sc = self.controller.settings_config
        self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"status": "playing", "settings": {"target_word": random.choice(f or self.controller.liste_mots), "rounds": self.s_rounds.get_value(), "current_round": 1, "essais": self.s_essais.get_value(), "min": mi, "max": ma, "timer": self.s_time.v, "host_id": self.controller.player_id, "password": sc["password"], "visible": sc["visible"], "start_time": time.time()}, "match_data": None, "fini_states": None})

class PageJeu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG); self.controller, self.active_sync = controller, False
        self.timer_actif, self.last_sync_data = False, None
        self.main_c = tk.Frame(self, bg=BG); self.main_c.place(relx=0.5, rely=0.5, anchor="center")
        h = tk.Frame(self.main_c, bg=BG, pady=10); h.pack(fill="x")
        BoutonPro(h, "MENU", self.quitter_jeu, width=80, height=35, color=BTN3).pack(side="left", padx=10)
        self.lbl_info = tk.Label(h, text="ROUND", fg=ACCENT2, bg=BG, font=("Helvetica", 16, "bold")); self.lbl_info.pack(side="left", padx=10)
        self.lbl_scores = tk.Label(h, text="", fg=TXT1, bg=BG, font=("Helvetica", 10, "bold")); self.lbl_scores.pack(side="left", padx=20)
        self.lbl_timer = tk.Label(h, text="03:00", fg=TXT1, bg=BG, font=("Courier", 22, "bold")); self.lbl_timer.pack(side="right", padx=10)
        ga = tk.Frame(self.main_c, bg=BG); ga.pack()
        self.moi_side = tk.Frame(ga, bg=BG); self.moi_side.pack(side="left", padx=40)
        tk.Frame(ga, width=3, bg=BTN1).pack(side="left", fill="y", padx=20, pady=20)
        self.adv_container = tk.Frame(ga, bg=BG); self.adv_container.pack(side="left", padx=40, fill="y")
        self.btn_next = BoutonPro(self.main_c, "ROUND SUIVANT", self.clic_suivant, color=ACCENT2, width=250)
    
    def quitter_jeu(self): self.active_sync, self.timer_actif = False, False; self.controller.quitter_lobby_logic(); self.controller.controller.creer_menu_accueil()
    
    def initialiser_partie(self):
        self.active_sync, self.last_sync_data, self.timer_actif = False, None, False; self.btn_next.pack_forget()
        [w.destroy() for w in self.moi_side.winfo_children() + self.adv_container.winfo_children()]
        conf = self.controller.settings_config
        self.mot, self.round_actuel, self.start_time_round = conf.get("target_word", "SMOUT"), conf.get("round_num", 1), conf.get("start_time", time.time())
        self.ligne, self.tape, self.fini_local, self.temps_restant = 0, [self.mot[0]], False, conf.get("timer", 180)
        self.statut_lettres, self.boutons_clavier = {l: "#052132" for l in ALPHABET}, {}
        
        dm = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        hid = dm.get("settings", {}).get("host_id") if dm else None
        self.labels_moi = self.creer_grille(self.moi_side, self.controller.pseudo + (" 👑" if self.controller.player_id == hid else ""), True)
        self.msg_c = tk.Frame(self.moi_side, bg=BG, height=40); self.msg_c.pack()
        self.lbl_msg = tk.Label(self.msg_c, text="", font=("Helvetica", 11, "bold"), bg=BG, fg=TXT1); self.lbl_msg.pack(side="left")
        self.btn_def = tk.Label(self.msg_c, text="?", font=("Helvetica", 10, "bold", "underline"), bg=BG, fg=BTN1, cursor="hand2")
        self.btn_def.bind("<Button-1>", lambda e: webbrowser.open(f"https://www.google.com/search?q=D%C3%A9finition+du+mot+{self.mot}"))
        
        self.creer_clavier(self.moi_side); bf = tk.Frame(self.moi_side, bg=BG); bf.pack(pady=10)
        self.btn_valider = BoutonPro(bf, "VALIDER", self.valider, width=100, color="#22c55e"); self.btn_valider.pack(side="left", padx=5)
        self.btn_effacer = BoutonPro(bf, "EFFACER", self.effacer, width=100, color=BTN3); self.btn_effacer.pack(side="left", padx=5)
        
        self.adv_labels = {} # Stockage des labels de noms pour mise à jour déconnexion
        self.adv_grids = {}
        if dm:
            for pid, p in dm.get("players", {}).items():
                if pid != self.controller.player_id:
                    f = tk.Frame(self.adv_container, bg=BG, pady=5); f.pack()
                    l_name = tk.Label(f, text=p["name"] + (" 👑" if pid == hid else ""), font=("Helvetica", 11, "bold"), fg=TXT1, bg=BG)
                    l_name.pack(); self.adv_labels[pid] = l_name
                    self.adv_grids[pid] = self.creer_grille_sans_label(f)
                    
        self.active_sync, self.timer_actif = True, True; self.update_timer()
        threading.Thread(target=self.bg_sync, daemon=True).start(); self.ui_loop()
        self.controller.focus_set(); self.controller.bind("<Key>", self.clavier_physique); self.maj_affichage()

    def bg_sync(self):
        while self.active_sync:
            d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
            if d: self.last_sync_data = d
            time.sleep(0.8)

    def ui_loop(self):
        if self.active_sync:
            if self.last_sync_data: self.traiter_match(self.last_sync_data)
            self.after(200, self.ui_loop)

    def traiter_match(self, d):
        if d.get("status") == "waiting": return
        if d.get("status") == "finished": self.active_sync = False; self.controller.show_frame("PageScoreFinal"); return
        s, p, now = d.get("settings", {}), d.get("players", {}), time.time()
        if int(s.get("current_round", 1)) > int(self.round_actuel): 
            self.active_sync = False; self.controller.settings_config.update({"target_word": s.get("target_word"), "round_num": int(s["current_round"]), "start_time": s.get("start_time")}); self.initialiser_partie(); return
        
        hid = s.get("host_id")
        self.lbl_scores.config(text=" | ".join([f"{v['name']}: {v.get('score', 0)}" for v in p.values()]))
        self.lbl_info.config(text=f"ROUND {s.get('current_round')} / {s.get('rounds')}")
        
        # Mise à jour des noms adverses pour afficher la déconnexion
        for pid, label in self.adv_labels.items():
            if pid in p:
                n = p[pid]["name"] + (" 👑" if pid == hid else "")
                if now - p[pid].get("last_seen", 0) > 8: n += " (DÉCONNECTÉ)"
                label.config(text=n, fg=(TXT1 if "(DÉCONNECTÉ)" not in n else ACCENT1))

        fs = d.get("fini_states") or {}; fc = sum(1 for pid in p if fs.get(pid))
        if fc >= len(p): self.timer_actif = False
        md = d.get("match_data", {})
        for pid, grid in self.adv_grids.items():
            if pid in md:
                for l_idx, content in (md[pid].items() if isinstance(md[pid], dict) else enumerate(md[pid])):
                    if content and int(l_idx) < len(grid):
                        for c_idx, coul in enumerate(content.get("c", [])): grid[int(l_idx)][c_idx].config(bg=coul, fg=get_txt_color(coul))
                        if self.fini_local: [grid[int(l_idx)][c_idx].config(text=char) for c_idx, char in enumerate(content.get("l", []))]
        if self.fini_local:
            if fc >= len(p):
                self.lbl_msg.config(text=f"LE MOT ÉTAIT : {self.mot} ", fg=ACCENT2); self.btn_def.pack(side="left")
                if self.controller.is_host and not self.btn_next.winfo_ismapped():
                    self.btn_next.set_text("VOIR LES RÉSULTATS" if int(s['current_round']) >= int(s['rounds']) else "ROUND SUIVANT"); self.btn_next.pack(pady=15)
            else: self.lbl_msg.config(text=f"ATTENTE... ({fc}/{len(p)})", fg=BTN1)

    def update_timer(self):
        if not self.timer_actif: return
        self.temps_restant = max(0, int(int(self.controller.settings_config.get("timer", 180)) - (time.time() - self.start_time_round)))
        m, s = divmod(self.temps_restant, 60); self.lbl_timer.config(text=f"{m:02d}:{s:02d}", fg=TXT1 if self.temps_restant > 30 else ACCENT1)
        if self.temps_restant <= 0 and not self.fini_local: self.finir_round(False)
        else: self.after(500, self.update_timer)
    
    def valider(self):
        if len(self.tape) != len(self.mot) or self.fini_local: return
        t = "".join(self.tape)
        if t not in self.controller.banque_verif and t != self.mot:
            self.lbl_msg.config(text="MOT INCONNU", fg=ACCENT1); self.after(1000, lambda: self.lbl_msg.config(text="") if not self.fini_local else None); return
        res, secret = [MUTED]*len(self.mot), list(self.mot)
        for i in range(len(self.mot)):
            if self.tape[i] == self.mot[i]: res[i], secret[i] = ACCENT1, None
        for i in range(len(self.mot)):
            if res[i] != ACCENT1 and self.tape[i] in secret: res[i] = ACCENT2; secret[secret.index(self.tape[i])] = None
        for i, char in enumerate(self.tape):
            cur = self.statut_lettres.get(char, "#052132")
            if res[i] == ACCENT1: self.statut_lettres[char] = ACCENT1
            elif res[i] == ACCENT2 and cur != ACCENT1: self.statut_lettres[char] = ACCENT2
            elif res[i] == MUTED and cur not in [ACCENT1, ACCENT2]: self.statut_lettres[char] = MUTED
        self.maj_clavier()
        for i, c in enumerate(res): self.labels_moi[self.ligne][i].config(bg=c, fg=get_txt_color(c))
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/match_data/{self.controller.player_id}/{self.ligne}", {"c": res, "l": self.tape})
        if t == self.mot: self.finir_round(True)
        elif self.ligne >= self.controller.settings_config["essais"]-1: self.finir_round(False)
        else: self.ligne += 1; self.tape = [self.mot[0]]; self.maj_affichage()
    
    def effacer(self): (self.tape.pop() if not self.fini_local and len(self.tape) > 1 else None); self.maj_affichage()
    
    def finir_round(self, vic):
        self.fini_local = True; self.btn_valider.pack_forget(); self.btn_effacer.pack_forget()
        if vic: self.controller.current_score += 1; self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}/players/{self.controller.player_id}", {"score": self.controller.current_score})
        self.controller.fb_put(f"lobbies/{self.controller.lobby_code}/fini_states/{self.controller.player_id}", True)
    
    def clic_suivant(self):
        self.btn_next.pack_forget(); d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if not d: return
        s = d["settings"]
        if int(s["current_round"]) < int(s["rounds"]):
            f = [m for m in self.controller.liste_mots if int(s["min"]) <= len(m) <= int(s["max"])]
            s.update({"target_word": random.choice(f or self.controller.liste_mots), "current_round": int(s["current_round"])+1, "start_time": time.time()})
            self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"settings": s, "status": "playing", "match_data": None, "fini_states": None})
        else: self.controller.fb_patch(f"lobbies/{self.controller.lobby_code}", {"status": "finished"})
    
    def clavier_physique(self, e):
        if self.fini_local: return
        k, c = e.keysym, e.char.upper()
        if c in ALPHABET and len(c) == 1: (self.tape.append(c) if len(self.tape) < len(self.mot) else None); self.maj_affichage()
        elif k == "BackSpace": self.effacer()
        elif k == "Return": self.valider()
    
    def maj_affichage(self):
        if self.fini_local: return
        for i, c in enumerate(self.tape): 
            coul = ACCENT1 if i == 0 else BG; self.labels_moi[self.ligne][i].config(text=c, bg=coul, fg=get_txt_color(coul))
        for i in range(len(self.tape), len(self.mot)): self.labels_moi[self.ligne][i].config(text="", bg=BG)
    
    def creer_grille(self, parent, name, main):
        tk.Label(parent, text=name, font=("Helvetica", 11, "bold"), fg=TXT1, bg=BG).pack(); return self.creer_grille_sans_label(parent, main)
    
    def creer_grille_sans_label(self, parent, main=False):
        g, rows, size = tk.Frame(parent, bg=BG), [], (28 if main else 10); g.pack()
        for l in range(self.controller.settings_config["essais"]):
            line = [tk.Label(g, text="", font=("Courier", size, "bold"), width=2, height=1, fg=TXT1, bg="#052132", borderwidth=1, relief="solid", highlightbackground=GRILLE, highlightthickness=1) for _ in range(len(self.mot))]
            [lbl.grid(row=l, column=c, padx=1, pady=1) for c, lbl in enumerate(line)]; rows.append(line)
        return rows
    
    def creer_clavier(self, parent):
        f = tk.Frame(parent, bg=BG); f.pack(pady=5)
        for r in ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ"]:
            row = tk.Frame(f, bg=BG); row.pack()
            for c in r: 
                btn = tk.Button(row, text=c, width=2, font=("Arial", 8, "bold"), bg="#052132", fg="white", relief="raised", bd=2, command=lambda x=c: (self.tape.append(x), self.maj_affichage()) if len(self.tape) < len(self.mot) and not self.fini_local else None)
                btn.pack(side="left", padx=1, pady=1); self.boutons_clavier[c] = btn
    def maj_clavier(self):
        for char, color in self.statut_lettres.items():
            if char in self.boutons_clavier:
                self.boutons_clavier[char].config(bg=color, fg=(get_txt_color(color) if color != MUTED else "#6b7280"), relief=("raised" if color != MUTED else "flat"), font=("Arial", 8, "bold" if color != MUTED else "bold overstrike"))

class PageScoreFinal(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG); self.controller, self.active_sync = controller, False
        c = tk.Frame(self, bg=BG); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="MATCH FINI", font=("Helvetica", 40, "bold"), fg=ACCENT2, bg=BG).pack(pady=30)
        self.lbl_res = tk.Label(c, text="", font=("Helvetica", 22, "bold"), fg=TXT1, bg=BG, justify="center"); self.lbl_res.pack(pady=30)
        self.btn_f = tk.Frame(c, bg=BG); self.btn_f.pack()
        self.btn_lobby = BoutonPro(self.btn_f, "RETOUR AU SALON", self.retour_lobby_host, color="#22c55e", width=300)
        BoutonPro(c, "RETOUR AU MENU", self.quitter_depuis_score, color=BTN3, width=300).pack(pady=10)
        self.lbl_wait = tk.Label(c, text="ATTENTE DE L'HÔTE...", font=FONT_UI, fg=MUTED, bg=BG)

    def quitter_depuis_score(self): self.active_sync = False; self.controller.quitter_lobby_logic(); self.controller.controller.creer_menu_accueil()

    def afficher_vainqueur(self):
        self.active_sync = True; self.btn_lobby.pack_forget(); self.lbl_wait.pack_forget()
        d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if d:
            p = d.get("players", {})
            if not p: return
            items = sorted(p.values(), key=lambda x: x.get("score", 0), reverse=True)
            winners = [v["name"] for v in items if v.get("score", 0) == items[0].get("score", 0)]
            self.lbl_res.config(text=f"{'VAINQUEUR : ' + winners[0] if len(winners)==1 else 'ÉGALITÉ : ' + ', '.join(winners)}\n\n" + "\n".join([f"{v['name']} : {v.get('score', 0)} pts" for v in items]))
            (self.btn_lobby.pack(pady=10) if self.controller.is_host else self.lbl_wait.pack(pady=10))
            self.ecouter_fin()

    def ecouter_fin(self):
        if self.active_sync:
            d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
            if d and d.get("status") == "waiting": self.active_sync = False; self.controller.show_frame("PageLobby")
            else: self.after(1000, self.ecouter_fin)

    def retour_lobby_host(self):
        d = self.controller.fb_get(f"lobbies/{self.controller.lobby_code}")
        if d:
            self.controller.current_score = 0; p = d.get("players", {})
            for pid in p: p[pid]["score"] = 0
            self.controller.fb_put(f"lobbies/{self.controller.lobby_code}", {"status": "waiting", "players": p, "settings": d.get("settings", {}), "match_data": None, "fini_states": None})
