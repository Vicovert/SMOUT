import tkinter as tk
import os, sys, json, colorsys, threading, traceback
import design, compte, amis, classements
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

    def _restaurer_defilement(self, y):
        def faire():
            try: self.update_idletasks(); self.liste.canvas.yview_moveto(y)
            except tk.TclError: pass
        self.after(30, faire)

    def choisir(self, nom):
        y = self.liste.canvas.yview()[0]  # choisir un thème ne remonte pas la liste
        self.choix = nom; self.remplir(); self.maj_apercu(); self._restaurer_defilement(y)

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
        y = self.liste.canvas.yview()[0]
        self.controller.apply_theme(self.choix); self.controller.show_skins()
        self.controller.container.winfo_children()[0]._restaurer_defilement(y)

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
            design.informer(self, "Ce nom est déjà celui d'un thème intégré. Choisis-en un autre.", "Nom déjà pris"); return
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
        self.page_courante = None
        self.creer_menu_accueil()
        self.after(300, self.synchro_compte)
        self._multi = None; self.bandeau = None; self.after(1500, self.boucle_amis)  # 9.2 : amis (comptes seulement)

    # --- compte (même avancement sur tous les appareils) ---
    def synchro_compte(self):
        """Au démarrage : relit l'avancement du compte (en arrière-plan) ; s'il est plus récent, il remplace celui de cet appareil."""
        if not compte.email(): return
        def fil():
            if compte.tirer(): self.after(0, self.apres_synchro)
        threading.Thread(target=fil, daemon=True).start()

    def apres_synchro(self):
        """Nouvelles données du compte : thèmes, thème choisi et accueil mis à jour."""
        self.charger_themes_personnalises()
        self.apply_theme(self.charger_parametre_theme(), save=False)
        if self.page_courante == "accueil": self.creer_menu_accueil()

    # --- configuration ---
    def charger_themes_personnalises(self):
        for n, c in design.lire_config().get("custom_themes", {}).items():
            if n in THEMES and THEMES[n].get("type") != "PERSO": n = n + " PERSO"  # ne jamais écraser un thème intégré
            c = dict(THEMES.get(THEME_PAR_DEFAUT, {}), **c); c["type"] = "PERSO"; THEMES[n] = c  # clés manquantes : celles du thème par défaut

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

    def pseudo(self): return design.nettoyer_pseudo(design.lire_config().get("pseudo", "")).strip() or "ANONYME"

    # --- écrans ---
    def vider(self):
        self.page_courante = None
        for widget in self.container.winfo_children(): widget.destroy()
        self.unbind("<Key>")

    def creer_menu_accueil(self):
        self.protocol("WM_DELETE_WINDOW", self.quitter_jeu)
        self.vider(); self.container.configure(bg=P["fond"]); self.page_courante = "accueil"
        page = tk.Frame(self.container, bg=P["fond"]); page.pack(fill="both", expand=True)
        haut = tk.Frame(page, bg=P["fond"]); haut.pack(fill="x", padx=28, pady=(22, 0))
        etiquette(haut, f"v{design.VERSION_APP}", "texte", 14, P["texte2"]).pack(side="left")  # 9.9 : numéro de version en haut à gauche
        # 9.12 : ma série du mot du jour en pastille 🔥 posée sur l'avatar
        self.avatar = Avatar(haut, self.pseudo(), 46, self.changer_pseudo, serie=design.serie_mot_du_jour()[0]); self.avatar.pack(side="right", padx=(10, 0))
        Icone(haut, "stats", self.ouvrir_stats).pack(side="right", padx=8)
        Icone(haut, "palette", self.show_skins).pack(side="right", padx=8)
        self.bouton_amis(haut).pack(side="right", padx=8)
        centre = tk.Frame(page, bg=P["fond"])
        centre.place(relx=0.5, rely=0.53, anchor="center")
        lc = 390
        Logo(centre, 88, 14).pack()
        etiquette(centre, "Trouvez le mot caché.", "texte", 19, P["texte2"]).pack(pady=(12, 30))
        h = 84 if self.winfo_height() < 200 or self.winfo_height() >= 820 else 72
        # Solo et Multijoueur côte à côte, chacun de sa couleur ; le Mot du jour, à part, dessous, d'une troisième couleur
        ligne = tk.Frame(centre, bg=P["fond"]); ligne.pack()
        CarteMenu(ligne, "Solo", "Normal, marathon, réglages", self.ouvrir_menu_solo, largeur=lc, hauteur=h + 30, couleur=P["bien"], texte=P["sur_bien"]).pack(side="left", padx=(0, 16))
        CarteMenu(ligne, "Multijoueur", "Salons publics ou entre amis", self.ouvrir_multi, largeur=lc, hauteur=h + 30, couleur=P["mal"], texte=P["sur_mal"]).pack(side="left")
        serie, joue = design.serie_mot_du_jour()
        badge = (f"Série {serie}" if serie else "") + (" · Joué ✓" if joue else "") if (serie or joue) else None
        CarteMenu(centre, "Mot du jour", "Un mot, une partie par jour", lambda: self.ouvrir_solo(True), largeur=2 * lc + 16, hauteur=h, badge=badge.strip(" ·") if badge else None,
                  couleur="#4CC9F0", texte="#14182A").pack(pady=(26, 0))  # couleur propre au Mot du jour (comme .carte-menu.mdj du web)
        classements.PanneauClassement(centre, "mdj", largeur=440, on_fiche=self.fiche_joueur).pack(pady=(22, 0))  # 9.9 : sous les cartes, centré
        if not getattr(self, "maj_lancee", False): self.maj_lancee = True; self.verifier_maj()
        self.after(300, self.proposer_maj)

    def changer_pseudo(self):
        o = Superposition(self.container, largeur=460); i = o.interieur; self.fen_pseudo = o
        def fermer(): o.cacher(); self.creer_menu_accueil()
        tt = tk.Frame(i, bg=i["bg"]); tt.pack(fill="x")
        etiquette(tt, "Ton pseudo", "titre", 28).pack(side="left")
        Icone(tt, "fermer", fermer, 36).pack(side="right")  # 9.4 : une croix plutôt que « Annuler »
        etiquette(i, "Il s'affiche pour les autres joueurs en multijoueur.", "texte", 15, P["texte2"]).pack(anchor="w", pady=(4, 16))
        ch = Champ(i, largeur=400, hauteur=52, mono=True, taille=19); ch.pack(anchor="w")
        ch.set(design.nettoyer_pseudo(design.lire_config().get("pseudo", "")))
        enreg = etiquette(i, "", "texte", 13, P["texte2"]); enreg.pack(anchor="w", pady=(6, 0))
        def filtrer(*a):  # 9.4 : enregistré tout seul à chaque modification (pas de bouton « Enregistrer »)
            v = design.nettoyer_pseudo(ch.get())
            if v != ch.get(): ch.set(v)  # (Tk ne relance pas la trace pendant son propre rappel)
            if v.strip(): design.maj_config(pseudo=v.strip()); enreg.config(text="Enregistré ✓")
        ch.var.trace_add("write", filtrer)
        ch.bind_entree(fermer)
        # compte : retrouver son avancement sur tous ses appareils
        tk.Frame(i, bg=P["bordure"], height=1, width=400).pack(anchor="w", pady=(22, 14))
        cfg = design.lire_config(); em = cfg.get("compte_email")
        etiquette(i, "Compte", "texte", 17, gras=True).pack(anchor="w")
        if em:
            etiquette(i, f"Connecté : {em}", "texte", 15).pack(anchor="w", pady=(4, 0))
            etiquette(i, "Ton avancement est enregistré sur ce compte et suit sur tous tes appareils.", "texte", 13, P["texte2"], wraplength=400, justify="left").pack(anchor="w", pady=(2, 12))
            def sortir():
                if design.confirmer(self, "Se déconnecter ?", "Tu quittes le compte sur cet appareil. Ton avancement reste enregistré sur le compte.", "Se déconnecter"):
                    compte.deconnecter(); o.cacher(); self.creer_menu_accueil()
            Bouton(i, "Se déconnecter", sortir, largeur=200, hauteur=42, variante="discret").pack(anchor="w")
        else:
            if cfg.get("compte_expire"):
                etiquette(i, "Ta session a expiré : reconnecte-toi.", "texte", 14, P["danger"], True).pack(anchor="w", pady=(4, 0))
            etiquette(i, "Crée un compte pour retrouver ton avancement (statistiques, série, thèmes, partie en cours) sur tous tes appareils.", "texte", 13, P["texte2"], wraplength=400, justify="left").pack(anchor="w", pady=(4, 12))
            Bouton(i, "Se connecter ou créer un compte", lambda: (o.cacher(), self.ouvrir_compte()), largeur=300, hauteur=44, variante="secondaire").pack(anchor="w")
        o.montrer()  # 9.4 : pas de focus automatique

    def ouvrir_compte(self):
        """Connexion à un compte existant, création d'un compte (le joueur de cet appareil y est rattaché) ou mot de passe oublié."""
        o = Superposition(self.container, largeur=480); i = o.interieur
        etiquette(i, "Mon compte", "titre", 28).pack(anchor="w")
        etiquette(i, "Le même compte sur ton PC, ton téléphone et le site : tu retrouves partout ton avancement.", "texte", 14, P["texte2"], wraplength=420, justify="left").pack(anchor="w", pady=(4, 14))
        etiquette(i, "E-mail", "texte", 14, P["texte2"], True).pack(anchor="w")
        ch_mail = Champ(i, largeur=420, hauteur=48, taille=16); ch_mail.pack(anchor="w", pady=(2, 10))
        etiquette(i, "Mot de passe (6 caractères minimum)", "texte", 14, P["texte2"], True).pack(anchor="w")
        ch_mdp = Champ(i, largeur=420, hauteur=48, taille=16, masque=True); ch_mdp.pack(anchor="w", pady=(2, 6))
        msg = etiquette(i, "", "texte", 14, P["danger"], True, wraplength=420, justify="left"); msg.pack(anchor="w", pady=(4, 0))
        oubli = etiquette(i, "Mot de passe oublié ?", "texte", 14, P["texte2"], cursor="hand2"); oubli.pack(anchor="w", pady=(6, 0))
        self.fen_compte = (o, ch_mail, ch_mdp, msg)
        def agir(action):
            msg.config(text="Connexion…", fg=P["texte2"]); i.update_idletasks()
            err = action(ch_mail.get(), ch_mdp.get())
            if err: msg.config(text=err, fg=P["danger"]); return
            o.cacher(); self.apres_synchro(); self.creer_menu_accueil()
        def oublie(e=None):
            if "@" not in ch_mail.get(): msg.config(text="Entre d'abord ton adresse e-mail.", fg=P["danger"]); return
            err = compte.reinitialiser(ch_mail.get())
            msg.config(text=err or f"Un e-mail pour choisir un nouveau mot de passe a été envoyé à {ch_mail.get().strip()}.", fg=P["danger"] if err else P["succes"])
        oubli.bind("<Button-1>", oublie)
        ch_mdp.bind_entree(lambda: agir(compte.connecter))
        bf = tk.Frame(i, bg=i["bg"]); bf.pack(anchor="e", pady=(18, 0))
        Bouton(bf, "Annuler", o.cacher, largeur=100, variante="discret").pack(side="left", padx=(0, 8))
        Bouton(bf, "Créer le compte", lambda: agir(compte.creer), largeur=150, variante="secondaire").pack(side="left", padx=(0, 8))
        Bouton(bf, "Se connecter", lambda: agir(compte.connecter), largeur=146).pack(side="left")
        o.montrer(); ch_mail.focus()

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
        self.vider(); self._multi = PageMulti(parent=self.container, controller=self); self._multi.pack(fill="both", expand=True)
        return self._multi

    # --- amis (9.2 ; même logique que l'objet Amis du site) ---
    def fiche_joueur(self, uid): return classements.fiche_joueur(self, uid)

    def bouton_amis(self, parent):
        """Icône Amis avec pastille du nombre de demandes reçues."""
        f = tk.Frame(parent, bg=P["fond"])
        Icone(f, "amis", self.ecran_amis).pack()
        n = len(amis.E["demandes"]) if compte.email() else 0
        if n: tk.Label(f, text=str(n), bg=P["danger"], fg="#ffffff", font=police("texte", 10, True), padx=4).place(relx=1.0, rely=0.0, anchor="ne")
        return f

    def salon_actuel(self):
        m = self._multi
        try: return m.lobby_code if (m is not None and m.winfo_exists()) else ""
        except Exception: return ""

    def en_partie(self):
        m = self._multi
        try: return bool(m is not None and m.winfo_exists() and m.frames["PageJeu"].active_sync and m.frames["PageJeu"].winfo_ismapped())
        except Exception: return False

    def boucle_amis(self):
        """Toutes les 10 s : signe de vie, demandes et invitations (dans un fil), puis bandeau."""
        salon, fini = self.salon_actuel(), threading.Event()
        def fil():
            try:
                amis.tic(salon)
                if compte.email() and amis.E["n"] % 3 == 1: classements.pousser()  # 9.4 : seulement si les valeurs ont changé
            except Exception: traceback.print_exc()
            fini.set()
        def attendre_fin():  # le bandeau se met à jour dans le fil de l'interface
            if fini.is_set(): self.maj_bandeau()
            else: self.after(150, attendre_fin)
        threading.Thread(target=fil, daemon=True).start(); self.after(150, attendre_fin)
        self.after(10000, self.boucle_amis)

    def maj_bandeau(self):
        """Bandeau en haut de tous les écrans (sauf en pleine partie) : invitation ou demande d'ami."""
        def fermer():
            if self.bandeau is not None:
                try: self.bandeau.destroy()
                except Exception: pass
            self.bandeau = None
        if self.en_partie() or not compte.email(): return fermer()
        E = amis.E
        inv = next(((c, v) for c, v in E["invitations"].items() if "i" + c not in E["vues"] and c != self.salon_actuel()), None)
        dem = None if inv else next(((u, v) for u, v in E["demandes"].items() if "d" + u not in E["vues"]), None)
        if not inv and not dem: return fermer()
        cle = "i" + inv[0] if inv else "d" + dem[0]
        if self.bandeau is not None and getattr(self.bandeau, "cle", None) == cle: return
        fermer()
        nom = str((inv or dem)[1].get("pseudo", "?")).capitalize()
        b = Panneau(self, padding=12, rayon=14, contour=P["mal"], largeur=560); b.cle = cle; i = b.interieur
        Avatar(i, nom, 34, index=1).pack(side="left")
        etiquette(i, f"{nom} t'invite dans son salon" if inv else f"{nom} veut être ton ami", "texte", 15, P["texte"], True).pack(side="left", padx=12)
        def oui():
            E["vues"].add(cle); fermer()
            if inv: self.rejoindre_invitation(inv[0])
            else: self.ecran_amis()
        def non():
            E["vues"].add(cle); fermer()
            if inv: threading.Thread(target=lambda: amis.effacer_invitation(inv[0]), daemon=True).start()
            self.maj_bandeau()
        Bouton(i, "Ignorer", non, largeur=96, hauteur=38, variante="discret", taille=13).pack(side="right")
        Bouton(i, "Rejoindre" if inv else "Voir", oui, largeur=110, hauteur=38, taille=13).pack(side="right", padx=(0, 8))
        b.place(relx=0.5, y=10, anchor="n"); b.tk.call("raise", b._w); self.bandeau = b  # (Panneau est un Canvas : lift() y monte un dessin)

    def rejoindre_invitation(self, code):
        """Sans taper le code ; mot de passe demandé si le salon en a un ; partie en cours → spectateur directement."""
        import page_multi as pm
        idx = amis.lire(f"index/{code}")
        if not idx or amis.maintenant_ms() - (idx.get("maj") or 0) > 30000:
            amis.effacer_invitation(code); design.informer(self, "Ce salon n'existe plus.", "Salon fermé"); return
        if idx.get("version") != pm.VERSION_JEU:
            design.informer(self, f"Ce salon utilise une autre version du jeu ({idx.get('version', '?')}). Mets SMOUT à jour.", "Autre version"); return
        m = self.ouvrir_multi(); self.update_idletasks()
        if not m.player_id and not m.assurer_connexion(): design.informer(self, "Connexion au serveur impossible.", "Pas de connexion"); return
        pr = m.frames["PageRejoindre"]
        while True:
            mdp = ""
            if idx.get("prive"):
                mdp = design.demander_texte(self, "Salon protégé", f"Entre le mot de passe du salon {code}.")
                if mdp is None: return
            preuve = pm.preuve_salon(code, mdp)
            ok = pr.entrer_spectateur(code, mdp, preuve, True) if idx.get("status") == "playing" else pr.rejoindre(code, mdp, silencieux=True)
            if ok: threading.Thread(target=lambda: amis.effacer_invitation(code), daemon=True).start(); return
            if not idx.get("prive"): design.informer(self, "Impossible de rejoindre ce salon.", "Salon"); return
            design.informer(self, "Mot de passe incorrect.", "Salon protégé")

    def ecran_amis(self, retour=None):
        """Écran Amis : mon code, ajouter par code, demandes reçues, liste avec statut (comme ecranAmis du site)."""
        retour = retour or self.creer_menu_accueil
        self.vider(); self.page_courante = "amis"
        page = tk.Frame(self.container, bg=P["fond"]); page.pack(fill="both", expand=True); self.page_amis = page
        h = tk.Frame(page, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", retour).pack(side="left")
        etiquette(h, "Amis", "texte", 18, P["texte"], True).pack(side="top", pady=8)
        if not compte.email():
            p = Panneau(page, padding=26, largeur=520); p.pack(pady=30)
            etiquette(p.interieur, "Crée un compte pour avoir des amis", "titre", 24).pack()
            etiquette(p.interieur, "Les amis suivent ton compte : tu les retrouves sur tous tes appareils.", "texte", 14, P["texte2"], wraplength=460, justify="center").pack(pady=(8, 18))
            Bouton(p.interieur, "Se connecter ou créer un compte", self.ouvrir_compte, largeur=320).pack()
            return
        zone = Defilant(page, hauteur=600); zone.pack(fill="both", expand=True, pady=(6, 0))
        c = tk.Frame(zone.interieur, bg=P["fond"]); c.pack(pady=(4, 30))
        pc = Panneau(c, padding=16, rayon=14, contour=P["mal"], largeur=640); pc.pack()
        etiquette(pc.interieur, design.espacer("Mon code ami"), "texte", 11, P["texte2"], True).pack(anchor="w")
        self.lbl_code_ami = etiquette(pc.interieur, amis.E["code"] or "······", "chiffres", 30, P["mal"]); self.lbl_code_ami.pack(anchor="w")
        etiquette(pc.interieur, "Donne-le pour ajouter des amis.", "texte", 13, P["texte2"]).pack(anchor="w")
        def section(t): etiquette(c, design.espacer(t), "texte", 11, P["texte2"], True).pack(anchor="w", pady=(20, 6))
        section("Ajouter un ami")
        la = tk.Frame(c, bg=P["fond"]); la.pack(anchor="w")
        self.champ_ami = Champ(la, largeur=500, hauteur=48, mono=True, taille=16); self.champ_ami.pack(side="left")
        self.msg_amis = etiquette(c, "", "texte", 14, P["danger"], True); self.msg_amis.pack(anchor="w", pady=(6, 0))
        def ajouter():
            err = amis.ajouter(self.champ_ami.get())
            if err: self.msg_amis.config(text=err, fg=P["danger"])
            else: self.msg_amis.config(text="Demande envoyée ✓", fg=P["succes"]); self.champ_ami.set(""); dessiner()
        Bouton(la, "Ajouter", ajouter, largeur=120, hauteur=48).pack(side="left", padx=(10, 0)); self.champ_ami.bind_entree(ajouter)
        self.zone_dem, self.zone_liste = tk.Frame(c, bg=P["fond"]), tk.Frame(c, bg=P["fond"])
        self.zone_dem.pack(anchor="w", fill="x"); self.zone_liste.pack(anchor="w", fill="x")
        def ligne(parent, nom, i, st, etat, actions, uid=None):
            p = Panneau(parent, padding=10, rayon=12, couleur=P["tuile"], largeur=640); p.pack(pady=3, anchor="w")
            if uid: p.interieur.bind("<Button-1>", lambda e, u=uid: self.fiche_joueur(u)); p.interieur.config(cursor="hand2")
            Avatar(p.interieur, nom, 36, index=i).pack(side="left")
            t = tk.Frame(p.interieur, bg=P["tuile"]); t.pack(side="left", padx=12)
            etiquette(t, str(nom).capitalize(), "texte", 16, P["texte"], True).pack(anchor="w")
            coul = {"on": P["succes"], "jeu": P["mal"]}.get(etat, P["texte_absent"])
            etiquette(t, "● " + st, "texte", 13, coul).pack(anchor="w")
            for txt, f, var in reversed(actions): Bouton(p.interieur, txt, f, largeur=max(96, 20 + len(txt) * 9), hauteur=36, variante=var, taille=13).pack(side="right", padx=(8, 0))
        def dessiner():
            if not compte.email(): return
            if not amis.E["code"] or amis.E["uid_code"] != amis.uid(): amis.assurer_profil(self.salon_actuel())
            amis.charger()
            try:
                if not page.winfo_exists(): return
            except Exception: return
            self.lbl_code_ami.config(text=amis.E["code"] or "······")
            for w in self.zone_dem.winfo_children() + self.zone_liste.winfo_children(): w.destroy()
            dem = list(amis.E["demandes"].items())
            if dem:
                etiquette(self.zone_dem, design.espacer(f"Demandes reçues ({len(dem)})"), "texte", 11, P["texte2"], True).pack(anchor="w", pady=(20, 6))
                for k, (u, v) in enumerate(dem):
                    ligne(self.zone_dem, v.get("pseudo", "?"), k + 2, "veut être ton ami", "off",
                          [("Accepter", lambda u=u: (amis.accepter(u), dessiner()), "principal"), ("Refuser", lambda u=u: (amis.refuser(u), dessiner()), "discret")])
            ids = amis.amis_tries()
            etiquette(self.zone_liste, design.espacer(f"Mes amis ({len(ids)})"), "texte", 11, P["texte2"], True).pack(anchor="w", pady=(20, 6))
            if not ids: etiquette(self.zone_liste, "Pas encore d'amis : donne ton code ou entre le leur.", "texte", 14, P["texte2"]).pack(anchor="w")
            salon = self.salon_actuel()
            for k, u in enumerate(ids):
                p = amis.E["profils"].get(u) or {}; st, etat, _ = amis.statut(p)
                if etat == "jeu": act = [("Rejoindre", lambda s=p.get("salon"): self.rejoindre_salon_ami(s), "discret")]
                elif salon and etat == "on": act = [("Inviter", lambda u=u: amis.inviter(u, salon), "principal")]
                else:
                    def retirer(u=u, n=p.get("pseudo", "?")):
                        if design.confirmer(self, "Retirer cet ami ?", f"{str(n).capitalize()} ne sera plus dans ta liste (et toi plus dans la sienne).", "Retirer"): amis.retirer(u); dessiner()
                    act = [("Retirer", retirer, "discret")]
                ligne(self.zone_liste, p.get("pseudo", "?"), k, st, etat, act, uid=u)
        self.dessiner_amis = dessiner
        dessiner()
        def rafraichir():
            try:
                if page.winfo_exists() and self.page_courante == "amis": dessiner(); self.after(8000, rafraichir)
            except Exception: pass
        self.after(8000, rafraichir)

    def rejoindre_salon_ami(self, code):
        """Salon d'un ami : comme avec le code (demande à l'hôte si la partie a commencé)."""
        if not code: return
        import page_multi as pm
        idx = amis.lire(f"index/{code}") or {}
        mdp = ""
        if idx.get("prive"):
            mdp = design.demander_texte(self, "Salon protégé", f"Entre le mot de passe du salon {code}.")
            if mdp is None: return
        m = self.ouvrir_multi(); self.update_idletasks()
        if not m.player_id and not m.assurer_connexion(): return
        if not m.frames["PageRejoindre"].rejoindre(code, mdp, silencieux=True):
            design.informer(self, "Mot de passe incorrect." if idx.get("prive") else "Impossible de rejoindre ce salon.", "Salon")

    # ---------------------------------------------------------------- 9.5 : version obsolète
    URL_DERNIERE = "https://api.github.com/repos/Vicovert/SMOUT/releases/latest"

    def verifier_maj(self):
        """Au lancement (version Windows seulement) : la dernière release est-elle plus récente ? Lecture dans un fil."""
        if not getattr(sys, "frozen", False) and not os.environ.get("SMOUT_MAJ_TEST"): return
        res, fini = {}, threading.Event()
        def fil():
            try:
                import requests
                j = requests.get(os.environ.get("SMOUT_MAJ_TEST") or self.URL_DERNIERE, timeout=8, headers={"Accept": "application/vnd.github+json"}).json()
                a = next(a for a in j.get("assets", []) if a.get("name", "").lower().endswith(".exe"))
                res.update(version=str(j["tag_name"]).lstrip("vV"), url=a["browser_download_url"], nom=a["name"], page=j.get("html_url", ""))
            except Exception: pass
            fini.set()
        def attendre():
            if not fini.is_set(): self.after(300, attendre); return
            if res and design.version_plus_recente(res["version"], design.VERSION_APP): self.maj_dispo = res; self.proposer_maj()
        threading.Thread(target=fil, daemon=True).start(); self.after(300, attendre)

    def proposer_maj(self):
        """Seulement sur l'accueil (jamais en pleine partie), une fois par lancement."""
        m = getattr(self, "maj_dispo", None)
        if not m or getattr(self, "maj_montree", False) or self.page_courante != "accueil": return
        self.maj_montree = True
        if design.dialogue(self, "Version obsolète", f"La version {m['version']} est disponible (tu as la {design.VERSION_APP}).",
                           [("Plus tard", False, "discret"), ("Mettre à jour", True, "principal")]): self.charger_maj()

    def charger_maj(self):
        """Télécharge SMOUT.X.Y.exe à côté de l'actuel, le lance et ferme celui-ci."""
        m = self.maj_dispo
        if not getattr(sys, "frozen", False) and not os.environ.get("SMOUT_MAJ_TEST"):
            import webbrowser; webbrowser.open(m["page"]); return
        dossier = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.environ.get("SMOUT_MAJ_DOSSIER", ".")
        dest = os.path.join(dossier, m["nom"])
        o = Superposition(self.container, largeur=460); i = o.interieur
        etiquette(i, "Mise à jour", "titre", 25).pack(anchor="w")
        txt = etiquette(i, "Téléchargement… 0 %", "texte", 15, P["texte2"]); txt.pack(anchor="w", pady=(8, 4))
        o.montrer(); o.dialogue = True
        etat = {"pc": 0, "fini": False, "erreur": None}
        def fil():
            try:
                import requests
                with requests.get(m["url"], stream=True, timeout=30) as r:
                    r.raise_for_status(); total = int(r.headers.get("content-length") or 0); lu = 0
                    with open(dest + ".part", "wb") as f:
                        for bloc in r.iter_content(256 * 1024):
                            f.write(bloc); lu += len(bloc)
                            if total: etat["pc"] = int(lu * 100 / total)
                os.replace(dest + ".part", dest)
            except Exception as e: etat["erreur"] = str(e) or "erreur"
            etat["fini"] = True
        def suivre():
            if not etat["fini"]: txt.config(text=f"Téléchargement… {etat['pc']} %"); self.after(200, suivre); return
            if etat["erreur"]:
                txt.config(text="Le téléchargement a échoué. Réessaie plus tard ou télécharge la nouvelle version sur la page des versions.")
                txt.config(wraplength=390, justify="left")
                bf = tk.Frame(i, bg=i["bg"]); bf.pack(anchor="e", pady=(14, 0))
                Bouton(bf, "Fermer", o.cacher, largeur=120, hauteur=44, variante="discret", taille=14).pack(side="left", padx=(0, 10))
                import webbrowser
                Bouton(bf, "Ouvrir la page", lambda: (webbrowser.open(m["page"]), o.cacher()), largeur=170, hauteur=44, taille=14).pack(side="left")
                return
            txt.config(text="Lancement de la nouvelle version…"); self.update_idletasks()
            try:
                import subprocess
                # nouveau programme indépendant : sans les variables du dossier temporaire de celui-ci (PyInstaller)
                tmp = getattr(sys, "_MEIPASS", None)
                env = {k: v for k, v in os.environ.items() if not k.startswith(("_MEI", "_PYI")) and not (tmp and tmp in v)}
                env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
                drapeaux = 0x00000008 | 0x00000200 if os.name == "nt" else 0  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                if not os.environ.get("SMOUT_MAJ_TEST"): subprocess.Popen([dest], cwd=dossier, env=env, creationflags=drapeaux, close_fds=True)
                self.maj_lancee_fichier = dest
            except Exception as e:
                txt.config(text=f"Impossible de lancer {m['nom']} : ouvre-le toi-même (dossier {dossier})."); return
            self.after(400, self.quitter_jeu)
        threading.Thread(target=fil, daemon=True).start(); self.after(200, suivre)

    def quitter_jeu(self): self.quit(); self.destroy()

if __name__ == "__main__":
    app = MenuPrincipal(); app.mainloop()
