#!/usr/bin/env python3
"""Vérifie les scores d'un scénario croisé (rapports /tmp/sc/<nom>/r*.json) contre la règle du mode.
Usage : verif_scores.py <nom>. Affiche « ÉCHEC score … » si une règle n'est pas respectée (repéré par lancer_tests.sh)."""
import glob, json, sys

nom = sys.argv[1]
robots = [json.load(open(f)) for f in sorted(glob.glob(f"/tmp/sc/{nom}/r*.json"))]
avec = [r for r in robots if r.get("resultats")]


def parties():
    """Résultats de chaque partie, lus par l'hôte (premier robot) : il les lit avant de relancer « Rejouer », qui remet les scores à 0.
    Les autres joueurs peuvent lire plus tard, donc la cohérence entre joueurs n'est contrôlée que sur la dernière partie."""
    if not avec: return []
    hote = robots[0]
    if not hote.get("resultats"): echec("l'hôte n'a pas relevé de résultats")
    ref = hote["resultats"]
    for r in avec[1:]:
        if r["resultats"][-1] != ref[-1]: echec(f"les joueurs ne voient pas les mêmes scores finaux : {ref[-1]} / {r['resultats'][-1]}")
    return ref


def echec(msg):
    print(f"  ÉCHEC score {nom} : {msg}"); sys.exit(0)


def exact(*attendus):  # scores exacts, une partie après l'autre
    p = parties()
    if p != list(attendus): echec(f"attendu {list(attendus)}, obtenu {p}")


def rush():  # Chaîne / Rush : le score final est le total des mots trouvés par chaque joueur
    p = parties()
    if len(p) != 1: echec(f"une partie attendue, obtenu {p}")
    for r in avec:
        if p[0][r["nom"]] != sum(r.get("rush_trouves") or []): echec(f"{r['nom']} : score {p[0][r['nom']]} ≠ mots trouvés {r.get('rush_trouves')}")
    if not all(v > 0 for v in p[0].values()): echec(f"un score nul : {p[0]}")


def blast():  # chaque manche distribue 4 + 3 points aux deux premiers ; qui ne trouve pas marque 0
    p = parties()
    if len(p) != 1: echec(f"une partie attendue, obtenu {p}")
    s = p[0]
    if s.get("DAVID") != 0 or s.get("BOB", 0) + s.get("ALICE", 0) != 14: echec(f"Blast : {s}")


REGLES = {
    "c1": lambda: exact({"ALICE": 32, "BOB": 32}),      # Précision : 16 points par mot trouvé du 1er coup, 2 manches
    "c2": blast,
    "c3": lambda: exact({"BOB": 1, "ALICE": 1}, {"BOB": 1, "ALICE": 1}),
    "c4": lambda: exact({"ALICE": 1, "BOB": 0, "CHLOE": 2}),   # Élimination : 1 point par manche survécue
    "c5": lambda: exact({"BOB": 2, "ALICE": 2}),        # Coopératif : 1 point par manche trouvée pour tous
    "c6": rush,
    "c8": lambda: exact({"ALICE": 3, "BOB": 3}),
    "c9": lambda: exact({"BOB": 2, "ALICE": 2, "DAVID": 0}),   # Mystère : 1 point par mot trouvé
    "c10": lambda: exact({"ALICE": 0, "BOB": 2}),
    "c11": rush,
    "c12": rush,
    "c13": lambda: exact({"BOB": 32, "ALICE": 0}),
}
REGLES[nom]()
print(f"  scores conformes ({nom})")
