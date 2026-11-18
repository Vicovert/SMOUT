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
    shutil.copytree(os.path.join(RACINE, "web"), sortie, dirs_exist_ok=True)
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
        "url_web": valeur_ast("design.py", "URL_WEB"),
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
    # Service worker (jeu installable et solo hors ligne) : liste des fichiers + empreinte du contenu pour forcer la mise à jour
    import hashlib
    fichiers, empreinte = [], hashlib.sha256()
    for d, _, fs in sorted(os.walk(sortie)):
        for f in sorted(fs):
            chemin = os.path.relpath(os.path.join(d, f), sortie).replace(os.sep, "/")
            if chemin in ("sw.js", ".nojekyll") or chemin.endswith((".ico", ".txt")) and "LICENCE" in chemin: continue
            fichiers.append(chemin); empreinte.update(chemin.encode()); empreinte.update(open(os.path.join(d, f), "rb").read())
    cache = f"smout-{donnees['version']}-{empreinte.hexdigest()[:10]}"
    with open(os.path.join(sortie, "sw.js"), "w", encoding="utf-8") as f:
        f.write(SW.replace("__CACHE__", cache).replace("__FICHIERS__", json.dumps(["./"] + [x for x in fichiers if x != "index.html"])))
    print("Version web construite dans", sortie, "- version", donnees["version"], "-", len(donnees["themes"]), "thèmes")

SW = """// Généré par outils/export_web.py : met le jeu en cache pour qu'il s'ouvre sans connexion (le multijoueur, lui, a besoin d'internet).
const CACHE = "__CACHE__";
const FICHIERS = __FICHIERS__;
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FICHIERS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(n => n !== CACHE).map(n => caches.delete(n)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;  // Firebase et connexion : toujours en ligne
  const page = e.request.mode === "navigate";
  // pages : réseau d'abord (dernière version), cache si hors ligne ; fichiers : cache d'abord
  e.respondWith(page
    ? fetch(e.request).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put("./", c)); return r; }).catch(() => caches.match("./"))
    : caches.match(e.request, { ignoreSearch: true }).then(r => r || fetch(e.request)));
});
"""

if __name__ == "__main__":
    construire(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RACINE, "_site"))
