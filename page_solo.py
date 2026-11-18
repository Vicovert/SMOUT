import tkinter as tk
import json, random, os, sys, time, datetime
import design
from design import P, police, etiquette, espacer, Tuile, Bouton, Panneau, Icone, Clavier, Stat, Chips, Superposition, entete, fenetre_aide


def get_data_path(filename):
    return os.path.join(design.dossier_config(), filename)

def resource_path(relative_path):
    return design.resource_path(relative_path)

def nombre(n):
    """2450 -> « 2 450 » (espace fine insécable)."""
    return f"{int(n):,}".replace(",", " ")

# --- Couleurs du thème (mises à jour par apply_theme_solo) ---
BG = ACCENT1 = ACCENT2 = MUTED = KEY_BG = TXT1 = None
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def apply_theme_solo(theme_data):
    global BG, ACCENT1, ACCENT2, MUTED, KEY_BG, TXT1
    if not P: design.appliquer_theme(theme_data)
    BG, ACCENT1, ACCENT2, MUTED, KEY_BG, TXT1 = P["fond"], P["bien"], P["mal"], P["absent"], P["tuile"], P["texte"]


def charger_config_solo():
    config = {"nb_essais": 6, "nb_lettres_min": 6, "nb_lettres_max": 10, "last_mdj": ""}
    cfg = design.lire_config()
    for k in config:
        if k in cfg: config[k] = cfg[k]
    return config

def charger_mots():
    def lire(p):
        p = resource_path(p)
        if not os.path.exists(p): return []
        for enc in ['utf-8', 'latin-1']:
            try:
                with open(p, 'r', encoding=enc) as f: return [l.strip().upper() for l in f if l.strip()]
            except Exception: continue
        return []
    liste = lire('fichiers/mots_trouver.txt')
    return liste, set(lire('fichiers/banque_mots.txt')) or set(liste)


class EcranFin(tk.Frame):
    """Fin de partie solo : mot, résultat, statistiques, résumé de la grille."""
    def __init__(self, parent, rejouer_cmd, menu_cmd):
        super().__init__(parent, bg=P["fond"])
        self.rejouer_cmd, self.menu_cmd = rejouer_cmd, menu_cmd

    def afficher(self, victoire, mot, historique, score="0", temps="00:00", essais="", mdj=False):
        for w in self.winfo_children(): w.destroy()
        c = tk.Frame(self, bg=P["fond"]); c.place(relx=0.5, rely=0.46, anchor="center")
        etiquette(c, "Le mot était", "texte", 17, P["texte2"]).pack()
        tl = tk.Frame(c, bg=P["fond"]); tl.pack(pady=(10, 26))
        for ch in mot:
            t = Tuile(tl, 56); t.config(text=ch, bg=P["bien"] if victoire else P["absent"]); t.pack(side="left", padx=4)
        titre = ("Bravo, mot du jour trouvé !" if mdj else "Bravo, mot trouvé !") if victoire else "Perdu…"
        etiquette(c, titre, "titre", 52).pack()
        st = tk.Frame(c, bg=P["fond"]); st.pack(pady=26)
        for lib, val, coul in (("Temps", temps, None), ("Score", score if victoire else "0", P["mal"]), ("Essais", essais, None)):
            Stat(st, lib, val, coul, taille=34).pack(side="left", padx=34)
        if historique:
            g = tk.Frame(c, bg=P["fond"]); g.pack(pady=(0, 26))
            for ligne in historique:
                r = tk.Frame(g, bg=P["fond"]); r.pack(pady=2)
                for ch, coul in ligne:
                    t = Tuile(r, 22, mini=True); t.config(bg=coul); t.pack(side="left", padx=2)
        bf = tk.Frame(c, bg=P["fond"]); bf.pack()
        if not mdj: Bouton(bf, "Rejouer", self._rejouer, largeur=230, hauteur=54, taille=17).pack(side="left", padx=8)
        Bouton(bf, "Retour à l'accueil", self.menu_cmd, largeur=230, hauteur=54, variante="discret", taille=17).pack(side="left", padx=8)
        self.place(relx=0, rely=0, relwidth=1, relheight=1); self.tkraise()

    def _rejouer(self): self.place_forget(); self.rejouer_cmd()


class PageSolo(tk.Frame):
    def __init__(self, parent, controller, mdj=False):
        super().__init__(parent, bg=P["fond"])
        self.controller, self.mdj = controller, mdj
        self.config = charger_config_solo(); self.config["mdj"] = mdj
        self.liste_mots, self.banque_verif = charger_mots()
        self.jeu = PageJeu(self, self); self.jeu.pack(fill="both", expand=True)
        self.jeu.initialiser_partie()

    def sauver_parametres(self):
        design.maj_config(**{k: self.config[k] for k in ("nb_essais", "nb_lettres_min", "nb_lettres_max", "last_mdj")})

    def retour_accueil(self):
        self.jeu.timer_actif = False
        self.winfo_toplevel().unbind("<Key>")
        self.controller.creer_menu_accueil()


class PageJeu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller, self.timer_actif = controller, False
        self.timer_gen = 0

    def initialiser_partie(self):
        self.timer_actif = False
        for w in self.winfo_children(): w.destroy()
        conf, mots = self.controller.config, self.controller.liste_mots
        auj = datetime.datetime.now().strftime("%Y-%m-%d")
        if conf["mdj"]:
            if conf.get("last_mdj") == auj:
                entete(self, "Mot du jour", self.controller.retour_accueil)
                c = tk.Frame(self, bg=P["fond"]); c.place(relx=0.5, rely=0.45, anchor="center")
                etiquette(c, "Déjà joué aujourd'hui", "titre", 44).pack()
                serie, _ = design.serie_mot_du_jour()
                msg = (f"Série en cours : {serie} jour" + ("s" if serie > 1 else "") + ". ") if serie else ""
                etiquette(c, msg + "Revenez demain pour un nouveau mot.", "texte", 18, P["texte2"]).pack(pady=(10, 28))
                Bouton(c, "Retour à l'accueil", self.controller.retour_accueil, largeur=240, hauteur=52).pack()
                return
            self.mot = design.mot_graine(sorted(mots), "mdj:" + auj); self.nb_essais_partie = 7  # même mot sur PC et sur le web
            # la partie compte dès qu'elle commence (on ne peut plus la rejouer en fermant la fenêtre)
            conf["last_mdj"] = auj; self.controller.sauver_parametres()
        else:
            mi, ma = conf["nb_lettres_min"], conf["nb_lettres_max"]; filtre = [m for m in mots if mi <= len(m) <= ma]
            self.mot = random.choice(filtre if filtre else mots); self.nb_essais_partie = conf["nb_essais"]

        self.score_initial, self.penalite_dict, self.historique_complet, self.fini_local = (len(self.mot) * 100) * (13 - self.nb_essais_partie), 0, [], False
        self.statut_lettres = {l: None for l in ALPHABET}
        titre = ("Mot du jour" if conf["mdj"] else "Solo") + f" · {len(self.mot)} lettres"
        entete(self, titre, self.controller.retour_accueil, droite=lambda h: Icone(h, "aide", lambda: self.aide.montrer()))

        stats = tk.Frame(self, bg=P["fond"]); stats.pack(pady=(10, 0))
        self.s_temps = Stat(stats, "Temps", "00:00"); self.s_temps.pack(side="left", padx=40)
        self.s_score = Stat(stats, "Score", "0", P["mal"]); self.s_score.pack(side="left", padx=40)
        self.s_essai = Stat(stats, "Essai", "1"); self.s_essai.pack(side="left", padx=40)
        self.s_essai.set("1", suffixe=f" / {self.nb_essais_partie}")

        taille = self.taille_tuile()
        self.grid_frame = tk.Frame(self, bg=P["fond"]); self.grid_frame.pack(pady=(18, 0))
        self.ligne_actuelle, self.mot_tape, self.grille_labels = 0, [self.mot[0]], []
        for l in range(self.nb_essais_partie):
            ligne = []
            for c in range(len(self.mot)):
                case = Tuile(self.grid_frame, taille)
                case.grid(row=l, column=c, padx=4, pady=4); ligne.append(case)
            self.grille_labels.append(ligne)
        self.label_message = etiquette(self, "", "texte", 15, P["danger"], True); self.label_message.pack(pady=(8, 4))
        self.clavier = Clavier(self, self.ajouter_lettre, self.effacer, self.valider, hauteur=self.hauteur_touche()); self.clavier.pack(pady=(0, 16))
        lien = etiquette(self, "Abandonner", "texte", 14, P["texte2"], cursor="hand2"); lien.pack()
        lien.bind("<Button-1>", lambda e: self.gestion_fin("PERDU") if not self.fini_local else None)
        self.overlay_fin = EcranFin(self, self.initialiser_partie, self.controller.retour_accueil)
        self.aide = fenetre_aide(self)
        self.timer_gen = getattr(self, "timer_gen", 0) + 1
        self.debut_temps, self.timer_actif = time.time(), True; self.update_loop(self.timer_gen)
        self.winfo_toplevel().bind("<Key>", self.clavier_physique); self.maj_affichage()

    def hauteur_fenetre(self):
        try: h = self.winfo_toplevel().winfo_height()
        except Exception: h = 860
        return 860 if h < 200 else h

    def hauteur_touche(self):
        return 50 if self.hauteur_fenetre() >= 760 else 40

    def taille_tuile(self):
        h = self.hauteur_fenetre()
        dispo = h - 300 - 3 * (self.hauteur_touche() + 8)
        return int(max(30, min(58, dispo / self.nb_essais_partie - 8, 560 / len(self.mot) - 8)))

    def score_actuel(self, ecoule):
        return max(0, self.score_initial - (ecoule * 2) - self.penalite_dict)

    def update_loop(self, gen):
        if self.timer_actif and gen == self.timer_gen:
            ecoule = int(time.time() - self.debut_temps)
            self.s_temps.set(f"{ecoule // 60:02d}:{ecoule % 60:02d}")
            self.s_score.set(nombre(self.score_actuel(ecoule))); self.after(1000, lambda: self.update_loop(gen))

    def valider(self):
        if len(self.mot_tape) != len(self.mot) or self.fini_local: return
        tentative = "".join(self.mot_tape)
        if tentative not in self.controller.banque_verif and tentative != self.mot:
            self.penalite_dict += 100
            self.label_message.config(text="Mot inconnu  ·  −100 points")
            self.after(1400, lambda: self.label_message.config(text="") if not self.fini_local else None)
            return
        res, secret = [MUTED] * len(self.mot), list(self.mot)
        for i in range(len(self.mot)):
            if self.mot_tape[i] == self.mot[i]: res[i], secret[i] = ACCENT1, None
        for i in range(len(self.mot)):
            if res[i] != ACCENT1 and self.mot_tape[i] in secret: res[i] = ACCENT2; secret[secret.index(self.mot_tape[i])] = None
        for i, char in enumerate(self.mot_tape):
            cur = self.statut_lettres.get(char)
            if res[i] == ACCENT1: self.statut_lettres[char] = ACCENT1
            elif res[i] == ACCENT2 and cur != ACCENT1: self.statut_lettres[char] = ACCENT2
            elif res[i] == MUTED and cur not in [ACCENT1, ACCENT2]: self.statut_lettres[char] = MUTED
        self.maj_clavier(); self.historique_complet.append([(self.mot_tape[i], res[i]) for i in range(len(self.mot))])
        for i, color in enumerate(res): self.grille_labels[self.ligne_actuelle][i].config(bg=color)
        for case in self.grille_labels[self.ligne_actuelle]: case.set_curseur(False)
        if tentative == self.mot: self.fini_local = True; self.gestion_fin("VICTOIRE")
        elif self.ligne_actuelle + 1 >= self.nb_essais_partie: self.fini_local = True; self.gestion_fin("PERDU")
        else:
            self.ligne_actuelle += 1; self.mot_tape = [self.mot[0]]
            self.s_essai.set(str(self.ligne_actuelle + 1)); self.maj_affichage()

    def gestion_fin(self, statut):
        victoire = statut == "VICTOIRE"
        ecoule = int(time.time() - self.debut_temps)
        self.timer_actif = False; self.fini_local = True; self.winfo_toplevel().unbind("<Key>")
        if self.controller.config["mdj"]:
            self.controller.config["last_mdj"] = datetime.datetime.now().strftime("%Y-%m-%d")
            self.controller.sauver_parametres()
            design.enregistrer_resultat_mdj(victoire)
        essais = f"{self.ligne_actuelle + 1} / {self.nb_essais_partie}" if victoire else f"– / {self.nb_essais_partie}"
        self.overlay_fin.afficher(victoire, self.mot, self.historique_complet, nombre(self.score_actuel(ecoule)),
                                  f"{ecoule // 60:02d}:{ecoule % 60:02d}", essais, self.controller.config["mdj"])

    def maj_clavier(self):
        for char, color in self.statut_lettres.items(): self.clavier.set_couleur(char, color)

    def clavier_physique(self, e):
        if not self.winfo_viewable() or self.fini_local: return
        c = e.char.upper()
        if c and c in ALPHABET: self.ajouter_lettre(c)
        elif e.keysym == "BackSpace": self.effacer()
        elif e.keysym in ("Return", "KP_Enter"): self.valider()

    def ajouter_lettre(self, c):
        if len(self.mot_tape) < len(self.mot) and not self.fini_local:
            self.mot_tape.append(c); self.maj_affichage()

    def effacer(self):
        if self.fini_local: return
        if len(self.mot_tape) > 1: self.mot_tape.pop()
        self.maj_affichage()

    def maj_affichage(self):
        if self.fini_local: return
        ligne = self.grille_labels[self.ligne_actuelle]
        for i, case in enumerate(ligne):
            if i < len(self.mot_tape):
                case.config(text=self.mot_tape[i], bg=ACCENT1 if i == 0 else BG)
            else:
                case.config(text="", bg=BG)
            case.set_curseur(i == len(self.mot_tape))


class PageParametres(tk.Frame):
    """Réglages de la partie solo (ouverts depuis l'icône engrenage de l'accueil)."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        self.config = charger_config_solo()
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", controller.creer_menu_accueil).pack(side="left")
        corps = tk.Frame(self, bg=P["fond"]); corps.pack(padx=90, anchor="w")
        etiquette(corps, "Paramètres", "titre", 46).pack(anchor="w", pady=(0, 6))
        etiquette(corps, "Réglages des parties solo (le mot du jour se joue toujours en 7 essais).", "texte", 16, P["texte2"]).pack(anchor="w", pady=(0, 24))
        p = Panneau(corps, padding=30, largeur=620); p.pack(anchor="w")
        i = p.interieur
        etiquette(i, "Nombre d'essais", "texte", 17, gras=True).pack(anchor="w")
        self.c_essais = Chips(i, range(4, 9), self.config["nb_essais"]); self.c_essais.pack(anchor="w", pady=(10, 22))
        etiquette(i, "Longueur minimale des mots", "texte", 17, gras=True).pack(anchor="w")
        self.c_min = Chips(i, range(6, 11), self.config["nb_lettres_min"], self._min); self.c_min.pack(anchor="w", pady=(10, 22))
        etiquette(i, "Longueur maximale des mots", "texte", 17, gras=True).pack(anchor="w")
        self.c_max = Chips(i, range(6, 11), self.config["nb_lettres_max"], self._max); self.c_max.pack(anchor="w", pady=(10, 26))
        self.btn = Bouton(i, "Enregistrer", self.save, largeur=560, hauteur=54, taille=17); self.btn.pack()

    def _min(self, v):
        if v > self.c_max.get(): self.c_max.set_valeur(v)
    def _max(self, v):
        if v < self.c_min.get(): self.c_min.set_valeur(v)

    def save(self):
        design.maj_config(nb_essais=self.c_essais.get(), nb_lettres_min=self.c_min.get(), nb_lettres_max=self.c_max.get())
        self.controller.creer_menu_accueil()
