import tkinter as tk
import os, sys, json
from page_solo import PageSolo, apply_theme_solo
from page_multi import PageMulti, LogoSmout, apply_theme_multi

# --- CONFIGURATION DES THÈMES (accent1 contrasté, accent2 clair, muted = nuance du bg) ---
THEMES = {
    # CLASSIQUE
    "SMOUT CLASSIC": {"bg": "#0a4160", "accent1": "#dc2626", "accent2": "#fde047", "highlight": "#0ea5e9", "muted": "#1a5170", "type": "CLASSIQUE"},
    "MIDNIGHT": {"bg": "#09090b", "accent1": "#ef4444", "accent2": "#fca5a5", "highlight": "#3f3f46", "muted": "#1a1a1c", "type": "CLASSIQUE"},
    "ARCTIC": {"bg": "#f0f9ff", "accent1": "#0369a1", "accent2": "#7dd3fc", "highlight": "#bae6fd", "muted": "#e0f2fe", "type": "CLASSIQUE"},
    "SLATE": {"bg": "#0f172a", "accent1": "#3b82f6", "accent2": "#93c5fd", "highlight": "#334155", "muted": "#1e293b", "type": "CLASSIQUE"},
    
    # NATURE
    "FOREST": {"bg": "#022c22", "accent1": "#10b981", "accent2": "#6ee7b7", "highlight": "#10b981", "muted": "#0b3d33", "type": "NATURE"},
    "OCEAN": {"bg": "#0c4a6e", "accent1": "#38bdf8", "accent2": "#bae6fd", "highlight": "#0ea5e9", "muted": "#1b597d", "type": "NATURE"},
    "DESERT": {"bg": "#451a03", "accent1": "#f59e0b", "accent2": "#fcd34d", "highlight": "#d97706", "muted": "#552a13", "type": "NATURE"},
    "SAKURA": {"bg": "#fff1f2", "accent1": "#be123c", "accent2": "#fda4af", "highlight": "#fb7185", "muted": "#ffe4e6", "type": "NATURE"},

    # TECH
    "CYBERPUNK": {"bg": "#000000", "accent1": "#f472b6", "accent2": "#fce7f3", "highlight": "#00f2ff", "muted": "#1a1a1a", "type": "TECH"},
    "MATRIX": {"bg": "#020617", "accent1": "#22c55e", "accent2": "#86efac", "highlight": "#22c55e", "muted": "#0f172a", "type": "TECH"},
    "VAPORWAVE": {"bg": "#2e1065", "accent1": "#ff71ce", "accent2": "#fbcfe8", "highlight": "#01cdfe", "muted": "#3b1e75", "type": "TECH"},
    "HACKER": {"bg": "#000000", "accent1": "#16a34a", "accent2": "#4ade80", "highlight": "#166534", "muted": "#121212", "type": "TECH"},

    # DOUCEUR
    "LAVENDER": {"bg": "#f5f3ff", "accent1": "#6d28d9", "accent2": "#c084fc", "highlight": "#ddd6fe", "muted": "#ede9fe", "type": "DOUCEUR"},
    "BUBBLEGUM": {"bg": "#fdf2f8", "accent1": "#9d174d", "accent2": "#f9a8d4", "highlight": "#fbcfe8", "muted": "#fce7f3", "type": "DOUCEUR"},
    "NORDIC": {"bg": "#f8fafc", "accent1": "#334155", "accent2": "#94a3b8", "highlight": "#e2e8f0", "muted": "#f1f5f9", "type": "DOUCEUR"},
    "PEACH": {"bg": "#fff7ed", "accent1": "#9a3412", "accent2": "#fdba74", "highlight": "#ffedd5", "muted": "#ffedd5", "type": "DOUCEUR"},

    # RÉTRO
    "GAMEBOY": {"bg": "#cadc9f", "accent1": "#0f380f", "accent2": "#8bac0f", "highlight": "#9bbc0f", "muted": "#bbcda0", "type": "RÉTRO"},
    "COMMODORE": {"bg": "#352879", "accent1": "#8b5cf6", "accent2": "#c4b5fd", "highlight": "#959595", "muted": "#46398a", "type": "RÉTRO"},
    "COFFEE": {"bg": "#fafaf9", "accent1": "#451a03", "accent2": "#b45309", "highlight": "#d6d3d1", "muted": "#f5f5f4", "type": "RÉTRO"},
    "NEON 80S": {"bg": "#1e1b4b", "accent1": "#db2777", "accent2": "#f9a8d4", "highlight": "#facc15", "muted": "#2d2a5a", "type": "RÉTRO"},

    # LUXE
    "ROYAL": {"bg": "#1e1b4b", "accent1": "#6366f1", "accent2": "#a5b4fc", "highlight": "#f59e0b", "muted": "#2e2b5b", "type": "LUXE"},
    "SUNSET": {"bg": "#450a0a", "accent1": "#f43f5e", "accent2": "#fecdd3", "highlight": "#fde047", "muted": "#551a1a", "type": "LUXE"},
    "GOLD": {"bg": "#0c0a09", "accent1": "#facc15", "accent2": "#fef9c3", "highlight": "#fef08a", "muted": "#1c1a19", "type": "LUXE"},
    "PLATINUM": {"bg": "#0f172a", "accent1": "#94a3b8", "accent2": "#e2e8f0", "highlight": "#f8fafc", "muted": "#1e293b", "type": "LUXE"}
}

def get_contrast_color(hex_color):
    """Retourne une couleur de contraste douce selon la luminosité du fond"""
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6: return "white"
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#f1f5f9" if luminance < 0.5 else "#1e293b"
    except: return "white"

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class BoutonSquare(tk.Canvas):
    def __init__(self, parent, text, command, size=180, color="#f5deb3", is_wide=False, h_override=None):
        width = size * 2 + 60 if is_wide else size
        height = h_override if h_override else (60 if is_wide else size)
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command, self.color = command, color
        self.hover_color = self._adjust_color(color, 1.1)
        self.rect = self.draw_round_rect(4, 4, width-4, height-4, 15, fill=color)
        f_size = 9 if h_override and h_override < 100 else 12
        self.create_text(width/2, height/2, text=text, fill=get_contrast_color(color), font=("Helvetica", f_size, "bold"), width=width-20, justify="center")
        self.bind("<ButtonRelease-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.color))

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

class PageSkins(tk.Frame):
    def __init__(self, parent, controller):
        from page_multi import BLEU as B_IMPORT
        super().__init__(parent, bg=B_IMPORT)
        self.controller = controller
        tk.Label(self, text="CHOISIS TON STYLE", font=("Helvetica", 24, "bold"), fg=get_contrast_color(B_IMPORT), bg=B_IMPORT).pack(pady=(30, 20))
        
        main_grid = tk.Frame(self, bg=B_IMPORT)
        main_grid.place(relx=0.5, rely=0.45, anchor="center")
        
        layout_map = {"CLASSIQUE": (0, 0), "NATURE": (0, 1), "TECH": (1, 0), "DOUCEUR": (1, 1), "RÉTRO": (2, 0), "LUXE": (2, 1)}
        cat_data = {}
        for name, data in THEMES.items():
            cat = data["type"]
            if cat not in cat_data: cat_data[cat] = []
            cat_data[cat].append((name, data))

        for cat_name, themes in cat_data.items():
            r, c = layout_map[cat_name]
            cat_frame = tk.Frame(main_grid, bg=B_IMPORT, padx=20, pady=10)
            cat_frame.grid(row=r, column=c, sticky="nw")
            tk.Label(cat_frame, text=cat_name, font=("Helvetica", 11, "bold"), fg=get_contrast_color(B_IMPORT), bg=B_IMPORT).pack(anchor="w", padx=5, pady=(0, 5))
            
            row_f = tk.Frame(cat_frame, bg=B_IMPORT)
            row_f.pack()
            
            for name, colors in themes:
                f = tk.Frame(row_f, bg=B_IMPORT, padx=4); f.pack(side="left")
                grid_color = get_contrast_color(colors["bg"])
                preview = tk.Frame(f, bg=colors["bg"], width=165, height=40, highlightthickness=1, highlightbackground=grid_color)
                preview.pack(pady=(0, 2)); preview.pack_propagate(False)
                
                # Aperçu simplifié à 3 cases centré : accent1, accent2, muted
                tk.Frame(preview, bg=colors["accent1"], width=20, height=15).place(x=40, y=12)
                tk.Frame(preview, bg=colors["accent2"], width=20, height=15).place(x=72, y=12)
                tk.Frame(preview, bg=colors["muted"], width=20, height=15).place(x=104, y=12)
                
                btn = BoutonSquare(f, name, lambda n=name: self.select_skin(n), size=165, h_override=70, color=colors["highlight"])
                btn.pack()

        BoutonSquare(self, "RETOUR AU MENU", self.controller.creer_menu_accueil, size=180, color="#94a3b8", is_wide=True).pack(side="bottom", pady=40)

    def select_skin(self, name):
        self.controller.apply_theme(name); self.controller.show_skins()

class MenuPrincipal(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("SMOUT"); self.geometry("1000x850")
        self.config_dir = os.path.join(os.getenv('APPDATA'), "SMOUT"); self.config_path = os.path.join(self.config_dir, "config.json")
        saved_theme = self.charger_parametre_theme(); self.apply_theme(saved_theme, save=False)
        icon_path = resource_path(os.path.join('fichiers', 'logo.ico'))
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass
        self.container = tk.Frame(self, bg=BLEU); self.container.pack(fill="both", expand=True); self.creer_menu_accueil()

    def charger_parametre_theme(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f); theme = data.get("theme", "SMOUT CLASSIC")
                    return theme if theme in THEMES else "SMOUT CLASSIC"
            except: pass
        return "SMOUT CLASSIC"

    def apply_theme(self, theme_name, save=True):
        theme_data = THEMES[theme_name]
        theme_data["grid"] = get_contrast_color(theme_data["bg"])
        
        apply_theme_multi(theme_data)
        apply_theme_solo(theme_data)
        
        global BLEU, JAUNE, ROUGE
        from page_multi import BLEU as B, JAUNE as J, ROUGE as R
        BLEU, JAUNE, ROUGE = B, J, R
        self.configure(bg=BLEU)
        if hasattr(self, 'container'): self.container.configure(bg=BLEU)
        if save:
            os.makedirs(self.config_dir, exist_ok=True); data = {}
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f: data = json.load(f)
                except: pass
            data["theme"] = theme_name
            try:
                with open(self.config_path, 'w') as f: json.dump(data, f)
            except: pass

    def creer_menu_accueil(self):
        for widget in self.container.winfo_children(): widget.destroy()
        from page_multi import BLEU as B_CUR, JAUNE as J_CUR, ROUGE as R_CUR, BLEU_C
        self.container.configure(bg=B_CUR); main_frame = tk.Frame(self.container, bg=B_CUR)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        LogoSmout(main_frame, 130).pack(pady=(0, 60))
        ligne_boutons = tk.Frame(main_frame, bg=B_CUR); ligne_boutons.pack()
        BoutonSquare(ligne_boutons, "SOLO", self.ouvrir_solo, size=180, color=J_CUR).pack(side="left", padx=15)
        BoutonSquare(ligne_boutons, "MULTIJOUEUR", self.ouvrir_multi, size=180, color=R_CUR).pack(side="left", padx=15)
        BoutonSquare(main_frame, "SKINS", self.show_skins, size=180, color=BLEU_C, is_wide=True).pack(pady=10)
        BoutonSquare(main_frame, "QUITTER", self.quitter_jeu, size=180, color="#f87171", is_wide=True).pack(pady=10)

    def show_skins(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageSkins(self.container, self).pack(fill="both", expand=True)

    def ouvrir_solo(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageSolo(parent=self.container, controller=self).pack(fill="both", expand=True)

    def ouvrir_multi(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageMulti(parent=self.container, controller=self).pack(fill="both", expand=True)

    def quitter_jeu(self): self.quit(); self.destroy()

if __name__ == "__main__":
    app = MenuPrincipal(); app.mainloop()
