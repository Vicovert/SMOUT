import sys, os, time
repo = sys.argv[1]; os.chdir(repo); sys.path.insert(0, repo)
import main as M, design as D
app = M.MenuPrincipal()
def pump(t=0.3):
    end = time.time() + t
    while time.time() < end: app.update(); time.sleep(0.01)
pump(0.5)
# solo libre : mot inconnu puis victoire au clavier physique
app.ouvrir_solo(False); pump(); j = app.container.winfo_children()[0].jeu
for ch in "Z" * (len(j.mot) - 1): j.ajouter_lettre(ch)
j.valider(); print("Mot inconnu pénalisé :", j.penalite_dict == 100, "| message :", j.label_message.cget("text"))
for _ in range(len(j.mot)): j.effacer()
print("Effacer garde la 1re lettre :", j.mot_tape == [j.mot[0]])
class E: pass
for ch in j.mot[1:]:
    e = E(); e.char = ch.lower(); e.keysym = ch.lower(); j.clavier_physique(e)
e = E(); e.char = "\r"; e.keysym = "Return"; j.clavier_physique(e); pump(0.5)
print("Victoire au clavier physique :", j.fini_local and j.overlay_fin.winfo_ismapped())
# mot du jour
D.maj_config(last_mdj="", mdj_serie=3, mdj_dernier_gagne=(__import__("datetime").date.today() - __import__("datetime").timedelta(days=1)).isoformat())
app.ouvrir_solo(True); pump(); j = app.container.winfo_children()[0].jeu
print("Mot du jour en 7 essais :", j.nb_essais_partie == 7, "| pas marqué joué avant d'avoir vu le mot :", D.lire_config().get("last_mdj") != __import__("datetime").date.today().isoformat())
j.mot_tape = list(j.mot); j.valider(); pump(0.3)
print("Série après victoire (3 → 4) :", D.serie_mot_du_jour())
app.creer_menu_accueil(); pump()
app.ouvrir_solo(True); pump(); j = app.container.winfo_children()[0].jeu
print("Rejouer le mot du jour bloqué :", not hasattr(j, "grille_labels") or not j.timer_actif)
# paramètres
app.ouvrir_parametres(); pump(); p = app.container.winfo_children()[0]
p.c_lettres.set_valeur(7, 7); print("Plage de lettres :", p.c_lettres.get())
p.save(); print("Paramètres enregistrés :", {k: D.lire_config()[k] for k in ("nb_essais", "nb_lettres_min", "nb_lettres_max")})
app.ouvrir_solo(False); pump(); j = app.container.winfo_children()[0].jeu
print("Longueur respectée :", 7 <= len(j.mot) <= 7, len(j.mot))
# thème perso
app.show_custom_creator(); pump(); c = app.container.winfo_children()[0]
c.select_prop("accent1"); c.hex_var.set("#00aa55"); c.nom_champ.set("MON TEST"); c.save(); pump()
print("Thème perso créé et appliqué :", app.current_theme_name == "MON TEST", D.P["bien"])
print("Sauvegardé dans la config :", "MON TEST" in D.lire_config().get("custom_themes", {}))
# thème perso portant le nom d'un thème intégré (bug 7.0)
import tkinter.messagebox as mb; avert = []; mb.showwarning = lambda *a, **k: avert.append(a)
app.show_custom_creator(); pump()
pc = [w for w in app.container.winfo_children() if hasattr(w, "save")]
if pc:
    pc[0].nom_champ.set("Plateau de nuit") if hasattr(pc[0].nom_champ, "set") else (pc[0].nom_champ.delete(0, "end"), pc[0].nom_champ.insert(0, "Plateau de nuit"))
    pc[0].save(); pump()
    print("Nom de thème intégré refusé :", M.THEMES["PLATEAU DE NUIT"].get("type") != "PERSO" and len(avert) == 1)
else: print("Créateur de thème introuvable pour le test")
D.maj_config(custom_themes={"PLATEAU DE NUIT": {"bg": "#000000", "type": "PERSO"}}, theme="PLATEAU DE NUIT")
app.charger_themes_personnalises()
print("Ancien thème perso homonyme renommé :", M.THEMES["PLATEAU DE NUIT"].get("type") != "PERSO" and "PLATEAU DE NUIT PERSO" in M.THEMES)

app.destroy()