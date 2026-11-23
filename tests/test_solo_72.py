"""Tests solo 7.2 (PC) : marathon, difficile, accueil et menu solo, statistiques, daltonien, captures."""
import sys, os, time, datetime, tkinter as tk

# diagnostic CI : quand un rappel Tkinter échoue, on affiche la fonction, les arguments et le widget (la trace seule n'indique pas qui l'a appelé)
import tkinter as _tkdiag
def _appel(self, *args):
    try:
        if self.subst: args = self.subst(*args)
        return self.func(*args)
    except SystemExit: raise
    except Exception as ex:
        print("RAPPEL TK EN ECHEC :", getattr(self.func, "__qualname__", self.func), "| args =", args, "| widget =", type(self.widget).__name__, getattr(self.widget, "_w", "?"), "|", ex, flush=True)
        self.widget._report_exception()
_tkdiag.CallWrapper.__call__ = _appel
repo = sys.argv[1]; os.chdir(repo); sys.path.insert(0, repo)
import main as M, design as D, page_solo as PS
res = []
def ok(nom, c, info=""): res.append(bool(c)); print(("OK    " if c else "ÉCHEC ") + nom + (f"  — {info}" if info else ""), flush=True)
D.maj_config(stats={}, difficile=False, daltonien=False, nb_essais=6, nb_lettres_min=6, nb_lettres_max=10, theme="PLATEAU DE NUIT")
app = M.MenuPrincipal(); app.geometry("1200x860")
def pump(t=0.3):
    end = time.time() + t
    while time.time() < end: app.update(); time.sleep(0.01)
def jeu(): return app.container.winfo_children()[0].jeu
def taper(j, mot):
    j.mot_tape = [j.mot[0]] + list(mot[1:]); j.valider(); pump(0.05)
def capture(nom):
    pump(0.4); os.system(f"import -window root /tmp/pc_{nom}.png 2>/dev/null")
pump(0.6); capture("accueil")
# --- solo libre + stats
app.ouvrir_solo(False); pump(); j = jeu(); mot = j.mot
taper(j, mot); pump(0.3)
st = D.lire_stats()
ok("solo gagné → stats solo", st["solo"]["parties"] == 1 and st["solo"]["victoires"] == 1 and st["solo"]["repartition"] == {"1": 1})
ok("historique", st["historique"][0]["m"] == mot)
# --- mode difficile
D.maj_config(difficile=True)
app.ouvrir_solo(False); pump(); j = jeu()
ok("titre difficile", j.controller.difficile)
faux = [m for m in sorted(j.controller.banque_verif) if len(m) == len(j.mot) and m[0] == j.mot[0] and m != j.mot]
# trouve un premier essai qui révèle au moins une lettre bien placée hors 1re
prem = next(m for m in faux if any(m[i] == j.mot[i] for i in range(1, len(m))))
taper(j, prem)
i_bien = next(i for i in range(1, len(prem)) if prem[i] == j.mot[i])
mauvais = next((m for m in faux if m[i_bien] != prem[i_bien]), None)
lg = j.ligne_actuelle; taper(j, mauvais)
ok("difficile : essai qui ignore une lettre bien placée refusé", j.ligne_actuelle == lg and "Mode difficile" in j.label_message.cget("text"), j.label_message.cget("text"))
taper(j, j.mot); pump(0.2); ok("difficile : bon mot accepté", j.fini_local)
D.maj_config(difficile=False)
# --- marathon
app.ouvrir_marathon(); pump(); j = jeu()
for k in range(3):
    taper(j, j.mot); pump(1.6); j = jeu()
ok("marathon : 3 mots enchaînés", j.controller.marathon["mots"] == 3, str(j.controller.marathon))
capture("marathon")
for w in sorted(j.controller.banque_verif):
    if j.fini_local: break
    if len(w) == len(j.mot) and w[0] == j.mot[0] and w != j.mot: taper(j, w)
pump(0.4); st = D.lire_stats()
ok("marathon terminé → record 3", st["marathon"]["record"] == 3 and st["marathon"]["parties"] == 1, str(st["marathon"]))
capture("marathon_fin")
app.creer_menu_accueil(); pump()
# --- accueil allégé + page intermédiaire du solo
def textes(w):
    out = []
    def rec(x):
        for c in x.winfo_children():
            if isinstance(c, tk.Canvas):
                for i in c.find_all():
                    if c.type(i) == "text": out.append(c.itemcget(i, "text"))
            rec(c)
    rec(w); return out
app.creer_menu_accueil(); pump(); t = textes(app.container)
ok("accueil : Solo, Mot du jour, Multijoueur seulement", all(x in t for x in ("Solo", "Mot du jour", "Multijoueur")) and not any(x in t for x in ("Marathon", "Défi entre amis")), str(t))
app.ouvrir_menu_solo(); pump(); t = textes(app.container); capture("menu_solo")
ok("menu solo : Jouer / Marathon / Paramètres", all(x in t for x in ("Jouer", "Marathon", "Paramètres")), str(t))
# --- mot du jour + stats
D.maj_config(last_mdj="")
app.ouvrir_solo(True); pump(); j = jeu(); taper(j, j.mot); pump(0.3)
st = D.lire_stats(); ok("mot du jour → stats mdj", st["mdj"]["victoires"] >= 1)
# --- mot du jour quitté en cours : la journée ne compte pas, on reprend avec ses essais
D.maj_config(last_mdj="", mdj_en_cours=None)
app.ouvrir_solo(True); pump(); j = jeu(); essai = [m for m in sorted(j.controller.banque_verif) if len(m) == len(j.mot) and m[0] == j.mot[0] and m != j.mot][0]; taper(j, essai); pump(0.3)
j.controller.retour_accueil(); pump(0.3)
ok("mot du jour quitté en cours : pas compté comme joué", D.serie_mot_du_jour()[1] is False and D.lire_config().get("last_mdj") != __import__("datetime").date.today().isoformat())
app.ouvrir_solo(True); pump(0.5); j = jeu()
ok("mot du jour repris avec son essai déjà fait", j.ligne_actuelle == 1 and "".join(c.cget("text") for c in j.grille_labels[0]) == essai and len(j.historique_complet) == 1)
taper(j, j.mot); pump(0.3)
ok("mot du jour terminé : plus rien à reprendre", not D.lire_config().get("mdj_en_cours"))
D.maj_config(last_mdj="")
app.ouvrir_solo(True); pump(); j = jeu(); taper(j, j.mot); pump(0.3)
app.ouvrir_stats(); pump(); capture("stats"); ok("écran statistiques", True)
# --- daltonien
app.ouvrir_parametres(); pump(); p = app.container.winfo_children()[0]
p.i_dalt.basculer(); p.save(); pump()
ok("daltonien : couleurs orange/bleu", D.P["bien"].upper() == "#F5793A" and D.P["mal"].upper() == "#85C0F9", D.P["bien"])
app.ouvrir_solo(False); pump(); j = jeu(); taper(j, [m for m in sorted(j.controller.banque_verif) if len(m) == len(j.mot) and m[0] == j.mot[0] and m != j.mot][0]); capture("daltonien")
app.ouvrir_parametres(); pump(); p = app.container.winfo_children()[0]; p.i_dalt.basculer(); p.save(); pump()
ok("daltonien désactivé", D.P["bien"].upper() != "#F5793A")
# fenêtre plus petite
app.geometry("1000x700"); pump(0.5); app.creer_menu_accueil(); pump(0.5); capture("accueil_petit")
print(f"{sum(res)}/{len(res)} conformes"); app.destroy()
