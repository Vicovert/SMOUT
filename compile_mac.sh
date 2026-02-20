#!/bin/bash

# ===========================================
#      SMOUT Compiler (macOS / Linux)
# ===========================================

echo "==========================================="
echo "      COMPILATION POUR MACOS (PyInstaller)"
echo "==========================================="

# Nettoyage des anciens fichiers de build
echo "Nettoyage des dossiers..."
rm -rf build dist main.spec

# Vérification/Installation des dépendances
echo "Vérification de PyInstaller et Requests..."
python3 -m pip install pyinstaller requests --quiet

# Génération de l'application macOS
# Note : Sur macOS, --onefile crée un exécutable UNIX. 
# Pour une application (.app), on utilise souvent le flag --windowed
echo "Génération du bundle macOS..."

python3 -m PyInstaller --noconsole --onefile --windowed \
 --add-data "fichiers:fichiers" \
 --icon="fichiers/logo.icns" \
 --name "SMOUT" \
 main.py

# Vérification du résultat
if [ -d "dist/SMOUT.app" ] || [ -f "dist/SMOUT" ]; then
    echo "-------------------------------------------"
    echo "TERMINE : Ton jeu est pret dans le dossier 'dist' !"
else
    echo "-------------------------------------------"
    echo "[ERREUR] La compilation a échoué."
fi