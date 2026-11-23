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


def elimination():  # BOB est éliminé d'emblée (0) ; entre les deux autres, le plus lent sort avant l'autre : 1 et 2, dans un ordre ou dans l'autre
    p = parties()
    if len(p) != 1: echec(f"une partie attendue, obtenu {p}")
    s = p[0]
    if s.get("BOB") != 0 or sorted(s.values()) != [0, 1, 2]: echec(f"Élimination : {s}")


def blast():  # chaque manche distribue 4 + 3 points aux deux premiers ; qui ne trouve pas marque 0
    p = parties()
    if len(p) != 1: echec(f"une partie attendue, obtenu {p}")
    s = p[0]
    if s.get("DAVID") != 0 or s.get("BOB", 0) + s.get("ALICE", 0) != 14: echec(f"Blast : {s}")


def piege(attendu):  # Mot piégé : scores exacts, et identiques au total recalculé depuis le récapitulatif (« qui a choisi quoi pour qui »)
    exact(attendu)
    src = open(__file__.replace("tests/verif_scores.py", "page_multi.py")).read()
    ns = {}; exec(src[src.index("def piege_points_paire"):src.index("def piege_lignes_recap")], ns)
    hote = robots[0]
    if not hote.get("recap_piege"): echec("pas de récapitulatif de Mot piégé")
    uids = {}
    for r in robots: uids.update(r.get("uids") or {})  # un joueur peut être parti avant que l'hôte ne relève les noms
    calc = {nom: ns["piege_points"](hote["recap_piege"], uid, 8) for uid, nom in uids.items()}
    final = parties()[-1]
    if any(calc.get(nom, 0) != v for nom, v in final.items()): echec(f"scores {final} ≠ récapitulatif {calc}")


REGLES = {
    "c1": lambda: exact({"ALICE": 32, "BOB": 32}),      # Précision : 16 points par mot trouvé du 1er coup, 2 manches
    "c2": blast,
    "c3": lambda: exact({"BOB": 1, "ALICE": 1}, {"BOB": 1, "ALICE": 1}),
    "c4": elimination,   # Élimination : 1 point par manche survécue
    "c5": lambda: exact({"BOB": 2, "ALICE": 2}),        # Coopératif : 1 point par manche trouvée pour tous
    "c6": rush,
    "c8": lambda: exact({"ALICE": 3, "BOB": 3}),
    "c9": lambda: exact({"BOB": 2, "ALICE": 2, "DAVID": 0}),   # Mystère : 1 point par mot trouvé
    "c10": lambda: exact({"ALICE": 0, "BOB": 2}),
    "c11": rush,
    "c12": rush,
    "c13": lambda: exact({"BOB": 32, "ALICE": 0}),
    "p1": lambda: piege({"ALICE": 2, "BOB": 0}),                 # Mot piégé : 1 point par mot trouvé, 0 sinon (2 manches)
    "p2": lambda: piege({"ALICE": 2, "BOB": 2, "CHLOE": 0}),     # mot au hasard après démarrage forcé, paire du joueur parti annulée
    "p3": lambda: piege({"ALICE": 2, "BOB": 0}),
    "q1": lambda: piege({"ALICE": 2, "BOB": 0}),                 # hôte PC, joueur web (choix invalide puis valide, devinette ratée)
    "q3": lambda: piege({"ALICE": 2, "BOB": 2, "CHLOE": 0}),     # joueur web parti après son choix : paire annulée, mot au hasard pour BOB
    "x1": lambda: piege({"ALICE": 2, "BOB": 0}),                 # cible cachée, hôte PC, joueur web
    "x2": lambda: piege({"BOB": 2, "ALICE": 0}),                 # cible cachée, hôte web, joueur PC
    "q2": lambda: piege({"BOB": 2, "ALICE": 0}),                 # hôte web, joueur PC (mot au hasard pour ALICE après démarrage forcé ; ALICE rate)
}
REGLES[nom]()
print(f"  scores conformes ({nom})")
