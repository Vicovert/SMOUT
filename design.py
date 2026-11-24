"""Kit visuel « Plateau de nuit » de SMOUT 6 : polices, palette dérivée du thème et composants Tkinter."""
import tkinter as tk
import tkinter.font as tkfont
import os, sys, ctypes, colorsys, hashlib

# Tk appelle parfois une liaison (<Leave>, <ButtonRelease-1>, <Configure>…) sans aucun événement quand une fenêtre sous le pointeur est détruite et recréée :
# le rappel plante alors (« missing 1 required positional argument: 'e' »). Un vrai événement a toujours ses arguments : on ignore ces appels parasites.
_appel_tk = tk.CallWrapper.__call__
def _appel_tk_sur(self, *args):
    if self.subst and not args: return
    return _appel_tk(self, *args)
tk.CallWrapper.__call__ = _appel_tk_sur

VERSION_APP = "9.0"
URL_WEB = "https://vicovert.github.io/SMOUT/"

def mot_graine(liste_triee, graine, index=0):
    """Mot choisi de façon déterministe : identique sur PC et sur le web (même calcul SHA-256)."""
    h = hashlib.sha256(f"{graine}:{index}".encode("utf-8")).hexdigest()[:12]
    return liste_triee[int(h, 16) % len(liste_triee)]

# ---------------------------------------------------------------- utilitaires
def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*[max(0, min(255, int(round(c)))) for c in rgb])

def melanger(a, b, t):
    """Mélange la couleur a vers b (t = 0 → a, t = 1 → b)."""
    try:
        ra, rb = hex_rgb(a), hex_rgb(b)
        return rgb_hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])
    except Exception:
        return a

def luminance(h):
    try:
        r, g, b = hex_rgb(h)
        return (0.299 * r + 0.587 * g + 0.114 * b) / 255
    except Exception:
        return 0

def contraste(h, clair="#ffffff", fonce="#16130a"):
    return fonce if luminance(h) > 0.6 else clair

def eclaircir(h, f):
    """f > 1 éclaircit, f < 1 assombrit (en gardant la teinte)."""
    try:
        r, g, b = [c / 255 for c in hex_rgb(h)]
        hh, l, s = colorsys.rgb_to_hls(r, g, b)
        l = max(0, min(1, l * f if f < 1 else l + (1 - l) * (f - 1)))
        return rgb_hex([c * 255 for c in colorsys.hls_to_rgb(hh, l, s)])
    except Exception:
        return h

# ---------------------------------------------------------------- polices
POLICES_CHARGEES = False
FAMILLES = {"titre": "SMOUT Titre", "chiffres": "SMOUT Chiffres", "texte": "SMOUT Texte"}
REPLIS = {
    "win32": {"titre": "Segoe UI Black", "chiffres": "Consolas", "texte": "Segoe UI"},
    "darwin": {"titre": "Helvetica Neue", "chiffres": "Menlo", "texte": "Helvetica Neue"},
    "linux": {"titre": "DejaVu Sans", "chiffres": "DejaVu Sans Mono", "texte": "DejaVu Sans"},
}

def charger_polices():
    """Rend les polices du jeu disponibles pour ce processus uniquement (rien n'est installé sur l'ordinateur)."""
    global POLICES_CHARGEES
    dossier = resource_path(os.path.join("fichiers", "polices"))
    if not os.path.isdir(dossier): return
    fichiers = [os.path.join(dossier, f) for f in os.listdir(dossier) if f.lower().endswith(".ttf")]
    try:
        if sys.platform == "win32":
            for f in fichiers: ctypes.windll.gdi32.AddFontResourceExW(f, 0x10, 0)  # FR_PRIVATE
        elif sys.platform == "darwin":
            cf = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
            ct = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreText.framework/CoreText")
            cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
            cf.CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool]
            ct.CTFontManagerRegisterFontsForURL.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
            for f in fichiers:
                b = f.encode("utf-8")
                url = cf.CFURLCreateFromFileSystemRepresentation(None, b, len(b), False)
                ct.CTFontManagerRegisterFontsForURL(url, 1, None)  # kCTFontManagerScopeProcess
        else:
            fc = ctypes.CDLL("libfontconfig.so.1")
            fc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            for f in fichiers: fc.FcConfigAppFontAddFile(None, f.encode("utf-8"))
        POLICES_CHARGEES = True
    except Exception:
        POLICES_CHARGEES = False

_familles_dispo = None
def police(role, taille, gras=None):
    """role : 'titre' (titres), 'chiffres' (lettres et nombres), 'texte'. taille en pixels."""
    global _familles_dispo
    if _familles_dispo is None:
        try: _familles_dispo = set(tkfont.families())
        except Exception: _familles_dispo = set()
    fam = FAMILLES[role]
    if fam not in _familles_dispo:
        cle = "win32" if sys.platform == "win32" else "darwin" if sys.platform == "darwin" else "linux"
        fam = REPLIS[cle][role]
    if gras is None: gras = role in ("titre", "chiffres")
    return (fam, -abs(int(taille)), "bold") if gras else (fam, -abs(int(taille)))

def espacer(texte):
    """Petites capitales espacées (TEMPS, SCORE...)."""
    return " ".join(texte.upper())

# ---------------------------------------------------------------- palette
P = {}

def calculer_palette(t):
    fond = t["bg"]
    texte = t.get("txt1", "#EAF0FF")
    if abs(luminance(texte) - luminance(fond)) < 0.35:
        texte = "#EAF0FF" if luminance(fond) < 0.5 else "#1b1a22"
    sombre = luminance(fond) < 0.5
    p = {
        "fond": fond, "texte": texte,
        "panneau": t.get("panel") or melanger(fond, texte, 0.06),
        "tuile": t.get("tuile") or melanger(fond, texte, 0.12),
        "vide": t.get("vide") or melanger(fond, texte, 0.035),
        "bordure": t.get("bordure") or melanger(fond, texte, 0.24),
        "bien": t["accent1"], "mal": t["accent2"],
        "absent": t.get("muted") or melanger(fond, texte, 0.06),
        "accent": t.get("btn1") or t["accent2"],
    }
    t2 = t.get("txt3")
    p["texte2"] = t2 if t2 and abs(luminance(t2) - luminance(fond)) > 0.25 else melanger(texte, fond, 0.35)
    if abs(luminance(p["absent"]) - luminance(fond)) > 0.35:  # thèmes où la lettre absente est très voyante
        p["absent"] = melanger(fond, texte, 0.07)
    p["texte_absent"] = melanger(p["absent"], texte, 0.38)
    p["sur_accent"] = contraste(p["accent"]); p["sur_bien"] = contraste(p["bien"]); p["sur_mal"] = contraste(p["mal"])
    p["danger"] = "#F28B8B" if sombre else "#B42318"
    p["succes"] = "#4ADE80" if sombre else "#15803D"
    p["ombre_bien"] = eclaircir(p["bien"], 0.72); p["ombre_mal"] = eclaircir(p["mal"], 0.72)
    p["survol"] = melanger(p["panneau"], texte, 0.06)
    p["sombre"] = sombre
    return p

PALETTE_DALTONIEN = ("#F5793A", "#85C0F9")  # orange = bien placée, bleu = mal placée (lisible par tous les daltonismes courants)

def appliquer_theme(t):
    if lire_config().get("daltonien"): t = dict(t, accent1=PALETTE_DALTONIEN[0], accent2=PALETTE_DALTONIEN[1])
    P.clear(); P.update(calculer_palette(t))
    return P

# ---------------------------------------------------------------- dessin
import math as _math

def arrondi(c, x1, y1, x2, y2, r, **kw):
    """Rectangle aux coins vraiment arrondis (rayon r)."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    p = []
    for cx, cy, debut in ((x2 - r, y1 + r, -90), (x2 - r, y2 - r, 0), (x1 + r, y2 - r, 90), (x1 + r, y1 + r, 180)):
        for i in range(9):
            a = _math.radians(debut + i * 90 / 8)
            p += [cx + r * _math.cos(a), cy + r * _math.sin(a)]
    return c.create_polygon(p, **kw)

def fond_parent(w):
    try: return w["bg"]
    except Exception: return P.get("fond", "#0B1226")

def etiquette(parent, texte, role="texte", taille=15, couleur=None, gras=None, **kw):
    return tk.Label(parent, text=texte, font=police(role, taille, gras), fg=couleur or P["texte"], bg=fond_parent(parent), **kw)

# ---------------------------------------------------------------- composants
class Tuile(tk.Canvas):
    """Case de la grille. Compatible avec l'ancien usage Label : config(text=, bg=, fg=) et cget()."""
    def __init__(self, parent, taille=48, rayon=None, mini=False):
        super().__init__(parent, width=taille, height=taille, bg=fond_parent(parent), highlightthickness=0, bd=0)
        self.taille, self.mini = taille, mini
        self.rayon = rayon if rayon is not None else max(3, int(taille * 0.18))
        self._texte, self._fond, self._fg, self._curseur = "", None, None, False
        self._pal = None  # palette d'un autre joueur (grilles adverses) ; None = thème de cet appareil
        self._dessiner()

    def set_palette(self, pal):
        if pal is not self._pal: self._pal = pal; self._dessiner()

    def configure(self, cnf=None, **kw):
        if cnf: kw.update(cnf)
        change = False
        for k, attr in (("text", "_texte"), ("bg", "_fond"), ("fg", "_fg")):
            if k in kw: setattr(self, attr, kw.pop(k)); change = True
        kw.pop("font", None)
        if kw: super().configure(**kw)
        if change: self._dessiner()
    config = configure

    def cget(self, key):
        if key == "text": return self._texte
        if key == "bg": return self._fond if self._fond is not None else P["fond"]
        if key == "fg": return self._fg or P["texte"]
        return super().cget(key)

    def set_curseur(self, actif):
        if actif != self._curseur: self._curseur = actif; self._dessiner()

    def set_pointilles(self, actif):
        if actif != getattr(self, "pointilles", False): self.pointilles = actif; self._dessiner()

    def set_taille(self, taille):
        if taille == self.taille: return
        self.taille = taille; self.rayon = max(3, int(taille * 0.18))
        super().configure(width=taille, height=taille); self._dessiner()

    def _style(self):
        f, txt, Q = self._fond, self._texte, (self._pal or P)
        if f == Q["bien"]: return Q["bien"], Q["sur_bien"], Q["ombre_bien"]
        if f == Q["mal"]: return Q["mal"], Q["sur_mal"], Q["ombre_mal"]
        if f == Q["absent"]: return Q["absent"], Q["texte_absent"], None
        if f in (None, Q["fond"], Q["vide"], Q["tuile"]):
            return (Q["tuile"], Q["texte"], None) if txt else (Q["vide"], Q["texte"], None)
        return f, contraste(f, Q["texte"] if not Q["sombre"] else "#ffffff"), None

    def _dessiner(self):
        self.delete("all")
        s, r = self.taille, self.rayon
        fill, fg, ombre = self._style()
        if ombre and not self.mini:
            arrondi(self, 1, 3, s - 1, s - 1, r, fill=ombre, outline="")
            arrondi(self, 1, 1, s - 1, s - 4, r, fill=fill, outline="")
        else:
            arrondi(self, 1, 1, s - 1, s - 1, r, fill=fill, outline="")
        if getattr(self, "pointilles", False) and not self._texte and not self._curseur:  # case facultative (Mot piégé)
            self.delete("all"); self.create_rectangle(2, 2, s - 2, s - 2, outline=P["texte2"], width=2, dash=(4, 3))
        if self._curseur:
            arrondi(self, 2, 2, s - 2, s - 2, r, fill="", outline=P["mal"], width=2)
        if self._texte and not self.mini:
            self.create_text(s / 2, s / 2 - (1 if ombre else 0), text=self._texte, fill=fg, font=police("chiffres", int(s * 0.5)))
        elif self._texte and self.mini and s >= 14:
            self.create_text(s / 2, s / 2, text=self._texte, fill=fg, font=police("chiffres", max(7, int(s * 0.55))))


class Bouton(tk.Canvas):
    """variante : 'principal' (accent), 'secondaire' (contour accent), 'discret' (contour discret), 'tuile' (plein discret)."""
    def __init__(self, parent, texte, commande, largeur=200, hauteur=46, variante="principal", taille=15, couleur=None):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
        self.texte, self.commande, self.largeur, self.hauteur = texte, commande, largeur, hauteur
        self.variante, self.taille, self.couleur, self.actif, self.survol = variante, taille, couleur, True, False
        self.bind("<Enter>", lambda e=None: self._set_survol(True)); self.bind("<Leave>", lambda e=None: self._set_survol(False))
        self.bind("<ButtonRelease-1>", self._clic)
        self._dessiner()

    def _couleurs(self):
        acc = self.couleur or P["accent"]
        v = self.variante
        if v == "principal": fill, out, fg = acc, "", contraste(acc)
        elif v == "secondaire": fill, out, fg = P["fond"] if fond_parent(self) == P["fond"] else fond_parent(self), acc, acc
        elif v == "tuile": fill, out, fg = P["tuile"], "", P["texte"]
        else: fill, out, fg = fond_parent(self), P["bordure"], P["texte"]
        if self.survol and self.actif:
            fill = eclaircir(fill, 1.12) if v == "principal" else melanger(fill, P["texte"], 0.07)
        if not self.actif:
            fill = melanger(fill, P["fond"], 0.55) if fill else fill
            fg = melanger(fg, P["fond"], 0.5); out = melanger(out, P["fond"], 0.5) if out else out
        return fill, out, fg

    def _dessiner(self):
        self.delete("all")
        fill, out, fg = self._couleurs()
        arrondi(self, 1, 1, self.largeur - 1, self.hauteur - 1, min(12, self.hauteur / 2.6), fill=fill, outline=out, width=1.5 if out else 0)
        self.create_text(self.largeur / 2, self.hauteur / 2, text=self.texte, fill=fg, font=police("texte", self.taille, True))

    def _set_survol(self, v): self.survol = v; self._dessiner()
    def _clic(self, e):
        if self.actif and 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height(): self.commande()
    def set_text(self, t): self.texte = t; self._dessiner()
    def set_variante(self, v): self.variante = v; self._dessiner()
    def set_couleur(self, c): self.couleur = c; self._dessiner()
    def activer(self, s): self.actif = s; self.config(cursor="hand2" if s else ""); self._dessiner()


class Panneau(tk.Canvas):
    """Panneau aux coins arrondis ; mettre les widgets dans .interieur (même couleur de fond)."""
    def __init__(self, parent, padding=22, rayon=18, couleur=None, contour=None, largeur=None, tirets=False):
        super().__init__(parent, bg=fond_parent(parent), highlightthickness=0, bd=0)
        self.padding, self.rayon, self.largeur, self.tirets = padding, rayon, largeur, tirets
        self.couleur, self.contour = couleur or P["panneau"], contour
        self.interieur = tk.Frame(self, bg=self.couleur)
        self._win = self.create_window(padding, padding, window=self.interieur, anchor="nw")
        self._taille = (0, 0)
        self.interieur.bind("<Configure>", lambda e=None: self.after_idle(self._maj))
        self.after_idle(self._maj)

    def _maj(self):
        if not self.winfo_exists(): return
        p = self.padding
        if self.largeur: self.itemconfig(self._win, width=self.largeur - 2 * p)
        w = self.largeur or self.interieur.winfo_reqwidth() + 2 * p
        h = self.interieur.winfo_reqheight() + 2 * p
        if (w, h) != self._taille:
            self._taille = (w, h); self.config(width=w, height=h)
        self.delete("fond")
        kw = {"dash": (4, 3)} if self.tirets else {}
        arrondi(self, 1, 1, w - 1, h - 1, self.rayon, fill=self.couleur, outline=self.contour or "", width=1.2 if self.contour else 0, tags="fond", **kw)
        self.tag_lower("fond")


def glyphe(c, nom, cx, cy, r, couleur):
    """Pictogrammes des cartes du menu Solo : jouer (triangle), infini (∞), engrenage (roue dentée)."""
    import math
    if nom == "jouer":
        c.create_polygon(cx - r*0.35, cy - r*0.5, cx + r*0.6, cy, cx - r*0.35, cy + r*0.5, outline=couleur, fill="", width=max(2, r/9), joinstyle="round")
    elif nom == "infini":
        pts = []
        for i in range(61):
            t = 2 * math.pi * i / 60
            d = 1 + math.sin(t) ** 2
            pts += [cx + r * 0.8 * math.cos(t) / d * 1.5, cy + r * 0.8 * math.sin(t) * math.cos(t) / d * 1.5]
        c.create_line(*pts, fill=couleur, width=max(2, r/7), smooth=True, capstyle="round", joinstyle="round")
    elif nom == "engrenage":
        pts = []
        for i in range(8):
            a0 = i * math.pi / 4
            for da, rr in ((-0.20, 0.72), (-0.13, 1.0), (0.13, 1.0), (0.20, 0.72)):
                pts += [cx + math.cos(a0 + da) * r * rr * 0.92, cy + math.sin(a0 + da) * r * rr * 0.92]
        c.create_polygon(*pts, outline=couleur, fill="", width=max(2, r/9), joinstyle="round")
        c.create_oval(cx - r*0.3, cy - r*0.3, cx + r*0.3, cy + r*0.3, outline=couleur, width=max(2, r/9))


class CarteMenu(tk.Canvas):
    """Carte cliquable : titre, sous-titre, chevron ou badge. Avec `couleur`, la carte est pleine (texte `texte`).
    Avec `icone` (jouer, infini, engrenage), un pictogramme est dessiné à gauche ; `degrade` = 2e couleur d'un dégradé horizontal ;
    `rond` = pictogramme dans un disque ; `grand` = titre en 38 px."""
    def __init__(self, parent, titre, sous_titre, commande, largeur=540, hauteur=94, badge=None, couleur=None, texte=None, icone=None, degrade=None, rond=False, grand=False, fond_icone=None):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
        self.titre, self.sous, self.commande, self.badge, self.l, self.h = titre, sous_titre, commande, badge, largeur, hauteur
        self.couleur, self.texte, self.icone, self.degrade, self.rond, self.grand, self.fond_icone = couleur, texte, icone, degrade, rond, grand, fond_icone
        self.survol = False
        self.bind("<Enter>", lambda e=None: self._s(True)); self.bind("<Leave>", lambda e=None: self._s(False))
        self.bind("<ButtonRelease-1>", lambda e=None: self.commande())
        self._dessiner()
    def _s(self, v): self.survol = v; self._dessiner()
    def set_badge(self, b): self.badge = b; self._dessiner()
    def _dessiner(self):
        self.delete("all")
        if self.couleur:
            fond, t1 = (eclaircir(self.couleur, 1.08) if self.survol else self.couleur), self.texte
            t2, tb = melanger(t1, self.couleur, 0.15), t1
        else:
            fond, t1, t2, tb = (P["survol"] if self.survol else P["panneau"]), P["texte"], P["texte2"], P["mal"]
        if self.degrade:  # dégradé horizontal : deux extrémités arrondies, bandes de 2 px entre les deux
            fin = eclaircir(self.degrade, 1.08) if self.survol else self.degrade
            arrondi(self, 1, 1, 36, self.h - 1, 16, fill=fond, outline=""); arrondi(self, self.l - 36, 1, self.l - 1, self.h - 1, 16, fill=fin, outline="")
            for x in range(18, self.l - 18, 2): self.create_rectangle(x, 1, x + 2, self.h, fill=melanger(fond, fin, x / self.l), outline="")
        else:
            arrondi(self, 1, 1, self.l - 1, self.h - 1, 16, fill=fond, outline="")
        x0 = 30
        if self.icone:
            d = 88 if self.rond else (56 if self.h > 90 else 48); x0 = 34 + d + 22
            cx, cy = 34 + d / 2, self.h / 2
            ton = self.fond_icone or melanger(fond, t1, 0.18)
            if self.rond: self.create_oval(cx - d/2, cy - d/2, cx + d/2, cy + d/2, fill=ton, outline="")
            else: arrondi(self, cx - d/2, cy - d/2, cx + d/2, cy + d/2, 16, fill=ton, outline="")
            glyphe(self, self.icone, cx, cy, d * 0.27, t1)
        ty = 38 if self.grand else 26
        self.create_text(x0, self.h / 2 - (14 if self.grand else 12), text=self.titre, anchor="w", fill=t1, font=police("titre", ty))
        self.create_text(x0, self.h / 2 + (24 if self.grand else 17), text=self.sous, anchor="w", fill=t2, font=police("texte", 17 if self.grand else 16))
        if self.badge:
            self.create_text(self.l - 30, self.h / 2, text=self.badge, anchor="e", fill=tb, font=police("texte", 15, True))
        elif not self.icone:
            x, y = self.l - 38, self.h / 2
            self.create_line(x - 4, y - 8, x + 4, y, x - 4, y + 8, fill=t2, width=2, capstyle="round", joinstyle="round")


class Icone(tk.Canvas):
    """Petites icônes dessinées : retour, aide, palette, reglages, copier, rafraichir, plus, moins."""
    def __init__(self, parent, nom, commande, taille=40, cadre=False):
        super().__init__(parent, width=taille, height=taille, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
        self.nom, self.commande, self.t, self.cadre, self.survol, self.actif = nom, commande, taille, cadre, False, True
        self.bind("<Enter>", lambda e=None: self._s(True)); self.bind("<Leave>", lambda e=None: self._s(False))
        self.bind("<ButtonRelease-1>", lambda e=None: self.commande() if self.actif else None)
        self._dessiner()
    def _s(self, v): self.survol = v; self._dessiner()
    def activer(self, s): self.actif = s; self.config(cursor="hand2" if s else ""); self._dessiner()
    def _dessiner(self):
        self.delete("all")
        if not self.actif: return
        t, c = self.t, (P["texte"] if self.survol else P["texte2"])
        if self.cadre or self.survol:
            arrondi(self, 1, 1, t - 1, t - 1, 10, fill=P["panneau"] if self.survol else fond_parent(self), outline=P["bordure"] if self.cadre else "")
        m, k = t / 2, t / 40
        w = max(1.6, 2 * k)
        if self.nom == "retour":
            self.create_line(m + 4*k, m - 8*k, m - 4*k, m, m + 4*k, m + 8*k, fill=c, width=w, capstyle="round", joinstyle="round")
        elif self.nom == "aide":
            self.create_oval(m - 11*k, m - 11*k, m + 11*k, m + 11*k, outline=c, width=w)
            self.create_text(m, m + k, text="?", fill=c, font=police("texte", 15 * k, True))
        elif self.nom == "palette":
            self.create_oval(m - 11*k, m - 10*k, m + 11*k, m + 11*k, outline=c, width=w)
            for dx, dy in ((-5, -3), (0, -6), (5, -3)): self.create_oval(m + dx*k - 1.8*k, m + dy*k - 1.8*k, m + dx*k + 1.8*k, m + dy*k + 1.8*k, fill=c, outline="")
            self.create_oval(m + 2*k, m + 3*k, m + 7*k, m + 8*k, fill=fond_parent(self), outline=c, width=w * 0.8)
        elif self.nom == "reglages":
            import math
            self.create_oval(m - 4*k, m - 4*k, m + 4*k, m + 4*k, outline=c, width=w)
            for i in range(8):
                a = i * math.pi / 4
                self.create_line(m + math.cos(a) * 7*k, m + math.sin(a) * 7*k, m + math.cos(a) * 11*k, m + math.sin(a) * 11*k, fill=c, width=w, capstyle="round")
        elif self.nom == "copier":
            arrondi(self, m - 3*k, m - 3*k, m + 9*k, m + 9*k, 3*k, fill="", outline=c, width=w)
            self.create_line(m - 9*k + 0, m + 4*k, m - 9*k, m - 9*k, m + 4*k, m - 9*k, fill=c, width=w, capstyle="round", joinstyle="round")
        elif self.nom == "rafraichir":
            self.create_arc(m - 10*k, m - 10*k, m + 10*k, m + 10*k, start=40, extent=290, style="arc", outline=c, width=w)
            self.create_line(m + 9*k, m - 11*k, m + 9*k, m - 4*k, m + 2*k, m - 4*k, fill=c, width=w, capstyle="round", joinstyle="round")
        elif self.nom == "stats":
            for i, hh in enumerate((7, 13, 10)):
                x = m + (i - 1) * 7 * k
                self.create_line(x, m + 9 * k, x, m + 9 * k - hh * 1.4 * k, fill=c, width=w * 1.6, capstyle="round")
        elif self.nom in ("plus", "moins"):
            self.create_line(m - 8*k, m, m + 8*k, m, fill=c, width=w * 1.2, capstyle="round")
            if self.nom == "plus": self.create_line(m, m - 8*k, m, m + 8*k, fill=c, width=w * 1.2, capstyle="round")


class Avatar(tk.Canvas):
    COULEURS = ["#F5B83D", "#8FB3FF", "#7ED6A8", "#F2A1C5", "#C4A7FF", "#FFB38A", "#7FD8F0", "#D6E58A"]
    def __init__(self, parent, nom, taille=44, commande=None, index=0, vide=False):
        super().__init__(parent, width=taille, height=taille, bg=fond_parent(parent), highlightthickness=0, cursor="hand2" if commande else "")
        self.t, self.vide = taille, vide
        if commande: self.bind("<ButtonRelease-1>", lambda e: commande())
        self.set_nom(nom, index)
    def set_nom(self, nom, index=0):
        self.delete("all"); t = self.t
        if self.vide:
            self.create_oval(1, 1, t - 1, t - 1, fill=P["vide"], outline=""); return
        coul = self.COULEURS[index % len(self.COULEURS)]
        self.create_oval(1, 1, t - 1, t - 1, fill=coul, outline="")
        self.create_text(t / 2, t / 2, text=(nom or "?")[:1].upper(), fill="#16130a", font=police("texte", t * 0.42, True))


class Logo(tk.Canvas):
    """SMOUT en tuiles, comme MOTUS (dont SMOUT est un anagramme) : U bien placé, les autres lettres mal placées."""
    def __init__(self, parent, taille=88, ecart=14):
        n = 5
        super().__init__(parent, width=n * taille + (n - 1) * ecart, height=taille + 4, bg=fond_parent(parent), highlightthickness=0)
        etats = ["mal", "mal", "mal", "bien", "mal"]
        for i, (ch, et) in enumerate(zip("SMOUT", etats)):
            x = i * (taille + ecart)
            fill = P[et]; fg = P["sur_bien"] if et == "bien" else P["sur_mal"]
            arrondi(self, x + 1, 1, x + taille - 1, taille - 1, taille * 0.14, fill=fill, outline="")
            self.create_text(x + taille / 2, taille / 2, text=ch, fill=fg, font=police("chiffres", taille * 0.5))


class Chips(tk.Frame):
    """Rangée de pastilles à choix unique (6, 7, 8... / 3, 5, 7...)."""
    def __init__(self, parent, valeurs, valeur, callback=None, largeur=52, hauteur=44, libelles=None):
        super().__init__(parent, bg=fond_parent(parent))
        self.valeurs, self.valeur, self.callback, self.actif, self.couleur = list(valeurs), valeur, callback, True, None
        self.libelles = libelles or [str(v) for v in self.valeurs]
        self.cases = []
        for i, v in enumerate(self.valeurs):
            c = tk.Canvas(self, width=largeur, height=hauteur, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
            c.pack(side="left", padx=(0, 8)); c.bind("<ButtonRelease-1>", lambda e, v=v: self._choisir(v))
            self.cases.append((v, c, largeur, hauteur, self.libelles[i]))
        self._dessiner()
    def _choisir(self, v):
        if not self.actif or v == self.valeur: return
        self.valeur = v; self._dessiner()
        if self.callback: self.callback(v)
    def set_valeur(self, v): self.valeur = v; self._dessiner()
    def set_couleur(self, c):  # couleur de la pastille choisie (ex. couleur du mode de jeu)
        if c != self.couleur: self.couleur = c; self._dessiner()
    def get(self): return self.valeur
    def activer(self, s):
        self.actif = s
        for _, c, *_ in self.cases: c.config(cursor="hand2" if s else "")
        self._dessiner()
    def _dessiner(self):
        for v, c, w, h, lib in self.cases:
            c.delete("all"); sel = v == self.valeur
            fill = (self.couleur or P["mal"]) if sel else fond_parent(self)
            out = "" if sel else P["bordure"]
            fg = (contraste(self.couleur) if self.couleur else P["sur_mal"]) if sel else P["texte"]
            if not self.actif: fill = melanger(fill, fond_parent(self), 0.45) if sel else fill; fg = melanger(fg, fond_parent(self), 0.35)
            arrondi(c, 1, 1, w - 1, h - 1, 10, fill=fill, outline=out, width=1.2 if out else 0)
            c.create_text(w / 2, h / 2, text=lib, fill=fg, font=police("chiffres", 17))


def dessiner_cadenas(c, cx, cy, t, couleur):
    """Petit cadenas fermé centré en (cx, cy), de hauteur t."""
    w, h = t * 0.72, t * 0.5; ep = max(1.8, t * 0.1)
    haut = cy - t * 0.5
    c.create_arc(cx - w * 0.3, haut, cx + w * 0.3, haut + t * 0.62, start=0, extent=180, style="arc", outline=couleur, width=ep)
    arrondi(c, cx - w / 2, cy - t * 0.08, cx + w / 2, cy - t * 0.08 + h, t * 0.1, fill=couleur, outline="")

class CarteChoix(tk.Canvas):
    """Carte de mode de jeu (titre + description), sélectionnée = couleur d'accent."""
    def __init__(self, parent, titre, description, commande, largeur=300, hauteur=78, couleur=None, icone=None):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
        self.titre, self.desc, self.commande, self.l, self.h, self.couleur, self.icone = titre, description, commande, largeur, hauteur, couleur, icone
        self.selection, self.actif = False, True
        self.bind("<ButtonRelease-1>", lambda e=None: self.commande() if self.actif else None)
        self._dessiner()
    def set_selection(self, s): self.selection = s; self._dessiner()
    def activer(self, s): self.actif = s; self.config(cursor="hand2" if s else ""); self._dessiner()
    def _dessiner(self):
        self.delete("all")
        sel, mc = self.selection, self.couleur
        fill = (mc or P["mal"]) if sel else fond_parent(self); out = "" if sel else P["bordure"]
        fg1 = (contraste(mc) if mc else P["sur_mal"]) if sel else (mc or P["texte"]); fg2 = melanger(fg1, fill, 0.2) if sel else P["texte2"]
        if not self.actif and not sel: fg1 = melanger(fg1, fill, 0.35)
        arrondi(self, 1, 1, self.l - 1, self.h - 1, 12, fill=fill, outline=out, width=1.2 if out else 0)
        if mc and not sel: arrondi(self, 5, 10, 9, self.h - 10, 2, fill=mc, outline="")  # liseré de couleur du mode
        compact = self.l < 200  # grille de 4 cartes par rangée
        x = 14 if compact else 20
        self.create_text(x, self.h * (0.36 if self.desc else 0.5), text=self.titre, anchor="w", fill=fg1, font=police("texte", 15 if compact else 17, True))
        marge = 56 if self.icone else 8
        if self.desc: self.create_text(x, self.h * 0.7, text=self.desc, anchor="w", fill=fg2, font=police("texte", 11 if compact else 12), width=self.l - x - marge)
        if self.icone == "cadenas": dessiner_cadenas(self, self.l - 32, self.h / 2, 26, fg1)


class Curseur(tk.Canvas):
    """Curseur à glisser (valeur unique) ou plage à deux poignées (plage=True, valeur = (min, max)).
    La valeur s'affiche à droite ; une poignée qui dépasse l'autre la pousse."""
    def __init__(self, parent, mini, maxi, valeur, pas=1, commande=None, formater=str, largeur=440, plage=False, couleur=None):
        super().__init__(parent, width=largeur, height=36, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
        self.mini, self.maxi, self.pas, self.commande, self.fmt, self.l, self.plage = mini, maxi, pas, commande, formater, largeur, plage
        self.x0, self.x1 = 14, largeur - 74
        self.v = list(valeur) if plage else [valeur]
        self.actif, self.couleur, self.idx = True, couleur, 0
        self.bind("<ButtonPress-1>", self._presse); self.bind("<B1-Motion>", self._bouge)
        self._dessiner()
    def get(self): return tuple(self.v) if self.plage else self.v[0]
    def set_valeur(self, *vals):
        nv = list(vals[0]) if (self.plage and len(vals) == 1) else list(vals)
        nv = [max(self.mini, min(self.maxi, int(x))) for x in nv]
        if nv != self.v: self.v = nv; self._dessiner()
    def set_couleur(self, c):
        if c != self.couleur: self.couleur = c; self._dessiner()
    def activer(self, s):
        self.actif = s; self.config(cursor="hand2" if s else ""); self._dessiner()
    def _x(self, val): return self.x0 + (val - self.mini) / (self.maxi - self.mini) * (self.x1 - self.x0)
    def _val(self, x):
        t = max(0.0, min(1.0, (x - self.x0) / (self.x1 - self.x0)))
        return max(self.mini, min(self.maxi, self.mini + round(t * (self.maxi - self.mini) / self.pas) * self.pas))
    def _presse(self, e):
        if not self.actif: return
        if self.plage:
            d0, d1 = abs(e.x - self._x(self.v[0])), abs(e.x - self._x(self.v[1]))
            self.idx = 0 if (d0 < d1 or (d0 == d1 and e.x < self._x(self.v[0]))) else 1
        else: self.idx = 0
        self._bouge(e)
    def _bouge(self, e):
        if not self.actif: return
        val, nv = self._val(e.x), list(self.v)
        nv[self.idx] = val
        if self.plage:
            if self.idx == 0 and nv[0] > nv[1]: nv[1] = nv[0]
            if self.idx == 1 and nv[1] < nv[0]: nv[0] = nv[1]
        if nv != self.v:
            self.v = nv; self._dessiner()
            if self.commande: self.commande(self.get())
    def _dessiner(self):
        self.delete("all")
        coul = self.couleur or P["mal"]; y = 18
        if not self.actif: coul = melanger(coul, fond_parent(self), 0.55)
        arrondi(self, self.x0 - 4, y - 4, self.x1 + 4, y + 4, 4, fill=P["tuile"], outline="")
        a = self._x(self.v[0]) if self.plage else self.x0
        b = self._x(self.v[-1])
        arrondi(self, a - 4 if self.plage else self.x0 - 4, y - 4, b + 4, y + 4, 4, fill=coul, outline="")
        for x in ([self._x(v) for v in self.v] if self.plage else [b]):
            self.create_oval(x - 11, y - 11, x + 11, y + 11, fill=coul, outline=fond_parent(self), width=3)
        txt = (f"{self.v[0]} à {self.v[1]}" if self.v[0] != self.v[1] else str(self.v[0])) if self.plage else self.fmt(self.v[0])
        self.create_text(self.l - 4, y, text=txt, anchor="e", fill=P["texte"] if self.actif else P["texte2"], font=police("chiffres", 15, True))


def nettoyer_pseudo(p):
    """9.0 : pseudo en lettres (accents compris), chiffres et espaces uniquement, en majuscules, 15 caractères au plus (comme nettoyerPseudo du site)."""
    import unicodedata
    p = unicodedata.normalize("NFC", str(p or "").upper())
    p = "".join(c for c in p if c.isalpha() or c in "0123456789 ")
    while "  " in p: p = p.replace("  ", " ")
    return p.lstrip()[:15]  # espaces simples, jamais au début (celui de la fin est retiré à l'enregistrement)


class BoutonLobby(Bouton):
    """9.0 : bouton de l'hôte « Lobby » (flèche de retour + texte, contour jaune), en haut à gauche de la partie et de la fin de partie.
    Même rendu que .btn-salon du site."""
    def __init__(self, parent, commande):
        super().__init__(parent, "Lobby", commande, largeur=96, hauteur=36, variante="secondaire", taille=14, couleur=P["mal"])
    def _dessiner(self):
        self.delete("all")
        fill, out, fg = self._couleurs()
        if self.survol and self.actif: fill, fg = P["mal"], P["sur_mal"]
        arrondi(self, 1, 1, self.largeur - 1, self.hauteur - 1, min(12, self.hauteur / 2.6), fill=fill, outline=out, width=1.5)
        x, m = 16, self.hauteur / 2  # flèche de retour : pointe à gauche puis crochet vers le bas
        self.create_line(x + 4, m - 6, x, m - 2, x + 4, m + 2, fill=fg, width=2, capstyle="round", joinstyle="round")
        self.create_line(x, m - 2, x + 9, m - 2, fill=fg, width=2, capstyle="round")
        self.create_arc(x + 4, m - 2, x + 14, m + 8, start=-90, extent=180, style="arc", outline=fg, width=2)
        self.create_line(x + 9, m + 8, x + 6, m + 8, fill=fg, width=2, capstyle="round")
        self.create_text(x + 22, m, text=self.texte, anchor="w", fill=fg, font=police("texte", self.taille, True))


class Clavier(tk.Frame):
    """Clavier AZERTY avec Effacer et Valider intégrés. zoom : le réglage « taille » (− 100 % +) agrandit aussi le clavier."""
    RANGS = ["AZERTYUIOP", "QSDFGHJKLM", "WXCVBN"]
    def __init__(self, parent, on_lettre, on_effacer, on_valider, touche=42, hauteur=50, zoom=1.0):
        super().__init__(parent, bg=fond_parent(parent))
        self.on_lettre, self.on_effacer, self.on_valider = on_lettre, on_effacer, on_valider
        self.touche0, self.h0, self.etats, self.canvas = touche, hauteur, {}, {}
        self.set_zoom(zoom)
    def set_zoom(self, zoom):
        """(Re)construit les touches à la taille voulue, en gardant leurs couleurs."""
        self.zoom = max(0.6, min(1.6, float(zoom or 1)))
        self.touche, self.h = int(round(self.touche0 * self.zoom)), int(round(self.h0 * self.zoom))
        for w in self.winfo_children(): w.destroy()
        self.canvas = {}
        for i, rang in enumerate(self.RANGS):
            f = tk.Frame(self, bg=self["bg"]); f.pack(pady=4)
            if i == 2: self._speciale(f, "Effacer", self.on_effacer, "tuile")
            for ch in rang:
                c = tk.Canvas(f, width=self.touche, height=self.h, bg=self["bg"], highlightthickness=0, cursor="hand2")
                c.pack(side="left", padx=4); c.bind("<ButtonRelease-1>", lambda e=None, ch=ch: e is not None and self.on_lettre(ch))  # e absent : appel parasite de Tk, ignoré
                self.canvas[ch] = c; self.etats.setdefault(ch, None); self._dessiner(ch)
            if i == 2: self._speciale(f, "Valider", self.on_valider, "principal")
    def _speciale(self, f, texte, cmd, variante):
        largeur = self.touche * 2 + 8
        b = Bouton(f, texte, cmd, largeur=largeur, hauteur=self.h, variante=variante, taille=max(9, round(15 * self.zoom)), couleur=P["mal"])
        b.pack(side="left", padx=4)
    def set_couleur(self, ch, couleur):
        if ch in self.canvas and self.etats.get(ch) != couleur: self.etats[ch] = couleur; self._dessiner(ch)
    def _dessiner(self, ch):
        c, w, h = self.canvas[ch], self.touche, self.h
        e = self.etats.get(ch)
        if e == P["bien"]: fill, fg = P["bien"], P["sur_bien"]
        elif e == P["mal"]: fill, fg = P["mal"], P["sur_mal"]
        elif e == P["absent"]: fill, fg = P["vide"], P["texte_absent"]
        else: fill, fg = P["tuile"], P["texte"]
        c.delete("all")
        arrondi(c, 1, 1, w - 1, h - 1, 8, fill=fill, outline="")
        c.create_text(w / 2, h / 2, text=ch, fill=fg, font=police("chiffres", max(10, round(17 * self.zoom))))


class Stat(tk.Frame):
    """Bloc statistique : petite étiquette en capitales + grande valeur."""
    def __init__(self, parent, titre, valeur="", couleur=None, taille=44):
        super().__init__(parent, bg=fond_parent(parent))
        etiquette(self, espacer(titre), "texte", 13, P["texte2"], True).pack()
        self.f = tk.Frame(self, bg=fond_parent(parent)); self.f.pack()
        self.lbl = etiquette(self.f, valeur, "chiffres", taille, couleur or P["texte"]); self.lbl.pack(side="left")
        self.suffixe = etiquette(self.f, "", "chiffres", taille * 0.55, P["texte2"]); self.suffixe.pack(side="left", anchor="s", pady=(0, taille * 0.12))
    def set(self, valeur, couleur=None, suffixe=None):
        self.lbl.config(text=valeur)
        if couleur: self.lbl.config(fg=couleur)
        if suffixe is not None: self.suffixe.config(text=suffixe)


class Defilant(tk.Frame):
    """Zone qui défile à la molette ; mettre le contenu dans .interieur."""
    def __init__(self, parent, largeur=None, hauteur=400):
        super().__init__(parent, bg=fond_parent(parent))
        self.canvas = tk.Canvas(self, bg=fond_parent(parent), highlightthickness=0, height=hauteur, width=largeur or 600)
        self.canvas.pack(fill="both", expand=True)
        self.interieur = tk.Frame(self.canvas, bg=fond_parent(parent))
        self._fen = self.canvas.create_window(0, 0, window=self.interieur, anchor="nw")
        self.interieur.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._fen, width=e.width))
        for w in (self.canvas, self.interieur):
            w.bind("<Enter>", self._lier); w.bind("<Leave>", self._delier)
    def _lier(self, e):
        self.bind_all("<MouseWheel>", self._molette); self.bind_all("<Button-4>", self._molette); self.bind_all("<Button-5>", self._molette)
    def _delier(self, e):
        try:
            w = self.winfo_containing(*self.winfo_pointerxy())
            if w is not None and str(w).startswith(str(self)): return  # toujours au-dessus de la zone (sur un enfant)
        except (tk.TclError, KeyError): pass
        self.unbind_all("<MouseWheel>"); self.unbind_all("<Button-4>"); self.unbind_all("<Button-5>")
    def _molette(self, e):
        try:
            if not self.winfo_exists() or self.interieur.winfo_reqheight() <= self.canvas.winfo_height(): return
        except tk.TclError: return
        if getattr(e, "num", None) == 4: d = -1
        elif getattr(e, "num", None) == 5: d = 1
        else: d = -1 if e.delta > 0 else 1
        self.canvas.yview_scroll(d * 2, "units")


class Champ(tk.Frame):
    """Champ de saisie arrondi."""
    def __init__(self, parent, largeur=300, hauteur=52, texte_aide="", mono=False, masque=False, taille=17, variable=None):
        super().__init__(parent, bg=fond_parent(parent))
        self.c = tk.Canvas(self, width=largeur, height=hauteur, bg=fond_parent(parent), highlightthickness=0)
        self.c.pack()
        arrondi(self.c, 1, 1, largeur - 1, hauteur - 1, 12, fill=P["panneau"], outline=P["bordure"], width=1)
        self.var = variable or tk.StringVar()
        self.e = tk.Entry(self.c, textvariable=self.var, font=police("chiffres" if mono else "texte", taille, mono), bd=0, relief="flat",
                          bg=P["panneau"], fg=P["texte"], insertbackground=P["texte"], highlightthickness=0, show="•" if masque else "")
        self.c.create_window(18, hauteur / 2, window=self.e, anchor="w", width=largeur - 36)
        self.aide = texte_aide
        self.ph = tk.Label(self.c, text=texte_aide, bg=P["panneau"], fg=P["texte2"], font=police("chiffres" if mono else "texte", taille, mono), cursor="xterm")
        self.ph.bind("<Button-1>", lambda e: self.e.focus_set())
        self.var.trace_add("write", lambda *a: self._maj_aide())
        self.e.bind("<FocusIn>", lambda e: self._maj_aide(True)); self.e.bind("<FocusOut>", lambda e: self._maj_aide(False))
        self.c.bind("<Button-1>", lambda e: self.e.focus_set())
        self.hauteur = hauteur; self._maj_aide(False)
    def _maj_aide(self, focus=None):
        try:
            if focus is None: focus = self.focus_get() == self.e
        except Exception: focus = False
        try:
            if self.aide and not self.var.get() and not focus: self.ph.place(x=18, y=self.hauteur / 2, anchor="w")
            else: self.ph.place_forget()
        except tk.TclError: pass
    def get(self): return self.var.get()
    def set(self, v): self.var.set(v)
    def focus(self): self.e.focus_set()
    def bind_entree(self, f): self.e.bind("<Return>", lambda e: f())


class Interrupteur(tk.Canvas):
    """Case à cocher style maquette."""
    def __init__(self, parent, texte, valeur=False, callback=None, largeur=420):
        super().__init__(parent, width=largeur, height=34, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
        self.texte, self.valeur, self.callback = texte, valeur, callback
        self.bind("<ButtonRelease-1>", lambda e: self.basculer()); self._dessiner()
    def basculer(self):
        self.valeur = not self.valeur; self._dessiner()
        if self.callback: self.callback(self.valeur)
    def _dessiner(self):
        self.delete("all")
        if self.valeur:
            arrondi(self, 2, 3, 30, 31, 6, fill=P["mal"], outline="")
            self.create_line(9, 17, 14, 23, 24, 10, fill=P["sur_mal"], width=3, capstyle="round", joinstyle="round")
        else:
            arrondi(self, 2, 3, 30, 31, 6, fill="", outline=P["bordure"], width=1.5)
        self.create_text(44, 17, text=self.texte, anchor="w", fill=P["texte"], font=police("texte", 16))


class Superposition(tk.Frame):
    """Fenêtre posée au-dessus d'un écran (aide, mot de passe, fin de partie)."""
    def __init__(self, parent, largeur=520):
        super().__init__(parent, bg=P["fond"])
        self.panneau = Panneau(self, padding=30, rayon=20, contour=P["bordure"], largeur=largeur)
        self.panneau.place(relx=0.5, rely=0.5, anchor="center")
        self.interieur = self.panneau.interieur
    def montrer(self): self.place(relx=0, rely=0, relwidth=1, relheight=1); self.tkraise()
    def cacher(self): self.place_forget()


def entete(parent, titre="", on_retour=None, droite=None):
    """Barre du haut : bouton retour, titre centré (texte secondaire), widget à droite."""
    h = tk.Frame(parent, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
    if on_retour: Icone(h, "retour", on_retour).pack(side="left")
    else: tk.Frame(h, width=40, height=40, bg=P["fond"]).pack(side="left")
    if droite: droite(h).pack(side="right")
    else: tk.Frame(h, width=40, height=40, bg=P["fond"]).pack(side="right")
    lbl = etiquette(h, titre, "texte", 16, P["texte2"]); lbl.pack(side="top", pady=8)
    return lbl


def fenetre_aide(parent):
    """Règles du jeu."""
    o = Superposition(parent, largeur=560)
    i = o.interieur
    etiquette(i, "Comment jouer", "titre", 28).pack(anchor="w")
    etiquette(i, "Trouvez le mot caché. La première lettre est donnée (sauf en mode Mystère).", "texte", 15, P["texte2"], wraplength=490, justify="left").pack(anchor="w", pady=(6, 16))
    for etat, txt in (("bien", "Lettre bien placée"), ("mal", "Lettre présente mais mal placée"), ("absent", "Lettre absente du mot")):
        r = tk.Frame(i, bg=i["bg"]); r.pack(anchor="w", pady=4)
        t = Tuile(r, 38); t.config(text="A", bg=P[etat]); t.pack(side="left")
        etiquette(r, txt, "texte", 15).pack(side="left", padx=12)
    etiquette(i, "Clavier : tapez les lettres, Entrée pour valider, Retour arrière pour effacer.", "texte", 13, P["texte2"], wraplength=490, justify="left").pack(anchor="w", pady=(16, 18))
    Bouton(i, "Compris", o.cacher, largeur=160).pack(anchor="e")
    return o


# ---------------------------------------------------------------- configuration
import json, datetime

def dossier_config():
    if sys.platform == "win32": d = os.path.join(os.getenv('APPDATA') or os.path.expanduser("~"), "SMOUT")
    else: d = os.path.join(os.path.expanduser("~"), ".config", "SMOUT")
    os.makedirs(d, exist_ok=True)
    return d

def lire_config():
    try:
        with open(os.path.join(dossier_config(), "config.json"), "r") as f: return json.load(f)
    except Exception: return {}

APRES_MAJ_CONFIG = []  # fonctions appelées avec les clés modifiées (compte.py : envoi de l'avancement au compte)
_VERROU_CONFIG = __import__("threading").RLock()

def maj_config(**valeurs):
    with _VERROU_CONFIG:  # la synchronisation du compte écrit aussi depuis un fil d'arrière-plan
        cfg = lire_config(); cfg.update(valeurs)
        try:
            with open(os.path.join(dossier_config(), "config.json"), "w") as f: json.dump(cfg, f)
        except Exception: pass
    for f in APRES_MAJ_CONFIG:
        try: f(list(valeurs))
        except Exception: pass
    return cfg

def serie_mot_du_jour():
    """(série en cours, joué aujourd'hui ?) pour le badge de l'accueil."""
    cfg = lire_config()
    auj = datetime.date.today()
    joue = cfg.get("last_mdj") == auj.isoformat()
    der = cfg.get("mdj_dernier_gagne")
    serie = cfg.get("mdj_serie", 0)
    if not der or der not in (auj.isoformat(), (auj - datetime.timedelta(days=1)).isoformat()): serie = 0
    return serie, joue

def enregistrer_resultat_mdj(victoire):
    cfg = lire_config(); auj = datetime.date.today()
    if victoire:
        hier = (auj - datetime.timedelta(days=1)).isoformat()
        serie = cfg.get("mdj_serie", 0) + 1 if cfg.get("mdj_dernier_gagne") == hier else 1
        maj_config(mdj_serie=serie, mdj_dernier_gagne=auj.isoformat())
    else:
        maj_config(mdj_serie=0)

THEMES_CAT_LIB = {"SMOUT": "Nouveaux thèmes", "CLASSIQUE": "Classiques", "NATURE": "Nature", "TECH": "Tech",
                  "DOUCEUR": "Douceur", "RÉTRO": "Rétro", "LUXE": "Luxe", "PERSO": "Mes thèmes"}

NOMS_THEMES = {"CLASSIQUE TV": "Classique TV", "SMOUT CLASSIC": "SMOUT Classic", "CONTRASTE ÉLEVÉ": "Contraste élevé"}
def nom_theme(n):
    return NOMS_THEMES.get(n, n.capitalize() if n.isupper() else n)


class Stepper(tk.Frame):
    """Sélecteur − valeur + (manches, essais, temps)."""
    def __init__(self, parent, mini, maxi, valeur, pas=1, callback=None, formater=str, largeur_valeur=86):
        super().__init__(parent, bg=fond_parent(parent))
        self.mini, self.maxi, self.valeur, self.pas, self.callback, self.formater, self.actif = mini, maxi, valeur, pas, callback, formater, True
        self.b_moins = Icone(self, "moins", lambda: self._changer(-1), 44, cadre=True); self.b_moins.pack(side="left")
        self.lbl = tk.Label(self, text="", width=0, font=police("chiffres", 20), fg=P["texte"], bg=fond_parent(parent))
        self.lbl.pack(side="left", ipadx=(largeur_valeur - 40) // 2)
        self.b_plus = Icone(self, "plus", lambda: self._changer(1), 44, cadre=True); self.b_plus.pack(side="left")
        self._maj()
    def _changer(self, s):
        if not self.actif: return
        v = max(self.mini, min(self.maxi, self.valeur + s * self.pas))
        if v != self.valeur:
            self.valeur = v; self._maj()
            if self.callback: self.callback(v)
    def _maj(self): self.lbl.config(text=self.formater(self.valeur), fg=P["texte"] if self.actif else P["texte2"])
    def set_valeur(self, v): self.valeur = v; self._maj()
    def get(self): return self.valeur
    def activer(self, s):
        if s == self.actif: return
        self.actif = s; self.b_moins.activer(s); self.b_plus.activer(s); self._maj()


def pas_suivant(v, s, mini, maxi, pas=1, valeurs=None):
    """Valeur suivante (s = +1) ou précédente (s = -1) : dans `valeurs` si donné (ex. temps), sinon de `pas` en `pas`."""
    if valeurs:
        l = [x for x in valeurs if (x > v if s > 0 else x < v)]
        return (min(l) if s > 0 else max(l)) if l else v
    return max(mini, min(maxi, v + s * pas))


class TuileReglage(tk.Canvas):
    """Réglage en tuile : libellé, grande valeur, boutons − / + (masqués en lecture seule : activer(False)).
    plage=True : deux valeurs (min, max), chacune avec ses boutons ; une valeur qui dépasse l'autre la pousse.
    Même API que Curseur : get(), set_valeur(), set_couleur(), activer()."""
    def __init__(self, parent, libelle, mini, maxi, valeur, pas=1, commande=None, formater=str, largeur=200, hauteur=92,
                 plage=False, valeurs=None, couleur=None):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond_parent(parent), highlightthickness=0)
        self.libelle, self.mini, self.maxi, self.pas, self.commande, self.fmt = libelle, mini, maxi, pas, commande, formater
        self.l, self.h, self.plage, self.valeurs, self.couleur, self.actif = largeur, hauteur, plage, valeurs, couleur, True
        self.v = list(valeur) if plage else [valeur]
        self.zones, self.survol = [], None
        self.bind("<ButtonRelease-1>", self._clic); self.bind("<Motion>", self._bouge); self.bind("<Leave>", lambda e: self._survoler(None))
        self._dessiner()
    def get(self): return tuple(self.v) if self.plage else self.v[0]
    def set_valeur(self, *vals):
        nv = list(vals[0]) if (self.plage and len(vals) == 1) else list(vals)
        nv = [max(self.mini, min(self.maxi, int(x))) for x in nv]
        if nv != self.v: self.v = nv; self._dessiner()
    def set_couleur(self, c):
        if c != self.couleur: self.couleur = c; self._dessiner()
    def set_libelle(self, t):
        if t != self.libelle: self.libelle = t; self._dessiner()
    def set_largeur(self, w):
        if w != self.l: self.l = w; self.config(width=w); self._dessiner()
    def activer(self, s):
        if s != self.actif: self.actif = s; self._dessiner()
    def _changer(self, i, s):
        nv = list(self.v)
        nv[i] = pas_suivant(nv[i], s, self.mini, self.maxi, self.pas, self.valeurs)
        if self.plage:
            if i == 0 and nv[0] > nv[1]: nv[1] = nv[0]
            if i == 1 and nv[1] < nv[0]: nv[0] = nv[1]
        if nv != self.v:
            self.v = nv; self._dessiner()
            if self.commande: self.commande(self.get())
    def _zone(self, e):
        for (x, y, i, s) in self.zones:
            if (e.x - x) ** 2 + (e.y - y) ** 2 <= 21 ** 2: return (i, s)
        return None
    def _clic(self, e):
        z = self._zone(e) if self.actif else None
        if z: self._changer(*z)
    def _bouge(self, e): self._survoler(self._zone(e) if self.actif else None)
    def _survoler(self, z):
        if z != self.survol:
            self.survol = z; self.config(cursor="hand2" if z else ""); self._dessiner()
    def _dessiner(self):
        self.delete("all"); self.zones = []
        fond = fond_parent(self); mc = self.couleur or P["mal"]; W, H = self.l, self.h
        arrondi(self, 1, 1, W - 1, H - 1, 14, fill=melanger(fond, P["fond"], 0.5), outline=melanger(fond, P["bordure"], 0.7), width=1)
        self.create_text(W / 2, 22, text=espacer(self.libelle), fill=P["texte2"], font=police("texte", 10, True))
        y = H * 0.62
        def bouton(x, i, s):
            limite = pas_suivant(self.v[i], s, self.mini, self.maxi, self.pas, self.valeurs) == self.v[i]
            base = melanger(fond, P["fond"], 0.5)
            disque = base if limite else melanger(base, mc, 0.42 if self.survol == (i, s) else 0.2)
            c = melanger(mc, base, 0.65) if limite else mc
            self.create_oval(x - 17, y - 17, x + 17, y + 17, fill=disque, outline="")
            self.create_line(x - 6, y, x + 6, y, fill=c, width=2.4, capstyle="round")
            if s > 0: self.create_line(x, y - 6, x, y + 6, fill=c, width=2.4, capstyle="round")
            self.zones.append((x, y, i, s))
        vf = police("chiffres", 24, True)
        if not self.plage:
            self.create_text(W / 2, y, text=self.fmt(self.v[0]), fill=P["texte"], font=vf)
            if self.actif: bouton(34, 0, -1); bouton(W - 34, 0, 1)
        elif not self.actif:
            txt = str(self.v[0]) if self.v[0] == self.v[1] else f"{self.v[0]} à {self.v[1]}"
            self.create_text(W / 2, y, text=txt, fill=P["texte"], font=vf)
        else:
            for i, cx in enumerate((W * 0.27, W * 0.73)):
                self.create_text(cx, y, text=str(self.v[i]), fill=P["texte"], font=vf)
                bouton(cx - 52, i, -1); bouton(cx + 52, i, 1)
            self.create_text(W / 2, y, text="à", fill=P["texte2"], font=police("texte", 15))


class CarteSalon(tk.Canvas):
    """Ligne de la liste des salons publics."""
    def __init__(self, parent, titre, sous_titre, droite, commande, largeur=740, hauteur=84):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
        self.args, self.survol = (titre, sous_titre, droite, largeur, hauteur), False
        self.bind("<Enter>", lambda e=None: self._s(True)); self.bind("<Leave>", lambda e=None: self._s(False))
        self.bind("<ButtonRelease-1>", lambda e: commande())
        self._dessiner()
    def _s(self, v): self.survol = v; self._dessiner()
    def _dessiner(self):
        titre, sous, droite, l, h = self.args
        self.delete("all")
        arrondi(self, 1, 1, l - 1, h - 1, 14, fill=P["survol"] if self.survol else P["panneau"], outline="")
        self.create_text(26, h / 2 - 12, text=titre, anchor="w", fill=P["texte"], font=police("texte", 18, True))
        self.create_text(26, h / 2 + 14, text=sous, anchor="w", fill=P["texte2"], font=police("texte", 15))
        self.create_text(l - 26, h / 2, text=droite, anchor="e", fill=P["texte2"], font=police("chiffres", 20))


# ---------------------------------------------------------------- mode difficile (identique à smout.js)
def verifier_difficile(tape, historique):
    """Mode difficile : chaque lettre bien placée doit rester à sa place et chaque lettre découverte doit être réutilisée.
    historique = [(mot_propose, [etats "bien"/"mal"/"absent"])]. Renvoie un message d'erreur ou None."""
    for mot, etats in historique:
        for i, e in enumerate(etats):
            if e == "bien" and tape[i] != mot[i]:
                return f"Mode difficile : la {i + 1}{'re' if i == 0 else 'e'} lettre doit être un {mot[i]}"
        besoin = {}
        for i, e in enumerate(etats):
            if e in ("bien", "mal"): besoin[mot[i]] = besoin.get(mot[i], 0) + 1
        for ch, n in sorted(besoin.items()):
            if list(tape).count(ch) < n: return f"Mode difficile : le mot doit contenir {'un' if n == 1 else str(n) + ' ×'} {ch}"
    return None

def evaluer(tape, mot):
    """États de chaque lettre : "bien", "mal" ou "absent"."""
    res, secret = ["absent"] * len(mot), list(mot)
    for i in range(len(mot)):
        if tape[i] == mot[i]: res[i], secret[i] = "bien", None
    for i in range(len(mot)):
        if res[i] != "bien" and tape[i] in secret: res[i] = "mal"; secret[secret.index(tape[i])] = None
    return res

EMOJI = {"bien": "🟥", "mal": "🟡", "absent": "🟦"}
def texte_partage(titre, etats_lignes, essais_txt, score_txt, lien=""):
    lignes = [f"SMOUT · {titre} · {essais_txt} · {score_txt} pts"] + ["".join(EMOJI[e] for e in l) for l in etats_lignes]
    if lien: lignes.append(lien)
    return "\n".join(lignes)

# ---------------------------------------------------------------- statistiques (enregistrées sur l'appareil)
def stats_vides():
    return {"parties": 0, "victoires": 0, "repartition": {}, "serie": 0, "meilleure_serie": 0, "meilleur_score": 0}

def lire_stats():
    st = lire_config().get("stats") or {}
    for k in ("solo", "mdj"): st[k] = dict(stats_vides(), **(st.get(k) or {}))
    st["marathon"] = dict({"parties": 0, "record": 0, "record_score": 0, "mots": 0}, **(st.get("marathon") or {}))
    st.setdefault("historique", [])
    return st

def enregistrer_partie(genre, victoire, essais=0, score=0, mot="", detail=""):
    """genre : solo, mdj (une partie) ; pour le marathon, utiliser enregistrer_marathon."""
    st = lire_stats(); s = st[genre]
    s["parties"] += 1
    if victoire:
        s["victoires"] += 1; s["serie"] += 1
        s["repartition"][str(essais)] = s["repartition"].get(str(essais), 0) + 1
        s["meilleur_score"] = max(s["meilleur_score"], int(score))
    else: s["serie"] = 0
    s["meilleure_serie"] = max(s["meilleure_serie"], s["serie"])
    st["historique"] = ([{"d": datetime.date.today().isoformat(), "g": genre, "m": mot, "v": bool(victoire), "e": essais, "s": int(score), "x": detail}] + st["historique"])[:30]
    maj_config(stats=st); return st

def enregistrer_marathon(nb_mots, score, dernier_mot=""):
    st = lire_stats(); m = st["marathon"]
    m["parties"] += 1; m["mots"] += nb_mots
    nouveau = nb_mots > m["record"] or (nb_mots == m["record"] and score > m["record_score"])
    if nouveau: m["record"], m["record_score"] = nb_mots, int(score)
    st["historique"] = ([{"d": datetime.date.today().isoformat(), "g": "marathon", "m": dernier_mot, "v": nb_mots > 0, "e": nb_mots, "s": int(score), "x": ""}] + st["historique"])[:30]
    maj_config(stats=st); return nouveau

# ---------------------------------------------------------------- mode Chaîne (identique à smout.js)
def mots_chaine(liste_triee, graine, n=100):
    """Suite de mots où chaque mot commence par la dernière lettre du précédent (même suite sur PC et sur le web)."""
    initiales = {m[0] for m in liste_triee}
    jouables = [m for m in liste_triee if m[-1] in initiales] or liste_triee  # la chaîne ne doit jamais se bloquer
    par_lettre = {}
    for m in jouables: par_lettre.setdefault(m[0], []).append(m)
    mots = [mot_graine(jouables, graine, 0)]
    for i in range(1, n):
        mots.append(mot_graine(par_lettre.get(mots[-1][-1]) or jouables, graine, i))
    return mots


class TuileAction(tk.Canvas):
    """Grande tuile d'action colorée (ex. « Créer un salon », « Rejoindre un salon »)."""
    def __init__(self, parent, titre, sous_titre, commande, fond, texte, largeur=360, hauteur=112):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond_parent(parent), highlightthickness=0, cursor="hand2")
        self.args = (titre, sous_titre, fond, texte, largeur, hauteur); self.commande, self.survol = commande, False
        self.bind("<Enter>", lambda e=None: self._s(True)); self.bind("<Leave>", lambda e=None: self._s(False))
        self.bind("<ButtonRelease-1>", lambda e=None: self.commande())
        self._dessiner()
    def _s(self, v): self.survol = v; self._dessiner()
    def _dessiner(self):
        titre, st, fond, texte, l, h = self.args
        self.delete("all")
        arrondi(self, 1, 1, l - 1, h - 1, 18, fill=eclaircir(fond, 1.08) if self.survol else fond, outline="")
        self.create_text(22, h - 52, text=titre, anchor="w", fill=texte, font=police("titre", 24))
        self.create_text(22, h - 24, text=st, anchor="w", fill=melanger(texte, fond, 0.15), font=police("texte", 13))
