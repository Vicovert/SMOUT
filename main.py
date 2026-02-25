import tkinter as tk
import os, sys, json, colorsys
from page_solo import PageSolo, apply_theme_solo
from page_multi import PageMulti, LogoSmout, apply_theme_multi

# --- CONFIGURATION DES THÈMES ---
THEMES = {
    "SMOUT CLASSIC": {
        "bg": "#084b60", "accent1": "#db3a34", "accent2": "#f7b735", "muted": "#053d4f",
        "btn1": "#f7b735", "btn2": "#db3a34", "btn3": "#0ea5e9", 
        "txt1": "#ffffff", "txt2": "#084b60", "txt3": "#e0f2fe", "type": "CLASSIQUE"
    },
    "MIDNIGHT": {
        "bg": "#18181b", "accent1": "#ef4444", "accent2": "#fca5a5", "muted": "#09090b",
        "btn1": "#ef4444", "btn2": "#3f3f46", "btn3": "#52525b",
        "txt1": "#f8fafc", "txt2": "#ffffff", "txt3": "#94a3b8", "type": "CLASSIQUE"
    },
    "ARCTIC": {
        "bg": "#f0f9ff", "accent1": "#0369a1", "accent2": "#7dd3fc", "muted": "#e0f2fe",
        "btn1": "#0ea5e9", "btn2": "#0369a1", "btn3": "#38bdf8",
        "txt1": "#0c4a6e", "txt2": "#ffffff", "txt3": "#0369a1", "type": "CLASSIQUE"
    },
    "SLATE": {
        "bg": "#0f172a", "accent1": "#1e40af", "accent2": "#60a5fa", "muted": "#020617",
        "btn1": "#3b82f6", "btn2": "#334155", "btn3": "#1e293b",
        "txt1": "#f1f5f9", "txt2": "#ffffff", "txt3": "#94a3b8", "type": "CLASSIQUE"
    },
    "VOLCANO": {
        "bg": "#121212", "accent1": "#9a3412", "accent2": "#fb923c", "muted": "#0a0a0a",
        "btn1": "#ea580c", "btn2": "#9a3412", "btn3": "#3f3f3f",
        "txt1": "#fb923c", "txt2": "#ffffff", "txt3": "#d4d4d4", "type": "NATURE"
    },
    "DESERT": {
        "bg": "#78350f", "accent1": "#b45309", "accent2": "#fde68a", "muted": "#451a03",
        "btn1": "#f59e0b", "btn2": "#b45309", "btn3": "#a16207",
        "txt1": "#db973d", "txt2": "#451a03", "txt3": "#fbbf24", "type": "NATURE"
    },
    "OCEAN": {
        "bg": "#0c4a6e", "accent1": "#0ea5e9", "accent2": "#7dd3fc", "muted": "#083344",
        "btn1": "#38bdf8", "btn2": "#0ea5e9", "btn3": "#1e293b",
        "txt1": "#f0f9ff", "txt2": "#ffffff", "txt3": "#7dd3fc", "type": "NATURE"
    },
    "SAKURA": {
        "bg": "#ffe8f9", "accent1": "#be123c", "accent2": "#fda4af", "muted": "#ffdce0",
        "btn1": "#fb7185", "btn2": "#be123c", "btn3": "#f0a8a8",
        "txt1": "#4c0519", "txt2": "#ffffff", "txt3": "#be123c", "type": "NATURE"
    },
    "CYBERPUNK": {
        "bg": "#1a1a1a", "accent1": "#db2777", "accent2": "#f472b6", "muted": "#000000",
        "btn1": "#00f2ff", "btn2": "#bd00ff", "btn3": "#00b8ff",
        "txt1": "#00f2ff", "txt2": "#000000", "txt3": "#f472b6", "type": "TECH"
    },
    "MATRIX": {
        "bg": "#052e16", "accent1": "#16a34a", "accent2": "#86efac", "muted": "#021a0c",
        "btn1": "#16a34a", "btn2": "#14532d", "btn3": "#334155",
        "txt1": "#00ff00", "txt2": "#000000", "txt3": "#86efac", "type": "TECH"
    },
    "RETRO": {
        "bg": "#1e1b4b", "accent1": "#4338ca", "accent2": "#c7d2fe", "muted": "#0f0e2b",
        "btn1": "#6366f1", "btn2": "#818cf8", "btn3": "#f472b6",
        "txt1": "#ffffff", "txt2": "#1e1b4b", "txt3": "#ffffff", "type": "TECH"
    },
    "VOLTAGE": {
        "bg": "#0f172a", "accent1": "#a16207", "accent2": "#fde047", "muted": "#020617",
        "btn1": "#eab308", "btn2": "#ca8a04", "btn3": "#334155",
        "txt1": "#cd9c0a", "txt2": "#ffffff", "txt3": "#ca8a04", "type": "TECH"
    },
    "PASTEL": {
        "bg": "#ffffff", "accent1": "#db2777", "accent2": "#f472b6", "muted": "#f5f5f4",
        "btn1": "#f472b6", "btn2": "#fbbf24", "btn3": "#d1d5db",
        "txt1": "#44403c", "txt2": "#ffffff", "txt3": "#78716c", "type": "DOUCEUR"
    },
    "LAVENDER": {
        "bg": "#f5f3ff", "accent1": "#7c3aed", "accent2": "#ddd6fe", "muted": "#ede9fe",
        "btn1": "#a78bfa", "btn2": "#8b5cf6", "btn3": "#c4b5fd",
        "txt1": "#4c1d95", "txt2": "#4c1d95", "txt3": "#4c1d95", "type": "DOUCEUR"
    },
    "COFFEE": {
        "bg": "#271612", "accent1": "#d97706", "accent2": "#fcd34d", "muted": "#1a0f0d",
        "btn1": "#a85d44", "btn2": "#d97706", "btn3": "#57534e",
        "txt1": "#fff7ed", "txt2": "#ffffff", "txt3": "#d3a392", "type": "DOUCEUR"
    },
    "MINT": {
        "bg": "#f0fdf4", "accent1": "#0d9e00", "accent2": "#86efac", "muted": "#dcfce7",
        "btn1": "#4ade80", "btn2": "#166534", "btn3": "#22c55e",
        "txt1": "#064e3b", "txt2": "#ffffff", "txt3": "#16a34a", "type": "DOUCEUR"
    },
    "GAMEBOY": {
        "bg": "#cadc9f", "accent1": "#306230", "accent2": "#8bac0f", "muted": "#b8cc8a",
        "btn1": "#8bac0f", "btn2": "#306230", "btn3": "#538058",
        "txt1": "#0f380f", "txt2": "#cadc9f", "txt3": "#306230", "type": "RÉTRO"
    },
    "ARCADE": {
        "bg": "#1f2937", "accent1": "#991b1b", "accent2": "#ef4444", "muted": "#111827",
        "btn1": "#3b82f6", "btn2": "#ef4444", "btn3": "#4b5563",
        "txt1": "#ffffff", "txt2": "#ffffff", "txt3": "#9ca3af", "type": "RÉTRO"
    },
    "VAPORWAVE": {
        "bg": "#2e1065", "accent1": "#701a75", "accent2": "#f472b6", "muted": "#1e0a45",
        "btn1": "#d8b4fe", "btn2": "#701a75", "btn3": "#9333ea",
        "txt1": "#f5d0fe", "txt2": "#2e1065", "txt3": "#c084fc", "type": "RÉTRO"
    },
    "NEON": {
        "bg": "#09090b", "accent1": "#1e40af", "accent2": "#60a5fa", "muted": "#020617",
        "btn1": "#3b82f6", "btn2": "#1e3a8a", "btn3": "#334155",
        "txt1": "#dbeafe", "txt2": "#ffffff", "txt3": "#60a5fa", "type": "RÉTRO"
    },
    "GOLD": {
        "bg": "#5d5d5d", "accent1": "#854d0e", "accent2": "#fde047", "muted": "#000000",
        "btn1": "#d4af37", "btn2": "#a16207", "btn3": "#281b1b",
        "txt1": "#d4af37", "txt2": "#ffffff", "txt3": "#f1e5ac", "type": "LUXE"
    },
    "AMETHYST": {
        "bg": "#1a0f1f", "accent1": "#7e22ce", "accent2": "#d8b4fe", "muted": "#0f0912",
        "btn1": "#a855f7", "btn2": "#7e22ce", "btn3": "#3b0764",
        "txt1": "#f5f3ff", "txt2": "#ffffff", "txt3": "#7e22ce", "type": "LUXE"
    },
    "EMERALD": {
        "bg": "#022c22", "accent1": "#065f46", "accent2": "#a7f3d0", "muted": "#011c16",
        "btn1": "#059669", "btn2": "#10b981", "btn3": "#334155",
        "txt1": "#ecfdf5", "txt2": "#ffffff", "txt3": "#064e3b", "type": "LUXE"
    },
    "OBSIDIAN": {
        "bg": "#070509", "accent1": "#3b0764", "accent2": "#a130c9", "muted": "#030204",
        "btn1": "#1a1221", "btn2": "#3b0764", "btn3": "#4d3a61",
        "txt1": "#b38ef3", "txt2": "#ffffff", "txt3": "#c862ff", "type": "LUXE"
    }
}

def get_contrast_color(hex_color):
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#f8fafc" if luminance < 0.6 else "#0f172a"
    except: return "white"

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ColorPickerWidget(tk.Frame):
    def __init__(self, parent, callback, bg_color):
        super().__init__(parent, bg=bg_color)
        self.callback = callback
        self.hue = 0.0
        self.can_sv = tk.Canvas(self, width=200, height=200, highlightthickness=1, cursor="cross")
        self.can_sv.grid(row=0, column=0, padx=5)
        self.can_h = tk.Canvas(self, width=20, height=200, highlightthickness=1, cursor="hand2")
        self.can_h.grid(row=0, column=1, padx=5)
        self._draw_hue_bar()
        self._draw_sv_map()
        self.can_h.bind("<B1-Motion>", self._on_hue_click)
        self.can_h.bind("<Button-1>", self._on_hue_click)
        self.can_sv.bind("<B1-Motion>", self._on_sv_click)
        self.can_sv.bind("<Button-1>", self._on_sv_click)

    def _draw_hue_bar(self):
        for y in range(200):
            h = y / 200
            rgb = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
            self.can_h.create_line(0, y, 20, y, fill=color)

    def _draw_sv_map(self):
        self.can_sv.delete("all")
        for x in range(0, 200, 5):
            for y in range(0, 200, 5):
                s, v = x / 200, 1.0 - (y / 200)
                rgb = colorsys.hsv_to_rgb(self.hue, s, v)
                color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
                self.can_sv.create_rectangle(x, y, x+5, y+5, fill=color, outline="")

    def _on_hue_click(self, event):
        self.hue = max(0, min(199, event.y)) / 200
        self._draw_sv_map()
        
    def _on_sv_click(self, event):
        s, v = max(0, min(199, event.x)) / 200, 1.0 - (max(0, min(199, event.y)) / 200)
        rgb = colorsys.hsv_to_rgb(self.hue, s, v)
        color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        self.callback(color)

class BoutonSquare(tk.Canvas):
    def __init__(self, parent, text, command, size=180, color="#f5deb3", is_wide=False, h_override=None, text_color=None):
        width = size * 2 + 60 if is_wide else size
        height = h_override if h_override else (60 if is_wide else size)
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command, self.color = command, color
        self.width, self.height = width, height
        self.text_val = text
        self.draw_button(color, text_color)
        self.bind("<ButtonRelease-1>", lambda e: self.command())

    def draw_button(self, color, text_color=None, bg_color=None):
        self.delete("all")
        if bg_color: self.configure(bg=bg_color)
        r, g, b = self._hex_to_rgb(color)
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        self.hover_color = self._adjust_color(color, 0.85 if lum > 0.7 else 1.2)
        self.rect = self.draw_round_rect(4, 4, self.width-4, self.height-4, 15, fill=color)
        f_size = 9 if (self.height < 100) else 12
        t_col = text_color if text_color else get_contrast_color(color)
        self.create_text(self.width/2, self.height/2, text=self.text_val, fill=t_col, font=("Helvetica", f_size, "bold"), width=self.width-20, justify="center")
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=color))

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _adjust_color(self, hex_color, factor):
        try:
            rgb = self._hex_to_rgb(hex_color)
            return '#{:02x}{:02x}{:02x}'.format(*[min(255, max(0, int(c * factor))) for c in rgb])
        except: return hex_color

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(p, **kwargs, smooth=True)

class PageCustomTheme(tk.Frame):
    def __init__(self, parent, controller):
        from page_multi import BG, TXT1, BTN1, BTN3, TXT2
        super().__init__(parent, bg=BG)
        self.controller, self.selected_key = controller, "bg"
        curr_name = self.controller.current_theme_name
        self.current_custom = THEMES[curr_name].copy()
        self.current_custom["type"] = "PERSO"
        
        tk.Label(self, text="CRÉATEUR DE THÈME", font=("Helvetica", 24, "bold"), fg=TXT1, bg=BG).pack(pady=15)
        main_ui = tk.Frame(self, bg=BG); main_ui.pack(expand=True, anchor="center")

        # GAUCHE : SÉLECTION DES PROPRIÉTÉS
        self.left_p = tk.Frame(main_ui, bg=BG); self.left_p.pack(side="left", padx=15)
        self.boxes = {}
        keys = [("bg", "Fond Principal"), ("accent1", "Lettre Validée"), ("accent2", "Lettre Mal Placée"), ("muted", "Lettre Absente"),
                ("btn1", "Bouton Solo"), ("btn2", "Bouton Multi"), ("btn3", "Bouton Skins"),
                ("txt1", "Texte Titre"), ("txt2", "Texte Bouton"), ("txt3", "Texte Info")]
        for k, lbl in keys:
            f = tk.Frame(self.left_p, bg=BG); f.pack(fill="x", pady=2)
            tk.Label(f, text=lbl, fg=TXT1, bg=BG, width=16, anchor="w").pack(side="left")
            b = tk.Canvas(f, width=35, height=22, bg=self.current_custom[k], highlightthickness=2, highlightbackground=TXT1, cursor="hand2")
            b.pack(side="left", padx=5); b.bind("<Button-1>", lambda e, k=k: self.select_prop(k))
            self.boxes[k] = b

        # CENTRE : PREVIEW DYNAMIQUE MOTUS
        self.center_p = tk.Frame(main_ui, bg=BG); self.center_p.pack(side="left", padx=15)
        tk.Label(self.center_p, text="APERÇU DU JEU", font=("Helvetica", 10, "bold"), fg=TXT1, bg=BG).pack(pady=5)
        self.preview_frame = tk.Frame(self.center_p, width=320, height=450, bg=self.current_custom["bg"], highlightthickness=2, highlightbackground=TXT1)
        self.preview_frame.pack_propagate(False); self.preview_frame.pack(pady=10)
        self.prev_title = tk.Label(self.preview_frame, text="MOTUS", font=("Helvetica", 18, "bold"), bg=self.current_custom["bg"], fg=self.current_custom["txt1"])
        self.prev_title.pack(pady=(15, 10))
        
        self.grid_frame = tk.Frame(self.preview_frame, bg=self.current_custom["bg"]); self.grid_frame.pack(pady=10)
        self.grid_cells = []
        cell_data = [("S", "accent1"), ("M", "accent2"), ("O", "muted")]
        for char, key in cell_data:
            c = tk.Label(self.grid_frame, text=char, font=("Helvetica", 16, "bold"), width=2, height=1, 
                         bg=self.current_custom[key], fg=self.current_custom["txt1"], relief="flat")
            c.pack(side="left", padx=5); self.grid_cells.append((c, key))

        self.prev_btn1 = BoutonSquare(self.preview_frame, "SOLO", lambda: None, size=140, h_override=40, color=self.current_custom["btn1"], text_color=self.current_custom["txt2"])
        self.prev_btn1.pack(pady=5)
        self.prev_btn2 = BoutonSquare(self.preview_frame, "MULTI", lambda: None, size=140, h_override=40, color=self.current_custom["btn2"], text_color=self.current_custom["txt2"])
        self.prev_btn2.pack(pady=5)
        self.prev_btn3 = BoutonSquare(self.preview_frame, "SKINS", lambda: None, size=140, h_override=40, color=self.current_custom["btn3"], text_color=self.current_custom["txt2"])
        self.prev_btn3.pack(pady=5)
        self.prev_info = tk.Label(self.preview_frame, text="Texte informatif du jeu...", font=("Helvetica", 8), bg=self.current_custom["bg"], fg=self.current_custom["txt3"])
        self.prev_info.pack(side="bottom", pady=15)

        # DROITE : NUANCIER ET MODIFICATION HEXADÉCIMALE
        self.right_p = tk.Frame(main_ui, bg=BG); self.right_p.pack(side="left", padx=15)
        self.picker = ColorPickerWidget(self.right_p, self.update_color, BG); self.picker.pack()
        
        # Champ de texte Hexadécimal
        hex_frame = tk.Frame(self.right_p, bg=BG)
        hex_frame.pack(fill="x", pady=10)
        tk.Label(hex_frame, text="CODE HEX :", fg=TXT1, bg=BG, font=("Helvetica", 9, "bold")).pack(side="left")
        self.hex_var = tk.StringVar(value=self.current_custom[self.selected_key])
        self.hex_entry = tk.Entry(hex_frame, textvariable=self.hex_var, font=("Helvetica", 10), width=10, bg=BG, fg=TXT1, insertbackground=TXT1)
        self.hex_entry.pack(side="right", padx=5)
        self.hex_var.trace_add("write", self.on_hex_edit)

        tk.Label(self.right_p, text="NOM DU STYLE :", fg=TXT1, bg=BG).pack(pady=(5,0))
        self.name_entry = tk.Entry(self.right_p, font=("Helvetica", 12), width=20); self.name_entry.insert(0, "STYLE PERSO"); self.name_entry.pack(pady=5)

        btn_f = tk.Frame(self, bg=BG); btn_f.pack(side="bottom", pady=25)
        BoutonSquare(btn_f, "ENREGISTRER", self.save, size=180, color=BTN1, text_color=TXT2, h_override=50).pack(side="left", padx=10)
        BoutonSquare(btn_f, "ANNULER", self.controller.show_skins, size=180, color=BTN3, text_color=TXT2, h_override=50).pack(side="left", padx=10)
        self.select_prop("bg")

    def select_prop(self, key):
        self.selected_key = key
        # On met à jour le code hex dans le champ pour la nouvelle propriété
        self.hex_var.set(self.current_custom[key])
        for k, b in self.boxes.items(): b.config(highlightbackground="white" if k == key else self.controller.current_txt1)

    def on_hex_edit(self, *args):
        """Appelé quand le texte hex est modifié manuellement"""
        val = self.hex_var.get().strip()
        # Validation simple format hex
        if len(val) == 7 and val.startswith('#'):
            try:
                # Test si c'est une couleur valide
                self.preview_frame.winfo_rgb(val)
                self.update_color(val, from_entry=True)
            except: pass

    def update_color(self, hex_col, from_entry=False):
        self.current_custom[self.selected_key] = hex_col
        self.boxes[self.selected_key].config(bg=hex_col)
        # Si ça vient du nuancier, on met à jour le champ hex
        if not from_entry:
            self.hex_var.set(hex_col)
        self._refresh_preview()

    def _refresh_preview(self):
        self.preview_frame.config(bg=self.current_custom["bg"])
        self.grid_frame.config(bg=self.current_custom["bg"])
        self.prev_title.config(bg=self.current_custom["bg"], fg=self.current_custom["txt1"])
        self.prev_info.config(bg=self.current_custom["bg"], fg=self.current_custom["txt3"])
        for cell, key in self.grid_cells: cell.config(bg=self.current_custom[key], fg=self.current_custom["txt1"])
        self.prev_btn1.draw_button(self.current_custom["btn1"], self.current_custom["txt2"], bg_color=self.current_custom["bg"])
        self.prev_btn2.draw_button(self.current_custom["btn2"], self.current_custom["txt2"], bg_color=self.current_custom["bg"])
        self.prev_btn3.draw_button(self.current_custom["btn3"], self.current_custom["txt2"], bg_color=self.current_custom["bg"])

    def save(self):
        name = self.name_entry.get().strip().upper()
        if name:
            THEMES[name] = self.current_custom.copy()
            self.controller.save_custom_themes_to_config()
            self.controller.apply_theme(name)
            self.controller.show_skins()

class PageSkins(tk.Frame):
    def __init__(self, parent, controller):
        from page_multi import BG as B_IMPORT, TXT1, BTN3, TXT2, BTN1
        super().__init__(parent, bg=B_IMPORT)
        self.controller = controller
        tk.Label(self, text="CHOISIS TON STYLE", font=("Helvetica", 24, "bold"), fg=TXT1, bg=B_IMPORT).pack(pady=(30, 20))
        main_grid = tk.Frame(self, bg=B_IMPORT); main_grid.place(relx=0.5, rely=0.45, anchor="center")
        layout_map = {"CLASSIQUE": (0, 0), "NATURE": (0, 1), "TECH": (1, 0), "DOUCEUR": (1, 1), "RÉTRO": (2, 0), "LUXE": (2, 1), "PERSO": (3, 0)}
        cat_data = {}; perso_count = 0
        for name, data in THEMES.items():
            cat = data.get("type", "CLASSIQUE")
            if cat == "PERSO": perso_count += 1
            if cat not in cat_data: cat_data[cat] = []
            cat_data[cat].append((name, data))
        for cat_name, themes in cat_data.items():
            r, c = layout_map.get(cat_name, (0, 0))
            cat_frame = tk.Frame(main_grid, bg=B_IMPORT, padx=20, pady=10)
            if cat_name == "PERSO": cat_frame.grid(row=r, column=0, columnspan=2)
            else: cat_frame.grid(row=r, column=c, sticky="nw")
            tk.Label(cat_frame, text=cat_name, font=("Helvetica", 11, "bold"), fg=TXT1, bg=B_IMPORT).pack(anchor="w", padx=5, pady=(0, 5))
            row_f = tk.Frame(cat_frame, bg=B_IMPORT); row_f.pack()
            for name, colors in themes:
                f = tk.Frame(row_f, bg=B_IMPORT, padx=4); f.pack(side="left")
                preview = tk.Frame(f, bg=colors["bg"], width=165, height=40, highlightthickness=1, highlightbackground=TXT1)
                preview.pack(pady=(0, 2)); preview.pack_propagate(False)
                tk.Frame(preview, bg=colors["accent1"], width=20, height=15).place(x=40, y=12)
                tk.Frame(preview, bg=colors["accent2"], width=20, height=15).place(x=72, y=12)
                btn = BoutonSquare(f, name, lambda n=name: self.select_skin(n), size=165, h_override=70, color=colors["btn1"], text_color=colors["txt2"])
                btn.pack()
                if colors.get("type") == "PERSO":
                    del_btn = tk.Canvas(preview, width=15, height=15, bg="#db3a34", highlightthickness=0, cursor="hand2")
                    del_btn.place(x=145, y=5); del_btn.create_text(8, 7, text="X", fill="white", font=("Arial", 8, "bold"))
                    del_btn.bind("<Button-1>", lambda e, n=name: self.delete_theme(n))
        bottom_f = tk.Frame(self, bg=B_IMPORT); bottom_f.pack(side="bottom", pady=40)
        if perso_count < 4:
            BoutonSquare(bottom_f, "CRÉER SON PROPRE THÈME", self.controller.show_custom_creator, size=180, color=BTN1, is_wide=True, text_color=TXT2).pack(pady=5)
        else:
            msg_f = tk.Frame(bottom_f, bg=B_IMPORT); msg_f.pack(pady=10)
            tk.Label(msg_f, text="LIMITE DE 4 THÈMES PERSO ATTEINTE", font=("Helvetica", 10, "bold"), fg="#db3a34", bg=B_IMPORT).pack()
            tk.Label(msg_f, text="Supprimez-en un pour en créer un nouveau", font=("Helvetica", 9), fg=TXT1, bg=B_IMPORT).pack()
        BoutonSquare(bottom_f, "RETOUR AU MENU", self.controller.creer_menu_accueil, size=180, color=BTN3, is_wide=True, text_color=TXT2).pack(pady=5)

    def select_skin(self, name):
        self.controller.apply_theme(name); self.controller.show_skins()

    def delete_theme(self, name):
        if name in THEMES:
            del THEMES[name]
            self.controller.save_custom_themes_to_config()
            self.controller.show_skins()

class MenuPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SMOUT"); self.geometry("1100x900")
        self.config_dir = os.path.join(os.getenv('APPDATA'), "SMOUT")
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.current_theme_name = "SMOUT CLASSIC"
        self.charger_themes_personnalises()
        self.apply_theme(self.charger_parametre_theme(), save=False)
        icon_path = resource_path(os.path.join('fichiers', 'logo.ico'))
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass
        self.container = tk.Frame(self, bg=self.current_bg); self.container.pack(fill="both", expand=True)
        self.creer_menu_accueil()

    def charger_themes_personnalises(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f).get("custom_themes", {})
                    for n, c in data.items(): c["type"] = "PERSO"; THEMES[n] = c
            except: pass

    def save_custom_themes_to_config(self):
        os.makedirs(self.config_dir, exist_ok=True)
        data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f: data = json.load(f)
            except: pass
        data["custom_themes"] = {n: d for n, d in THEMES.items() if d.get("type") == "PERSO"}
        with open(self.config_path, 'w') as f: json.dump(data, f)

    def charger_parametre_theme(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    t = json.load(f).get("theme", "SMOUT CLASSIC")
                    return t if t in THEMES else "SMOUT CLASSIC"
            except: pass
        return "SMOUT CLASSIC"

    def apply_theme(self, theme_name, save=True):
        self.current_theme_name = theme_name
        theme_data = THEMES[theme_name].copy()
        apply_theme_multi(theme_data); apply_theme_solo(theme_data)
        from page_multi import BG, BTN1, BTN2, BTN3, TXT1, TXT2
        self.current_bg, self.current_btn1, self.current_btn2, self.current_btn3, self.current_txt1, self.current_txt2 = BG, BTN1, BTN2, BTN3, TXT1, TXT2
        self.configure(bg=BG)
        if hasattr(self, 'container'): self.container.configure(bg=BG)
        if save:
            data = {}
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f: data = json.load(f)
                except: pass
            data["theme"] = theme_name
            with open(self.config_path, 'w') as f: json.dump(data, f)

    def creer_menu_accueil(self):
        for widget in self.container.winfo_children(): widget.destroy()
        from page_multi import BG, BTN1, BTN2, BTN3, TXT2
        main_frame = tk.Frame(self.container, bg=BG); main_frame.place(relx=0.5, rely=0.5, anchor="center")
        LogoSmout(main_frame, 130).pack(pady=(0, 60))
        l_btn = tk.Frame(main_frame, bg=BG); l_btn.pack()
        BoutonSquare(l_btn, "SOLO", self.ouvrir_solo, size=180, color=BTN1, text_color=TXT2).pack(side="left", padx=15)
        BoutonSquare(l_btn, "MULTIJOUEUR", self.ouvrir_multi, size=180, color=BTN2, text_color=TXT2).pack(side="left", padx=15)
        BoutonSquare(main_frame, "SKINS", self.show_skins, size=180, color=BTN3, is_wide=True, text_color=TXT2).pack(pady=10)
        BoutonSquare(main_frame, "QUITTER", self.quitter_jeu, size=180, color=BTN2, is_wide=True, text_color=TXT2).pack(pady=10)

    def show_skins(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageSkins(self.container, self).pack(fill="both", expand=True)

    def show_custom_creator(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageCustomTheme(self.container, self).pack(fill="both", expand=True)

    def ouvrir_solo(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageSolo(parent=self.container, controller=self).pack(fill="both", expand=True)

    def ouvrir_multi(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageMulti(parent=self.container, controller=self).pack(fill="both", expand=True)

    def quitter_jeu(self): self.quit(); self.destroy()

if __name__ == "__main__":
    app = MenuPrincipal(); app.mainloop()
