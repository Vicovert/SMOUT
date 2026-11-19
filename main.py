import tkinter as tk
import os, sys, json, colorsys
import design
from design import P, police, etiquette, Bouton, Panneau, Icone, Avatar, Logo, CarteMenu, Defilant, Champ, Superposition, arrondi, calculer_palette, melanger, contraste
design.charger_polices()  # avant la création de la fenêtre
from page_solo import PageSolo, PageMenuSolo, PageParametres, PageStats, apply_theme_solo
from page_multi import PageMulti, apply_theme_multi

THEME_PAR_DEFAUT = "PLATEAU DE NUIT"
ORDRE_CATEGORIES = ["SMOUT", "CLASSIQUE", "NATURE", "TECH", "DOUCEUR", "RÉTRO", "LUXE", "PERSO"]

THEMES = {
    # --- Thèmes de la refonte 6.0 (catégorie SMOUT) ---
    "PLATEAU DE NUIT": {
        "bg": "#0B1226", "accent1": "#C92F35", "accent2": "#F5B83D", "muted": "#131D3F",
        "btn1": "#F5B83D", "btn2": "#1B2A55", "btn3": "#2F3D72",
        "txt1": "#EAF0FF", "txt2": "#16130a", "txt3": "#A9B6DA", "type": "SMOUT",
        "panel": "#131D3F", "tuile": "#1B2A55", "bordure": "#2F3D72", "vide": "#0F1833"
    },
    "CLASSIQUE TV": {
        "bg": "#0A2463", "accent1": "#D62839", "accent2": "#F7C600", "muted": "#10306F",
        "btn1": "#F7C600", "btn2": "#1749B8", "btn3": "#2B57C4",
        "txt1": "#FFFFFF", "txt2": "#16130a", "txt3": "#AFC3F2", "type": "SMOUT",
        "panel": "#0E2C74", "tuile": "#1749B8", "bordure": "#3563D1", "vide": "#0C2869"
    },
    "PAPIER": {
        "bg": "#F4F1EA", "accent1": "#A8322D", "accent2": "#E9A93B", "muted": "#E9E3D5",
        "btn1": "#A8322D", "btn2": "#DCD3BF", "btn3": "#CFC5AE",
        "txt1": "#2A2420", "txt2": "#ffffff", "txt3": "#6E6359", "type": "SMOUT",
        "panel": "#ECE6DA", "tuile": "#DCD3BF", "bordure": "#C9BEA6", "vide": "#EFEAE0"
    },
    "MENTHE": {
        "bg": "#0F1E19", "accent1": "#1F8A5B", "accent2": "#F2C14E", "muted": "#16291F",
        "btn1": "#F2C14E", "btn2": "#1D3A30", "btn3": "#2C5345",
        "txt1": "#E8F5EE", "txt2": "#16130a", "txt3": "#9CC3B0", "type": "SMOUT",
        "panel": "#152A22", "tuile": "#1D3A30", "bordure": "#2C5345", "vide": "#12241D"
    },
    "ARCADE": {
        "bg": "#1A0F2B", "accent1": "#E2407A", "accent2": "#FFD23F", "muted": "#22153A",
        "btn1": "#FFD23F", "btn2": "#33204F", "btn3": "#4A2F70",
        "txt1": "#F6EEFF", "txt2": "#16130a", "txt3": "#BFA9E0", "type": "SMOUT",
        "panel": "#24163B", "tuile": "#33204F", "bordure": "#4A2F70", "vide": "#1F1334"
    },
    "CONTRASTE ÉLEVÉ": {
        "bg": "#000000", "accent1": "#0A84D6", "accent2": "#F0A202", "muted": "#141414",
        "btn1": "#F0A202", "btn2": "#262626", "btn3": "#3A3A3A",
        "txt1": "#FFFFFF", "txt2": "#000000", "txt3": "#D4D4D4", "type": "SMOUT",
        "panel": "#121212", "tuile": "#262626", "bordure": "#5A5A5A", "vide": "#0B0B0B"
    },
    # --- Thèmes historiques ---
    "SMOUT CLASSIC": {
        "bg": "#0b1329", "accent1": "#b81d24", "accent2": "#d4af37", "muted": "#1e293b",
        "btn1": "#d4af37", "btn2": "#b81d24", "btn3": "#475569", 
        "txt1": "#ffffff", "txt2": "#ffffff", "txt3": "#94a3b8", "type": "CLASSIQUE"
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
    "ARCADE CLASSIQUE": {
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


def resource_path(relative_path):
    return design.resource_path(relative_path)

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
        for x in range(0, 200, 10):
            for y in range(0, 200, 10):
                s, v = x / 200, 1.0 - (y / 200)
                rgb = colorsys.hsv_to_rgb(self.hue, s, v)
                color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
                self.can_sv.create_rectangle(x, y, x+10, y+10, fill=color, outline="")

    def _on_hue_click(self, event):
        self.hue = max(0, min(199, event.y)) / 200
        self._draw_sv_map()
        
    def _on_sv_click(self, event):
        s, v = max(0, min(199, event.x)) / 200, 1.0 - (max(0, min(199, event.y)) / 200)
        rgb = colorsys.hsv_to_rgb(self.hue, s, v)
        color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        self.callback(color)



def dessiner_apercu(c, pal, x0=0, y0=0, taille=46, ecart=8):
    """Mini-partie dessinée avec une palette donnée (aperçu d'un thème sans l'appliquer)."""
    lignes = [("STORE", "bmmaa"), ("SOUPE", "bmmaa"), ("SMO", "sss")]
    for r in range(4):
        mot, etats = lignes[r] if r < len(lignes) else ("", "")
        for col in range(5):
            x, y = x0 + col * (taille + ecart), y0 + r * (taille + ecart)
            ch = mot[col] if col < len(mot) else ""
            e = etats[col] if col < len(etats) else ""
            if e == "b": fill, fg = pal["bien"], pal["sur_bien"]
            elif e == "m": fill, fg = pal["mal"], pal["sur_mal"]
            elif e == "a": fill, fg = pal["absent"], pal["texte_absent"]
            elif e == "s": fill, fg = pal["tuile"], pal["texte"]
            else: fill, fg = pal["vide"], pal["texte"]
            arrondi(c, x, y, x + taille, y + taille, 8, fill=fill, outline="")
            if r == 2 and col == 3: arrondi(c, x + 1, y + 1, x + taille - 1, y + taille - 1, 8, fill="", outline=pal["mal"], width=2)
            if ch: c.create_text(x + taille / 2, y + taille / 2, text=ch, fill=fg, font=police("chiffres", taille * 0.5))


class CarteTheme(tk.Canvas):
    """Vignette d'un thème dessinée avec ses propres couleurs."""
    def __init__(self, parent, nom, theme, commande, choisi=False, actuel=False, on_suppr=None, largeur=206, hauteur=108):
        super().__init__(parent, width=largeur, height=hauteur, bg=P["fond"], highlightthickness=0, cursor="hand2")
        pal = calculer_palette(theme); l, h = largeur, hauteur
        if choisi: arrondi(self, 0, 0, l, h, 18, fill="", outline=P["mal"], width=3)
        arrondi(self, 4, 4, l - 4, h - 4, 15, fill=pal["fond"], outline=pal["bordure"] if pal["fond"] == P["fond"] else "")
        etats = [("S", "bien"), ("M", "tuile"), ("O", "mal"), ("U", "vide"), ("T", "bien")]
        for i, (ch, e) in enumerate(etats):
            x = 22 + i * 34
            fg = pal["sur_bien"] if e == "bien" else pal["sur_mal"] if e == "mal" else pal["texte_absent"] if e == "vide" else pal["texte"]
            arrondi(self, x, 22, x + 28, 50, 6, fill=pal[e], outline="")
            self.create_text(x + 14, 36, text=ch, fill=fg, font=police("chiffres", 14))
        nom_aff = design.nom_theme(nom)
        self.create_text(22, 80, text=nom_aff, anchor="w", fill=pal["texte"], font=police("texte", 16, True), width=l - 70)
        if actuel: self.create_line(l - 44, 80, l - 37, 87, l - 24, 72, fill=pal["texte"], width=2.5, capstyle="round", joinstyle="round")
        self.bind("<ButtonRelease-1>", lambda e: commande(nom))
        if on_suppr:
            arrondi(self, l - 34, 12, l - 12, 34, 6, fill=pal["panneau"], outline="", tags="x")
            self.create_text(l - 23, 23, text="×", fill=pal["texte"], font=police("texte", 16, True), tags="x")
            self.tag_bind("x", "<ButtonRelease-1>", lambda e: (on_suppr(nom), "break")[1])


class PageSkins(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"])
        self.controller = controller
        self.choix = controller.current_theme_name
        tk.Frame(self, bg=P["fond"], height=4).pack()
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(14, 0))
        Icone(h, "retour", controller.creer_menu_accueil).pack(side="left")
        corps = tk.Frame(self, bg=P["fond"]); corps.pack(fill="both", expand=True, padx=60, pady=(4, 20))
        etiquette(corps, "Thèmes", "titre", 46).pack(anchor="w", pady=(0, 22))
        ligne = tk.Frame(corps, bg=P["fond"]); ligne.pack(fill="both", expand=True)
        # Aperçu
        self.apercu = Panneau(ligne, padding=28, largeur=350); self.apercu.pack(side="left", anchor="n")
        i = self.apercu.interieur
        self.lbl_apercu = etiquette(i, "", "texte", 13, P["texte2"], True); self.lbl_apercu.pack()
        self.can = tk.Canvas(i, width=294, height=330, bg=P["panneau"], highlightthickness=0); self.can.pack(pady=(14, 18))
        self.btn_appliquer = Bouton(i, "Appliquer ce thème", self.appliquer, largeur=294, hauteur=50); self.btn_appliquer.pack()
        # Liste
        self.liste = Defilant(ligne, hauteur=600); self.liste.pack(side="left", fill="both", expand=True, padx=(26, 0))
        self.remplir(); self.maj_apercu()

    def remplir(self):
        from design import THEMES_CAT_LIB
        cont = self.liste.interieur
        for w in cont.winfo_children(): w.destroy()
        cats = {}
        for nom, t in THEMES.items(): cats.setdefault(t.get("type", "CLASSIQUE"), []).append(nom)
        nb_perso = len(cats.get("PERSO", []))
        try: larg = self.winfo_toplevel().winfo_width()
        except Exception: larg = 1200
        if larg < 300: larg = 1200
        nc = max(1, min(3, int((larg - 120 - 350 - 30) // 218)))
        for cat in ORDRE_CATEGORIES:
            noms = cats.get(cat, [])
            if not noms and cat != "PERSO": continue
            etiquette(cont, design.espacer(THEMES_CAT_LIB.get(cat, cat)), "texte", 12, P["texte2"], True).pack(anchor="w", pady=(10, 8))
            g = tk.Frame(cont, bg=P["fond"]); g.pack(anchor="w")
            items = list(noms)
            for k, nom in enumerate(items):
                CarteTheme(g, nom, THEMES[nom], self.choisir, choisi=(nom == self.choix), actuel=(nom == self.controller.current_theme_name),
                           on_suppr=self.supprimer if cat == "PERSO" else None).grid(row=k // nc, column=k % nc, padx=(0, 12), pady=(0, 12))
            if cat == "PERSO":
                k = len(items)
                c = tk.Canvas(g, width=206, height=108, bg=P["fond"], highlightthickness=0, cursor="hand2" if nb_perso < 4 else "")
                arrondi(c, 4, 4, 202, 104, 15, fill="", outline=P["bordure"], width=1.5, dash=(5, 4))
                c.create_text(103, 54, text="+ Créer mon thème" if nb_perso < 4 else "Limite de 4 thèmes perso", fill=P["texte2"], font=police("texte", 15, True))
                if nb_perso < 4: c.bind("<ButtonRelease-1>", lambda e: self.controller.show_custom_creator())
                c.grid(row=k // nc, column=k % nc, padx=(0, 12), pady=(0, 12))

    def choisir(self, nom):
        self.choix = nom; self.remplir(); self.maj_apercu()

    def maj_apercu(self):
        t = THEMES[self.choix]; pal = calculer_palette(t)
        nom = design.nom_theme(self.choix)
        self.lbl_apercu.config(text=design.espacer("Aperçu") + " · " + design.espacer(nom))
        c = self.can; c.delete("all")
        arrondi(c, 0, 0, 294, 330, 14, fill=pal["fond"], outline="")
        c.create_text(90, 30, text=design.espacer("Temps"), fill=pal["texte2"], font=police("texte", 11, True))
        c.create_text(90, 58, text="01:42", fill=pal["texte"], font=police("chiffres", 28))
        c.create_text(204, 30, text=design.espacer("Score"), fill=pal["texte2"], font=police("texte", 11, True))
        c.create_text(204, 58, text="2 450", fill=pal["mal"], font=police("chiffres", 28))
        dessiner_apercu(c, pal, 22, 96, 46, 7)
        actuel = self.choix == self.controller.current_theme_name
        self.btn_appliquer.set_text("Thème actuel ✓" if actuel else "Appliquer ce thème")
        self.btn_appliquer.set_variante("discret" if actuel else "principal"); self.btn_appliquer.actif = not actuel

    def appliquer(self):
        self.controller.apply_theme(self.choix); self.controller.show_skins()

    def supprimer(self, nom):
        if nom in THEMES:
            del THEMES[nom]
            if self.controller.current_theme_name == nom: self.controller.apply_theme(THEME_PAR_DEFAUT)
            self.controller.save_custom_themes_to_config(); self.controller.show_skins()


class PageCustomTheme(tk.Frame):
    PROPRIETES = [("bg", "Fond"), ("tuile", "Tuile"), ("accent1", "Bien placée"), ("accent2", "Mal placée"), ("muted", "Absente"),
                  ("btn1", "Bouton principal"), ("txt1", "Texte"), ("txt3", "Texte secondaire")]
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"])
        self.controller, self.selected_key = controller, "bg"
        self.current_custom = dict(THEMES[controller.current_theme_name])
        self.current_custom.setdefault("tuile", P["tuile"])
        for k in ("panel", "vide", "bordure"): self.current_custom.pop(k, None)  # recalculés à partir du fond
        self.current_custom["type"] = "PERSO"
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", controller.show_skins).pack(side="left")
        corps = tk.Frame(self, bg=P["fond"]); corps.pack(fill="both", expand=True, padx=90)
        etiquette(corps, "Créer mon thème", "titre", 46).pack(anchor="w", pady=(0, 20))
        ligne = tk.Frame(corps, bg=P["fond"]); ligne.pack(anchor="w")
        # Propriétés
        gauche = Panneau(ligne, padding=22, largeur=280); gauche.pack(side="left", anchor="n")
        gi = gauche.interieur; self.boxes = {}
        etiquette(gi, "Couleurs", "texte", 17, gras=True).pack(anchor="w", pady=(0, 10))
        for k, lbl in self.PROPRIETES:
            f = tk.Frame(gi, bg=P["panneau"], cursor="hand2"); f.pack(fill="x", pady=3)
            b = tk.Canvas(f, width=34, height=34, bg=P["panneau"], highlightthickness=0, cursor="hand2"); b.pack(side="left")
            l = etiquette(f, lbl, "texte", 15); l.pack(side="left", padx=10)
            for w in (f, b, l): w.bind("<Button-1>", lambda e, k=k: self.select_prop(k))
            self.boxes[k] = (b, l)
        # Aperçu
        centre = Panneau(ligne, padding=22, largeur=330); centre.pack(side="left", anchor="n", padx=24)
        etiquette(centre.interieur, design.espacer("Aperçu"), "texte", 12, P["texte2"], True).pack()
        self.can = tk.Canvas(centre.interieur, width=286, height=300, bg=P["panneau"], highlightthickness=0); self.can.pack(pady=(12, 0))
        # Nuancier
        droite = Panneau(ligne, padding=22); droite.pack(side="left", anchor="n")
        di = droite.interieur
        self.picker = ColorPickerWidget(di, self.update_color, P["panneau"]); self.picker.pack()
        etiquette(di, "Code hexadécimal", "texte", 13, P["texte2"]).pack(anchor="w", pady=(14, 4))
        self.hex_champ = Champ(di, largeur=240, hauteur=44, mono=True, taille=15); self.hex_champ.pack(anchor="w")
        self.hex_var = self.hex_champ.var; self.hex_var.trace_add("write", self.on_hex_edit)
        etiquette(di, "Nom du thème", "texte", 13, P["texte2"]).pack(anchor="w", pady=(14, 4))
        self.nom_champ = Champ(di, largeur=240, hauteur=44, taille=15); self.nom_champ.set("MON THÈME"); self.nom_champ.pack(anchor="w")
        self.name_entry = self.nom_champ.e
        bf = tk.Frame(corps, bg=P["fond"]); bf.pack(anchor="w", pady=24)
        Bouton(bf, "Enregistrer", self.save, largeur=200, hauteur=50).pack(side="left")
        Bouton(bf, "Annuler", controller.show_skins, largeur=160, hauteur=50, variante="discret").pack(side="left", padx=12)
        self.select_prop("bg")

    def select_prop(self, key):
        self.selected_key = key
        self.hex_var.set(self.current_custom.get(key, "#000000"))
        self._refresh()

    def on_hex_edit(self, *args):
        val = self.hex_var.get().strip()
        if len(val) == 7 and val.startswith('#'):
            try:
                self.winfo_rgb(val); self.update_color(val, from_entry=True)
            except tk.TclError: pass

    def update_color(self, hex_col, from_entry=False):
        self.current_custom[self.selected_key] = hex_col
        if not from_entry: self.hex_var.set(hex_col)
        self._refresh()

    def _refresh(self):
        for k, (b, l) in self.boxes.items():
            b.delete("all")
            arrondi(b, 2, 2, 32, 32, 8, fill=self.current_custom.get(k, "#000000"), outline=P["mal"] if k == self.selected_key else P["bordure"], width=2.5 if k == self.selected_key else 1)
            l.config(fg=P["texte"] if k == self.selected_key else P["texte2"])
        pal = calculer_palette(self.current_custom)
        c = self.can; c.delete("all")
        arrondi(c, 0, 0, 286, 300, 14, fill=pal["fond"], outline="")
        dessiner_apercu(c, pal, 18, 22, 44, 8)
        arrondi(c, 18, 242, 268, 284, 10, fill=pal["accent"], outline="")
        c.create_text(143, 263, text="Bouton principal", fill=pal["sur_accent"], font=police("texte", 14, True))

    def save(self):
        name = self.nom_champ.get().strip().upper()
        if name in THEMES and THEMES[name].get("type") != "PERSO":
            from tkinter import messagebox
            messagebox.showwarning("SMOUT", "Ce nom est déjà celui d'un thème intégré. Choisis-en un autre."); return
        if name:
            THEMES[name] = dict(self.current_custom)
            self.controller.save_custom_themes_to_config()
            self.controller.apply_theme(name)
            self.controller.show_skins()


class MenuPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SMOUT")
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1200, sw - 40), min(860, sh - 90)
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}"); self.minsize(min(980, w), min(640, h))
        self.config_dir = design.dossier_config()
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.current_theme_name = THEME_PAR_DEFAUT
        self.charger_themes_personnalises()
        self.apply_theme(self.charger_parametre_theme(), save=False)
        icon_path = resource_path(os.path.join('fichiers', 'logo.ico'))
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except Exception: pass
        self.container = tk.Frame(self, bg=P["fond"]); self.container.pack(fill="both", expand=True)
        self.creer_menu_accueil()

    # --- configuration ---
    def charger_themes_personnalises(self):
        for n, c in design.lire_config().get("custom_themes", {}).items():
            if n in THEMES and THEMES[n].get("type") != "PERSO": n = n + " PERSO"  # ne jamais écraser un thème intégré
            c["type"] = "PERSO"; THEMES[n] = c

    def save_custom_themes_to_config(self):
        design.maj_config(custom_themes={n: d for n, d in THEMES.items() if d.get("type") == "PERSO"})

    def charger_parametre_theme(self):
        t = design.lire_config().get("theme", THEME_PAR_DEFAUT)
        return t if t in THEMES else THEME_PAR_DEFAUT

    def apply_theme(self, theme_name, save=True):
        self.current_theme_name = theme_name
        theme_data = dict(THEMES[theme_name])
        design.appliquer_theme(theme_data)
        apply_theme_multi(theme_data); apply_theme_solo(theme_data)
        self.configure(bg=P["fond"])
        if hasattr(self, 'container'): self.container.configure(bg=P["fond"])
        if save: design.maj_config(theme=theme_name)

    def pseudo(self): return design.lire_config().get("pseudo", "") or "ANONYME"

    # --- écrans ---
    def vider(self):
        for widget in self.container.winfo_children(): widget.destroy()
        self.unbind("<Key>")

    def creer_menu_accueil(self):
        self.protocol("WM_DELETE_WINDOW", self.quitter_jeu)
        self.vider(); self.container.configure(bg=P["fond"])
        page = tk.Frame(self.container, bg=P["fond"]); page.pack(fill="both", expand=True)
        haut = tk.Frame(page, bg=P["fond"]); haut.pack(fill="x", padx=28, pady=(22, 0))
        self.avatar = Avatar(haut, self.pseudo(), 46, self.changer_pseudo); self.avatar.pack(side="right", padx=(10, 0))
        Icone(haut, "stats", self.ouvrir_stats).pack(side="right", padx=8)
        Icone(haut, "palette", self.show_skins).pack(side="right", padx=8)
        centre = tk.Frame(page, bg=P["fond"]); centre.place(relx=0.5, rely=0.5, anchor="center")
        Logo(centre, 88, 14).pack()
        etiquette(centre, "Trouvez le mot caché.", "texte", 19, P["texte2"]).pack(pady=(12, 30))
        h = 84 if self.winfo_height() < 200 or self.winfo_height() >= 820 else 72
        CarteMenu(centre, "Solo", "Normal, marathon, réglages", self.ouvrir_menu_solo, hauteur=h).pack(pady=6)
        serie, joue = design.serie_mot_du_jour()
        badge = (f"Série {serie}" if serie else "") + (" · Joué ✓" if joue else "") if (serie or joue) else None
        CarteMenu(centre, "Mot du jour", "Un mot, une partie par jour", lambda: self.ouvrir_solo(True), badge=badge.strip(" ·") if badge else None, hauteur=h).pack(pady=6)
        CarteMenu(centre, "Multijoueur", "Salons publics ou entre amis", self.ouvrir_multi, hauteur=h).pack(pady=6)
        etiquette(page, f"SMOUT v{design.VERSION_APP}", "texte", 14, P["texte2"]).pack(side="bottom", pady=22)

    def changer_pseudo(self):
        o = Superposition(self.container, largeur=460); i = o.interieur
        etiquette(i, "Ton pseudo", "titre", 28).pack(anchor="w")
        etiquette(i, "Il s'affiche pour les autres joueurs en multijoueur.", "texte", 15, P["texte2"]).pack(anchor="w", pady=(4, 16))
        ch = Champ(i, largeur=400, hauteur=52, mono=True, taille=19); ch.pack(anchor="w")
        ch.set(design.lire_config().get("pseudo", ""))
        def filtrer(*a):
            v = "".join(c for c in ch.get().upper() if c.isalnum())[:15]
            if v != ch.get(): ch.set(v)
        ch.var.trace_add("write", filtrer)
        def ok():
            if ch.get(): design.maj_config(pseudo=ch.get()); self.creer_menu_accueil()
            else: o.cacher()
        ch.bind_entree(ok)
        bf = tk.Frame(i, bg=i["bg"]); bf.pack(anchor="e", pady=(20, 0))
        Bouton(bf, "Annuler", o.cacher, largeur=130, variante="discret").pack(side="left", padx=10)
        Bouton(bf, "Enregistrer", ok, largeur=160).pack(side="left")
        o.montrer(); ch.focus()

    def show_skins(self):
        self.vider(); PageSkins(self.container, self).pack(fill="both", expand=True)

    def show_custom_creator(self):
        self.vider(); PageCustomTheme(self.container, self).pack(fill="both", expand=True)

    def ouvrir_parametres(self):
        self.vider(); PageParametres(self.container, self).pack(fill="both", expand=True)

    def ouvrir_solo(self, mdj=False):
        self.vider(); PageSolo(parent=self.container, controller=self, mdj=mdj).pack(fill="both", expand=True)

    def ouvrir_marathon(self):
        self.vider(); PageSolo(parent=self.container, controller=self, mode="marathon").pack(fill="both", expand=True)

    def ouvrir_menu_solo(self):
        self.vider(); PageMenuSolo(self.container, self).pack(fill="both", expand=True)

    def ouvrir_stats(self):
        self.vider(); PageStats(self.container, self).pack(fill="both", expand=True)

    def ouvrir_multi(self):
        self.vider(); PageMulti(parent=self.container, controller=self).pack(fill="both", expand=True)

    def quitter_jeu(self): self.quit(); self.destroy()

if __name__ == "__main__":
    app = MenuPrincipal(); app.mainloop()
