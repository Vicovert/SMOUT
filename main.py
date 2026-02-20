import tkinter as tk
import os
import sys
import json
from page_solo import PageSolo, apply_theme_solo
from page_multi import PageMulti, LogoSmout, apply_theme_multi

# --- CONFIGURATION DES THÈMES (24 STYLES ORGANISÉS PAR 4) ---
THEMES = {
    # CLASSIQUE
    "SMOUT CLASSIC": {"bg": "#0a4160", "accent1": "#ef4444", "accent2": "#eab308", "highlight": "#0ea5e9", "muted": "#64748b", "type": "CLASSIQUE"},
    "MIDNIGHT": {"bg": "#18181b", "accent1": "#52525b", "accent2": "#a1a1aa", "highlight": "#3f3f46", "muted": "#71717a", "type": "CLASSIQUE"},
    "ARCTIC": {"bg": "#0c4a6e", "accent1": "#38bdf8", "accent2": "#f0f9ff", "highlight": "#7dd3fc", "muted": "#94a3b8", "type": "CLASSIQUE"},
    "SLATE": {"bg": "#1e293b", "accent1": "#475569", "accent2": "#94a3b8", "highlight": "#64748b", "muted": "#334155", "type": "CLASSIQUE"},
    
    # NATURE
    "FOREST": {"bg": "#064e3b", "accent1": "#10b981", "accent2": "#fbbf24", "highlight": "#34d399", "muted": "#94a3b8", "type": "NATURE"},
    "OCEAN": {"bg": "#1e3a8a", "accent1": "#0ea5e9", "accent2": "#60a5fa", "highlight": "#38bdf8", "muted": "#94a3b8", "type": "NATURE"},
    "DESERT": {"bg": "#451a03", "accent1": "#d97706", "accent2": "#fcd34d", "highlight": "#fbbf24", "muted": "#a8a29e", "type": "NATURE"},
    "SAKURA": {"bg": "#4c0519", "accent1": "#fb7185", "accent2": "#fce7f3", "highlight": "#fda4af", "muted": "#9f1239", "type": "NATURE"},

    # TECH
    "CYBERPUNK": {"bg": "#000000", "accent1": "#ff007f", "accent2": "#00f2ff", "highlight": "#7000ff", "muted": "#4b5563", "type": "TECH"},
    "MATRIX": {"bg": "#020617", "accent1": "#22c55e", "accent2": "#15803d", "highlight": "#4ade80", "muted": "#475569", "type": "TECH"},
    "VAPORWAVE": {"bg": "#2e1065", "accent1": "#ff71ce", "accent2": "#01cdfe", "highlight": "#b967ff", "muted": "#6b7280", "type": "TECH"},
    "HACKER": {"bg": "#000000", "accent1": "#00ff00", "accent2": "#008f11", "highlight": "#003b00", "muted": "#00ff41", "type": "TECH"},

    # DOUCEUR
    "LAVENDER": {"bg": "#4c1d95", "accent1": "#ec4899", "accent2": "#c084fc", "highlight": "#8b5cf6", "muted": "#94a3b8", "type": "DOUCEUR"},
    "BUBBLEGUM": {"bg": "#831843", "accent1": "#f472b6", "accent2": "#fb923c", "highlight": "#f9a8d4", "muted": "#be185d", "type": "DOUCEUR"},
    "NORDIC": {"bg": "#334155", "accent1": "#94a3b8", "accent2": "#f1f5f9", "highlight": "#cbd5e1", "muted": "#475569", "type": "DOUCEUR"},
    "PEACH": {"bg": "#7c2d12", "accent1": "#fb923c", "accent2": "#ffedd5", "highlight": "#fdba74", "muted": "#9a3412", "type": "DOUCEUR"},

    # RÉTRO
    "GAMEBOY": {"bg": "#0f380f", "accent1": "#8bac0f", "accent2": "#9bbc0f", "highlight": "#306230", "muted": "#8bac0f", "type": "RÉTRO"},
    "COMMODORE": {"bg": "#352879", "accent1": "#6c5eb5", "accent2": "#959595", "highlight": "#444444", "muted": "#352879", "type": "RÉTRO"},
    "COFFEE": {"bg": "#451a03", "accent1": "#b45309", "accent2": "#d97706", "highlight": "#f59e0b", "muted": "#a8a29e", "type": "RÉTRO"},
    "NEON 80S": {"bg": "#1e1b4b", "accent1": "#db2777", "accent2": "#facc15", "highlight": "#4338ca", "muted": "#312e81", "type": "RÉTRO"},

    # LUXE
    "ROYAL": {"bg": "#2e1065", "accent1": "#f59e0b", "accent2": "#d8b4fe", "highlight": "#a855f7", "muted": "#6b7280", "type": "LUXE"},
    "SUNSET": {"bg": "#450a0a", "accent1": "#f97316", "accent2": "#fde047", "highlight": "#ef4444", "muted": "#71717a", "type": "LUXE"},
    "GOLD": {"bg": "#1c1917", "accent1": "#ca8a04", "accent2": "#fef08a", "highlight": "#eab308", "muted": "#44403c", "type": "LUXE"},
    "PLATINUM": {"bg": "#0f172a", "accent1": "#94a3b8", "accent2": "#f8fafc", "highlight": "#334155", "muted": "#1e293b", "type": "LUXE"}
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class BoutonSquare(tk.Canvas):
    def __init__(self, parent, text, command, size=180, color="#f5deb3", is_wide=False, h_override=None):
        width = size * 2 + 60 if is_wide else size
        # Restauration de la logique de hauteur d'origine avec option d'écrasement
        height = h_override if h_override else (60 if is_wide else size)
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command = command
        self.color = color
        self.hover_color = self._adjust_color(color, 1.1)
        from page_multi import BLEU as B_IMPORT
        self.rect = self.draw_round_rect(4, 4, width-4, height-4, 15, fill=color)
        # Ajustement de la police pour les petits boutons de skin
        f_size = 9 if h_override and h_override < 100 else 12
        self.create_text(width/2, height/2, text=text, fill=B_IMPORT, font=("Helvetica", f_size, "bold"), width=width-20, justify="center")
        self.bind("<ButtonRelease-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.color))

    def _adjust_color(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = [min(255, max(0, int(c * factor))) for c in rgb]
        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(p, **kwargs, smooth=True)

class PageSkins(tk.Frame):
    def __init__(self, parent, controller):
        from page_multi import BLEU as B_IMPORT, JAUNE as J_IMPORT
        super().__init__(parent, bg=B_IMPORT)
        self.controller = controller
        
        tk.Label(self, text="CHOISIS TON STYLE", font=("Helvetica", 24, "bold"), fg=J_IMPORT, bg=B_IMPORT).pack(pady=(30, 20))
        
        # Grille de catégories (2 colonnes)
        main_grid = tk.Frame(self, bg=B_IMPORT)
        main_grid.place(relx=0.5, rely=0.45, anchor="center")
        
        # Placement selon le schéma
        layout_map = {
            "CLASSIQUE": (0, 0), "NATURE": (0, 1),
            "TECH": (1, 0),      "DOUCEUR": (1, 1),
            "RÉTRO": (2, 0),     "LUXE": (2, 1)
        }
        
        cat_data = {}
        for name, data in THEMES.items():
            cat = data["type"]
            if cat not in cat_data: cat_data[cat] = []
            cat_data[cat].append((name, data))

        for cat_name, themes in cat_data.items():
            r, c = layout_map[cat_name]
            cat_frame = tk.Frame(main_grid, bg=B_IMPORT, padx=20, pady=10)
            cat_frame.grid(row=r, column=c, sticky="nw")
            
            tk.Label(cat_frame, text=cat_name, font=("Helvetica", 11, "bold"), fg="white", bg=B_IMPORT).pack(anchor="w", padx=5, pady=(0, 5))
            
            row_f = tk.Frame(cat_frame, bg=B_IMPORT)
            row_f.pack()
            
            for name, colors in themes:
                f = tk.Frame(row_f, bg=B_IMPORT, padx=4)
                f.pack(side="left")
                
                # Aperçu plus haut (40px au lieu de 25px)
                preview = tk.Frame(f, bg=colors["bg"], width=110, height=40, highlightthickness=1, highlightbackground=colors["highlight"])
                preview.pack(pady=(0, 2))
                preview.pack_propagate(False)
                tk.Frame(preview, bg=colors["accent1"], width=20, height=15).place(x=10, y=12)
                tk.Frame(preview, bg=colors["accent2"], width=20, height=15).place(x=40, y=12)
                
                # Bouton thématique plus haut (70px au lieu de 45px)
                btn = BoutonSquare(f, name, lambda n=name: self.select_skin(n), size=110, h_override=70, color=colors["highlight"])
                btn.pack()

        BoutonSquare(self, "RETOUR AU MENU", self.controller.creer_menu_accueil, size=180, color="#94a3b8", is_wide=True).pack(side="bottom", pady=40)

    def select_skin(self, name):
        self.controller.apply_theme(name)
        self.controller.show_skins()

class MenuPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SMOUT")
        self.geometry("1000x850")
        
        self.config_dir = os.path.join(os.getenv('APPDATA'), "SMOUT")
        self.config_path = os.path.join(self.config_dir, "config.json")
        
        saved_theme = self.charger_parametre_theme()
        self.apply_theme(saved_theme, save=False)
        
        icon_path = resource_path(os.path.join('fichiers', 'logo.ico'))
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass
            
        self.container = tk.Frame(self, bg=BLEU)
        self.container.pack(fill="both", expand=True)
        self.creer_menu_accueil()

    def charger_parametre_theme(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    theme = data.get("theme", "SMOUT CLASSIC")
                    return theme if theme in THEMES else "SMOUT CLASSIC"
            except: pass
        return "SMOUT CLASSIC"

    def apply_theme(self, theme_name, save=True):
        theme_data = THEMES[theme_name]
        apply_theme_multi(theme_data)
        apply_theme_solo(theme_data)
        
        global BLEU, JAUNE, ROUGE
        from page_multi import BLEU as B, JAUNE as J, ROUGE as R
        BLEU, JAUNE, ROUGE = B, J, R
        
        self.configure(bg=BLEU)
        if hasattr(self, 'container'): self.container.configure(bg=BLEU)
        
        if save:
            os.makedirs(self.config_dir, exist_ok=True)
            data = {}
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
        from page_multi import BLEU as B_CUR, JAUNE as J_CUR, ROUGE as R_CUR
        self.container.configure(bg=B_CUR)
        main_frame = tk.Frame(self.container, bg=B_CUR)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        LogoSmout(main_frame, 130).pack(pady=(0, 60))
        ligne_boutons = tk.Frame(main_frame, bg=B_CUR); ligne_boutons.pack()
        BoutonSquare(ligne_boutons, "SOLO", self.ouvrir_solo, size=180, color=J_CUR).pack(side="left", padx=15)
        BoutonSquare(ligne_boutons, "MULTIJOUEUR", self.ouvrir_multi, size=180, color=R_CUR).pack(side="left", padx=15)
        
        from page_multi import BLEU_C
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

    def quitter_jeu(self):
        self.quit(); self.destroy()

if __name__ == "__main__":
    app = MenuPrincipal(); app.mainloop()
