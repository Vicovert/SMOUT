#!/bin/bash

echo "==========================================="
echo "          COMPILATION SOUS LINUX"
echo "==========================================="

# Nettoyage des anciens dossiers (équivalent de rmdir /s /q et del)
rm -rf build dist main.spec

# Création et activation d'un environnement virtuel local
echo "Configuration de l'environnement Python..."
python3 -m venv venv_build
source venv_build/bin/activate

echo "Vérification de PyInstaller et Requests..."
pip install pyinstaller requests --quiet

echo "Génération de l'exécutable unique..."
# ATTENTION : Sous Linux, le séparateur pour --add-data est ':' (deux-points) et non ';'
pyinstaller --onefile \
 --add-data "fichiers:fichiers" \
 --icon="fichiers/logo.ico" \
 main.py

# Sous Linux, les exécutables n'ont pas d'extension .exe
if [ -f "dist/main" ]; then
    mv dist/main dist/SMOUT
    echo "TERMINÉ : Ton jeu est prêt dans le dossier 'dist' !"
else
    echo "[ERREUR] La compilation a échoué."
fi

# On quitte l'environnement virtuel
deactivate

echo ""
read -n 1 -s -r -p "Appuyez sur une touche pour continuer..."
echo ""