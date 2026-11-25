"""Classements (9.4) côté PC : même logique que l'objet Classements de web/smout.js.
classements/mdj/<uid> = {pseudo, meilleure, actuelle, maj} ; classements/marathon/<uid> = {pseudo, record, maj}.
Seuls les comptes y écrivent (leur ligne) ; tout le monde lit."""
import os, threading, tkinter as tk
import design, compte, amis
import datetime
from design import P, police, etiquette, Panneau, Avatar, arrondi, melanger

SV = {".sv": "timestamp"}
ENVOYE = {}


def moyenne_mdj(s):
    """9.8 : moyenne d'essais au mot du jour (raté = 8), arrondie au centième ; None si aucune partie (identique à moyenneMdj du site)."""
    total = trouves = 0
    for e, c in (s.get("repartition") or {}).items(): total += int(e) * int(c); trouves += int(c)
    rates = max(0, int(s.get("parties") or 0) - int(s.get("victoires") or 0)); n = trouves + rates  # parties connues seulement
    return int((total + rates * 8) / n * 100 + 0.5) / 100 if n else None


def detail_marathon(d):
    """9.10 : mots et réglages de la meilleure partie de marathon, tels qu'envoyés à la base (identique à detailMarathon du site)."""
    if not isinstance(d, dict) or not isinstance(d.get("mots"), (int, float)): return {}
    n = lambda x, a, b: max(a, min(b, int(x or a)))
    return {"mots": n(d["mots"], 0, 500), "essais": n(d.get("essais"), 4, 8), "lmin": n(d.get("lmin"), 6, 10), "lmax": n(d.get("lmax"), 6, 10), "difficile": bool(d.get("difficile"))}


def texte_reglages(d):
    if not d: return ""
    lg = str(d["lmin"]) if d["lmin"] == d["lmax"] else f"{d['lmin']}–{d['lmax']}"
    return f"{d['essais']} essais · {lg} lettres" + (" · difficile" if d.get("difficile") else "")


def lire(type_):
    d = amis.lire(f"classements/{type_}") or {}
    auj = datetime.date.today().isoformat()
    l = [{"uid": u, "pseudo": v.get("pseudo") or "?", "valeur": int(v.get("meilleure" if type_ == "mdj" else "score") or 0), "actuelle": int(v.get("actuelle") or 0),
          "jour": max(0, int(v.get("essais") or 0)) if v.get("jour") == auj else None,
          "moy": v["moyenne"] if isinstance(v.get("moyenne"), (int, float)) and v["moyenne"] > 0 else None,
          "det": {"mots": v["mots"], "essais": v.get("essais"), "lmin": v.get("lmin"), "lmax": v.get("lmax"), "difficile": bool(v.get("difficile"))}
                 if type_ == "marathon" and isinstance(v.get("mots"), (int, float)) else None}  # 9.10  # 9.6 : essais du mot du jour d'aujourd'hui (0 = raté, None = pas joué)
         for u, v in d.items() if isinstance(v, dict)]
    # 9.8 : égalité de série → moyenne d'essais la plus basse
    return sorted([e for e in l if e["valeur"] > 0], key=lambda e: (-e["valeur"], e["moy"] if e["moy"] is not None else 9, str(e["pseudo"]).lower()))


def pousser():
    """Nos valeurs (compte seulement), quand elles ont changé."""
    if not compte.email() or not compte.auth().jeton(): return
    st = design.lire_stats(); serie = design.serie_mot_du_jour()[0]; m = max(st["mdj"].get("meilleure_serie", 0), serie)
    ps = amis.pseudo(); u = amis.uid()
    auj = datetime.date.today().isoformat()  # 9.6 : résultat du jour (depuis les stats)
    dj = next((x for x in st["historique"] if x.get("g") == "mdj" and x.get("d") == auj), None) if design.lire_config().get("last_mdj") == auj else None
    jour = {"jour": auj, "essais": min(8, int(dj.get("e") or 1)) if dj.get("v") else 0} if dj else {}
    moy = moyenne_mdj(st["mdj"])
    if moy: jour["moyenne"] = moy  # 9.8 : moyenne d'essais (raté = 8)
    lignes = {"mdj": dict({"pseudo": ps, "meilleure": m, "actuelle": min(serie, m), "maj": SV}, **jour) if (m > 0 or dj) else None,
              "marathon": dict({"pseudo": ps, "record": min(500, st["marathon"].get("record", 0)), "score": min(10000000, st["marathon"].get("meilleur_points", 0)), "maj": SV},
                               **detail_marathon(st["marathon"].get("meilleur_detail")))
                          if st["marathon"].get("meilleur_points", 0) > 0 else None}  # 9.7 : marathon en points (nouveau calcul, repart de zéro)
    for t, l in lignes.items():
        if not l: continue
        sig = repr(sorted((k, v) for k, v in l.items() if k != "maj"))
        if ENVOYE.get(t) == sig: continue
        if amis.ok("put", f"classements/{t}/{u}", l): ENVOYE[t] = sig; continue
        if t == "mdj":  # série montée trop vite pour la base (autre appareil) : on envoie le maximum permis
            srv = amis.lire(f"classements/mdj/{u}") or {}
            jours = int((amis.maintenant_ms() - (srv.get("maj") or 0)) // 86400000)
            l["meilleure"] = min(l["meilleure"], int(srv.get("meilleure") or 0) + 1 + jours); l["actuelle"] = min(l["actuelle"], l["meilleure"])
            if amis.ok("put", f"classements/mdj/{u}", l): ENVOYE[t] = sig


class PanneauClassement(tk.Frame):
    """« Top 5 + ma place » ; toucher une ligne ouvre la fiche du joueur. live (marathon en cours) : mon score actuel."""
    def __init__(self, parent, type_, live=None, largeur=300, on_fiche=None):
        super().__init__(parent, bg=P["fond"])
        self.type, self.live, self.on_fiche, self.l = type_, live, on_fiche, largeur
        self.p = Panneau(self, padding=14, rayon=16, contour=P["bordure"], largeur=largeur); self.p.pack()
        t = tk.Frame(self.p.interieur, bg=P["panneau"]); t.pack(fill="x")
        etiquette(t, "Mot du jour" if type_ == "mdj" else "Marathon", "texte", 15, P["texte"], True).pack(side="left")
        etiquette(t, "en direct" if live is not None else ("meilleure série" if type_ == "mdj" else "meilleur score"), "texte", 11, P["texte2"], True).pack(side="right")
        self.deux = type_ == "mdj" and live is None  # 9.6 : colonnes « série max » (pastille 🔥) et « aujourd'hui » (pastille de couleur)
        if self.deux:
            etiq = t.winfo_children()[-1]; etiq.pack_forget()
            tt = tk.Frame(self.p.interieur, bg=P["panneau"]); tt.pack(fill="x", pady=(4, 0))
            etiquette(tt, "aujourd'hui", "texte", 11, P["texte2"], True, width=11, anchor="e").pack(side="right", padx=(0, 4))
            etiquette(tt, "moy. essais", "texte", 11, P["texte2"], True, width=11, anchor="e").pack(side="right")
            etiquette(tt, "série max", "texte", 11, P["texte2"], True, width=9, anchor="e").pack(side="right")
        self.mar = type_ == "marathon" and live is None  # 9.10 : 2 lignes (pseudo puis réglages), colonnes « mots » et « meilleur »
        if self.mar:
            t.winfo_children()[-1].pack_forget()
            tt = tk.Frame(self.p.interieur, bg=P["panneau"]); tt.pack(fill="x", pady=(4, 0))
            etiquette(tt, "meilleur", "texte", 11, P["texte2"], True, width=9, anchor="e").pack(side="right", padx=(0, 4))
            etiquette(tt, "mots", "texte", 11, P["texte2"], True, width=5, anchor="e").pack(side="right")
        self.corps = tk.Frame(self.p.interieur, bg=P["panneau"]); self.corps.pack(fill="x", pady=(6, 0))
        etiquette(self.corps, "Chargement…", "texte", 12, P["texte2"]).pack(anchor="w")
        self.note = etiquette(self.p.interieur, "", "texte", 11, P["texte2"], wraplength=largeur - 30, justify="left"); self.note.pack(anchor="w", pady=(6, 0))
        self.res, self.fait = None, threading.Event()
        threading.Thread(target=self._charger, daemon=True).start(); self.after(150, self._attendre)

    def _charger(self):
        try:
            pousser(); self.res = lire(self.type)
        except Exception: self.res = None
        self.fait.set()

    def _attendre(self):
        try:
            if not self.winfo_exists(): return
        except tk.TclError: return
        if self.fait.is_set(): self.remplir()
        else: self.after(150, self._attendre)

    def remplir(self):
        for w in self.corps.winfo_children(): w.destroy()
        if self.res is None: etiquette(self.corps, "Hors ligne", "texte", 12, P["texte2"]).pack(anchor="w"); return
        l = list(self.res); moi = amis.uid() if compte.email() else None
        if self.live is not None:
            l = [e for e in l if e["uid"] != moi] + [{"uid": moi, "pseudo": amis.pseudo(), "valeur": self.live, "vivant": True}]
            l.sort(key=lambda e: (-e["valeur"], 0 if e.get("vivant") else 1))
        rang = lambda i: 1 + next(k for k, e in enumerate(l) if e["valeur"] == l[i]["valeur"] and (not self.deux or e.get("moy") == l[i].get("moy")))  # ex aequo : même rang
        i = next((k for k, e in enumerate(l) if (e.get("vivant") if self.live is not None else (moi and e["uid"] == moi))), -1)
        if not l: etiquette(self.corps, "Personne pour le moment.", "texte", 12, P["texte2"]).pack(anchor="w")
        def ligne(parent, k):
            e, est_moi = l[k], k == i
            f = tk.Frame(parent, bg=P["tuile"] if est_moi else P["panneau"], cursor="hand2")
            etiquette(f, str(rang(k)), "chiffres", 13, P["mal"] if rang(k) == 1 else P["texte2"]).pack(side="left", padx=(6, 8))
            Avatar(f, e["pseudo"], 22, index=k).pack(side="left")
            if self.mar:
                nm = tk.Frame(f, bg=f["bg"]); nm.pack(side="left", padx=8)
                etiquette(nm, str(e["pseudo"]).capitalize(), "texte", 13, P["texte"], True).pack(anchor="w")
                etiquette(nm, texte_reglages(e.get("det")), "texte", 10, P["texte2"], True).pack(anchor="w")
            else: etiquette(f, "Toi" if (est_moi and self.live is not None) else str(e["pseudo"]).capitalize(), "texte", 13, P["texte"], True).pack(side="left", padx=8)
            if self.deux:
                j = e.get("jour")
                txt, coul = ("pas joué", P["texte2"]) if j is None else ((f"{j} essai" + ("s" if j > 1 else ""), P["succes"]) if j > 0 else ("raté", P["danger"]))
                puce(f, txt, coul, 92, gras=j is not None).pack(side="right", padx=(4, 2))
                m = e.get("moy")  # 9.8 : vert ≤ 3,5, jaune ≤ 4,5, rouge au-delà
                mc = P["texte2"] if m is None else P["succes"] if m <= 3.5 else P["mal"] if m <= 4.5 else P["danger"]
                puce(f, "–" if m is None else f"{m:.1f}".replace(".", ","), mc, 64, gras=m is not None).pack(side="right", padx=4)
                puce(f, str(e["valeur"]), P["mal"], 64, flamme=True).pack(side="right", padx=4)
            elif self.mar:
                puce(f, design.nombre(e["valeur"]), P["mal"], 78).pack(side="right", padx=(4, 2))
                puce(f, str(e["det"]["mots"]) if e.get("det") else "–", P["texte"], 48).pack(side="right", padx=4)
            else: etiquette(f, design.nombre(e["valeur"]), "chiffres", 13, P["mal"]).pack(side="right", padx=6)
            if e.get("uid") and self.on_fiche:
                for w in [f] + f.winfo_children() + [x for c in f.winfo_children() for x in c.winfo_children()]: w.bind("<Button-1>", lambda ev, u=e["uid"]: self.on_fiche(u))
            return f
        if l:
            # 9.8 : tout le classement, 5 lignes visibles, le reste en faisant défiler ; ma ligne reste visible
            # (collée en bas si ma place est plus bas, en haut si on a défilé plus loin), comme position: sticky sur le site
            HL = 42 if self.mar else 28
            zone = design.Defilant(self.corps, hauteur=min(5, len(l)) * HL); zone.pack(fill="x")
            lignes = []
            for k in range(len(l)):
                f = ligne(zone.interieur, k); f.configure(height=HL - 2); f.pack_propagate(False); f.pack(fill="x", pady=1); lignes.append(f)
            if i >= 0 and len(l) > 5:
                epingle = ligne(zone, i); epingle.configure(height=HL - 2); epingle.pack_propagate(False)
                cv = zone.canvas
                def suivre(premier, dernier):
                    try:
                        haut = float(premier) * zone.interieur.winfo_height(); vue = cv.winfo_height()
                        y = lignes[i].winfo_y()
                        if y < haut: epingle.place(x=0, y=0, relwidth=1)
                        elif y + HL - 2 > haut + vue: epingle.place(x=0, rely=1, y=-(HL - 2), relwidth=1)
                        else: epingle.place_forget()
                    except tk.TclError: pass
                cv.configure(yscrollcommand=suivre)
                self.after(50, lambda: suivre(*cv.yview()))
        if self.live is not None:
            devant = l[i - 1] if i > 0 else None
            self.note.config(text=f"Encore {design.nombre(devant['valeur'] - self.live + 1)} pts pour dépasser {str(devant['pseudo']).capitalize()}" if devant else "Tu es en tête !")
        elif not compte.email(): self.note.config(text="Crée un compte pour apparaître dans le classement.")
        elif self.type == "mdj": self.note.config(text="")  # 9.6 : « Ta série en cours » retirée (doublon avec le tableau)
        else: self.note.config(text="")  # 9.6 : « Ton record » retiré (doublon avec le tableau)


_FLAMME = {}


def image_flamme():
    """9.6 : le 🔥 en couleur (Tk n'affiche les émojis qu'en noir et blanc)."""
    if "img" not in _FLAMME:
        try: _FLAMME["img"] = tk.PhotoImage(file=design.resource_path(os.path.join("fichiers", "flamme14.png")))
        except Exception: _FLAMME["img"] = None
    return _FLAMME["img"]


def puce(parent, texte, couleur, largeur, gras=True, flamme=False):
    """9.6 : pastille arrondie (fond teinté de la couleur, texte de la couleur), calée à droite dans une colonne de largeur fixe."""
    import tkinter.font as tkfont
    fond = parent["bg"]; f = police("chiffres", 12, gras); h = 24
    c = tk.Canvas(parent, width=largeur, height=h, bg=fond, highlightthickness=0, bd=0)
    img = image_flamme() if flamme else None
    if flamme and not img: texte = "🔥 " + texte
    tw = tkfont.Font(font=f).measure(texte) + 18 + (18 if img else 0); x2 = largeur - 1; x1 = max(0, x2 - tw)
    arrondi(c, x1, 1, x2, h - 1, 11, fill=melanger(fond, couleur, 0.18), outline="")
    if img: c.create_image(x1 + 9, h / 2, image=img, anchor="w"); c.create_text(x1 + 9 + 18, h / 2, text=texte, font=f, fill=couleur, anchor="w")
    else: c.create_text((x1 + x2) / 2, h / 2, text=texte, font=f, fill=couleur)
    return c


def fiche_joueur(fenetre, uid):
    """Fiche joueur : ancienneté, meilleure série, record marathon ; « Ajouter en ami » (comme ficheJoueur du site)."""
    import datetime
    pr, cm, cr = amis.lire(f"profils/{uid}") or {}, amis.lire(f"classements/mdj/{uid}") or {}, amis.lire(f"classements/marathon/{uid}") or {}
    nom = str(pr.get("pseudo") or cm.get("pseudo") or cr.get("pseudo") or "?").capitalize()
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    depuis = None
    if pr.get("cree"):
        d = datetime.datetime.fromtimestamp(pr["cree"] / 1000); depuis = f"{mois[d.month - 1]} {d.year}"
    o = design.Superposition(getattr(fenetre, "container", fenetre), largeur=420); i = o.interieur  # (dans la page : fermée avec elle)
    Avatar(i, nom, 64, index=3).pack()
    etiquette(i, nom, "titre", 26).pack(pady=(8, 0))
    etiquette(i, f"Joueur depuis {depuis}" if depuis else "Ancienneté inconnue", "texte", 14, P["texte2"]).pack()
    st = tk.Frame(i, bg=i["bg"]); st.pack(pady=(10, 6))
    design.Stat(st, "Meilleure série", str(cm.get("meilleure") or 0), P["mal"], 28).pack(side="left", padx=14)
    design.Stat(st, "Record marathon", design.nombre(cr.get("score") or 0), P["mal"], 28).pack(side="left", padx=14)
    msg = etiquette(i, "", "texte", 13, P["succes"], True); msg.pack()
    bf = tk.Frame(i, bg=i["bg"]); bf.pack(pady=(8, 0))
    design.Bouton(bf, "Fermer", o.destroy, largeur=120, hauteur=44, variante="discret", taille=14).pack(side="left")
    if uid != amis.uid() and compte.email() and uid not in amis.E["liste"]:
        def ajouter():
            msg.config(text="Demande envoyée ✓" if amis.ok("put", f"amis_demandes/{uid}/{amis.uid()}", {"pseudo": amis.pseudo(), "t": SV}) else "Connexion au serveur impossible.")
        design.Bouton(bf, "Ajouter en ami", ajouter, largeur=180, hauteur=44, taille=14).pack(side="left", padx=(10, 0))
    o.montrer(); o.fiche = True
    return o
