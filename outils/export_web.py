"""Construit la version web dans le dossier donné (par défaut _site) : pages, thèmes et version tirés du code PC."""
import ast, json, os, shutil, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def valeur_ast(fichier, nom):
    arbre = ast.parse(open(os.path.join(RACINE, fichier), encoding="utf-8").read())
    for n in arbre.body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == nom for t in n.targets):
            return ast.literal_eval(n.value)
    raise KeyError(nom)

def construire(sortie):
    os.makedirs(sortie, exist_ok=True)
    for f in os.listdir(os.path.join(RACINE, "web")):
        shutil.copy2(os.path.join(RACINE, "web", f), os.path.join(sortie, f))
    os.makedirs(os.path.join(sortie, "fichiers", "polices"), exist_ok=True)
    for f in ("mots_trouver.txt", "banque_mots.txt"):
        shutil.copy2(os.path.join(RACINE, "fichiers", f), os.path.join(sortie, "fichiers", f))
    for f in os.listdir(os.path.join(RACINE, "fichiers", "polices")):
        shutil.copy2(os.path.join(RACINE, "fichiers", "polices", f), os.path.join(sortie, "fichiers", "polices", f))
    for f in ("logo.ico", "logo.png"):
        p = os.path.join(RACINE, "fichiers", f)
        if os.path.exists(p): shutil.copy2(p, os.path.join(sortie, "fichiers", f))
    donnees = {
        "version": valeur_ast("design.py", "VERSION_APP"),
        "themes": valeur_ast("main.py", "THEMES"),
        "categories": valeur_ast("design.py", "THEMES_CAT_LIB"),
        "ordre_categories": valeur_ast("main.py", "ORDRE_CATEGORIES"),
        "noms_themes": valeur_ast("design.py", "NOMS_THEMES"),
        "theme_defaut": valeur_ast("main.py", "THEME_PAR_DEFAUT"),
    }
    with open(os.path.join(sortie, "donnees.js"), "w", encoding="utf-8") as f:
        f.write("// Généré automatiquement depuis le code PC (outils/export_web.py) : ne pas modifier à la main.\n")
        f.write("window.SMOUT_DONNEES = " + json.dumps(donnees, ensure_ascii=False) + ";\n")
    open(os.path.join(sortie, ".nojekyll"), "w").close()
    print("Version web construite dans", sortie, "- version", donnees["version"], "-", len(donnees["themes"]), "thèmes")

if __name__ == "__main__":
    construire(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RACINE, "_site"))
