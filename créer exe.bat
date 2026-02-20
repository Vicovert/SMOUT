@echo off
title SMOUT Compiler (WinPython Portable)
echo ===========================================
echo    COMPILATION AVEC WINPYTHON PORTABLE
echo ===========================================

REM --- CONFIGURATION DES CHEMINS ---
set WPY_PATH=D:\Logitiels portables\WPy64-31241
set PYTHON_EXE=%WPY_PATH%\python-3.12.4.amd64\python.exe

REM 1. Nettoyage
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist main.spec del /q main.spec

REM 2. Verification des dependances (au cas ou)
echo Verification de PyInstaller...
"%PYTHON_EXE%" -m pip install pyinstaller requests --quiet

REM 3. Lancement de PyInstaller
echo Generation de l'EXE unique...
"%PYTHON_EXE%" -m PyInstaller --noconsole --onefile ^
 --add-data "fichiers;fichiers" ^
 --add-data "icones;icones" ^
 --icon="icones/logo.ico" ^
 main.py

REM 4. Renommage
if exist dist\main.exe (
    ren dist\main.exe SMOUT.exe
    echo.
    echo ===========================================
    echo    TERMINE : Ton jeu est pret dans 'dist' !
    echo ===========================================
) else (
    echo [ERREUR] La compilation a echoue.
)

pause