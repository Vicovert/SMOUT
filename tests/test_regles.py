import json, urllib.request, time
B = "http://127.0.0.1:9000/"
def req(m, path, tok=None, data=None):
    u = B + path + ".json" + (f"?auth={tok}" if tok else "")
    r = urllib.request.Request(u, method=m, data=None if data is None else json.dumps(data).encode())
    try: return urllib.request.urlopen(r).status
    except urllib.error.HTTPError as e: return e.code
def signup(): return json.load(urllib.request.urlopen(urllib.request.Request(B + "signup", method="POST", data=b"{}")))["idToken"]
A, Bt, C = signup(), signup(), signup(); ua, ub, uc = A[4:], Bt[4:], C[4:]
SV = {".sv": "timestamp"}
ok = []
def t(nom, obt, att): ok.append(obt == att); print(("OK   " if obt == att else "ÉCHEC"), nom, obt, "attendu", att)
reglages = {"essais": 8, "min": 6, "max": 7, "rounds": 3, "timer": 180, "host_id": ua, "visible": True, "version": "7.0", "game_mode": "CLASSIQUE"}
t("lecture sans connexion", req("GET", "v7/index"), 401)
t("liste de tous les salons", req("GET", "v7/lobbies", A), 401)
t("secret écrit avant le salon", req("PUT", "v7/secrets/1234", A, "abc123"), 200)
t("lecture du secret interdite", req("GET", "v7/secrets/1234", Bt), 401)
t("création du salon", req("PUT", "v7/lobbies/1234", A, {"status": "waiting", "maj": SV, "settings": reglages, "players": {ua: {"name": "A", "score": 0, "last_seen": SV, "preuve": "abc123"}}}), 200)
t("autre joueur ne lit pas un salon dont il n'est pas membre", req("GET", "v7/lobbies/1234", Bt), 401)
t("rejoindre sans preuve refusé", req("PUT", f"v7/lobbies/1234/players/{ub}", Bt, {"name": "B", "score": 0, "last_seen": SV}), 401)
t("rejoindre avec mauvaise preuve refusé", req("PUT", f"v7/lobbies/1234/players/{ub}", Bt, {"name": "B", "score": 0, "last_seen": SV, "preuve": "faux"}), 401)
t("rejoindre avec la bonne preuve", req("PUT", f"v7/lobbies/1234/players/{ub}", Bt, {"name": "B", "score": 0, "last_seen": SV, "preuve": "abc123"}), 200)
t("membre lit le salon", req("GET", "v7/lobbies/1234", Bt), 200)
t("écraser le secret d'un salon existant (non hôte)", req("PUT", "v7/secrets/1234", Bt, "pirate"), 401)
t("modifier le score d'un autre", req("PATCH", f"v7/lobbies/1234/players/{ua}", Bt, {"score": 99}), 401)
t("heartbeat multi-chemins", req("PATCH", "v7/lobbies/1234", Bt, {"maj": SV, f"players/{ub}/last_seen": SV, f"players/{ub}/name": "B", f"players/{ub}/score": 0}), 200)
t("paramètres par non-hôte", req("PATCH", "v7/lobbies/1234/settings", Bt, {"rounds": 9}), 401)
t("voler l'hôte actif", req("PATCH", "v7/lobbies/1234/settings", Bt, {"host_id": ub}), 401)
t("supprimer un salon actif", req("DELETE", "v7/lobbies/1234", C), 401)
t("grille d'un autre", req("PUT", f"v7/lobbies/1234/match_data/{ua}/0", Bt, {"c": ["B"]}), 401)
t("sa propre grille", req("PUT", f"v7/lobbies/1234/match_data/{ub}/0", Bt, {"c": ["B"]}), 200)
t("l'hôte relance (PUT du salon)", req("PUT", "v7/lobbies/1234", A, {"status": "waiting", "maj": SV, "settings": reglages, "players": {ua: {"name": "A", "score": 0, "last_seen": SV}, ub: {"name": "B", "score": 0, "last_seen": SV}}}), 200)
t("annonce index", req("PATCH", "v7/index/1234", A, {"owner": ua, "hote": "A", "nb": 2, "prive": True, "visible": True, "status": "waiting", "version": "7.0", "maj": SV}), 200)
t("écraser l'annonce d'un autre", req("PATCH", "v7/index/1234", Bt, {"owner": ub, "maj": SV, "version": "7.0"}), 401)
urllib.request.urlopen(urllib.request.Request(B + "__vieillir?ms=30000", method="POST"))
t("reprise d'hôte après 30 s sans signe de vie", req("PATCH", "v7/lobbies/1234/settings", Bt, {"host_id": ub}), 200)
t("retrait d'un joueur inactif", req("DELETE", f"v7/lobbies/1234/players/{ua}", Bt), 200)
t("supprimer le salon encore actif (B dedans, maj < 2 min)", req("DELETE", "v7/lobbies/1234", C), 401)
urllib.request.urlopen(urllib.request.Request(B + "__vieillir?ms=130000", method="POST"))
t("supprimer le salon abandonné (> 2 min)", req("DELETE", "v7/lobbies/1234", C), 200)
t("supprimer son secret ensuite", req("DELETE", "v7/secrets/1234", C), 200)
t("supprimer l'annonce périmée", req("DELETE", "v7/index/1234", C), 200)
t("code non numérique refusé", req("PUT", "v7/lobbies/abcd", A, {"status": "waiting", "settings": dict(reglages), "players": {ua: {"name": "A", "score": 0}}}), 401)
print(f"{sum(ok)}/{len(ok)} conformes")
