import tkinter as tk
import json, random, os, sys, time, datetime
import design
from design import (P, police, etiquette, espacer, Tuile, Bouton, Panneau, Icone, Clavier, Stat, Chips, Superposition, entete, fenetre_aide,
                    Champ, Interrupteur, CarteMenu, Curseur, melanger)


def get_data_path(filename):
    return os.path.join(design.dossier_config(), filename)

def resource_path(relative_path):
    return design.resource_path(relative_path)

def nombre(n):
    """2450 -> « 2 450 » (espace fine insécable)."""
    return f"{int(n):,}".replace(",", " ")

def mmss(s): return f"{int(s) // 60:02d}:{int(s) % 60:02d}"

# --- Couleurs du thème (mises à jour par apply_theme_solo) ---
BG = ACCENT1 = ACCENT2 = MUTED = KEY_BG = TXT1 = None
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def apply_theme_solo(theme_data):
    global BG, ACCENT1, ACCENT2, MUTED, KEY_BG, TXT1
    if not P: design.appliquer_theme(theme_data)
    BG, ACCENT1, ACCENT2, MUTED, KEY_BG, TXT1 = P["fond"], P["bien"], P["mal"], P["absent"], P["tuile"], P["texte"]


def charger_config_solo():
    config = {"nb_essais": 6, "nb_lettres_min": 6, "nb_lettres_max": 10, "last_mdj": "", "difficile": False}
    cfg = design.lire_config()
    for k in config:
        if k in cfg: config[k] = cfg[k]
    return config

_MOTS = None
def charger_mots():
    global _MOTS
    if _MOTS: return _MOTS
    def lire(p):
        p = resource_path(p)
        if not os.path.exists(p): return []
        for enc in ['utf-8', 'latin-1']:
            try:
                with open(p, 'r', encoding=enc) as f: return [l.strip().upper() for l in f if l.strip()]
            except Exception: continue
        return []
    liste = lire('fichiers/mots_trouver.txt')
    _MOTS = (liste, set(lire('fichiers/banque_mots.txt')) or set(liste))
    return _MOTS

TITRES = {"libre": "Solo", "mdj": "Mot du jour", "marathon": "Marathon"}


class EcranFin(tk.Frame):
    """Fin de partie solo : mot, résultat, statistiques, résumé de la grille, partage."""
    def __init__(self, parent, rejouer_cmd, menu_cmd):
        super().__init__(parent, bg=P["fond"])
        self.rejouer_cmd, self.menu_cmd = rejouer_cmd, menu_cmd

    def afficher(self, victoire, mot, historique, titre, stats, rejouer=True, partage=None, note=None):
        """historique = [[(lettre, etat)]] ; stats = [(libellé, valeur, couleur)] ; partage = texte à copier."""
        for w in self.winfo_children(): w.destroy()
        c = tk.Frame(self, bg=P["fond"]); c.place(relx=0.5, rely=0.46, anchor="center")
        etiquette(c, "Le mot était", "texte", 17, P["texte2"]).pack()
        tl = tk.Frame(c, bg=P["fond"]); tl.pack(pady=(10, 22))
        t_tuile = max(30, min(56, 640 // max(1, len(mot)) - 8))
        for ch in mot:
            t = Tuile(tl, t_tuile); t.config(text=ch, bg=P["bien"] if victoire else P["absent"]); t.pack(side="left", padx=4)
        etiquette(c, titre, "titre", 46).pack()
        if note: etiquette(c, note, "texte", 17, P["texte2"]).pack(pady=(6, 0))
        st = tk.Frame(c, bg=P["fond"]); st.pack(pady=22)
        for lib, val, coul in stats: Stat(st, lib, val, coul, taille=34).pack(side="left", padx=30)
        if historique:
            g = tk.Frame(c, bg=P["fond"]); g.pack(pady=(0, 22))
            for ligne in historique[-8:]:
                r = tk.Frame(g, bg=P["fond"]); r.pack(pady=2)
                for ch, etat in ligne:
                    t = Tuile(r, 22, mini=True); t.config(bg=P[etat]); t.pack(side="left", padx=2)
        self.msg = etiquette(c, "", "texte", 14, P["succes"], True); self.msg.pack(pady=(0, 6))
        bf = tk.Frame(c, bg=P["fond"]); bf.pack()
        if rejouer: Bouton(bf, "Rejouer", self._rejouer, largeur=210, hauteur=54, taille=17).pack(side="left", padx=8)
        if partage: Bouton(bf, "Copier le résultat", lambda: self._copier(partage), largeur=230, hauteur=54, taille=17, variante="secondaire").pack(side="left", padx=8)
        Bouton(bf, "Retour", self.menu_cmd, largeur=230, hauteur=54, variante="discret", taille=17).pack(side="left", padx=8)
        self.place(relx=0, rely=0, relwidth=1, relheight=1); self.tkraise()

    def _copier(self, texte):
        try:
            self.clipboard_clear(); self.clipboard_append(texte); self.msg.config(text="Résultat copié ✓ — colle-le à tes amis")
        except tk.TclError: self.msg.config(text=texte)

    def _rejouer(self): self.place_forget(); self.rejouer_cmd()


class PageSolo(tk.Frame):
    """mode : libre, mdj, marathon."""
    def __init__(self, parent, controller, mdj=False, mode=None):
        super().__init__(parent, bg=P["fond"])
        self.controller, self.mode = controller, mode or ("mdj" if mdj else "libre")
        self.mdj = self.mode == "mdj"
        self.config = charger_config_solo(); self.config["mdj"] = self.mdj
        self.difficile = bool(self.config.get("difficile")) and self.mode != "mdj"
        self.liste_mots, self.banque_verif = charger_mots()
        self.marathon = {"mots": 0, "score": 0, "temps": 0}
        self.jeu = PageJeu(self, self); self.jeu.pack(fill="both", expand=True)
        self.jeu.initialiser_partie()

    def sauver_parametres(self):
        design.maj_config(**{k: self.config[k] for k in ("nb_essais", "nb_lettres_min", "nb_lettres_max", "last_mdj")})

    def nouvelle_partie(self):
        """« Rejouer » : nouveau mot (libre) ou nouveau marathon."""
        if self.mode == "marathon": self.marathon = {"mots": 0, "score": 0, "temps": 0}
        self.jeu.initialiser_partie()

    def retour_accueil(self):
        self.jeu.timer_actif = False
        self.winfo_toplevel().unbind("<Key>")
        if self.mode == "mdj": self.controller.creer_menu_accueil()
        else: self.controller.ouvrir_menu_solo()


class PageJeu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller, self.timer_actif = controller, False
        self.timer_gen = 0

    def initialiser_partie(self):
        self.timer_actif = False
        for w in self.winfo_children(): w.destroy()
        ctl = self.controller; conf, mots, mode = ctl.config, ctl.liste_mots, ctl.mode
        auj = datetime.date.today().isoformat()
        if mode == "mdj":
            if conf.get("last_mdj") == auj:
                entete(self, "Mot du jour", ctl.retour_accueil)
                c = tk.Frame(self, bg=P["fond"]); c.place(relx=0.5, rely=0.45, anchor="center")
                etiquette(c, "Déjà joué aujourd'hui", "titre", 44).pack()
                serie, _ = design.serie_mot_du_jour()
                msg = (f"Série en cours : {serie} jour" + ("s" if serie > 1 else "") + ". ") if serie else ""
                etiquette(c, msg + "Revenez demain pour un nouveau mot.", "texte", 18, P["texte2"]).pack(pady=(10, 28))
                Bouton(c, "Retour à l'accueil", ctl.retour_accueil, largeur=240, hauteur=52).pack()
                return
            self.mot = design.mot_graine(sorted(mots), "mdj:" + auj); self.nb_essais_partie = 7  # même mot sur PC et sur le web
            # la partie compte dès qu'elle commence (on ne peut plus la rejouer en fermant la fenêtre)
            conf["last_mdj"] = auj; ctl.sauver_parametres()
        else:
            mi, ma = conf["nb_lettres_min"], conf["nb_lettres_max"]; filtre = [m for m in mots if mi <= len(m) <= ma]
            self.mot = random.choice(filtre if filtre else mots); self.nb_essais_partie = conf["nb_essais"]

        self.score_initial, self.penalite_dict, self.historique_complet, self.fini_local = (len(self.mot) * 100) * (13 - self.nb_essais_partie), 0, [], False
        self.statut_lettres = {l: None for l in ALPHABET}
        titre = TITRES[mode] + (f" · mot {ctl.marathon['mots'] + 1}" if mode == "marathon" else "") \
            + f" · {len(self.mot)} lettres" + (" · difficile" if ctl.difficile else "")
        entete(self, titre, ctl.retour_accueil, droite=lambda h: Icone(h, "aide", lambda: self.aide.montrer()))

        stats = tk.Frame(self, bg=P["fond"]); stats.pack(pady=(10, 0))
        self.s_temps = Stat(stats, "Temps", "00:00"); self.s_temps.pack(side="left", padx=40)
        self.s_score = Stat(stats, "Score", "0", P["mal"]); self.s_score.pack(side="left", padx=40)
        self.s_essai = Stat(stats, "Essai", "1"); self.s_essai.pack(side="left", padx=40)
        self.s_essai.set("1", suffixe=f" / {self.nb_essais_partie}")
        if mode == "marathon":
            self.s_total = Stat(stats, "Total", nombre(ctl.marathon["score"]), P["bien"]); self.s_total.pack(side="left", padx=40)

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
        self.overlay_fin = EcranFin(self, ctl.nouvelle_partie, ctl.retour_accueil)
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
            self.s_temps.set(mmss(ecoule))
            self.s_score.set(nombre(self.score_actuel(ecoule))); self.after(1000, lambda: self.update_loop(gen))

    def message(self, texte, couleur=None, duree=1600):
        self.label_message.config(text=texte, fg=couleur or P["danger"])
        self.after(duree, lambda: self.label_message.config(text="") if not self.fini_local and self.label_message.cget("text") == texte else None)

    def valider(self):
        if len(self.mot_tape) != len(self.mot) or self.fini_local: return
        tentative = "".join(self.mot_tape)
        if tentative not in self.controller.banque_verif and tentative != self.mot:
            self.penalite_dict += 100
            self.message("Mot inconnu  ·  −100 points"); return
        if self.controller.difficile:
            err = design.verifier_difficile(self.mot_tape, [("".join(ch for ch, _ in l), [e for _, e in l]) for l in self.historique_complet])
            if err: self.message(err, duree=2200); return
        res = design.evaluer(self.mot_tape, self.mot)
        for i, char in enumerate(self.mot_tape):
            cur = self.statut_lettres.get(char)
            if res[i] == "bien": self.statut_lettres[char] = "bien"
            elif res[i] == "mal" and cur != "bien": self.statut_lettres[char] = "mal"
            elif res[i] == "absent" and cur not in ("bien", "mal"): self.statut_lettres[char] = "absent"
        self.maj_clavier(); self.historique_complet.append([(self.mot_tape[i], res[i]) for i in range(len(self.mot))])
        for i, etat in enumerate(res): self.grille_labels[self.ligne_actuelle][i].config(bg=P[etat])
        for case in self.grille_labels[self.ligne_actuelle]: case.set_curseur(False)
        if tentative == self.mot: self.fini_local = True; self.gestion_fin("VICTOIRE")
        elif self.ligne_actuelle + 1 >= self.nb_essais_partie: self.fini_local = True; self.gestion_fin("PERDU")
        else:
            self.ligne_actuelle += 1; self.mot_tape = [self.mot[0]]
            self.s_essai.set(str(self.ligne_actuelle + 1)); self.maj_affichage()

    def gestion_fin(self, statut):
        ctl = self.controller; mode = ctl.mode
        victoire = statut == "VICTOIRE"
        ecoule = int(time.time() - self.debut_temps)
        score = self.score_actuel(ecoule) if victoire else 0
        self.timer_actif = False; self.fini_local = True
        essais_n = self.ligne_actuelle + 1
        etats = [[e for _, e in l] for l in self.historique_complet]
        if mode == "marathon":
            ctl.marathon["temps"] += ecoule
            if victoire:  # mot suivant
                ctl.marathon["mots"] += 1; ctl.marathon["score"] += score
                self.s_total.set(nombre(ctl.marathon["score"]))
                self.label_message.config(text=f"Trouvé ! +{nombre(score)} pts · mot suivant…", fg=P["succes"])
                self.after(1300, lambda: self.initialiser_partie() if self.winfo_exists() else None)
                return
            self.winfo_toplevel().unbind("<Key>")
            m = ctl.marathon; ancien = design.lire_stats()["marathon"]["record"]
            record = design.enregistrer_marathon(m["mots"], m["score"], self.mot)
            note = "Nouveau record !" if record and m["mots"] else f"Record : {max(ancien, m['mots'])} mot" + ("s" if max(ancien, m["mots"]) > 1 else "")
            partage = f"SMOUT · Marathon · {m['mots']} mot{'s' if m['mots'] > 1 else ''} · {nombre(m['score'])} pts" + (" · difficile" if ctl.difficile else "") + f"\n{design.URL_WEB}"
            self.overlay_fin.afficher(False, self.mot, self.historique_complet, "Marathon terminé",
                                      [("Mots trouvés", str(m["mots"]), None), ("Score total", nombre(m["score"]), P["mal"]), ("Temps", mmss(m["temps"]), None)],
                                      partage=partage, note=note)
            return
        self.winfo_toplevel().unbind("<Key>")
        if mode == "mdj":
            ctl.config["last_mdj"] = datetime.date.today().isoformat(); ctl.sauver_parametres()
            design.enregistrer_resultat_mdj(victoire)
        essais_txt = f"{essais_n} / {self.nb_essais_partie}" if victoire else f"– / {self.nb_essais_partie}"
        design.enregistrer_partie({"libre": "solo", "mdj": "mdj"}[mode], victoire, essais_n, score, self.mot)
        partage = None
        if mode == "mdj":
            t = f"Mot du jour {datetime.date.today().strftime('%d/%m')}"
            if ctl.difficile: t += " (difficile)"
            partage = design.texte_partage(t, etats, essais_txt.replace(" ", ""), nombre(score), design.URL_WEB)
        titre = ("Bravo, mot du jour trouvé !" if mode == "mdj" else "Bravo, mot trouvé !") if victoire else "Perdu…"
        self.overlay_fin.afficher(victoire, self.mot, self.historique_complet, titre,
                                  [("Temps", mmss(ecoule), None), ("Score", nombre(score), P["mal"]), ("Essais", essais_txt, None)],
                                  rejouer=mode != "mdj", partage=partage)

    def maj_clavier(self):
        for char, etat in self.statut_lettres.items(): self.clavier.set_couleur(char, P[etat] if etat else None)

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


COULEUR_MARATHON = "#A78BFA"  # couleur propre au Marathon (même que COULEUR_MARATHON de smout.js)

def resume_reglages(c):
    mn, mx = c["nb_lettres_min"], c["nb_lettres_max"]
    longueur = f"{mn} lettres" if mn == mx else f"{mn} à {mx} lettres"
    return f"{c['nb_essais']} essais · {longueur}" + (" · difficile" if c.get("difficile") else "")


class PageMenuSolo(tk.Frame):
    """Page intermédiaire du solo : titre en tuiles, grand bouton « Jouer », puis Marathon et Paramètres (chacun avec son icône)."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        entete(self, "", controller.creer_menu_accueil)
        rec = design.lire_stats()["marathon"]["record"]
        centre = tk.Frame(self, bg=P["fond"]); centre.place(relx=0.5, rely=0.46, anchor="center")
        titre = tk.Frame(centre, bg=P["fond"]); titre.pack(pady=(0, 4))
        for ch, e in zip("SOLO", ("bien", "mal", "bien", "mal")):
            t = Tuile(titre, 60); t.config(text=ch, bg=P[e]); t.pack(side="left", padx=4)
        etiquette(centre, "À votre rythme", "texte", 18, P["texte2"]).pack(pady=(6, 14))
        CarteMenu(centre, "Jouer", "Partie normale · un mot, à votre rythme", lambda: controller.ouvrir_solo(False), largeur=796, hauteur=170,
                  couleur=P["bien"], texte=P["sur_bien"], degrade=melanger(P["bien"], P["mal"], 0.45), icone="jouer", rond=True, grand=True).pack()
        ligne = tk.Frame(centre, bg=P["fond"]); ligne.pack(pady=(14, 0))
        CarteMenu(ligne, "Marathon", f"Record {rec}" if rec else "Jusqu'à l'erreur", controller.ouvrir_marathon, largeur=390, hauteur=96,
                  couleur=COULEUR_MARATHON, texte="#14182A", icone="infini").pack(side="left", padx=(0, 16))
        CarteMenu(ligne, "Paramètres", resume_reglages(charger_config_solo()), controller.ouvrir_parametres, largeur=390, hauteur=96,
                  icone="engrenage", fond_icone=melanger(P["panneau"], P["texte"], 0.08)).pack(side="left")


class PageStats(tk.Frame):
    """Statistiques enregistrées sur cet appareil."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        st = design.lire_stats()
        entete(self, "", controller.creer_menu_accueil)
        c = tk.Frame(self, bg=P["fond"]); c.pack(pady=(0, 0), padx=60, fill="x")
        etiquette(c, "Statistiques", "titre", 46).pack(anchor="w", pady=(0, 16))
        haut = tk.Frame(c, bg=P["fond"]); haut.pack(anchor="w")
        for col, (cle, nom) in enumerate((("solo", "Solo"), ("mdj", "Mot du jour"))):
            s = st[cle]; p = Panneau(haut, padding=20, largeur=330); p.grid(row=0, column=col, padx=(0, 16), sticky="n")
            i = p.interieur
            etiquette(i, nom, "texte", 18, gras=True).pack(anchor="w")
            l = tk.Frame(i, bg=i["bg"]); l.pack(anchor="w", pady=(8, 10))
            taux = round(100 * s["victoires"] / s["parties"]) if s["parties"] else 0
            for k, (lib, v) in enumerate((("Parties", s["parties"]), ("Réussite", f"{taux} %"), ("Série", s["serie"]), ("Max", s["meilleure_serie"]))):
                Stat(l, lib, str(v), taille=22).grid(row=0, column=k, padx=(0, 14))
            rep = s["repartition"]; mx = max([1] + list(rep.values()))
            for n in range(1, 9):
                v = rep.get(str(n), 0)
                if n > 7 and not v: continue
                r = tk.Frame(i, bg=i["bg"]); r.pack(anchor="w", pady=1)
                etiquette(r, str(n), "chiffres", 13, P["texte2"], width=2).pack(side="left")
                w = 18 + int(200 * v / mx)
                b = tk.Canvas(r, width=w + 30, height=20, bg=i["bg"], highlightthickness=0); b.pack(side="left")
                design.arrondi(b, 0, 1, w, 19, 5, fill=P["bien"] if v and v == mx else P["tuile"], outline="")
                b.create_text(w - 6, 10, text=str(v), anchor="e", fill=P["sur_bien"] if v and v == mx else P["texte"], font=police("chiffres", 11))
        bas = tk.Frame(c, bg=P["fond"]); bas.pack(anchor="w", pady=16)
        m = st["marathon"]; p = Panneau(haut, padding=20, largeur=330); p.grid(row=0, column=2, sticky="n")
        i = p.interieur
        etiquette(i, "Marathon", "texte", 18, gras=True).pack(anchor="w")
        l = tk.Frame(i, bg=i["bg"]); l.pack(anchor="w", pady=(8, 0))
        for k, (lib, v) in enumerate((("Record", m["record"]), ("Meilleur score", nombre(m["record_score"])), ("Parties", m["parties"]))):
            Stat(l, lib, str(v), taille=22).grid(row=0, column=k, padx=(0, 14))
        p = Panneau(bas, padding=20, largeur=1022); p.grid(row=0, column=0, sticky="n")
        i = p.interieur
        etiquette(i, "Dernières parties", "texte", 18, gras=True).pack(anchor="w", pady=(0, 6))
        if not st["historique"]: etiquette(i, "Aucune partie pour le moment.", "texte", 15, P["texte2"]).pack(anchor="w")
        tab = tk.Frame(i, bg=i["bg"]); tab.pack(anchor="w")
        for r, h in enumerate(st["historique"][:7]):
            g = TITRES.get({"solo": "libre"}.get(h["g"], h["g"]), h["g"])
            if h["g"] == "marathon": res = f"{h['e']} mot" + ("s" if h["e"] > 1 else "")
            else: res = f"{h['e']} essai" + ("s" if h["e"] > 1 else "") if h["v"] else "perdu"
            coul = P["texte"] if h["v"] else P["texte2"]
            for col, (txt, role) in enumerate(((f"{h['d'][8:10]}/{h['d'][5:7]}", "chiffres"), (g, "texte"), (h["m"], "chiffres"), (res, "texte"), (f"{nombre(h['s'])} pts", "chiffres"))):
                etiquette(tab, txt, role, 13, coul).grid(row=r, column=col, sticky="e" if col == 4 else "w", padx=(0, 18), pady=1)


class PageParametres(tk.Frame):
    """Réglages (ouverts depuis l'icône engrenage de l'accueil)."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=P["fond"]); self.controller = controller
        self.config = charger_config_solo()
        h = tk.Frame(self, bg=P["fond"]); h.pack(fill="x", padx=28, pady=(18, 0))
        Icone(h, "retour", controller.ouvrir_menu_solo).pack(side="left")
        corps = tk.Frame(self, bg=P["fond"]); corps.pack(padx=90, anchor="w")
        etiquette(corps, "Paramètres", "titre", 46).pack(anchor="w", pady=(0, 6))
        etiquette(corps, "Réglages des parties normales et du marathon (le mot du jour se joue toujours en 7 essais).", "texte", 16, P["texte2"]).pack(anchor="w", pady=(0, 18))
        p = Panneau(corps, padding=26, largeur=620); p.pack(anchor="w")
        i = p.interieur
        etiquette(i, "Nombre d'essais", "texte", 17, gras=True).pack(anchor="w")
        self.c_essais = Curseur(i, 4, 8, self.config["nb_essais"], 1, largeur=560); self.c_essais.pack(anchor="w", pady=(4, 14))
        etiquette(i, "Longueur des mots", "texte", 17, gras=True).pack(anchor="w")
        self.c_lettres = Curseur(i, 6, 10, (self.config["nb_lettres_min"], self.config["nb_lettres_max"]), 1, largeur=560, plage=True); self.c_lettres.pack(anchor="w", pady=(4, 14))
        self.i_diff = Interrupteur(i, "Mode difficile (lettres trouvées obligatoires)", bool(self.config.get("difficile")), largeur=560); self.i_diff.pack(anchor="w", pady=(0, 6))
        self.i_dalt = Interrupteur(i, "Mode daltonien (orange et bleu)", bool(design.lire_config().get("daltonien")), largeur=560); self.i_dalt.pack(anchor="w", pady=(0, 18))
        self.btn = Bouton(i, "Enregistrer", self.save, largeur=560, hauteur=54, taille=17); self.btn.pack()


    def save(self):
        changement = bool(design.lire_config().get("daltonien")) != self.i_dalt.valeur
        design.maj_config(nb_essais=self.c_essais.get(), nb_lettres_min=self.c_lettres.get()[0], nb_lettres_max=self.c_lettres.get()[1],
                          difficile=self.i_diff.valeur, daltonien=self.i_dalt.valeur)
        if changement and hasattr(self.controller, "apply_theme"): self.controller.apply_theme(self.controller.current_theme_name, save=False)
        self.controller.ouvrir_menu_solo()
