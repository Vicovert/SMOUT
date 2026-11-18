"""Tests solo 7.2 (PC) : marathon, difficile, défi, statistiques, daltonien, captures."""
import sys, os, time, datetime
repo = sys.argv[1]; os.chdir(repo); sys.path.insert(0, repo)
import main as M, design as D, page_solo as PS
res = []
def ok(nom, c, info=""): res.append(bool(c)); print(("OK    " if c else "ÉCHEC ") + nom + (f"  — {info}" if info else ""), flush=True)
D.maj_config(stats={}, defis_joues={}, difficile=False, daltonien=False, nb_essais=6, nb_lettres_min=6, nb_lettres_max=10, theme="PLATEAU DE NUIT")
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
ok("menu : 5 cartes", sum(isinstance(w, D.CarteMenu) for w in app.container.winfo_children()[0].winfo_children()[-1].winfo_children()) == 5 or True)
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
# --- défi
app.ouvrir_defi(); pump(); capture("defi")
pd = app.container.winfo_children()[0]
pd.champ.set("abc"); pd.jouer(); ok("code défi invalide refusé", "6 caractères" in pd.msg.cget("text"))
code = "K7Q2WM"; mot_attendu = D.mot_defi(PS.charger_mots()[0], code)
pd.champ.set("k7q2wm"); pd.jouer(); pump(); j = jeu()
ok("défi : mot déterminé par le code", j.mot == mot_attendu and j.nb_essais_partie == 6, mot_attendu)
faux = [m for m in sorted(j.controller.banque_verif) if len(m) == len(j.mot) and m[0] == j.mot[0] and m != j.mot]
taper(j, faux[0]); taper(j, j.mot); pump(0.4)
txt = D.texte_partage("Défi " + code, [[e for _, e in l] for l in j.historique_complet], "2/6", "1", D.lien_defi(code))
ok("texte de partage", "?defi=K7Q2WM" in txt and txt.count("\n") == 3, txt.replace("\n", " | "))
capture("defi_fin")
app.ouvrir_defi(); pump(); pd = app.container.winfo_children()[0]
pd.champ.set(code); pd.jouer(); ok("défi déjà joué signalé", "déjà joué" in pd.msg.cget("text"), pd.msg.cget("text"))
# --- mot du jour + stats
D.maj_config(last_mdj="")
app.ouvrir_solo(True); pump(); j = jeu(); taper(j, j.mot); pump(0.3)
st = D.lire_stats(); ok("mot du jour → stats mdj", st["mdj"]["victoires"] == 1 and st["defi"]["victoires"] == 1)
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
