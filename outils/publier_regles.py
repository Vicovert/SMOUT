"""Publie database.rules.json dans Firebase (Realtime Database), depuis GitHub Actions.
La clé du compte de service est dans le secret GitHub FIREBASE_SA : jamais dans le dépôt ni dans une conversation.
Usage : FIREBASE_SA='{...}' python outils/publier_regles.py"""
import json, os, sys
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

BASE = "https://smout-multi-default-rtdb.europe-west1.firebasedatabase.app"
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cle = os.environ.get("FIREBASE_SA", "").strip()
if not cle:
    sys.exit("Secret FIREBASE_SA absent : ajoute la clé du compte de service dans les secrets du dépôt (voir CLAUDE.md).")
texte = open(os.path.join(RACINE, "database.rules.json"), encoding="utf-8").read()
regles = json.loads(texte)  # refuse un fichier mal formé avant d'envoyer quoi que ce soit
cred = service_account.Credentials.from_service_account_info(json.loads(cle), scopes=[
    "https://www.googleapis.com/auth/firebase.database", "https://www.googleapis.com/auth/userinfo.email"])
cred.refresh(Request())
h = {"Authorization": f"Bearer {cred.token}"}
r = requests.put(f"{BASE}/.settings/rules.json", headers=h, data=texte.encode("utf-8"), timeout=30)
print("Publication :", r.status_code, r.text[:300])
if r.status_code != 200: sys.exit(1)
lu = requests.get(f"{BASE}/.settings/rules.json", headers=h, timeout=30)
if lu.status_code != 200 or json.loads(lu.text) != regles:
    sys.exit(f"Vérification : les règles relues ne sont pas celles du dépôt ({lu.status_code}).")
print("Règles publiées et vérifiées :", regles["rules"]["v7"].get(".read", ""), "…", len(texte), "caractères")
