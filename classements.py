"""Classements (9.4) côté PC : même logique que l'objet Classements de web/smout.js.
classements/mdj/<uid> = {pseudo, meilleure, actuelle, maj} ; classements/marathon/<uid> = {pseudo, record, maj}.
Seuls les comptes y écrivent (leur ligne) ; tout le monde lit."""
import threading, tkinter as tk
import design, compte, amis
from design import P, police, etiquette, Panneau, Avatar

SV = {".sv": "timestamp"}
ENVOYE = {}


def lire(type_):
    d = amis.lire(f"classements/{type_}") or {}
    l = [{"uid": u, "pseudo": v.get("pseudo") or "?", "valeur": int(v.get("meilleure" if type_ == "mdj" else "record") or 0), "actuelle": int(v.get("actuelle") or 0)}
         for u, v in d.items() if isinstance(v, dict)]
    return sorted([e for e in l if e["valeur"] > 0], key=lambda e: (-e["valeur"], str(e["pseudo"])))


def pousser():
    """Nos valeurs (compte seulement), quand elles ont changé."""
    if not compte.email() or not compte.auth().jeton(): return
    st = design.lire_stats(); serie = design.serie_mot_du_jour()[0]; m = max(st["mdj"].get("meilleure_serie", 0), serie)
    ps = amis.pseudo(); u = amis.uid()
    lignes = {"mdj": {"pseudo": ps, "meilleure": m, "actuelle": min(serie, m), "maj": SV} if m > 0 else None,
              "marathon": {"pseudo": ps, "record": min(500, st["marathon"].get("record", 0)), "maj": SV} if st["marathon"].get("record", 0) > 0 else None}
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
        etiquette(t, "en direct" if live is not None else ("meilleure série" if type_ == "mdj" else "record de mots"), "texte", 11, P["texte2"], True).pack(side="right")
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
        rang = lambda i: 1 + next(k for k, e in enumerate(l) if e["valeur"] == l[i]["valeur"])  # ex aequo : même rang
        i = next((k for k, e in enumerate(l) if (e.get("vivant") if self.live is not None else (moi and e["uid"] == moi))), -1)
        a_montrer = list(range(min(5, len(l))))
        if i >= 5: a_montrer.append(-1); a_montrer.append(i)
        if not l: etiquette(self.corps, "Personne pour le moment.", "texte", 12, P["texte2"]).pack(anchor="w")
        for k in a_montrer:
            if k == -1: etiquette(self.corps, "···", "texte", 11, P["texte2"]).pack(); continue
            e, est_moi = l[k], k == i
            f = tk.Frame(self.corps, bg=P["tuile"] if est_moi else P["panneau"], cursor="hand2"); f.pack(fill="x", pady=1)
            etiquette(f, str(rang(k)), "chiffres", 13, P["mal"] if rang(k) == 1 else P["texte2"]).pack(side="left", padx=(6, 8))
            Avatar(f, e["pseudo"], 22, index=k).pack(side="left")
            etiquette(f, "Toi" if (est_moi and self.live is not None) else str(e["pseudo"]).capitalize(), "texte", 13, P["texte"], True).pack(side="left", padx=8)
            etiquette(f, str(e["valeur"]), "chiffres", 13, P["mal"]).pack(side="right", padx=6)
            if e.get("uid") and self.on_fiche:
                for w in [f] + f.winfo_children(): w.bind("<Button-1>", lambda ev, u=e["uid"]: self.on_fiche(u))
        if self.live is not None:
            devant = l[i - 1] if i > 0 else None
            self.note.config(text=f"Encore {devant['valeur'] - self.live + 1} mots pour dépasser {str(devant['pseudo']).capitalize()}" if devant else "Tu es en tête !")
        elif not compte.email(): self.note.config(text="Crée un compte pour apparaître dans le classement.")
        elif self.type == "mdj":
            s = design.serie_mot_du_jour()[0]; self.note.config(text=f"🔥 Ta série en cours : {s} jour{'s' if s > 1 else ''}" if s else "")
        else:
            r = design.lire_stats()["marathon"].get("record", 0); self.note.config(text=f"Ton record : {r} mots" if r else "")


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
    design.Stat(st, "Record marathon", str(cr.get("record") or 0), P["mal"], 28).pack(side="left", padx=14)
    msg = etiquette(i, "", "texte", 13, P["succes"], True); msg.pack()
    bf = tk.Frame(i, bg=i["bg"]); bf.pack(pady=(8, 0))
    design.Bouton(bf, "Fermer", o.destroy, largeur=120, hauteur=44, variante="discret", taille=14).pack(side="left")
    if uid != amis.uid() and compte.email() and uid not in amis.E["liste"]:
        def ajouter():
            msg.config(text="Demande envoyée ✓" if amis.ok("put", f"amis_demandes/{uid}/{amis.uid()}", {"pseudo": amis.pseudo(), "t": SV}) else "Connexion au serveur impossible.")
        design.Bouton(bf, "Ajouter en ami", ajouter, largeur=180, hauteur=44, taille=14).pack(side="left", padx=(10, 0))
    o.montrer(); o.fiche = True
    return o
